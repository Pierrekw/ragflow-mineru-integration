#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Handlers for Ragflow-MinerU Integration

This module provides centralized error handling for the application.
"""

import logging
import traceback
from datetime import datetime
from flask import jsonify, request, current_app
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from jwt.exceptions import PyJWTError as JWTError

from backend.utils.logging_config import log_security_event


def register_error_handlers(app):
    """
    Register error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return create_error_response(
            error_code='BAD_REQUEST',
            message='Invalid request data',
            status_code=400,
            details=str(error.description) if hasattr(error, 'description') else None
        )
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        log_security_event(
            'unauthorized_access',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            endpoint=request.endpoint
        )
        
        return create_error_response(
            error_code='UNAUTHORIZED',
            message='Authentication required',
            status_code=401
        )
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        log_security_event(
            'access_denied',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            endpoint=request.endpoint
        )
        
        return create_error_response(
            error_code='FORBIDDEN',
            message='Access denied',
            status_code=403
        )
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return create_error_response(
            error_code='NOT_FOUND',
            message='Resource not found',
            status_code=404
        )
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return create_error_response(
            error_code='METHOD_NOT_ALLOWED',
            message='Method not allowed',
            status_code=405,
            details=f"Allowed methods: {', '.join(error.valid_methods)}"
        )
    
    @app.errorhandler(413)
    def payload_too_large(error):
        """Handle 413 Payload Too Large errors."""
        return create_error_response(
            error_code='PAYLOAD_TOO_LARGE',
            message='File too large',
            status_code=413
        )
    
    @app.errorhandler(415)
    def unsupported_media_type(error):
        """Handle 415 Unsupported Media Type errors."""
        return create_error_response(
            error_code='UNSUPPORTED_MEDIA_TYPE',
            message='Unsupported media type',
            status_code=415
        )
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors."""
        return create_error_response(
            error_code='UNPROCESSABLE_ENTITY',
            message='Validation failed',
            status_code=422,
            details=str(error.description) if hasattr(error, 'description') else None
        )
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Too Many Requests errors."""
        log_security_event(
            'rate_limit_exceeded',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            endpoint=request.endpoint
        )
        
        return create_error_response(
            error_code='RATE_LIMIT_EXCEEDED',
            message='Rate limit exceeded',
            status_code=429,
            details=f"Retry after {getattr(error, 'retry_after', 'unknown')} seconds"
        )
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        app.logger.error(
            f"Internal server error: {str(error)}",
            exc_info=True,
            extra={
                'endpoint': request.endpoint,
                'method': request.method,
                'url': request.url,
                'ip_address': request.remote_addr
            }
        )
        
        # Rollback database session if exists
        try:
            from backend.config.database import get_db
            db = get_db()
            if hasattr(db, 'rollback'):
                db.rollback()
        except Exception:
            pass
        
        return create_error_response(
            error_code='INTERNAL_SERVER_ERROR',
            message='Internal server error',
            status_code=500,
            include_traceback=app.config.get('DEBUG', False)
        )
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle Marshmallow validation errors."""
        app.logger.warning(
            f"Validation error: {error.messages}",
            extra={
                'endpoint': request.endpoint,
                'validation_errors': error.messages
            }
        )
        
        return create_error_response(
            error_code='VALIDATION_ERROR',
            message='Validation failed',
            status_code=400,
            details=error.messages
        )
    
    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        """Handle SQLAlchemy database errors."""
        app.logger.error(
            f"Database error: {str(error)}",
            exc_info=True,
            extra={
                'endpoint': request.endpoint,
                'error_type': type(error).__name__
            }
        )
        
        # Rollback database session
        try:
            from backend.config.database import get_db
            db = get_db()
            if hasattr(db, 'rollback'):
                db.rollback()
        except Exception:
            pass
        
        return create_error_response(
            error_code='DATABASE_ERROR',
            message='Database operation failed',
            status_code=500,
            include_traceback=app.config.get('DEBUG', False)
        )
    
    @app.errorhandler(JWTError)
    def handle_jwt_error(error):
        """Handle JWT-related errors."""
        log_security_event(
            'jwt_error',
            ip_address=request.remote_addr,
            error_type=type(error).__name__,
            error_message=str(error)
        )
        
        return create_error_response(
            error_code='JWT_ERROR',
            message='Token validation failed',
            status_code=401,
            details=str(error) if app.config.get('DEBUG') else None
        )
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        app.logger.error(
            f"Unexpected error: {str(error)}",
            exc_info=True,
            extra={
                'endpoint': request.endpoint,
                'error_type': type(error).__name__
            }
        )
        
        # Rollback database session if exists
        try:
            from backend.config.database import get_db
            db = get_db()
            if hasattr(db, 'rollback'):
                db.rollback()
        except Exception:
            pass
        
        return create_error_response(
            error_code='UNEXPECTED_ERROR',
            message='An unexpected error occurred',
            status_code=500,
            include_traceback=app.config.get('DEBUG', False)
        )


def create_error_response(error_code: str, message: str, status_code: int, 
                         details=None, include_traceback: bool = False):
    """
    Create a standardized error response.
    
    Args:
        error_code: Error code identifier
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        include_traceback: Whether to include traceback in response
        
    Returns:
        tuple: JSON response and status code
    """
    response_data = {
        'success': False,
        'error': {
            'code': error_code,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': getattr(request, 'id', 'unknown')
        }
    }
    
    if details:
        response_data['error']['details'] = details
    
    if include_traceback:
        response_data['error']['traceback'] = traceback.format_exc()
    
    return jsonify(response_data), status_code


class ApplicationError(Exception):
    """
    Base application error class.
    """
    
    def __init__(self, message: str, error_code: str = None, status_code: int = 500, details=None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or 'APPLICATION_ERROR'
        self.status_code = status_code
        self.details = details


class ValidationError(ApplicationError):
    """
    Validation error.
    """
    
    def __init__(self, message: str, details=None):
        super().__init__(
            message=message,
            error_code='VALIDATION_ERROR',
            status_code=400,
            details=details
        )


class AuthenticationError(ApplicationError):
    """
    Authentication error.
    """
    
    def __init__(self, message: str = 'Authentication failed'):
        super().__init__(
            message=message,
            error_code='AUTHENTICATION_ERROR',
            status_code=401
        )


class AuthorizationError(ApplicationError):
    """
    Authorization error.
    """
    
    def __init__(self, message: str = 'Access denied'):
        super().__init__(
            message=message,
            error_code='AUTHORIZATION_ERROR',
            status_code=403
        )


class ResourceNotFoundError(ApplicationError):
    """
    Resource not found error.
    """
    
    def __init__(self, resource_type: str, resource_id=None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        super().__init__(
            message=message,
            error_code='RESOURCE_NOT_FOUND',
            status_code=404
        )


class BusinessLogicError(ApplicationError):
    """
    Business logic error.
    """
    
    def __init__(self, message: str, details=None):
        super().__init__(
            message=message,
            error_code='BUSINESS_LOGIC_ERROR',
            status_code=422,
            details=details
        )


class ExternalServiceError(ApplicationError):
    """
    External service error.
    """
    
    def __init__(self, service_name: str, message: str = None):
        message = message or f"{service_name} service unavailable"
        super().__init__(
            message=message,
            error_code='EXTERNAL_SERVICE_ERROR',
            status_code=503
        )


class RateLimitError(ApplicationError):
    """
    Rate limit error.
    """
    
    def __init__(self, retry_after: int = None):
        message = 'Rate limit exceeded'
        if retry_after:
            message += f", retry after {retry_after} seconds"
        
        super().__init__(
            message=message,
            error_code='RATE_LIMIT_ERROR',
            status_code=429,
            details={'retry_after': retry_after} if retry_after else None
        )


def handle_application_error(error: ApplicationError):
    """
    Handle custom application errors.
    
    Args:
        error: Application error instance
        
    Returns:
        tuple: JSON response and status code
    """
    current_app.logger.warning(
        f"Application error: {error.message}",
        extra={
            'error_code': error.error_code,
            'status_code': error.status_code,
            'details': error.details,
            'endpoint': request.endpoint
        }
    )
    
    return create_error_response(
        error_code=error.error_code,
        message=error.message,
        status_code=error.status_code,
        details=error.details
    )