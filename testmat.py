import time
import pickle
import os

times = 90
skip = 30

devices1 = ['Heatpump',  'Car charger', 'Smart plug testi', 'Smart plug auto']
devices2 = ['Heatpump', 'Floor heating', 'Car charger', 'Smart plug testi', 'Smart plug auto']
devices3 = ['Heatpump', 'Floor heating']
devices4 = ['Heatpump', 'Floor heating']
devices5 = ['Heatpump', 'Floor heating', 'Car charger', 'Smart plug testi', 'Smart plug auto']

devices = [devices1, devices2, devices3, devices4, devices5]

schedule = {}

count = 0
now = time.time()

while times > 0:
    now = int(now) + 10
    schedule[now] = devices[count]
    times = times - 1
    if count == 4:
        count = 0
    else:
        count = count + 1

try:
    if os.path.exists('data/schedule1.pkl'):
        os.remove('data/schedule1.pkl')
    with open('data/schedule1.pkl', 'wb') as f:  # Full schedule
        pickle.dump(schedule, f)
        f.close()
except Exception as e:
    print("Schedule file write failed", e, 0)
