from app import create_app, db
from app.models import Team, Event, TeamMember

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Create a test team
        test_team = Team(
            name="Test Team",
            team_phrase="test phrase 123"
        )
        db.session.add(test_team)
        
        # Add some test members
        test_captain = TeamMember(
            name="Test Captain",
            team_id=1,
            is_captain=True
        )
        db.session.add(test_captain)
        
        db.session.commit()
    
    app.run(debug=True)
