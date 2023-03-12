#!/usr/bin/python3
import datetime
from bs4 import BeautifulSoup as bs
import requests
import sys
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# City name in Finland 
city = "tampere"

# Tool for scraping weather data
# Works with fmi.fi opendata, URL can be replaced with any WFS source containing right BsWfs parameters
URL = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::harmonie::surface::point::simple&place=" + city + "&parameters=temperature,winddirection,windspeedms,TotalCloudCover,RadiationGlobal"

filename1 = "../data_sources/temperature"
filename2 = "../data_sources/wind"
filename3 = "../data_sources/cloud.csv"
filename4 = "../data_sources/sun.csv"

content = []

try:
    content = requests.get(URL)
except:
    print("Couldn't connect to site")
    sys.exit(1)

# Combine the lines in the list into a string
#content = "".join(content)
bs_content = bs(content.content, features="xml")

results = {}
temperatures = {}
winds = {}
windd = {}
cloud = {}
radiation = {}


# Find right elements and return text to dictionary containing arrays
for row in bs_content.findAll("wfs:member"):
    date = row.find("BsWfs:Time").text
    date_time = (datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')) 
    day = (date_time.strftime('%Y-%m-%d')) 
    if day not in temperatures:
        temperatures.update({day: []})
    if day not in winds:
        winds.update({day: []})
    if day not in windd:
        windd.update({day: []})
    if day not in cloud:
        cloud.update({day: []})
    if day not in radiation:
        radiation.update({day: []})
    if row.find("BsWfs:ParameterName").text == "temperature": 
        temp = row.find("BsWfs:ParameterValue").text
        temperatures[day].append(temp)
    if row.find("BsWfs:ParameterName").text == "winddirection": 
        temp = row.find("BsWfs:ParameterValue").text
        windd[day].append(temp)
    if row.find("BsWfs:ParameterName").text == "windspeedms": 
        temp = row.find("BsWfs:ParameterValue").text
        winds[day].append(temp)
    if row.find("BsWfs:ParameterName").text == "TotalCloudCover":
        cloudtime = row.find("BsWfs:Time").text
        cloudtime = (datetime.datetime.strptime(cloudtime, '%Y-%m-%dT%H:%M:%S%z'))
        cloudtime = (cloudtime.strftime('%H:%M:%S'))
        temp = row.find("BsWfs:ParameterValue").text
        cloud[day].append((cloudtime, temp))
        # RadiationGlobal
    if row.find("BsWfs:ParameterName").text == "RadiationGlobal":
        radtime = row.find("BsWfs:Time").text
        radtime = (datetime.datetime.strptime(radtime, '%Y-%m-%dT%H:%M:%S%z'))
        radtime = (radtime.strftime('%H:%M:%S'))
        temp = row.find("BsWfs:ParameterValue").text
        radiation[day].append((radtime, temp))


# Data is hour based, so combine and calculate averages
averagetemps = {}

for each in temperatures:
    x = 0
    y = 0
    for t in temperatures[each]:
        x = x + float(t)
        y = y + 1
    averagetemps.update({each : x/y})

averagewind = {}

for each in winds:
    x = 0
    y = 0
    for t in winds[each]:
        x = x + float(t)
        y = y + 1
    averagewind.update({each : [x/y]})

for each in windd:
    x = 0
    y = 0
    for t in windd[each]:
        x = x + float(t)
        y = y + 1
    averagewind[each].append(x/y)

# Convert wind degrees to directions

for each in averagewind:
    if (averagewind[each][1] < 22.5 and averagewind[each][1] >= 0) or (averagewind[each][1] >= 337.5):
        averagewind[each][1] = "n"
    elif averagewind[each][1] >= 22.5 and averagewind[each][1] < 67.5:
        averagewind[each][1] = "ne"
    elif averagewind[each][1] >= 67.5 and averagewind[each][1] < 112.5:
        averagewind[each][1] = "e"
    elif averagewind[each][1] >= 112.5 and averagewind[each][1] < 157.5:
        averagewind[each][1] = "se"
    elif averagewind[each][1] >= 157.5 and averagewind[each][1] < 202.5:
        averagewind[each][1] = "s"
    elif averagewind[each][1] >= 202.5 and averagewind[each][1] < 247.5:
        averagewind[each][1] = "sw"
    elif averagewind[each][1] >= 247.5 and averagewind[each][1] < 292.5:
        averagewind[each][1] = "w"
    elif averagewind[each][1] >= 292.5 and averagewind[each][1] < 337.5:
        averagewind[each][1] = "nw"

t = 0
templines = []
for each in averagetemps:
    templines.append(list(averagetemps.items())[t][1])
    t = t + 1

t = 0
windlines = []
for each in averagetemps:
    windlines.append(list(averagewind.items())[t][1])
    t = t + 1

linesrad = ""
linescloud = ""


for each in cloud:
    line = ""
    line2 = ""
    for item in cloud[each]:
        line = line + "," + each + " " + item[0]
        line2 = line2 + "," + item[1]
        line = line.lstrip(",")
        line2 = line2.lstrip(",")
    linescloud = linescloud + line + "\n" + line2 + "\n"

for each in radiation:
    line = ""
    line2 = ""
    for item in radiation[each]:
        line = line + "," + each + " " + item[0]
        line2 = line2 + "," + item[1]
        line = line.lstrip(",")
        line2 = line2.lstrip(",")
    linesrad = linesrad + line + "\n" + line2 + "\n"


try:
    tfile = open(filename1, "w")
    tfile.write("[temperature]" + "\n")
    tfile.write("today=" + str(templines[0]) + "\n")
    tfile.write("tomorrow=" + str(templines[1]) + "\n")
    tfile.write("dayaftertomorrow=" + str(templines[2]) + "\n")
    tfile.close()
    tfile = open(filename2, "w")
    tfile.write("[wind]" + "\n")
    tfile.write("today_spd=" + str(windlines[0][0]) + "\n")
    tfile.write("tomorrow_spd=" + str(windlines[1][0]) + "\n")
    tfile.write("dayaftertomorrow_spd=" + str(windlines[2][0]) + "\n")
    tfile.write("today_dir=" + str(windlines[0][1]) + "\n")
    tfile.write("tomorrow_dir=" + str(windlines[1][1]) + "\n")
    tfile.write("dayaftertomorrow_dir=" + str(windlines[2][1]) + "\n")
    tfile.close()
    today = datetime.date.today()
    print(str(today) + " New weatherdata retrieved")
    tfile = open(filename3, "w")
    tfile.write(linescloud)
    tfile.close()
    tfile = open(filename4, "w")
    tfile.write(linesrad)
    tfile.close()
except Exception as y:
    print("File write failed" + str(y))
    sys.exit(1)
