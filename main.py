import requests
import json
import datetime
import os
from operator import itemgetter


# GLOBALS
PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))   # Gets the absolute path for the running file
FILE_NAME = "Riven_data_{platform}_{monday:%y}-{monday:%m}-{monday:%d}.json"

RAW_PATH = os.path.join(PATH, 'data/{platform}/raw')
RAW_FILE_PATH = os.path.join(RAW_PATH, FILE_NAME)

EDIT_PATH = os.path.join(PATH, "data/{platform}/edited")
TOTAL_FILE_PATH = os.path.join(EDIT_PATH, "TOTAL_{platform}.json")

L_MONDAY = ""
PLATFORMS = ["PC", "PS4", "XB1", "SWI"]
URL = "https://n9e5v4d8.ssl.hwcdn.net/repos/weeklyRivens{}.json"


def last_monday():
    '''Gets the last monday date'''
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    return monday


def get_riven_json(platform):
    '''Gets the json for a given platform'''
    print(f"Checking if this week json for {platform} is saved!")
    file_path = os.path.normpath(RAW_FILE_PATH.format(platform=platform, monday=L_MONDAY))

    # Checks if the file already exists
    if os.path.isfile(file_path):
        print("File already exists!\n-----------------")
        return

    print("No file found, saving it!\n-----------------")
    r = requests.get(URL.format(platform))
    r.raise_for_status()
    data = r.json()
    with open(file_path, "w") as outfile:
        json.dump(data, outfile, indent=4)


def process_data(platform):
    '''Calls all of the processing functions for every raw file'''

    # Goes over every file in the raw folder and processes the data for it
    for filename in os.listdir(os.path.normpath(RAW_PATH.format(platform=platform))):

        print(f"\nProcessing raw {filename}\n")

        date = filename.rstrip(".json")[-8:]
        raw_file_path = os.path.normpath(os.path.join(RAW_PATH.format(platform=platform), filename))
        edit_file_path = os.path.normpath(os.path.join(EDIT_PATH.format(platform=platform), filename))

        with open(raw_file_path, "r") as raw:
            raw_data = json.load(raw)
            sales = sale_calc(raw_data)
            raw_dict = create_dict(raw_data, 1)
            del raw_data

        # Calls total_json which handles the total file and returns the total_dict
        total_dict = total_json(platform, raw_dict, date, sales)

        if os.path.isfile(edit_file_path):
            print(f"/edited/{filename} Aleady exists!")
        else:
            comparison(platform, raw_dict, total_dict, sales, edit_file_path)


def sale_calc(data):
    '''Calculates the number of sales'''
    print("Calculating the total sales number!")
    min_price = []
    max_price = []
    pop = []
    for d in data:
        min_price.append(d["min"])
        max_price.append(d["max"])
        pop.append(d["pop"])

    min_pop = min(pop)
    pop_ind = [i for i, x in enumerate(pop) if x == min_pop]  # Creates a list with all of the indices for min(pop)

    # Goes overy every instance of a riven having the min pop, if all of them have min == max it assumes min_pop is only 1 trade
    for i in pop_ind:
        if min_price[i] != max_price[i]:
            break
    else:
        trades = 100 / min_pop
        return trades

    # If the for loop breaks it assumes that min_pop is 2 trades which can't be confirmed but it's the best we got
    trades = 100 / (min_pop / 2)
    return trades


