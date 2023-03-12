#!/bin/bash
echo "Installing ClickClack as service for Raspberry"
sudo cp clickclack.service_rasbian /etc/systemd/system/clickclack.service
sudo systemctl daemon-reload
sudo systemctl enable clickclack.service_rasbian
sudo systemctl start clickclack.service_rasbian