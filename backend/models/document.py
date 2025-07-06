#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document models for Ragflow-MinerU Integration

This module contains document-related database models.
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from peewee import *

from backend.models.base import BaseModel, SoftDeleteModel, JSONField, StatusMixin


class DocumentType(Enum):
    """Document type enumeration."""
    PDF = 'pdf'
    DOCX = 'docx'
    DOC = 'doc'
    TXT = 'txt'
    MD = 'md'
    HTML = 'html'
    RTF = 'rtf'
    ODT = 'odt'
    XLSX = 'xlsx'
    XLS = 'xls'
    CSV = 'csv'
    PPT = 'ppt'
    PPTX = 'pptx'
    IMAGE = 'image'
    OTHER = 'other'


class ProcessingStatus(Enum):
    """Document processing status enumeration."""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    RETRY = 'retry'


class Document(SoftDeleteModel, StatusMixin):
    """Document model for storing document metadata and content."""
    
    # Basic information
    title = CharField(max_length=255, index=True)
    description = TextField(null=True)
    
    # File information
    filename = CharField(max_length=255)
    original_filename = CharField(max_length=255)
    file_path = CharField(max_length=500)
    file_size = BigIntegerField(default=0, index=True)
    file_hash = CharField(max_length=64, index=True)  # SHA-256 hash
    mime_type = CharField(max_length=100, null=True)
    document_type = CharField(max_length=20, default=DocumentType.OTHER.value)
    
    # Content information
    content = TextField(null=True)  # Extracted text content
    content_preview = CharField(max_length=500, null=True)  # First 500 chars
    page_count = IntegerField(default=0)
    word_count = IntegerField(default=0)
    character_count = IntegerField(default=0)
    
    # Processing information
    processing_status = CharField(
        max_length=20, 
        default=ProcessingStatus.PENDING.value,
        index=True
    )
    processing_progress = IntegerField(default=0)  # 0-100
    processing_started_at = DateTimeField(null=True)
    processing_completed_at = DateTimeField(null=True)
    processing_error = TextField(null=True)
    processing_metadata = JSONField(default=dict)
    
    # MinerU specific fields
    mineru_task_id = CharField(max_length=100, null=True, index=True)
    mineru_result = JSONField(default=dict)
    extraction_config = JSONField(default=dict)
    
    # Ownership and access
    owner_id = CharField(max_length=36, index=True)
    is_public = BooleanField(default=False, index=True)
    access_permissions = JSONField(default=dict)  # User/role permissions
    
    # Categorization and tagging
    category = CharField(max_length=100, null=True, index=True)
    tags = JSONField(default=list)
    language = CharField(max_length=10, null=True)
    
    # Version control
    version = IntegerField(default=1)
    parent_document_id = CharField(max_length=36, null=True, index=True)
    
    # Statistics
    view_count = IntegerField(default=0)
    download_count = IntegerField(default=0)
    last_accessed_at = DateTimeField(null=True)
    
    class Meta:
        table_name = 'document'
        indexes = (
            (('owner_id', 'status'), False),
            (('processing_status', 'created_at'), False),
            (('file_hash',), False),
            (('document_type', 'is_public'), False),
            (('category', 'tags'), False),
        )
    
    @property
    def owner(self):
        """Get document owner."""
        from backend.models.user import User
        try:
            return User.get_by_id(self.owner_id)
        except User.DoesNotExist:
            return None
    
    @property
    def parent_document(self) -> Optional['Document']:
        """Get parent document if this is a version."""
        if not self.parent_document_id:
            return None
        try:
            return Document.get_by_id(self.parent_document_id)
        except Document.DoesNotExist:
            return None
    
    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return os.path.splitext(self.filename)[1].lower()
    
    @property
    def is_processing(self) -> bool:
        """Check if document is currently being processed."""
        return self.processing_status in [
            ProcessingStatus.PENDING.value,
            ProcessingStatus.PROCESSING.value,
            ProcessingStatus.RETRY.value
        ]
    
    @property
    def is_processed(self) -> bool:
        """Check if document has been processed successfully."""
        return self.processing_status == ProcessingStatus.COMPLETED.value
    
    @property
    def processing_duration(self) -> Optional[timedelta]:
        """Get processing duration."""
        if not self.processing_started_at:
            return None
        
        end_time = self.processing_completed_at or datetime.now()
        return end_time - self.processing_started_at
    
    def calculate_file_hash(self, file_path: Optional[str] = None) -> str:
        """
        Calculate SHA-256 hash of the file.
        
        Args:
            file_path (str, optional): File path to calculate hash for
            
        Returns:
            str: SHA-256 hash
        """
        path = file_path or self.file_path
        
        if not os.path.exists(path):
            return ''
        
        sha256_hash = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def update_content_stats(self) -> None:
        """
        Update content statistics (word count, character count, etc.).
        """
        if self.content:
            self.character_count = len(self.content)
            self.word_count = len(self.content.split())
            self.content_preview = self.content[:500]
        else:
            self.character_count = 0
            self.word_count = 0
            self.content_preview = None
        
        self.save()
    
    def start_processing(self, task_id: Optional[str] = None) -> None:
        """
        Mark document as processing started.
        
        Args:
            task_id (str, optional): MinerU task ID
        """
        self.processing_status = ProcessingStatus.PROCESSING.value
        self.processing_started_at = datetime.now()
        self.processing_progress = 0
        self.processing_error = None
        
        if task_id:
            self.mineru_task_id = task_id
        
        self.save()
    
    def complete_processing(self, content: str = None, metadata: Dict = None) -> None:
        """
        Mark document as processing completed.
        
        Args:
            content (str, optional): Extracted content
            metadata (Dict, optional): Processing metadata
        """
        self.processing_status = ProcessingStatus.COMPLETED.value
        self.processing_completed_at = datetime.now()
        self.processing_progress = 100
        self.processing_error = None
        
        if content is not None:
            self.content = content
            self.update_content_stats()
        
        if metadata:
            self.processing_metadata = metadata
        
        self.save()
    
    def fail_processing(self, error: str, retry: bool = False) -> None:
        """
        Mark document as processing failed.
        
        Args:
            error (str): Error message
            retry (bool): Whether to mark for retry
        """
        self.processing_status = ProcessingStatus.RETRY.value if retry else ProcessingStatus.FAILED.value
        self.processing_error = error
        
        if not retry:
            self.processing_completed_at = datetime.now()
        
        self.save()
    
    def update_progress(self, progress: int) -> None:
        """
        Update processing progress.
        
        Args:
            progress (int): Progress percentage (0-100)
        """
        self.processing_progress = max(0, min(100, progress))
        self.save()
    
    def record_access(self, user_id: Optional[str] = None) -> None:
        """
        Record document access.
        
        Args:
            user_id (str, optional): User ID who accessed the document
        """
        self.view_count += 1
        self.last_accessed_at = datetime.now()
        self.save()
    
    def record_download(self) -> None:
        """
        Record document download.
        """
        self.download_count += 1
        self.save()
    
    def has_access(self, user_id: str) -> bool:
        """
        Check if user has access to document.
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if user has access
        """
        # Owner always has access
        if self.owner_id == user_id:
            return True
        
        # Public documents are accessible to all
        if self.is_public:
            return True
        
        # Check explicit permissions
        if isinstance(self.access_permissions, dict):
            return user_id in self.access_permissions.get('users', [])
        
        return False
    
    def grant_access(self, user_id: str, permission: str = 'read') -> None:
        """
        Grant access to user.
        
        Args:
            user_id (str): User ID
            permission (str): Permission level ('read', 'write', 'admin')
        """
        if not isinstance(self.access_permissions, dict):
            self.access_permissions = {'users': {}, 'roles': {}}
        
        if 'users' not in self.access_permissions:
            self.access_permissions['users'] = {}
        
        self.access_permissions['users'][user_id] = permission
        self.save()
    
    def revoke_access(self, user_id: str) -> None:
        """
        Revoke access from user.
        
        Args:
            user_id (str): User ID
        """
        if isinstance(self.access_permissions, dict) and 'users' in self.access_permissions:
            self.access_permissions['users'].pop(user_id, None)
            self.save()
    
    def add_tag(self, tag: str) -> None:
        """
        Add tag to document.
        
        Args:
            tag (str): Tag to add
        """
        if not isinstance(self.tags, list):
            self.tags = []
        
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.save()
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove tag from document.
        
        Args:
            tag (str): Tag to remove
        """
        if isinstance(self.tags, list):
            tag = tag.strip().lower()
            if tag in self.tags:
                self.tags.remove(tag)
                self.save()
    
    @classmethod
    def get_by_hash(cls, file_hash: str) -> Optional['Document']:
        """
        Get document by file hash.
        
        Args:
            file_hash (str): File hash
            
        Returns:
            Document: Document instance or None
        """
        try:
            return cls.get(cls.file_hash == file_hash)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_by_owner(cls, owner_id: str, include_deleted: bool = False) -> List['Document']:
        """
        Get documents by owner.
        
        Args:
            owner_id (str): Owner user ID
            include_deleted (bool): Whether to include soft-deleted documents
            
        Returns:
            List[Document]: List of documents
        """
        query = cls.select().where(cls.owner_id == owner_id)
        
        if not include_deleted:
            query = query.where(cls.deleted_at.is_null())
        
        return list(query.order_by(cls.created_at.desc()))
    
    @classmethod
    def search_documents(cls, 
                        query: str,
                        owner_id: Optional[str] = None,
                        document_type: Optional[str] = None,
                        category: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        is_public: Optional[bool] = None,
                        limit: int = 50) -> List['Document']:
        """
        Search documents with various filters.
        
        Args:
            query (str): Search query
            owner_id (str, optional): Filter by owner
            document_type (str, optional): Filter by document type
            category (str, optional): Filter by category
            tags (List[str], optional): Filter by tags
            is_public (bool, optional): Filter by public status
            limit (int): Maximum number of results
            
        Returns:
            List[Document]: List of matching documents
        """
        search_query = cls.select().where(cls.deleted_at.is_null())
        
        # Text search in title, description, and content
        if query:
            search_terms = query.split()
            for term in search_terms:
                search_query = search_query.where(
                    (cls.title.contains(term)) |
                    (cls.description.contains(term)) |
                    (cls.content.contains(term))
                )
        
        # Apply filters
        if owner_id:
            search_query = search_query.where(cls.owner_id == owner_id)
        
        if document_type:
            search_query = search_query.where(cls.document_type == document_type)
        
        if category:
            search_query = search_query.where(cls.category == category)
        
        if is_public is not None:
            search_query = search_query.where(cls.is_public == is_public)
        
        # Tag filtering (simplified - in production, use proper JSON queries)
        if tags:
            for tag in tags:
                search_query = search_query.where(cls.tags.contains(tag))
        
        return list(search_query.order_by(cls.created_at.desc()).limit(limit))
    
    def to_dict(self, include_content: bool = False, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Convert document to dictionary.
        
        Args:
            include_content (bool): Whether to include full content
            include_metadata (bool): Whether to include processing metadata
            
        Returns:
            Dict[str, Any]: Document data dictionary
        """
        exclude_fields = []
        if not include_content:
            exclude_fields.append('content')
        if not include_metadata:
            exclude_fields.extend(['processing_metadata', 'mineru_result'])
        
        data = super().to_dict(exclude=exclude_fields)
        
        # Add computed fields
        data['file_extension'] = self.file_extension
        data['is_processing'] = self.is_processing
        data['is_processed'] = self.is_processed
        
        if self.processing_duration:
            data['processing_duration_seconds'] = self.processing_duration.total_seconds()
        
        # Add owner information
        if self.owner:
            data['owner'] = {
                'id': self.owner.id,
                'username': self.owner.username,
                'display_name': self.owner.display_name
            }
        
        return data
    
    def __str__(self) -> str:
        return f"Document: {self.title} ({self.filename})"


