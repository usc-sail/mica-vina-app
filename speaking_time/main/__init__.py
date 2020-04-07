from flask import Blueprint

bp = Blueprint('main', __name__)

from speaking_time.main import routes
