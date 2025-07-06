#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging Configuration for Ragflow-MinerU Integration

This module provides comprehensive logging configuration for the application.
"""

import os
import sys
import logging
import logging.config
import logging.handlers
from typing import Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    """
    
    def format(self, record):
        """
        Format log record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            JSON formatted log string
        """
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process': record.process,
            'thread': record.thread
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


class RequestFormatter(logging.Formatter):
    """
    Custom formatter for HTTP request logging.
    """
    
    def format(self, record):
        """
        Format HTTP request log record.
        
        Args:
            record: Log record
            
        Returns:
            Formatted log string
        """
        # Extract request information
        request_id = getattr(record, 'request_id', 'N/A')
        method = getattr(record, 'method', 'N/A')
        url = getattr(record, 'url', 'N/A')
        status_code = getattr(record, 'status_code', 'N/A')
        duration = getattr(record, 'duration', 'N/A')
        user_id = getattr(record, 'user_id', 'N/A')
        ip_address = getattr(record, 'ip_address', 'N/A')
        
        # Format message
        formatted_message = (
            f"[{request_id}] {method} {url} - {status_code} "
            f"({duration}ms) - User: {user_id} - IP: {ip_address}"
        )
        
        # Create new record with formatted message
        record.msg = formatted_message
        record.args = ()
        
        return super().format(record)


class SecurityFormatter(logging.Formatter):
    """
    Custom formatter for security event logging.
    """
    
    def format(self, record):
        """
        Format security event log record.
        
        Args:
            record: Log record
            
        Returns:
            Formatted log string
        """
        # Extract security information
        event_type = getattr(record, 'event_type', 'UNKNOWN')
        user_id = getattr(record, 'user_id', 'N/A')
        ip_address = getattr(record, 'ip_address', 'N/A')
        user_agent = getattr(record, 'user_agent', 'N/A')
        details = getattr(record, 'details', '')
        
        # Format message
        formatted_message = (
            f"SECURITY [{event_type}] User: {user_id} - IP: {ip_address} - "
            f"Agent: {user_agent} - {record.getMessage()}"
        )
        
        if details:
            formatted_message += f" - Details: {details}"
        
        # Create new record with formatted message
        record.msg = formatted_message
        record.args = ()
        
        return super().format(record)


