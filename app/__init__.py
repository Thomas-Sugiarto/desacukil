from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config
from dotenv import load_dotenv
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
load_dotenv()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Initialize Flask-Mail
    from app.core.email import mail
    mail.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Register context processors
    @app.context_processor
    def inject_site_settings():
        """Make site_settings available to all templates"""
        from app.models.setting import Setting
        try:
            site_settings = Setting.get_public_settings()
            return {'site_settings': site_settings}
        except Exception as e:
            # Return default settings if database is not initialized
            return {
                'site_settings': {
                    'site_name': 'Portal Desa Digital',
                    'site_description': 'Sistem Informasi dan Layanan Desa',
                    'contact_email': 'info@desa.go.id',
                    'contact_phone': '021-12345678',
                    'address': 'Jl. Raya Desa No. 123'
                }
            }
    
    @app.context_processor
    def inject_navigation_categories():
        """Make navigation categories available to all templates"""
        from app.models.content import Category
        try:
            nav_categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
            return {'nav_categories': nav_categories}
        except Exception:
            return {'nav_categories': []}
    
    # Register blueprints
    from app.blueprints.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.blueprints.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.blueprints.editor import bp as editor_bp
    app.register_blueprint(editor_bp, url_prefix='/editor')
    
    from app.blueprints.publisher import bp as publisher_bp
    app.register_blueprint(publisher_bp, url_prefix='/publisher')
    
    from app.blueprints.public import bp as public_bp
    app.register_blueprint(public_bp)
    
    # Register template filters and globals
    from app.core.helpers import register_template_helpers
    register_template_helpers(app)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app