#!/bin/bash
echo "Uninstalling ClickClack webservice as service for Raspberry"
sudo systemctl disable web.service_rasbian
sudo systemctl stop web.service_rasbian
sudo rm /etc/systemd/system/web.service_rasbian
sudo systemctl daemon-reload