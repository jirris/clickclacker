import usocket as socket
import uselect as select
from utime import sleep
import utime as time
from machine import Pin
from machine import reset
from machine import PWM
import gc

gc.enable()


# Defaults
settings = {
    "relayp": "off",  # Vaihtaako releen tila PWMää
    "relayonp": "50",  # Jos rele päällä, mikä on PWM
    "relayoffp": "12",  # Jos rele pois, mikä on PWM
    "sid": "xxx",  # Wifi
    "pass": "xxx",  # Wifi pass
    "pumpcp": "50",  # Millä teholla ajetaan aika-ajoin
    "pumpc": "off",  # Pumppukello eli ajetaanko wait ja run mukaan
    "wait": "60",  # Odotusaika pumpun käynnistysten välissä
    "run": "5",  # Pumpun ajoaika
}

frequency = 1000
pwm = PWM(Pin(2), frequency)  # PWM D4
pwm.duty(511)
# ESP8266 GPIO
relay1 = Pin(5, Pin.OUT)  # Pin D1
relay1.value(0)

# If file doesn't exist
try:
    test = open("setfile")
    for set in test:
        set = set.strip()
        item = set.split(":")
        if item[0] in settings:
            settings[item[0]] = item[1]

except OSError:
    with open("setfile", "w") as f:
        sleep(1)
        for each in settings:
            f.write(each + ":" + settings[each] + "\n")
    f.close()
# Lue myös
print("Boot...")
reply1 = "OK"
reply1 = reply1.encode()
reply2 = "Error"
reply2 = reply2.encode()
sock1 = socket.socket()
sock1.bind(("0.0.0.0", 2323))
sock1.listen(2)
extrelay = -1
currentpwm = pwm.duty()

# jos releohjaus, muuta dc
def clocktotime():
    import ntptime
    try:
        ntptime.settime()
    except:
        pass

def pumpcontrol(state):
    global currentpwm
    global settings
    if state == 1:
        print("Pump on")
        # Store current PWM setting
        currentpwm = pwm.duty()
        tempduty = settings["pumpcp"]
        tempduty = tempduty.strip()
        tempdutyc = 1023 * (int(tempduty) / 100)

        if int(currentpwm) < int(tempdutyc):
            pwm.duty(int(tempdutyc))
            print("Pump DC updated")
    else:
        tempduty = settings["pumpcp"]
        tempduty = tempduty.strip()
        tempdutyc = 1023 * (int(tempduty) / 100)
        pwmnow = pwm.duty()
        if int(pwmnow) == int(tempdutyc):
            pwm.duty(int(currentpwm))  # Reset previous DC
            print("Pump reset to previous setting")
        else:
            print("DC chnged, keep current DC")

def relaycontrol(state):
    global settings
    global pwm
    print("Relay bind to PWM setting, changing")
    if state == 1:
        duty = settings["relayonp"]
        duty = duty.strip()
        dutyc = 1023 * (int(duty) / 100)
        pwm.duty(int(dutyc))
    if state == 0:
        duty = settings["relayoffp"]
        duty = duty.strip()
        dutyc = 1023 * (int(duty) / 100)
        pwm.duty(int(dutyc))

def loop():
    global sock1
    global settings
    clocktotime()
    starttime = time.time() + (int(settings["wait"]) * 60)
    stoptime = starttime + (int(settings["run"]) * 60)

    while True:
        r, w, err = select.select((sock1,), (), (), 1)
        if r:
            for readable in r:
                client, client_addr = sock1.accept()
                try:
                    Client_handler(client, client_addr)
                except OSError as e:
                    pass

        t = time.time()

        if settings["pumpc"] == "on":
            if t >= starttime:
                pumpcontrol(1)
                starttime = time.time() + (int(settings["wait"]) * 60)
            if t >= stoptime:
                pumpcontrol(0)
                stoptime = starttime + (int(settings["run"]) * 60)


def Client_handler(sock2, remote):
    global reply1
    global reply2
    global pwm
    global relay1
    global extrelay
    global settings
    try:
        gc.collect()
        # print("Waiting for connection...")
        # sock2, remote = sock1.accept()
        print("Connected..." + str(remote))
        text = sock2.recv(1024)
        text = text.decode()
    except OSError as e:
        print("Connect failed." + str(e))
        return

    if text == "12345R1_1":  # Relay 1 control
        try:
            print("Rele 1 On")
            extrelay = 1
            relay1.value(1)
            sock2.sendall(reply1)
            if settings["relayp"] == "on":
                relaycontrol(1)
        except OSError as e:
            print("Failed to write status." + str(e))
            sock2.write(reply2)
    elif text == "12345R1_0":
        try:
            print("Rele 1 Off")
            relay1.value(0)
            extrelay = 0
            sock2.write(reply1)
            if settings["relayp"] == "on":
                relaycontrol(0)
        except OSError as e:
            print("Failed to write status." + str(e))
            sock2.write(reply2)
    elif text == "12345statusR1":
        try:
            status = str(relay1.value())
            sock2.write(status.encode())
            print("Status of relay" + status)
        except OSError as e:
            print("Failed to read status." + str(e))
            sock2.write(reply2)
    elif "12345pwm" in text:
        try:
            duty = text.split(" ")
            if len(duty) != 2 or duty[1].isdigit() == False:
                sock2.write(reply2)
                print("Wrong parameters")
                sock2.close()
                return
            dutyc = 1023 * (int(duty[1]) / 100)
            print(dutyc)
            pwm.duty(int(dutyc))
            sock2.write(reply1)
            print("PWM set to " + str(duty[1]))
        except OSError as e:
            print("Failed to set pwm." + str(e))
            sock2.write(reply2)
    elif "12345conf" == text:
        file = open("setfile", "r")
        for line in file:
            sock2.write(line)
        file.close()
    elif "12345set" in text:
        setdata = text.split(" ")
        if len(setdata) != 3:
            sock2.write(reply2)
            print("Wrong parameters")
            sock2.close()
            return
        if setdata[1] in settings:
            settings[setdata[1]] = setdata[2]
        with open("setfile", "w") as f:
            sleep(1)
            for each in settings:
                f.write(each + ":" + settings[each] + "\n")
        sock2.write(reply1)
        f.close()
    elif text == "12345reset":
        print("Resetting")
        sock2.write(reply1)
        sock2.close()
        sleep(2)
        reset()
    else:
        print("False request: " + text)
        sock2.write(reply2)
    sock2.close()

loop()
