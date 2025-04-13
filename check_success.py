from main import load_data


if __name__ == "__main__":
    total = 0
    failed = 0
    data = load_data()
    for date, date_data in data.items():
        for period, period_data in date_data.items():
            for location, location_data in period_data.items():
                if not location_data["success"]:
                    failed += 1
                total += 1
    print(f"Total: {total}, Failed: {failed}")
    print(f"Failed rate: {failed/total}")


