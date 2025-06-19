"""
Cursor Autopilot API Package

This package provides REST API endpoints for managing configuration,
taking screenshots, and controlling the autopilot system.
"""

__version__ = "1.0.0"
__author__ = "Cursor Autopilot"

from flask import Flask

def create_app(config_path=None):
    """
    Application factory for creating Flask app instances.
    
    Args:
        config_path (str, optional): Path to configuration file
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_path:
        app.config['CONFIG_PATH'] = config_path
    
    # Register blueprints
    from .config_endpoints import config_bp
    from .slack_endpoints import slack_bp
    
    app.register_blueprint(config_bp, url_prefix='/api')
    app.register_blueprint(slack_bp)
    
    # Error handlers
    from .errors import register_error_handlers
    register_error_handlers(app)
    
    # Middleware
    from .auth import setup_auth_middleware
    setup_auth_middleware(app)
    
    return app 