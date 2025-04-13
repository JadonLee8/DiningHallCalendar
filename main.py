import cloudscraper
import json
from datetime import datetime, timedelta
from pathlib import Path

BASE_URL_SCHEME = "https://api.dineoncampus.com/v1/location/"
SBISA_LOCATION_ID = "587909deee596f31cedc179c"
COMMONS_LOCATION_ID = "59972586ee596fe55d2eef75"
LOCATION_IDS = {"SBISA": SBISA_LOCATION_ID, "COMMONS": COMMONS_LOCATION_ID}
LOCATION_NAMES = {SBISA_LOCATION_ID: "SBISA", COMMONS_LOCATION_ID: "COMMONS"}
DATA_FILE = "dining_data.json"

# FORMAT FOR DATA
# {
#     "YYYY-MM-DD": {
#         "periods": {
#             "period_name": "period_id",
#             ...
#         },
#         "period_name": {
#             "location_name": {
#                 "category_name": {
#                     "category_id": "category_id",
#                     "items": [
#                         {
#                             "name": "item_name",
#                             "id": "item_id"
#                         },
#                         ...
#                     ]
#                 },
#                 ...
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
    return {}

def save_data(data: dict):
    """Save data to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_url(location_id : str, date : str, period_id : str | None = None) -> str:
    if period_id:
        return f"{BASE_URL_SCHEME}{location_id}/periods/{period_id}?platform=0&date={date}"
    else:
        return f"{BASE_URL_SCHEME}{location_id}/periods?platform=0&date={date}"

def get_periods(location_id : str, date : str) -> dict[str, str]:
    url = get_url(location_id, date)
    print(f"Making request to: {url}")
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)
    periods = response.json()["periods"]
    return {period["name"]: period["id"] for period in periods}

def get_menu(location_id : str, date : str, period_id : str) -> list:
    url = get_url(location_id, date, period_id)
    print(f"Making request to: {url}")
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)
    return response.json()["menu"]["periods"]["categories"]

def update_dining_data(location_id: str, start_date: str, days: int = 28):
    """Update dining data for the specified number of days starting from start_date"""
    data = load_data()
    
    # Parse start date
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    for _ in range(days):
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"\nFetching data for {date_str}")
        
        # Initialize date entry if it doesn't exist
        if date_str not in data:
            data[date_str] = {}
        
        try:
            # Get periods for the date
            periods = get_periods(location_id, date_str)
            data[date_str]["periods"] = periods
            
            # Get menu for each period
            for period_name, period_id in periods.items():
                menu = get_menu(location_id, date_str, period_id)
                data[date_str][period_name][LOCATION_NAMES[location_id]] = menu
                
            # Save after each successful date to prevent data loss
            save_data(data)
            print(f"Successfully saved data for {date_str}")
            
        except Exception as e:
            print(f"Error fetching data for {date_str}: {e}")
        
        # Move to next day
        current_date += timedelta(days=1)

def print_menu_for_date(date: str):
    """Print menu for a specific date"""
    data = load_data()
    if date not in data:
        print(f"No data available for {date}")
        return
        
    print(f"\nMenu for {date}:")
    for period_name, period_data in data[date].items():
        if period_name == "periods":
            continue
        print(f"\nPeriod: {period_name}")
        for category in period_data:
            print(f"  {category['name']}")
            for item in category['items']:
                print(f"    {item['name']:<40} {item['id']}")

if __name__ == "__main__":
    # Update data for the next 28 days
    today = datetime.now().strftime("%Y-%m-%d")
    update_dining_data(SBISA_LOCATION_ID, today,3)
    
    # Print today's menu as an example
    print_menu_for_date(today)
    print_menu_for_date((datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))
    print_menu_for_date((datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"))


