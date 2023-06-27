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
from aux import errorhandler
from aux import infohandler

schedule1 = {}
utime1 = []
errorcode = 0
config = configparser.ConfigParser()
currentchange = 30
nextchange = 30
devicestate = {}
allOff = 0
previousupdate = 0
changeorigin = ""
solstate = {}
solcheckon = 0


abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Read config for various defaults
try:
    config.read('conf/devices.conf')
    cron = int(config.get("DEFAULT", "cron", fallback="16"))
    # Set if we do solar wattage checking
    for each in config:
        if config.get(each, "solarwatt", fallback="n") == "y":
            solcheckon = 1
            solarwattfile = config.get(each, "solarwattfile", fallback="n")
except Exception as e:
    errorhandler("Config not found", e, 2)
    exit()
for device in config:
    if device != "DEFAULT":
        devicestate.update({device: 2})  # Default value for device state 2 = unknown

def switcher(dev, state):
    if not solstate:
        for each in devicestate:
            solstate[each] = "n"

    if state == 1:
        solaronly = config.get(dev, "solaronly", fallback="n").lower()
        if solaronly == "n":
            controller.switch(dev, state)
        else:
            currentM = datetime.datetime.today().strftime("%-m")
            listM = config.get(dev, "solaronlymonths", fallback=0)
            if currentM in listM:
                if solaronly == "s":
                    if config.get(dev, "static", fallback="n").lower() == "y":
                        controller.switch(dev, state)
                        aux.infohandler("Solaronly setting in use for " + dev + ", but override with static done.")
                else:
                    aux.infohandler("Solaronly setting in use " + dev + ", switch on overriden.")
            else:
                aux.infohandler("Solaronly setting in use " + dev + ", but not enabled this month.")
                controller.switch(dev, state)
    elif state == 0:
        if solstate[dev] == "n":
            controller.switch(dev, state)
        else:
            aux.infohandler("Solaronly setting in use " + dev + ", switch off overriden.")

def solcheck(devs, watts):
    global solstate

    if not solstate:
        for each in devs:
            solstate[each] = "n"

    for each in solstate:
        if config.get(each, "solarwatt", fallback="n").lower() == "y":
            if int(config.get(each, "solarwattlimit", fallback=-1)) != -1:
                if watts >= int(config.get(each, "solarwattlimit")):
                    if solstate[each] == "n":
                        if devs[each] != 1 or config.get(each, "solaronly", fallback="n").lower() == "y":
                            controller.switch(each, 1)
                            aux.infohandler("Solar power over threshold " + str(watts/10) + "W, switch on " + each)
                            aux.notifier("Solar power over threshold " + str(watts / 10) + "W, switch on " + each)
                    solstate[each] = time.time()
                elif solstate[each] != "n":
                    solwattminon = int(config.get(each, "solarminon", fallback='30'))
                    if solstate[each] + solwattminon * 60 < time.time():
                        solstate[each] = "n"
                        if devs[each] == 0 or config.get(each, "solaronly", fallback="n").lower() == "y": # add month
                            currentM = datetime.datetime.today().strftime("%-m")
                            listM = config.get(each, "solaronlymonths", fallback=0)
                            if currentM in listM:
                                controller.switch(each, 0)
                                aux.infohandler("Solar power under threshold " + str(watts/10) + "W, switch off " + each)
                                aux.notifier("Solar power under threshold " + str(watts / 10) + "W, switch off " + each)
                            else:
                                aux.infohandler("Solar power under threshold " + str(watts/10) + "W, but schedule is on " + each)
                                aux.notifier("Solar power under threshold " + str(watts / 10) + "W, sbut schedule is on " + each)
                    else:
                        pass
                        #aux.infohandler("Solar power under threshold " + str(watts) + ", keeping on for " + str(solwattminon) + " minutes")
                else:
                    solstate[each] = "n" # Never here

def reload():
    global schedule1
    global changeorigin

    infohandler("Clickclack: Getting new schedule")
    #scheduleerr = 0
    scheduleerr = schedulecreator.main()

    if scheduleerr == "error":
        while scheduleerr == "error":
            errorhandler("Clickclack: Schedule could not be created, running backup setting and wait for hour", 0, 2)
            # --> Catastrofic fail
            switcher("backup", 0)
            time.sleep(3600)
            scheduleerr = schedulecreator.main()

    schedule1.clear()

    try:
        with open('data/schedule1.pkl', 'rb') as f:
            schedule1 = pickle.load(f)
            f.close()
        changeorigin = "r"
    except Exception as y:
        errorhandler("Clickclack: Schedule file not found on reload, running backup setting and exiting", y, 2)
        # --> Catastrofic fail
        switcher("backup", 0)
        sys.exit()


