#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication API for Ragflow-MinerU Integration

This module provides authentication and authorization API endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt,
    create_access_token, create_refresh_token
)
from marshmallow import Schema, fields, ValidationError
from functools import wraps
import re

from backend.services.auth_service import AuthService, AuthenticationError, AuthorizationError
from backend.services.permission_service import PermissionService
from backend.models.user import User
from backend.api import HTTP_STATUS, RESPONSE_MESSAGES, RATE_LIMITS


# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
api = Api(auth_bp)

# Initialize services
auth_service = AuthService()
permission_service = PermissionService()


# Validation schemas
class RegisterSchema(Schema):
    """User registration validation schema."""
    username = fields.Str(required=True, validate=lambda x: len(x) >= 3 and len(x) <= 50)
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda x: len(x) >= 8)
    first_name = fields.Str(missing=None, validate=lambda x: len(x) <= 50 if x else True)
    last_name = fields.Str(missing=None, validate=lambda x: len(x) <= 50 if x else True)
    role_name = fields.Str(missing='user')


class LoginSchema(Schema):
    """User login validation schema."""
    identifier = fields.Str(required=True)  # username or email
    password = fields.Str(required=True)
    remember_me = fields.Bool(missing=False)


class ChangePasswordSchema(Schema):
    """Change password validation schema."""
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=lambda x: len(x) >= 8)


class ResetPasswordRequestSchema(Schema):
    """Password reset request validation schema."""
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    """Password reset validation schema."""
    reset_token = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=lambda x: len(x) >= 8)


class RefreshTokenSchema(Schema):
    """Refresh token validation schema."""
    refresh_token = fields.Str(required=True)


