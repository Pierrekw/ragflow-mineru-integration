#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User models for Ragflow-MinerU Integration

This module contains user-related database models.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from peewee import *
import bcrypt

from backend.models.base import BaseModel, SoftDeleteModel, JSONField, StatusMixin


class UserRole(BaseModel, StatusMixin):
    """User role model for role-based access control."""
    
    name = CharField(max_length=50, unique=True, index=True)
    display_name = CharField(max_length=100)
    description = TextField(null=True)
    permissions = JSONField(default=list)  # List of permission strings
    is_system = BooleanField(default=False)  # System roles cannot be deleted
    priority = IntegerField(default=0, index=True)  # Higher priority = more permissions
    
    class Meta:
        table_name = 'user_role'
        indexes = (
            (('name',), True),  # Unique index on name
            (('priority', 'status'), False),  # Composite index
        )
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if role has a specific permission.
        
        Args:
            permission (str): Permission string (e.g., 'user.create')
            
        Returns:
            bool: True if role has permission
        """
        if not isinstance(self.permissions, list):
            return False
        
        # Check exact permission
        if permission in self.permissions:
            return True
        
        # Check wildcard permissions
        for perm in self.permissions:
            if perm.endswith('.*'):
                prefix = perm[:-2]
                if permission.startswith(prefix + '.'):
                    return True
            elif perm == '*':
                return True
        
        return False
    
    def add_permission(self, permission: str) -> None:
        """
        Add permission to role.
        
        Args:
            permission (str): Permission string to add
        """
        if not isinstance(self.permissions, list):
            self.permissions = []
        
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.save()
    
    def remove_permission(self, permission: str) -> None:
        """
        Remove permission from role.
        
        Args:
            permission (str): Permission string to remove
        """
        if isinstance(self.permissions, list) and permission in self.permissions:
            self.permissions.remove(permission)
            self.save()
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional['UserRole']:
        """
        Get role by name.
        
        Args:
            name (str): Role name
            
        Returns:
            UserRole: Role instance or None
        """
        try:
            return cls.get(cls.name == name)
        except cls.DoesNotExist:
            return None
    
    def __str__(self) -> str:
        return f"Role: {self.display_name}"


class User(SoftDeleteModel, StatusMixin):
    """User model with authentication and profile information."""
    
    # Authentication fields
    username = CharField(max_length=50, unique=True, index=True)
    email = CharField(max_length=255, unique=True, index=True)
    password_hash = CharField(max_length=255)
    
    # Profile fields
    nickname = CharField(max_length=100, null=True)
    first_name = CharField(max_length=50, null=True)
    last_name = CharField(max_length=50, null=True)
    avatar_url = CharField(max_length=500, null=True)
    bio = TextField(null=True)
    
    # Role and permissions
    role_id = CharField(max_length=36, index=True)
    is_superuser = BooleanField(default=False)
    is_staff = BooleanField(default=False)
    
    # Account status
    is_active = BooleanField(default=True, index=True)
    is_verified = BooleanField(default=False)
    email_verified_at = DateTimeField(null=True)
    
    # Login tracking
    last_login_at = DateTimeField(null=True)
    last_login_ip = CharField(max_length=45, null=True)
    login_count = IntegerField(default=0)
    failed_login_attempts = IntegerField(default=0)
    locked_until = DateTimeField(null=True)
    
    # Settings and preferences
    settings = JSONField(default=dict)
    timezone = CharField(max_length=50, default='UTC')
    language = CharField(max_length=10, default='zh-CN')
    
    # API access
    api_key = CharField(max_length=64, null=True, unique=True)
    api_key_created_at = DateTimeField(null=True)
    
    class Meta:
        table_name = 'user'
        indexes = (
            (('email',), True),  # Unique index on email
            (('username',), True),  # Unique index on username
            (('role_id', 'is_active'), False),  # Composite index
            (('last_login_at',), False),  # Index for sorting by last login
        )
    
    def set_password(self, password: str) -> None:
        """
        Set user password with bcrypt hashing.
        
        Args:
            password (str): Plain text password
        """
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """
        Check if provided password matches stored hash.
        
        Args:
            password (str): Plain text password to check
            
        Returns:
            bool: True if password matches
        """
        if not self.password_hash:
            return False
        
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                self.password_hash.encode('utf-8')
            )
        except (ValueError, TypeError):
            return False
    
    def generate_api_key(self) -> str:
        """
        Generate a new API key for the user.
        
        Returns:
            str: Generated API key
        """
        self.api_key = secrets.token_urlsafe(32)
        self.api_key_created_at = datetime.now()
        self.save()
        return self.api_key
    
    def revoke_api_key(self) -> None:
        """
        Revoke the user's API key.
        """
        self.api_key = None
        self.api_key_created_at = None
        self.save()
    
    @property
    def role(self) -> Optional[UserRole]:
        """
        Get user's role.
        
        Returns:
            UserRole: User's role or None
        """
        if not self.role_id:
            return None
        
        try:
            return UserRole.get_by_id(self.role_id)
        except UserRole.DoesNotExist:
            return None
    
    @property
    def full_name(self) -> str:
        """
        Get user's full name.
        
        Returns:
            str: Full name or nickname or username
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.nickname:
            return self.nickname
        else:
            return self.username
    
    @property
    def display_name(self) -> str:
        """
        Get user's display name.
        
        Returns:
            str: Display name (nickname or full name or username)
        """
        return self.nickname or self.full_name or self.username
    
    @property
    def is_locked(self) -> bool:
        """
        Check if user account is locked.
        
        Returns:
            bool: True if account is locked
        """
        if not self.locked_until:
            return False
        return datetime.now() < self.locked_until
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            permission (str): Permission string
            
        Returns:
            bool: True if user has permission
        """
        # Superuser has all permissions
        if self.is_superuser:
            return True
        
        # Check role permissions
        role = self.role
        if role:
            return role.has_permission(permission)
        
        return False
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """
        Lock user account for specified duration.
        
        Args:
            duration_minutes (int): Lock duration in minutes
        """
        self.locked_until = datetime.now() + timedelta(minutes=duration_minutes)
        self.save()
    
    def unlock_account(self) -> None:
        """
        Unlock user account.
        """
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save()
    
    def record_login(self, ip_address: Optional[str] = None) -> None:
        """
        Record successful login.
        
        Args:
            ip_address (str, optional): IP address of login
        """
        self.last_login_at = datetime.now()
        self.last_login_ip = ip_address
        self.login_count += 1
        self.failed_login_attempts = 0
        self.save()
    
    def record_failed_login(self, max_attempts: int = 5) -> None:
        """
        Record failed login attempt.
        
        Args:
            max_attempts (int): Maximum failed attempts before locking
        """
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= max_attempts:
            self.lock_account()
        
        self.save()
    
    def update_setting(self, key: str, value: Any) -> None:
        """
        Update user setting.
        
        Args:
            key (str): Setting key
            value (Any): Setting value
        """
        if not isinstance(self.settings, dict):
            self.settings = {}
        
        self.settings[key] = value
        self.save()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get user setting.
        
        Args:
            key (str): Setting key
            default (Any): Default value if key not found
            
        Returns:
            Any: Setting value or default
        """
        if not isinstance(self.settings, dict):
            return default
        
        return self.settings.get(key, default)
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        """
        Get user by email address.
        
        Args:
            email (str): Email address
            
        Returns:
            User: User instance or None
        """
        try:
            return cls.get(cls.email == email.lower())
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """
        Get user by username.
        
        Args:
            username (str): Username
            
        Returns:
            User: User instance or None
        """
        try:
            return cls.get(cls.username == username.lower())
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_by_api_key(cls, api_key: str) -> Optional['User']:
        """
        Get user by API key.
        
        Args:
            api_key (str): API key
            
        Returns:
            User: User instance or None
        """
        try:
            return cls.get(cls.api_key == api_key)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def create_user(cls, username: str, email: str, password: str, **kwargs) -> 'User':
        """
        Create a new user with proper validation.
        
        Args:
            username (str): Username
            email (str): Email address
            password (str): Plain text password
            **kwargs: Additional user fields
            
        Returns:
            User: Created user instance
        """
        # Normalize email and username
        email = email.lower().strip()
        username = username.lower().strip()
        
        # Create user instance
        user = cls(
            username=username,
            email=email,
            **kwargs
        )
        
        # Set password
        user.set_password(password)
        
        # Save user
        user.save()
        
        return user
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert user to dictionary.
        
        Args:
            include_sensitive (bool): Whether to include sensitive fields
            
        Returns:
            Dict[str, Any]: User data dictionary
        """
        exclude_fields = ['password_hash']
        if not include_sensitive:
            exclude_fields.extend(['api_key', 'failed_login_attempts', 'locked_until'])
        
        data = super().to_dict(exclude=exclude_fields)
        
        # Add computed fields
        data['full_name'] = self.full_name
        data['display_name'] = self.display_name
        data['is_locked'] = self.is_locked
        
        # Add role information
        if self.role:
            data['role'] = {
                'id': self.role.id,
                'name': self.role.name,
                'display_name': self.role.display_name
            }
        
        return data
    
    def __str__(self) -> str:
        return f"User: {self.display_name} ({self.email})"


class UserSession(BaseModel):
    """User session model for tracking active sessions."""
    
    user_id = CharField(max_length=36, index=True)
    session_token = CharField(max_length=255, unique=True, index=True)
    refresh_token = CharField(max_length=255, unique=True, index=True, null=True)
    
    # Session metadata
    ip_address = CharField(max_length=45, null=True)
    user_agent = TextField(null=True)
    device_info = JSONField(default=dict)
    
    # Session timing
    expires_at = DateTimeField(index=True)
    last_activity_at = DateTimeField(default=datetime.now, index=True)
    
    # Session status
    is_active = BooleanField(default=True, index=True)
    logout_reason = CharField(max_length=50, null=True)  # 'manual', 'expired', 'revoked'
    
    class Meta:
        table_name = 'user_session'
        indexes = (
            (('user_id', 'is_active'), False),
            (('session_token',), True),
            (('expires_at', 'is_active'), False),
        )
    
    @property
    def user(self) -> Optional[User]:
        """
        Get session user.
        
        Returns:
            User: User instance or None
        """
        try:
            return User.get_by_id(self.user_id)
        except User.DoesNotExist:
            return None
    
    @property
    def is_expired(self) -> bool:
        """
        Check if session is expired.
        
        Returns:
            bool: True if session is expired
        """
        return datetime.now() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """
        Check if session is valid (active and not expired).
        
        Returns:
            bool: True if session is valid
        """
        return self.is_active and not self.is_expired
    
    def update_activity(self) -> None:
        """
        Update last activity timestamp.
        """
        self.last_activity_at = datetime.now()
        self.save()
    
    def revoke(self, reason: str = 'revoked') -> None:
        """
        Revoke the session.
        
        Args:
            reason (str): Reason for revocation
        """
        self.is_active = False
        self.logout_reason = reason
        self.save()
    
    @classmethod
    def get_by_token(cls, session_token: str) -> Optional['UserSession']:
        """
        Get session by token.
        
        Args:
            session_token (str): Session token
            
        Returns:
            UserSession: Session instance or None
        """
        try:
            return cls.get(cls.session_token == session_token)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def create_session(cls, user: User, expires_in_hours: int = 24, **kwargs) -> 'UserSession':
        """
        Create a new user session.
        
        Args:
            user (User): User instance
            expires_in_hours (int): Session expiration in hours
            **kwargs: Additional session fields
            
        Returns:
            UserSession: Created session instance
        """
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        session = cls.create(
            user_id=user.id,
            session_token=session_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            **kwargs
        )
        
        return session
    
    @classmethod
    def cleanup_expired(cls) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            int: Number of cleaned up sessions
        """
        expired_sessions = cls.select().where(
            (cls.expires_at < datetime.now()) |
            (cls.is_active == False)
        )
        
        count = expired_sessions.count()
        
        # Update expired sessions
        cls.update(
            is_active=False,
            logout_reason='expired'
        ).where(
            cls.expires_at < datetime.now(),
            cls.is_active == True
        ).execute()
        
        return count
    
    @classmethod
    def revoke_user_sessions(cls, user_id: str, except_session_id: Optional[str] = None) -> int:
        """
        Revoke all sessions for a user.
        
        Args:
            user_id (str): User ID
            except_session_id (str, optional): Session ID to exclude from revocation
            
        Returns:
            int: Number of revoked sessions
        """
        query = cls.update(
            is_active=False,
            logout_reason='revoked'
        ).where(
            cls.user_id == user_id,
            cls.is_active == True
        )
        
        if except_session_id:
            query = query.where(cls.id != except_session_id)
        
        return query.execute()
    
    def __str__(self) -> str:
        return f"Session: {self.user_id} ({self.session_token[:8]}...)"