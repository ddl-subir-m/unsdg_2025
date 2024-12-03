from dotenv import load_dotenv
from datetime import datetime

from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
load_dotenv()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Add datetime filter
    @app.template_filter('datetime')
    def format_datetime(value):
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                # Try to parse the string into a datetime object
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # If parsing fails, return the original string
                return value
        return value.strftime('%Y-%m-%d %H:%M:%S')

    # Register the filter with your app
    app.jinja_env.filters['datetime'] = format_datetime

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp)

    return app

from app import models  # Import models at the end to avoid circular imports

