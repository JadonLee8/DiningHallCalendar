import cloudscraper
import json
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
import time

from check_success import check_success

BASE_URL_SCHEME = "https://api.dineoncampus.com/v1/location/"
SBISA_LOCATION_ID = "587909deee596f31cedc179c"
COMMONS_LOCATION_ID = "59972586ee596fe55d2eef75"
LOCATION_IDS = {"SBISA": SBISA_LOCATION_ID, "COMMONS": COMMONS_LOCATION_ID}
LOCATION_NAMES = {SBISA_LOCATION_ID: "SBISA", COMMONS_LOCATION_ID: "COMMONS"}
DATA_FILE = "dining_data.json"

# Configure logger
logger.add("dining.log", rotation="1 day", retention="7 days", level="INFO")

# FORMAT FOR DATA
# {
#     "YYYY-MM-DD": {
#         "periods": {
#             "period_name": "period_id",
#             ...
#         },
#         "period_name": {
#             "location_name": {
#                 "success": false,
#                 "menu": {
#                     "category_name": {
#                         "category_id": "category_id",
#                         "items": [
#                             {
#                                 "name": "item_name",
#                                 "id": "item_id"
#                             },
#                             ...
#                         ]
#                     },
#                     ...
#                 }
#             }
#             ...
#         }
#         ...
#     },
#     repeat for each day
# }

def load_data() -> dict:
    """Load existing data from file or return empty dict if file doesn't exist"""
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    logger.info("No existing data file found, starting with empty data")
    return {}

def save_data(data: dict):
    """Save data to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Data saved to {DATA_FILE}")

def get_url(location_id : str, date : str, period_id : str | None = None) -> str:
    if period_id:
        return f"{BASE_URL_SCHEME}{location_id}/periods/{period_id}?platform=0&date={date}"
    else:
        return f"{BASE_URL_SCHEME}{location_id}/periods?platform=0&date={date}"

def get_periods(location_id : str, date : str) -> dict[str, str]:
    url = get_url(location_id, date)
    logger.debug(f"Fetching periods from {url}")
    scraper = cloudscraper.create_scraper()
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = scraper.get(url)
            periods = response.json()["periods"]
            logger.info(f"Found {len(periods)} periods for {date}")
            return {period["name"]: period["id"] for period in periods}
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                time.sleep(1)
                continue
            else:
                logger.error(f"All {max_retries} attempts failed: {str(e)}")
                raise

def get_menu(location_id : str, date : str, period_id : str) -> list:
    url = get_url(location_id, date, period_id)
    logger.debug(f"Fetching menu from {url}")
    scraper = cloudscraper.create_scraper()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = scraper.get(url)
            return response.json()["menu"]["periods"]["categories"]
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                time.sleep(1)
                continue
            else:
                logger.error(f"All {max_retries} attempts failed: {str(e)}")
                raise

def update_dining_data(location_id: str, start_date: str, days: int = 28):
    """Update dining data for the specified number of days starting from start_date"""
    data = load_data()
    
    # Parse start date
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    location_name = LOCATION_NAMES[location_id]
    
    logger.info(f"Starting update for {location_name} from {start_date} for {days} days")
    
    for _ in range(days):
        date_str = current_date.strftime("%Y-%m-%d")
        logger.info(f"Processing {date_str} for {location_name}")
        
        # Initialize date entry if it doesn't exist
        if date_str not in data:
            data[date_str] = {}
        
        # Check if day is already fully successful
        if data[date_str].get("full_success", False):
            logger.info(f"Skipping {date_str} - already fully successful")
            current_date += timedelta(days=1)
            continue
        
        try:
            # Get periods for the date
            periods = get_periods(location_id, date_str)
            data[date_str]["periods"] = periods

            # Initialize full_success as True, will be set to False if any location fails
            data[date_str]["full_success"] = True
            
            # Get menu for each period
            for period_name, period_id in periods.items():
                # Skip if this period was already successfully fetched
                if (period_name in data[date_str] and 
                    location_name in data[date_str][period_name] and 
                    data[date_str][period_name][location_name]["success"]):
                    logger.info(f"Skipping {period_name} for {date_str} - already successfully fetched")
                    continue
                
                # Initialize the period and location structure
                if period_name not in data[date_str]:
                    data[date_str][period_name] = {}
                if location_name not in data[date_str][period_name]:
                    data[date_str][period_name][location_name] = {"success": False}
                
                logger.debug(f"Fetching {period_name} menu for {date_str}")
                menu = get_menu(location_id, date_str, period_id)
                
                # Add menu items to the existing structure
                data[date_str][period_name][location_name]["menu"] = {}
                for category in menu:
                    category_name = category["name"]
                    if category_name not in data[date_str][period_name][location_name]["menu"]:
                        data[date_str][period_name][location_name]["menu"][category_name] = {
                            "category_id": category.get("id", ""),
                            "items": []
                        }
                    for item in category["items"]:
                        data[date_str][period_name][location_name]["menu"][category_name]["items"].append({
                            "name": item["name"],
                            "id": item["id"]
                        })
                
                data[date_str][period_name][location_name]["success"] = True
                
            # Check if all locations in all periods are successful
            for period_name, period_data in data[date_str].items():
                if period_name == "periods" or period_name == "full_success":
                    continue
                for location_name, location_data in period_data.items():
                    if not location_data.get("success", False):
                        data[date_str]["full_success"] = False
                        break
                if not data[date_str]["full_success"]:
                    break
                
            # Save after each successful date to prevent data loss
            save_data(data)
            logger.success(f"Successfully processed {date_str}")
            
        except Exception as e:
            logger.error(f"Error processing {date_str}: {str(e)}")
        
        # Move to next day
        current_date += timedelta(days=1)

def print_menu_for_date(date: str):
    """Print menu for a specific date"""
    data = load_data()
    if date not in data:
        logger.warning(f"No data available for {date}")
        return
        
    logger.info(f"Displaying menu for {date}")
    for period_name, period_data in data[date].items():
        if period_name == "periods":
            continue
            
        print(f"\nPeriod: {period_name}")
        for location_name, location_data in period_data.items():
            print(f"  Location: {location_name}")
            for category in location_data:
                print(f"    {category['name']}")
                for item in category['items']:
                    print(f"      {item['name']:<40} {item['id']}")

if __name__ == "__main__":
    # Update data for the next 28 days
    today = datetime.now().strftime("%Y-%m-%d")

    dining_hall = input("Enter SBISA or COMMONS: \n")
    if dining_hall != "COMMONS" and dining_hall != "SBISA":
        raise ValueError("Invalid input: Please enter either 'SBISA' or 'COMMONS'")
    
    num_days = int(input("Enter the number of days to update: \n"))
    if num_days <= 0 or num_days >= 100:
        raise ValueError("Invalid input: Please enter a positive integer less than 100")

    update_dining_data(LOCATION_IDS[dining_hall], today, 28)
    check_success(load_data())