class DocumentVersion(BaseModel):
    """Document version model for tracking document changes."""
    
    document_id = CharField(max_length=36, index=True)
    version_number = IntegerField(index=True)
    
    # Version metadata
    title = CharField(max_length=255)
    description = TextField(null=True)
    change_summary = TextField(null=True)
    
    # File information
    filename = CharField(max_length=255)
    file_path = CharField(max_length=500)
    file_size = BigIntegerField(default=0)
    file_hash = CharField(max_length=64)
    
    # Content snapshot
    content = TextField(null=True)
    processing_metadata = JSONField(default=dict)
    
    # Version tracking
    created_by = CharField(max_length=36, index=True)
    is_current = BooleanField(default=False, index=True)
    
    class Meta:
        table_name = 'document_version'
        indexes = (
            (('document_id', 'version_number'), True),  # Unique version per document
            (('document_id', 'is_current'), False),
        )
    
    @property
    def document(self) -> Optional[Document]:
        """Get the parent document."""
        try:
            return Document.get_by_id(self.document_id)
        except Document.DoesNotExist:
            return None
    
    @property
    def creator(self):
        """Get version creator."""
        from backend.models.user import User
        try:
            return User.get_by_id(self.created_by)
        except User.DoesNotExist:
            return None
    
    @classmethod
    def create_version(cls, document: Document, created_by: str, change_summary: str = None) -> 'DocumentVersion':
        """
        Create a new version of a document.
        
        Args:
            document (Document): Document to version
            created_by (str): User ID who created the version
            change_summary (str, optional): Summary of changes
            
        Returns:
            DocumentVersion: Created version instance
        """
        # Get next version number
        last_version = cls.select().where(
            cls.document_id == document.id
        ).order_by(cls.version_number.desc()).first()
        
        next_version = (last_version.version_number + 1) if last_version else 1
        
        # Mark previous versions as not current
        cls.update(is_current=False).where(
            cls.document_id == document.id
        ).execute()
        
        # Create new version
        version = cls.create(
            document_id=document.id,
            version_number=next_version,
            title=document.title,
            description=document.description,
            change_summary=change_summary,
            filename=document.filename,
            file_path=document.file_path,
            file_size=document.file_size,
            file_hash=document.file_hash,
            content=document.content,
            processing_metadata=document.processing_metadata,
            created_by=created_by,
            is_current=True
        )
        
        # Update document version
        document.version = next_version
        document.save()
        
        return version
    
    def __str__(self) -> str:
        return f"Version {self.version_number} of {self.title}"


