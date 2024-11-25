from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Notification
from app import db

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
    return redirect(url_for('admin.manage_notifications'))

@bp.route('/notifications/<int:id>/delete', methods=['POST'])
def delete_notification(id):
    notification = Notification.query.get_or_404(id)
    db.session.delete(notification)
    db.session.commit()
    # flash('Notification deleted successfully!', 'success')
    return redirect(url_for('admin.manage_notifications')) 