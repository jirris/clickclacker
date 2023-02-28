#!/bin/bash
nano conf/devices.conf
(python3 configchecker.py)

if [ $? -eq 1 ]
  then
    echo "Error in config, please correct."
else
  FILE=/etc/systemd/system/clickclack.service
  if test -f "$FILE"; then
    if [[ $1 -ne 1 ]]; then
      echo "Restarting service"
      sudo systemctl restart clickclack.service
    fi
  fi
fi