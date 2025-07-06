#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication Service for Ragflow-MinerU Integration

This module provides authentication and authorization services.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from flask import current_app, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    decode_token, get_jwt_identity, get_jwt
)
import jwt
from email_validator import validate_email, EmailNotValidError

from backend.models.user import User, UserRole, UserSession
from backend.models.permission import AccessLog
from backend.services.permission_service import PermissionService


class AuthenticationError(Exception):
    """Authentication related errors."""
    pass


class AuthorizationError(Exception):
    """Authorization related errors."""
    pass


class AuthService:
    """Authentication and authorization service."""
    
    def __init__(self):
        self.permission_service = PermissionService()
    
    def register_user(self, 
                     username: str, 
                     email: str, 
                     password: str,
                     first_name: str = None,
                     last_name: str = None,
                     role_name: str = 'user') -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            username (str): Username
            email (str): Email address
            password (str): Password
            first_name (str, optional): First name
            last_name (str, optional): Last name
            role_name (str): Role name (default: 'user')
            
        Returns:
            Dict[str, Any]: Registration result
            
        Raises:
            AuthenticationError: If registration fails
        """
        try:
            # Validate input
            self._validate_registration_data(username, email, password)
            
            # Check if user already exists
            if User.get_by_username(username):
                raise AuthenticationError(f"Username '{username}' already exists")
            
            if User.get_by_email(email):
                raise AuthenticationError(f"Email '{email}' already registered")
            
            # Get role
            role = UserRole.get_by_name(role_name)
            if not role:
                raise AuthenticationError(f"Role '{role_name}' not found")
            
            # Create user
            user = User.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role_id=role.id
            )
            
            # Log registration
            current_app.logger.info(f"User registered: {username} ({email})")
            
            return {
                'success': True,
                'message': 'User registered successfully',
                'user': user.to_dict()
            }
            
        except Exception as e:
            current_app.logger.error(f"Registration failed: {str(e)}")
            raise AuthenticationError(str(e))
    
    def authenticate_user(self, 
                         identifier: str, 
                         password: str,
                         ip_address: str = None,
                         user_agent: str = None) -> Dict[str, Any]:
        """
        Authenticate user with username/email and password.
        
        Args:
            identifier (str): Username or email
            password (str): Password
            ip_address (str, optional): IP address
            user_agent (str, optional): User agent
            
        Returns:
            Dict[str, Any]: Authentication result with tokens
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Find user by username or email
            user = self._find_user_by_identifier(identifier)
            
            if not user:
                raise AuthenticationError("Invalid credentials")
            
            # Check if account is active
            if not user.is_active:
                raise AuthenticationError("Account is deactivated")
            
            # Check if account is locked
            if user.is_locked:
                raise AuthenticationError("Account is temporarily locked")
            
            # Verify password
            if not user.check_password(password):
                user.record_failed_login()
                raise AuthenticationError("Invalid credentials")
            
            # Record successful login
            user.record_login(ip_address)
            
            # Create tokens
            tokens = self._create_user_tokens(user)
            
            # Create session
            session = UserSession.create_session(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Log successful authentication
            AccessLog.log_access(
                user_id=user.id,
                permission_name='auth.login',
                access_granted=True,
                access_reason='Valid credentials',
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session.id
            )
            
            current_app.logger.info(f"User authenticated: {user.username}")
            
            return {
                'success': True,
                'message': 'Authentication successful',
                'user': user.to_dict(),
                'tokens': tokens,
                'session': {
                    'id': session.id,
                    'expires_at': session.expires_at.isoformat()
                }
            }
            
        except AuthenticationError:
            # Log failed authentication
            if 'user' in locals() and user:
                AccessLog.log_access(
                    user_id=user.id,
                    permission_name='auth.login',
                    access_granted=False,
                    access_reason='Invalid credentials',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            raise
        except Exception as e:
            current_app.logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationError("Authentication failed")
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token (str): Refresh token
            
        Returns:
            Dict[str, Any]: New tokens
            
        Raises:
            AuthenticationError: If token refresh fails
        """
        try:
            # Decode refresh token
            decoded_token = decode_token(refresh_token)
            user_id = decoded_token['sub']
            
            # Get user
            user = User.get_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("Invalid refresh token")
            
            # Find session by refresh token
            session = UserSession.select().where(
                (UserSession.user_id == user_id) &
                (UserSession.refresh_token == refresh_token) &
                (UserSession.is_active == True)
            ).first()
            
            if not session or not session.is_valid:
                raise AuthenticationError("Invalid or expired refresh token")
            
            # Create new tokens
            tokens = self._create_user_tokens(user)
            
            # Update session with new refresh token
            session.refresh_token = tokens['refresh_token']
            session.update_activity()
            
            current_app.logger.info(f"Token refreshed for user: {user.username}")
            
            return {
                'success': True,
                'message': 'Token refreshed successfully',
                'tokens': tokens
            }
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Refresh token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid refresh token")
        except Exception as e:
            current_app.logger.error(f"Token refresh error: {str(e)}")
            raise AuthenticationError("Token refresh failed")
    
    def logout_user(self, session_token: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Logout user and invalidate session.
        
        Args:
            session_token (str, optional): Session token
            user_id (str, optional): User ID (for logout all sessions)
            
        Returns:
            Dict[str, Any]: Logout result
        """
        try:
            if session_token:
                # Logout specific session
                session = UserSession.get_by_token(session_token)
                if session:
                    session.revoke('manual')
                    current_app.logger.info(f"Session logged out: {session.id}")
            
            elif user_id:
                # Logout all user sessions
                count = UserSession.revoke_user_sessions(user_id)
                current_app.logger.info(f"All sessions logged out for user: {user_id} ({count} sessions)")
            
            return {
                'success': True,
                'message': 'Logout successful'
            }
            
        except Exception as e:
            current_app.logger.error(f"Logout error: {str(e)}")
            return {
                'success': False,
                'message': 'Logout failed'
            }
    
    def validate_session(self, session_token: str) -> Optional[User]:
        """
        Validate session token and return user.
        
        Args:
            session_token (str): Session token
            
        Returns:
            User: User instance if session is valid, None otherwise
        """
        try:
            session = UserSession.get_by_token(session_token)
            
            if not session or not session.is_valid:
                return None
            
            # Update session activity
            session.update_activity()
            
            return session.user
            
        except Exception as e:
            current_app.logger.error(f"Session validation error: {str(e)}")
            return None
    
    def validate_api_key(self, api_key: str) -> Optional[User]:
        """
        Validate API key and return user.
        
        Args:
            api_key (str): API key
            
        Returns:
            User: User instance if API key is valid, None otherwise
        """
        try:
            user = User.get_by_api_key(api_key)
            
            if not user or not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            current_app.logger.error(f"API key validation error: {str(e)}")
            return None
    
    def change_password(self, 
                       user_id: str, 
                       current_password: str, 
                       new_password: str) -> Dict[str, Any]:
        """
        Change user password.
        
        Args:
            user_id (str): User ID
            current_password (str): Current password
            new_password (str): New password
            
        Returns:
            Dict[str, Any]: Password change result
            
        Raises:
            AuthenticationError: If password change fails
        """
        try:
            user = User.get_by_id(user_id)
            if not user:
                raise AuthenticationError("User not found")
            
            # Verify current password
            if not user.check_password(current_password):
                raise AuthenticationError("Current password is incorrect")
            
            # Validate new password
            self._validate_password(new_password)
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Revoke all existing sessions except current
            UserSession.revoke_user_sessions(user_id)
            
            current_app.logger.info(f"Password changed for user: {user.username}")
            
            return {
                'success': True,
                'message': 'Password changed successfully'
            }
            
        except Exception as e:
            current_app.logger.error(f"Password change error: {str(e)}")
            raise AuthenticationError(str(e))
    
    def reset_password_request(self, email: str) -> Dict[str, Any]:
        """
        Request password reset.
        
        Args:
            email (str): Email address
            
        Returns:
            Dict[str, Any]: Reset request result
        """
        try:
            user = User.get_by_email(email)
            if not user:
                # Don't reveal if email exists
                return {
                    'success': True,
                    'message': 'If the email exists, a reset link has been sent'
                }
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)
            
            # Store reset token in user settings
            user.update_setting('password_reset_token', reset_token)
            user.update_setting('password_reset_expires', expires_at.isoformat())
            
            # TODO: Send email with reset link
            # email_service.send_password_reset_email(user.email, reset_token)
            
            current_app.logger.info(f"Password reset requested for: {email}")
            
            return {
                'success': True,
                'message': 'If the email exists, a reset link has been sent',
                'reset_token': reset_token  # Remove in production
            }
            
        except Exception as e:
            current_app.logger.error(f"Password reset request error: {str(e)}")
            return {
                'success': False,
                'message': 'Password reset request failed'
            }
    
    def reset_password(self, reset_token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset password using reset token.
        
        Args:
            reset_token (str): Reset token
            new_password (str): New password
            
        Returns:
            Dict[str, Any]: Reset result
            
        Raises:
            AuthenticationError: If password reset fails
        """
        try:
            # Find user by reset token
            users = User.select().where(
                User.settings.contains(f'"password_reset_token": "{reset_token}"')
            )
            
            user = None
            for u in users:
                if u.get_setting('password_reset_token') == reset_token:
                    user = u
                    break
            
            if not user:
                raise AuthenticationError("Invalid reset token")
            
            # Check token expiration
            expires_str = user.get_setting('password_reset_expires')
            if not expires_str:
                raise AuthenticationError("Invalid reset token")
            
            expires_at = datetime.fromisoformat(expires_str)
            if datetime.now() > expires_at:
                raise AuthenticationError("Reset token expired")
            
            # Validate new password
            self._validate_password(new_password)
            
            # Set new password
            user.set_password(new_password)
            
            # Clear reset token
            user.update_setting('password_reset_token', None)
            user.update_setting('password_reset_expires', None)
            
            # Revoke all sessions
            UserSession.revoke_user_sessions(user.id)
            
            current_app.logger.info(f"Password reset completed for: {user.username}")
            
            return {
                'success': True,
                'message': 'Password reset successfully'
            }
            
        except Exception as e:
            current_app.logger.error(f"Password reset error: {str(e)}")
            raise AuthenticationError(str(e))
    
    def verify_email(self, user_id: str, verification_token: str) -> Dict[str, Any]:
        """
        Verify user email address.
        
        Args:
            user_id (str): User ID
            verification_token (str): Verification token
            
        Returns:
            Dict[str, Any]: Verification result
        """
        try:
            user = User.get_by_id(user_id)
            if not user:
                raise AuthenticationError("User not found")
            
            # Check verification token
            stored_token = user.get_setting('email_verification_token')
            if not stored_token or stored_token != verification_token:
                raise AuthenticationError("Invalid verification token")
            
            # Mark email as verified
            user.is_verified = True
            user.email_verified_at = datetime.now()
            user.update_setting('email_verification_token', None)
            user.save()
            
            current_app.logger.info(f"Email verified for user: {user.username}")
            
            return {
                'success': True,
                'message': 'Email verified successfully'
            }
            
        except Exception as e:
            current_app.logger.error(f"Email verification error: {str(e)}")
            raise AuthenticationError(str(e))
    
    def check_permission(self, 
                        user: User, 
                        permission: str,
                        resource_type: str = None,
                        resource_id: str = None) -> bool:
        """
        Check if user has permission.
        
        Args:
            user (User): User instance
            permission (str): Permission name
            resource_type (str, optional): Resource type
            resource_id (str, optional): Resource ID
            
        Returns:
            bool: True if user has permission
        """
        try:
            return self.permission_service.check_user_permission(
                user_id=user.id,
                permission_name=permission,
                resource_type=resource_type,
                resource_id=resource_id
            )
        except Exception as e:
            current_app.logger.error(f"Permission check error: {str(e)}")
            return False
    
    def _validate_registration_data(self, username: str, email: str, password: str) -> None:
        """
        Validate registration data.
        
        Args:
            username (str): Username
            email (str): Email
            password (str): Password
            
        Raises:
            AuthenticationError: If validation fails
        """
        # Validate username
        if not username or len(username) < 3:
            raise AuthenticationError("Username must be at least 3 characters long")
        
        if len(username) > 50:
            raise AuthenticationError("Username must be less than 50 characters")
        
        # Validate email
        try:
            validate_email(email)
        except EmailNotValidError:
            raise AuthenticationError("Invalid email address")
        
        # Validate password
        self._validate_password(password)
    
    def _validate_password(self, password: str) -> None:
        """
        Validate password strength.
        
        Args:
            password (str): Password
            
        Raises:
            AuthenticationError: If password is invalid
        """
        if not password or len(password) < 8:
            raise AuthenticationError("Password must be at least 8 characters long")
        
        if len(password) > 128:
            raise AuthenticationError("Password must be less than 128 characters")
        
        # Check for at least one uppercase, lowercase, digit, and special character
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise AuthenticationError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character"
            )
    
    def _find_user_by_identifier(self, identifier: str) -> Optional[User]:
        """
        Find user by username or email.
        
        Args:
            identifier (str): Username or email
            
        Returns:
            User: User instance or None
        """
        # Try to find by email first
        if '@' in identifier:
            return User.get_by_email(identifier)
        else:
            return User.get_by_username(identifier)
    
    def _create_user_tokens(self, user: User) -> Dict[str, str]:
        """
        Create JWT tokens for user.
        
        Args:
            user (User): User instance
            
        Returns:
            Dict[str, str]: Access and refresh tokens
        """
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'username': user.username,
                'email': user.email,
                'role': user.role.name if user.role else None,
                'is_superuser': user.is_superuser
            }
        )
        
        # Create refresh token
        refresh_token = create_refresh_token(identity=user.id)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }
    
    @staticmethod
    def cleanup_expired_sessions() -> int:
        """
        Clean up expired sessions.
        
        Returns:
            int: Number of cleaned up sessions
        """
        return UserSession.cleanup_expired()