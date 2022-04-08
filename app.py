from flask import Flask, flash, make_response, render_template, request, redirect, url_for
from onefootball2ics import main as create_ics
from os import getenv
from datetime import timedelta
from redis import Redis

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY', 'abc')
redis_db = Redis(
                host=getenv('REDIS_ENDPOINT_URI', '127.0.0.1'),
                port=getenv('REDIS_PORT', '6379'),
                password=getenv('REDIS_PASSWORD', None)
                )

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        team_id = request.form.get('team_id', '')
        if not team_id:
            flash('You must provide a team_id! See the help page if unsure.')
            return render_template('index.html')
        
        event_length = request.form.get('event_length', '120')
        if event_length:
            if not event_length.isnumeric():
                flash('Event length must be a number! See help page if unsure.')
                return render_template('index.html')
        
        return redirect(url_for('create_team_calendar', team_id=team_id, event_length_in_minutes=event_length))

    return render_template('index.html')


@app.route('/help/')
def help():
    return render_template('help.html')


@app.route('/team/<team_id>/')
@app.route('/team/<team_id>/<event_length>/')
def create_team_calendar(team_id, event_length='120'):
    '''Serve an ics calendar for the desire team with each match event the desire length.'''
    event_length = int(event_length)
    hours = event_length // 60
    minutes = event_length % 60
    calendar = create_ics(team_id, timedelta(hours=hours, minutes=minutes), redis_db=redis_db)
    response = make_response(f'{calendar}')
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
