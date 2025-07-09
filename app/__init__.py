import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from config import Config
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    csrf.init_app(app)

    # Import models here to avoid circular imports
    from app import models

    # Register CLI commands
    from app.cli import register_commands
    register_commands(app)

    # Security headers
    csp = {
        'default-src': "'self'",
        'img-src': "'self' data: https:",
        'script-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
        'font-src': "'self' https://fonts.gstatic.com https://cdn.jsdelivr.net",
        'frame-ancestors': "'none'",
        'form-action': "'self'"
    }
    
    Talisman(app,
             force_https=True,
             strict_transport_security=True,
             session_cookie_secure=True,
             session_cookie_http_only=True,
             content_security_policy=csp)

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.context_processor
    def utility_processor():
        return {'now': datetime.utcnow()}

    return app 