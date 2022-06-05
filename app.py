from flask import Flask
from flask import render_template
from flask_talisman import Talisman
from flask_seasurf import SeaSurf
import os

app = Flask(__name__)
Talisman(app)
csrf = SeaSurf(app)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)


@app.route("/")
def index():
    return render_template("index.html", strava_auth="")