def start():
    global schedule1, errorcode
    global utime1
    global currentchange
    global nextchange
    global devicestate
    global config
    global allOff
    global previousupdate
    global changeorigin
    global cron
    oldtime = 0
    sun_old = 0

    # def inner function
    def init():
        global schedule1
        global utime1
        global errorcode
        global currentchange
        global nextchange
        global devicestate
        global allOff

        #errorcode = 0
        currentchange = 30
        nextchange = 30
        allOff = 0

        utime1.clear()
        for utime in schedule1:
            utime1.append(utime)

        timenow = int(time.time())
        n = 0
        while n != len(utime1):  # Set current setting on startup
            if not utime1[n] > timenow and (utime1[n] + 3600) > timenow:  # One hour setting
                currentchange = int(utime1[n])
                infohandler("Init. This Update --> Schedule: " + datetime.datetime.fromtimestamp(
                    currentchange).strftime('%H:%M (%Y-%m-%d)'))
                for each in schedule1[currentchange]:
                    if devicestate[each] == 0 or devicestate[each] == 2:
                        infohandler("Switch on " + str(each))  # Set stage device was off
                        switcher(each, 1)
                        devicestate[each] = 1
                    elif devicestate[each] == 1 and config.get(each, "repeat", fallback="y") == "y":  # Repeat requested
                        infohandler("Repeat on " + str(each))  # Set stage as repeat was on
                        switcher(each, 1)
                        devicestate[each] = 1
                    elif devicestate[each] == 1:
                        infohandler("Stays on " + str(each))  # Device was on and command not repeated
                    allOff = 0

                for each in config:
                    if each not in schedule1[currentchange] and each != "DEFAULT":  # Devices to set off
                        if devicestate[each] == 1 or devicestate[each] == 2:
                            switcher(each, 0)
                            devicestate[each] = 0
                            infohandler("Switch off " + str(each))  # Set stage off
                        elif devicestate[each] == 0 and config.get(each, "repeat", fallback="y") == "y":
                            infohandler("Repeat off " + str(each))  # Set stage as repeat was on
                            switcher(each, 0)
                            devicestate[each] = 0
                        elif devicestate[each] == 0:
                            infohandler("Stays off " + str(each))  # Device was on and command not repeated
                if n == (len(utime1) - 1):  # Set next change on startup
                    errorhandler("Clickclack: No next schedule found on init", 0, 1)
                else:
                    nextchange = int(utime1[n + 1])
            n = n + 1

        if currentchange == 30:  # Current change was not found, assume all Off
            infohandler("Initial Update: All off. --> Time now: " +
                        datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M (%Y-%m-%d)'))
            currentchange = timenow
            for each in config:
                if each == "DEFAULT":
                    continue
                elif devicestate[each] == 1 or devicestate[each] == 2:
                    infohandler("Switch off " + str(each))  # Set stage device was off
                    switcher(each, 0)
                    devicestate[each] = 0
                elif config.get(each, "repeat", fallback="y") == "y":
                    infohandler("Repeat off " + str(each))  # Set stage as repeat was on
                    switcher(each, 0)
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
                if changeorigin != "w" and changeorigin != "f":
                    infohandler("Init. Something is wrong, next setup not found!")
                    errorhandler("Clickclack: Schedule not found for future setting in init", 0, 1)
                elif changeorigin == "w":
                    infohandler("Webchange was initiated, no next schedule found.")
                elif changeorigin == "f":
                    infohandler("Webchange was initiated, no next schedule found, fixed days.")
        else:
            infohandler("Init. Next Update, --> Schedule: " + datetime.datetime.fromtimestamp(
                nextchange).strftime('%H:%M'))
            infohandler("Switch on " + str(schedule1[nextchange]))
            errorcode = 0

    init()

    originalcron = cron
    cronchecked = "0"  # To avoid multiple file reads

    while True:
        if nextchange <= int(time.time()) and int(time.time()) < (nextchange + 3600):
            if nextchange not in schedule1:
                nextchange = 30
                errorcode = 24
                continue
            infohandler("This Update -> Time now:" + datetime.datetime.fromtimestamp(
                time.time()).strftime('%H:%M (%Y-%m-%d)') + " Scheduled: "
                        + datetime.datetime.fromtimestamp(nextchange).strftime('%H:%M (%Y-%m-%d)'))
            for each in schedule1[nextchange]:
                if devicestate[each] == 0 or devicestate[each] == 2:
                    infohandler("Switch on " + str(each))  # Set stage device was off
                    switcher(each, 1)
                    devicestate[each] = 1
                elif config.get(each, "repeat", fallback="y") == "y":
                    infohandler("Repeat on " + str(each))  # Set stage as repeat was on
                    switcher(each, 1)
                    devicestate[each] = 1
                else:
                    infohandler("Stays on " + str(each))  # Device was on and command not repeated
            for each in config:
                if each not in schedule1[nextchange] and each != "DEFAULT":  # Devices to set off
                    if devicestate[each] == 1 or devicestate[each] == 2:
                        switcher(each, 0)
                        devicestate[each] = 0
                        infohandler("Switch off " + str(each))  # Set stage off
                    elif config.get(each, "repeat", fallback="y") == "y":
                        infohandler("Repeat off " + str(each))  # Set stage as repeat was on
                        switcher(each, 0)
                        devicestate[each] = 0
                    else:
                        infohandler("Stays off " + str(each))  # Device was on and command not repeated

            currentchange = nextchange
            allOff = 0
            for next in utime1:
                nextchange = 30  # If next time is not found, variable stays in 30
                if next > currentchange:
                    nextchange = next
                    errorcode = 0
                    infohandler("Next Update --> Time now: " + datetime.datetime.fromtimestamp(
                        time.time()).strftime('%H:%M') + " Scheduled: "
                                + datetime.datetime.fromtimestamp(nextchange).strftime('%H:%M'))
                    break
        elif int(time.time()) > (currentchange + 3600) and allOff == 0:
            infohandler("This Update. --> " + datetime.datetime.fromtimestamp(
                time.time()).strftime('%H:%M (%Y-%m-%d)'))
            for each in config:
                if each == "DEFAULT":
                    continue
                elif devicestate[each] == 1 or devicestate[each] == 2:
                    infohandler("Switch off " + str(each))  # Set stage device off
                    devicestate[each] = 0
                    switcher(each, 0)
                elif config.get(each, "repeat", fallback="y") == "y":
                    infohandler("Repeat off " + str(each))  # Set stage as repeat was on
                    switcher(each, 0)
                    devicestate[each] = 0
                else:
                    infohandler("Stays off " + str(each))  # Device was on and command not repeated
            devicestate = devicestate.fromkeys(devicestate, 0)  # Set all device states to zero
            infohandler("All off")  # Set stage
            allOff = 1

        if nextchange == 30:
            if errorcode == 22:  # We are here the second time, so init and schedulecreation has failed
                currentchangeday = (datetime.datetime.fromtimestamp(currentchange).strftime('%Y-%m-%d %H:%M'))
                currentday = (datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M'))
                midnight = datetime.datetime.combine(datetime.datetime.today(), datetime.datetime.max.time())
                crondate = midnight.replace(hour=int(cron), minute=0, second=0, microsecond=0)
                now = datetime.datetime.today()

                if currentchangeday == currentday:
                    aux.infohandler("Next schedule not found, but we are still in same day.")
                    aux.infohandler("Wait until new schedule is available")
                    if now < crondate:
                        wait = ((crondate - now).total_seconds())
                        infohandler("Autofetch event incoming, waiting for " + str(int(wait)) + " seconds.")
                    else:
                        wait = ((midnight - now).total_seconds())
                        infohandler("Autofetch event passed, wait until midnight for "
                                    + str(int(wait)) + " seconds.")
                    time.sleep(wait)
                    errorcode = 23
                    reload()
                    init()
                else:
                    errorcode = 23
            elif errorcode == 23:
                infohandler("Something is wrong, next schedule not found!")
                infohandler("Fallback to backup schedule.")
                errorhandler("Clickclack: New schedule creation has failed, "
                             "fallback to backup and pause for 1h until fixed.", "none", 1)
                # Errorhandler on second time
                switcher("backup", 0)
                time.sleep(3600)
                reload()
                init()
                continue
            elif errorcode == 24:
                errorcode = 22  # Next change not found, try reloading all
                infohandler("Reloading schedule")
                reload()  # Time to get new schedule
                init()  # Inner function
            else:
                origin = ""  # Origin of change, do we need to stop updates?
                try:
                    f = open("data/origin", "r")
                    origin = f.read()
                    f.close()
                except:
                    origin = "S"
                    pass

                if origin == "S" or origin == "f":
                    errorcode = 22  # Next change not found, try reloading all
                    infohandler("Reloading schedule")
                    reload()  # Time to get new schedule
                    init()  # Inner function
                else:
                    try:
                        f = open("data/last", "r")
                        key = f.read()
                        f.close()
                    except:
                        key = 0
                        pass
                    nextchange = int(key)
                    infohandler("Next Update --> Time now: " + datetime.datetime.fromtimestamp(
                        time.time()).strftime('%H:%M') + " Scheduled: "
                                + datetime.datetime.fromtimestamp(nextchange).strftime('%H:%M'))
                continue
        # Reload at set time
        elif int((datetime.datetime.fromtimestamp(time.time()).strftime('%H'))) == int(cron) and \
                cronchecked != str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H')):
            if previousupdate != (int((datetime.datetime.fromtimestamp(time.time()).strftime('%d')))):
                try:
                    f = open("data/origin", "r")
                    origin = f.read()
                    f.close()
                except:
                    origin = "S"
                    pass

                if origin != "S":
                    try:
                        f = open("data/lastitem", "r")
                        lastitem = f.read()
                        f.close()
                        lastitem = int(lastitem)
                    except:
                        lastitem = 0
                        pass
                else:
                    lastitem = 0
                cronchecked = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H')
                if int(datetime.datetime.fromtimestamp(lastitem).strftime('%H')) == cron:
                    originalcron = cron   # Last change is done on time with cron, so move cron 1h
                    if cron == 23:
                        cron = 0
                    else:
                        cron = cron + 1
                    aux.infohandler("Manual change on schedule was done, periodical reload skipped.")
                elif float(lastitem) < time.time():  # If last manual change is gone already
                    aux.infohandler("Periodical schedule creation")
                    reload()
                    init()
                    previousupdate = (int((datetime.datetime.fromtimestamp(time.time()).strftime('%d'))))
                    cron = originalcron
                    continue
                else:
                    originalcron = cron  # Manual change still pending, move cron one hour
                    if cron == 23:
                        cron = 0
                    else:
                        cron = cron + 1
                    aux.infohandler("Manual change on schedule was done, periodical reload skipped.")


        # Check if schedule has been updated
        ti_m = int(os.path.getctime('data/schedule1.pkl'))
        if changeorigin == "r":  # Reload was done, so don't read file again
            oldtime = ti_m
            changeorigin = ""

        if oldtime < ti_m:
            schedule1.clear()
            oldtime = ti_m
            time.sleep(1)  # let filesystem settle down
            try:
                with open('data/schedule1.pkl', 'rb') as f:
                    infohandler("Reloading schedule due change in file")
                    temp_schedule = pickle.load(f)
                    f.close()
                    # Sort hours, annoying dic....
                    dkeys = list(temp_schedule.keys())
                    dkeys.sort()
                    schedule1 = {i: temp_schedule[i] for i in dkeys}
                    changeorigin = "w"  # External update on file happened
            except Exception as y:
                errorhandler("Clickclack: Schedule file not found on reload (file update).", y, 1)
                pass
            init()

        # Run solar energy settings if set on in setup.
        # Check if solarenergy has been updated within hour, if longer, set to zero
        if solcheckon == 1:
            try:
                sun_m = int(os.path.getctime(solarwattfile))
            except Exception as y:
                errorhandler("Clickclack: Solarenergy file not found.", y, 1)
                sun_m = sun_old
                pass
            if sun_m + 3600 < int(time.time()):
                watts = 0
            elif sun_m > sun_old:  # Avoid reads
                sun_old = sun_m
                time.sleep(1)
                try:
                    with open(solarwattfile, 'r') as w:
                        watts = w.read()
                        watts = ''.join(filter(str.isdigit, watts))
                        if watts.isdigit():
                            watts = int(watts)
                            infohandler("Current available wattage updated " + str(watts/10) + "W.")
                        else:
                            watts = 0
                            raise ValueError("The string contains non-digit characters and is not an integer.")
                        w.close()
                except Exception as y:
                    errorhandler("Clickclack: Solarenergy file error on file update.", y, 1)
                    pass
            solcheck(devicestate, watts)

        time.sleep(0.1)

reload()
start()
