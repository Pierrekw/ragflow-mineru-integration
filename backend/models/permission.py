#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Permission models for Ragflow-MinerU Integration

This module contains permission and access control related database models.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from enum import Enum
from peewee import *

from backend.models.base import BaseModel, SoftDeleteModel, JSONField, StatusMixin


class PermissionType(Enum):
    """Permission type enumeration."""
    SYSTEM = 'system'
    USER = 'user'
    DOCUMENT = 'document'
    TASK = 'task'
    API = 'api'
    ADMIN = 'admin'


class AccessLevel(Enum):
    """Access level enumeration."""
    NONE = 'none'
    READ = 'read'
    WRITE = 'write'
    DELETE = 'delete'
    ADMIN = 'admin'
    OWNER = 'owner'


class Permission(BaseModel, StatusMixin):
    """Permission model for defining system permissions."""
    
    # Permission identification
    name = CharField(max_length=100, unique=True, index=True)
    display_name = CharField(max_length=150)
    description = TextField(null=True)
    
    # Permission categorization
    permission_type = CharField(max_length=20, default=PermissionType.SYSTEM.value, index=True)
    category = CharField(max_length=50, null=True, index=True)
    
    # Permission hierarchy
    parent_permission_id = CharField(max_length=36, null=True, index=True)
    level = IntegerField(default=0, index=True)  # Hierarchy level
    
    # Permission configuration
    is_system = BooleanField(default=False)  # System permissions cannot be deleted
    requires_approval = BooleanField(default=False)  # Requires admin approval to grant
    is_dangerous = BooleanField(default=False)  # Dangerous permissions (e.g., delete all)
    
    # Resource constraints
    resource_pattern = CharField(max_length=255, null=True)  # Resource pattern this permission applies to
    conditions = JSONField(default=dict)  # Additional conditions for permission
    
    # Metadata
    tags = JSONField(default=list)
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'permission'
        indexes = (
            (('name',), True),
            (('permission_type', 'category'), False),
            (('parent_permission_id', 'level'), False),
        )
    
    @property
    def parent_permission(self) -> Optional['Permission']:
        """Get parent permission."""
        if not self.parent_permission_id:
            return None
        
        try:
            return Permission.get_by_id(self.parent_permission_id)
        except Permission.DoesNotExist:
            return None
    
    @property
    def child_permissions(self) -> List['Permission']:
        """Get child permissions."""
        return list(
            Permission.select().where(
                Permission.parent_permission_id == self.id
            ).order_by(Permission.name.asc())
        )
    
    @property
    def full_name(self) -> str:
        """Get full permission name with hierarchy."""
        if self.parent_permission:
            return f"{self.parent_permission.full_name}.{self.name}"
        return self.name
    
    def implies(self, other_permission: 'Permission') -> bool:
        """
        Check if this permission implies another permission.
        
        Args:
            other_permission (Permission): Permission to check
            
        Returns:
            bool: True if this permission implies the other
        """
        # Same permission
        if self.id == other_permission.id:
            return True
        
        # Check if other permission is a child of this permission
        current = other_permission.parent_permission
        while current:
            if current.id == self.id:
                return True
            current = current.parent_permission
        
        # Check wildcard patterns
        if self.name.endswith('.*'):
            prefix = self.name[:-2]
            return other_permission.name.startswith(prefix + '.')
        
        if self.name == '*':
            return True
        
        return False
    
    def can_be_granted_to_role(self, role_name: str) -> bool:
        """
        Check if this permission can be granted to a specific role.
        
        Args:
            role_name (str): Role name
            
        Returns:
            bool: True if permission can be granted to role
        """
        # System permissions have restrictions
        if self.is_system and role_name not in ['admin', 'superuser']:
            return False
        
        # Dangerous permissions require admin role
        if self.is_dangerous and role_name not in ['admin', 'superuser']:
            return False
        
        return True
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional['Permission']:
        """
        Get permission by name.
        
        Args:
            name (str): Permission name
            
        Returns:
            Permission: Permission instance or None
        """
        try:
            return cls.get(cls.name == name)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_by_type(cls, permission_type: str) -> List['Permission']:
        """
        Get permissions by type.
        
        Args:
            permission_type (str): Permission type
            
        Returns:
            List[Permission]: List of permissions
        """
        return list(
            cls.select().where(
                cls.permission_type == permission_type
            ).order_by(cls.name.asc())
        )
    
    @classmethod
    def get_hierarchy(cls, root_permission_id: str = None) -> List['Permission']:
        """
        Get permission hierarchy.
        
        Args:
            root_permission_id (str, optional): Root permission ID
            
        Returns:
            List[Permission]: List of permissions in hierarchy order
        """
        if root_permission_id:
            query = cls.select().where(
                (cls.id == root_permission_id) |
                (cls.parent_permission_id == root_permission_id)
            )
        else:
            query = cls.select().where(cls.parent_permission_id.is_null())
        
        return list(query.order_by(cls.level.asc(), cls.name.asc()))
    
    def __str__(self) -> str:
        return f"Permission: {self.display_name} ({self.name})"


