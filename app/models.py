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
    members = db.relationship('TeamMember', backref='team', lazy='dynamic', 
                            cascade='all, delete-orphan')
    events = db.relationship('Event', backref='team', lazy='dynamic',
                           cascade='all, delete-orphan')
    bingo_card = db.relationship('BingoCard', backref='team', uselist=False,
                                cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'team_phrase': self.team_phrase,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

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
    team_id = db.Column(db.Integer, db.ForeignKey('team.id', ondelete='CASCADE'), nullable=False)
    sdg_goals = db.Column(JSONType)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'timezone': self.timezone,
            'location': self.location,
            'team_id': self.team_id,
            'sdg_goals': self.sdg_goals,
            'created_at': self.created_at
        }

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id', ondelete='CASCADE'), nullable=False)
    is_captain = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('team_id', 'name', name='unique_member_per_team'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'team_id': self.team_id,
            'is_captain': self.is_captain
        }

class BingoCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id', ondelete='CASCADE'), nullable=False)
    card_numbers = db.Column(JSONType)
    marked_numbers = db.Column(JSONType)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'card_numbers': self.card_numbers,
            'marked_numbers': self.marked_numbers,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Notification {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class EventVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id', ondelete='CASCADE'), nullable=False)
    photo_data = db.Column(db.LargeBinary, nullable=False)
    photo_filename = db.Column(db.String(256), nullable=False)
    mime_type = db.Column(db.String(64), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)

    # Add these relationships
    event = db.relationship('Event', backref=db.backref('verification', uselist=False))
    team = db.relationship('Team', backref=db.backref('verifications', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'team_id': self.team_id,
            'photo_filename': self.photo_filename,
            'mime_type': self.mime_type,
            'verified': self.verified,
            'submitted_at': self.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if self.submitted_at else None,
            'verified_at': self.verified_at.strftime('%Y-%m-%d %H:%M:%S') if self.verified_at else None
        }
