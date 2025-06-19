"""
Main Flask application for the Cursor Autopilot API.

This is the main entry point for the API server, replacing the old slack_bot.py
with a modular structure that supports both configuration management and 
Slack integration.
"""

import os
import logging
from flask import Flask, jsonify
from src.utils.colored_logging import setup_colored_logging

# Setup logging
debug_mode = os.getenv("CURSOR_AUTOPILOT_DEBUG", "false").lower() == "true"
setup_colored_logging(debug=debug_mode)
logger = logging.getLogger(__name__)

def create_production_app():
    """
    Create the Flask application for production use.
    
    Returns:
        Flask: Configured Flask application
    """
    # Import create_app function
    from . import create_app
    
    # Find config file
    from src.config.loader import find_config_file
    config_path = find_config_file()
    
    # Create app using factory
    app = create_app(config_path=config_path)
    
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        return jsonify({
            "status": "healthy",
            "service": "cursor-autopilot-api",
            "version": "1.0.0"
        })
    
    # Add API info endpoint
    @app.route('/api/info')
    def api_info():
        """API information endpoint."""
        return jsonify({
            "name": "Cursor Autopilot API",
            "version": "1.0.0",
            "description": "API for managing Cursor Autopilot configuration and operations",
            "endpoints": {
                "config": {
                    "GET /api/config": "Get current configuration",
                    "POST /api/config": "Update configuration"
                },
                "slack": {
                    "POST /cursor": "Slack slash command handler"
                },
                "health": {
                    "GET /health": "Health check"
                }
            }
        })
    
    return app

# Create app instance for WSGI
app = create_production_app()

if __name__ == "__main__":
    """Run the Flask application in development mode."""
    logger.info("Starting Cursor Autopilot API server...")
    
    # Development configuration
    app.config['DEBUG'] = debug_mode
    
    # Run with development server
    port = int(os.getenv('FLASK_PORT', 5005))
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    
    logger.info(f"Server starting on {host}:{port}")
    logger.info("Available endpoints:")
    logger.info("  - GET  /health                 - Health check")
    logger.info("  - GET  /api/info               - API information")
    logger.info("  - GET  /api/config             - Get configuration")
    logger.info("  - POST /api/config             - Update configuration")
    logger.info("  - POST /cursor                 - Slack commands")
    
    app.run(host=host, port=port, debug=debug_mode) 