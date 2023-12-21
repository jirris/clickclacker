import pickle
import configparser
import sys
import os
from flask import *
from datetime import datetime
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import time

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

sys.path.append("..")
import publish
from aux import messagehandler, sendhtml, errorhandler, settime
# Edit these:
port = 5050
bindIP = "0.0.0.0"
users = {
    "click": generate_password_hash("clack"),
}

###

app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True
config = configparser.ConfigParser()

# Read config for various defaults
try:
    config.read('conf/devices.conf')
    tz = (float(config["DEFAULT"]["timezone"]))
    daylight = config.get("DEFAULT", 'daylight', fallback="n")
    if daylight == "y" or daylight == "Y":
        tz = tz + int(time.daylight)
except Exception as e:
    errorhandler("Config not found", e, 1)
    exit()

auth = HTTPBasicAuth()

oldtime = 0

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


@app.route("/", methods=["GET", "POST"])
@auth.login_required
def home():
    global oldtime
    updatedict = {}
    updatedict.clear()
    if request.method == "POST":
        if request.form.get('action').upper() == 'SAVE':
            dict = request.form.to_dict()
            del dict['action']
            for each in dict:
                value = each.split("_")
                if int(value[0]) not in updatedict:
                    updatedict[int(value[0])] = [value[1]]
                else:
                    updatedict[int(value[0])].append(value[1])

            # Sort hours, annoying dic....
            dkeys = list(updatedict.keys())
            dkeys.sort()
            updatedict = {i: updatedict[i] for i in dkeys}

            try:
                with open('data/schedule1.pkl', 'rb') as f:  # Full schedule
                    oldsch = pickle.load(f)
                    f.close()
                    newkey = []
                    for key in updatedict:
                        if key not in oldsch:
                            newkey.append(key)
                            #print("Cannot change setting outside prices")
                        else:
                            if updatedict[key] != oldsch[key]:
                                print("Content change")
                                newkey.append(key)

                    for key in oldsch:
                        if key not in updatedict:
                            newkey.append(key)
                            print("Item removed")
                if len(newkey) == 0:
                    return render_template("web.html")
                lastitem = max(newkey)

                try:
                    f = open("data/lastitem", "r")
                    oldkey = f.read()
                    if oldkey == "":
                        oldkey = 0
                    f.close()
                    f = open("data/lastitem", "w")
                    if int(oldkey) < int(lastitem):
                        f.write(str(lastitem))
                    f.close()
                except Exception:
                    pass

                with open('data/schedule1.pkl', 'wb') as f:
                    pickle.dump(updatedict, f)
                    f.close()
                    f = open("data/origin", "w")
                    f.write("w")
                    f.close()
            except Exception as y:
                errorhandler("Clickclack: Schedule file save failed", y, 0)
                return render_template("error.html")

            try:
                with open('data/prices.pkl', 'rb') as f:
                    pricelist = pickle.load(f)
                    f.close()
            except Exception as y:
                errorhandler("Clickclack: Pricelist open failed", y, 0)
                return render_template("error.html")
            publish.csvcreator(updatedict, pricelist)

            hrsched = ""
            price = ""

            for key in updatedict:  # This moments settings
                t = datetime.fromtimestamp(key)
                t = t.strftime('%Y-%m-%d %H:%M:%S %Z')
                for each in pricelist:
                    if (int(each[0])) == int(key):
                        price = each[1]
                        break
                    else:
                        price = "Unknown"

                hrsched = hrsched + (str(t) + "--> ON:\t" + str(updatedict[key]) + "  Price: " + str(price) + "\n")

            if config.get('DEFAULT', 'html', fallback="n") == "y":
                sendhtml()
                messagehandler(hrsched)
            else:
                messagehandler(hrsched)
            return render_template("web.html")

        if request.form.get('action').upper() == 'REGENERATE':
            print("Regenerate")
            ti_m = int(os.path.getctime('webedit/templates/web.html'))
            os.system('python3 schedulecreator.py')
            # Check if schedule has been updated
            a = 10
            while a != 0:
                if ti_m == int(os.path.getctime('webedit/templates/web.html')):
                    time.sleep(1)  # let filesystem settle down
                    a = a - 1
                else:
                    break
            return render_template("web.html")
    elif request.method == "GET":
            return render_template("web.html")
    return render_template("web.html")


if __name__ == "__main__":
    from waitress import serve
    serve(app, host=bindIP, port=port)
