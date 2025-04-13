import cloudscraper

BASE_URL_SCHEME = "https://api.dineoncampus.com/v1/location/"
SBISA_LOCATION_ID = "587909deee596f31cedc179c"
COMMONS_LOCATION_ID = "59972586ee596fe55d2eef75"
# headers = {
#     'accept': 'application/json, text/plain, */*',
#     'accept-language': 'en-US,en;q=0.9',
#     'origin': 'https://dineoncampus.com',
#     'priority': 'u=1, i',
#     'referer': 'https://dineoncampus.com/',
#     'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"Windows"',
#     'sec-fetch-dest': 'empty',
#     'sec-fetch-mode': 'cors',
#     'sec-fetch-site': 'same-site',
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
#     'cookie': 'cf_clearance=hxxprh3H1wR9Lfj4tTl6v_Yez6hIy6Zj5Gxvkx7x1dU-1744559421-1.2.1.1-rMJCJOhPkFU9CLKLu21s3WcUrIOgKc1b.2RDGSUnQqXwRlKlQVL5fP_IJVA9jOViup4D.Hl.DoVqaR9S0MG8ul0uu2QIoBRZ9qpQ4f_PMTyvJ3vL4_3349eOspZA3Wdf4AKU1ljv4Wp8zU8TyOVnofbR5sKIJ_GHoDAAzOviP4rgmalSdS55aXmGPL9YFauU3VpVUezdVYzSpLqbtmXJbsPRc68wCfIVNGFelswPwW7TEptsvBUXGpuwyM1bg40ElO_Ii84RqECs.LwUDA.zEE6Wg1XXW5roKq9ycM1.jw.JyI0w3zpUlkYAiz9WmX5v6Z.OPINwXXzS.lEKk4U_JiIDSg_nWb2XGpULCFVmeUo'  # You'll need to get this from your browser
# }

# date format: YYYY-MM-DD
# if you don't provide a period_id, it will return the url for the default period as well as the period ids for the other periods
# if you provide a period_id, it will return the url for that period
def get_url(location_id : str, date : str, period_id : str | None = None) -> str:
    if period_id:
        return f"{BASE_URL_SCHEME}{location_id}/periods/{period_id}?platform=0&date={date}"
    else:
        return f"{BASE_URL_SCHEME}{location_id}/periods?platform=0&date={date}"

# returns a dict of period_name -> period_id
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

if __name__ == "__main__":
    periods = get_periods(SBISA_LOCATION_ID, "2025-04-14")
    for period_name, period_id in periods.items():
        menu = get_menu(SBISA_LOCATION_ID, "2025-04-14", period_id)
        print(f"Period: {period_name}")
        for category in menu:
            print(f"  {category['name']}")
            for item in category['items']:
                print(f"    {item['name']:<40} {item['id']}")


