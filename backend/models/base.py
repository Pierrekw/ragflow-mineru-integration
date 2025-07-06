#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base model classes for Ragflow-MinerU Integration

This module contains base model classes with common functionality.
"""

import uuid
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model

from backend.config.database import get_db

# Type variable for model classes
ModelType = TypeVar('ModelType', bound='BaseModel')


class UUIDField(CharField):
    """Custom UUID field that automatically generates UUIDs."""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 36)
        kwargs.setdefault('unique', True)
        kwargs.setdefault('default', self.generate_uuid)
        super().__init__(*args, **kwargs)
    
    @staticmethod
    def generate_uuid():
        """Generate a new UUID string."""
        return str(uuid.uuid4())


class JSONField(TextField):
    """Custom JSON field that automatically serializes/deserializes JSON data."""
    
    def db_value(self, value):
        """Convert Python object to database value."""
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False, default=str)
    
    def python_value(self, value):
        """Convert database value to Python object."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value


class BaseModel(Model):
    """Base model class with common fields and methods."""
    
    id = UUIDField(primary_key=True)
    created_at = DateTimeField(default=datetime.now, index=True)
    updated_at = DateTimeField(default=datetime.now, index=True)
    
    class Meta:
        database = get_db()
    
    def save(self, *args, **kwargs):
        """Override save to update the updated_at field."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def to_dict(self, exclude: Optional[List[str]] = None, include_foreign_keys: bool = False) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Args:
            exclude (List[str], optional): Fields to exclude from the dictionary
            include_foreign_keys (bool): Whether to include foreign key relationships
            
        Returns:
            Dict[str, Any]: Model data as dictionary
        """
        data = model_to_dict(
            self, 
            recurse=include_foreign_keys,
            exclude=exclude or []
        )
        
        # Convert datetime objects to ISO format strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls: Type[ModelType], data: Dict[str, Any]) -> ModelType:
        """
        Create model instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Data dictionary
            
        Returns:
            ModelType: Model instance
        """
        # Convert ISO format strings back to datetime objects
        for key, value in data.items():
            if isinstance(value, str) and key.endswith('_at'):
                try:
                    data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
        
        return dict_to_model(cls, data)
    
    @classmethod
    def get_by_id(cls: Type[ModelType], model_id: str) -> Optional[ModelType]:
        """
        Get model instance by ID.
        
        Args:
            model_id (str): Model ID
            
        Returns:
            ModelType: Model instance or None if not found
        """
        try:
            return cls.get(cls.id == model_id)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_or_create_by_id(cls: Type[ModelType], model_id: str, **defaults) -> tuple[ModelType, bool]:
        """
        Get or create model instance by ID.
        
        Args:
            model_id (str): Model ID
            **defaults: Default values for creation
            
        Returns:
            tuple[ModelType, bool]: (instance, created)
        """
        try:
            instance = cls.get(cls.id == model_id)
            return instance, False
        except cls.DoesNotExist:
            defaults['id'] = model_id
            instance = cls.create(**defaults)
            return instance, True
    
    @classmethod
    def bulk_create(cls: Type[ModelType], data_list: List[Dict[str, Any]], batch_size: int = 100) -> List[ModelType]:
        """
        Bulk create model instances.
        
        Args:
            data_list (List[Dict[str, Any]]): List of data dictionaries
            batch_size (int): Batch size for bulk operations
            
        Returns:
            List[ModelType]: Created model instances
        """
        instances = []
        
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            batch_instances = []
            
            for data in batch:
                if 'id' not in data:
                    data['id'] = str(uuid.uuid4())
                if 'created_at' not in data:
                    data['created_at'] = datetime.now()
                if 'updated_at' not in data:
                    data['updated_at'] = datetime.now()
                
                batch_instances.append(cls(**data))
            
            cls.bulk_create(batch_instances)
            instances.extend(batch_instances)
        
        return instances
    
    @classmethod
    def paginate_query(cls, query, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Paginate query results.
        
        Args:
            query: Peewee query object
            page (int): Page number (1-based)
            per_page (int): Items per page
            
        Returns:
            Dict[str, Any]: Pagination result with items, total, page info
        """
        total = query.count()
        
        # Calculate pagination
        offset = (page - 1) * per_page
        items = list(query.offset(offset).limit(per_page))
        
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_page': page - 1 if has_prev else None,
            'next_page': page + 1 if has_next else None
        }
    
    @classmethod
    def search(cls, query_text: str, fields: List[str], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Search model instances by text in specified fields.
        
        Args:
            query_text (str): Search query text
            fields (List[str]): Fields to search in
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            Dict[str, Any]: Search results with pagination
        """
        if not query_text.strip():
            return cls.paginate_query(cls.select(), page, per_page)
        
        # Build search conditions
        conditions = []
        for field_name in fields:
            if hasattr(cls, field_name):
                field = getattr(cls, field_name)
                conditions.append(field.contains(query_text))
        
        if not conditions:
            return cls.paginate_query(cls.select(), page, per_page)
        
        # Combine conditions with OR
        search_condition = conditions[0]
        for condition in conditions[1:]:
            search_condition = search_condition | condition
        
        query = cls.select().where(search_condition)
        return cls.paginate_query(query, page, per_page)
    
    def refresh(self) -> None:
        """
        Refresh model instance from database.
        """
        fresh_instance = self.__class__.get_by_id(self.id)
        if fresh_instance:
            for field_name in self._meta.fields:
                setattr(self, field_name, getattr(fresh_instance, field_name))
    
    def soft_delete(self) -> None:
        """
        Soft delete the model instance (if deleted_at field exists).
        """
        if hasattr(self, 'deleted_at'):
            self.deleted_at = datetime.now()
            self.save()
        else:
            raise AttributeError(f"{self.__class__.__name__} does not support soft delete")
    
    def restore(self) -> None:
        """
        Restore soft deleted model instance.
        """
        if hasattr(self, 'deleted_at'):
            self.deleted_at = None
            self.save()
        else:
            raise AttributeError(f"{self.__class__.__name__} does not support soft delete")
    
    @classmethod
    def active(cls):
        """
        Get query for active (non-deleted) instances.
        
        Returns:
            Query: Query for active instances
        """
        if hasattr(cls, 'deleted_at'):
            return cls.select().where(cls.deleted_at.is_null())
        return cls.select()
    
    @classmethod
    def deleted(cls):
        """
        Get query for deleted instances.
        
        Returns:
            Query: Query for deleted instances
        """
        if hasattr(cls, 'deleted_at'):
            return cls.select().where(cls.deleted_at.is_null(False))
        return cls.select().where(False)  # Return empty query
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        if hasattr(self, 'name'):
            return f"{self.__class__.__name__}: {self.name}"
        elif hasattr(self, 'title'):
            return f"{self.__class__.__name__}: {self.title}"
        else:
            return f"{self.__class__.__name__}: {self.id}"


class SoftDeleteModel(BaseModel):
    """Base model class with soft delete functionality."""
    
    deleted_at = DateTimeField(null=True, index=True)
    
    class Meta:
        database = get_db()
    
    def delete_instance(self, permanently: bool = False, *args, **kwargs):
        """
        Delete model instance (soft delete by default).
        
        Args:
            permanently (bool): Whether to permanently delete the instance
        """
        if permanently:
            return super().delete_instance(*args, **kwargs)
        else:
            self.soft_delete()


class TimestampMixin:
    """Mixin for models that need timestamp tracking."""
    
    created_at = DateTimeField(default=datetime.now, index=True)
    updated_at = DateTimeField(default=datetime.now, index=True)
    
    def save(self, *args, **kwargs):
        """Override save to update the updated_at field."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class UserTrackingMixin:
    """Mixin for models that need user tracking."""
    
    created_by = CharField(max_length=36, null=True, index=True)
    updated_by = CharField(max_length=36, null=True, index=True)
    
    def save(self, user_id: Optional[str] = None, *args, **kwargs):
        """
        Override save to track user changes.
        
        Args:
            user_id (str, optional): ID of the user making the change
        """
        if user_id:
            if not self.created_by:
                self.created_by = user_id
            self.updated_by = user_id
        
        return super().save(*args, **kwargs)


class StatusMixin:
    """Mixin for models that need status tracking."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('archived', 'Archived')
    ]
    
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='active', index=True)
    
    @classmethod
    def active(cls):
        """Get query for active instances."""
        return cls.select().where(cls.status == 'active')
    
    @classmethod
    def inactive(cls):
        """Get query for inactive instances."""
        return cls.select().where(cls.status == 'inactive')
    
    def activate(self):
        """Activate the instance."""
        self.status = 'active'
        self.save()
    
    def deactivate(self):
        """Deactivate the instance."""
        self.status = 'inactive'
        self.save()
    
    def archive(self):
        """Archive the instance."""
        self.status = 'archived'
        self.save()