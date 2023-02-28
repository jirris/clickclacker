#!/usr/bin/python3
import configparser
import aux
import hours
import pickle
import os
import sys
import static
from datetime import datetime
from aux import settime
from aux import errorhandler
from aux import infohandler
from aux import messagehandler
from aux import sendhtml

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

config = configparser.ConfigParser()
tempfile = configparser.ConfigParser()
windfile = configparser.ConfigParser()

# schedule1 = {}  # Today (for history)


def tempcurve(device, day):  # Calculate needed hours based on the average temperature per day
    # Change to Kelvins
    K = 273
    try:
        min_temp = int(config[device]["min_temp"]) + K
        mid_temp = int(config[device]["mid_temp"]) + K
        max_temp = int(config[device]["max_temp"]) + K
        min_hours = int(config[device]["min_hours"])
        mid_hours = int(config[device]["mid_hours"])
        max_hours = int(config[device]["max_hours"])
        curveW = (mid_hours - min_hours) / (mid_temp - min_temp)  # Slope for below 0C
        curveS = (max_hours - mid_hours) / (max_temp - mid_temp)  # Slope for above 0C
        temperatureTuple = averageT(device)
    except Exception as e:
        aux.errorhandler("Configuration error", e, 1)
        return 0

    if temperatureTuple is None:
        return int(config[device]["hours"])

    if day == 0:
        # Today
        avgtemperature = temperatureTuple[0] + K
    else:
        # Tomorrow
        avgtemperature = temperatureTuple[1] + K

    hoursS = mid_hours + (avgtemperature-mid_temp) * curveS
    hoursW = mid_hours + (avgtemperature-mid_temp) * curveW

    if avgtemperature < min_temp:
        hoursW = min_hours
    if avgtemperature > max_temp:
        hoursS = max_hours

    if avgtemperature > mid_temp:
        return hoursS
    else:
        return hoursW


def windcurve(device, day, temperature):  # Adds windchill factor by calculating speed (in m/s) times chill factor
    try:
        wind_file = config["DEFAULT"]["wind_file"]
        cutoff_temp = int(config[device]["cutoff_chill"])
    except Exception as e:
        aux.errorhandler("Configuration error", e, 1)
        return 0

    if temperature is None:  # No average temperature got
        return 0

    if cutoff_temp <= temperature:  # Wind compensation not done
        return 0

    try:
        windfile.read(wind_file)
        if day == 0:
            # Today
            if windfile["wind"]["today_dir"] == "" or windfile["wind"]["today_spd"] == "":
                raise Exception
            windD = (windfile["wind"]["today_dir"])
            windS = float(windfile["wind"]["today_spd"])
        else:
            # Tomorrow
            if windfile["wind"]["tomorrow_dir"] == "" or windfile["wind"]["tomorrow_spd"] == "":
                raise Exception
            windD = (windfile["wind"]["tomorrow_dir"])
            windS = float(windfile["wind"]["tomorrow_spd"])
    except Exception as e:
        errorhandler("Wind file not found, default to no adjustment", e, 0)
        return 0
    wind = 0

    try:
        if windD == "n":
            wind = int(config[device]["n_chill"])
        if windD == "nw":
            wind = int(config[device]["nw_chill"])
        if windD == "w":
            wind = int(config[device]["w_chill"])
        if windD == "sw":
            wind = int(config[device]["sw_chill"])
        if windD == "s":
            wind = int(config[device]["s_chill"])
        if windD == "se":
            wind = int(config[device]["se_chill"])
        if windD == "e":
            wind = int(config[device]["e_chill"])
        if windD == "ne":
            wind = int(config[device]["ne_chill"])
        chillfactor = windS/5 * wind
    except Exception as e:
        aux.errorhandler("Configuration error", e, 1)
        return 0

    if chillfactor < 0:
        return chillfactor
    else:
        return 0


def averageT(device):
    try:
        temp_file = config["DEFAULT"]["temp_file"]
        tempfile.read(temp_file)
        # Today
        if tempfile["temperature"]["today"] == "":
            raise Exception
        today = float(tempfile["temperature"]["today"])
        # Tomorrow
        if tempfile["temperature"]["tomorrow"] == "":
            raise Exception
        tomorrow = float(tempfile["temperature"]["tomorrow"])
        if config[device]["adj_chill"] == "y":
            today = today + windcurve(device, 0, today)
            tomorrow = tomorrow + windcurve(device, 1, tomorrow)
    except Exception as e:
        errorhandler("Temperature file not found, default to no adjustment", e, 0)
        return None
    return today, tomorrow


