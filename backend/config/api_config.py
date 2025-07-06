#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Configuration for Ragflow-MinerU Integration

This module provides API-related configuration and utilities.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_restful import Api
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)


class APIConfig:
    """
    API configuration class.
    """
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.api = None
        self.limiter = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize API configuration with Flask app.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Set API defaults
        self._set_api_defaults(app)
        
        # Initialize CORS
        self._init_cors(app)
        
        # Initialize rate limiting
        self._init_rate_limiting(app)
        
        # Initialize Flask-RESTful
        self._init_restful_api(app)
        
        # Register API handlers
        self._register_api_handlers(app)
    
    def _set_api_defaults(self, app: Flask):
        """
        Set default API configuration.
        
        Args:
            app: Flask application instance
        """
        # API Configuration
        app.config.setdefault('API_VERSION', 'v1')
        app.config.setdefault('API_PREFIX', '/api')
        app.config.setdefault('API_TITLE', 'Ragflow-MinerU Integration API')
        app.config.setdefault('API_DESCRIPTION', 'API for document processing and knowledge base management')
        app.config.setdefault('API_CONTACT', {
            'name': 'API Support',
            'email': 'support@ragflow-mineru.com',
            'url': 'https://github.com/ragflow-mineru/integration'
        })
        
        # Response Configuration
        app.config.setdefault('API_DEFAULT_PAGE_SIZE', 20)
        app.config.setdefault('API_MAX_PAGE_SIZE', 100)
        app.config.setdefault('API_RESPONSE_TIMEOUT', 30)
        
        # Content Type Configuration
        app.config.setdefault('API_SUPPORTED_CONTENT_TYPES', [
            'application/json',
            'multipart/form-data',
            'application/x-www-form-urlencoded'
        ])
        
        # Documentation Configuration
        app.config.setdefault('API_DOC_ENABLED', True)
        app.config.setdefault('API_DOC_PATH', '/docs')
        app.config.setdefault('API_SPEC_PATH', '/swagger.json')
    
    def _init_cors(self, app: Flask):
        """
        Initialize CORS configuration.
        
        Args:
            app: Flask application instance
        """
        cors_config = {
            'origins': app.config.get('CORS_ORIGINS', ['*']),
            'methods': app.config.get('CORS_METHODS', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']),
            'allow_headers': app.config.get('CORS_HEADERS', [
                'Content-Type', 'Authorization', 'X-Requested-With',
                'X-API-Key', 'X-Request-ID', 'Accept'
            ]),
            'expose_headers': ['X-Total-Count', 'X-Page-Count', 'X-Request-ID'],
            'supports_credentials': True,
            'max_age': 86400  # 24 hours
        }
        
        CORS(app, **cors_config)
        app.logger.info("CORS initialized with origins: %s", cors_config['origins'])
    
    def _init_rate_limiting(self, app: Flask):
        """
        Initialize rate limiting.
        
        Args:
            app: Flask application instance
        """
        if app.config.get('RATE_LIMIT_ENABLED', True):
            # Initialize limiter
            self.limiter = Limiter(
                app,
                key_func=self._get_rate_limit_key,
                default_limits=[app.config.get('RATE_LIMIT_DEFAULT', '1000/hour')],
                storage_uri=app.config.get('RATE_LIMIT_STORAGE_URL', 'memory://'),
                strategy='fixed-window'
            )
            
            # Custom rate limit exceeded handler
            @self.limiter.request_filter
            def rate_limit_filter():
                """Filter requests that should not be rate limited."""
                # Skip rate limiting for health checks
                if request.endpoint in ['health', 'ping']:
                    return True
                return False
            
            @app.errorhandler(429)
            def rate_limit_exceeded(error):
                """Handle rate limit exceeded errors."""
                return create_error_response(
                    'rate_limit_exceeded',
                    'Rate limit exceeded. Please try again later.',
                    429,
                    {
                        'retry_after': error.retry_after,
                        'limit': error.limit,
                        'reset_time': error.reset_time
                    }
                )
            
            app.logger.info("Rate limiting initialized")
    
    def _init_restful_api(self, app: Flask):
        """
        Initialize Flask-RESTful API.
        
        Args:
            app: Flask application instance
        """
        self.api = Api(app, prefix=app.config['API_PREFIX'])
        
        # Custom error handlers for Flask-RESTful
        @self.api.representation('application/json')
        def output_json(data, code, headers=None):
            """Custom JSON output with consistent format."""
            response = jsonify(data)
            response.status_code = code
            if headers:
                response.headers.extend(headers)
            return response
    
    def _register_api_handlers(self, app: Flask):
        """
        Register API-related handlers.
        
        Args:
            app: Flask application instance
        """
        @app.before_request
        def before_api_request():
            """Handle pre-request processing."""
            # Generate request ID
            g.request_id = self._generate_request_id()
            
            # Log request
            if app.config.get('LOG_API_REQUESTS', True):
                app.logger.info(
                    "API Request: %s %s [%s] - %s",
                    request.method,
                    request.url,
                    g.request_id,
                    request.remote_addr
                )
            
            # Validate content type for POST/PUT requests
            if request.method in ['POST', 'PUT', 'PATCH']:
                content_type = request.content_type
                if content_type:
                    content_type = content_type.split(';')[0]  # Remove charset
                
                supported_types = app.config['API_SUPPORTED_CONTENT_TYPES']
                if content_type not in supported_types:
                    return create_error_response(
                        'unsupported_media_type',
                        f'Content-Type "{content_type}" not supported',
                        415
                    )
        
        @app.after_request
        def after_api_request(response):
            """Handle post-request processing."""
            # Add request ID to response headers
            if hasattr(g, 'request_id'):
                response.headers['X-Request-ID'] = g.request_id
            
            # Add API version header
            response.headers['X-API-Version'] = app.config['API_VERSION']
            
            # Log response
            if app.config.get('LOG_API_RESPONSES', True):
                app.logger.info(
                    "API Response: %s %s [%s] - %d",
                    request.method,
                    request.url,
                    getattr(g, 'request_id', 'unknown'),
                    response.status_code
                )
            
            return response
        
        # Register error handlers
        self._register_error_handlers(app)
    
    def _register_error_handlers(self, app: Flask):
        """
        Register API error handlers.
        
        Args:
            app: Flask application instance
        """
        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            """Handle Marshmallow validation errors."""
            return create_error_response(
                'validation_error',
                'Request validation failed',
                400,
                {'validation_errors': error.messages}
            )
        
        @app.errorhandler(404)
        def handle_not_found(error):
            """Handle 404 errors."""
            return create_error_response(
                'not_found',
                'The requested resource was not found',
                404
            )
        
        @app.errorhandler(405)
        def handle_method_not_allowed(error):
            """Handle 405 errors."""
            return create_error_response(
                'method_not_allowed',
                'The requested method is not allowed for this resource',
                405
            )
        
        @app.errorhandler(500)
        def handle_internal_error(error):
            """Handle 500 errors."""
            app.logger.error(f"Internal server error: {error}")
            return create_error_response(
                'internal_error',
                'An internal server error occurred',
                500
            )
    
    def _get_rate_limit_key(self) -> str:
        """
        Get rate limit key for current request.
        
        Returns:
            Rate limit key
        """
        # Use user ID if authenticated, otherwise use IP
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
        
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
        
        return get_remote_address()
    
    def _generate_request_id(self) -> str:
        """
        Generate unique request ID.
        
        Returns:
            Request ID
        """
        import uuid
        return str(uuid.uuid4())


def create_success_response(data: Any = None, message: str = None, 
                          status_code: int = 200, meta: Dict = None) -> tuple:
    """
    Create standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        meta: Additional metadata
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': True,
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': getattr(g, 'request_id', None)
    }
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    if meta:
        response['meta'] = meta
    
    return response, status_code


def create_error_response(error_code: str, message: str, 
                         status_code: int = 400, details: Dict = None) -> tuple:
    """
    Create standardized error response.
    
    Args:
        error_code: Error code
        message: Error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': False,
        'error': {
            'code': error_code,
            'message': message
        },
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': getattr(g, 'request_id', None)
    }
    
    if details:
        response['error']['details'] = details
    
    return response, status_code


