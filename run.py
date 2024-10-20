from app import create_app, db
from app.models import User, Team, Event

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create a default team if none exists
        if not Team.query.first():
            default_team = Team(name="Default Team")
            db.session.add(default_team)
            db.session.commit()
    app.run(debug=True)
