import configparser
import datetime
import os
import time

from aux import infohandler
from aux import errorhandler


abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

config = configparser.ConfigParser()

# Read config for various defaults
try:
    config.read('conf/devices.conf')
except Exception as e:
    errorhandler("Static: Config not found", e, 2)
    exit()

def createtimetablesOld(device, day):
    # create unixtime timetables
    timetable = {}
    hour = 0
    devicefile = config[device]["static_file"]

    infohandler("Load static schedule for " + str(device))

    try:
        config.read(devicefile)
    except Exception as e:
        errorhandler("Static: Static config for device not found", e, 2)
        exit()
    if day == 0:  # Today
        basedate = datetime.datetime.now()
    else:
        basedate = datetime.datetime.now() + datetime.timedelta(days=1)

    while hour < 24:
        basedate = basedate.replace(hour=hour, minute=0, second=0, microsecond=0)
        Utime = (int(time.mktime(basedate.timetuple())))
        try:
            if int(config[device][str(hour)]) == 1:
                timetable.update({int(Utime): device})
        except KeyError as e:
            errorhandler("Static: Static config for device not correct", e, 2)
            break
        hour = hour + 1

    return timetable


def createtimetables(device, day):
    # create unixtime timetables
    timetable = {}
    hour = 0

    infohandler("Load static schedule for " + str(device))

    try:
        deviceschedule = config[device]["static_sche"]
    except Exception as e:
        errorhandler("Static: Static config for device not found", e, 2)
        exit()
    if day == 0:  # Today
        basedate = datetime.datetime.now()
    else:
        basedate = datetime.datetime.now() + datetime.timedelta(days=1)


    deviceschedule = deviceschedule.replace(" ", "")
    deviceschedule = deviceschedule.split(",")
    schedule = []

    for digit in deviceschedule:
        try:
            int(digit)
            if int(digit) < 24 and int(digit) >= 0:
                schedule.append(int(digit))
        except ValueError as x:
            errorhandler("Static schedule value error on " + device, x, 1)
            continue

    if day == 0:  # Today
        basedate = datetime.datetime.now()
    else:
        basedate = datetime.datetime.now() + datetime.timedelta(days=1)

    while hour < 24:
        basedate = basedate.replace(hour=hour, minute=0, second=0, microsecond=0)
        Utime = (int(time.mktime(basedate.timetuple())))
        if hour in schedule:
            timetable.update({int(Utime): device})
        hour = hour + 1

    return timetable



if __name__ == '__main__':
    print(createtimetables("Car charger", 1))
    print(createtimetablesOld("Car charger", 1))