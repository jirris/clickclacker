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
    errorhandler("Static: Config not found", e, 1)
    exit()


def load(device, day):
    infohandler("Load static schedule for " + str(device))
    print(createtimetables(device, day))


def createtimetables(device, day):
    # create unixtime timetables
    timetable = {}
    hour = 0
    devicefile = config[device]["static_file"]

    try:
        config.read(devicefile)
    except Exception as e:
        errorhandler("Static: Static config for device not found", e, 1)
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
            errorhandler("Static: Static config for device not correct", e, 1)
            break
        hour = hour + 1

    return timetable
