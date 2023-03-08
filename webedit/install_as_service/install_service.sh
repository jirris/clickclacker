#!/bin/bash
echo "Installing ClickClack webeditor as service for Raspberry"
sudo cp web.service_rasbian /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable web.service_rasbian
sudo systemctl start web.service_rasbian