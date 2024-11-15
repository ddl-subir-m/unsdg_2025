from flask import render_template, redirect, url_for, flash, request
from datetime import date, datetime
from app.main import bp
from app import db
from app.models import Team, Event
from sqlalchemy import func

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date_str = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        
        # Combine date and time strings into datetime objects
        start_datetime = datetime.strptime(f"{date_str} {start_time}", '%Y-%m-%d %H:%M')
        end_datetime = datetime.strptime(f"{date_str} {end_time}", '%Y-%m-%d %H:%M')
        
        # Validate that end time is after start time
        if end_datetime <= start_datetime:
            flash('End time must be after start time', 'error')
            return redirect(url_for('main.create_event'))
        
        # Assuming you have a way to get the current team
        team = Team.query.first()
        
        new_event = Event(
            title=title, 
            description=description, 
            start_date=start_datetime,
            end_date=end_datetime,
            team=team
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('main.index'))
    
    # Add today's date for the date picker
    today_date = date.today().strftime('%Y-%m-%d')
    return render_template('create_event.html', today_date=today_date)

@bp.route('/leaderboard')
def leaderboard():
    teams = db.session.query(Team, func.count(Event.id).label('event_count')) \
        .outerjoin(Event) \
        .group_by(Team.id) \
        .order_by(func.count(Event.id).desc()) \
        .all()
    ranked_teams = [(rank, team, event_count) for rank, (team, event_count) in enumerate(teams, start=1)]
    return render_template('leaderboard.html', ranked_teams=ranked_teams)

@bp.route('/team/<int:team_id>')
def team(team_id):
    team = Team.query.get_or_404(team_id)
    return render_template('team.html', team=team)

@bp.route('/about')
def about():
    return render_template('about.html')

# Add any other routes that were in app/routes.py
