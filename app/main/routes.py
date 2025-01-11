from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from datetime import date, datetime
from app.main import bp
from app import db
from app.models import Team, Event, TeamMember, BingoCard, Notification, EventVerification
from sqlalchemy import func
from openai import OpenAI
import json
import os
import random
import pytz
from PIL import Image
from io import BytesIO
from werkzeug.utils import secure_filename


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

def update_bingo_card(team_id, sdg_goals):
    bingo_card = BingoCard.query.filter_by(team_id=team_id).first()
    if not bingo_card:
        return
    
    # Get the SDG goal numbers from the event
    new_goals = sdg_goals.get('goals', [])
    
    # Update marked numbers
    marked = set(bingo_card.marked_numbers or [])
    for goal in new_goals:
        # Check if this goal exists in the bingo card
        for row in bingo_card.card_numbers:
            if goal in row:
                marked.add(goal)
    
    bingo_card.marked_numbers = list(marked)
    db.session.commit()

def compress_image(image_data):
    img = Image.open(BytesIO(image_data))
    output = BytesIO()
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    max_size = (1920, 1080)
    if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
        img.thumbnail(max_size, Image.LANCZOS)
    
    img.save(output, format='JPEG', quality=85, optimize=True)
    return output.getvalue()

@bp.route('/')
def index():
    notifications = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template('index.html', notifications=notifications)

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
                    flash(('Please select a team', request.path), 'error')
                    return redirect(url_for('main.create_event'))
                
                team = Team.query.get(team_id)
                if not team:
                    flash(('Invalid team', request.path), 'error')
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
                flash(('Please fill in all event details', request.path), 'error')
                return redirect(url_for('main.create_event'))

            try:
                start_datetime = datetime.strptime(f"{event_date} {start_time}", '%Y-%m-%d %H:%M')
                end_datetime = datetime.strptime(f"{event_date} {end_time}", '%Y-%m-%d %H:%M')
                
                if end_datetime <= start_datetime:
                    flash(('End time must be after start time', request.path), 'error')
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

            update_bingo_card(team.id, sdg_analysis)
            
            return jsonify({
                'success': True,
                'message': f'Event "{title}" has been created successfully!',
                'redirect': url_for('main.events')
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            }), 400

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
    
    team = Team.query.get_or_404(team_id)
    verified = team.team_phrase == team_phrase
    
    return jsonify({
        'success': verified,
        'message': 'Team verified successfully' if verified else 'Invalid team phrase'
    })

@bp.route('/leaderboard')
def leaderboard():
    current_time = datetime.utcnow()
    print(f"Current UTC time: {current_time}")
    
    # Get all verified events
    verified_events = Event.query.join(EventVerification)\
        .filter(EventVerification.verified == True).all()
    print(f"Found {len(verified_events)} verified events")
    
    # Process events and count them per team
    team_counts = {}
    for event in verified_events:
        # Convert event end time to UTC for comparison
        event_tz = pytz.timezone(event.timezone)
        event_end_utc = event_tz.localize(event.end_date).astimezone(pytz.UTC)
        
        if event_end_utc.replace(tzinfo=None) < current_time:
            team_counts[event.team_id] = team_counts.get(event.team_id, 0) + 1
    
    print(f"Team counts: {team_counts}")
    
    # Get teams with their counts
    teams = []
    for team_id, count in team_counts.items():
        team = Team.query.get(team_id)
        if team:
            teams.append((team, count))
    
    # Sort by count descending
    teams.sort(key=lambda x: x[1], reverse=True)
    
    ranked_teams = [(rank, team, event_count) for rank, (team, event_count) in enumerate(teams, start=1)]
    return render_template('leaderboard.html', ranked_teams=ranked_teams)

