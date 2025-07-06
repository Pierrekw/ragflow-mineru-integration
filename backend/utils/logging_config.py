#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging Configuration for Ragflow-MinerU Integration

This module provides centralized logging configuration.
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(app, log_level: Optional[str] = None):
    """
    Setup application logging configuration.
    
    Args:
        app: Flask application instance
        log_level: Override log level
    """
    # Get configuration
    log_level = log_level or app.config.get('LOG_LEVEL', 'INFO')
    log_format = app.config.get('LOG_FORMAT', 'standard')
    log_file = app.config.get('LOG_FILE')
    log_to_stdout = app.config.get('LOG_TO_STDOUT', False)
    
    # Create logs directory if needed
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = get_formatter(log_format)
    
    # Console handler
    if log_to_stdout or app.config.get('DEBUG'):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=app.config.get('LOG_MAX_SIZE', 10 * 1024 * 1024),  # 10MB
            backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(file_handler)
    
    # Configure Flask app logger
    app.logger.setLevel(getattr(logging, log_level.upper()))
    
    # Configure other loggers
    configure_third_party_loggers(log_level)
    
    app.logger.info(f"Logging configured - Level: {log_level}, Format: {log_format}")


def get_formatter(log_format: str) -> logging.Formatter:
    """
    Get logging formatter based on format type.
    
    Args:
        log_format: Format type ('standard', 'json', 'detailed')
        
    Returns:
        logging.Formatter: Configured formatter
    """
    if log_format == 'json':
        return JsonFormatter()
    elif log_format == 'detailed':
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - '
            '%(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:  # standard
        return logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    """
    
    def format(self, record):
        import json
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info'):
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


def configure_third_party_loggers(log_level: str):
    """
    Configure third-party library loggers.
    
    Args:
        log_level: Log level to set
    """
    # Reduce noise from third-party libraries
    third_party_loggers = {
        'urllib3.connectionpool': 'WARNING',
        'requests.packages.urllib3': 'WARNING',
        'werkzeug': 'WARNING',
        'celery': 'INFO',
        'sqlalchemy.engine': 'WARNING',
        'sqlalchemy.pool': 'WARNING',
        'redis': 'WARNING',
        'elasticsearch': 'WARNING'
    }
    
    for logger_name, level in third_party_loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level))


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


class RequestContextFilter(logging.Filter):
    """
    Filter to add request context to log records.
    """
    
    def filter(self, record):
        from flask import has_request_context, request, g
        
        if has_request_context():
            record.request_id = getattr(g, 'request_id', 'unknown')
            record.user_id = getattr(g, 'current_user_id', 'anonymous')
            record.ip_address = request.remote_addr
            record.method = request.method
            record.url = request.url
        else:
            record.request_id = 'no-request'
            record.user_id = 'system'
            record.ip_address = 'unknown'
            record.method = 'unknown'
            record.url = 'unknown'
        
        return True


def setup_request_logging(app):
    """
    Setup request-specific logging.
    
    Args:
        app: Flask application instance
    """
    # Add request context filter
    request_filter = RequestContextFilter()
    
    for handler in app.logger.handlers:
        handler.addFilter(request_filter)
    
    @app.before_request
    def before_request_logging():
        from flask import g, request
        import uuid
        
        # Generate request ID
        g.request_id = str(uuid.uuid4())[:8]
        g.start_time = datetime.utcnow()
        
        # Log request start
        app.logger.info(
            f"Request started: {request.method} {request.url}",
            extra={
                'request_id': g.request_id,
                'user_agent': request.headers.get('User-Agent', 'unknown')
            }
        )
    
    @app.after_request
    def after_request_logging(response):
        from flask import g
        
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            
            app.logger.info(
                f"Request completed: {response.status_code} - {duration:.3f}s",
                extra={
                    'request_id': getattr(g, 'request_id', 'unknown'),
                    'status_code': response.status_code,
                    'duration': duration
                }
            )
        
        return response


def log_performance(func_name: str, duration: float, **kwargs):
    """
    Log performance metrics.
    
    Args:
        func_name: Function name
        duration: Execution duration in seconds
        **kwargs: Additional context
    """
    logger = get_logger('performance')
    logger.info(
        f"Performance: {func_name} took {duration:.3f}s",
        extra={
            'function': func_name,
            'duration': duration,
            **kwargs
        }
    )


def log_security_event(event_type: str, user_id: str = None, **kwargs):
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        user_id: User ID if applicable
        **kwargs: Additional context
    """
    logger = get_logger('security')
    logger.warning(
        f"Security event: {event_type}",
        extra={
            'event_type': event_type,
            'user_id': user_id or 'unknown',
            **kwargs
        }
    )


def log_business_event(event_type: str, user_id: str = None, **kwargs):
    """
    Log business-related events.
    
    Args:
        event_type: Type of business event
        user_id: User ID if applicable
        **kwargs: Additional context
    """
    logger = get_logger('business')
    logger.info(
        f"Business event: {event_type}",
        extra={
            'event_type': event_type,
            'user_id': user_id or 'unknown',
            **kwargs
        }
    )