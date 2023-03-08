This application is very simple web server for editing hours. It is ugly and buggy, but contributions are welcome.

On install/setup:
- Install this as a service with the provided tool or run in screen
- Edit the desired port on the header of the server.py file
- Run with python3 server.py
- If you plan to use this externally, e.g. facing internet, please use Nginx, do not open this without protection to internet!
  - (https://dev.to/thetrebelcc/how-to-run-a-flask-app-over-https-using-waitress-and-nginx-2020-235c)

Note on usage: if you change settings, those are frozen until they run out, so periodical updates or any other updates don't change schedule, 
to change schedule back to normal, wait until schedule runs out, re-run schdedulecreator.py or click reload button.
