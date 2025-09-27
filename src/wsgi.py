#!/usr/bin/env python3
"""
Production Flask Application Entry Point

This module provides production-ready configuration for the Flask application,
designed to work with various hosting platforms like Render, Railway, Heroku, etc.
"""

import os
from .app import app
from flask import request, redirect

# Production configuration
class ProductionConfig:
    """Production configuration settings"""
    DEBUG = False
    TESTING = False
    # Set secret key from environment or use a default for development
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    # Force HTTPS in production (optional)
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'false').lower() == 'true'

def create_app():
    """Create and configure the Flask application for production"""
    
    # Apply production configuration
    app.config.from_object(ProductionConfig)
    
    # Force HTTPS redirects if enabled
    if app.config.get('FORCE_HTTPS'):
        @app.before_request
        def force_https():
            if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
                return redirect(request.url.replace('http://', 'https://'))
    
    # Add production-specific logging
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        # Set up file logging
        file_handler = RotatingFileHandler('logs/flbb_statistics.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('FLBB Statistics application startup')
    
    return app

# For production WSGI servers (gunicorn, uWSGI, etc.)
application = create_app()

if __name__ == '__main__':
    # This will only run when called directly (for local testing)
    # Production should use gunicorn or similar WSGI server
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    application.run(host=host, port=port, debug=False)