#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration settings for Ragflow-MinerU Integration

This module contains configuration classes for different environments.
"""

import os
from datetime import timedelta
from typing import List, Optional


class BaseConfig:
    """Base configuration class with common settings."""
    
    # Application settings
    VERSION = '1.0.0'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Database settings
    DB_TYPE = os.environ.get('DB_TYPE', 'mysql')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_NAME = os.environ.get('DB_NAME', 'ragflow_mineru')
    DB_USER = os.environ.get('DB_USER', 'ragflow')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    DB_CHARSET = os.environ.get('DB_CHARSET', 'utf8mb4')
    
    # Database connection pool settings
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))
    DB_MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', 20))
    DB_POOL_TIMEOUT = int(os.environ.get('DB_POOL_TIMEOUT', 30))
    DB_POOL_RECYCLE = int(os.environ.get('DB_POOL_RECYCLE', 3600))
    
    # Redis settings
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
    REDIS_URL = os.environ.get('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')
    
    # Elasticsearch settings
    ES_HOST = os.environ.get('ES_HOST', 'localhost')
    ES_PORT = int(os.environ.get('ES_PORT', 9200))
    ES_USER = os.environ.get('ES_USER', '')
    ES_PASSWORD = os.environ.get('ES_PASSWORD', '')
    ES_INDEX_PREFIX = os.environ.get('ES_INDEX_PREFIX', 'ragflow_mineru')
    
    # MinIO/S3 settings
    MINIO_HOST = os.environ.get('MINIO_HOST', 'localhost')
    MINIO_PORT = int(os.environ.get('MINIO_PORT', 9000))
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
    MINIO_BUCKET = os.environ.get('MINIO_BUCKET', 'ragflow-documents')
    MINIO_SECURE = os.environ.get('MINIO_SECURE', 'false').lower() == 'true'
    
    # MinerU service settings
    MINERU_API_URL = os.environ.get('MINERU_API_URL', 'http://localhost:8001')
    MINERU_API_KEY = os.environ.get('MINERU_API_KEY', '')
    MINERU_TIMEOUT = int(os.environ.get('MINERU_TIMEOUT', 300))
    MINERU_MAX_RETRIES = int(os.environ.get('MINERU_MAX_RETRIES', 3))
    MINERU_BATCH_SIZE = int(os.environ.get('MINERU_BATCH_SIZE', 5))
    
    # GPU settings
    CUDA_VISIBLE_DEVICES = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
    GPU_MEMORY_FRACTION = float(os.environ.get('GPU_MEMORY_FRACTION', 0.8))
    USE_GPU = os.environ.get('USE_GPU', 'true').lower() == 'true'
    
    # File upload settings
    MAX_FILE_SIZE = os.environ.get('MAX_FILE_SIZE', '100MB')
    ALLOWED_EXTENSIONS = os.environ.get(
        'ALLOWED_EXTENSIONS', 
        'pdf,docx,doc,pptx,ppt,xlsx,xls,txt,md'
    ).split(',')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER', './temp')
    
    # Celery settings
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/1')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:{REDIS_PORT}/1')
    CELERY_TASK_SERIALIZER = os.environ.get('CELERY_TASK_SERIALIZER', 'json')
    CELERY_RESULT_SERIALIZER = os.environ.get('CELERY_RESULT_SERIALIZER', 'json')
    CELERY_ACCEPT_CONTENT = os.environ.get('CELERY_ACCEPT_CONTENT', 'json').split(',')
    CELERY_TIMEZONE = os.environ.get('CELERY_TIMEZONE', 'UTC')
    
    # Concurrency settings
    MAX_CONCURRENT_TASKS_PER_USER = int(os.environ.get('MAX_CONCURRENT_TASKS_PER_USER', 2))
    MAX_GLOBAL_CONCURRENT_TASKS = int(os.environ.get('MAX_GLOBAL_CONCURRENT_TASKS', 10))
    TASK_TIMEOUT = int(os.environ.get('TASK_TIMEOUT', 1800))
    TASK_RETRY_DELAY = int(os.environ.get('TASK_RETRY_DELAY', 60))
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))
    JWT_ALGORITHM = 'HS256'
    
    # Password settings
    PASSWORD_HASH_ROUNDS = int(os.environ.get('PASSWORD_HASH_ROUNDS', 12))
    
    # Email settings
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
    FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@ragflow-mineru.com')
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.environ.get('LOG_FORMAT', 'json')
    LOG_FILE = os.environ.get('LOG_FILE', './logs/app.log')
    LOG_MAX_SIZE = os.environ.get('LOG_MAX_SIZE', '10MB')
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # Monitoring settings
    PROMETHEUS_PORT = int(os.environ.get('PROMETHEUS_PORT', 8000))
    METRICS_ENABLED = os.environ.get('METRICS_ENABLED', 'true').lower() == 'true'
    HEALTH_CHECK_ENABLED = os.environ.get('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'
    
    # Rate limiting settings
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 60))
    RATE_LIMIT_PER_HOUR = int(os.environ.get('RATE_LIMIT_PER_HOUR', 1000))
    
    # Cache settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    CACHE_KEY_PREFIX = os.environ.get('CACHE_KEY_PREFIX', 'ragflow_mineru:')
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Security settings
    CSRF_ENABLED = os.environ.get('CSRF_ENABLED', 'true').lower() == 'true'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # API settings
    API_VERSION = os.environ.get('API_VERSION', 'v1')
    API_PREFIX = os.environ.get('API_PREFIX', '/api/v1')
    API_DOCS_ENABLED = os.environ.get('API_DOCS_ENABLED', 'true').lower() == 'true'
    API_RATE_LIMIT = os.environ.get('API_RATE_LIMIT', '100/minute')
    
    # Frontend settings
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    STATIC_FOLDER = os.environ.get('STATIC_FOLDER', './static')
    TEMPLATE_FOLDER = os.environ.get('TEMPLATE_FOLDER', './templates')
    
    # Feature flags
    FEATURE_USER_REGISTRATION = os.environ.get('FEATURE_USER_REGISTRATION', 'true').lower() == 'true'
    FEATURE_SOCIAL_LOGIN = os.environ.get('FEATURE_SOCIAL_LOGIN', 'false').lower() == 'true'
    FEATURE_ADVANCED_ANALYTICS = os.environ.get('FEATURE_ADVANCED_ANALYTICS', 'true').lower() == 'true'
    FEATURE_BATCH_PROCESSING = os.environ.get('FEATURE_BATCH_PROCESSING', 'true').lower() == 'true'
    FEATURE_WEBHOOK_NOTIFICATIONS = os.environ.get('FEATURE_WEBHOOK_NOTIFICATIONS', 'false').lower() == 'true'
    
    # Third-party integrations
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    HUGGINGFACE_TOKEN = os.environ.get('HUGGINGFACE_TOKEN', '')
    WANDB_API_KEY = os.environ.get('WANDB_API_KEY', '')
    
    # Localization
    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'zh-CN')
    SUPPORTED_LANGUAGES = os.environ.get('SUPPORTED_LANGUAGES', 'zh-CN,en-US').split(',')
    TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Shanghai')
    
    # Custom MinerU model paths
    MINERU_LAYOUT_MODEL_PATH = os.environ.get('MINERU_LAYOUT_MODEL_PATH', '')
    MINERU_FORMULA_MODEL_PATH = os.environ.get('MINERU_FORMULA_MODEL_PATH', '')
    MINERU_OCR_MODEL_PATH = os.environ.get('MINERU_OCR_MODEL_PATH', '')
    MINERU_TABLE_MODEL_PATH = os.environ.get('MINERU_TABLE_MODEL_PATH', '')
    
    @property
    def database_url(self) -> str:
        """Generate database URL from configuration."""
        if self.DB_TYPE == 'mysql':
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset={self.DB_CHARSET}"
        elif self.DB_TYPE == 'postgresql':
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_TYPE == 'sqlite':
            return f"sqlite:///{self.DB_NAME}.db"
        else:
            raise ValueError(f"Unsupported database type: {self.DB_TYPE}")
    
    @property
    def elasticsearch_url(self) -> str:
        """Generate Elasticsearch URL from configuration."""
        if self.ES_USER and self.ES_PASSWORD:
            return f"http://{self.ES_USER}:{self.ES_PASSWORD}@{self.ES_HOST}:{self.ES_PORT}"
        return f"http://{self.ES_HOST}:{self.ES_PORT}"
    
    @property
    def minio_endpoint(self) -> str:
        """Generate MinIO endpoint from configuration."""
        protocol = 'https' if self.MINIO_SECURE else 'http'
        return f"{protocol}://{self.MINIO_HOST}:{self.MINIO_PORT}"


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    
    ENVIRONMENT = 'development'
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    DEV_RELOAD = os.environ.get('DEV_RELOAD', 'true').lower() == 'true'
    DEV_DEBUG_TOOLBAR = os.environ.get('DEV_DEBUG_TOOLBAR', 'true').lower() == 'true'
    DEV_PROFILER = os.environ.get('DEV_PROFILER', 'false').lower() == 'true'
    
    # Relaxed security for development
    SESSION_COOKIE_SECURE = False
    CSRF_ENABLED = False
    
    # More verbose logging
    LOG_LEVEL = 'DEBUG'
    
    # Disable rate limiting in development
    RATE_LIMIT_ENABLED = False


class TestingConfig(BaseConfig):
    """Testing environment configuration."""
    
    ENVIRONMENT = 'testing'
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    DB_TYPE = 'sqlite'
    DB_NAME = ':memory:'
    
    # Use separate Redis database for testing
    REDIS_DB = 15
    REDIS_URL = f'redis://{BaseConfig.REDIS_HOST}:{BaseConfig.REDIS_PORT}/15'
    
    # Disable external services in testing
    MINERU_API_URL = 'http://mock-mineru:8001'
    
    # Fast password hashing for tests
    PASSWORD_HASH_ROUNDS = 4
    
    # Disable rate limiting in tests
    RATE_LIMIT_ENABLED = False
    
    # Disable email sending in tests
    SMTP_HOST = 'localhost'
    SMTP_PORT = 1025
    
    # Short token expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=1)


class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    
    ENVIRONMENT = 'production'
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    CSRF_ENABLED = True
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Enable all security features
    RATE_LIMIT_ENABLED = True
    
    # Stricter CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []
    
    # Production-specific settings
    WORKERS = int(os.environ.get('WORKERS', 4))
    WORKER_CLASS = os.environ.get('WORKER_CLASS', 'gevent')
    WORKER_CONNECTIONS = int(os.environ.get('WORKER_CONNECTIONS', 1000))
    
    # Enhanced monitoring
    METRICS_ENABLED = True
    HEALTH_CHECK_ENABLED = True


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> BaseConfig:
    """
    Get configuration class based on environment.
    
    Args:
        config_name (str, optional): Configuration name
        
    Returns:
        BaseConfig: Configuration class instance
    """
    if config_name is None:
        config_name = os.environ.get('ENVIRONMENT', 'development')
    
    config_class = config_map.get(config_name, DevelopmentConfig)
    return config_class()


def validate_config(config: BaseConfig) -> List[str]:
    """
    Validate configuration settings.
    
    Args:
        config (BaseConfig): Configuration instance
        
    Returns:
        List[str]: List of validation errors
    """
    errors = []
    
    # Check required settings
    if not config.SECRET_KEY or config.SECRET_KEY == 'dev-secret-key-change-in-production':
        if config.ENVIRONMENT == 'production':
            errors.append("SECRET_KEY must be set in production")
    
    if not config.DB_PASSWORD and config.ENVIRONMENT == 'production':
        errors.append("DB_PASSWORD must be set in production")
    
    if config.ENVIRONMENT == 'production' and not config.CORS_ORIGINS:
        errors.append("CORS_ORIGINS must be configured in production")
    
    # Validate file size format
    try:
        _parse_file_size(config.MAX_FILE_SIZE)
    except ValueError as e:
        errors.append(f"Invalid MAX_FILE_SIZE format: {e}")
    
    return errors


def _parse_file_size(size_str: str) -> int:
    """
    Parse file size string to bytes.
    
    Args:
        size_str (str): Size string like '100MB', '1GB'
        
    Returns:
        int: Size in bytes
    """
    size_str = size_str.upper().strip()
    
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)