from flask import Blueprint

bp = Blueprint('editor', __name__)

from app.blueprints.editor import routes