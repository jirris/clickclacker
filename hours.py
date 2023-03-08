import json
import aux
import datetime
import time
from bs4 import BeautifulSoup as bs
import requests
import configparser
import os
from aux import errorhandler

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

config = configparser.ConfigParser()

# Read config for various defaults
try:
    config.read('conf/devices.conf')
    jsonToday = config["DEFAULT"]["jsonToday"]
    jsonTomorrow = config["DEFAULT"]["jsonTomorrow"]
    json_date = config["DEFAULT"]["json_date"]
    json_rank = config["DEFAULT"]["json_rank"]
    entsoe = config["DEFAULT"]["entsoe"]
    etoken = config["DEFAULT"]["etoken"]
    ecountry = config["DEFAULT"]["ecountry"]
    tz = float(config["DEFAULT"]["timezone"])

except Exception as e:
    aux.errorhandler("Hours: Config not found", e, 2)
    exit()

def priorities(table, device, nhours):
    try:
        priorityhours = config[device]["priority_hours"]
    except KeyError as x:
        errorhandler("Priority hours config not found for " + device, x, 0)
        return "error", 0

    priorityhours = priorityhours.split(",")
    cleanhours = []
    table2 = []

    for digit in priorityhours:
        try:
            int(digit)
            if int(digit) < 24 and int(digit) >= 0:
                cleanhours.append(int(digit))
        except ValueError as x:
            errorhandler("Priority hour value error on " + device, x, 1)
            continue

    prioritytable = []

    for key in table:
        hour = int(datetime.datetime.fromtimestamp(key[0]).strftime('%H'))
        if hour in cleanhours:
            prioritytable.append(key)
    prioritytable.sort(key=lambda x: x[1])  # Sort by price

    for key in prioritytable:
        if nhours == 0:
            break
        hour = int(datetime.datetime.fromtimestamp(key[0]).strftime('%H'))
        if hour in cleanhours:
            table2.append(key)
            nhours = nhours - 1
    return table2, nhours
def priceLimit(table, device):
    a = 0
    result = []
    max = config.get(device, 'upperlimit', fallback="n")
    if max != "n":
        max = float(max)

    for key in table:  # Remove higher prices
        if float(key[1]) <= max:
            result.append(key)
        a = a + 1
    return result


def hoursJSON(day, hours, adj, device):
    if 1 <= hours <= 24:
        nhours = hours
    else:
        nhours = 0
    if int(day) == 2:
        jsonfile = jsonTomorrow
        basedate = datetime.datetime.now() + datetime.timedelta(days=1)
        compdate = basedate
    else:
        jsonfile = jsonToday
        basedate = datetime.datetime.now()
        compdate = basedate

    try:
        f = open(jsonfile)
        data = json.load(f) 
        f.close()
        data.sort(key=lambda x: x[json_rank])
    except Exception as e:
        if int(day) == 2:
            return "error"
        aux.errorhandler("Hours: An exception occurred ", str(e), 2)  # --> catastrofic fail
        return "error"
    table = []

    origtime = datetime.datetime.strptime(data[1][json_date], '%Y-%m-%dT%H:%M:%S%z')
    origtime = (origtime.strftime("%Y-%m-%d"))
    comptime = (compdate.strftime("%Y-%m-%d"))

    if origtime == comptime:
        for key in data:
            date_time = (datetime.datetime.strptime(key[json_date], '%Y-%m-%dT%H:%M:%S%z'))
            currenttz = datetime.timedelta(hours=tz)
            sourcetz = (date_time.utcoffset())
            correction = currenttz - sourcetz
            date_time = date_time + correction
            date_time = int((int(time.mktime(date_time.timetuple()))))
            price = str((key[json_rank]))
            price = round(float(price), 2)
            tuplev = (int(date_time), float(price))
            table.append(tuplev)
    else:
        return "error"
    table2 = []

    # If force is used, add hours and remove those from needed hours to keep amount the same
    count = 1
    table.sort()

    if config.get(device, 'force', fallback="n") == "y":
        diff = int(config[device]["forceh"])

        for extra in table:
            if count == diff:
                if extra not in table2:
                    table2.append(extra)
                    nhours = nhours - 1
                count = 0
            count = count + 1

    # Priority hours

    if config.get(device, 'priority', fallback="n") == "y":
        returnvalue = priorities(table, device, nhours)
        if returnvalue[0] != "error":
            table2 = returnvalue[0]
            nhours = returnvalue[1]

    table.sort(key=lambda x: x[1])  # Sort by price
    for key in table:
        if nhours == 0:
            break
        if key not in table2:
            table2.append(key)
            nhours = nhours - 1

    if adj == 1:
        low = config.get(device, 'lowerlimit', fallback="n")
        if low != "n":
            low = float(low)
            for key in table:  # Add for low cost hours
                if key[1] <= low:
                    if key not in table2:
                        table2.append(key)

    if adj == 1:  # Adjust expensive hours off
        if config.get(device, 'upperlimit', fallback="n") != "n":
            # config[device]["upperlimit"] != "n":
            table2 = priceLimit(table2, device)
    table2.sort()
    return table2


