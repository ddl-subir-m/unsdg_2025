from app import create_app, db
from app.models import Team, Event, TeamMember

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

    app.run(debug=True, host='0.0.0.0', port=5001)