def total_json(platform, raw_dict, date, sales):
    '''Creates/modifies the total files'''
    total_file_path = os.path.normpath(TOTAL_FILE_PATH.format(platform=platform))
    try:
        with open(total_file_path, "r") as open_file:
            total_file = json.load(open_file)
            total_dict = create_dict(total_file, 3)
            dates = total_file[0]
            del total_file
        print(f"Found TOTAL_{platform} adding data!")

        if date in dates:
            print(f"Data from {date} already in TOTAL!")
            return total_dict      # Will stop the function to prevent the unneeded saving of the same data

        dates.append(date)

        for key in list(raw_dict.keys()):
            if raw_dict[key]["median"] == 0:
                median_count = 0
            else:
                median_count = 1

            raw = raw_dict[key]
            # Creates a empty entry if not in total
            if key not in total_dict:
                total_dict[key] = {
                    "itemType": raw["itemType"],
                    "compatibility": raw["compatibility"],
                    "rerolled": raw["rerolled"],
                    "total_avg": 0,
                    "total_stddev": 0,
                    "total_min": 0,
                    "total_max": 0,
                    "total_pop": 0,
                    "total_sales": 0,
                    "total_median": 0,
                    "median_count": 0,
                    "count": 0,
                }

            # Adds the values
            total = total_dict[key]
            total["total_avg"] += raw["avg"]
            total["total_stddev"] += raw["stddev"]
            total["total_min"] += raw["min"]
            total["total_max"] += raw["max"]
            total["total_pop"] += raw["pop"]
            total["total_sales"] += raw["pop"] * sales / 100
            total["total_median"] += raw["median"]
            total["median_count"] += median_count
            total["count"] += 1

        total_file = []
        total_file.append(dates)

        d_l = []
        for key in list(total_dict.keys()):
            total = total_dict[key]
            d_l.append({
                "itemType": total["itemType"],
                "compatibility": total["compatibility"],
                "rerolled": total["rerolled"],
                "total_avg": total["total_avg"],
                "total_stddev": total["total_stddev"],
                "total_min": total["total_min"],
                "total_max": total["total_max"],
                "total_pop": total["total_pop"],
                "total_sales": total["total_sales"],
                "total_median": total["total_median"],
                "median_count": total["median_count"],
                "count": total["count"]
            })
        total_file.append(d_l)

    # File doesn't exist
    except FileNotFoundError:
        print(f"No TOTAL_{platform} found creating it!")
        # Adds the date into the first list
        total_file = []
        total_file.append([date])

        # Data list
        d_l = []
        for key in list(raw_dict.keys()):
            raw = raw_dict[key]

            if raw_dict[key]["median"] == 0:
                median_count = 0
            else:
                median_count = 1

            d_l.append({
                "itemType": raw["itemType"],
                "compatibility": raw["compatibility"],
                "rerolled": raw["rerolled"],
                "total_avg": raw["avg"],
                "total_stddev": raw["stddev"],
                "total_min": raw["min"],
                "total_max": raw["max"],
                "total_pop": raw["pop"],
                "total_sales": (raw["pop"] * sales) / 100,
                "total_median": raw["median"],
                "median_count": median_count,
                "count": 1
            })

        total_file.append(d_l)
        total_dict = create_dict(total_file, 3)
    print(f"Saving TOTAL_{platform}.json\n")

    with open(total_file_path, "w") as file:
        json.dump(total_file, file, indent=4)
    return total_dict


def comparison(platform, raw_dict, total_dict, sales, file_path):
    '''Does all of the comparisons'''
    edited_list = []
    for key in list(raw_dict.keys()):
        total = total_dict[key]
        raw = raw_dict[key]

        # First 2 weeks don't have median this handles it
        try:
            median = raw["Median"]
            total_median = total["total_median"]
            median_count = total["median_count"]
            if median_count == 0:
                median_diff = 0
            else:
                median_diff = median - (total_median / median_count)
        except KeyError:
            median = 0
            median_diff = 0

        current_sales = (sales * raw["pop"]) / 100
        try:
            avg_diff = raw["avg"] - ((total["total_avg"] - raw["avg"]) / (total["count"] - 1))
            stddev_diff = raw["stddev"] - ((total["total_stddev"] - raw["stddev"]) / (total["count"] - 1))
            min_diff = raw["min"] - ((total["total_min"] - raw["min"]) / (total["count"] - 1))
            max_diff = raw["max"] - ((total["total_max"] - raw["max"]) / (total["count"] - 1))
            pop_diff = raw["pop"] - ((total["total_pop"] - raw["pop"]) / (total["count"] - 1))
            sales_diff = current_sales - ((total["total_sales"] - current_sales) / (total["count"] - 1))
        except ZeroDivisionError:
            avg_diff = 0
            stddev_diff = 0
            min_diff = 0
            max_diff = 0
            pop_diff = 0
            sales_diff = 0

        edited_list.append({
            "itemType": raw["itemType"],
            "compatibility": raw["compatibility"],
            "rerolled": raw["rerolled"],
            "avg": raw["avg"],
            "avg_diff": avg_diff,
            "stddev": raw["stddev"],
            "stddev_diff": stddev_diff,
            "min": raw["min"],
            "min_diff": min_diff,
            "max": raw["max"],
            "max_diff": max_diff,
            "pop": raw["pop"],
            "pop_diff": pop_diff,
            "median": raw["median"],
            "median_diff": median_diff,
            "sales": current_sales,
            "sale_diff": sales_diff
        })

    with open(file_path, "w") as file:
        json.dump(edited_list, file, indent=4)
    print(f"Saved {file_path}\n-----------------\n")


