import csv
from datetime import datetime

def radiation(value, start, end):
    filename1 = "data_sources/cloud.csv"
    filename2 = "data_sources/sun.csv"

    clouddict = {}
    sundict = {}
    header = []
    lines = []

    a = 0
    with open(filename1, 'r') as data:
        for line in csv.reader(data):
            if a == 0:
                header.append(line)
                a = 1
            else:
                lines.append(line)
                a = 0
    data.close()

    for day1, day2 in zip(header, lines):
        for time, value in zip(day1, day2):
            clouddict[time] = value

    a = 0
    with open(filename2, 'r') as data:
        for line in csv.reader(data):
            if a == 0:
                header.append(line)
                a = 1
            else:
                lines.append(line)
                a = 0
    data.close()

    for day1, day2 in zip(header, lines):
        for time, value in zip(day1, day2):
            sundict[time] = value

    # Filter based on need
    filteredsun = []
    for power in sundict:
        if float(sundict[power]) < float(value):
            date = datetime.strptime(power, '%Y-%m-%d %H:%M:%S')
            if date.hour >= start and date.hour <= end:
                filteredsun.append(power)

    return filteredsun

if __name__ == '__main__':
    print(radiation(30, 12, 16))