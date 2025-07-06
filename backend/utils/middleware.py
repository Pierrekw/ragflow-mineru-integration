#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Middleware for Ragflow-MinerU Integration

This module provides middleware functions for request processing.
"""

import time
import uuid
from datetime import datetime
from flask import request, g, current_app, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request
from functools import wraps

from backend.utils.logging_config import log_security_event, log_performance


def register_middleware(app):
    """
    Register middleware for the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Handle proxy headers
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_prefix=1
    )
    
    # Register request hooks
    register_request_hooks(app)
    
    # Register security middleware
    register_security_middleware(app)


def register_request_hooks(app):
    """
    Register request processing hooks.
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def before_request():
        """Execute before each request."""
        # Generate request ID
        g.request_id = str(uuid.uuid4())[:8]
        g.start_time = time.time()
        g.request_start = datetime.utcnow()
        
        # Add request info to context
        g.ip_address = get_real_ip()
        g.user_agent = request.headers.get('User-Agent', 'unknown')
        
        # Try to get current user from JWT
        try:
            verify_jwt_in_request(optional=True)
            g.current_user_id = get_jwt_identity()
        except Exception:
            g.current_user_id = None
        
        # Log request start
        if app.config.get('LOG_REQUESTS', False):
            app.logger.info(
                f"Request started: {request.method} {request.url}",
                extra={
                    'request_id': g.request_id,
                    'user_id': g.current_user_id,
                    'ip_address': g.ip_address,
                    'user_agent': g.user_agent
                }
            )
    
    @app.after_request
    def after_request(response):
        """Execute after each request."""
        # Calculate request duration
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Log performance if enabled
            if app.config.get('LOG_PERFORMANCE', False) and duration > 1.0:
                log_performance(
                    func_name=f"{request.method} {request.endpoint}",
                    duration=duration,
                    request_id=getattr(g, 'request_id', 'unknown'),
                    user_id=getattr(g, 'current_user_id', 'unknown')
                )
        
        # Add security headers
        add_security_headers(response)
        
        # Add CORS headers if not already present
        add_cors_headers(response)
        
        # Add request ID to response headers
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        # Log request completion
        if app.config.get('LOG_REQUESTS', False) and hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            app.logger.info(
                f"Request completed: {response.status_code} - {duration:.3f}s",
                extra={
                    'request_id': getattr(g, 'request_id', 'unknown'),
                    'status_code': response.status_code,
                    'duration': duration
                }
            )
        
        return response
    
    @app.teardown_appcontext
    def teardown_appcontext(exception=None):
        """Clean up after request."""
        # Clean up database session
        try:
            from backend.config.database import get_db
            db = get_db()
            if hasattr(db, 'close'):
                db.close()
        except Exception:
            pass
        
        # Log any exceptions during teardown
        if exception:
            app.logger.error(
                f"Exception during request teardown: {str(exception)}",
                exc_info=True,
                extra={
                    'request_id': getattr(g, 'request_id', 'unknown')
                }
            )


def register_security_middleware(app):
    """
    Register security-related middleware.
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def security_checks():
        """Perform security checks before request processing."""
        # Check for suspicious requests
        if is_suspicious_request():
            log_security_event(
                'suspicious_request',
                ip_address=g.ip_address,
                user_agent=g.user_agent,
                endpoint=request.endpoint,
                method=request.method,
                url=request.url
            )
        
        # Check for blocked IPs (if implemented)
        if is_blocked_ip(g.ip_address):
            log_security_event(
                'blocked_ip_access',
                ip_address=g.ip_address,
                user_agent=g.user_agent
            )
            return jsonify({
                'success': False,
                'error': {
                    'code': 'IP_BLOCKED',
                    'message': 'Access denied'
                }
            }), 403


def get_real_ip():
    """
    Get the real IP address of the client.
    
    Returns:
        str: Client IP address
    """
    # Check for forwarded headers
    forwarded_ips = [
        request.headers.get('X-Forwarded-For'),
        request.headers.get('X-Real-IP'),
        request.headers.get('CF-Connecting-IP'),  # Cloudflare
        request.environ.get('HTTP_X_FORWARDED_FOR'),
        request.environ.get('HTTP_X_REAL_IP')
    ]
    
    for ip in forwarded_ips:
        if ip:
            # Take the first IP if there are multiple
            return ip.split(',')[0].strip()
    
    return request.remote_addr or 'unknown'


