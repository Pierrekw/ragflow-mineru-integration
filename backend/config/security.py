#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security Configuration for Ragflow-MinerU Integration

This module provides security-related configuration and utilities.
"""

import os
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps

from flask import Flask, request, jsonify, current_app, g
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, \
    jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import bcrypt


class SecurityConfig:
    """
    Security configuration class.
    """
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.jwt_manager = None
        self.cipher_suite = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize security with Flask app.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Set security defaults
        self._set_security_defaults(app)
        
        # Initialize JWT
        self._init_jwt(app)
        
        # Initialize encryption
        self._init_encryption(app)
        
        # Register security handlers
        self._register_security_handlers(app)
    
    def _set_security_defaults(self, app: Flask):
        """
        Set default security configuration.
        
        Args:
            app: Flask application instance
        """
        # JWT Configuration
        app.config.setdefault('JWT_SECRET_KEY', os.environ.get('JWT_SECRET_KEY', self._generate_secret_key()))
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=1))
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30))
        app.config.setdefault('JWT_ALGORITHM', 'HS256')
        app.config.setdefault('JWT_BLACKLIST_ENABLED', True)
        app.config.setdefault('JWT_BLACKLIST_TOKEN_CHECKS', ['access', 'refresh'])
        
        # Password Configuration
        app.config.setdefault('PASSWORD_MIN_LENGTH', 8)
        app.config.setdefault('PASSWORD_REQUIRE_UPPERCASE', True)
        app.config.setdefault('PASSWORD_REQUIRE_LOWERCASE', True)
        app.config.setdefault('PASSWORD_REQUIRE_NUMBERS', True)
        app.config.setdefault('PASSWORD_REQUIRE_SPECIAL', True)
        app.config.setdefault('PASSWORD_HASH_ROUNDS', 12)
        
        # Session Configuration
        app.config.setdefault('SESSION_TIMEOUT', 3600)  # 1 hour
        app.config.setdefault('MAX_LOGIN_ATTEMPTS', 5)
        app.config.setdefault('LOCKOUT_DURATION', 900)  # 15 minutes
        
        # CORS Configuration
        app.config.setdefault('CORS_ORIGINS', ['http://localhost:3000'])
        app.config.setdefault('CORS_METHODS', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
        app.config.setdefault('CORS_HEADERS', ['Content-Type', 'Authorization'])
        
        # Rate Limiting
        app.config.setdefault('RATE_LIMIT_ENABLED', True)
        app.config.setdefault('RATE_LIMIT_DEFAULT', '100/hour')
        app.config.setdefault('RATE_LIMIT_LOGIN', '10/minute')
        
        # File Upload Security
        app.config.setdefault('MAX_CONTENT_LENGTH', 100 * 1024 * 1024)  # 100MB
        app.config.setdefault('ALLOWED_EXTENSIONS', {
            'pdf', 'doc', 'docx', 'txt', 'md', 'html', 'htm',
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',
            'xls', 'xlsx', 'ppt', 'pptx'
        })
        
        # Encryption
        app.config.setdefault('ENCRYPTION_KEY', os.environ.get('ENCRYPTION_KEY', Fernet.generate_key()))
    
    def _init_jwt(self, app: Flask):
        """
        Initialize JWT manager.
        
        Args:
            app: Flask application instance
        """
        self.jwt_manager = JWTManager(app)
        
        # JWT error handlers
        @self.jwt_manager.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            return jsonify({
                'error': 'token_expired',
                'message': 'Token has expired'
            }), 401
        
        @self.jwt_manager.invalid_token_loader
        def invalid_token_callback(error):
            return jsonify({
                'error': 'invalid_token',
                'message': 'Invalid token'
            }), 401
        
        @self.jwt_manager.unauthorized_loader
        def missing_token_callback(error):
            return jsonify({
                'error': 'missing_token',
                'message': 'Authorization token is required'
            }), 401
        
        @self.jwt_manager.revoked_token_loader
        def revoked_token_callback(jwt_header, jwt_payload):
            return jsonify({
                'error': 'token_revoked',
                'message': 'Token has been revoked'
            }), 401
        
        # Token blacklist check
        @self.jwt_manager.token_in_blocklist_loader
        def check_if_token_revoked(jwt_header, jwt_payload):
            from backend.models.user import TokenBlacklist
            jti = jwt_payload['jti']
            return TokenBlacklist.is_token_revoked(jti)
    
    def _init_encryption(self, app: Flask):
        """
        Initialize encryption.
        
        Args:
            app: Flask application instance
        """
        encryption_key = app.config['ENCRYPTION_KEY']
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self.cipher_suite = Fernet(encryption_key)
    
    def _register_security_handlers(self, app: Flask):
        """
        Register security-related handlers.
        
        Args:
            app: Flask application instance
        """
        @app.before_request
        def security_headers():
            """Add security headers to all responses."""
            # Skip for OPTIONS requests
            if request.method == 'OPTIONS':
                return
            
            # Check for suspicious requests
            if self._is_suspicious_request(request):
                app.logger.warning(f"Suspicious request detected: {request.remote_addr} - {request.url}")
                return jsonify({'error': 'Request blocked'}), 403
        
        @app.after_request
        def add_security_headers(response):
            """Add security headers to response."""
            # Security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Content Security Policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            response.headers['Content-Security-Policy'] = csp
            
            return response
    
    def _generate_secret_key(self) -> str:
        """
        Generate a secure secret key.
        
        Returns:
            Generated secret key
        """
        return secrets.token_urlsafe(32)
    
    def _is_suspicious_request(self, request) -> bool:
        """
        Check if request is suspicious.
        
        Args:
            request: Flask request object
            
        Returns:
            True if suspicious, False otherwise
        """
        # Check for common attack patterns
        suspicious_patterns = [
            'script', 'javascript:', 'vbscript:', 'onload=', 'onerror=',
            'eval(', 'alert(', 'document.cookie', 'document.write',
            '../', '..\\', '/etc/passwd', '/proc/version',
            'union select', 'drop table', 'insert into', 'delete from'
        ]
        
        # Check URL and query parameters
        full_url = request.url.lower()
        for pattern in suspicious_patterns:
            if pattern in full_url:
                return True
        
        # Check headers
        user_agent = request.headers.get('User-Agent', '').lower()
        if any(bot in user_agent for bot in ['sqlmap', 'nikto', 'nmap', 'masscan']):
            return True
        
        return False
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        if not self.cipher_suite:
            raise RuntimeError("Encryption not initialized")
        
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data
            
        Returns:
            Decrypted data
        """
        if not self.cipher_suite:
            raise RuntimeError("Encryption not initialized")
        
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()


