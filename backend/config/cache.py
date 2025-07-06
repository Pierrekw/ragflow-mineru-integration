#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cache Configuration for Ragflow-MinerU Integration

This module provides Redis cache configuration and utilities.
"""

import json
import pickle
import logging
from typing import Any, Optional, Union, Dict, List
from functools import wraps
from datetime import datetime, timedelta

import redis
from flask import Flask, current_app, request, g

logger = logging.getLogger(__name__)

# Global Redis instances
redis_client = None
redis_session_client = None


class CacheConfig:
    """
    Cache configuration class.
    """
    
    def __init__(self, app: Flask = None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize cache with Flask app.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Set default cache configuration
        app.config.setdefault('CACHE_TYPE', 'redis')
        app.config.setdefault('CACHE_DEFAULT_TIMEOUT', 300)  # 5 minutes
        app.config.setdefault('CACHE_KEY_PREFIX', 'ragflow_mineru:')
        
        # Redis configuration
        app.config.setdefault('REDIS_HOST', 'localhost')
        app.config.setdefault('REDIS_PORT', 6379)
        app.config.setdefault('REDIS_DB', 0)
        app.config.setdefault('REDIS_PASSWORD', None)
        app.config.setdefault('REDIS_DECODE_RESPONSES', True)
        app.config.setdefault('REDIS_SOCKET_TIMEOUT', 5)
        app.config.setdefault('REDIS_CONNECTION_POOL_MAX_CONNECTIONS', 50)
        
        # Session Redis configuration (separate database)
        app.config.setdefault('REDIS_SESSION_DB', 1)
        
        # Initialize Redis clients
        self._init_redis_clients(app)
        
        # Register teardown handler
        app.teardown_appcontext(self._teardown_redis)
    
    def _init_redis_clients(self, app: Flask):
        """
        Initialize Redis clients.
        
        Args:
            app: Flask application instance
        """
        global redis_client, redis_session_client
        
        try:
            # Main Redis client for caching
            redis_client = redis.Redis(
                host=app.config['REDIS_HOST'],
                port=app.config['REDIS_PORT'],
                db=app.config['REDIS_DB'],
                password=app.config['REDIS_PASSWORD'],
                decode_responses=app.config['REDIS_DECODE_RESPONSES'],
                socket_timeout=app.config['REDIS_SOCKET_TIMEOUT'],
                max_connections=app.config['REDIS_CONNECTION_POOL_MAX_CONNECTIONS']
            )
            
            # Session Redis client (separate database)
            redis_session_client = redis.Redis(
                host=app.config['REDIS_HOST'],
                port=app.config['REDIS_PORT'],
                db=app.config['REDIS_SESSION_DB'],
                password=app.config['REDIS_PASSWORD'],
                decode_responses=False,  # Sessions use binary data
                socket_timeout=app.config['REDIS_SOCKET_TIMEOUT'],
                max_connections=app.config['REDIS_CONNECTION_POOL_MAX_CONNECTIONS']
            )
            
            # Test connections
            redis_client.ping()
            redis_session_client.ping()
            
            app.logger.info("Redis clients initialized successfully")
            
        except Exception as e:
            app.logger.error(f"Failed to initialize Redis clients: {e}")
            # Fallback to None (cache will be disabled)
            redis_client = None
            redis_session_client = None
    
    def _teardown_redis(self, exception):
        """
        Teardown Redis connections.
        
        Args:
            exception: Exception that occurred during request
        """
        # Redis connections are managed by connection pool
        pass


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get the main Redis client.
    
    Returns:
        Redis client instance or None if not available
    """
    return redis_client


def get_session_redis_client() -> Optional[redis.Redis]:
    """
    Get the session Redis client.
    
    Returns:
        Session Redis client instance or None if not available
    """
    return redis_session_client


