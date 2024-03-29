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

def settingspage():
    config = configparser.ConfigParser()
    try:
        config.read('conf/devices.conf')
    except Exception as e:
        aux.errorhandler("Config not found on publisher", e, 2)
        sys.exit()
    css = "table, th, td {" \
          "border: 1px solid black;" \
          "border-collapse: collapse;" \
          "border-color: #96D4D4;}"

    html =  "<!DOCTYPE HTML><html lang=\"fi\"><head><title>Clickclack settings</title></head><style>" + css + "</style><body><form method=\"post\"><table border=\"3\" class=\"dataframe\">\n"

    for each in config:
        html = html + "<tr><td colspan=\"2\"><br/></td></tr><th colspan=\"2\"><u><b>" + each + "</b></u></th>\n"
        for set in config[each]:
            try:
                if config["DEFAULT"][set] != config[each][set]:
                    html = html + "<tr><td>" + str(set) + "</td><td><input size=\"50\" type=\"text\" id=\"" + str(each + "." + set) + "\" name=\"" + str(each + "." + set) + "\" value=\"" + str(config[each][set]) + "\"/></td></tr>\n"
                else:
                    if each == "DEFAULT":
                        html = html + "<tr><td>" + str(set) + "</td><td><input size=\"50\" type=\"text\" id=\"" + str(each + "." + set) + "\" name=\"" + str(each + "." + set) + "\" value=\"" + str(config[each][set]) + "\"/></td></tr>\n"
            except:
                html = html + "<tr><td>" + str(set) + "</td><td><input size=\"50\" type=\"text\" id=\"" + str(each + "." + set) + "\" name=\"" + str(each + "." + set) + "\" value=\"" + str(config[each][set]) + "\"/></td></tr>\n"

    html = html + "</table><br/><input name=\"action\" type=\"submit\" value=\"SAVE\"></form></body></html>"

    try:
        f = open("webedit/templates/settings.html", "w")
        f.write(html)
        f.close()
    except Exception as e:
        aux.errorhandler("File write failed", str(e), 2)
        return 0



def webpage2(table):
    columns = int((len(table[0]) - 1) / 2 + 1)  # Remove header and add one per table
    rows = len(table)
    if rows == 0 or columns < 13:
        aux.errorhandler("Webpage cannot be created due lack of data", "none", 0)
        return 1

    # read CSS
    try:
        f = open("webedit/header", "r")
        header = f.read()
        f.close()
    except Exception as e:
        aux.errorhandler("Template file read failed", str(e), 2)
        return 0

    prevdate = ""
    cellnr = -1
    firstrow = []
    counter = 24
    nextday = "Not set"

    # Create header row and pickup dates
    for cell in table[0]:
        if counter == 0:
            if cell != "-":
                nextday = (cell[8:10] + '.' + cell[5:7] + "." + cell[:4])
            break
        cellnr = cellnr + 1
        dat = cell[:10]
        if "Devices" in cell:
            continue
        elif dat == prevdate:
            firstrow.append(cell[11:13])
        else:
            firstrow.append(cell[8:10] + '.' + cell[5:7] + "." + cell[:4])
            firstrow.append(cell[11:13])
        prevdate = dat
        counter = counter - 1

    midsec = ".parent { \n" \
             "display: grid;\n" \
             "grid-template-columns: repeat(" + str(columns) + ", 1fr);\n" \
             "grid-template-rows: repeat(" + str(rows * 2) + ", 1fr);\n" \
             "grid-column-gap: 0px;\n" \
             "grid-row-gap: 10px;\n" \
             "}\n"

    html = header + midsec
    html = html + '   </style>\n </head>\n <body>\n<form method=\"post\">\n<div class=\"parent\">\n'

    divnr = 1
    first = 0
    counter = 25

    for each in firstrow:
        counter = counter - 1
        if first == 0:
            html = html + '<div class=\"date\">' + each + '</div>\n'
            first = 1
        else:
            html = html + '<div class=\"div' + str(divnr) + '\">' + each + '</div>\n'
        divnr = divnr + 1
        if counter == 0:
            break

    rownr = 0

    for row in table:
        if rownr == 0:
            rownr = rownr + 1
            continue
        hour = 0
        s = ""
        counter = columns
        #counter = 25

        for cell in row:
            counter = counter - 1
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
                html = html + '<div class=\"devices\">' + cell + ' </div>\n'
            divnr = divnr + 1
            hour = hour + 1
            if counter == 0:
                break

    # Block
    counter = 25
    counter = columns
    first = 0
    if nextday != "Not set":
        while counter != 0:
            if first == 0:
                html = html + "<div class=\"date\">" + nextday + "</div>\n"
                first = 1
            else:
                html = html + "<div class=\"div" + str(divnr) + "\"></div>\n"
            counter = counter - 1
            divnr = divnr + 1

        rownr = 0

        # Second table
        for row in table:
            if rownr == 0:
                rownr = rownr + 1
                continue

            hour = 25
            counter = 24
            html = html + '<div class=\"devices\">' + row[0] + ' </div>\n'
            for cell in row[25:]:
                counter = counter - 1
                s = table[0][hour]
                s = time.mktime(datetime.strptime(s, "%Y-%m-%d %H:%M").timetuple())  # 2023-03-01 08:00
                s = str(int(s)) + "_" + row[0]
                if "off " in cell:
                    price = cell.split(" ")[1]
                    html = html + '<div class=\"div' + str(divnr) + '\">' \
                        '<label class=\"switch switch-yes-no\"><input class=\"switch-input\" ' \
                        'type=\"checkbox\" name=\"' + s + '\"/>' \
                        '<span class=\"switch-handle\"></span><span class=\"switch-label\" data-on=\"' + price + '\" data-off=\"' + price + '\"></span> ' \
                        '</label></div>\n'
                elif "on " in cell:
                    price = cell.split(" ")[1]
                    html = html + '<div class=\"div' + str(divnr) + '\">' \
                        '<label class=\"switch switch-yes-no\"><input class=\"switch-input\" ' \
                        'type=\"checkbox\" name=\"' + s + '\" checked/>' \
                        '<span class=\"switch-handle\"></span><span class=\"switch-label\" data-on=\"' + price + '\" data-off=\"' + price + '\"></span> ' \
                        '</label></div>\n'

                divnr = divnr + 1
                hour = hour + 1

    config = configparser.ConfigParser()
    try:
        config.read('conf/devices.conf')
        soldevices = ""
        for each in config:
            if config.get(each, "solaronly", fallback="n").lower() == "y":
                currentM = datetime.today().strftime("%-m")
                listM = config.get(each, "solaronlymonths", fallback=0)
                if currentM in listM:
                    soldevices = soldevices + "," + each

    except Exception as e:
        aux.errorhandler("Config not found on publisher", e, 2)
        soldevices = ""
        pass

    if len(soldevices) > 1:
        html = html + '</div><br/><b>Devices: ' + soldevices[1:] + ' overrided with sun power.</b><br>\n<input style=\"background-color: #32B532;\" type=\"submit\" value=\"Save\" name=\"action\">' \
                      '<br><input style=\"background-color: #F7CA00;\" type=\"submit\" value=\"Regenerate\" name=\"action\"/>\n</form>\n' \
                      '<form><input type=\"submit\" name=\"reload\" value=\"Reload\"></form></body>\n</html>'
    else:
        html = html + '</div><br>\n<input style=\"background-color: #32B532;\" type=\"submit\" value=\"Save\" name=\"action\">' \
                      '<br><input style=\"background-color: #F7CA00;\" type=\"submit\" value=\"Regenerate\" name=\"action\"/>\n</form>\n' \
                      '<form><input type=\"submit\" name=\"reload\" value=\"Reload\"></form></body>\n</html>'
    try:
        f = open("webedit/templates/web.html", "w")
        f.write(html)
        f.close()
    except Exception as e:
        aux.errorhandler("File write failed", str(e), 2)
        return 0

