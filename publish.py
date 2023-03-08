from datetime import datetime, timedelta, date
import time
import os
import aux
import sys
import configparser
import shutil

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def webpage(table):
    columns = len(table[0])
    rows = len(table)
    try:
        f = open("webedit/templates/header", "r")
        header = f.read()
        f.close()
    except Exception as e:
        aux.errorhandler("Template file read failed", str(e), 2)
        return 0

    prevdate = ""
    cellnr = -1
    firstrow = []

    for cell in table[0]:
        cellnr = cellnr + 1
        dat = cell[:10]
        if "Devices" in cell:
            firstrow.append(cell)
        elif dat == prevdate:
            firstrow.append(cell[11:13])
        else:
            firstrow.append(cell[8:10] + '.' + cell[5:7] + cell[10:])
        prevdate = dat

    midsec = "grid-template-columns: repeat(" + str(columns) + ", 1fr);\n" \
             "grid-template-rows: repeat(" + str(rows) + ", 1fr);\n" \
             "grid-column-gap: 0px;\n" \
             "grid-row-gap: 0px;\n" \
             "}\n" \
             "div {border-left: solid;}\n" \
             "div {border-top: solid;}\n"
    divr = 0
    css = ""
    divnr = 1

    while divr != rows:
        divr = divr + 1
        divc = 0
        while divc != columns:
            divc = divc + 1
            css = css + ".div" + str(divnr) + " { grid-area: " + str(divr) + " / " + str(divc) + " / " + str(divr + 1) \
                  + " / " + str(divc + 1) + "; }\n"
            divnr = divnr + 1


    html = header + midsec + css

    html = html + '   </style>\n </head>\n <body>\n<form method=\"post\">\n<div class=\"parent\">\n'

    divnr = 1

    for each in firstrow:
        html = html + '<div class=\"div' + str(divnr) + '\">' + each + '</div>\n'
        divnr = divnr + 1

    rownr = 0

    for row in table:
        if rownr == 0:
            rownr = rownr + 1
            continue
        hour = 0
        s = ""

        for cell in row:
            if hour != 0:
                s = table[0][hour]
                s = time.mktime(datetime.strptime(s, "%Y-%m-%d %H:%M").timetuple())  # 2023-03-01 08:00
                s = str(int(s)) + "_" + row[0]
            if "off " in cell:
                price = cell.split(" ")[1]
                html = html + '<div class=\"div' + str(divnr) + '\">' \
                            '<label class=\"switch switch-yes-no\"><input class=\"switch-input\" type=\"checkbox\" name=\"' + s + '\"/>' \
                            '<span class=\"switch-handle\"></span><span class=\"switch-label\" data-on=\"' + price + '\" data-off=\"' + price + '\"></span> ' \
                            '</label></div>\n'
            elif "on " in cell:
                price = cell.split(" ")[1]
                html = html + '<div class=\"div' + str(divnr) + '\">' \
                            '<label class=\"switch switch-yes-no\"><input class=\"switch-input\" type=\"checkbox\" name=\"' + s + '\" checked/>' \
                            '<span class=\"switch-handle\"></span><span class=\"switch-label\" data-on=\"' + price + '\" data-off=\"' + price + '\"></span> ' \
                            '</label></div>\n'
            else:
                html = html + '<div class=\"div' + str(divnr) + '\">' + cell + ' </div>\n'
            divnr = divnr + 1
            hour = hour + 1
    html = html + '</div>\n<input type=\"submit\" value=\"save\" name=\"action\">' \
                  '<input type=\"submit\" value=\"reload\" name=\"action\"/>\n</form>\n</body>\n</html>'

    try:
        f = open("webedit/templates/web.html", "w")
        f.write(html)
        f.close()
    except Exception as e:
        aux.errorhandler("File write failed", str(e), 2)
        return 0

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
    html = html + '</tr></thead><tbody><tr>'

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
        aux.errorhandler("File write failed", str(e), 2)
        return 0


def csvcreator(schedule1, pricelist):
    config = configparser.ConfigParser()

    try:
        config.read('conf/devices.conf')
    except Exception as e:
        aux.errorhandler("Config not found on publisher", e, 2)
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

    missing = 0

    if len(headerrow) < 25:
        missing = 25
    elif len(headerrow) < 49:
        missing = 49

    while len(headerrow) < missing:
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
        lastitem = ut
    try:
        f = open("data/last", "w")
        f.write(str(lastitem))
        f.close()
    except Exception:
        pass

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

    webpage(table)
    htmlcreator(table)



    try:
        f = open("data/schedule.csv", "w")
        f.write(csv)
        f.close()

        aux.infohandler("CSV written to data/schedule.csv")
    except Exception as e:
        aux.errorhandler("File write failed", str(e), 1)
        return 0
