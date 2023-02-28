#!/usr/bin/python3
import time
import sys
import pickle
import datetime
import configparser

import aux
import controller
import os
import schedulecreator
from aux import settime
from aux import errorhandler
from aux import infohandler

# All times handled in UTC!
schedule1 = {}
utime1 = []
errorCode = 0
config = configparser.ConfigParser()
currentchange = 30
nextchange = 30
devicestate = {}
allOff = 0
previousupdate = 0


abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Read config for various defaults
try:
    config.read('conf/devices.conf')
    tz = (int(config["DEFAULT"]["timezone"]))
    cron = config.get("DEFAULT", "cron", fallback="16")
except Exception as e:
    errorhandler("Config not found", e, 1)
    exit()
for device in config:
    if device != "DEFAULT":
        devicestate.update({device: 2})  # Default value for device state 2 = unknown


def reload():
    global schedule1
    global utime1
    utime1.clear()
    schedule1.clear()
    scheduleerr = 0
    infohandler("Clickclack: Getting new schedule")
    scheduleerr = schedulecreator.main()

    if scheduleerr == "error":
        while scheduleerr == "error":
            errorhandler("Clickclack: Schedule could not be created, running backup setting and wait for hour", 0,
                         0)  # --> Catastrofic fail
            controller.switch("backup", 0)
            time.sleep(3600)
            scheduleerr = schedulecreator.main()
    try:
        with open('data/schedule1.pkl', 'rb') as f:
            schedule1 = pickle.load(f)
            f.close()
    except Exception as y:
        errorhandler("Clickclack: Schedule file not found on reload, running backup setting and exiting", y, 0)
        # --> Catastrofic fail
        controller.switch("backup", 0)
        sys.exit()
    for utime in schedule1:
        utime1.append(utime)


