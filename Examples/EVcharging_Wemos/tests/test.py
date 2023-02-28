import client
import time
import random

while(True):
   waittime = random.randrange(10,60)
   print(waittime)
   time.sleep(waittime)
   client.client("hum")
   time.sleep(5)
   client.client("temp")
   time.sleep(5)
   client.client("R1_1")
   time.sleep(5)
   client.client("R2_0")
   time.sleep(5)
   client.client("R1_0")
   time.sleep(5)
   client.client("R2_1")
   time.sleep(5)
   client.client("statusR1")
   time.sleep(5)
   client.client("statusR2")
   time.sleep(5)