class LoggingConfig:
    """
    Logging configuration manager.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.log_dir = None
        self.log_level = logging.INFO
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        self.json_logging = False
        self.console_logging = True
        self.file_logging = True
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize logging with Flask app.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Load configuration
        self._load_config(app)
        
        # Setup logging
        self._setup_logging()
        
        # Store in app config
        app.config['LOGGING'] = self
        
        # Setup Flask app logger
        self._setup_flask_logger(app)
        
        logging.info("Logging configuration initialized")
    
    def _load_config(self, app):
        """
        Load logging configuration from app config.
        
        Args:
            app: Flask application instance
        """
        # Log directory
        self.log_dir = Path(app.config.get('LOG_DIR', 'logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log level
        log_level_str = app.config.get('LOG_LEVEL', 'INFO').upper()
        self.log_level = getattr(logging, log_level_str, logging.INFO)
        
        # File settings
        self.max_file_size = app.config.get('LOG_MAX_FILE_SIZE', 10 * 1024 * 1024)
        self.backup_count = app.config.get('LOG_BACKUP_COUNT', 5)
        
        # Format settings
        self.json_logging = app.config.get('LOG_JSON_FORMAT', False)
        self.console_logging = app.config.get('LOG_CONSOLE', True)
        self.file_logging = app.config.get('LOG_FILE', True)
    
    def _setup_logging(self):
        """
        Setup logging configuration.
        """
        # Create logging configuration
        config = self._create_logging_config()
        
        # Apply configuration
        logging.config.dictConfig(config)
        
        # Set root logger level
        logging.getLogger().setLevel(self.log_level)
    
    def _create_logging_config(self) -> Dict[str, Any]:
        """
        Create logging configuration dictionary.
        
        Returns:
            Logging configuration
        """
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': self._get_formatters(),
            'handlers': self._get_handlers(),
            'loggers': self._get_loggers(),
            'root': {
                'level': self.log_level,
                'handlers': self._get_root_handlers()
            }
        }
        
        return config
    
    def _get_formatters(self) -> Dict[str, Any]:
        """
        Get logging formatters configuration.
        
        Returns:
            Formatters configuration
        """
        formatters = {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': (
                    '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d '
                    '(%(funcName)s) - %(message)s'
                ),
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'request': {
                '()': RequestFormatter,
                'format': '%(asctime)s [%(levelname)s] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'security': {
                '()': SecurityFormatter,
                'format': '%(asctime)s [%(levelname)s] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        }
        
        if self.json_logging:
            formatters['json'] = {
                '()': JSONFormatter
            }
        
        return formatters
    
    def _get_handlers(self) -> Dict[str, Any]:
        """
        Get logging handlers configuration.
        
        Returns:
            Handlers configuration
        """
        handlers = {}
        
        # Console handler
        if self.console_logging:
            handlers['console'] = {
                'class': 'logging.StreamHandler',
                'level': self.log_level,
                'formatter': 'json' if self.json_logging else 'standard',
                'stream': 'ext://sys.stdout'
            }
        
        # File handlers
        if self.file_logging:
            # Application log
            handlers['app_file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': self.log_level,
                'formatter': 'json' if self.json_logging else 'detailed',
                'filename': str(self.log_dir / 'app.log'),
                'maxBytes': self.max_file_size,
                'backupCount': self.backup_count,
                'encoding': 'utf-8'
            }
            
            # Error log
            handlers['error_file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': logging.ERROR,
                'formatter': 'json' if self.json_logging else 'detailed',
                'filename': str(self.log_dir / 'error.log'),
                'maxBytes': self.max_file_size,
                'backupCount': self.backup_count,
                'encoding': 'utf-8'
            }
            
            # Request log
            handlers['request_file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': logging.INFO,
                'formatter': 'request',
                'filename': str(self.log_dir / 'requests.log'),
                'maxBytes': self.max_file_size,
                'backupCount': self.backup_count,
                'encoding': 'utf-8'
            }
            
            # Security log
            handlers['security_file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': logging.WARNING,
                'formatter': 'security',
                'filename': str(self.log_dir / 'security.log'),
                'maxBytes': self.max_file_size,
                'backupCount': self.backup_count,
                'encoding': 'utf-8'
            }
            
            # Task log
            handlers['task_file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': logging.INFO,
                'formatter': 'json' if self.json_logging else 'detailed',
                'filename': str(self.log_dir / 'tasks.log'),
                'maxBytes': self.max_file_size,
                'backupCount': self.backup_count,
                'encoding': 'utf-8'
            }
        
        return handlers
    
    def _get_loggers(self) -> Dict[str, Any]:
        """
        Get loggers configuration.
        
        Returns:
            Loggers configuration
        """
        loggers = {
            # Application loggers
            'app': {
                'level': self.log_level,
                'handlers': self._get_app_handlers(),
                'propagate': False
            },
            'api': {
                'level': self.log_level,
                'handlers': self._get_app_handlers(),
                'propagate': False
            },
            'services': {
                'level': self.log_level,
                'handlers': self._get_app_handlers(),
                'propagate': False
            },
            'models': {
                'level': self.log_level,
                'handlers': self._get_app_handlers(),
                'propagate': False
            },
            'utils': {
                'level': self.log_level,
                'handlers': self._get_app_handlers(),
                'propagate': False
            },
            
            # Request logger
            'requests': {
                'level': logging.INFO,
                'handlers': ['request_file'] if self.file_logging else [],
                'propagate': False
            },
            
            # Security logger
            'security': {
                'level': logging.WARNING,
                'handlers': ['security_file'] if self.file_logging else [],
                'propagate': False
            },
            
            # Task logger
            'tasks': {
                'level': logging.INFO,
                'handlers': ['task_file'] if self.file_logging else [],
                'propagate': False
            },
            
            # Third-party loggers
            'werkzeug': {
                'level': logging.WARNING,
                'handlers': self._get_app_handlers(),
                'propagate': False
            },
            'celery': {
                'level': logging.INFO,
                'handlers': ['task_file'] if self.file_logging else [],
                'propagate': False
            },
            'peewee': {
                'level': logging.WARNING,
                'handlers': self._get_app_handlers(),
                'propagate': False
            },
            'redis': {
                'level': logging.WARNING,
                'handlers': self._get_app_handlers(),
                'propagate': False
            },
            'elasticsearch': {
                'level': logging.WARNING,
                'handlers': self._get_app_handlers(),
                'propagate': False
            }
        }
        
        return loggers
    
    def _get_root_handlers(self) -> list:
        """
        Get root logger handlers.
        
        Returns:
            List of handler names
        """
        handlers = []
        
        if self.console_logging:
            handlers.append('console')
        
        if self.file_logging:
            handlers.extend(['app_file', 'error_file'])
        
        return handlers
    
    def _get_app_handlers(self) -> list:
        """
        Get application logger handlers.
        
        Returns:
            List of handler names
        """
        handlers = []
        
        if self.console_logging:
            handlers.append('console')
        
        if self.file_logging:
            handlers.extend(['app_file', 'error_file'])
        
        return handlers
    
    def _setup_flask_logger(self, app):
        """
        Setup Flask application logger.
        
        Args:
            app: Flask application instance
        """
        # Remove default Flask handlers
        app.logger.handlers.clear()
        
        # Set Flask logger level
        app.logger.setLevel(self.log_level)
        
        # Add our handlers
        for handler_name in self._get_app_handlers():
            handler = logging.getLogger().handlers[0]  # Get configured handler
            app.logger.addHandler(handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get logger by name.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    def log_request(self, request_id: str, method: str, url: str, 
                   status_code: int, duration: float, user_id: Optional[str] = None,
                   ip_address: Optional[str] = None):
        """
        Log HTTP request.
        
        Args:
            request_id: Request ID
            method: HTTP method
            url: Request URL
            status_code: Response status code
            duration: Request duration in milliseconds
            user_id: User ID (optional)
            ip_address: Client IP address (optional)
        """
        logger = self.get_logger('requests')
        logger.info(
            'Request completed',
            extra={
                'request_id': request_id,
                'method': method,
                'url': url,
                'status_code': status_code,
                'duration': duration,
                'user_id': user_id,
                'ip_address': ip_address
            }
        )
    
    def log_security_event(self, event_type: str, message: str,
                          user_id: Optional[str] = None,
                          ip_address: Optional[str] = None,
                          user_agent: Optional[str] = None,
                          details: Optional[str] = None,
                          level: int = logging.WARNING):
        """
        Log security event.
        
        Args:
            event_type: Type of security event
            message: Event message
            user_id: User ID (optional)
            ip_address: Client IP address (optional)
            user_agent: User agent (optional)
            details: Additional details (optional)
            level: Log level
        """
        logger = self.get_logger('security')
        logger.log(
            level,
            message,
            extra={
                'event_type': event_type,
                'user_id': user_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'details': details
            }
        )
    
    def log_task_event(self, task_id: str, task_name: str, event: str,
                      message: str, **kwargs):
        """
        Log task event.
        
        Args:
            task_id: Task ID
            task_name: Task name
            event: Event type
            message: Event message
            **kwargs: Additional context
        """
        logger = self.get_logger('tasks')
        logger.info(
            message,
            extra={
                'task_id': task_id,
                'task_name': task_name,
                'event': event,
                **kwargs
            }
        )
    
    def get_log_files(self) -> Dict[str, str]:
        """
        Get paths to log files.
        
        Returns:
            Dictionary of log file paths
        """
        if not self.file_logging:
            return {}
        
        return {
            'app': str(self.log_dir / 'app.log'),
            'error': str(self.log_dir / 'error.log'),
            'requests': str(self.log_dir / 'requests.log'),
            'security': str(self.log_dir / 'security.log'),
            'tasks': str(self.log_dir / 'tasks.log')
        }
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics.
        
        Returns:
            Logging statistics
        """
        stats = {
            'log_level': logging.getLevelName(self.log_level),
            'console_logging': self.console_logging,
            'file_logging': self.file_logging,
            'json_logging': self.json_logging,
            'log_dir': str(self.log_dir),
            'max_file_size': self.max_file_size,
            'backup_count': self.backup_count
        }
        
        if self.file_logging:
            # Get log file sizes
            log_files = self.get_log_files()
            file_stats = {}
            
            for name, path in log_files.items():
                if os.path.exists(path):
                    file_stats[name] = {
                        'size': os.path.getsize(path),
                        'modified': datetime.fromtimestamp(
                            os.path.getmtime(path)
                        ).isoformat()
                    }
                else:
                    file_stats[name] = {'size': 0, 'modified': None}
            
            stats['file_stats'] = file_stats
        
        return stats


