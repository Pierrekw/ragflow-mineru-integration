#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinerU Integration Service for Ragflow-MinerU Integration

This module provides MinerU document processing and integration services.
"""

import os
import json
import hashlib
import tempfile
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from flask import current_app
from celery import Celery

from backend.models.document import Document, DocumentType, ProcessingStatus
from backend.models.task import Task, TaskType, TaskStatus, TaskPriority
from backend.models.user import User


class MinerUError(Exception):
    """MinerU related errors."""
    pass


class DocumentProcessingError(Exception):
    """Document processing related errors."""
    pass


class MinerUService:
    """MinerU integration and document processing service."""
    
    def __init__(self, celery_app: Celery = None):
        self.celery_app = celery_app
        self.supported_formats = {
            'pdf': ['.pdf'],
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'],
            'office': ['.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'],
            'text': ['.txt', '.md', '.rtf'],
            'html': ['.html', '.htm']
        }
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
        self.processed_dir = Path(current_app.config.get('PROCESSED_FOLDER', 'processed'))
        
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def upload_document(self, 
                       file_data: bytes,
                       filename: str,
                       user_id: str,
                       title: str = None,
                       description: str = None,
                       tags: List[str] = None,
                       is_public: bool = False,
                       auto_process: bool = True) -> Dict[str, Any]:
        """
        Upload and optionally process a document.
        
        Args:
            file_data (bytes): File content
            filename (str): Original filename
            user_id (str): User ID
            title (str, optional): Document title
            description (str, optional): Document description
            tags (List[str], optional): Document tags
            is_public (bool): Whether document is public
            auto_process (bool): Whether to automatically start processing
            
        Returns:
            Dict[str, Any]: Upload result with document info
            
        Raises:
            DocumentProcessingError: If upload fails
        """
        try:
            # Validate file
            self._validate_file(file_data, filename)
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_data)
            
            # Check if document already exists
            existing_doc = Document.get_by_hash(file_hash)
            if existing_doc:
                return {
                    'success': True,
                    'message': 'Document already exists',
                    'document': existing_doc.to_dict(),
                    'duplicate': True
                }
            
            # Determine document type
            doc_type = self._determine_document_type(filename)
            
            # Generate unique filename
            file_extension = Path(filename).suffix.lower()
            unique_filename = f"{file_hash}{file_extension}"
            file_path = self.upload_dir / unique_filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Create document record
            document = Document.create(
                title=title or Path(filename).stem,
                description=description,
                filename=filename,
                file_path=str(file_path),
                file_size=len(file_data),
                file_hash=file_hash,
                mime_type=self._get_mime_type(filename),
                document_type=doc_type,
                owner_id=user_id,
                is_public=is_public,
                tags=tags or [],
                status=ProcessingStatus.PENDING if auto_process else ProcessingStatus.UPLOADED
            )
            
            result = {
                'success': True,
                'message': 'Document uploaded successfully',
                'document': document.to_dict(),
                'duplicate': False
            }
            
            # Start processing if requested
            if auto_process:
                task_result = self.process_document(document.id, user_id)
                result['task'] = task_result
            
            current_app.logger.info(f"Document uploaded: {filename} by user {user_id}")
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Document upload error: {str(e)}")
            raise DocumentProcessingError(str(e))
    
    def process_document(self, 
                        document_id: str, 
                        user_id: str,
                        config: Dict[str, Any] = None,
                        priority: TaskPriority = TaskPriority.NORMAL) -> Dict[str, Any]:
        """
        Start document processing with MinerU.
        
        Args:
            document_id (str): Document ID
            user_id (str): User ID
            config (Dict[str, Any], optional): Processing configuration
            priority (TaskPriority): Task priority
            
        Returns:
            Dict[str, Any]: Processing task info
            
        Raises:
            DocumentProcessingError: If processing start fails
        """
        try:
            # Get document
            document = Document.get_by_id(document_id)
            if not document:
                raise DocumentProcessingError("Document not found")
            
            # Check if user has access
            if document.owner_id != user_id and not document.is_public:
                raise DocumentProcessingError("Access denied")
            
            # Check if document is already being processed
            if document.status in [ProcessingStatus.PROCESSING, ProcessingStatus.COMPLETED]:
                return {
                    'success': False,
                    'message': f'Document is already {document.status.value}',
                    'document': document.to_dict()
                }
            
            # Validate file exists
            if not os.path.exists(document.file_path):
                raise DocumentProcessingError("Document file not found")
            
            # Create processing task
            task_data = {
                'document_id': document_id,
                'file_path': document.file_path,
                'filename': document.filename,
                'document_type': document.document_type.value,
                'config': config or self._get_default_config(document.document_type)
            }
            
            task = Task.create(
                name=f"Process document: {document.filename}",
                description=f"MinerU processing for document {document.title}",
                type=TaskType.DOCUMENT_PROCESSING,
                data=task_data,
                priority=priority,
                created_by=user_id,
                assigned_to=user_id
            )
            
            # Update document status
            document.start_processing()
            document.mineru_task_id = task.id
            document.save()
            
            # Submit to Celery if available
            if self.celery_app:
                celery_task = self.celery_app.send_task(
                    'process_document_task',
                    args=[task.id],
                    priority=priority.value
                )
                task.celery_task_id = celery_task.id
                task.start()
            
            current_app.logger.info(f"Document processing started: {document_id} (task: {task.id})")
            
            return {
                'success': True,
                'message': 'Document processing started',
                'task': task.to_dict(),
                'document': document.to_dict()
            }
            
        except Exception as e:
            current_app.logger.error(f"Document processing start error: {str(e)}")
            raise DocumentProcessingError(str(e))
    
    def get_processing_status(self, document_id: str, user_id: str = None) -> Dict[str, Any]:
        """
        Get document processing status.
        
        Args:
            document_id (str): Document ID
            user_id (str, optional): User ID for access control
            
        Returns:
            Dict[str, Any]: Processing status info
        """
        try:
            document = Document.get_by_id(document_id)
            if not document:
                return {
                    'success': False,
                    'message': 'Document not found'
                }
            
            # Check access if user_id provided
            if user_id and document.owner_id != user_id and not document.is_public:
                return {
                    'success': False,
                    'message': 'Access denied'
                }
            
            result = {
                'success': True,
                'document_id': document_id,
                'status': document.status.value,
                'progress': document.processing_progress,
                'started_at': document.processing_started_at.isoformat() if document.processing_started_at else None,
                'completed_at': document.processing_completed_at.isoformat() if document.processing_completed_at else None,
                'error_message': document.processing_error
            }
            
            # Get task info if available
            if document.mineru_task_id:
                task = Task.get_by_id(document.mineru_task_id)
                if task:
                    result['task'] = {
                        'id': task.id,
                        'status': task.status.value,
                        'progress': task.progress,
                        'worker_node': task.worker_node_id,
                        'queue': task.queue_name
                    }
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Get processing status error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to get processing status'
            }
    
    def get_document_content(self, document_id: str, user_id: str = None) -> Dict[str, Any]:
        """
        Get processed document content.
        
        Args:
            document_id (str): Document ID
            user_id (str, optional): User ID for access control
            
        Returns:
            Dict[str, Any]: Document content
        """
        try:
            document = Document.get_by_id(document_id)
            if not document:
                return {
                    'success': False,
                    'message': 'Document not found'
                }
            
            # Check access
            if user_id and document.owner_id != user_id and not document.is_public:
                return {
                    'success': False,
                    'message': 'Access denied'
                }
            
            # Check if processing is completed
            if document.status != ProcessingStatus.COMPLETED:
                return {
                    'success': False,
                    'message': f'Document processing not completed (status: {document.status.value})'
                }
            
            # Record access
            if user_id:
                document.record_access()
            
            return {
                'success': True,
                'document': document.to_dict(),
                'content': {
                    'text': document.extracted_text,
                    'metadata': document.mineru_result,
                    'page_count': document.page_count,
                    'word_count': document.word_count,
                    'character_count': document.character_count
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Get document content error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to get document content'
            }
    
    def cancel_processing(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """
        Cancel document processing.
        
        Args:
            document_id (str): Document ID
            user_id (str): User ID
            
        Returns:
            Dict[str, Any]: Cancellation result
        """
        try:
            document = Document.get_by_id(document_id)
            if not document:
                return {
                    'success': False,
                    'message': 'Document not found'
                }
            
            # Check access
            if document.owner_id != user_id:
                return {
                    'success': False,
                    'message': 'Access denied'
                }
            
            # Check if processing can be cancelled
            if document.status not in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]:
                return {
                    'success': False,
                    'message': f'Cannot cancel processing (status: {document.status.value})'
                }
            
            # Cancel task if exists
            if document.mineru_task_id:
                task = Task.get_by_id(document.mineru_task_id)
                if task:
                    task.cancel()
                    
                    # Cancel Celery task if exists
                    if task.celery_task_id and self.celery_app:
                        self.celery_app.control.revoke(task.celery_task_id, terminate=True)
            
            # Update document status
            document.fail_processing("Processing cancelled by user")
            
            current_app.logger.info(f"Document processing cancelled: {document_id} by user {user_id}")
            
            return {
                'success': True,
                'message': 'Processing cancelled successfully'
            }
            
        except Exception as e:
            current_app.logger.error(f"Cancel processing error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to cancel processing'
            }
    
    def delete_document(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """
        Delete document and associated files.
        
        Args:
            document_id (str): Document ID
            user_id (str): User ID
            
        Returns:
            Dict[str, Any]: Deletion result
        """
        try:
            document = Document.get_by_id(document_id)
            if not document:
                return {
                    'success': False,
                    'message': 'Document not found'
                }
            
            # Check access
            if document.owner_id != user_id:
                return {
                    'success': False,
                    'message': 'Access denied'
                }
            
            # Cancel processing if active
            if document.status in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]:
                self.cancel_processing(document_id, user_id)
            
            # Delete files
            try:
                if os.path.exists(document.file_path):
                    os.remove(document.file_path)
                
                # Delete processed files if they exist
                processed_path = self.processed_dir / f"{document.file_hash}_processed"
                if processed_path.exists():
                    if processed_path.is_dir():
                        import shutil
                        shutil.rmtree(processed_path)
                    else:
                        processed_path.unlink()
                        
            except Exception as e:
                current_app.logger.warning(f"Failed to delete files for document {document_id}: {str(e)}")
            
            # Soft delete document
            document.soft_delete()
            
            current_app.logger.info(f"Document deleted: {document_id} by user {user_id}")
            
            return {
                'success': True,
                'message': 'Document deleted successfully'
            }
            
        except Exception as e:
            current_app.logger.error(f"Delete document error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to delete document'
            }
    
    def search_documents(self, 
                        query: str,
                        user_id: str = None,
                        filters: Dict[str, Any] = None,
                        page: int = 1,
                        per_page: int = 20) -> Dict[str, Any]:
        """
        Search documents.
        
        Args:
            query (str): Search query
            user_id (str, optional): User ID for access control
            filters (Dict[str, Any], optional): Search filters
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            Dict[str, Any]: Search results
        """
        try:
            results = Document.search(
                query=query,
                user_id=user_id,
                filters=filters,
                page=page,
                per_page=per_page
            )
            
            return {
                'success': True,
                'results': [doc.to_dict() for doc in results['documents']],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': results['total'],
                    'pages': results['pages']
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Search documents error: {str(e)}")
            return {
                'success': False,
                'message': 'Search failed',
                'results': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0
                }
            }
    
    def get_user_documents(self, 
                          user_id: str,
                          status: ProcessingStatus = None,
                          page: int = 1,
                          per_page: int = 20) -> Dict[str, Any]:
        """
        Get user's documents.
        
        Args:
            user_id (str): User ID
            status (ProcessingStatus, optional): Filter by status
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            Dict[str, Any]: User documents
        """
        try:
            results = Document.get_by_owner(
                owner_id=user_id,
                status=status,
                page=page,
                per_page=per_page
            )
            
            return {
                'success': True,
                'documents': [doc.to_dict() for doc in results['documents']],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': results['total'],
                    'pages': results['pages']
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Get user documents error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to get user documents',
                'documents': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0
                }
            }
    
    def get_processing_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Args:
            user_id (str, optional): User ID for user-specific stats
            
        Returns:
            Dict[str, Any]: Processing statistics
        """
        try:
            # Get document counts by status
            stats = {
                'total_documents': 0,
                'by_status': {},
                'by_type': {},
                'processing_queue': 0,
                'average_processing_time': 0
            }
            
            # Build query
            query = Document.select()
            if user_id:
                query = query.where(Document.owner_id == user_id)
            
            # Count by status
            for status in ProcessingStatus:
                count = query.where(Document.status == status).count()
                stats['by_status'][status.value] = count
                stats['total_documents'] += count
            
            # Count by type
            for doc_type in DocumentType:
                count = query.where(Document.document_type == doc_type).count()
                stats['by_type'][doc_type.value] = count
            
            # Processing queue
            stats['processing_queue'] = query.where(
                Document.status.in_([ProcessingStatus.PENDING, ProcessingStatus.PROCESSING])
            ).count()
            
            # Average processing time (for completed documents)
            completed_docs = query.where(
                (Document.status == ProcessingStatus.COMPLETED) &
                (Document.processing_started_at.is_null(False)) &
                (Document.processing_completed_at.is_null(False))
            )
            
            total_time = 0
            count = 0
            for doc in completed_docs:
                if doc.processing_started_at and doc.processing_completed_at:
                    duration = (doc.processing_completed_at - doc.processing_started_at).total_seconds()
                    total_time += duration
                    count += 1
            
            if count > 0:
                stats['average_processing_time'] = total_time / count
            
            return {
                'success': True,
                'statistics': stats
            }
            
        except Exception as e:
            current_app.logger.error(f"Get processing statistics error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to get statistics'
            }
    
    def _validate_file(self, file_data: bytes, filename: str) -> None:
        """
        Validate uploaded file.
        
        Args:
            file_data (bytes): File content
            filename (str): Filename
            
        Raises:
            DocumentProcessingError: If file is invalid
        """
        # Check file size
        if len(file_data) > self.max_file_size:
            raise DocumentProcessingError(f"File size exceeds maximum limit ({self.max_file_size} bytes)")
        
        # Check file extension
        file_extension = Path(filename).suffix.lower()
        supported_extensions = []
        for extensions in self.supported_formats.values():
            supported_extensions.extend(extensions)
        
        if file_extension not in supported_extensions:
            raise DocumentProcessingError(f"Unsupported file format: {file_extension}")
        
        # Check if file is empty
        if len(file_data) == 0:
            raise DocumentProcessingError("File is empty")
    
    def _calculate_file_hash(self, file_data: bytes) -> str:
        """
        Calculate SHA-256 hash of file content.
        
        Args:
            file_data (bytes): File content
            
        Returns:
            str: File hash
        """
        return hashlib.sha256(file_data).hexdigest()
    
    def _determine_document_type(self, filename: str) -> DocumentType:
        """
        Determine document type from filename.
        
        Args:
            filename (str): Filename
            
        Returns:
            DocumentType: Document type
        """
        file_extension = Path(filename).suffix.lower()
        
        for doc_type, extensions in self.supported_formats.items():
            if file_extension in extensions:
                if doc_type == 'pdf':
                    return DocumentType.PDF
                elif doc_type == 'image':
                    return DocumentType.IMAGE
                elif doc_type == 'office':
                    return DocumentType.OFFICE
                elif doc_type == 'text':
                    return DocumentType.TEXT
                elif doc_type == 'html':
                    return DocumentType.HTML
        
        return DocumentType.OTHER
    
    def _get_mime_type(self, filename: str) -> str:
        """
        Get MIME type from filename.
        
        Args:
            filename (str): Filename
            
        Returns:
            str: MIME type
        """
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def _get_default_config(self, document_type: DocumentType) -> Dict[str, Any]:
        """
        Get default processing configuration for document type.
        
        Args:
            document_type (DocumentType): Document type
            
        Returns:
            Dict[str, Any]: Default configuration
        """
        base_config = {
            'extract_text': True,
            'extract_images': True,
            'extract_tables': True,
            'ocr_enabled': True,
            'language': 'auto'
        }
        
        if document_type == DocumentType.PDF:
            base_config.update({
                'pdf_extract_mode': 'auto',  # auto, text, ocr
                'preserve_layout': True,
                'extract_annotations': True
            })
        elif document_type == DocumentType.IMAGE:
            base_config.update({
                'ocr_engine': 'paddleocr',
                'image_preprocessing': True,
                'deskew': True
            })
        elif document_type == DocumentType.OFFICE:
            base_config.update({
                'extract_metadata': True,
                'convert_to_pdf': False
            })
        
        return base_config
    
    @staticmethod
    def cleanup_old_files(days: int = 30) -> Dict[str, int]:
        """
        Clean up old uploaded and processed files.
        
        Args:
            days (int): Number of days to keep files
            
        Returns:
            Dict[str, int]: Cleanup statistics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Find documents to clean up
            old_docs = Document.select().where(
                (Document.created_at < cutoff_date) &
                (Document.is_deleted == True)
            )
            
            files_deleted = 0
            for doc in old_docs:
                try:
                    # Delete original file
                    if os.path.exists(doc.file_path):
                        os.remove(doc.file_path)
                        files_deleted += 1
                    
                    # Delete processed files
                    processed_dir = Path(current_app.config.get('PROCESSED_FOLDER', 'processed'))
                    processed_path = processed_dir / f"{doc.file_hash}_processed"
                    if processed_path.exists():
                        if processed_path.is_dir():
                            import shutil
                            shutil.rmtree(processed_path)
                        else:
                            processed_path.unlink()
                        files_deleted += 1
                        
                except Exception as e:
                    current_app.logger.warning(f"Failed to delete files for document {doc.id}: {str(e)}")
            
            current_app.logger.info(f"File cleanup completed: {files_deleted} files deleted")
            
            return {
                'files_deleted': files_deleted,
                'documents_processed': len(old_docs)
            }
            
        except Exception as e:
            current_app.logger.error(f"File cleanup error: {str(e)}")
            return {
                'files_deleted': 0,
                'documents_processed': 0
            }