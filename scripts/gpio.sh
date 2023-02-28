#!/bin/bash
echo "Setting GPIO $1 to:"

if [ ! -e /sys/class/gpio/gpio$1 ]; then
   echo "$1" > /sys/class/gpio/export
fi

sleep 2

echo "out" > /sys/class/gpio/gpio$1/direction

if [ $2 == "on" ]; then
   echo "ON"
   raspi-gpio set $1 dl
elif [ $2 == "off" ]; then
   echo "OFF"
   raspi-gpio set $1 dh
fi