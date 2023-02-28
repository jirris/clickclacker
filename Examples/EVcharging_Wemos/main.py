import socket
import dht
import network
from time import sleep
from machine import Pin
from machine import reset
from machine import PWM
import gc
gc.enable()
gc.collect()

frequency = 5000
pwm = PWM(Pin(5), frequency) # PWM D1

# ESP8266 GPIO
relay1 = Pin(4, Pin.OUT)  # Pin D1
relay2 = Pin(4, Pin.OUT)  # Pin D2

print("Boot...")
reply1 = "OK"
reply1 = reply1.encode()
reply2 = "Error"
reply2 = reply2.encode()
sock1 = socket.socket()
sock1.bind(("0.0.0.0", 2323))
sock1.listen(2)


def loop():
    while True:
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected():
            reset()
        try:
            print("Waiting for connection...")
            led.value(1)
            sock2, remote = sock1.accept()
            print("Connected..." + str(remote))
            led.value(0)
            text = sock2.recv(1024)
            text = text.decode()
        except OSError as e:
            print("Connect failed." + str(e))

        if text == "12345R1_1":  # Relay 1 control
            try:
                print("Rele 1 On")
                relay1.value(1)
                sock2.sendall(reply1)
            except OSError as e:
                print("Failed to write status." + str(e))
                sock2.write(reply2)
        elif text == "12345R1_0":
            try:
                print("Rele 1 Off")
                relay1.value(0)
                sock2.write(reply1)
            except OSError as e:
                print("Failed to write status." + str(e))
                sock2.write(reply2)
        elif text == "12345statusR1":
            try:
                status = str(relay1.value())
                sock2.write(status.encode())
                print("Status of relay" + status)
            except OSError as e:
                print("Failed to write status." + str(e))
                sock2.write(reply2)
        else:
            print("False request: " + text)
            sock2.write(reply2)
        sock2.close()

loop()
