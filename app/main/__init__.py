from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes  # Move this import to the end of the file