def start():
    global schedule1
    global utime1
    global errorCode
    global currentchange
    global nextchange
    global devicestate
    global config
    global allOff
    global previousupdate

    # def inner function
    def init():
        global schedule1
        global utime1
        global errorCode
        global currentchange
        global nextchange
        global devicestate
        global allOff

        timenow = int(time.time())
        n = 0
        while n < len(utime1):  # Set current setting on startup
            if not utime1[n] > timenow and (utime1[n] + 3600) > timenow:  # One hour setting
                currentchange = int(utime1[n])
                infohandler("Init. This Update --> Schedule: " + datetime.datetime.utcfromtimestamp(
                    currentchange + settime(tz)).strftime('%H:%M (%Y-%m-%d)'))
                for each in schedule1[currentchange]:
                    if devicestate[each] == 0 or devicestate[each] == 2:
                        infohandler("Switch on " + str(each))  # Set stage device was off
                        controller.switch(each, 1)
                        devicestate[each] = 1
                    elif config.get(each, "repeat", fallback="y") == "y":  # Repeat requested
                        infohandler("Repeat on " + str(each))  # Set stage as repeat was on
                        controller.switch(each, 1)
                        devicestate[each] = 1
                    else:
                        infohandler("Stays on " + str(each))  # Device was on and command not repeated
                    allOff = 0

                for each in config:
                    if each not in schedule1[currentchange] and each != "DEFAULT":  # Devices to set off
                        if devicestate[each] == 1 or devicestate[each] == 2:
                            controller.switch(each, 0)
                            devicestate[each] = 0
                            infohandler("Switch off " + str(each))  # Set stage off
                        elif config.get(each, "repeat", fallback="y") == "y":
                            infohandler("Repeat off " + str(each))  # Set stage as repeat was on
                            controller.switch(each, 0)
                            devicestate[each] = 0
                        else:
                            infohandler("Stays off " + str(each))  # Device was on and command not repeated
                if n == (len(utime1) - 1):  # Set next change on startup
                    errorhandler("Clickclack: No next schedule found on init", 0, 0)
                else:
                    nextchange = int(utime1[n + 1])

            n = n + 1

        if currentchange == 30:  # Current change was not found, assume all Off
            infohandler("Initial Update: All off. --> Time now: " +
                        datetime.datetime.utcfromtimestamp(time.time() + settime(tz)).strftime('%H:%M (%Y-%m-%d)'))
            currentchange = timenow
            for each in config:
                if each == "DEFAULT":
                    continue
                elif devicestate[each] == 1 or devicestate[each] == 2:
                    infohandler("Switch off " + str(each))  # Set stage device was off
                    controller.switch(each, 0)
                    devicestate[each] = 0
                elif config.get(each, "repeat", fallback="y") == "y":
                    infohandler("Repeat off " + str(each))  # Set stage as repeat was on
                    controller.switch(each, 0)
                    devicestate[each] = 0
                else:
                    infohandler("Stays off " + str(each))  # Device was on and command not repeated
            devicestate = devicestate.fromkeys(devicestate, 0)  # Set all device states to 0
            infohandler("All off")  # Set stage
            allOff = 1

            for next in utime1:  # Set next change on startup based on time
                if next > currentchange:
                    nextchange = next
                    break

        if nextchange == 30:  # Next change not found
            for next in utime1:  # Set next change on startup based on time
                if next > currentchange:
                    nextchange = next
                    break
            if nextchange == 30:  # Next change not found
                infohandler("Init. Something is wrong, next setup not found!")
                errorhandler("Clickclack: Schedule not found for future setting in init", 0, 0)

        else:
            infohandler("Init. Next Update, --> Schedule: " + datetime.datetime.utcfromtimestamp(
                nextchange + settime(tz)).strftime('%H:%M'))
            infohandler("Switch on " + str(schedule1[nextchange]))

    init()

    while True:
        if nextchange <= int(time.time()) and int(time.time()) < (nextchange + 3600):
            infohandler("This Update -> Time now:" + datetime.datetime.utcfromtimestamp(
                time.time() + settime(tz)).strftime('%H:%M (%Y-%m-%d)') + " Scheduled: "
                        + datetime.datetime.utcfromtimestamp(nextchange + settime(tz)).strftime('%H:%M (%Y-%m-%d)'))
            for each in schedule1[nextchange]:
                if devicestate[each] == 0 or devicestate[each] == 2:
                    infohandler("Switch on " + str(each))  # Set stage device was off
                    controller.switch(each, 1)
                    devicestate[each] = 1
                elif config.get(each, "repeat", fallback="y") == "y":
                    infohandler("Repeat on " + str(each))  # Set stage as repeat was on
                    controller.switch(each, 1)
                    devicestate[each] = 1
                else:
                    infohandler("Stays on " + str(each))  # Device was on and command not repeated
            for each in config:
                if each not in schedule1[nextchange] and each != "DEFAULT":  # Devices to set off
                    if devicestate[each] == 1 or devicestate[each] == 2:
                        controller.switch(each, 0)
                        devicestate[each] = 0
                        infohandler("Switch off " + str(each))  # Set stage off
                    elif config.get(each, "repeat", fallback="y") == "y":
                        infohandler("Repeat off " + str(each))  # Set stage as repeat was on
                        controller.switch(each, 0)
                        devicestate[each] = 0
                    else:
                        infohandler("Stays off " + str(each))  # Device was on and command not repeated

            currentchange = nextchange
            allOff = 0
            for next in utime1:
                nextchange = 30  # If next time is not found, variable stays in 30
                if next > currentchange:
                    nextchange = next
                    errorCode = 0
                    infohandler("Next Update --> Time now: " + datetime.datetime.utcfromtimestamp(
                        time.time() + settime(tz)).strftime('%H:%M') + " Scheduled: "
                                + datetime.datetime.utcfromtimestamp(nextchange + settime(tz)).strftime('%H:%M'))
                    break
        elif int(time.time()) > (currentchange + 3600) and allOff == 0:
            infohandler("This Update. --> " + datetime.datetime.utcfromtimestamp(
                time.time() + settime(tz)).strftime('%H:%M (%Y-%m-%d)'))
            for each in config:
                if each == "DEFAULT":
                    continue
                elif devicestate[each] == 1 or devicestate[each] == 2:
                    infohandler("Switch off " + str(each))  # Set stage device off
                    devicestate[each] = 0
                    controller.switch(each, 0)
                elif config.get(each, "repeat", fallback="y") == "y":
                    infohandler("Repeat off " + str(each))  # Set stage as repeat was on
                    controller.switch(each, 0)
                    devicestate[each] = 0
                else:
                    infohandler("Stays off " + str(each))  # Device was on and command not repeated
            devicestate = devicestate.fromkeys(devicestate, 0)  # Set all device states to zero
            infohandler("All off")  # Set stage
            allOff = 1

        if nextchange == 30:
            if errorCode != 0:  # We are here the second time, so init and schedulecreation has failed
                infohandler("Something is wrong, next schedule not found!")
                infohandler("Fallback to backup schedule.")
                errorhandler("Clickclack: New schedule creation has failed, "
                             "fallback too all backup and pause for 1h until fixed.", "none", 1)
                # Errorhandler on second time
                controller.switch("backup", 0)
                time.sleep(3600)
                reload()
                init()
                continue
            else:
                errorCode = 22  # Next change not found, try reloading all
                infohandler("Reloading schedule")
                reload()  # Time to get new schedule
                init()  # Inner function
                continue
        # Reload at set time
        elif int((datetime.datetime.utcfromtimestamp(time.time() + settime(tz)).strftime('%H'))) == int(cron):
            if previousupdate != (int((datetime.datetime.utcfromtimestamp(time.time() + settime(tz)).strftime('%d')))):
                aux.infohandler("Periodical schedule creation")
                reload()
                init()
                previousupdate = (int((datetime.datetime.utcfromtimestamp(time.time() + settime(tz)).strftime('%d'))))
                continue
        time.sleep(0.01)


reload()
start()
