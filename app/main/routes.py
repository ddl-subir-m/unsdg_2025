from flask import render_template, redirect, url_for, flash, request, jsonify
from datetime import date, datetime
from app.main import bp
from app import db
from app.models import Team, Event, TeamMember
from sqlalchemy import func
from openai import OpenAI
import json
import os


client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

SDG_DESCRIPTIONS = {
    1: "No Poverty",
    2: "Zero Hunger",
    3: "Good Health and Well-being",
    4: "Quality Education",
    5: "Gender Equality",
    6: "Clean Water and Sanitation",
    7: "Affordable and Clean Energy",
    8: "Decent Work and Economic Growth",
    9: "Industry, Innovation and Infrastructure",
    10: "Reduced Inequalities",
    11: "Sustainable Cities and Communities",
    12: "Responsible Consumption and Production",
    13: "Climate Action",
    14: "Life Below Water",
    15: "Life on Land",
    16: "Peace, Justice and Strong Institutions",
    17: "Partnerships for the Goals"
}

def analyze_sdg_goals(description):
    prompt = f"""Given the following event description, identify between 1 and 5 UN Sustainable Development Goals (SDGs) it aligns with most strongly.
    Return only a JSON object with two fields: 
    - 'goals': array of SDG numbers (1-17), containing 1-5 goals, ordered by relevance
    - 'primary': the main SDG number (the first goal in the goals array)
    
    Only include goals that are clearly relevant to the event. If the description is vague or only matches 1-2 goals, that's fine.
    
    Event description: {description}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={ "type": "json_object" }
        )
        result = json.loads(response.choices[0].message.content)
        result['goals'] = result['goals'][:5]
        return result
    except Exception as e:
        print(f"Error analyzing SDGs: {e}")
        return {"goals": [], "primary": None}

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        try:
            # Get team information
            team_choice = request.form.get('team_choice')
            
            # Handle team selection/creation
            if team_choice == 'existing':
                team_id = request.form.get('selected_team_id')
                
                if not team_id:
                    flash('Please select a team ', 'error')
                    return redirect(url_for('main.create_event'))
                
                team = Team.query.get(team_id)
                if not team:
                    flash('Invalid team', 'error')
                    return redirect(url_for('main.create_event'))
            else:
                # Create new team
                team_name = request.form.get('team_name')
                team_phrase = request.form.get('team_phrase')
                team_members = request.form.getlist('team_members[]')
                
                if not team_name or not team_phrase or not team_members:
                    flash('Please provide team name, phrase, and at least one member', 'error')
                    return redirect(url_for('main.create_event'))
                
                team = Team(name=team_name, team_phrase=team_phrase)
                db.session.add(team)
                db.session.flush()
                
                for i, member_name in enumerate(team_members):
                    if member_name.strip():
                        member = TeamMember(
                            name=member_name.strip(),
                            team_id=team.id,
                            is_captain=(i == 0)
                        )
                        db.session.add(member)

            # Get event details
            title = request.form.get('title')
            description = request.form.get('description')
            event_date = request.form.get('date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            timezone = request.form.get('timezone')
            location = request.form.get('location')
            sdg_goals = request.form.get('sdg_goals')

            if not all([title, description, event_date, start_time, end_time, timezone, location]):
                flash('Please fill in all event details', 'error')
                return redirect(url_for('main.create_event'))

            try:
                start_datetime = datetime.strptime(f"{event_date} {start_time}", '%Y-%m-%d %H:%M')
                end_datetime = datetime.strptime(f"{event_date} {end_time}", '%Y-%m-%d %H:%M')
                
                if end_datetime <= start_datetime:
                    flash('End time must be after start time', 'error')
                    return redirect(url_for('main.create_event'))
            except ValueError:
                flash('Invalid date or time format', 'error')
                return redirect(url_for('main.create_event'))

            sdg_analysis = analyze_sdg_goals(description)
            
            event = Event(
                title=title,
                description=description,
                start_date=start_datetime,
                end_date=end_datetime,
                timezone=timezone,
                location=location,
                team_id=team.id,
                sdg_goals=sdg_analysis
            )
            db.session.add(event)
            db.session.commit()

            flash(f'Event "{title}" has been created successfully!', 'success')
            today_date = date.today().strftime('%Y-%m-%d')
            
            # Pass the selected team information back to the template
            selected_team = {
                'id': team.id,
                'name': team.name
            }
            
            return render_template('create_event.html', 
                                 today_date=today_date,
                                 selected_team=selected_team)

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('main.create_event'))

    # GET request
    today_date = date.today().strftime('%Y-%m-%d')
    return render_template('create_event.html', 
                         today_date=today_date,
                         selected_team=None)

@bp.route('/api/search_teams')
def search_teams():
    query = request.args.get('q', '')
    if len(query.strip()) < 2:
        return jsonify([])
    
    # Search for teams by name or member names
    teams = Team.query.join(TeamMember).filter(
        db.or_(
            Team.name.ilike(f'%{query}%'),
            TeamMember.name.ilike(f'%{query}%')
        )
    ).distinct().all()
    
    # Format results with team and member information
    results = []
    for team in teams:
        members = [member.name for member in team.members.all()]
        captain = team.members.filter_by(is_captain=True).first()
        
        results.append({
            'id': team.id,
            'name': team.name,
            'member_count': team.members.count(),
            'members': members,
            'captain': captain.name if captain else 'No captain'
        })
    
    return jsonify(results)

@bp.route('/api/verify_team', methods=['POST'])
def verify_team():
    data = request.get_json()
    team_id = data.get('team_id')
    team_phrase = data.get('team_phrase')
    
    team = Team.query.get(team_id)
    if team and team.team_phrase == team_phrase:
        return jsonify({'verified': True})
    return jsonify({'verified': False})

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
    events_count = Event.query.filter_by(team_id=team_id).count()
    members_count = TeamMember.query.filter_by(team_id=team_id).count()
    events = Event.query.filter_by(team_id=team_id).all()
    return render_template('team.html', 
                         team=team, 
                         events=events,
                         events_count=events_count,
                         members_count=members_count)

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/api/create_team', methods=['POST'])
def create_team():
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('name') or not data.get('team_phrase') or not data.get('members'):
            return jsonify({'message': 'Please fill in all required fields'}), 400
        
        # Check for existing teams
        new_member_names = sorted([m.strip().lower() for m in data['members'] if m.strip()])
        existing_teams = Team.query.filter(func.lower(Team.name) == data['name'].lower()).all()
        
        for team in existing_teams:
            existing_member_names = sorted([m.name.lower() for m in team.members.all()])
            if existing_member_names == new_member_names:
                return jsonify({
                    'message': 'A team with this name and members already exists'
                }), 400
        
        # Create team and members
        team = Team(
            name=data['name'],
            team_phrase=data['team_phrase']
        )
        db.session.add(team)
        db.session.flush()  # Get the team ID
        
        # Add members
        for i, member_name in enumerate(data['members']):
            if member_name.strip():
                member = TeamMember(
                    name=member_name.strip(),
                    team_id=team.id,
                    is_captain=(i == 0)
                )
                db.session.add(member)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Team created successfully',
            'team_id': team.id
        }), 201  # Created status code
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

@bp.route('/team_profiles')
def team_profiles():
    # Get all teams with their members and event counts
    teams = db.session.query(Team, func.count(Event.id).label('event_count')) \
        .outerjoin(Event) \
        .group_by(Team.id) \
        .order_by(Team.name) \
        .all()
    return render_template('team_profiles.html', teams=teams)

@bp.route('/events')
def events():
    # Get current datetime in UTC
    current_date = datetime.utcnow()
    
    # Query upcoming events (events with end_date >= current date)
    upcoming_events = Event.query\
        .join(Team)\
        .filter(Event.end_date >= current_date)\
        .order_by(Event.start_date.asc())\
        .all()
    
    # Query past events (events with end_date < current date)
    past_events = Event.query\
        .join(Team)\
        .filter(Event.end_date < current_date)\
        .order_by(Event.start_date.desc())\
        .all()
    
    return render_template('events.html', 
                         upcoming_events=upcoming_events,
                         past_events=past_events)

@bp.route('/api/analyze_sdgs', methods=['POST'])
def analyze_sdgs():
    try:
        data = request.get_json()
        description = data.get('description', '')
        
        if not description:
            return jsonify({'message': 'Description is required'}), 400
            
        result = analyze_sdg_goals(description)
        return jsonify(result)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Add any other routes that were in app/routes.py

@bp.context_processor
def utility_processor():
    return dict(SDG_DESCRIPTIONS=SDG_DESCRIPTIONS)