# Global logging configuration instance
logging_config = LoggingConfig()


def setup_logging(app):
    """
    Setup logging for Flask application.
    
    Args:
        app: Flask application instance
    """
    logging_config.init_app(app)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger by name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_request(request_id: str, method: str, url: str, status_code: int,
               duration: float, user_id: Optional[str] = None,
               ip_address: Optional[str] = None):
    """
    Log HTTP request.
    
    Args:
        request_id: Request ID
        method: HTTP method
        url: Request URL
        status_code: Response status code
        duration: Request duration in milliseconds
        user_id: User ID (optional)
        ip_address: Client IP address (optional)
    """
    if logging_config.app:
        logging_config.log_request(
            request_id, method, url, status_code, duration, user_id, ip_address
        )


def log_security_event(event_type: str, message: str,
                      user_id: Optional[str] = None,
                      ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None,
                      details: Optional[str] = None,
                      level: int = logging.WARNING):
    """
    Log security event.
    
    Args:
        event_type: Type of security event
        message: Event message
        user_id: User ID (optional)
        ip_address: Client IP address (optional)
        user_agent: User agent (optional)
        details: Additional details (optional)
        level: Log level
    """
    if logging_config.app:
        logging_config.log_security_event(
            event_type, message, user_id, ip_address, user_agent, details, level
        )


def log_task_event(task_id: str, task_name: str, event: str,
                  message: str, **kwargs):
    """
    Log task event.
    
    Args:
        task_id: Task ID
        task_name: Task name
        event: Event type
        message: Event message
        **kwargs: Additional context
    """
    if logging_config.app:
        logging_config.log_task_event(task_id, task_name, event, message, **kwargs)