class RolePermission(BaseModel):
    """Role-Permission association model."""
    
    role_id = CharField(max_length=36, index=True)
    permission_id = CharField(max_length=36, index=True)
    
    # Grant information
    granted_by = CharField(max_length=36, index=True)
    granted_at = DateTimeField(default=datetime.now)
    
    # Permission constraints
    conditions = JSONField(default=dict)  # Additional conditions for this grant
    expires_at = DateTimeField(null=True, index=True)  # Permission expiration
    
    # Status
    is_active = BooleanField(default=True, index=True)
    
    class Meta:
        table_name = 'role_permission'
        indexes = (
            (('role_id', 'permission_id'), True),  # Unique role-permission pair
            (('role_id', 'is_active'), False),
            (('expires_at', 'is_active'), False),
        )
    
    @property
    def role(self):
        """Get associated role."""
        from backend.models.user import UserRole
        try:
            return UserRole.get_by_id(self.role_id)
        except UserRole.DoesNotExist:
            return None
    
    @property
    def permission(self) -> Optional[Permission]:
        """Get associated permission."""
        try:
            return Permission.get_by_id(self.permission_id)
        except Permission.DoesNotExist:
            return None
    
    @property
    def granter(self):
        """Get user who granted this permission."""
        from backend.models.user import User
        try:
            return User.get_by_id(self.granted_by)
        except User.DoesNotExist:
            return None
    
    @property
    def is_expired(self) -> bool:
        """Check if permission grant is expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if permission grant is valid."""
        return self.is_active and not self.is_expired
    
    def revoke(self, revoked_by: str = None) -> None:
        """
        Revoke the permission grant.
        
        Args:
            revoked_by (str, optional): User ID who revoked the permission
        """
        self.is_active = False
        
        if revoked_by:
            if not isinstance(self.conditions, dict):
                self.conditions = {}
            self.conditions['revoked_by'] = revoked_by
            self.conditions['revoked_at'] = datetime.now().isoformat()
        
        self.save()
    
    @classmethod
    def grant_permission(cls, 
                        role_id: str, 
                        permission_id: str, 
                        granted_by: str,
                        expires_at: datetime = None,
                        conditions: Dict = None) -> 'RolePermission':
        """
        Grant permission to role.
        
        Args:
            role_id (str): Role ID
            permission_id (str): Permission ID
            granted_by (str): User ID who grants the permission
            expires_at (datetime, optional): Permission expiration
            conditions (Dict, optional): Additional conditions
            
        Returns:
            RolePermission: Created role permission instance
        """
        # Check if permission already exists
        existing = cls.select().where(
            (cls.role_id == role_id) &
            (cls.permission_id == permission_id)
        ).first()
        
        if existing:
            # Update existing grant
            existing.is_active = True
            existing.granted_by = granted_by
            existing.granted_at = datetime.now()
            existing.expires_at = expires_at
            existing.conditions = conditions or {}
            existing.save()
            return existing
        else:
            # Create new grant
            return cls.create(
                role_id=role_id,
                permission_id=permission_id,
                granted_by=granted_by,
                expires_at=expires_at,
                conditions=conditions or {}
            )
    
    @classmethod
    def get_role_permissions(cls, role_id: str, include_expired: bool = False) -> List['RolePermission']:
        """
        Get all permissions for a role.
        
        Args:
            role_id (str): Role ID
            include_expired (bool): Whether to include expired permissions
            
        Returns:
            List[RolePermission]: List of role permissions
        """
        query = cls.select().where(cls.role_id == role_id)
        
        if not include_expired:
            now = datetime.now()
            query = query.where(
                (cls.is_active == True) &
                ((cls.expires_at.is_null()) | (cls.expires_at > now))
            )
        
        return list(query.order_by(cls.granted_at.desc()))
    
    @classmethod
    def cleanup_expired(cls) -> int:
        """
        Clean up expired permission grants.
        
        Returns:
            int: Number of cleaned up grants
        """
        now = datetime.now()
        
        expired_grants = cls.select().where(
            (cls.expires_at < now) &
            (cls.is_active == True)
        )
        
        count = expired_grants.count()
        
        # Deactivate expired grants
        cls.update(is_active=False).where(
            (cls.expires_at < now) &
            (cls.is_active == True)
        ).execute()
        
        return count
    
    def __str__(self) -> str:
        return f"RolePermission: {self.role_id} -> {self.permission_id}"


