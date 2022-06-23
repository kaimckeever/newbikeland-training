from flask import Flask
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    make_response,
    flash,
)
from flask_talisman import Talisman
from flask_seasurf import SeaSurf
from deta import Deta
import os
import requests

app = Flask(__name__)
Talisman(app)
csrf = SeaSurf(app)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
VERIFY_TOKEN = str(os.urandom(24))
CLIENT_ID = os.environ.get("CLIENT_ID")
PRODUCTION_URL = os.environ.get("PRODUCTION_URL")
FLASK_ENV = os.environ.get("FLASK_ENV")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
if PROJECT_KEY := os.environ.get("PROJECT_KEY") or None:
    deta = Deta(PROJECT_KEY)
    users = deta.Base("users")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/authorize")
def authorize():
    exchange_token_url = (
        "http://localhost:5000" if FLASK_ENV == "development" else PRODUCTION_URL
    )
    strava_url = f"http://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={exchange_token_url}/exchange_token&approval_prompt=force&scope=activity:read_all"
    return redirect(strava_url)


@app.route("/exchange_token")
def exchange_token():
    code = request.args.get("code")
    if error := request.args.get("error") or None:
        return render_template("error.html", error=error)
    exchange_token_url = "https://www.strava.com/oauth/token"
    exchange_token_params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    }
    exchange_token_response = requests.post(
        exchange_token_url, params=exchange_token_params
    )
    response_json = exchange_token_response.json()
    access_token = response_json["access_token"]
    refresh_token = response_json["refresh_token"]
    expires_at = response_json["expires_at"]
    accepted_scopes = response_json["scope"]
    user_id = response_json["athlete"]["id"]
    user_name = response_json["athlete"]["firstname"]

    response = redirect(url_for("dashboard"))
    response.set_cookie("refresh_token", refresh_token)
    response.set_cookie("access_token", access_token)
    response.set_cookie("expires_at", expires_at)
    response.set_cookie("accepted_scopes", accepted_scopes)
    response.set_cookie("user_name", user_name)
    response.set_cookie("user_id", user_id)
    flash("You were successfully logged in")
    return response


@app.route("/dashboard")
def dashboard():
    return render_template(
        "dashboard.html", user_name=request.cookies.get("user_name") or ""
    )


@app.route("/sync")
def sync():
    push_subscription_url = "https://www.strava.com/api/v3/push_subscriptions"
    callback_url = (
        "http://localhost:5000/webhook"
        if FLASK_ENV == "development"
        else f"{PRODUCTION_URL}/webhook"
    )
    push_subscription_params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "callback_url": callback_url,
        "verify_token": VERIFY_TOKEN,
    }
    push_subscription_response = requests.post(
        push_subscription_url, params=push_subscription_params
    )
    response_json = push_subscription_response.json()
    return jsonify(response_json)


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "POST":
        # TODO - process webhook data
        app.logger.info("webhook received")
        data = request.get_json()
        return make_response(jsonify(data), 200)
    mode = request.args.get("hub.mode")
    challenge = request.args.get("hub.challenge")
    token = request.args.get("hub.verify_token")
    if mode and token:
        if mode != "subscribe" or token != VERIFY_TOKEN:
            return make_response("", 403)
        app.logger.info("WEBHOOK_VERIFIED")
        return make_response(jsonify({"hub.challenge": challenge}), 200)
    return make_response("", 403)


@app.route("/add")
def add():
    return make_response(
        jsonify(
            {"message": "placeholder for add functionality", "progress": "not started"}
        ),
        200,
    )


@app.route("/logout")
def logout():
    response = redirect(url_for("index"))
    response.set_cookie("access_token", expires=0)
    response.set_cookie("refresh_token", expires=0)
    response.set_cookie("expires_at", expires=0)
    response.set_cookie("user_name", expires=0)
    response.set_cookie("user_id", expires=0)
    flash("You were successfully logged out")
    return response


@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        "error.html",
        who="You",
        error="Error 404: Page not found.",
    )


@app.errorhandler(403)
def forbidden(e):
    return render_template(
        "error.html",
        who="We",
        error="Error 403: Forbidden. Check your permissions for Strava",
    )


@app.errorhandler(500)
def internal_server_error(e):
    return render_template(
        "error.html",
        who="I",
        error="Error 500: Internal server error. Try again another time.",
    )