class DocumentShare(BaseModel):
    """Document sharing model for managing shared access."""
    
    document_id = CharField(max_length=36, index=True)
    shared_by = CharField(max_length=36, index=True)
    shared_with = CharField(max_length=36, index=True, null=True)  # Null for public shares
    
    # Share configuration
    share_token = CharField(max_length=64, unique=True, index=True)
    permission_level = CharField(max_length=20, default='read')  # read, write, admin
    
    # Access control
    password_hash = CharField(max_length=255, null=True)
    max_downloads = IntegerField(null=True)
    download_count = IntegerField(default=0)
    
    # Timing
    expires_at = DateTimeField(null=True, index=True)
    last_accessed_at = DateTimeField(null=True)
    
    # Status
    is_active = BooleanField(default=True, index=True)
    
    class Meta:
        table_name = 'document_share'
        indexes = (
            (('document_id', 'shared_with'), False),
            (('share_token',), True),
            (('expires_at', 'is_active'), False),
        )
    
    @property
    def document(self) -> Optional[Document]:
        """Get shared document."""
        try:
            return Document.get_by_id(self.document_id)
        except Document.DoesNotExist:
            return None
    
    @property
    def sharer(self):
        """Get user who shared the document."""
        from backend.models.user import User
        try:
            return User.get_by_id(self.shared_by)
        except User.DoesNotExist:
            return None
    
    @property
    def recipient(self):
        """Get user who received the share."""
        if not self.shared_with:
            return None
        
        from backend.models.user import User
        try:
            return User.get_by_id(self.shared_with)
        except User.DoesNotExist:
            return None
    
    @property
    def is_expired(self) -> bool:
        """Check if share is expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if share is valid."""
        if not self.is_active:
            return False
        
        if self.is_expired:
            return False
        
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        
        return True
    
    def record_access(self) -> None:
        """Record share access."""
        self.last_accessed_at = datetime.now()
        self.save()
    
    def record_download(self) -> None:
        """Record share download."""
        self.download_count += 1
        self.last_accessed_at = datetime.now()
        self.save()
    
    @classmethod
    def get_by_token(cls, share_token: str) -> Optional['DocumentShare']:
        """
        Get share by token.
        
        Args:
            share_token (str): Share token
            
        Returns:
            DocumentShare: Share instance or None
        """
        try:
            return cls.get(cls.share_token == share_token)
        except cls.DoesNotExist:
            return None
    
    def __str__(self) -> str:
        return f"Share: {self.document_id} by {self.shared_by}"