class UserPermission(BaseModel):
    """User-specific permission model for direct user permissions."""
    
    user_id = CharField(max_length=36, index=True)
    permission_id = CharField(max_length=36, index=True)
    
    # Grant information
    granted_by = CharField(max_length=36, index=True)
    granted_at = DateTimeField(default=datetime.now)
    
    # Permission scope
    resource_type = CharField(max_length=50, null=True, index=True)  # e.g., 'document', 'task'
    resource_id = CharField(max_length=36, null=True, index=True)  # Specific resource ID
    
    # Permission constraints
    conditions = JSONField(default=dict)
    expires_at = DateTimeField(null=True, index=True)
    
    # Status
    is_active = BooleanField(default=True, index=True)
    
    class Meta:
        table_name = 'user_permission'
        indexes = (
            (('user_id', 'permission_id', 'resource_id'), True),  # Unique user-permission-resource
            (('user_id', 'resource_type'), False),
            (('expires_at', 'is_active'), False),
        )
    
    @property
    def user(self):
        """Get associated user."""
        from backend.models.user import User
        try:
            return User.get_by_id(self.user_id)
        except User.DoesNotExist:
            return None
    
    @property
    def permission(self) -> Optional[Permission]:
        """Get associated permission."""
        try:
            return Permission.get_by_id(self.permission_id)
        except Permission.DoesNotExist:
            return None
    
    @property
    def granter(self):
        """Get user who granted this permission."""
        from backend.models.user import User
        try:
            return User.get_by_id(self.granted_by)
        except User.DoesNotExist:
            return None
    
    @property
    def is_expired(self) -> bool:
        """Check if permission grant is expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if permission grant is valid."""
        return self.is_active and not self.is_expired
    
    def revoke(self, revoked_by: str = None) -> None:
        """
        Revoke the permission grant.
        
        Args:
            revoked_by (str, optional): User ID who revoked the permission
        """
        self.is_active = False
        
        if revoked_by:
            if not isinstance(self.conditions, dict):
                self.conditions = {}
            self.conditions['revoked_by'] = revoked_by
            self.conditions['revoked_at'] = datetime.now().isoformat()
        
        self.save()
    
    @classmethod
    def grant_permission(cls,
                        user_id: str,
                        permission_id: str,
                        granted_by: str,
                        resource_type: str = None,
                        resource_id: str = None,
                        expires_at: datetime = None,
                        conditions: Dict = None) -> 'UserPermission':
        """
        Grant permission to user.
        
        Args:
            user_id (str): User ID
            permission_id (str): Permission ID
            granted_by (str): User ID who grants the permission
            resource_type (str, optional): Resource type
            resource_id (str, optional): Resource ID
            expires_at (datetime, optional): Permission expiration
            conditions (Dict, optional): Additional conditions
            
        Returns:
            UserPermission: Created user permission instance
        """
        # Check if permission already exists
        existing = cls.select().where(
            (cls.user_id == user_id) &
            (cls.permission_id == permission_id) &
            (cls.resource_id == resource_id)
        ).first()
        
        if existing:
            # Update existing grant
            existing.is_active = True
            existing.granted_by = granted_by
            existing.granted_at = datetime.now()
            existing.resource_type = resource_type
            existing.expires_at = expires_at
            existing.conditions = conditions or {}
            existing.save()
            return existing
        else:
            # Create new grant
            return cls.create(
                user_id=user_id,
                permission_id=permission_id,
                granted_by=granted_by,
                resource_type=resource_type,
                resource_id=resource_id,
                expires_at=expires_at,
                conditions=conditions or {}
            )
    
    @classmethod
    def get_user_permissions(cls, 
                           user_id: str, 
                           resource_type: str = None,
                           resource_id: str = None,
                           include_expired: bool = False) -> List['UserPermission']:
        """
        Get permissions for a user.
        
        Args:
            user_id (str): User ID
            resource_type (str, optional): Filter by resource type
            resource_id (str, optional): Filter by resource ID
            include_expired (bool): Whether to include expired permissions
            
        Returns:
            List[UserPermission]: List of user permissions
        """
        query = cls.select().where(cls.user_id == user_id)
        
        if resource_type:
            query = query.where(cls.resource_type == resource_type)
        
        if resource_id:
            query = query.where(cls.resource_id == resource_id)
        
        if not include_expired:
            now = datetime.now()
            query = query.where(
                (cls.is_active == True) &
                ((cls.expires_at.is_null()) | (cls.expires_at > now))
            )
        
        return list(query.order_by(cls.granted_at.desc()))
    
    def __str__(self) -> str:
        return f"UserPermission: {self.user_id} -> {self.permission_id}"