# Global security instance
security = SecurityConfig()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    rounds = current_app.config.get('PASSWORD_HASH_ROUNDS', 12)
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=rounds)).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password
        hashed: Hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def validate_password(password: str) -> Dict[str, Any]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Validation result
    """
    errors = []
    
    # Check minimum length
    min_length = current_app.config.get('PASSWORD_MIN_LENGTH', 8)
    if len(password) < min_length:
        errors.append(f'Password must be at least {min_length} characters long')
    
    # Check for uppercase letters
    if current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', True):
        if not any(c.isupper() for c in password):
            errors.append('Password must contain at least one uppercase letter')
    
    # Check for lowercase letters
    if current_app.config.get('PASSWORD_REQUIRE_LOWERCASE', True):
        if not any(c.islower() for c in password):
            errors.append('Password must contain at least one lowercase letter')
    
    # Check for numbers
    if current_app.config.get('PASSWORD_REQUIRE_NUMBERS', True):
        if not any(c.isdigit() for c in password):
            errors.append('Password must contain at least one number')
    
    # Check for special characters
    if current_app.config.get('PASSWORD_REQUIRE_SPECIAL', True):
        special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        if not any(c in special_chars for c in password):
            errors.append('Password must contain at least one special character')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def generate_tokens(user_id: int, additional_claims: Optional[Dict] = None) -> Dict[str, str]:
    """
    Generate access and refresh tokens for a user.
    
    Args:
        user_id: User ID
        additional_claims: Additional claims to include in token
        
    Returns:
        Dictionary containing access and refresh tokens
    """
    identity = str(user_id)
    
    # Create additional claims
    claims = additional_claims or {}
    claims.update({
        'user_id': user_id,
        'iat': datetime.utcnow(),
        'type': 'access'
    })
    
    # Generate tokens
    access_token = create_access_token(
        identity=identity,
        additional_claims=claims
    )
    
    refresh_claims = claims.copy()
    refresh_claims['type'] = 'refresh'
    
    refresh_token = create_refresh_token(
        identity=identity,
        additional_claims=refresh_claims
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
    }


def revoke_token(jti: str) -> bool:
    """
    Revoke a token by adding it to blacklist.
    
    Args:
        jti: JWT ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from backend.models.user import TokenBlacklist
        TokenBlacklist.revoke_token(jti)
        return True
    except Exception:
        return False


