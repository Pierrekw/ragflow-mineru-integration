#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Permission Management API for Ragflow-MinerU Integration

This module provides permission and role management API endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from functools import wraps
from datetime import datetime, timedelta

from backend.services.permission_service import PermissionService
from backend.services.auth_service import AuthService
from backend.models.permission import Permission, PermissionType, AccessLevel
from backend.models.role import Role
from backend.models.user import User
from backend.api import HTTP_STATUS, RESPONSE_MESSAGES
from backend.api.auth import require_permission


# Create blueprint
permissions_bp = Blueprint('permissions', __name__, url_prefix='/api/v1/permissions')
api = Api(permissions_bp)

# Initialize services
permission_service = PermissionService()
auth_service = AuthService()


# Validation schemas
class PermissionCreateSchema(Schema):
    """Permission creation validation schema."""
    name = fields.Str(required=True, validate=lambda x: len(x) <= 100)
    display_name = fields.Str(required=True, validate=lambda x: len(x) <= 255)
    description = fields.Str(allow_none=True, validate=lambda x: len(x) <= 1000 if x else True)
    permission_type = fields.Str(required=True, validate=lambda x: x in [t.value for t in PermissionType])
    category = fields.Str(load_default='general', validate=lambda x: len(x) <= 50)
    parent_id = fields.Str(allow_none=True)
    is_system = fields.Bool(load_default=False)
    requires_approval = fields.Bool(load_default=False)
    is_dangerous = fields.Bool(load_default=False)
    resource_pattern = fields.Str(allow_none=True)
    conditions = fields.Dict(load_default={})
    tags = fields.List(fields.Str(), load_default=[])
    metadata = fields.Dict(load_default={})


class RoleCreateSchema(Schema):
    """Role creation validation schema."""
    name = fields.Str(required=True, validate=lambda x: len(x) <= 100)
    display_name = fields.Str(required=True, validate=lambda x: len(x) <= 255)
    description = fields.Str(allow_none=True, validate=lambda x: len(x) <= 1000 if x else True)
    is_system = fields.Bool(load_default=False)
    is_default = fields.Bool(load_default=False)
    access_level = fields.Str(load_default='user', validate=lambda x: x in [l.value for l in AccessLevel])
    permissions = fields.List(fields.Str(), load_default=[])
    tags = fields.List(fields.Str(), load_default=[])
    metadata = fields.Dict(load_default={})


class PermissionGrantSchema(Schema):
    """Permission grant validation schema."""
    user_id = fields.Str(allow_none=True)
    role_id = fields.Str(allow_none=True)
    permission_id = fields.Str(required=True)
    resource_type = fields.Str(allow_none=True)
    resource_id = fields.Str(allow_none=True)
    conditions = fields.Dict(load_default={})
    expires_at = fields.DateTime(allow_none=True)
    reason = fields.Str(allow_none=True, validate=lambda x: len(x) <= 500 if x else True)


class RoleAssignSchema(Schema):
    """Role assignment validation schema."""
    user_id = fields.Str(required=True)
    role_id = fields.Str(required=True)
    expires_at = fields.DateTime(allow_none=True)
    reason = fields.Str(allow_none=True, validate=lambda x: len(x) <= 500 if x else True)


class AccessLogSearchSchema(Schema):
    """Access log search validation schema."""
    user_id = fields.Str(allow_none=True)
    permission_name = fields.Str(allow_none=True)
    resource_type = fields.Str(allow_none=True)
    resource_id = fields.Str(allow_none=True)
    access_result = fields.Str(allow_none=True, validate=lambda x: x in ['granted', 'denied'] if x else True)
    ip_address = fields.Str(allow_none=True)
    created_after = fields.DateTime(allow_none=True)
    created_before = fields.DateTime(allow_none=True)
    page = fields.Int(load_default=1, validate=lambda x: x > 0)
    per_page = fields.Int(load_default=20, validate=lambda x: 1 <= x <= 100)
    sort_by = fields.Str(load_default='created_at', validate=lambda x: x in ['created_at', 'user_id', 'permission_name'])
    sort_order = fields.Str(load_default='desc', validate=lambda x: x in ['asc', 'desc'])


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


