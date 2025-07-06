#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Permission Service for Ragflow-MinerU Integration

This module provides permission and authorization management services.
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from flask import current_app

from backend.models.user import User, UserRole
from backend.models.permission import (
    Permission, RolePermission, UserPermission, AccessLog,
    PermissionType, AccessLevel
)


class PermissionError(Exception):
    """Permission related errors."""
    pass


class PermissionService:
    """Permission and authorization service."""
    
    def __init__(self):
        self._permission_cache = {}
        self._cache_ttl = timedelta(minutes=15)
        self._last_cache_update = {}
    
    def check_user_permission(self, 
                             user_id: str, 
                             permission_name: str,
                             resource_type: str = None,
                             resource_id: str = None,
                             log_access: bool = True) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            user_id (str): User ID
            permission_name (str): Permission name
            resource_type (str, optional): Resource type
            resource_id (str, optional): Resource ID
            log_access (bool): Whether to log access attempt
            
        Returns:
            bool: True if user has permission
        """
        try:
            user = User.get_by_id(user_id)
            if not user or not user.is_active:
                if log_access:
                    AccessLog.log_access(
                        user_id=user_id,
                        permission_name=permission_name,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        access_granted=False,
                        access_reason='User not found or inactive'
                    )
                return False
            
            # Superuser has all permissions
            if user.is_superuser:
                if log_access:
                    AccessLog.log_access(
                        user_id=user_id,
                        permission_name=permission_name,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        access_granted=True,
                        access_reason='Superuser access'
                    )
                return True
            
            # Check direct user permissions
            has_permission = self._check_direct_user_permission(
                user_id, permission_name, resource_type, resource_id
            )
            
            if not has_permission:
                # Check role-based permissions
                has_permission = self._check_role_permission(
                    user, permission_name, resource_type, resource_id
                )
            
            # Log access attempt
            if log_access:
                AccessLog.log_access(
                    user_id=user_id,
                    permission_name=permission_name,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    access_granted=has_permission,
                    access_reason='Permission check' if has_permission else 'Permission denied'
                )
            
            return has_permission
            
        except Exception as e:
            current_app.logger.error(f"Permission check error: {str(e)}")
            if log_access:
                AccessLog.log_access(
                    user_id=user_id,
                    permission_name=permission_name,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    access_granted=False,
                    access_reason=f'Error: {str(e)}'
                )
            return False
    
    def get_user_permissions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all permissions for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            List[Dict[str, Any]]: List of permissions
        """
        try:
            user = User.get_by_id(user_id)
            if not user:
                return []
            
            permissions = []
            
            # Get direct user permissions
            user_perms = UserPermission.get_user_permissions(user_id)
            for perm in user_perms:
                if perm.is_valid:
                    permissions.append({
                        'name': perm.permission.name,
                        'display_name': perm.permission.display_name,
                        'type': perm.permission.type,
                        'source': 'direct',
                        'resource_type': perm.resource_type,
                        'resource_id': perm.resource_id,
                        'granted_at': perm.granted_at.isoformat(),
                        'expires_at': perm.expires_at.isoformat() if perm.expires_at else None
                    })
            
            # Get role-based permissions
            if user.role:
                role_perms = RolePermission.get_role_permissions(user.role_id)
                for perm in role_perms:
                    if perm.is_valid:
                        permissions.append({
                            'name': perm.permission.name,
                            'display_name': perm.permission.display_name,
                            'type': perm.permission.type,
                            'source': 'role',
                            'role_name': user.role.name,
                            'granted_at': perm.granted_at.isoformat(),
                            'expires_at': perm.expires_at.isoformat() if perm.expires_at else None
                        })
            
            return permissions
            
        except Exception as e:
            current_app.logger.error(f"Get user permissions error: {str(e)}")
            return []
    
    def grant_user_permission(self, 
                             user_id: str, 
                             permission_name: str,
                             granted_by: str,
                             resource_type: str = None,
                             resource_id: str = None,
                             expires_at: datetime = None,
                             conditions: Dict[str, Any] = None) -> bool:
        """
        Grant permission to user.
        
        Args:
            user_id (str): User ID
            permission_name (str): Permission name
            granted_by (str): ID of user granting permission
            resource_type (str, optional): Resource type
            resource_id (str, optional): Resource ID
            expires_at (datetime, optional): Expiration time
            conditions (Dict[str, Any], optional): Permission conditions
            
        Returns:
            bool: True if permission granted successfully
        """
        try:
            # Check if permission exists
            permission = Permission.get_by_name(permission_name)
            if not permission:
                raise PermissionError(f"Permission '{permission_name}' not found")
            
            # Check if user exists
            user = User.get_by_id(user_id)
            if not user:
                raise PermissionError("User not found")
            
            # Check if granter has permission to grant this permission
            granter = User.get_by_id(granted_by)
            if not granter or not granter.is_superuser:
                # TODO: Implement more granular permission granting rules
                raise PermissionError("Insufficient privileges to grant permission")
            
            # Grant permission
            user_perm = UserPermission.grant_permission(
                user_id=user_id,
                permission_id=permission.id,
                granted_by=granted_by,
                resource_type=resource_type,
                resource_id=resource_id,
                expires_at=expires_at,
                conditions=conditions
            )
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            current_app.logger.info(
                f"Permission '{permission_name}' granted to user {user_id} by {granted_by}"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Grant user permission error: {str(e)}")
            raise PermissionError(str(e))
    
    def revoke_user_permission(self, 
                              user_id: str, 
                              permission_name: str,
                              resource_type: str = None,
                              resource_id: str = None) -> bool:
        """
        Revoke permission from user.
        
        Args:
            user_id (str): User ID
            permission_name (str): Permission name
            resource_type (str, optional): Resource type
            resource_id (str, optional): Resource ID
            
        Returns:
            bool: True if permission revoked successfully
        """
        try:
            permission = Permission.get_by_name(permission_name)
            if not permission:
                return False
            
            # Find and revoke permission
            query = UserPermission.select().where(
                (UserPermission.user_id == user_id) &
                (UserPermission.permission_id == permission.id) &
                (UserPermission.is_active == True)
            )
            
            if resource_type:
                query = query.where(UserPermission.resource_type == resource_type)
            
            if resource_id:
                query = query.where(UserPermission.resource_id == resource_id)
            
            for user_perm in query:
                user_perm.revoke()
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            current_app.logger.info(
                f"Permission '{permission_name}' revoked from user {user_id}"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Revoke user permission error: {str(e)}")
            return False
    
    def create_role(self, 
                   name: str, 
                   display_name: str,
                   description: str = None,
                   permissions: List[str] = None,
                   created_by: str = None) -> UserRole:
        """
        Create a new role.
        
        Args:
            name (str): Role name
            display_name (str): Display name
            description (str, optional): Description
            permissions (List[str], optional): List of permission names
            created_by (str, optional): Creator user ID
            
        Returns:
            UserRole: Created role
        """
        try:
            # Check if role already exists
            if UserRole.get_by_name(name):
                raise PermissionError(f"Role '{name}' already exists")
            
            # Create role
            role = UserRole.create(
                name=name,
                display_name=display_name,
                description=description,
                permissions=permissions or [],
                created_by=created_by
            )
            
            # Grant permissions to role
            if permissions:
                for perm_name in permissions:
                    self.grant_role_permission(role.id, perm_name, created_by)
            
            current_app.logger.info(f"Role '{name}' created by {created_by}")
            
            return role
            
        except Exception as e:
            current_app.logger.error(f"Create role error: {str(e)}")
            raise PermissionError(str(e))
    
    def grant_role_permission(self, 
                             role_id: str, 
                             permission_name: str,
                             granted_by: str,
                             expires_at: datetime = None,
                             conditions: Dict[str, Any] = None) -> bool:
        """
        Grant permission to role.
        
        Args:
            role_id (str): Role ID
            permission_name (str): Permission name
            granted_by (str): ID of user granting permission
            expires_at (datetime, optional): Expiration time
            conditions (Dict[str, Any], optional): Permission conditions
            
        Returns:
            bool: True if permission granted successfully
        """
        try:
            # Check if permission exists
            permission = Permission.get_by_name(permission_name)
            if not permission:
                raise PermissionError(f"Permission '{permission_name}' not found")
            
            # Check if role exists
            role = UserRole.get_by_id(role_id)
            if not role:
                raise PermissionError("Role not found")
            
            # Grant permission
            role_perm = RolePermission.grant_permission(
                role_id=role_id,
                permission_id=permission.id,
                granted_by=granted_by,
                expires_at=expires_at,
                conditions=conditions
            )
            
            # Clear cache for all users with this role
            self._clear_role_cache(role_id)
            
            current_app.logger.info(
                f"Permission '{permission_name}' granted to role {role.name} by {granted_by}"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Grant role permission error: {str(e)}")
            raise PermissionError(str(e))
    
    def revoke_role_permission(self, role_id: str, permission_name: str) -> bool:
        """
        Revoke permission from role.
        
        Args:
            role_id (str): Role ID
            permission_name (str): Permission name
            
        Returns:
            bool: True if permission revoked successfully
        """
        try:
            permission = Permission.get_by_name(permission_name)
            if not permission:
                return False
            
            # Find and revoke permission
            role_perms = RolePermission.select().where(
                (RolePermission.role_id == role_id) &
                (RolePermission.permission_id == permission.id) &
                (RolePermission.is_active == True)
            )
            
            for role_perm in role_perms:
                role_perm.revoke()
            
            # Clear cache
            self._clear_role_cache(role_id)
            
            role = UserRole.get_by_id(role_id)
            current_app.logger.info(
                f"Permission '{permission_name}' revoked from role {role.name if role else role_id}"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Revoke role permission error: {str(e)}")
            return False
    
    def assign_user_role(self, user_id: str, role_name: str, assigned_by: str = None) -> bool:
        """
        Assign role to user.
        
        Args:
            user_id (str): User ID
            role_name (str): Role name
            assigned_by (str, optional): ID of user assigning role
            
        Returns:
            bool: True if role assigned successfully
        """
        try:
            user = User.get_by_id(user_id)
            if not user:
                raise PermissionError("User not found")
            
            role = UserRole.get_by_name(role_name)
            if not role:
                raise PermissionError(f"Role '{role_name}' not found")
            
            # Assign role
            user.role_id = role.id
            user.save()
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            current_app.logger.info(
                f"Role '{role_name}' assigned to user {user.username} by {assigned_by}"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Assign user role error: {str(e)}")
            raise PermissionError(str(e))
    
    def get_permission_hierarchy(self, permission_name: str) -> Dict[str, Any]:
        """
        Get permission hierarchy.
        
        Args:
            permission_name (str): Permission name
            
        Returns:
            Dict[str, Any]: Permission hierarchy
        """
        try:
            permission = Permission.get_by_name(permission_name)
            if not permission:
                return {}
            
            hierarchy = {
                'permission': permission.to_dict(),
                'parent': None,
                'children': []
            }
            
            # Get parent permission
            if permission.parent_id:
                parent = Permission.get_by_id(permission.parent_id)
                if parent:
                    hierarchy['parent'] = parent.to_dict()
            
            # Get child permissions
            children = Permission.select().where(Permission.parent_id == permission.id)
            hierarchy['children'] = [child.to_dict() for child in children]
            
            return hierarchy
            
        except Exception as e:
            current_app.logger.error(f"Get permission hierarchy error: {str(e)}")
            return {}
    
    def get_access_logs(self, 
                       user_id: str = None,
                       permission_name: str = None,
                       start_date: datetime = None,
                       end_date: datetime = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get access logs.
        
        Args:
            user_id (str, optional): User ID
            permission_name (str, optional): Permission name
            start_date (datetime, optional): Start date
            end_date (datetime, optional): End date
            limit (int): Maximum number of logs
            
        Returns:
            List[Dict[str, Any]]: Access logs
        """
        try:
            return AccessLog.get_access_logs(
                user_id=user_id,
                permission_name=permission_name,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
        except Exception as e:
            current_app.logger.error(f"Get access logs error: {str(e)}")
            return []
    
    def get_permission_usage_stats(self, 
                                  start_date: datetime = None,
                                  end_date: datetime = None) -> Dict[str, Any]:
        """
        Get permission usage statistics.
        
        Args:
            start_date (datetime, optional): Start date
            end_date (datetime, optional): End date
            
        Returns:
            Dict[str, Any]: Usage statistics
        """
        try:
            return AccessLog.get_permission_usage_stats(
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            current_app.logger.error(f"Get permission usage stats error: {str(e)}")
            return {}
    
    def _check_direct_user_permission(self, 
                                     user_id: str, 
                                     permission_name: str,
                                     resource_type: str = None,
                                     resource_id: str = None) -> bool:
        """
        Check direct user permission.
        
        Args:
            user_id (str): User ID
            permission_name (str): Permission name
            resource_type (str, optional): Resource type
            resource_id (str, optional): Resource ID
            
        Returns:
            bool: True if user has direct permission
        """
        try:
            permission = Permission.get_by_name(permission_name)
            if not permission:
                return False
            
            # Check cache first
            cache_key = f"user_perm_{user_id}_{permission.id}_{resource_type}_{resource_id}"
            if self._is_cache_valid(cache_key):
                return self._permission_cache.get(cache_key, False)
            
            # Query database
            query = UserPermission.select().where(
                (UserPermission.user_id == user_id) &
                (UserPermission.permission_id == permission.id) &
                (UserPermission.is_active == True)
            )
            
            if resource_type:
                query = query.where(UserPermission.resource_type == resource_type)
            
            if resource_id:
                query = query.where(UserPermission.resource_id == resource_id)
            
            has_permission = False
            for user_perm in query:
                if user_perm.is_valid:
                    has_permission = True
                    break
            
            # Cache result
            self._permission_cache[cache_key] = has_permission
            self._last_cache_update[cache_key] = datetime.now()
            
            return has_permission
            
        except Exception as e:
            current_app.logger.error(f"Check direct user permission error: {str(e)}")
            return False
    
    def _check_role_permission(self, 
                              user: User, 
                              permission_name: str,
                              resource_type: str = None,
                              resource_id: str = None) -> bool:
        """
        Check role-based permission.
        
        Args:
            user (User): User instance
            permission_name (str): Permission name
            resource_type (str, optional): Resource type
            resource_id (str, optional): Resource ID
            
        Returns:
            bool: True if user has role-based permission
        """
        try:
            if not user.role:
                return False
            
            permission = Permission.get_by_name(permission_name)
            if not permission:
                return False
            
            # Check cache first
            cache_key = f"role_perm_{user.role_id}_{permission.id}"
            if self._is_cache_valid(cache_key):
                return self._permission_cache.get(cache_key, False)
            
            # Query database
            role_perms = RolePermission.select().where(
                (RolePermission.role_id == user.role_id) &
                (RolePermission.permission_id == permission.id) &
                (RolePermission.is_active == True)
            )
            
            has_permission = False
            for role_perm in role_perms:
                if role_perm.is_valid:
                    has_permission = True
                    break
            
            # Cache result
            self._permission_cache[cache_key] = has_permission
            self._last_cache_update[cache_key] = datetime.now()
            
            return has_permission
            
        except Exception as e:
            current_app.logger.error(f"Check role permission error: {str(e)}")
            return False
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cache entry is valid.
        
        Args:
            cache_key (str): Cache key
            
        Returns:
            bool: True if cache is valid
        """
        if cache_key not in self._permission_cache:
            return False
        
        last_update = self._last_cache_update.get(cache_key)
        if not last_update:
            return False
        
        return datetime.now() - last_update < self._cache_ttl
    
    def _clear_user_cache(self, user_id: str) -> None:
        """
        Clear cache for user.
        
        Args:
            user_id (str): User ID
        """
        keys_to_remove = [
            key for key in self._permission_cache.keys()
            if key.startswith(f"user_perm_{user_id}_")
        ]
        
        for key in keys_to_remove:
            self._permission_cache.pop(key, None)
            self._last_cache_update.pop(key, None)
    
    def _clear_role_cache(self, role_id: str) -> None:
        """
        Clear cache for role.
        
        Args:
            role_id (str): Role ID
        """
        keys_to_remove = [
            key for key in self._permission_cache.keys()
            if key.startswith(f"role_perm_{role_id}_")
        ]
        
        for key in keys_to_remove:
            self._permission_cache.pop(key, None)
            self._last_cache_update.pop(key, None)
        
        # Also clear user caches for users with this role
        users_with_role = User.select().where(User.role_id == role_id)
        for user in users_with_role:
            self._clear_user_cache(user.id)
    
    @staticmethod
    def cleanup_expired_permissions() -> Dict[str, int]:
        """
        Clean up expired permissions.
        
        Returns:
            Dict[str, int]: Cleanup statistics
        """
        try:
            user_perms_cleaned = 0
            role_perms_cleaned = 0
            
            # Clean up expired user permissions
            expired_user_perms = UserPermission.select().where(
                (UserPermission.expires_at.is_null(False)) &
                (UserPermission.expires_at < datetime.now()) &
                (UserPermission.is_active == True)
            )
            
            for perm in expired_user_perms:
                perm.revoke()
                user_perms_cleaned += 1
            
            # Clean up expired role permissions
            expired_role_perms = RolePermission.select().where(
                (RolePermission.expires_at.is_null(False)) &
                (RolePermission.expires_at < datetime.now()) &
                (RolePermission.is_active == True)
            )
            
            for perm in expired_role_perms:
                perm.revoke()
                role_perms_cleaned += 1
            
            # Clean up old access logs
            logs_cleaned = AccessLog.cleanup_old_logs()
            
            current_app.logger.info(
                f"Permission cleanup completed: {user_perms_cleaned} user permissions, "
                f"{role_perms_cleaned} role permissions, {logs_cleaned} access logs"
            )
            
            return {
                'user_permissions_cleaned': user_perms_cleaned,
                'role_permissions_cleaned': role_perms_cleaned,
                'access_logs_cleaned': logs_cleaned
            }
            
        except Exception as e:
            current_app.logger.error(f"Permission cleanup error: {str(e)}")
            return {
                'user_permissions_cleaned': 0,
                'role_permissions_cleaned': 0,
                'access_logs_cleaned': 0
            }