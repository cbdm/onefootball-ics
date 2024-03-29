from flask import (
    Flask,
    flash,
    make_response,
    render_template,
    request,
    redirect,
    url_for,
)
from onefootball2ics import main as create_ics
from os import getenv
from datetime import timedelta
from flask_talisman import Talisman
from requests import get
from flask_sqlalchemy import SQLAlchemy
from pymysql import install_as_MySQLdb

install_as_MySQLdb()

app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = getenv("FLASK_SECRET_KEY", "abc")
# Connect to the DB.
db_config = {
    "host": getenv("DB_HOST", "localhost"),
    "port": getenv("DB_PORT", "3306"),
    "user": getenv("DB_USER", "user"),
    "passwd": getenv("DB_PASS", "pass"),
    "database": getenv("DB_NAME", "db"),
}
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql://{user}:{passwd}@{host}:{port}/{database}".format(**db_config)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Configure the DB table.
class MatchList(db.Model):
    of_id = db.Column(db.String(100), primary_key=True)
    data = db.Column(db.LargeBinary)

    def __repr__(self):
        return f"<MatchList {self.of_id}>"


@app.route("/", methods=("GET", "POST"))
def index():
    # if request.method == "POST":
    #     calendar_type = request.form.get("calendar_type", "")
    #     if not calendar_type:
    #         flash("You must select a valid calendar type; see the help page!")
    #         return render_template("index.html")

    #     of_id = request.form.get("onefootball_id", "")
    #     if not of_id:
    #         flash("You must provide a OneFootball ID; see the help page!")
    #         return render_template("index.html")

    #     event_length = request.form.get("event_length", "")
    #     if not event_length:
    #         event_length = "120"
    #     if event_length:
    #         if not event_length.isnumeric():
    #             flash("Event length must be a number; see help page!")
    #             return render_template("index.html")

    #     return redirect(
    #         url_for(
    #             "download",
    #             calendar_type=calendar_type,
    #             onefootball_id=of_id,
    #             event_length=event_length,
    #         )
    #     )

    return render_template("index.html")


# @app.route("/download/<calendar_type>/<onefootball_id>/<event_length>/")
# def download(calendar_type, onefootball_id, event_length):
#     if calendar_type == "team":
#         url = url_for(
#             "create_team_calendar",
#             team_id=onefootball_id,
#             event_length=event_length,
#             _external=True,
#             _scheme="https",
#         )
#     else:
#         url = url_for(
#             "create_competition_calendar",
#             comp_id=onefootball_id,
#             event_length=event_length,
#             _external=True,
#             _scheme="https",
#         )
#     test_resp = get(url)
#     if test_resp.status_code != 200:
#         flash(
#             f'Could not find the page for a {"team" if calendar_type == "team" else "competition"} with ID = "{onefootball_id}"'
#         )
#         return redirect(url_for("index"))
#     return render_template("download.html", calendar_url=url)


@app.route("/help/")
def help():
    return render_template("help.html")


# @app.route("/team/<team_id>/")
# @app.route("/team/<team_id>/<event_length>/")
# def create_team_calendar(team_id, event_length="120"):
#     """Serve an ics calendar for the desire team with each match event during the desired length."""
#     event_length = int(event_length)
#     hours = event_length // 60
#     minutes = event_length % 60
#     calendar = create_ics(
#         is_team=True,
#         of_id=team_id,
#         event_length=timedelta(hours=hours, minutes=minutes),
#         db=db,
#         MatchList=MatchList,
#     )
#     response = make_response(f"{calendar}")
#     response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
#     return response


# @app.route("/competition/<comp_id>/")
# @app.route("/competition/<comp_id>/<event_length>/")
# def create_competition_calendar(comp_id, event_length="120"):
#     """Serve an ics calendar for the desire competition with each match event during the desired length."""
#     event_length = int(event_length)
#     hours = event_length // 60
#     minutes = event_length % 60
#     calendar = create_ics(
#         is_team=False,
#         of_id=comp_id,
#         event_length=timedelta(hours=hours, minutes=minutes),
#         db=db,
#         MatchList=MatchList,
#     )
#     response = make_response(f"{calendar}")
#     response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
#     return response


# Wrap Flask app with Talisman
Talisman(app, content_security_policy=None)

if __name__ == "__main__":
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