def htmlcreator(table):
    html = '<!DOCTYPE html><html lang="en"><head><title>ClickClack schedule</title></head><table border=\"1\" class=\"dataframe\"><thead><tr style=\"text-align: right;\">' + '\n'
    html2 = '<table border=\"1\" class=\"dataframe\"><thead><tr style=\"text-align: right;\">' + '\n'
    prevdate = ""
    # print(cell[8:10] + '.' + cell[5:7] + cell[10:]

    tablecount = 0

    for cell in table[0]:
        dat = cell[:10]
        if cell == "Devices":
            html = html + '<th>' + cell + '</th>'
            html2 = html2 + '<th>' + cell + '</th>'
        elif dat == prevdate:
            if tablecount == 1:
                html = html + '<th>' + cell[10:13] + '</th>'
            elif tablecount == 2:
                if cell == "-":
                    html2 = html2 + '<th>' + cell + '</th>'
                else:
                    html2 = html2 + '<th>' + cell[10:13] + '</th>'
        else:
            if tablecount == 0:
                html = html + '<th>' + cell[8:10] + '.' + cell[5:7] + cell[10:] + '</th>'
                tablecount = 1
            else:
                html2 = html2 + '<th>' + cell[8:10] + '.' + cell[5:7] + cell[10:] + '</th>'
                tablecount = 2
        prevdate = dat
    html = html + '</tr></thead><tbody>' + '\n'
    html2 = html2 + '</tr></thead><tbody>' + '\n'

    rownr = 0
    content = ""

    for row in table:
        cnr = 0
        if rownr == 0:
            rownr = rownr + 1
            continue
        content = content + '<tr>'
        for cell in row:
            cnr = cnr + 1
            if cnr == 26:
                html = html + content + "</tr>" + '\n'
                content = ""
            if "off " in cell or "NA " in cell:
                content = content + '<td>' + cell + '</td>'
            elif "on " in cell:
                content = content + '<td bgcolor=\"green\">' + cell + '</td>'
            else:
                content = content + '<td>' + cell + '</td>'
                html2 = html2 + '<tr><td>' + cell + '</td>'
        html2 = html2 + content + '</tr>' + '\n'
        content = ""

    html = html + '</tbody></table>' + html2 + '</tbody></table>'

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

    first_hour = datetime.fromtimestamp(time).hour
    headerrow = ["Devices"]

    while first_hour != 0:
        correcttime = schedule_first - 3600
        headerrow.append(correcttime)
        first_hour = first_hour - 1


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

    lastitem = 0
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
            yesterdaycsv = "log/history/" + str(yesterday) + ".csv"
            yesterdayhtml = "log/history/" + str(yesterday) + ".html"
            shutil.copy("data/schedule.csv", yesterdaycsv)
            shutil.copy("data/schedule.html", yesterdayhtml)
        except Exception as e:
            aux.errorhandler("CSV/HTML history write failed", e, 1)

    if len(table[0]) != 49:
        tlen = len(table[0])
        while tlen != 49:
            table[0].append("-")
            tlen = tlen + 1
    webpage2(table)
    htmlcreator(table)

    try:
        f = open("data/schedule.csv", "w")
        f.write(csv)
        f.close()

        aux.infohandler("CSV written to data/schedule.csv")
    except Exception as e:
        aux.errorhandler("File write failed", str(e), 1)
        return 0

if __name__ == '__main__':
    pass
    #settingspage()