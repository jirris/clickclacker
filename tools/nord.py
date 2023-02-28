# Tool for fetching price information from Nordpool
# Uses Nordpool package, install with pip3 install nordpool
#
from nordpool import elspot
import datetime
import json
import sys, argparse, os

areas = ['FI']  # Configure areas to get prices, see Nordpool webpages API description
tax = 1.1 # Tax percentage multiplier (1.1 = 10%)

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

argParser = argparse.ArgumentParser()
argParser.add_argument("-t", "--time", help="1=todays prices, 2=tomorrows", default="1")
args = argParser.parse_args()


#For JSON Files
json2 = '../data_sources/tomorrow.json'
json1 = '../data_sources/today.json'

if int(args.time) == 2:
    endtime = datetime.date.today() + datetime.timedelta(days=1)
    endtime = endtime.strftime("%Y-%m-%d")
    jsonfile = json2
    when = "tomorrow"
else:
    endtime = datetime.date.today()
    endtime = endtime.strftime("%Y-%m-%d")
    jsonfile = json1
    when = "today"

try:
    # Initialize class for fetching Elspot prices
    prices_spot = elspot.Prices()

    # Fetch hourly Elspot prices for Finland and print the resulting dictionary
    dic = (prices_spot.hourly(end_date=endtime, areas=areas))

    table = []

    for each in dic["areas"]["FI"]["values"]:
       day = (each["start"].strftime("%Y-%m-%dT%H:%M:%S%z"))
       price = (int(each["value"])/10)
       table.append({"DateTime": day, "PriceNoTax": price, "PriceWithTax": price * tax})

    json_object = json.dumps(table, indent = 4)

    with open(jsonfile, 'w', encoding='utf-8') as f:
        json.dump(table, f, ensure_ascii=False, indent=4)
        today = datetime.date.today()

        print(str(today) + " New pricedata retrieved for " + when)
    f.close()
    sys.exit(0)

except Exception as e:
    print("Price data not available for " + when)
    sys.exit(1)