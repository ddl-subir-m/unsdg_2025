from app import db
from datetime import datetime
import json
from sqlalchemy.types import TypeDecorator, Text


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_phrase = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    members = db.relationship('TeamMember', backref='team', lazy='dynamic')
    events = db.relationship('Event', backref='team', lazy='dynamic')
    bingo_card = db.relationship('BingoCard', backref='team', uselist=False)

class JSONType(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text(1000))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    timezone = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    sdg_goals = db.Column(JSONType)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    is_captain = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('team_id', 'name', name='unique_member_per_team'),
    )

class BingoCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    card_numbers = db.Column(JSONType, nullable=False)  # 4x4 grid of SDG numbers
    marked_numbers = db.Column(JSONType, default=list)  # List of marked SDG numbers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