@bp.route('/team/<int:team_id>')
def team(team_id):
    team = Team.query.get_or_404(team_id)
    events = team.events.order_by(Event.start_date.desc()).all()
    bingo_card = BingoCard.query.filter_by(team_id=team_id).first()
    
    # Collect all unique SDG goals from team's events
    team_sdg_goals = set()
    for event in events:
        if event.sdg_goals and 'goals' in event.sdg_goals:
            team_sdg_goals.update(event.sdg_goals['goals'])
    
    # Create a list of all SDG goals with their status
    all_sdg_goals = [
        {
            'number': i,
            'description': SDG_DESCRIPTIONS[i],
            'achieved': i in team_sdg_goals
        } for i in range(1, 18)
    ]
    
    return render_template('team.html', 
                         team=team, 
                         events=events, 
                         bingo_card=bingo_card,
                         sdg_descriptions=SDG_DESCRIPTIONS,
                         all_sdg_goals=all_sdg_goals)

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/api/create_team', methods=['POST'])
def create_team():
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('name') or not data.get('team_phrase') or not data.get('members'):
            return jsonify({
                'message': 'Please fill in all required fields'
            }), 400
        
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
        db.session.flush()
        
        # Add members
        for i, member_name in enumerate(data['members']):
            if member_name.strip():
                member = TeamMember(
                    name=member_name.strip(),
                    team_id=team.id,
                    is_captain=(i == 0)
                )
                db.session.add(member)

        # Generate and add bingo card
        sdg_numbers = list(range(1, 18))  # SDG goals 1-17
        random.shuffle(sdg_numbers)

        # Create empty 4x4 grid
        bingo_grid = [[None] * 4 for _ in range(4)]

        # Take first 16 numbers for the 4x4 grid
        selected_numbers = sdg_numbers[:16]
        
        # Fill the grid row by row
        for i in range(4):
            for j in range(4):
                bingo_grid[i][j] = selected_numbers[i * 4 + j]

        bingo_card = BingoCard(
            team_id=team.id,
            card_numbers=bingo_grid,
            marked_numbers=[]
        )
        db.session.add(bingo_card)
        
        db.session.commit()
        
        # Use the create_event route path instead of the API path
        flash(('Team created successfully!', url_for('main.create_event')), 'success')
        
        return jsonify({
            'message': 'Team created successfully',
            'team_id': team.id,
            'bingo_card': bingo_grid
        }), 201

    except Exception as e:
        db.session.rollback()
        flash((f'An error occurred: {str(e)}', url_for('main.create_event')), 'error')
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
    from datetime import datetime
    import pytz
    
    all_events = Event.query.all()
    upcoming_events = []
    past_events = []
    now = datetime.utcnow()  # Get naive UTC time
    
    for event in all_events:
        # Convert event times to naive UTC for comparison
        event_tz = pytz.timezone(event.timezone)
        event_start = event_tz.localize(event.start_date).astimezone(pytz.UTC).replace(tzinfo=None)
        event_end = event_tz.localize(event.end_date).astimezone(pytz.UTC).replace(tzinfo=None)
        
        if event_start > now:
            upcoming_events.append(event)
        else:
            past_events.append(event)
    
    upcoming_events.sort(key=lambda x: x.start_date)
    past_events.sort(key=lambda x: x.start_date, reverse=True)
    
    return render_template('events.html', 
                         upcoming_events=upcoming_events,
                         past_events=past_events,
                         SDG_DESCRIPTIONS=SDG_DESCRIPTIONS,
                         now=now)

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

@bp.route('/api/team/<int:team_id>/bingo_card')
def get_team_bingo_card(team_id):
    bingo_card = BingoCard.query.filter_by(team_id=team_id).first()
    if not bingo_card:
        return jsonify({'message': 'Bingo card not found'}), 404
    
    return jsonify({
        'card_numbers': bingo_card.card_numbers,
        'marked_numbers': bingo_card.marked_numbers
    })