def add_security_headers(response):
    """
    Add security headers to the response.
    
    Args:
        response: Flask response object
    """
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy (basic)
    if not response.headers.get('Content-Security-Policy'):
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self';"
        )
    
    # HSTS (only for HTTPS)
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains'
        )


def add_cors_headers(response):
    """
    Add CORS headers to the response if not already present.
    
    Args:
        response: Flask response object
    """
    if not response.headers.get('Access-Control-Allow-Origin'):
        # Get allowed origins from config
        allowed_origins = current_app.config.get('CORS_ORIGINS', ['*'])
        origin = request.headers.get('Origin')
        
        if '*' in allowed_origins or origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin or '*'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = (
                'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            )
            response.headers['Access-Control-Allow-Headers'] = (
                'Content-Type, Authorization, X-Requested-With, X-Request-ID'
            )
            response.headers['Access-Control-Expose-Headers'] = (
                'X-Request-ID, X-Total-Count'
            )


def is_suspicious_request():
    """
    Check if the current request is suspicious.
    
    Returns:
        bool: True if request is suspicious
    """
    # Check for common attack patterns
    suspicious_patterns = [
        'script',
        'javascript:',
        '<script',
        'eval(',
        'union select',
        'drop table',
        '../',
        '..\\',
        'cmd.exe',
        '/etc/passwd'
    ]
    
    # Check URL and query parameters
    full_url = request.url.lower()
    for pattern in suspicious_patterns:
        if pattern in full_url:
            return True
    
    # Check request headers
    user_agent = request.headers.get('User-Agent', '').lower()
    suspicious_user_agents = [
        'sqlmap',
        'nikto',
        'nessus',
        'burp',
        'nmap',
        'masscan'
    ]
    
    for agent in suspicious_user_agents:
        if agent in user_agent:
            return True
    
    return False


def is_blocked_ip(ip_address):
    """
    Check if an IP address is blocked.
    
    Args:
        ip_address: IP address to check
        
    Returns:
        bool: True if IP is blocked
    """
    # TODO: Implement IP blocking logic
    # This could check against a database, Redis cache, or external service
    blocked_ips = current_app.config.get('BLOCKED_IPS', [])
    return ip_address in blocked_ips


def require_permission(permission_name):
    """
    Decorator to require specific permission for accessing an endpoint.
    
    Args:
        permission_name: Name of the required permission
        
    Returns:
        function: Decorator function
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            from backend.services.permission_service import PermissionService
            
            user_id = get_jwt_identity()
            permission_service = PermissionService()
            
            if not permission_service.check_user_permission(user_id, permission_name):
                log_security_event(
                    'permission_denied',
                    user_id=user_id,
                    permission=permission_name,
                    endpoint=request.endpoint
                )
                
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'PERMISSION_DENIED',
                        'message': f'Permission required: {permission_name}'
                    }
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_role(role_name):
    """
    Decorator to require specific role for accessing an endpoint.
    
    Args:
        role_name: Name of the required role
        
    Returns:
        function: Decorator function
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            from backend.models.user import User
            
            user_id = get_jwt_identity()
            user = User.get_by_id(user_id)
            
            if not user or not user.role or user.role.name != role_name:
                log_security_event(
                    'role_access_denied',
                    user_id=user_id,
                    required_role=role_name,
                    user_role=user.role.name if user and user.role else None,
                    endpoint=request.endpoint
                )
                
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'ROLE_REQUIRED',
                        'message': f'Role required: {role_name}'
                    }
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def rate_limit_by_user():
    """
    Decorator to apply rate limiting per user.
    
    Returns:
        function: Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # TODO: Implement user-based rate limiting
            # This could use Redis to track request counts per user
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def cache_response(timeout=300):
    """
    Decorator to cache response for a specified time.
    
    Args:
        timeout: Cache timeout in seconds
        
    Returns:
        function: Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # TODO: Implement response caching
            # This could use Redis or Flask-Caching
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator