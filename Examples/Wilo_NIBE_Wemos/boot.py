def do_connect(ssid, pwd):
    import network
    from time import sleep
    sta_if = network.WLAN(network.STA_IF)
    counter = 5
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid, pwd)
        while not sta_if.isconnected() and counter != 0:
            print("Retry")
            sleep(1)
            counter = counter - 1
            pass
    print('network config:', sta_if.ifconfig())

# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)

# Attempt to connect to WiFi network
try:
    with open('setfile', 'r') as f:
        for line in f:
            items = line.split(":")
            if items[0] == "sid":
                sid = items[1]
            elif items[0] == "pass":
                pas = items[1]
    f.close()
    do_connect(sid.strip(), pas.strip())
except OSError:
    print("Error on file open")
import webrepl
webrepl.start()
