#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ragflow-MinerU Integration Application Factory

This module contains the Flask application factory and configuration.
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException

from backend.config.settings import get_config
from backend.config.database import init_db
from backend.utils.logging_config import setup_logging
from backend.utils.error_handlers import register_error_handlers
from backend.utils.middleware import register_middleware

# Import blueprints
from backend.api.auth.views import auth_bp
from backend.api.users.views import users_bp
from backend.api.documents.views import documents_bp
from backend.api.mineru.views import mineru_bp
from backend.api.permissions.views import permissions_bp
from backend.api.health.views import health_bp


def create_app(config_name=None):
    """
    Application factory pattern for creating Flask app instances.
    
    Args:
        config_name (str): Configuration name ('development', 'production', 'testing')
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Setup logging
    setup_logging(app)
    
    # Initialize extensions
    init_extensions(app)
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register middleware
    register_middleware(app)
    
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for load balancers and monitoring."""
        return jsonify({
            'status': 'healthy',
            'version': app.config.get('VERSION', '1.0.0'),
            'environment': app.config.get('ENVIRONMENT', 'development'),
            'timestamp': request.headers.get('X-Request-ID', 'unknown')
        })
    
    # Add application info endpoint
    @app.route('/info')
    def app_info():
        """Application information endpoint."""
        return jsonify({
            'name': 'Ragflow-MinerU Integration',
            'version': app.config.get('VERSION', '1.0.0'),
            'description': 'High-precision document parsing with multi-user management',
            'environment': app.config.get('ENVIRONMENT', 'development'),
            'features': {
                'mineru_integration': True,
                'multi_user_support': True,
                'concurrent_processing': True,
                'permission_management': True,
                'real_time_monitoring': True
            }
        })
    
    return app


def init_extensions(app):
    """
    Initialize Flask extensions.
    
    Args:
        app (Flask): Flask application instance
    """
    # CORS configuration
    CORS(app, 
         origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'])
    
    # JWT configuration
    jwt = JWTManager(app)
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'message': 'Please log in again'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Invalid token',
            'message': 'Token verification failed'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Authorization required',
            'message': 'Request does not contain an access token'
        }), 401


def register_blueprints(app):
    """
    Register application blueprints.
    
    Args:
        app (Flask): Flask application instance
    """
    api_prefix = app.config.get('API_PREFIX', '/api/v1')
    
    # Register API blueprints
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix=api_prefix)
    app.register_blueprint(users_bp, url_prefix=api_prefix)
    app.register_blueprint(documents_bp, url_prefix=api_prefix)
    app.register_blueprint(mineru_bp, url_prefix=api_prefix)
    app.register_blueprint(permissions_bp, url_prefix=api_prefix)
    
    # Log registered routes in development
    if app.config.get('DEBUG'):
        app.logger.info("Registered routes:")
        for rule in app.url_map.iter_rules():
            app.logger.info(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")


def create_celery_app(app=None):
    """
    Create Celery application for background tasks.
    
    Args:
        app (Flask): Flask application instance
        
    Returns:
        Celery: Configured Celery application
    """
    from celery import Celery
    
    app = app or create_app()
    
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND'),
        broker=app.config.get('CELERY_BROKER_URL')
    )
    
    # Update Celery configuration
    celery.conf.update(
        task_serializer=app.config.get('CELERY_TASK_SERIALIZER', 'json'),
        accept_content=app.config.get('CELERY_ACCEPT_CONTENT', ['json']),
        result_serializer=app.config.get('CELERY_RESULT_SERIALIZER', 'json'),
        timezone=app.config.get('CELERY_TIMEZONE', 'UTC'),
        enable_utc=True,
        task_track_started=True,
        task_time_limit=app.config.get('TASK_TIMEOUT', 1800),
        task_soft_time_limit=app.config.get('TASK_TIMEOUT', 1800) - 60,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
    )
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery


if __name__ == '__main__':
    # Development server
    app = create_app('development')
    
    # Get configuration
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', True)
    
    app.logger.info(f"Starting Ragflow-MinerU Integration server on {host}:{port}")
    app.logger.info(f"Debug mode: {debug}")
    app.logger.info(f"Environment: {app.config.get('ENVIRONMENT', 'development')}")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )