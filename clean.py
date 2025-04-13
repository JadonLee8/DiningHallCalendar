from main import load_data, save_data

if __name__ == "__main__":
    data = load_data()
    dates_to_remove = []
    
    for date, date_data in data.items():
        has_wrong_menu = False
        for period_name, period_data in date_data.items():
            if period_name == "Dinner" or period_name == "Breakfast" or period_name == "Lunch" or period_name == "Brunch":
                has_wrong_menu = True
                break
        if has_wrong_menu:
            dates_to_remove.append(date)
    
    for date in dates_to_remove:
        del data[date]
        print(f"Removed date {date} - no menu data found")
    
    save_data(data)
    print(f"Removed {len(dates_to_remove)} dates without menu data") 