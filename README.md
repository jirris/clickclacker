ClickClack for Clicking and Clacking devices on and off based on spot electricity prices
---------
  
Application is intended to be used to save energy costs, by controlling for example relays that control heating, based on spot electricity prices in Europe. It also takes in account the hours needed for heating (or cooling) based on external temperature forecast and wind.
  
Usecase examples:
- Controlling water heater to heat during cheap hours
- Controlling Inverters to change setting or go on/off based on price (see for example mecloud in Github)
- Controlling car charger to charge only during cheap hours (tested with Webasto charging stations)
- Set loads on when Solarenergy is available
  
-------INSTALLATION-------------
  
Prequisites:
- Python3
- Following additional Python3 libraries:
  - bs4
  - configparser
  - lxml (note in Rasbian you have to install this with apt-get install python3-lxml, this installs also bs4). 
  - nordpool, if you plan to use Nordpool script in tools instead of Entsoe.
  - Flask, waitress and flask_httpauth, if you plan to use webeditor (small and bad), check readme.md in webedit folder
  - discord_webhook, if you want to use discord for messages
  
Install with: pip3 install library  
  
Steps to take in use:  
1. Download release and extract it to your home directory
2. Install needed libraries and test run.
3. Configure conf/devices.conf, see CONFIGURATION below
4. Use existing tools or your own to create data_sources (today.json and tomorrow.json are mandatory. Temperature and wind, if you intend to use those)
5. Create scripts to run when device state changes and add those do devices.conf (for example GPIO on/off).
6. Following files must exist before running: data_sources/today.json and tomorrow.json
7. Test run clickclack.py
8. Install clickclack as service (optional) with tools/install/install_service.sh (Rasbian) or run clickclack in screen.
9. Edit configuration later with bash edit_config.sh script.
  
Errors:  
In case of errors, system defaults all on or off, based on configuration and emails user, if email is configured, otherwise just writes log.  
You may also use Callmebot (https://callmebot.com) to send error and alive messages to Telegram, Signal or Whatsapp.

------FILES IN SYSTEM---------
  
System assumes datafiles in data_sources directory (examples in the directory):  
Today.json —> Todays prices for electricity in JSON format. Tagnames can be set in config, but time should follow datetime format.  
Tomorrow.json —> Tomorrows prices.  
Temperature —> Temperature forecasts for today and tomorrow as average.  
Wind —> wind forecast in m/s as speed and lowercase English acronyms for direction (n, ne, e, se, s, sw, w, nw).  
currentW -> If used, the current Wattage from solarpanels, checked when file changes.
    
You can use your own scripts to create these files (see devices.conf/fetch.sh) in json or use static files, if you want heating to hit to same hours every day.  
For spotprices there is also a alternative to use Entso-e site, see more information in devices.conf
  
There is also ready tools to use in Finland and Nordpool as example in data_sources/tools directory. You should run these for example thru cron, when data is available (for example after midnight) or use in build "fetch" setting.   
For Nordpool (nord.py) edit Location and Tax multiplier in file header.  

Cron example for tools:  
 0 16 * * * timeout 60 python3 /home/pi/clickclack/tools/price.py -t 1  
 2 16 * * * timeout 60 python3 /home/pi/clickclack/tools/price.py -t 2  
 0 16 * * * timeout 60 python3 /home/pi/clickclack/tools/fmi_parser.py  
   
Which gets new prices and weather at 4pm when those are released.
  
------CONFIGURATION----------
  
For configuration, see file data/devices.conf. Configuration is explained there, all fields are mandatory for all devices, but default values can be used under "DEFAULT". 
  
Use system by running python3 clickclack.py, or installing it as service. Raspbian compatible install script is in Tools directory.  
  
Other files in system:  
tools/fetch.sh, example of running periodical scripts instead of CRON. In example config this is used to get price and weather data in Finland.
tools/fmi_parser.py, for retrieving forecasts from FMI.fi (Finland).  
tools/price.py, for retrieving prices from open api (Finland).    
tools/nord.py, for retrieving prices from Nordpool api, see script for configuring, relys on Nordpool library.  
tools/spotprice, a Go implementation to retrieve spot prices from Ensto-e. (Europe). 
tools/check_clickclack.sh, small script to check if clickclack service is running, use from crontab hourly or so

data/schedule.csv and data/schedule.html, current schedules in CSV and HTML format for viewing.

tools/install/ tools for system service for Rasbian installation, for others edit clickclack.service file for right user and home directory.  
edit_config.sh, use this to edit devices.conf after Clickclack has been installed as service (restarts service after install)

Scripts/gpio.sh, tool for changing GPIO state for example to change relay status on Raspberry. Use with:    
  - on=bash scripts/gpio.sh 5 on
  - off=bash scripts/gpio.sh 5 off, in devices.conf
Scripts/shelly.py, for controlling Shelly relays (ShellyPy package needed, install with pip3 install shellypy)
scripts/test.sh, for testing purposes, just prints text to log/test.log

webedit, a small server for editing active hour online, refer to readme.md in folder

------TESTED WITH-----------
  
Possible hardware to use / tested with:
- Raspberry Pi with Relay shield (http://robomaa.fi/index.php?route=product/product&product_id=2142)
  - Uponor Smartix (setting at home/away to lower temperature) (Raspberry relay board)
  - Ekowell heatpump (setting at home/away) (Raspberry relay board)
- Wemos D1 with relay shield controlled over TCP/IP (to be added as example) 
  - Webasto Pure II car charger + Wemos D1 to switch on/off
  - NIBE heatpump (setting at home/away)
  - Wilo PWM controlled waterpump, for controlling circulation based on need/external temperature.
With great GitHub projects:
- Panasonic inverter (https://github.com/lostfields/python-panasonic-comfort-cloud)
- Gree inverter (https://github.com/tomikaa87/gree-remote)
- Deltaco smartplug (https://github.com/jasonacox/tinytuya)
- Grott for Growatt inverters (https://github.com/johanmeijer/grott)
