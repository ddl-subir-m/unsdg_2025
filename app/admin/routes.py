from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.models import BingoCard, Event, Notification, Team, TeamMember, JSONType
from app import db
from datetime import datetime
import json

from app.admin import bp


@bp.route('/notifications')
def manage_notifications():
    notifications = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template('admin/notifications.html', notifications=notifications)

@bp.route('/notifications/add', methods=['POST'])
def add_notification():
    message = request.form.get('message')
    if message:
        notification = Notification(message=message)
        db.session.add(notification)
        db.session.commit()
        # flash('Notification added successfully!', 'success')
        flash((f'Notification added successfully!', url_for('admin.manage_notifications')), 'success')
    return redirect(url_for('admin.manage_notifications'))

@bp.route('/notifications/<int:id>/delete', methods=['POST'])
def delete_notification(id):
    notification = Notification.query.get_or_404(id)
    db.session.delete(notification)
    db.session.commit()
    # flash('Notification deleted successfully!', 'success')
    flash((f'Notification deleted successfully!', url_for('admin.manage_notifications')), 'success')
    return redirect(url_for('admin.manage_notifications'))

@bp.route('/database')
def manage_database():
    # Get all model classes from your models
    models = {
        'Team': Team,
        'Event': Event,
        'TeamMember': TeamMember,
        'BingoCard': BingoCard,
        'Notification': Notification
    }
    
    # Get counts for each model
    model_counts = {name: db.session.query(model).count() for name, model in models.items()}
    
    return render_template('admin/database.html', models=models, model_counts=model_counts)

@bp.route('/database/<model_name>')
def view_model(model_name):
    models = {
        'Team': Team,
        'Event': Event,
        'TeamMember': TeamMember,
        'BingoCard': BingoCard,
        'Notification': Notification
    }
    
    if model_name not in models:
        flash(('Invalid model name', request.path), 'error')
        return redirect(url_for('admin.manage_database'))
    
    model = models[model_name]
    records = model.query.all()
    records = [record.to_dict() for record in records]  # Convert to dictionaries
    return render_template('admin/view_model.html', model_name=model_name, records=records)

@bp.route('/database/<model_name>/delete/<int:id>', methods=['POST'])
def delete_record(model_name, id):
    models = {
        'Team': Team,
        'Event': Event,
        'TeamMember': TeamMember,
        'BingoCard': BingoCard,
        'Notification': Notification
    }
    
    if model_name not in models:
        flash('Invalid model name', 'error')
        return redirect(url_for('admin.manage_database'))
    
    model = models[model_name]
    record = model.query.get_or_404(id)
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash((f'{model_name} record deleted successfully', request.path), 'success')
    except Exception as e:
        db.session.rollback()
        flash((f'Error deleting record: {str(e)}', request.path), 'error')
    
    return redirect(url_for('admin.view_model', model_name=model_name))

@bp.route('/admin/database/<model_name>/update/<int:id>', methods=['POST'])
def update_record(model_name, id):
    models = {
        'Team': Team,
        'Event': Event,
        'TeamMember': TeamMember,
        'BingoCard': BingoCard,
        'Notification': Notification
    }
    
    if model_name not in models:
        flash('Invalid model name', 'error')
        return redirect(url_for('admin.manage_database'))
    
    model = models[model_name]
    record = model.query.get_or_404(id)
    
    try:
        # Get the form data
        for column in record.__table__.columns:
            if column.name != 'id':  # Skip the ID field
                value = request.form.get(column.name)
                
                # Handle different data types
                if value is not None:
                    if isinstance(column.type, db.Boolean):
                        value = value.lower() == 'true'
                    elif isinstance(column.type, db.Integer):
                        value = int(value) if value.strip() else None
                    elif isinstance(column.type, db.DateTime):
                        value = datetime.strptime(value, '%Y-%m-%dT%H:%M') if value else None
                    elif isinstance(column.type, JSONType):
                        value = json.loads(value) if value else None
                
                setattr(record, column.name, value)
        
        db.session.commit()
        flash((f'{model_name} record updated successfully', request.path), 'success')
    except Exception as e:
        db.session.rollback()
        flash((f'Error updating record: {str(e)}', request.path), 'error')
    
    return redirect(url_for('admin.view_model', model_name=model_name)) 