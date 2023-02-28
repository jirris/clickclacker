#!/bin/bash
echo "Uninstalling ClickClack as service for Raspberry"
sudo systemctl disable clickclack.service_rasbian
sudo systemctl stop clickclack.service_rasbian
sudo rm /etc/systemd/system/clickclack.service_rasbian
sudo systemctl daemon-reload