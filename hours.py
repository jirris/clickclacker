import json
import aux
import datetime
from datetime import datetime as dt
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
    entsoebackup = config["DEFAULT"]["entsoebackup"]
    etoken = config["DEFAULT"]["etoken"]
    ecountry = config["DEFAULT"]["ecountry"]
    tz = float(config["DEFAULT"]["timezone"])
    tax = float(config.get("DEFAULT", 'tax', fallback="0"))
    daylight = config.get("DEFAULT", 'daylight', fallback="n")

    if daylight == "y" or daylight == "Y":
        is_dst = time.daylight and time.localtime().tm_isdst > 0
        utc_offset = - (time.altzone if is_dst else time.timezone)
        tz2 = utc_offset / 3600
        if tz != tz2:
            aux.infohandler("Daylight saving in use, timezone: " + str(tz2))
            tz = tz2

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
            if 24 > int(digit) >= 0:
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

    origtime = dt.strptime(data[1][json_date], '%Y-%m-%dT%H:%M:%S%z')
    origtime = (origtime.strftime("%Y-%m-%d"))
    comptime = (compdate.strftime("%Y-%m-%d"))

    if origtime == comptime:
        for key in data:
            date_time = (dt.strptime(key[json_date], '%Y-%m-%dT%H:%M:%S%z'))
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
    # Adding possible extra network cost per hour
    if config.get(device, 'networkoffset', fallback="n") == "y":
        tadd = []
        networkosvalue = config.get(device, 'networkosvalue', fallback="0:0")
        stringT = networkosvalue.split(",")

        addprice = {}
        for t in stringT:
            addprice[int(t.split(":")[0])] = t.split(":")[1]

        for each in table:
            if dt.fromtimestamp(each[0]).hour in addprice:
                tadd.append((each[0], round(float(each[1]) + float(addprice[dt.fromtimestamp(each[0]).hour]), 2)))
            else:
                tadd.append((each[0], each[1]))
        table = tadd

    table2 = []

    # If force is used, add hours and remove those from needed hours to keep amount the same
    count = 1
    table.sort()

    if config.get(device, 'force', fallback="n") == "y":
        range = int(config.get(device, 'force_range', fallback="1"))
        diff = int(config.get(device, 'forceh', fallback="1"))

        for extra in table:
            if count == diff:
                if extra not in table2:
                    table2.append(extra)
                    if range > 1:
                        index = table.index(extra)
                        a = 1
                        while a != range and index + a < len(table):
                            table2.append(table[index + a])
                            a = a + 1
                            nhours = nhours - 1
                    nhours = nhours - 1
                count = 0
            count = count + 1

    table.sort(key=lambda x: x[1])  # Sort by price

    if nhours < 0:
        nhours = 0

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
            table2 = priceLimit(table2, device)
    table2.sort()
    return table2


def ehours(day, hours, adj, device):
    data = []
    table = []
    when = "tomorrow"
    skip = 0

    offset = 0
    if 1 <= hours <= 24:
        nhours = hours
    else:
        nhours = 0
    if day == 1:  # Today
        when = "today"
        basedate = datetime.datetime.now()
        xmlfile = "data/entsoe_today.xml"
    else:
        basedate = datetime.datetime.now() + datetime.timedelta(days=1)
        xmlfile = "data/entsoe_tomorrow.xml"
    start = basedate.replace(hour=0, minute=0, second=0, microsecond=0)
    ustart = start.timestamp()
    end = basedate.replace(hour=23, minute=0, second=0, microsecond=0)

    start = start + datetime.timedelta(hours=-(tz))
    end = end + datetime.timedelta(hours=-(tz))
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
                enddate = data.find("end").text
                startdate = dt.strptime(startdate, "%Y-%m-%dT%H:%M%z")
                startdate = int(startdate.timestamp())
                enddate = dt.strptime(enddate, "%Y-%m-%dT%H:%M%z")
                enddate = int(enddate.timestamp())
                if (ustart + aux.settime(tz) * 3600) >= startdate and (ustart + aux.settime(tz) * 3600) < enddate:
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
        pricedata = []
        periodlist = data.findAll("Period")

        for pr in periodlist:
            sday = (pr.find("start").text)
            sday = dt.strptime(sday, "%Y-%m-%dT%H:%M%z")
            points = pr.findAll("Point")
            for x in points:
                price = x.find('price.amount')
                price = float(price.text) / 10 * tax
                price = round(price, 2)
                pricedata.append((int(sday.timestamp()), price))
                sday = sday + datetime.timedelta(hours=1)

        need = 0

        for each in pricedata:
            if each[0] >= ustart:
                table.append(each)
                need = need + 1
            if need == 24:
                break

    except Exception as e:
        if int(day) == 2:
            return "error"
        aux.errorhandler("Hours: An exception occurred ", str(e), 2)  # --> catastrofic fail
        return "error"

    # Adding possible extra network cost per hour
    if config.get(device, 'networkoffset', fallback="n") == "y":
        tadd = []
        networkosvalue = config.get(device, 'networkosvalue', fallback="0:0")
        stringT = networkosvalue.split(",")

        addprice = {}
        for t in stringT:
            addprice[int(t.split(":")[0])] = t.split(":")[1]

        for each in table:
            if dt.fromtimestamp(each[0]).hour in addprice:
                tadd.append((each[0], round(float(each[1]) + float(addprice[dt.fromtimestamp(each[0]).hour]), 2)))
            else:
                tadd.append((each[0], each[1]))
        table = tadd
    #

    table2 = []

    # If force is used, add hours and remove those from needed hours to keep amount the same
    count = 1
    table.sort()

    if config.get(device, 'force', fallback="n") == "y":
        range = int(config.get(device, 'force_range', fallback="1"))
        diff = int(config.get(device, 'forceh', fallback="1"))

        for extra in table:
            if count == diff:
                if extra not in table2:
                    table2.append(extra)
                    if range > 1:
                        index = table.index(extra)
                        a = 1
                        while a != range and index + a < len(table):
                            table2.append(table[index + a])
                            a = a + 1
                            nhours = nhours - 1
                    nhours = nhours - 1
                count = 0
            count = count + 1

    table.sort(key=lambda x: x[1])  # Sort by price

    if nhours < 0:
        nhours = 0

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
        returnvalue = ehours(day, hours, adj, device)
        if returnvalue == "error" and entsoebackup == "y":
            return hoursJSON(day, hours, adj, device)
        else:
            return returnvalue
    else:
        return hoursJSON(day, hours, adj, device)


if __name__ == '__main__':
    #print((ehours(1, 24, 0, "Estä lämpö")))
    print((hoursJSON(1, 24, 0, "Estä lämpö")))