class AccessLog(BaseModel):
    """Access log model for tracking permission usage and access attempts."""
    
    # Access information
    user_id = CharField(max_length=36, index=True)
    permission_name = CharField(max_length=100, index=True)
    resource_type = CharField(max_length=50, null=True, index=True)
    resource_id = CharField(max_length=36, null=True, index=True)
    
    # Access result
    access_granted = BooleanField(index=True)
    access_reason = CharField(max_length=255, null=True)  # Reason for grant/deny
    
    # Request information
    ip_address = CharField(max_length=45, null=True)
    user_agent = TextField(null=True)
    request_method = CharField(max_length=10, null=True)
    request_path = CharField(max_length=500, null=True)
    
    # Context information
    session_id = CharField(max_length=255, null=True, index=True)
    api_key_used = BooleanField(default=False)
    
    # Metadata
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'access_log'
        indexes = (
            (('user_id', 'created_at'), False),
            (('permission_name', 'access_granted'), False),
            (('resource_type', 'resource_id'), False),
            (('ip_address', 'created_at'), False),
        )
    
    @property
    def user(self):
        """Get associated user."""
        from backend.models.user import User
        try:
            return User.get_by_id(self.user_id)
        except User.DoesNotExist:
            return None
    
    @classmethod
    def log_access(cls,
                  user_id: str,
                  permission_name: str,
                  access_granted: bool,
                  resource_type: str = None,
                  resource_id: str = None,
                  access_reason: str = None,
                  ip_address: str = None,
                  user_agent: str = None,
                  request_method: str = None,
                  request_path: str = None,
                  session_id: str = None,
                  api_key_used: bool = False,
                  metadata: Dict = None) -> 'AccessLog':
        """
        Log an access attempt.
        
        Args:
            user_id (str): User ID
            permission_name (str): Permission name
            access_granted (bool): Whether access was granted
            resource_type (str, optional): Resource type
            resource_id (str, optional): Resource ID
            access_reason (str, optional): Reason for grant/deny
            ip_address (str, optional): IP address
            user_agent (str, optional): User agent
            request_method (str, optional): HTTP method
            request_path (str, optional): Request path
            session_id (str, optional): Session ID
            api_key_used (bool): Whether API key was used
            metadata (Dict, optional): Additional metadata
            
        Returns:
            AccessLog: Created access log instance
        """
        return cls.create(
            user_id=user_id,
            permission_name=permission_name,
            access_granted=access_granted,
            resource_type=resource_type,
            resource_id=resource_id,
            access_reason=access_reason,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            session_id=session_id,
            api_key_used=api_key_used,
            metadata=metadata or {}
        )
    
    @classmethod
    def get_user_access_logs(cls, 
                           user_id: str, 
                           days: int = 30,
                           access_granted: bool = None) -> List['AccessLog']:
        """
        Get access logs for a user.
        
        Args:
            user_id (str): User ID
            days (int): Number of days to look back
            access_granted (bool, optional): Filter by access result
            
        Returns:
            List[AccessLog]: List of access logs
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = cls.select().where(
            (cls.user_id == user_id) &
            (cls.created_at >= cutoff_date)
        )
        
        if access_granted is not None:
            query = query.where(cls.access_granted == access_granted)
        
        return list(query.order_by(cls.created_at.desc()))
    
    @classmethod
    def get_permission_usage_stats(cls, 
                                 permission_name: str, 
                                 days: int = 30) -> Dict[str, Any]:
        """
        Get usage statistics for a permission.
        
        Args:
            permission_name (str): Permission name
            days (int): Number of days to analyze
            
        Returns:
            Dict[str, Any]: Usage statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        logs = cls.select().where(
            (cls.permission_name == permission_name) &
            (cls.created_at >= cutoff_date)
        )
        
        total_attempts = logs.count()
        granted_attempts = logs.where(cls.access_granted == True).count()
        denied_attempts = total_attempts - granted_attempts
        
        unique_users = len(set(log.user_id for log in logs))
        
        return {
            'permission_name': permission_name,
            'total_attempts': total_attempts,
            'granted_attempts': granted_attempts,
            'denied_attempts': denied_attempts,
            'success_rate': (granted_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            'unique_users': unique_users,
            'period_days': days
        }
    
    @classmethod
    def cleanup_old_logs(cls, days: int = 90) -> int:
        """
        Clean up old access logs.
        
        Args:
            days (int): Number of days to keep logs
            
        Returns:
            int: Number of cleaned up logs
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        old_logs = cls.select().where(cls.created_at < cutoff_date)
        count = old_logs.count()
        
        # Delete old logs
        cls.delete().where(cls.created_at < cutoff_date).execute()
        
        return count
    
    def __str__(self) -> str:
        status = "GRANTED" if self.access_granted else "DENIED"
        return f"AccessLog: {self.user_id} -> {self.permission_name} ({status})"