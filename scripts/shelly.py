# Install shellypy
import ShellyPy
from sys import argv

if len(argv) != 4:
   print("Usage: shelly.py IP on/off relaynumber, for example: shelly.py 192.168.11.2 on 0")
   exit()

IP = argv[1]
relay = argv[3]

print(str(argv))

try:
   device = ShellyPy.Shelly(IP)
except:
   print("Device not reachable")
   exit()

if argv[2] == "on":
   device.relay(0, turn=True) # turn the relay at index 0 on
else:
   device.relay(0, turn=False) # same as above but turn it off

# device.relay(0, turn=True, delay=3) # turn the relay 0 on for 3 seconds then off
# most shelly devices only have 1 or 2 relays