@bp.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        data = request.get_json()
        team_phrase = data.get('team_phrase')
        
        # Get the event
        event = Event.query.get_or_404(event_id)
        team_id = event.team_id
        
        # Convert event time to UTC for comparison
        event_tz = pytz.timezone(event.timezone)
        event_start_utc = event_tz.localize(event.start_date).astimezone(pytz.UTC)
        now_utc = datetime.now(pytz.UTC)
        
        # Check if event is in the future
        if event_start_utc <= now_utc:
            return jsonify({'message': 'Cannot delete past events'}), 400
        
        # Verify team phrase
        team = Team.query.get(event.team_id)
        if not team or team.team_phrase != team_phrase:
            return jsonify({'message': 'Invalid team phrase'}), 403
        
        # Delete the event
        db.session.delete(event)
                # Update bingo card
        bingo_card = BingoCard.query.filter_by(team_id=team_id).first()
        if bingo_card:
            # Get all remaining events for this team
            remaining_events = Event.query.filter_by(team_id=team_id).all()
            
            # Collect all SDG goals from remaining events
            marked = set()
            for remaining_event in remaining_events:
                if remaining_event.sdg_goals and 'goals' in remaining_event.sdg_goals:
                    marked.update(remaining_event.sdg_goals['goals'])
            
            # Update bingo card with remaining marked numbers
            bingo_card.marked_numbers = list(marked)
        db.session.commit()
        
        return jsonify({'message': 'Event deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

@bp.route('/learn-unsdg')
def learn_unsdg():
    sdg_details = {
        1: {
            "title": "No Poverty",
            "description": "Imagine a world where everyone has enough for their piggy banks and no one ever has to worry about money again!"
        },
        2: {
            "title": "Zero Hunger",
            "description": "A planet where your favourite foods are always on the menu, and no one ever goes to bed with a growling tummy."
        },
        3: {
            "title": "Good Health and Well-being",
            "description": "A life where doctors are superheroes, and everyone feels like they just stepped out of a spa!"
        },
        4: {
            "title": "Quality Education",
            "description": "A world full of exciting classrooms and cool gadgets where everyone learns awesome things every day."
        },
        5: {
            "title": "Gender Equality",
            "description": "A place where anyone can be a boss, and everyone’s talents shine, no matter who they are!"
        },
        6: {
            "title": "Clean Water and Sanitation",
            "description": "Crystal-clear water for everyone, like having your own personal waterfall on tap."
        },
        7: {
            "title": "Affordable and Clean Energy",
            "description": "Power that’s as green as grass, keeping everything running without a drop of pollution."
        },
        8: {
            "title": "Decent Work and Economic Growth",
            "description": "Dream jobs for everyone, where work is as fun as a game and everyone shares in the success."
        },
        9: {
            "title": "Industry, Innovation and Infrastructure",
            "description": "Building the future with flying cars, smart cities, and robots helping us out!"
        },
        10: {
            "title": "Reduced Inequalities",
            "description": "A world where everyone gets a fair shot at success, whether you're from the big city or a tiny village."
        },
        11: {
            "title": "Sustainable Cities and Communities",
            "description": "Cities so eco-friendly they look like they’re straight out of a nature documentary."
        },
        12: {
            "title": "Responsible Consumption and Production",
            "description": "Using just what we need, so there’s always enough for everyone, forever."
        },
        13: {
            "title": "Climate Action",
            "description": "Team Earth fighting climate change like superheroes battling the biggest villain."
        },
        14: {
            "title": "Life Below Water",
            "description": "Oceans so clean that dolphins and sea turtles would throw parties for us."
        },
        15: {
            "title": "Life on Land",
            "description": "Forests full of happy trees and wildlife, where nature and people live in perfect harmony."
        },
        16: {
            "title": "Peace, Justice and Strong Institutions",
            "description": "A world where disputes are solved with teamwork, not fights, and everyone plays fair."
        },
        17: {
            "title": "Partnerships for the Goals",
            "description": "The ultimate team-up where countries and people join forces like a global superhero squad to save the day!"
        }
    }
    return render_template('learn_unsdg.html', sdg_details=sdg_details)

@bp.route('/sponsors')
def sponsors():
    return render_template('sponsors.html')

@bp.route('/api/teams/<int:team_id>/members', methods=['POST'])
def add_team_member(team_id):
    data = request.get_json()
    team = Team.query.get_or_404(team_id)
    
    if not team.team_phrase == data.get('team_phrase'):
        return jsonify({'message': 'Invalid team phrase'}), 403
    
    new_member_name = data.get('name', '').strip()
    if not new_member_name:
        return jsonify({'message': 'Member name is required'}), 400
        
    # Check if member already exists
    existing_member = TeamMember.query.filter_by(
        team_id=team_id, 
        name=new_member_name
    ).first()
    
    if existing_member:
        return jsonify({'message': 'Member already exists'}), 400
        
    new_member = TeamMember(
        name=new_member_name,
        team_id=team_id,
        is_captain=False
    )
    
    try:
        db.session.add(new_member)
        db.session.commit()
        return jsonify({'message': 'Member added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@bp.route('/api/teams/<int:team_id>/captain', methods=['PUT'])
def change_team_captain(team_id):
    data = request.get_json()
    team = Team.query.get_or_404(team_id)
    
    if not team.team_phrase == data.get('team_phrase'):
        return jsonify({'message': 'Invalid team phrase'}), 403
    
    new_captain_id = data.get('new_captain_id')
    if not new_captain_id:
        return jsonify({'message': 'New captain ID is required'}), 400
        
    try:
        # Remove current captain
        current_captain = TeamMember.query.filter_by(
            team_id=team_id, 
            is_captain=True
        ).first()
        if current_captain:
            current_captain.is_captain = False
            
        # Set new captain
        new_captain = TeamMember.query.get(new_captain_id)
        if not new_captain or new_captain.team_id != team_id:
            return jsonify({'message': 'Invalid team member'}), 400
            
        new_captain.is_captain = True
        db.session.commit()
        return jsonify({'message': 'Captain updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@bp.route('/api/teams/<int:team_id>/members/<int:member_id>', methods=['DELETE'])
def delete_team_member(team_id, member_id):
    data = request.get_json()
    team = Team.query.get_or_404(team_id)
    
    if not team.team_phrase == data.get('team_phrase'):
        return jsonify({'message': 'Invalid team phrase'}), 403
        
    member = TeamMember.query.get_or_404(member_id)
    
    if member.team_id != team_id:
        return jsonify({'message': 'Member does not belong to this team'}), 400
        
    if member.is_captain:
        return jsonify({'message': 'Cannot delete team captain'}), 400
        
    try:
        db.session.delete(member)
        db.session.commit()
        return jsonify({'message': 'Member deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@bp.route('/api/events/<int:event_id>/verify', methods=['POST'])
def submit_verification(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        team_phrase = request.form.get('team_phrase')
        is_update = request.form.get('is_update') == 'true'
        
        team = Team.query.get(event.team_id)
        if not team or team.team_phrase != team_phrase:
            return jsonify({'message': 'Invalid team phrase'}), 403
            
        if 'photo' not in request.files:
            return jsonify({'message': 'No photo uploaded'}), 400
            
        photo = request.files['photo']
        if photo.filename == '':
            return jsonify({'message': 'No photo selected'}), 400
            
        if not photo.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return jsonify({'message': 'Invalid file type'}), 400
        
        photo_data = photo.read()
        if len(photo_data) > 5 * 1024 * 1024:  # 5MB limit
            return jsonify({'message': 'Photo size exceeds 5MB limit'}), 400
        
        compressed_photo_data = compress_image(photo_data)
        
        if is_update and event.verification:
            # Update existing verification
            event.verification.photo_data = compressed_photo_data
            event.verification.photo_filename = secure_filename(photo.filename)
            event.verification.mime_type = photo.content_type
            event.verification.verified = False
            event.verification.verified_at = None
        else:
            # Create new verification
            verification = EventVerification(
                event_id=event_id,
                team_id=team.id,
                photo_data=compressed_photo_data,
                photo_filename=secure_filename(photo.filename),
                mime_type=photo.content_type
            )
            db.session.add(verification)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Verification {"updated" if is_update else "submitted"} successfully',
            'verification_id': event.verification.id if is_update else verification.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@bp.route('/verification_photo/<int:verification_id>')
def get_verification_photo(verification_id):
    verification = EventVerification.query.get_or_404(verification_id)
    return send_file(
        BytesIO(verification.photo_data),
        mimetype=verification.mime_type,
        as_attachment=False,
        download_name=verification.photo_filename
    )