def create_dict(data, mode):
    '''Creates the useful dicts with name as key and the data as a value
    Mode 1 for raw data
    Mode 2 for edited data
    Mode 3 for Total data'''
    data_dict = {}
    if mode == 1:
        for d in data:

            # Creates the name for the riven
            if d["compatibility"] is None:
                name = f"Veiled {d['itemType']}"
            elif d["rerolled"]:
                name = f"{d['compatibility']}_T"
            else:
                name = f"{d['compatibility']}_F"

            # Older data doesn't have median
            median = d.get('median', 0)

            data_dict[name] = {
                "itemType": d["itemType"],
                "compatibility": d["compatibility"],
                "rerolled": d["rerolled"],
                "avg": d["avg"],
                "stddev": d["stddev"],
                "min": d["min"],
                "max": d["max"],
                "pop": d["pop"],
                "median": median
            }
    elif mode == 2:
        for d in data:

            # Creates the name for the riven
            if d["compatibility"] is None:
                name = f"Veiled {d['itemType']}"
            elif d["rerolled"]:
                name = f"{d['compatibility']}_T"
            else:
                name = f"{d['compatibility']}_F"

            data_dict[name] = {d}

    elif mode == 3:
        for d in data[1]:

            # Creates the name for the riven
            if d["compatibility"] is None:
                name = f"Veiled {d['itemType']}"
            elif d["rerolled"]:
                name = f"{d['compatibility']}_T"
            else:
                name = f"{d['compatibility']}_F"

            data_dict[name] = {
                "itemType": d["itemType"],
                "compatibility": d["compatibility"],
                "rerolled": d["rerolled"],
                "total_avg": d["total_avg"],
                "total_stddev": d["total_stddev"],
                "total_min": d["total_min"],
                "total_max": d["total_max"],
                "total_pop": d["total_pop"],
                "total_sales": d["total_sales"],
                "total_median": d["total_median"],
                "median_count": d["median_count"],
                "count": d["count"]
            }
    return data_dict


def total_sort(platform):
    '''Sorts the TOTAL file. First by weapon name then by rerolled status and keeps the veiled first'''
    print(f"Sorting TOTAL_{platform}")
    total_file_path = os.path.normpath(TOTAL_FILE_PATH.format(platform=platform))

    with open(total_file_path, "r") as in_file:
        data = json.load(in_file)

    veiled = data[1][0:6]
    un_veiled = sorted(data[1][6:], key=itemgetter('compatibility', 'rerolled'))
    sorted_file = [data[0], veiled + un_veiled]

    with open(total_file_path, "w") as out_file:
        json.dump(sorted_file, out_file, indent=4)


if __name__ == '__main__':
    L_MONDAY = last_monday()
    for p in PLATFORMS:
        print(f"\n-----------------\n     {p}     \n-----------------\n")
        get_riven_json(p)
        process_data(p)
        total_sort(p)
