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
from aux import messagehandler, settime, sendhtml, errorhandler
# Edit these:
port = 5050
bindIP = "0.0.0.0"
users = {
    "john": generate_password_hash("hello"),
    "susan": generate_password_hash("bye")
}

###

app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True
config = configparser.ConfigParser()

# Read config for various defaults
try:
    config.read('conf/devices.conf')
    tz = (int(config["DEFAULT"]["timezone"]))
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
                with open('data/schedule1.pkl', 'wb') as f:  # Full schedule
                    pickle.dump(updatedict, f)
                    f.close()
                    f = open("data/origin", "w")
                    f.write("w")
                    f.close()
            except Exception as y:
                errorhandler("Clickclack: Schedule file save failed", y, 0)
                sys.exit()

            try:
                with open('data/prices.pkl', 'rb') as f:  # Full schedule
                    pricelist = pickle.load(f)
                    f.close()
            except Exception as y:
                errorhandler("Clickclack: Pricelist open failed", y, 0)
                sys.exit()
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

        if request.form.get('action').upper() == 'RELOAD':
            print("Reload")
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
    return render_template("web.html")


if __name__ == "__main__":
    from waitress import serve
    serve(app, host=bindIP, port=port)
