#!/usr/bin/python3
import datetime
import json
import sys, argparse
from urllib.request import urlopen
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# This script can be used for getting prices of electricity from https://api.spot-hinta.fi
# Script stores prices in JSON file in data_sources

#For JSON Files
json2 = '../data_sources/tomorrow.json'
json1 = '../data_sources/today.json'

argParser = argparse.ArgumentParser()
argParser.add_argument("-t", "--time", help="1=todays prices, 2=tomorrows", default="1")
args = argParser.parse_args()

if int(args.time) == 2:
    url = "https://api.spot-hinta.fi/DayForward"
    jsonfile = json2
    when = "tomorrow"
else:
    url = "https://api.spot-hinta.fi/Today"
    jsonfile = json1
    when = "today"
try:
    json_url = urlopen(url)
    data = json.loads(json_url.read())

    if len(data) < 10:
        print("No data get!")
        exit(1)
    else:
        hour = 0

    for each in data:
        each["PriceNoTax"] = each["PriceNoTax"] * 100
        each["PriceWithTax"] = each["PriceWithTax"] * 100

    with open(jsonfile, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        today = datetime.date.today()

        print(str(today) + " New pricedata retrieved for " + when)
    f.close()
    sys.exit(0)

except Exception as e:
    print("Price data not available for " + when)
    sys.exit(1)