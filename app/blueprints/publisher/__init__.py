from flask import Blueprint

bp = Blueprint('publisher', __name__)

from app.blueprints.publisher import routes