# Utility functions
def validate_json(schema_class):
    """Decorator to validate JSON request data."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                schema = schema_class()
                data = schema.load(request.get_json() or {})
                return f(data, *args, **kwargs)
            except ValidationError as e:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['VALIDATION_ERROR'],
                    'errors': e.messages
                }, HTTP_STATUS['BAD_REQUEST']
        return decorated_function
    return decorator


def get_client_info():
    """Get client IP and user agent."""
    return {
        'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
        'user_agent': request.headers.get('User-Agent', '')
    }


def require_permission(permission_name):
    """Decorator to require specific permission."""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                user_id = get_jwt_identity()
                user = User.get_by_id(user_id)
                
                if not user or not user.is_active:
                    return {
                        'success': False,
                        'message': RESPONSE_MESSAGES['UNAUTHORIZED']
                    }, HTTP_STATUS['UNAUTHORIZED']
                
                if not auth_service.check_permission(user, permission_name):
                    return {
                        'success': False,
                        'message': RESPONSE_MESSAGES['FORBIDDEN']
                    }, HTTP_STATUS['FORBIDDEN']
                
                return f(*args, **kwargs)
            except Exception as e:
                current_app.logger.error(f"Permission check error: {str(e)}")
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
                }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
        return decorated_function
    return decorator


# API Resources
class RegisterResource(Resource):
    """User registration endpoint."""
    
    @validate_json(RegisterSchema)
    def post(self, data):
        """Register a new user."""
        try:
            client_info = get_client_info()
            
            result = auth_service.register_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                role_name=data.get('role_name', 'user')
            )
            
            if result['success']:
                # Remove sensitive data
                user_data = result['user'].copy()
                user_data.pop('password_hash', None)
                
                return {
                    'success': True,
                    'message': RESPONSE_MESSAGES['CREATED'],
                    'user': user_data
                }, HTTP_STATUS['CREATED']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except AuthenticationError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['BAD_REQUEST']
        except Exception as e:
            current_app.logger.error(f"Registration error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class LoginResource(Resource):
    """User login endpoint."""
    
    @validate_json(LoginSchema)
    def post(self, data):
        """Authenticate user and return tokens."""
        try:
            client_info = get_client_info()
            
            result = auth_service.authenticate_user(
                identifier=data['identifier'],
                password=data['password'],
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent']
            )
            
            if result['success']:
                # Remove sensitive data
                user_data = result['user'].copy()
                user_data.pop('password_hash', None)
                user_data.pop('api_key', None)
                
                return {
                    'success': True,
                    'message': RESPONSE_MESSAGES['SUCCESS'],
                    'user': user_data,
                    'tokens': result['tokens'],
                    'session': result['session']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['UNAUTHORIZED']
                
        except AuthenticationError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['UNAUTHORIZED']
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class LogoutResource(Resource):
    """User logout endpoint."""
    
    @jwt_required()
    def post(self):
        """Logout user and invalidate session."""
        try:
            user_id = get_jwt_identity()
            jti = get_jwt().get('jti')  # JWT ID for token blacklisting
            
            result = auth_service.logout_user(user_id=user_id)
            
            # TODO: Add token to blacklist
            # blacklist_service.add_token(jti)
            
            return {
                'success': True,
                'message': 'Logged out successfully'
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Logout error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class RefreshTokenResource(Resource):
    """Token refresh endpoint."""
    
    @validate_json(RefreshTokenSchema)
    def post(self, data):
        """Refresh access token using refresh token."""
        try:
            result = auth_service.refresh_token(data['refresh_token'])
            
            if result['success']:
                return {
                    'success': True,
                    'message': RESPONSE_MESSAGES['SUCCESS'],
                    'tokens': result['tokens']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['UNAUTHORIZED']
                
        except AuthenticationError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['UNAUTHORIZED']
        except Exception as e:
            current_app.logger.error(f"Token refresh error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class ProfileResource(Resource):
    """User profile endpoint."""
    
    @jwt_required()
    def get(self):
        """Get current user profile."""
        try:
            user_id = get_jwt_identity()
            user = User.get_by_id(user_id)
            
            if not user:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['NOT_FOUND']
                }, HTTP_STATUS['NOT_FOUND']
            
            # Get user permissions
            permissions = permission_service.get_user_permissions(user_id)
            
            user_data = user.to_dict()
            user_data.pop('password_hash', None)
            user_data.pop('api_key', None)
            user_data['permissions'] = permissions
            
            return {
                'success': True,
                'user': user_data
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get profile error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    def put(self):
        """Update user profile."""
        try:
            user_id = get_jwt_identity()
            user = User.get_by_id(user_id)
            
            if not user:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['NOT_FOUND']
                }, HTTP_STATUS['NOT_FOUND']
            
            data = request.get_json() or {}
            
            # Update allowed fields
            allowed_fields = ['first_name', 'last_name', 'nickname', 'bio', 'timezone', 'language']
            updated = False
            
            for field in allowed_fields:
                if field in data:
                    setattr(user, field, data[field])
                    updated = True
            
            if updated:
                user.save()
            
            user_data = user.to_dict()
            user_data.pop('password_hash', None)
            user_data.pop('api_key', None)
            
            return {
                'success': True,
                'message': RESPONSE_MESSAGES['UPDATED'],
                'user': user_data
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Update profile error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class ChangePasswordResource(Resource):
    """Change password endpoint."""
    
    @jwt_required()
    @validate_json(ChangePasswordSchema)
    def post(self, data):
        """Change user password."""
        try:
            user_id = get_jwt_identity()
            
            result = auth_service.change_password(
                user_id=user_id,
                current_password=data['current_password'],
                new_password=data['new_password']
            )
            
            if result['success']:
                return {
                    'success': True,
                    'message': result['message']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except AuthenticationError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['BAD_REQUEST']
        except Exception as e:
            current_app.logger.error(f"Change password error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class ResetPasswordRequestResource(Resource):
    """Password reset request endpoint."""
    
    @validate_json(ResetPasswordRequestSchema)
    def post(self, data):
        """Request password reset."""
        try:
            result = auth_service.reset_password_request(data['email'])
            
            # Always return success to prevent email enumeration
            return {
                'success': True,
                'message': result['message']
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Password reset request error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class ResetPasswordResource(Resource):
    """Password reset endpoint."""
    
    @validate_json(ResetPasswordSchema)
    def post(self, data):
        """Reset password using reset token."""
        try:
            result = auth_service.reset_password(
                reset_token=data['reset_token'],
                new_password=data['new_password']
            )
            
            if result['success']:
                return {
                    'success': True,
                    'message': result['message']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except AuthenticationError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['BAD_REQUEST']
        except Exception as e:
            current_app.logger.error(f"Password reset error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class VerifyEmailResource(Resource):
    """Email verification endpoint."""
    
    def get(self, user_id, token):
        """Verify email address."""
        try:
            result = auth_service.verify_email(user_id, token)
            
            if result['success']:
                return {
                    'success': True,
                    'message': result['message']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except AuthenticationError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['BAD_REQUEST']
        except Exception as e:
            current_app.logger.error(f"Email verification error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class PermissionCheckResource(Resource):
    """Permission check endpoint."""
    
    @jwt_required()
    def post(self):
        """Check if user has specific permissions."""
        try:
            user_id = get_jwt_identity()
            user = User.get_by_id(user_id)
            
            if not user:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['NOT_FOUND']
                }, HTTP_STATUS['NOT_FOUND']
            
            data = request.get_json() or {}
            permissions = data.get('permissions', [])
            
            if not isinstance(permissions, list):
                return {
                    'success': False,
                    'message': 'Permissions must be a list'
                }, HTTP_STATUS['BAD_REQUEST']
            
            results = {}
            for permission in permissions:
                if isinstance(permission, str):
                    results[permission] = auth_service.check_permission(user, permission)
                elif isinstance(permission, dict):
                    perm_name = permission.get('name')
                    resource_type = permission.get('resource_type')
                    resource_id = permission.get('resource_id')
                    
                    if perm_name:
                        results[perm_name] = auth_service.check_permission(
                            user, perm_name, resource_type, resource_id
                        )
            
            return {
                'success': True,
                'permissions': results
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Permission check error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


# Register API resources
api.add_resource(RegisterResource, '/register')
api.add_resource(LoginResource, '/login')
api.add_resource(LogoutResource, '/logout')
api.add_resource(RefreshTokenResource, '/refresh')
api.add_resource(ProfileResource, '/profile')
api.add_resource(ChangePasswordResource, '/change-password')
api.add_resource(ResetPasswordRequestResource, '/reset-password-request')
api.add_resource(ResetPasswordResource, '/reset-password')
api.add_resource(VerifyEmailResource, '/verify-email/<string:user_id>/<string:token>')
api.add_resource(PermissionCheckResource, '/check-permissions')


# Error handlers
@auth_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handle validation errors."""
    return {
        'success': False,
        'message': RESPONSE_MESSAGES['VALIDATION_ERROR'],
        'errors': e.messages
    }, HTTP_STATUS['BAD_REQUEST']


@auth_bp.errorhandler(AuthenticationError)
def handle_auth_error(e):
    """Handle authentication errors."""
    return {
        'success': False,
        'message': str(e)
    }, HTTP_STATUS['UNAUTHORIZED']


@auth_bp.errorhandler(AuthorizationError)
def handle_authz_error(e):
    """Handle authorization errors."""
    return {
        'success': False,
        'message': str(e)
    }, HTTP_STATUS['FORBIDDEN']


@auth_bp.errorhandler(Exception)
def handle_generic_error(e):
    """Handle generic errors."""
    current_app.logger.error(f"Unhandled error in auth API: {str(e)}")
    return {
        'success': False,
        'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
    }, HTTP_STATUS['INTERNAL_SERVER_ERROR']