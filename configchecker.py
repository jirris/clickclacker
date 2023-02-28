#!/usr/bin/python3
import configparser
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Mandatory configs
configs = ["hours", "adj_temp", "adj_chill", "backup", "repeat", "static"]
chillconf = ["n_chill", "ne_chill", "e_chill", "se_chill", "s_chill", "sw_chill", "w_chill", "nw_chill", "cutoff_chill"]
tempconf = ["min_temp", "min_hours", "mid_hours", "mid_temp", "max_temp", "max_hours"]

config = configparser.ConfigParser()
error = 0
missing = {}

try:
    config.read('conf/devices.conf')
except Exception as e:
    print("Config file could not be opened", e)

for each in configs:  # Check for each mandatory configuration
    if each not in config["DEFAULT"]:
        for device in config:
            if device != "DEFAULT":
                if each not in config[device]:
                    if each != "hours" and each != "static":
                        missing[device] = each
                        print("Setting " + each + " missing on " + device + " and DEFAULT")
                        error = 1
                    elif "static" not in config[device] and "hours" not in config[device]:
                        missing[device] = each
                        print("Setting " + each + " missing on " + device + " and DEFAULT")
                        error = 1
checkneeded = 0

for each in tempconf:
    if each not in config["DEFAULT"]:
        checkneeded = 1

if checkneeded == 1:
    for device in config:
        if device != "DEFAULT" and config[device]["adj_temp"] != "n":
            for each in tempconf:
                if each not in config[device]:
                    print("Setting " + each + " missing on " + device + " and DEFAULT")

checkneeded = 0

for each in chillconf:
    if each not in config["DEFAULT"]:
        checkneeded = 1

for device in config:
    if device != "DEFAULT" and config[device]["adj_chill"] != "n":
        for each in chillconf:
            if each not in config[device]:
                print("Setting " + each + " missing on " + device + " and DEFAULT")

if error:
    print("-->  Set missing values to DEFAULT or device.")
exit(error)