# Main
def main():
    schedule1 = {}
    try:
        config.read('conf/devices.conf')
        tz = (int(config["DEFAULT"]["timezone"]))
    except Exception as e:
        errorhandler("Config not found on scheduler", e, 0)
        sys.exit()

    if config["DEFAULT"]["fetch"] == "y":  # Run script to get new pricelist and weatherdata
        command = config["DEFAULT"]["fetch_command"]
        if not os.path.isfile(command):
            errorhandler("Schedulecreator, script to run not found", command, 0)
        else:
            os.system(command)

    for device in config:
        if device == "DEFAULT":
            continue
        if config.get(device, 'static', fallback="n") == "n":
            if config.get(device, 'adj_temp', fallback="n") == "y":
                weatheradjH_TD = tempcurve(device, 0)
                weatheradjH_TM = tempcurve(device, 1)
            else:
                weatheradjH_TD = int(config[device]["hours"])
                weatheradjH_TM = int(config[device]["hours"])
            adj = 0
            if config.get(device, 'pricelimit', fallback="n") == "y":
                aux.infohandler("Schedule for " + device + " will be price adjusted")
                adj = 1

            if int(weatheradjH_TD) != 0:
                onhours1 = (hours.hours(1, int(weatheradjH_TD), adj, device))  # Today
            else:
                onhours1 = []
            if int(weatheradjH_TM) != 0:
                onhours2 = (hours.hours(2, int(weatheradjH_TM), adj, device))  # Tomorrow
            else:
                onhours2 = []

            if onhours1 != "error":
                infohandler("Device total on hours today:")
                infohandler(device + ": " + str(len(onhours1)) + "h")

                if onhours2 != "error":
                    infohandler("Tomorrow")
                    infohandler(device + ": " + str(len(onhours2)) + "h")
                    infohandler("------")

            if onhours1 == "error":
                aux.errorhandler("Schedulecreator: No new price information got today", 0, 1)
                return "error"
            else:
                for hour in onhours1:
                    if hour[0] not in schedule1:
                        schedule1.update({int(hour[0]): []})
                    if device not in schedule1[hour[0]]:
                        schedule1[hour[0]].append(device)
            if onhours2 == "error":
                aux.errorhandler("Schedulecreator: No new price information got for tomorrow for " + device, 0, 1)
            else:
                for hour in onhours2:
                    if hour[0] not in schedule1:
                        schedule1.update({int(hour[0]): []})
                    if device not in schedule1[hour[0]]:
                        schedule1[hour[0]].append(device)
        else:
            staticTD = static.createtimetables(device, 0)
            staticTM = static.createtimetables(device, 1)

            if config.get(device, 'pricelimit', fallback="n") == "y":
                aux.infohandler("Schedule for " + device + " will be price adjusted")
                # Add cheap hours
                if config.get(device, 'lowerlimit', fallback="n") != "n":
                    addhoursTD = (hours.hours(1, 0, 1, device))  # Get cheap hours
                    addhoursTM = (hours.hours(2, 0, 1, device))

                    if addhoursTD != "error":
                        for each in addhoursTD:
                            if each[0] not in staticTD:
                                staticTD.update({int(each[0]): device})

                    if addhoursTM != "error":
                        for each in addhoursTM:
                            if each[0] not in staticTM:
                                staticTM.update({int(each[0]): device})

                # remove expensive hours
                if config.get(device, 'upperlimit', fallback="n") != "n":
                    delhoursTD = (hours.hours(1, 24, 1, device))  # Get all expensive hours inverted
                    delhoursTM = (hours.hours(2, 24, 1, device))

                    helperlist = []
                    croppeddic = {}
                    if delhoursTD != "error":
                        for each in delhoursTD:  # Change to array
                            helperlist.append(each[0])

                        for each in staticTD:
                            if each in helperlist:
                                croppeddic.update({int(each): staticTD[each]})
                        staticTD = croppeddic

                    helperlist = []
                    croppeddic = {}
                    if delhoursTM != "error":
                        for each in delhoursTM:  # Change to array
                            helperlist.append(each[0])

                        for each in staticTM:
                            if each in helperlist:
                                croppeddic.update({int(each): staticTM[each]})
                        staticTM = croppeddic

            for each in staticTD:
                if each not in schedule1:
                    schedule1.update({int(each): []})
                if device not in schedule1[each]:
                    schedule1[each].append(device)
            for each in staticTM:
                if each not in schedule1:
                    schedule1.update({int(each): []})
                if device not in schedule1[each]:
                    schedule1[each].append(device)

            infohandler("Devices total on hours today:")
            infohandler(device + ": " + str(len(staticTD)) + "h")
            infohandler("Tomorrow")
            infohandler(device + ": " + str(len(staticTM)) + "h")
            infohandler("------")

    if len(schedule1) < 1:
        errorhandler("Schdedulecreator: Schedule empty after creation", 0, 0)

    hrsched = ""
    price = "Unknown"

    pricelist = hours.hours(1, 24, 0, "DEFAULT")  # Get price information
    pricelist2 = hours.hours(2, 24, 0, "DEFAULT")

    if not isinstance(pricelist2, str):
        pricelist = pricelist + pricelist2

    # Sort hours, annoying dic....
    dkeys = list(schedule1.keys())
    dkeys.sort()
    temp_schedule = {i: schedule1[i] for i in dkeys}

    for key in temp_schedule:   # This moments settings
        t = datetime.utcfromtimestamp(key + settime(tz))
        t = t.strftime('%Y-%m-%d %H:%M:%S %Z')
        for each in pricelist:
            if (int(each[0])) == int(key):
                price = each[1]
                break
            else:
                price = "Unknown"

        hrsched = hrsched + (str(t) + "--> ON:\t" + str(temp_schedule[key]) + "  Price: " + str(price) + "\n")

    import publish
    publish.csvcreator(temp_schedule, pricelist)

    if config.get('DEFAULT', 'html', fallback="n") == "y":
        sendhtml()
        messagehandler(hrsched)
    else:
        messagehandler(hrsched)

    try:
        if os.path.exists('data/schedule1.pkl'):
            os.remove('data/schedule1.pkl')
        with open('data/schedule1.pkl', 'wb') as f:  # Full schedule
            pickle.dump(temp_schedule, f)
            f.close()
    except Exception as e:
        errorhandler("Schedule file write failed", e, 0)


if __name__ == '__main__':
    main()
