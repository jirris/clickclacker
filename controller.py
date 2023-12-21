import configparser
import os
import aux
import subprocess
debug = 0

config = configparser.ConfigParser()

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Read config for various defaults
try:
    config.read('conf/devices.conf')
except Exception as e:
    aux.errorhandler("Controller: Config not found", e, 2)
    exit()


def switch(devices, value):
    process = ""
    if devices == "backup":
        try:
            for device in config: # timeout + wait
                if device == "DEFAULT":
                    continue
                if config.get(device, "backup", fallback="on") == "off":
                    #subprocess.Popen(config[device]["off"], shell=True)
                    subprocess.Popen("nohup " + config[device]["off"] + " > " +
                                     "log/command.log" + " 2>&1 " + "&", shell=True)
                else:
                    #subprocess.Popen(config[device]["on"], shell=True)
                    subprocess.Popen("nohup " + config[device]["on"] + " > " +
                                     "log/command.log" + " 2>&1 " + "&", shell=True)
        except Exception as e:
            aux.errorhandler("Controller: state change failed, check configuration", e, 1)
            exit(1)
    else:
        try:
            for device in config:
                if device == "DEFAULT":
                    continue
                if device == devices and value == 1:
                    delay = config.get(device, 'delay', fallback="0")
                    away = config.get(device, 'away', fallback="n")
                    #subprocess.Popen("sleep " + delay + ";" + config[device]["on"], shell=True)
                    if away == "y":
                        subprocess.Popen("nohup sh -c \'" + "sleep " + delay + ";" + config[device]["off"] + "\' > " +
                                         "log/command.log" + " 2>&1 " + "&", shell=True)
                        aux.infohandler("Controller: Away mode on, setting device to off.")
                    else:
                        subprocess.Popen("nohup sh -c \'" + "sleep " + delay + ";" + config[device]["on"] + "\' > " +
                                                "log/command.log" + " 2>&1 " + "&", shell=True)
                        if debug == 1:
                            aux.notifier("Device " + device + " ON")
                elif device == devices and value == 0:
                    delay = config.get(device, 'delay', fallback="0")
                    if debug == 1:
                        aux.notifier("Device " + device + " OFF")
                    #subprocess.Popen("sleep " + delay + ";" + config[device]["off"], shell=True)
                    subprocess.Popen("nohup sh -c \'" + "sleep " + delay + ";" + config[device]["off"] + "\' > " +
                                                "log/command.log" + " 2>&1 " + "&", shell=True)
        except Exception as e:
            aux.errorhandler("Controller: statechange failed, check configuration", e, 1)
            exit(1)
