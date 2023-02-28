import socket
import sys

# Commands ESP8266 takes command as option:
# 
# status1 for relay status 0/1
# R1_0 relay number 1 set to 0, reply as "OK"
# R1_1 relay number 1 set to 1, reply as "OK"
# pwm n to set pwm to dutycycle n, reply as "OK"
#
# Errors in command, reply as "Error" 
#
# conf for configuration
# set nn for setting configuration
#
# Errors in command, reply as "Error" 
#
# Configuration:
'''
"relayp": "off",  # Does relay state change change PWM (on/off)
"relayonp": "50",  # If relay is on, what is PWM (0-100%)
"relayoffp": "16",  # If relay is off, what is PWM (0-100%)
"sid": "xxx",  # Wifi SID
"pass": "xxx",  # Wifi password
"pumpcp": "50",  # PWM for occational pump drive (0-100%)
"pumpc": "off",  # Is pump being started occasionally to avoid freezing etc. (on/off)
"wait": "60",  # Wait time in minutes between pump drives
"run": "5",  # How long to run pump

ESP was equipped with 3.3v - 5V converted to control Wilo_NIBE_Wemos pump and relay to switch heatpump home/away
'''

def client(call):
   received = ""
   try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      #s.connect(('192.168.178.157', 2323))
      s.connect(('192.168.4.1', 2323))
      #s.connect(('esp_1ce90a', 2323))
      text = "12345" + str(call)
      s.sendall(text.encode())

      while True:
         data = s.recv(1024)
         if data and data.decode() != "Error":
            received = data.decode()
            #  print(data)
         else:
            break
      s.close()

      #print(received)
      if received == "OK":
         print(received)
         return
      elif str(call) == "statusR1" or str(call) == "conf":
         print(received)
   except OSError as e:
      print('Failed to read status.')
      print('Error ' + str(e))

if __name__ == '__main__':
    if sys.argv[1] == "pwm":
       client(sys.argv[1] + " " + sys.argv[2])
    elif sys.argv[1] == "set":
       client(sys.argv[1] + " " + sys.argv[2] + " " + sys.argv[3])
    else:
       client(sys.argv[1])