def create_paginated_response(items: List, total: int, page: int, 
                             per_page: int, **kwargs) -> Dict:
    """
    Create paginated response.
    
    Args:
        items: List of items
        total: Total number of items
        page: Current page number
        per_page: Items per page
        **kwargs: Additional data
        
    Returns:
        Paginated response data
    """
    total_pages = (total + per_page - 1) // per_page
    
    data = {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'next_page': page + 1 if page < total_pages else None,
            'prev_page': page - 1 if page > 1 else None
        }
    }
    
    # Add any additional data
    data.update(kwargs)
    
    return data


def validate_pagination_params(page: int = None, per_page: int = None) -> Dict[str, int]:
    """
    Validate and normalize pagination parameters.
    
    Args:
        page: Page number
        per_page: Items per page
        
    Returns:
        Validated pagination parameters
    """
    from flask import current_app
    
    # Default values
    default_page_size = current_app.config.get('API_DEFAULT_PAGE_SIZE', 20)
    max_page_size = current_app.config.get('API_MAX_PAGE_SIZE', 100)
    
    # Validate page
    if page is None or page < 1:
        page = 1
    
    # Validate per_page
    if per_page is None:
        per_page = default_page_size
    elif per_page < 1:
        per_page = default_page_size
    elif per_page > max_page_size:
        per_page = max_page_size
    
    return {
        'page': page,
        'per_page': per_page,
        'offset': (page - 1) * per_page
    }


