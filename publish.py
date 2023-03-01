from datetime import datetime, timedelta, date
import os
import aux
import sys
import configparser
import shutil

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


def htmlcreator(table):
    html = '<table border=\"1\" class=\"dataframe\"><thead><tr style=\"text-align: right;\">'
    prevdate = ""
    # print(cell[8:10] + '.' + cell[5:7] + cell[10:]

    for cell in table[0]:
        dat = cell[:10]
        if cell == "Devices":
            html = html + '<th>' + cell + '</th>'
        elif dat == prevdate:
            html = html + '<th>' + cell[10:13] + '</th>'
        else:
            html = html + '<th>' + cell[8:10] + '.' + cell[5:7] + cell[10:] + '</th>'
        prevdate = dat
    html = html + '</tr></thead><tbody>'

    rownr = 0

    for row in table:
        if rownr == 0:
            rownr = rownr + 1
            continue
        html = html + '<tr>'
        for cell in row:
            if "off " in cell:
                html = html + '<td>' + cell + '</td>'
            elif "on " in cell:
                html = html + '<td bgcolor=\"green\">' + cell + '</td>'
            else:
                html = html + '<td>' + cell + '</td>'
        html = html + '</tr>'

    html = html + '</tbody></table>'

    try:
        f = open("data/schedule.html", "w")
        f.write(html)
        f.close()
        aux.infohandler("HTML written to data/schedule.html")
    except Exception as e:
        aux.errorhandler("File write failed", str(e), 1)
        return 0


def csvcreator(schedule1, pricelist):
    config = configparser.ConfigParser()

    try:
        config.read('conf/devices.conf')
    except Exception as e:
        aux.errorhandler("Config not found on publisher", e, 0)
        sys.exit()

    dkeys = list(schedule1.keys())
    dkeys.sort()
    sorted_schedule = {i: schedule1[i] for i in dkeys}
    sorted_prices = sorted(pricelist)

    schedule_last = list(sorted_schedule)[-1]
    schedule_first = list(sorted_schedule)[0]
    time = schedule_first

    headerrow = ["Devices"]

    while time <= schedule_last:
        headerrow.append(time)
        time = time + 3600

    first_column = []

    for device in config:
        if device != "DEFAULT":
            first_column.append(device)

    table = [headerrow]

    for device in first_column:
        device_states = [device]
        for hour in headerrow:
            if hour == "Devices":
                continue
            state = "off"
            if hour in sorted_schedule:
                for each in sorted_schedule[hour]:
                    if each == device:
                        state = "on"
            price = "-"
            for tuplev in sorted_prices:
                if tuplev[0] == hour:
                    price = tuplev[1]

            device_states.append(state + " " + str(price))
        table.append(device_states)

    counter = 1
    for ut in table[0]:
        if ut == "Devices":
            continue
        table[0][counter] = datetime.fromtimestamp(int(ut)).strftime('%Y-%m-%d %H:%M')
        counter = counter + 1

    csv = ""

    for row in table:
        for cell in row:
            csv = csv + str(cell) + ","
        csv = csv[:-1] + "\n"


    if config.get('DEFAULT', 'history', fallback="n") == "y":
        try:
            yesterday = date.today() - timedelta(days=1)
            yesterdaycsv = "data/history/" + str(yesterday) + ".csv"
            yesterdayhtml = "data/history/" + str(yesterday) + ".html"
            shutil.copy("data/schedule.csv", yesterdaycsv)
            shutil.copy("data/schedule.html", yesterdayhtml)
        except Exception as e:
            aux.errorhandler("CSV/HTML history write failed", e, 1)

    htmlcreator(table)

    try:
        f = open("data/schedule.csv", "w")
        f.write(csv)
        f.close()

        aux.infohandler("CSV written to data/schedule.csv")
    except Exception as e:
        aux.errorhandler("File write failed", str(e), 1)
        return 0
