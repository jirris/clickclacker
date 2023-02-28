import socket
import sys

# Commands ESP8266 takes command as option:
# 
# status1 or status2 for relay status 0/1
# temp for temperature in C
# hum for humidity 
# R1_0 relay number 1 set to 0, reply as "OK"
# R1_1 relay number 1 set to 1, reply as "OK"
# R2_0 relay number 2 set to 0, reply as "OK"
# R2_1 relay number 2 set to 1, reply as "OK"
# 
# Errors in command, reply as "Error" 
#
# ESP equipped with relayboard (2 relays) and DHT22 sensor for humidity and temperature.
#

def client(call):
   received = ""
   try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect(('192.168.178.140', 2323))
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
      elif str(call) == "hum":
         print(received)
      elif str(call) == "temp":
         print(received)
      elif str(call) == "statusR1":
         print(received)
      elif str(call) == "statusR2":
         print(received)
   except OSError as e:
      print('Failed to read status.')
      print('Error ' + str(e))

if __name__ == '__main__':
    client(sys.argv[1])



