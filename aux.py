# Auxillary functions
import time
import sys
import smtplib
import configparser
import os
import callmebot
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Takes option tz as timezone correction and returns localtime correction for unixtime


def settime(tz):
    t = time.time()
    UTC_OFFSET = int(tz) * 60 * 60
    tm = time.localtime(t + UTC_OFFSET)
    year = tm[0]  # get current year

    HHMarch = time.mktime(
        (year, 3, (14 - (int(5 * year / 4 + 1)) % 7), 1, 0, 0, 0, 0, 0)
    )  # Time of March change to DST
    HHNovember = time.mktime(
        (year, 10, (7 - (int(5 * year / 4 + 1)) % 7), 1, 0, 0, 0, 0, 0)
    )  # Time of November change to EST

    now = time.time()
    if now < HHMarch:  # we are before last sunday of march
        offset = UTC_OFFSET
    elif now < HHNovember:  # we are before last sunday of october
        offset = UTC_OFFSET + 3600
    else:  # we are after last sunday of october
        offset = UTC_OFFSET
    return offset

#  Email sender


def sendemail(msg, server, email, password):
    s = smtplib.SMTP(server, 587)
    s.starttls()
    s.login(email, password)
    s.sendmail(email, email, ("MIME-version: 1.0\nContent-Type: text/plain; charset=UTF-8\n"
                              "Subject: ClickClack info\n\n" + msg).encode('utf-8'))
    s.quit()

#  Error notifier


def errorhandler(msg, exp, code):
    config = configparser.ConfigParser()
    returnvalue = 0
    try:
        config.read('conf/devices.conf')
        consoleon = (config["DEFAULT"]["consoleon"])
        emailon = (config["DEFAULT"]["emailon"])
        email = (config["DEFAULT"]["email"])
        password = (config["DEFAULT"]["emailpassword"])
        server = (config["DEFAULT"]["emailserver"])
        errorlog = (config["DEFAULT"]["errorlog"])
        log = (config["DEFAULT"]["log"])
        html = (config["DEFAULT"]["html"])
        callmebotset = (config["DEFAULT"]["callmebot"])
    except Exception as e:
        print("Config not found" + str(e))
        sys.exit()
    try:
        if code == "message":
            if os.path.exists(log):
                append_write = 'a'  # append if already exists
            else:
                append_write = 'w'  # make a new file if not
            logfile = open(log, append_write)
            logfile.write(msg + "\n")
            logfile.close()
            if emailon == "y" and html == "n":
                sendemail(msg, server, email, password)
            if consoleon == "y":
                print(msg)
            if callmebotset == "y":
                phone_number = (config["DEFAULT"]["phone_number"])
                api_key = (config["DEFAULT"]["api_key"])
                service = (config["DEFAULT"]["service"])
                message = "Clickclack running normally"
                returnvalue = callmebot.send_message(phone_number, api_key, message, service)
                if returnvalue:
                    errorhandler(returnvalue, 0, 0)
        elif code == "info":
            if os.path.exists(log):
                append_write = 'a'  # append if already exists
            else:
                append_write = 'w'  # make a new file if not
            logfile = open(log, append_write)
            logfile.write(msg + "\n")
            logfile.close()
            if consoleon == "y":
                print(msg)
        else:
            if os.path.exists(log):
                append_write = 'a'  # append if already exists
            else:
                append_write = 'w'  # make a new file if not
            logfile = open(errorlog, append_write)
            logfile.write(msg + "\n" + str(exp) + "\n")
            logfile.close()
            if emailon == "y":
                sendemail(msg, server, email, password)
            if consoleon == "y":
                if str(exp) == "0":
                    exp = "Normal operation"
                print(msg + ". Exception: " + str(exp))
            if callmebotset == "y":
                phone_number = (config["DEFAULT"]["phone_number"])
                api_key = (config["DEFAULT"]["api_key"])
                service = (config["DEFAULT"]["service"])
                returnvalue = callmebot.send_message(phone_number, api_key, msg, service)
                if returnvalue:
                    errorhandler(returnvalue, 0, 0)
    except Exception as e:
        print("Log write failed or email send failed " + str(e))

# Information logger


def messagehandler(msg):
    errorhandler(msg, 0, "message")


def infohandler(msg):
    errorhandler(msg, 0, "info")


def sendhtml():
    try:
        config = configparser.ConfigParser()
        config.read('conf/devices.conf')
        consoleon = (config["DEFAULT"]["consoleon"])
        emailon = (config["DEFAULT"]["emailon"])
        email = (config["DEFAULT"]["email"])
        password = (config["DEFAULT"]["emailpassword"])
        server = (config["DEFAULT"]["emailserver"])
        errorlog = (config["DEFAULT"]["errorlog"])
        log = (config["DEFAULT"]["log"])
        callmebotset = (config["DEFAULT"]["callmebot"])
    except Exception as e:
        print("Config not found " + str(e))
        sys.exit()
    if emailon == "y":
        try:
            file = open("data/schedule.html", "r")
            message = file.read()
            file.close()
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "ClickClack schedule"
            msg['From'] = email
            msg['To'] = email
            part1 = MIMEText(message, 'html')
            msg.attach(part1)
            mail = smtplib.SMTP(server, 587)
            mail.ehlo()
            mail.starttls()
            mail.login(email, password)
            mail.sendmail(email, email, msg.as_string())
            mail.quit()
        except Exception as e:
            print("HTML not found " + str(e))
            sys.exit()
