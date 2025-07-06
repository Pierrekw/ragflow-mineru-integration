#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Package for Ragflow-MinerU Integration

This package provides comprehensive configuration management for the application,
including database, cache, security, API, services, and logging configurations.
"""

from .settings import BaseConfig, DevelopmentConfig, ProductionConfig, TestingConfig, get_config
from .database import (
    init_db, get_db, create_tables, drop_tables, migrate_database,
    seed_database, check_database_connection, get_database_info
)
from .cache import CacheConfig, Cache, cached
from .security import SecurityConfig
from .api_config import APIConfig
from .services import ServicesManager, services, get_service_config, is_service_enabled
from .celery_config import make_celery, get_task_queues, get_task_routes
from .logging_config import LoggingConfig, logging_config, setup_logging, get_logger
# from .middleware import register_middleware
# from .error_handlers import register_error_handlers

__all__ = [
    # Core configuration classes
    'BaseConfig',
    'DevelopmentConfig', 
    'ProductionConfig',
    'TestingConfig',
    'get_config',
    
    # Database
    'init_db',
    'get_db',
    'create_tables',
    'drop_tables',
    'migrate_database',
    'seed_database',
    'check_database_connection',
    'get_database_info',
    
    # Cache
    'CacheConfig',
    'Cache',
    'cached',
    
    # Security
    'SecurityConfig',
    
    # API
    'APIConfig',
    
    # Services
    'ServicesManager',
    'services',
    'get_service_config',
    'is_service_enabled',
    
    # Celery
    'make_celery',
    'get_task_queues',
    'get_task_routes',
    
    # Logging
    'LoggingConfig',
    'logging_config',
    'setup_logging',
    'get_logger',
    
    # Middleware and error handling
    # 'register_middleware',
    # 'register_error_handlers'
]


def init_app_config(app, config_name=None):
    """
    Initialize all application configurations.
    
    Args:
        app: Flask application instance
        config_name: Configuration name (development, production, testing)
    """
    # Load base configuration
    if config_name:
        config_map = {
            'development': DevelopmentConfig,
            'production': ProductionConfig,
            'testing': TestingConfig
        }
        config_class = config_map.get(config_name, DevelopmentConfig)
        app.config.from_object(config_class)
    
    # Initialize database
    init_db(app)
    
    # Initialize cache
    cache_config = CacheConfig(app)
    
    # Initialize security
    security_config = SecurityConfig(app)
    
    # Initialize API configuration
    api_config = APIConfig(app)
    
    # Initialize services
    services.init_app(app)
    
    # Initialize logging
    setup_logging(app)
    
    # Register middleware
    # register_middleware(app)
    
    # Register error handlers
    # register_error_handlers(app)
    
    return app


def get_config_info(app):
    """
    Get comprehensive configuration information.
    
    Args:
        app: Flask application instance
        
    Returns:
        Dictionary containing configuration information
    """
    info = {
        'environment': app.config.get('ENV', 'unknown'),
        'debug': app.config.get('DEBUG', False),
        'testing': app.config.get('TESTING', False),
        'database': get_database_info(),
        'services': services.get_service_status() if hasattr(services, 'get_service_status') else {},
        'logging': logging_config.get_log_stats() if hasattr(logging_config, 'get_log_stats') else {},
        'cache': {
            'enabled': app.config.get('CACHE_ENABLED', False),
            'type': app.config.get('CACHE_TYPE', 'simple'),
            'redis_url': app.config.get('CACHE_REDIS_URL', 'N/A')
        },
        'security': {
            'jwt_enabled': app.config.get('JWT_ENABLED', False),
            'cors_enabled': app.config.get('CORS_ENABLED', False),
            'rate_limiting': app.config.get('RATE_LIMITING_ENABLED', False)
        },
        'api': {
            'version': app.config.get('API_VERSION', 'v1'),
            'prefix': app.config.get('API_PREFIX', '/api'),
            'title': app.config.get('API_TITLE', 'Ragflow-MinerU Integration API')
        }
    }
    
    return info


def validate_config(app):
    """
    Validate application configuration.
    
    Args:
        app: Flask application instance
        
    Returns:
        Dictionary containing validation results
    """
    errors = []
    warnings = []
    
    # Check required configuration
    required_configs = ['SECRET_KEY', 'DATABASE_URL']
    for config_key in required_configs:
        if not app.config.get(config_key):
            errors.append(f"Missing required configuration: {config_key}")
    
    # Check database connection
    try:
        db_info = get_database_info()
        if not db_info.get('connected', False):
            errors.append("Database connection failed")
    except Exception as e:
        errors.append(f"Database validation error: {str(e)}")
    
    # Validate services configuration
    if hasattr(services, 'validate_configurations'):
        service_errors = services.validate_configurations()
        for service, service_errors_list in service_errors.items():
            for error in service_errors_list:
                warnings.append(f"Service {service}: {error}")
    
    # Check security configuration
    if app.config.get('ENV') == 'production':
        if app.config.get('DEBUG', False):
            warnings.append("Debug mode is enabled in production")
        
        if not app.config.get('JWT_SECRET_KEY'):
            errors.append("JWT_SECRET_KEY is required in production")
        
        if not app.config.get('ENCRYPTION_KEY'):
            errors.append("ENCRYPTION_KEY is required in production")
    
    # Check file upload configuration
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder:
        import os
        if not os.path.exists(upload_folder):
            warnings.append(f"Upload folder does not exist: {upload_folder}")
        elif not os.access(upload_folder, os.W_OK):
            errors.append(f"Upload folder is not writable: {upload_folder}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def create_app_factory(config_name=None):
    """
    Create Flask application factory with configuration.
    
    Args:
        config_name: Configuration name
        
    Returns:
        Configured Flask application
    """
    from flask import Flask
    
    app = Flask(__name__)
    
    # Initialize configuration
    init_app_config(app, config_name)
    
    # Validate configuration
    validation_result = validate_config(app)
    if not validation_result['valid']:
        logger = get_logger('config')
        logger.error(f"Configuration validation failed: {validation_result['errors']}")
        if validation_result['warnings']:
            logger.warning(f"Configuration warnings: {validation_result['warnings']}")
    
    return app