class Cache:
    """
    Cache utility class.
    """
    
    def __init__(self, redis_client: redis.Redis = None, key_prefix: str = 'ragflow_mineru:'):
        self.redis_client = redis_client or get_redis_client()
        self.key_prefix = key_prefix
    
    def _make_key(self, key: str) -> str:
        """
        Create cache key with prefix.
        
        Args:
            key: Original key
            
        Returns:
            Prefixed key
        """
        return f"{self.key_prefix}{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        if not self.redis_client:
            return default
        
        try:
            cache_key = self._make_key(key)
            value = self.redis_client.get(cache_key)
            
            if value is None:
                return default
            
            # Try to deserialize JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value.encode('latin1') if isinstance(value, str) else value)
                except (pickle.PickleError, UnicodeDecodeError):
                    return value
        
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: Expiration timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(key)
            
            # Serialize value
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, default=str)
            elif isinstance(value, (str, int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = pickle.dumps(value)
            
            # Set with timeout
            if timeout:
                return self.redis_client.setex(cache_key, timeout, serialized_value)
            else:
                return self.redis_client.set(cache_key, serialized_value)
        
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(key)
            return bool(self.redis_client.delete(cache_key))
        
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(key)
            return bool(self.redis_client.exists(cache_key))
        
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Key pattern (supports wildcards)
            
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            cache_pattern = self._make_key(pattern)
            keys = self.redis_client.keys(cache_pattern)
            
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        
        except Exception as e:
            logger.error(f"Cache clear pattern error for pattern '{pattern}': {e}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment
            
        Returns:
            New value or None if error
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._make_key(key)
            return self.redis_client.incrby(cache_key, amount)
        
        except Exception as e:
            logger.error(f"Cache increment error for key '{key}': {e}")
            return None
    
    def expire(self, key: str, timeout: int) -> bool:
        """
        Set expiration timeout for key.
        
        Args:
            key: Cache key
            timeout: Timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(key)
            return bool(self.redis_client.expire(cache_key, timeout))
        
        except Exception as e:
            logger.error(f"Cache expire error for key '{key}': {e}")
            return False


# Global cache instance
cache = Cache()


def cached(timeout: int = 300, key_func: Optional[callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        timeout: Cache timeout in seconds
        key_func: Function to generate cache key
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                if args:
                    key_parts.extend([str(arg) for arg in args])
                if kwargs:
                    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


def cache_user_data(user_id: int, data: Dict, timeout: int = 3600):
    """
    Cache user-specific data.
    
    Args:
        user_id: User ID
        data: Data to cache
        timeout: Cache timeout in seconds
    """
    cache_key = f"user:{user_id}:data"
    cache.set(cache_key, data, timeout)


def get_user_data(user_id: int) -> Optional[Dict]:
    """
    Get cached user data.
    
    Args:
        user_id: User ID
        
    Returns:
        Cached user data or None
    """
    cache_key = f"user:{user_id}:data"
    return cache.get(cache_key)


def clear_user_cache(user_id: int):
    """
    Clear all cached data for a user.
    
    Args:
        user_id: User ID
    """
    pattern = f"user:{user_id}:*"
    cache.clear_pattern(pattern)


def cache_document_data(doc_id: int, data: Dict, timeout: int = 1800):
    """
    Cache document-specific data.
    
    Args:
        doc_id: Document ID
        data: Data to cache
        timeout: Cache timeout in seconds
    """
    cache_key = f"document:{doc_id}:data"
    cache.set(cache_key, data, timeout)


def get_document_data(doc_id: int) -> Optional[Dict]:
    """
    Get cached document data.
    
    Args:
        doc_id: Document ID
        
    Returns:
        Cached document data or None
    """
    cache_key = f"document:{doc_id}:data"
    return cache.get(cache_key)


def clear_document_cache(doc_id: int):
    """
    Clear all cached data for a document.
    
    Args:
        doc_id: Document ID
    """
    pattern = f"document:{doc_id}:*"
    cache.clear_pattern(pattern)


def cache_task_result(task_id: str, result: Dict, timeout: int = 7200):
    """
    Cache task result.
    
    Args:
        task_id: Task ID
        result: Task result
        timeout: Cache timeout in seconds
    """
    cache_key = f"task:{task_id}:result"
    cache.set(cache_key, result, timeout)


def get_task_result(task_id: str) -> Optional[Dict]:
    """
    Get cached task result.
    
    Args:
        task_id: Task ID
        
    Returns:
        Cached task result or None
    """
    cache_key = f"task:{task_id}:result"
    return cache.get(cache_key)


def clear_task_cache(task_id: str):
    """
    Clear all cached data for a task.
    
    Args:
        task_id: Task ID
    """
    pattern = f"task:{task_id}:*"
    cache.clear_pattern(pattern)


def get_cache_stats() -> Dict:
    """
    Get cache statistics.
    
    Returns:
        Cache statistics
    """
    if not redis_client:
        return {'status': 'disabled'}
    
    try:
        info = redis_client.info()
        return {
            'status': 'connected',
            'used_memory': info.get('used_memory_human', 'N/A'),
            'connected_clients': info.get('connected_clients', 0),
            'total_commands_processed': info.get('total_commands_processed', 0),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'uptime_in_seconds': info.get('uptime_in_seconds', 0)
        }
    
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {'status': 'error', 'error': str(e)}


def health_check() -> bool:
    """
    Check cache health.
    
    Returns:
        True if cache is healthy, False otherwise
    """
    if not redis_client:
        return False
    
    try:
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return False