def parse_sort_params(sort_param: str, allowed_fields: List[str]) -> List[Dict[str, str]]:
    """
    Parse sort parameters.
    
    Args:
        sort_param: Sort parameter string (e.g., 'name,-created_at')
        allowed_fields: List of allowed sort fields
        
    Returns:
        List of sort specifications
    """
    if not sort_param:
        return []
    
    sort_specs = []
    
    for field in sort_param.split(','):
        field = field.strip()
        if not field:
            continue
        
        # Check for descending order prefix
        if field.startswith('-'):
            direction = 'desc'
            field = field[1:]
        else:
            direction = 'asc'
        
        # Validate field
        if field in allowed_fields:
            sort_specs.append({
                'field': field,
                'direction': direction
            })
    
    return sort_specs


def parse_filter_params(filter_params: Dict[str, Any], 
                       allowed_fields: List[str]) -> Dict[str, Any]:
    """
    Parse and validate filter parameters.
    
    Args:
        filter_params: Raw filter parameters
        allowed_fields: List of allowed filter fields
        
    Returns:
        Validated filter parameters
    """
    filters = {}
    
    for field, value in filter_params.items():
        if field in allowed_fields and value is not None:
            # Handle different filter operators
            if field.endswith('__gte'):
                base_field = field[:-5]
                if base_field in allowed_fields:
                    filters[field] = value
            elif field.endswith('__lte'):
                base_field = field[:-5]
                if base_field in allowed_fields:
                    filters[field] = value
            elif field.endswith('__like'):
                base_field = field[:-6]
                if base_field in allowed_fields:
                    filters[field] = f"%{value}%"
            else:
                filters[field] = value
    
    return filters


def get_api_info() -> Dict[str, Any]:
    """
    Get API information.
    
    Returns:
        API information
    """
    from flask import current_app
    
    return {
        'title': current_app.config.get('API_TITLE'),
        'description': current_app.config.get('API_DESCRIPTION'),
        'version': current_app.config.get('API_VERSION'),
        'contact': current_app.config.get('API_CONTACT'),
        'endpoints': {
            'docs': current_app.config.get('API_DOC_PATH'),
            'spec': current_app.config.get('API_SPEC_PATH')
        },
        'limits': {
            'default_page_size': current_app.config.get('API_DEFAULT_PAGE_SIZE'),
            'max_page_size': current_app.config.get('API_MAX_PAGE_SIZE'),
            'response_timeout': current_app.config.get('API_RESPONSE_TIMEOUT')
        },
        'supported_content_types': current_app.config.get('API_SUPPORTED_CONTENT_TYPES')
    }


def validate_json_request() -> Dict[str, Any]:
    """
    Validate JSON request data.
    
    Returns:
        Parsed JSON data
        
    Raises:
        ValidationError: If JSON is invalid
    """
    from flask import request
    
    if not request.is_json:
        raise ValidationError('Request must be JSON')
    
    try:
        data = request.get_json()
        if data is None:
            raise ValidationError('Invalid JSON data')
        return data
    except Exception as e:
        raise ValidationError(f'JSON parsing error: {str(e)}')


def require_json(func):
    """
    Decorator to require JSON request.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            validate_json_request()
        except ValidationError as e:
            return create_error_response(
                'invalid_json',
                str(e),
                400
            )
        
        return func(*args, **kwargs)
    
    return wrapper


# Global API config instance
api_config = APIConfig()