def ehours(day, hours, adj, device):
    data = []
    when = "tomorrow"
    skip = 0

    offset = aux.settime(tz)  # Unixtime offset

    if 1 <= hours <= 24:
        nhours = hours
    else:
        nhours = 0
    if day == 1:  # Today
        when = "today"
        basedate = datetime.datetime.now()
        compdate = basedate
        xmlfile = "data/entsoe_today.xml"
    else:
        basedate = datetime.datetime.now() + datetime.timedelta(days=1)
        compdate = basedate
        xmlfile = "data/entsoe_tomorrow.xml"
    start = basedate.replace(hour=0, minute=0, second=0, microsecond=0)
    end = basedate.replace(hour=23, minute=0, second=0, microsecond=0)
    start = start.strftime("%Y%m%d%H%M")
    end = end.strftime("%Y%m%d%H%M")
    url = "https://web-api.tp.entsoe.eu/api?securityToken=" + etoken + "&documentType=A44&in_Domain=" + \
          ecountry + "&out_Domain=" + ecountry + "&periodStart=" + start + "&periodEnd=" + end

    try:
        if os.path.isfile(xmlfile):  # See if we already have needed data
            with open(xmlfile, "r") as file:
                xml = file.readlines()
            file.close()
            xml = "".join(xml)
            data = bs(xml, features="xml")
            if data.find("start") is None:
                skip = 0
            else:
                startdate = data.find("start").text
                origdate = (datetime.datetime.strptime(startdate, '%Y-%m-%dT%H:%MZ')
                            + datetime.timedelta(hours=int(tz)))  # make sure we hit right day due timezones
                if str(origdate.date()) == str(compdate.strftime("%Y-%m-%d")):
                    skip = 1
    except:
        skip = 0
        pass

    if skip == 0:
        try:
            xml = requests.get(url)
            f = open(xmlfile, "w")
            f.write(xml.text)
            f.close()
            data = bs(xml.content, features="xml")
        except Exception as e:
            aux.errorhandler("Hours: Couldn't connect to site", e, 2)
            return "error"

    try:
        prices = {}
        table = []
        if data.find("Point") is not None:

            for row in data.findAll("Point"):
                date = row.find("position").text
                price = row.find("price.amount").text
                price = float(price) / 10
                price = round(price, 2)
                prices.update({date: price})

            startdate = data.find("start").text
            enddate = data.find("end").text

            date_time = (datetime.datetime.strptime(startdate, '%Y-%m-%dT%H:%M%z'))
            date_time = int((int(time.mktime(date_time.timetuple()))))

            hour = 1

            while hour < 25:  # Change position to unixtime
                table.append((date_time, prices[str(hour)]))
                date_time = date_time + 3600
                hour = hour + 1

    except Exception as e:
        aux.errorhandler("Hours: An exception occurred",e ,2)
        return "error"

    table2 = []

    # If force is used, add hours and remove those from needed hours to keep amount the same
    count = 1
    table.sort()

    if config.get(device, 'force', fallback="n") == "y":
        try:
            diff = int(config[device]["forceh"])
        except Exception as e:
            aux.errorhandler("Hours: Force configuration failure", e, 2)
            return "error"

        for extra in table:
            if count == diff:
                if extra not in table2:
                    table2.append(extra)
                    nhours = nhours - 1
                count = 0
            count = count + 1

    table.sort(key=lambda x: x[1])  # Sort by price

    # Priority hours

    if config.get(device, 'priority', fallback="n") == "y":
        returnvalue = priorities(table, device, nhours)
        if returnvalue[0] != "error":
            table2 = returnvalue[0]
            nhours = returnvalue[1]

    for key in table:  # Return requested amount
        if nhours == 0:
            break
        if key not in table2:
            nhours = nhours - 1
            table2.append(key)

    if adj == 1:
        low = config.get(device, 'lowerlimit', fallback="n")
        if low != "n":
            low = float(low)
            for key in table:  # Add for low cost hours
                if key[1] <= low:
                    if key not in table2:
                        table2.append(key)

    table3 = []
    for each in table2:   # Timezone correction
        utime = int(each[0]) + offset
        price = each[1]
        each = (utime, price)
        table3.append(each)

    if adj == 1:   # Adjust expensive hours off
        if config.get(device, 'upperlimit', fallback="n") != "n":
            table3 = priceLimit(table3, device)

    table3.sort()

    if table3 == []:
        return "error"
    if skip == 0:
        aux.infohandler(str(datetime.datetime.now()) + " New pricedata retrieved for " + when)
    return table3

def hours(day, hours, adj, device):
    if entsoe == "y":
        return ehours(day, hours, adj, device)
    else:
        return hoursJSON(day, hours, adj, device)


if __name__ == '__main__':
    # print((ehours(2, 4, 0, "Inverter")))
    print((hoursJSON(1, 6, 0, "Inverter")))