def get_permission_or_404(permission_id):
    """Get permission by ID or return 404."""
    permission = Permission.get_by_id(permission_id)
    if not permission:
        return None, {
            'success': False,
            'message': RESPONSE_MESSAGES['NOT_FOUND']
        }, HTTP_STATUS['NOT_FOUND']
    return permission, None, None


def get_role_or_404(role_id):
    """Get role by ID or return 404."""
    role = Role.get_by_id(role_id)
    if not role:
        return None, {
            'success': False,
            'message': RESPONSE_MESSAGES['NOT_FOUND']
        }, HTTP_STATUS['NOT_FOUND']
    return role, None, None


# API Resources
class PermissionListResource(Resource):
    """Permission list endpoint."""
    
    @jwt_required()
    @require_permission('permission.read')
    def get(self):
        """Get permissions with filtering."""
        try:
            # Parse query parameters
            parser = reqparse.RequestParser()
            parser.add_argument('category', type=str, location='args')
            parser.add_argument('permission_type', type=str, location='args')
            parser.add_argument('is_system', type=bool, location='args')
            parser.add_argument('parent_id', type=str, location='args')
            parser.add_argument('page', type=int, default=1, location='args')
            parser.add_argument('per_page', type=int, default=50, location='args')
            
            args = parser.parse_args()
            
            # Validate pagination
            if args['page'] < 1:
                args['page'] = 1
            if args['per_page'] < 1 or args['per_page'] > 100:
                args['per_page'] = 50
            
            # Get permissions
            permissions = Permission.search(
                category=args['category'],
                permission_type=args['permission_type'],
                is_system=args['is_system'],
                parent_id=args['parent_id'],
                page=args['page'],
                per_page=args['per_page']
            )
            
            return {
                'success': True,
                'permissions': [p.to_dict() for p in permissions['items']],
                'pagination': {
                    'page': permissions['page'],
                    'per_page': permissions['per_page'],
                    'total': permissions['total'],
                    'pages': permissions['pages']
                }
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get permissions error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('permission.create')
    @validate_json(PermissionCreateSchema)
    def post(self, data):
        """Create a new permission."""
        try:
            user_id = get_jwt_identity()
            
            # Check if permission name already exists
            existing = Permission.get_by_name(data['name'])
            if existing:
                return {
                    'success': False,
                    'message': 'Permission name already exists'
                }, HTTP_STATUS['BAD_REQUEST']
            
            # Create permission
            permission = Permission(
                name=data['name'],
                display_name=data['display_name'],
                description=data.get('description'),
                permission_type=data['permission_type'],
                category=data.get('category', 'general'),
                parent_id=data.get('parent_id'),
                is_system=data.get('is_system', False),
                requires_approval=data.get('requires_approval', False),
                is_dangerous=data.get('is_dangerous', False),
                resource_pattern=data.get('resource_pattern'),
                conditions=data.get('conditions', {}),
                tags=data.get('tags', []),
                metadata=data.get('metadata', {}),
                created_by=user_id
            )
            permission.save()
            
            return {
                'success': True,
                'message': RESPONSE_MESSAGES['CREATED'],
                'permission': permission.to_dict()
            }, HTTP_STATUS['CREATED']
            
        except Exception as e:
            current_app.logger.error(f"Create permission error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class PermissionResource(Resource):
    """Individual permission endpoint."""
    
    @jwt_required()
    @require_permission('permission.read')
    def get(self, permission_id):
        """Get permission details."""
        try:
            permission, error_response, status_code = get_permission_or_404(permission_id)
            
            if error_response:
                return error_response, status_code
            
            return {
                'success': True,
                'permission': permission.to_dict()
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get permission error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('permission.update')
    def put(self, permission_id):
        """Update permission."""
        try:
            permission, error_response, status_code = get_permission_or_404(permission_id)
            
            if error_response:
                return error_response, status_code
            
            # Check if permission is system permission
            if permission.is_system:
                return {
                    'success': False,
                    'message': 'Cannot modify system permission'
                }, HTTP_STATUS['FORBIDDEN']
            
            data = request.get_json() or {}
            
            # Update allowed fields
            allowed_fields = ['display_name', 'description', 'category', 'requires_approval', 
                            'is_dangerous', 'resource_pattern', 'conditions', 'tags', 'metadata']
            updated = False
            
            for field in allowed_fields:
                if field in data:
                    setattr(permission, field, data[field])
                    updated = True
            
            if updated:
                permission.updated_at = datetime.utcnow()
                permission.save()
            
            return {
                'success': True,
                'message': RESPONSE_MESSAGES['UPDATED'],
                'permission': permission.to_dict()
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Update permission error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('permission.delete')
    def delete(self, permission_id):
        """Delete permission."""
        try:
            permission, error_response, status_code = get_permission_or_404(permission_id)
            
            if error_response:
                return error_response, status_code
            
            # Check if permission is system permission
            if permission.is_system:
                return {
                    'success': False,
                    'message': 'Cannot delete system permission'
                }, HTTP_STATUS['FORBIDDEN']
            
            # Check if permission is in use
            if permission.is_in_use():
                return {
                    'success': False,
                    'message': 'Cannot delete permission that is in use'
                }, HTTP_STATUS['BAD_REQUEST']
            
            permission.delete()
            
            return {
                'success': True,
                'message': 'Permission deleted successfully'
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Delete permission error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class RoleListResource(Resource):
    """Role list endpoint."""
    
    @jwt_required()
    @require_permission('role.read')
    def get(self):
        """Get roles with filtering."""
        try:
            # Parse query parameters
            parser = reqparse.RequestParser()
            parser.add_argument('is_system', type=bool, location='args')
            parser.add_argument('access_level', type=str, location='args')
            parser.add_argument('page', type=int, default=1, location='args')
            parser.add_argument('per_page', type=int, default=20, location='args')
            
            args = parser.parse_args()
            
            # Validate pagination
            if args['page'] < 1:
                args['page'] = 1
            if args['per_page'] < 1 or args['per_page'] > 100:
                args['per_page'] = 20
            
            # Get roles
            roles = Role.search(
                is_system=args['is_system'],
                access_level=args['access_level'],
                page=args['page'],
                per_page=args['per_page']
            )
            
            return {
                'success': True,
                'roles': [r.to_dict() for r in roles['items']],
                'pagination': {
                    'page': roles['page'],
                    'per_page': roles['per_page'],
                    'total': roles['total'],
                    'pages': roles['pages']
                }
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get roles error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('role.create')
    @validate_json(RoleCreateSchema)
    def post(self, data):
        """Create a new role."""
        try:
            user_id = get_jwt_identity()
            
            # Check if role name already exists
            existing = Role.get_by_name(data['name'])
            if existing:
                return {
                    'success': False,
                    'message': 'Role name already exists'
                }, HTTP_STATUS['BAD_REQUEST']
            
            # Create role
            result = permission_service.create_role(
                name=data['name'],
                display_name=data['display_name'],
                description=data.get('description'),
                is_system=data.get('is_system', False),
                is_default=data.get('is_default', False),
                access_level=data.get('access_level', 'user'),
                permissions=data.get('permissions', []),
                tags=data.get('tags', []),
                metadata=data.get('metadata', {}),
                created_by=user_id
            )
            
            if result['success']:
                return {
                    'success': True,
                    'message': RESPONSE_MESSAGES['CREATED'],
                    'role': result['role']
                }, HTTP_STATUS['CREATED']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Create role error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class RoleResource(Resource):
    """Individual role endpoint."""
    
    @jwt_required()
    @require_permission('role.read')
    def get(self, role_id):
        """Get role details."""
        try:
            role, error_response, status_code = get_role_or_404(role_id)
            
            if error_response:
                return error_response, status_code
            
            role_data = role.to_dict()
            
            # Add permissions
            permissions = permission_service.get_role_permissions(role_id)
            role_data['permissions'] = permissions
            
            return {
                'success': True,
                'role': role_data
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get role error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('role.delete')
    def delete(self, role_id):
        """Delete role."""
        try:
            role, error_response, status_code = get_role_or_404(role_id)
            
            if error_response:
                return error_response, status_code
            
            # Check if role is system role
            if role.is_system:
                return {
                    'success': False,
                    'message': 'Cannot delete system role'
                }, HTTP_STATUS['FORBIDDEN']
            
            # Check if role is in use
            if role.is_in_use():
                return {
                    'success': False,
                    'message': 'Cannot delete role that is assigned to users'
                }, HTTP_STATUS['BAD_REQUEST']
            
            role.delete()
            
            return {
                'success': True,
                'message': 'Role deleted successfully'
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Delete role error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class PermissionGrantResource(Resource):
    """Permission grant endpoint."""
    
    @jwt_required()
    @require_permission('permission.grant')
    @validate_json(PermissionGrantSchema)
    def post(self, data):
        """Grant permission to user or role."""
        try:
            user_id = get_jwt_identity()
            
            if data.get('user_id'):
                # Grant permission to user
                result = permission_service.grant_user_permission(
                    user_id=data['user_id'],
                    permission_id=data['permission_id'],
                    granted_by=user_id,
                    resource_type=data.get('resource_type'),
                    resource_id=data.get('resource_id'),
                    conditions=data.get('conditions', {}),
                    expires_at=data.get('expires_at'),
                    reason=data.get('reason')
                )
            elif data.get('role_id'):
                # Grant permission to role
                result = permission_service.grant_role_permission(
                    role_id=data['role_id'],
                    permission_id=data['permission_id'],
                    granted_by=user_id,
                    conditions=data.get('conditions', {}),
                    expires_at=data.get('expires_at'),
                    reason=data.get('reason')
                )
            else:
                return {
                    'success': False,
                    'message': 'Either user_id or role_id must be provided'
                }, HTTP_STATUS['BAD_REQUEST']
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Permission granted successfully'
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Grant permission error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class PermissionRevokeResource(Resource):
    """Permission revoke endpoint."""
    
    @jwt_required()
    @require_permission('permission.revoke')
    def post(self):
        """Revoke permission from user or role."""
        try:
            user_id = get_jwt_identity()
            data = request.get_json() or {}
            
            if data.get('user_id'):
                # Revoke permission from user
                result = permission_service.revoke_user_permission(
                    user_id=data['user_id'],
                    permission_id=data['permission_id'],
                    revoked_by=user_id,
                    resource_type=data.get('resource_type'),
                    resource_id=data.get('resource_id'),
                    reason=data.get('reason')
                )
            elif data.get('role_id'):
                # Revoke permission from role
                result = permission_service.revoke_role_permission(
                    role_id=data['role_id'],
                    permission_id=data['permission_id'],
                    revoked_by=user_id,
                    reason=data.get('reason')
                )
            else:
                return {
                    'success': False,
                    'message': 'Either user_id or role_id must be provided'
                }, HTTP_STATUS['BAD_REQUEST']
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Permission revoked successfully'
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Revoke permission error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class RoleAssignResource(Resource):
    """Role assignment endpoint."""
    
    @jwt_required()
    @require_permission('role.assign')
    @validate_json(RoleAssignSchema)
    def post(self, data):
        """Assign role to user."""
        try:
            user_id = get_jwt_identity()
            
            result = permission_service.assign_user_role(
                user_id=data['user_id'],
                role_id=data['role_id'],
                assigned_by=user_id,
                expires_at=data.get('expires_at'),
                reason=data.get('reason')
            )
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Role assigned successfully'
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Assign role error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class UserPermissionsResource(Resource):
    """User permissions endpoint."""
    
    @jwt_required()
    @require_permission('permission.read')
    def get(self, user_id):
        """Get user permissions."""
        try:
            current_user_id = get_jwt_identity()
            
            # Check if user can view permissions
            if current_user_id != user_id:
                current_user = User.get_by_id(current_user_id)
                if not auth_service.check_permission(current_user, 'permission.admin'):
                    return {
                        'success': False,
                        'message': RESPONSE_MESSAGES['FORBIDDEN']
                    }, HTTP_STATUS['FORBIDDEN']
            
            # Get user permissions
            permissions = permission_service.get_user_permissions(user_id)
            
            return {
                'success': True,
                'permissions': permissions
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get user permissions error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class AccessLogResource(Resource):
    """Access log endpoint."""
    
    @jwt_required()
    @require_permission('permission.audit')
    def get(self):
        """Get access logs."""
        try:
            # Parse query parameters
            parser = reqparse.RequestParser()
            parser.add_argument('user_id', type=str, location='args')
            parser.add_argument('permission_name', type=str, location='args')
            parser.add_argument('resource_type', type=str, location='args')
            parser.add_argument('resource_id', type=str, location='args')
            parser.add_argument('access_result', type=str, location='args')
            parser.add_argument('ip_address', type=str, location='args')
            parser.add_argument('created_after', type=str, location='args')
            parser.add_argument('created_before', type=str, location='args')
            parser.add_argument('page', type=int, default=1, location='args')
            parser.add_argument('per_page', type=int, default=20, location='args')
            parser.add_argument('sort_by', type=str, default='created_at', location='args')
            parser.add_argument('sort_order', type=str, default='desc', location='args')
            
            args = parser.parse_args()
            
            # Validate pagination
            if args['page'] < 1:
                args['page'] = 1
            if args['per_page'] < 1 or args['per_page'] > 100:
                args['per_page'] = 20
            
            # Get access logs
            result = permission_service.get_access_logs(
                user_id=args['user_id'],
                permission_name=args['permission_name'],
                resource_type=args['resource_type'],
                resource_id=args['resource_id'],
                access_result=args['access_result'],
                ip_address=args['ip_address'],
                created_after=args['created_after'],
                created_before=args['created_before'],
                page=args['page'],
                per_page=args['per_page'],
                sort_by=args['sort_by'],
                sort_order=args['sort_order']
            )
            
            return {
                'success': True,
                'logs': result['logs'],
                'pagination': result['pagination']
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get access logs error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class PermissionStatsResource(Resource):
    """Permission statistics endpoint."""
    
    @jwt_required()
    @require_permission('permission.stats')
    def get(self):
        """Get permission usage statistics."""
        try:
            # Parse query parameters
            parser = reqparse.RequestParser()
            parser.add_argument('days', type=int, default=30, location='args')
            
            args = parser.parse_args()
            
            # Get statistics
            result = permission_service.get_permission_stats(days=args['days'])
            
            return {
                'success': True,
                'stats': result['stats']
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get permission stats error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


# Register API resources
api.add_resource(PermissionListResource, '/')
api.add_resource(PermissionResource, '/<string:permission_id>')
api.add_resource(RoleListResource, '/roles')
api.add_resource(RoleResource, '/roles/<string:role_id>')
api.add_resource(PermissionGrantResource, '/grant')
api.add_resource(PermissionRevokeResource, '/revoke')
api.add_resource(RoleAssignResource, '/roles/assign')
api.add_resource(UserPermissionsResource, '/users/<string:user_id>')
api.add_resource(AccessLogResource, '/logs')
api.add_resource(PermissionStatsResource, '/stats')


# Error handlers
@permissions_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handle validation errors."""
    return {
        'success': False,
        'message': RESPONSE_MESSAGES['VALIDATION_ERROR'],
        'errors': e.messages
    }, HTTP_STATUS['BAD_REQUEST']


@permissions_bp.errorhandler(Exception)
def handle_generic_error(e):
    """Handle generic errors."""
    current_app.logger.error(f"Unhandled error in permissions API: {str(e)}")
    return {
        'success': False,
        'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
    }, HTTP_STATUS['INTERNAL_SERVER_ERROR']