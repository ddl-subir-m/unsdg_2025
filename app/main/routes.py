from flask import render_template, redirect, url_for, flash, request
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
        date = request.form['date']
        sdg_goal = request.form['sdg_goal']
        
        # Assuming you have a way to get the current team
        # For now, let's just use the first team in the database
        team = Team.query.first()
        
        new_event = Event(title=title, description=description, date=date, sdg_goal=sdg_goal, team=team)
        db.session.add(new_event)
        db.session.commit()
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_event.html')

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
