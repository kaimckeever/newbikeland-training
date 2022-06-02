from flask import Flask
from flask_talisman import Talisman
from flask_seasurf import SeaSurf
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)
Talisman(app)
csrf = SeaSurf(app)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)


@app.route("/")
def index():
    return "Hello Newfoundland!"