def require_permission(permission: str):
    """
    Decorator to require specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            
            # Get user permissions
            from backend.models.user import User
            user = User.get_by_id(user_id)
            
            if not user or not user.has_permission(permission):
                return jsonify({
                    'error': 'insufficient_permissions',
                    'message': f'Permission "{permission}" required'
                }), 403
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role: str):
    """
    Decorator to require specific role.
    
    Args:
        role: Required role
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            
            # Get user role
            from backend.models.user import User
            user = User.get_by_id(user_id)
            
            if not user or user.role.name != role:
                return jsonify({
                    'error': 'insufficient_role',
                    'message': f'Role "{role}" required'
                }), 403
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_admin():
    """
    Decorator to require admin role.
    
    Returns:
        Decorated function
    """
    return require_role('admin')


def rate_limit(limit: str):
    """
    Decorator for rate limiting.
    
    Args:
        limit: Rate limit string (e.g., '10/minute')
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Rate limiting logic would be implemented here
            # For now, just pass through
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def sanitize_input(data: Any) -> Any:
    """
    Sanitize user input to prevent XSS and injection attacks.
    
    Args:
        data: Input data
        
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', 'javascript:', 'vbscript:']
        for char in dangerous_chars:
            data = data.replace(char, '')
        
        # Limit length
        if len(data) > 10000:  # 10KB limit
            data = data[:10000]
    
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    
    return data


def validate_file_upload(file) -> Dict[str, Any]:
    """
    Validate uploaded file.
    
    Args:
        file: Uploaded file object
        
    Returns:
        Validation result
    """
    errors = []
    
    # Check if file exists
    if not file or not file.filename:
        errors.append('No file provided')
        return {'valid': False, 'errors': errors}
    
    # Check file extension
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        errors.append(f'File type "{file_ext}" not allowed')
    
    # Check file size (this is handled by Flask's MAX_CONTENT_LENGTH)
    # Additional checks can be added here
    
    # Check filename for suspicious patterns
    suspicious_patterns = ['../', '..\\', '/etc/', 'C:\\', 'cmd.exe', 'powershell']
    filename_lower = file.filename.lower()
    
    for pattern in suspicious_patterns:
        if pattern in filename_lower:
            errors.append('Suspicious filename detected')
            break
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'filename': file.filename,
        'extension': file_ext
    }


def generate_csrf_token() -> str:
    """
    Generate CSRF token.
    
    Returns:
        CSRF token
    """
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, session_token: str) -> bool:
    """
    Validate CSRF token.
    
    Args:
        token: Provided token
        session_token: Session token
        
    Returns:
        True if valid, False otherwise
    """
    return secrets.compare_digest(token, session_token)


def get_client_ip() -> str:
    """
    Get client IP address.
    
    Returns:
        Client IP address
    """
    # Check for forwarded headers
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def log_security_event(event_type: str, details: Dict[str, Any]):
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        details: Event details
    """
    from backend.models.audit import AuditLog
    
    try:
        AuditLog.create(
            event_type=event_type,
            details=details,
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent', ''),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        current_app.logger.error(f"Failed to log security event: {e}")


def check_rate_limit(key: str, limit: int, window: int) -> bool:
    """
    Check if rate limit is exceeded.
    
    Args:
        key: Rate limit key
        limit: Maximum requests
        window: Time window in seconds
        
    Returns:
        True if within limit, False if exceeded
    """
    from backend.config.cache import cache
    
    current_time = datetime.utcnow().timestamp()
    cache_key = f"rate_limit:{key}"
    
    # Get current count
    requests = cache.get(cache_key, [])
    
    # Filter requests within window
    requests = [req_time for req_time in requests if current_time - req_time < window]
    
    # Check if limit exceeded
    if len(requests) >= limit:
        return False
    
    # Add current request
    requests.append(current_time)
    cache.set(cache_key, requests, window)
    
    return True