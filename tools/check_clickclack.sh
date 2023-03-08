#!/bin/bash
# Small script for checking if service is up. Use from crontab for example hourly
cd ~/clickclack
systemctl is-active --quiet clickclack.service || python3 -c 'from aux import errorhandler; errorhandler("Clickclack is down", 1, 1)'