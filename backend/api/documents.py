#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document Management API for Ragflow-MinerU Integration

This module provides document management API endpoints.
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from werkzeug.utils import secure_filename
from functools import wraps
import os
import mimetypes
from datetime import datetime

from backend.services.mineru_service import MinerUService, MinerUError, DocumentProcessingError
from backend.services.auth_service import AuthService
from backend.services.permission_service import PermissionService
from backend.models.document import Document, DocumentType, ProcessingStatus
from backend.models.user import User
from backend.api import HTTP_STATUS, RESPONSE_MESSAGES, FILE_UPLOAD
from backend.api.auth import require_permission


# Create blueprint
documents_bp = Blueprint('documents', __name__, url_prefix='/api/v1/documents')
api = Api(documents_bp)

# Initialize services
mineru_service = MinerUService()
auth_service = AuthService()
permission_service = PermissionService()


# Validation schemas
class DocumentUploadSchema(Schema):
    """Document upload validation schema."""
    title = fields.Str(missing=None, validate=lambda x: len(x) <= 255 if x else True)
    description = fields.Str(missing=None, validate=lambda x: len(x) <= 1000 if x else True)
    document_type = fields.Str(missing='auto', validate=lambda x: x in [t.value for t in DocumentType])
    is_public = fields.Bool(missing=False)
    tags = fields.List(fields.Str(), missing=[])
    processing_config = fields.Dict(missing={})


class DocumentSearchSchema(Schema):
    """Document search validation schema."""
    query = fields.Str(missing=None)
    document_type = fields.Str(missing=None, validate=lambda x: x in [t.value for t in DocumentType] if x else True)
    status = fields.Str(missing=None, validate=lambda x: x in [s.value for s in ProcessingStatus] if x else True)
    tags = fields.List(fields.Str(), missing=[])
    owner_id = fields.Str(missing=None)
    is_public = fields.Bool(missing=None)
    created_after = fields.DateTime(missing=None)
    created_before = fields.DateTime(missing=None)
    page = fields.Int(missing=1, validate=lambda x: x > 0)
    per_page = fields.Int(missing=20, validate=lambda x: 1 <= x <= 100)
    sort_by = fields.Str(missing='created_at', validate=lambda x: x in ['created_at', 'updated_at', 'title', 'file_size'])
    sort_order = fields.Str(missing='desc', validate=lambda x: x in ['asc', 'desc'])


class DocumentUpdateSchema(Schema):
    """Document update validation schema."""
    title = fields.Str(missing=None, validate=lambda x: len(x) <= 255 if x else True)
    description = fields.Str(missing=None, validate=lambda x: len(x) <= 1000 if x else True)
    is_public = fields.Bool(missing=None)
    tags = fields.List(fields.Str(), missing=None)


class DocumentShareSchema(Schema):
    """Document share validation schema."""
    share_with = fields.Str(required=True)  # user_id or email
    permission_level = fields.Str(required=True, validate=lambda x: x in ['read', 'write', 'admin'])
    expires_at = fields.DateTime(missing=None)
    password = fields.Str(missing=None)
    max_downloads = fields.Int(missing=None, validate=lambda x: x > 0 if x else True)


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


def validate_file_upload(f):
    """Decorator to validate file upload."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'file' not in request.files:
            return {
                'success': False,
                'message': 'No file provided'
            }, HTTP_STATUS['BAD_REQUEST']
        
        file = request.files['file']
        if file.filename == '':
            return {
                'success': False,
                'message': 'No file selected'
            }, HTTP_STATUS['BAD_REQUEST']
        
        # Check file size
        if hasattr(file, 'content_length') and file.content_length:
            if file.content_length > FILE_UPLOAD['MAX_FILE_SIZE']:
                return {
                    'success': False,
                    'message': f'File too large. Maximum size: {FILE_UPLOAD["MAX_FILE_SIZE"] // (1024*1024)}MB'
                }, HTTP_STATUS['BAD_REQUEST']
        
        # Check file extension
        filename = secure_filename(file.filename)
        if '.' not in filename:
            return {
                'success': False,
                'message': 'File must have an extension'
            }, HTTP_STATUS['BAD_REQUEST']
        
        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in FILE_UPLOAD['ALLOWED_EXTENSIONS']:
            return {
                'success': False,
                'message': f'File type not allowed. Allowed types: {", ".join(FILE_UPLOAD["ALLOWED_EXTENSIONS"])}'
            }, HTTP_STATUS['BAD_REQUEST']
        
        return f(file, *args, **kwargs)
    return decorated_function


def get_document_or_404(document_id, user_id=None, check_access=True):
    """Get document by ID or return 404."""
    document = Document.get_by_id(document_id)
    if not document:
        return None, {
            'success': False,
            'message': RESPONSE_MESSAGES['NOT_FOUND']
        }, HTTP_STATUS['NOT_FOUND']
    
    if check_access and user_id:
        # Check if user has access to document
        if not document.is_public and document.owner_id != user_id:
            # Check if document is shared with user
            if not document.check_access(user_id, 'read'):
                return None, {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
    
    return document, None, None


# API Resources
class DocumentListResource(Resource):
    """Document list endpoint."""
    
    @jwt_required()
    @require_permission('document.read')
    def get(self):
        """Get user documents with search and filtering."""
        try:
            user_id = get_jwt_identity()
            
            # Parse query parameters
            parser = reqparse.RequestParser()
            parser.add_argument('query', type=str, location='args')
            parser.add_argument('document_type', type=str, location='args')
            parser.add_argument('status', type=str, location='args')
            parser.add_argument('tags', type=str, action='append', location='args')
            parser.add_argument('is_public', type=bool, location='args')
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
            
            # Get documents
            result = mineru_service.search_documents(
                user_id=user_id,
                query=args['query'],
                document_type=args['document_type'],
                status=args['status'],
                tags=args['tags'] or [],
                is_public=args['is_public'],
                created_after=args['created_after'],
                created_before=args['created_before'],
                page=args['page'],
                per_page=args['per_page'],
                sort_by=args['sort_by'],
                sort_order=args['sort_order']
            )
            
            return {
                'success': True,
                'documents': result['documents'],
                'pagination': result['pagination']
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get documents error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('document.create')
    @validate_file_upload
    def post(self, file):
        """Upload and process a new document."""
        try:
            user_id = get_jwt_identity()
            
            # Get form data
            form_data = request.form.to_dict()
            
            # Parse tags if provided
            tags = []
            if 'tags' in form_data:
                if isinstance(form_data['tags'], str):
                    tags = [tag.strip() for tag in form_data['tags'].split(',') if tag.strip()]
                elif isinstance(form_data['tags'], list):
                    tags = form_data['tags']
            
            # Parse processing config
            processing_config = {}
            if 'processing_config' in form_data:
                try:
                    import json
                    processing_config = json.loads(form_data['processing_config'])
                except (json.JSONDecodeError, TypeError):
                    processing_config = {}
            
            # Upload and process document
            result = mineru_service.upload_document(
                file=file,
                user_id=user_id,
                title=form_data.get('title'),
                description=form_data.get('description'),
                document_type=form_data.get('document_type', 'auto'),
                is_public=form_data.get('is_public', 'false').lower() == 'true',
                tags=tags,
                processing_config=processing_config
            )
            
            if result['success']:
                return {
                    'success': True,
                    'message': RESPONSE_MESSAGES['CREATED'],
                    'document': result['document'],
                    'task': result.get('task')
                }, HTTP_STATUS['CREATED']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except MinerUError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['BAD_REQUEST']
        except Exception as e:
            current_app.logger.error(f"Upload document error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class DocumentResource(Resource):
    """Individual document endpoint."""
    
    @jwt_required()
    @require_permission('document.read')
    def get(self, document_id):
        """Get document details."""
        try:
            user_id = get_jwt_identity()
            document, error_response, status_code = get_document_or_404(document_id, user_id)
            
            if error_response:
                return error_response, status_code
            
            # Record access
            document.record_access(user_id)
            
            document_data = document.to_dict()
            
            # Add processing status if available
            if document.processing_status != ProcessingStatus.COMPLETED:
                status_result = mineru_service.get_processing_status(document_id)
                if status_result['success']:
                    document_data['processing_info'] = status_result['status']
            
            return {
                'success': True,
                'document': document_data
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get document error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('document.update')
    @validate_json(DocumentUpdateSchema)
    def put(self, data, document_id):
        """Update document metadata."""
        try:
            user_id = get_jwt_identity()
            document, error_response, status_code = get_document_or_404(document_id, user_id)
            
            if error_response:
                return error_response, status_code
            
            # Check if user can update document
            if document.owner_id != user_id and not document.check_access(user_id, 'write'):
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
            
            # Update fields
            updated = False
            for field, value in data.items():
                if value is not None and hasattr(document, field):
                    setattr(document, field, value)
                    updated = True
            
            if updated:
                document.updated_at = datetime.utcnow()
                document.save()
            
            return {
                'success': True,
                'message': RESPONSE_MESSAGES['UPDATED'],
                'document': document.to_dict()
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Update document error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('document.delete')
    def delete(self, document_id):
        """Delete document."""
        try:
            user_id = get_jwt_identity()
            document, error_response, status_code = get_document_or_404(document_id, user_id, check_access=False)
            
            if error_response:
                return error_response, status_code
            
            # Check if user can delete document
            if document.owner_id != user_id:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
            
            # Delete document
            result = mineru_service.delete_document(document_id, user_id)
            
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
                
        except MinerUError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['BAD_REQUEST']
        except Exception as e:
            current_app.logger.error(f"Delete document error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class DocumentContentResource(Resource):
    """Document content endpoint."""
    
    @jwt_required()
    @require_permission('document.read')
    def get(self, document_id):
        """Get document content."""
        try:
            user_id = get_jwt_identity()
            document, error_response, status_code = get_document_or_404(document_id, user_id)
            
            if error_response:
                return error_response, status_code
            
            # Get content
            result = mineru_service.get_document_content(document_id, user_id)
            
            if result['success']:
                # Record access
                document.record_access(user_id)
                
                return {
                    'success': True,
                    'content': result['content']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except MinerUError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['BAD_REQUEST']
        except Exception as e:
            current_app.logger.error(f"Get document content error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class DocumentDownloadResource(Resource):
    """Document download endpoint."""
    
    @jwt_required()
    @require_permission('document.read')
    def get(self, document_id):
        """Download document file."""
        try:
            user_id = get_jwt_identity()
            document, error_response, status_code = get_document_or_404(document_id, user_id)
            
            if error_response:
                return error_response, status_code
            
            # Check if file exists
            if not document.file_path or not os.path.exists(document.file_path):
                return {
                    'success': False,
                    'message': 'File not found'
                }, HTTP_STATUS['NOT_FOUND']
            
            # Record download
            document.record_download(user_id)
            
            # Return file
            return send_file(
                document.file_path,
                as_attachment=True,
                download_name=document.filename,
                mimetype=document.mime_type
            )
            
        except Exception as e:
            current_app.logger.error(f"Download document error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class DocumentProcessingResource(Resource):
    """Document processing endpoint."""
    
    @jwt_required()
    @require_permission('document.process')
    def post(self, document_id):
        """Reprocess document."""
        try:
            user_id = get_jwt_identity()
            document, error_response, status_code = get_document_or_404(document_id, user_id, check_access=False)
            
            if error_response:
                return error_response, status_code
            
            # Check if user can process document
            if document.owner_id != user_id and not document.check_access(user_id, 'write'):
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
            
            # Get processing config from request
            data = request.get_json() or {}
            processing_config = data.get('processing_config', {})
            
            # Start processing
            result = mineru_service.process_document(
                document_id=document_id,
                user_id=user_id,
                config=processing_config
            )
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Processing started',
                    'task': result['task']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except MinerUError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['BAD_REQUEST']
        except Exception as e:
            current_app.logger.error(f"Process document error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('document.read')
    def get(self, document_id):
        """Get processing status."""
        try:
            user_id = get_jwt_identity()
            document, error_response, status_code = get_document_or_404(document_id, user_id)
            
            if error_response:
                return error_response, status_code
            
            # Get processing status
            result = mineru_service.get_processing_status(document_id)
            
            if result['success']:
                return {
                    'success': True,
                    'status': result['status']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except MinerUError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['BAD_REQUEST']
        except Exception as e:
            current_app.logger.error(f"Get processing status error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('document.process')
    def delete(self, document_id):
        """Cancel processing."""
        try:
            user_id = get_jwt_identity()
            document, error_response, status_code = get_document_or_404(document_id, user_id, check_access=False)
            
            if error_response:
                return error_response, status_code
            
            # Check if user can cancel processing
            if document.owner_id != user_id and not document.check_access(user_id, 'write'):
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
            
            # Cancel processing
            result = mineru_service.cancel_processing(document_id, user_id)
            
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
                
        except MinerUError as e:
            return {
                'success': False,
                'message': str(e)
            }, HTTP_STATUS['BAD_REQUEST']
        except Exception as e:
            current_app.logger.error(f"Cancel processing error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class DocumentShareResource(Resource):
    """Document sharing endpoint."""
    
    @jwt_required()
    @require_permission('document.share')
    @validate_json(DocumentShareSchema)
    def post(self, data, document_id):
        """Share document with user."""
        try:
            user_id = get_jwt_identity()
            document, error_response, status_code = get_document_or_404(document_id, user_id, check_access=False)
            
            if error_response:
                return error_response, status_code
            
            # Check if user can share document
            if document.owner_id != user_id and not document.check_access(user_id, 'admin'):
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
            
            # Grant access
            success = document.grant_access(
                user_identifier=data['share_with'],
                permission_level=data['permission_level'],
                granted_by=user_id,
                expires_at=data.get('expires_at'),
                password=data.get('password'),
                max_downloads=data.get('max_downloads')
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'Document shared successfully'
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': 'Failed to share document'
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Share document error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('document.share')
    def delete(self, document_id):
        """Revoke document access."""
        try:
            user_id = get_jwt_identity()
            document, error_response, status_code = get_document_or_404(document_id, user_id, check_access=False)
            
            if error_response:
                return error_response, status_code
            
            # Check if user can revoke access
            if document.owner_id != user_id and not document.check_access(user_id, 'admin'):
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
            
            data = request.get_json() or {}
            user_identifier = data.get('user_identifier')
            
            if not user_identifier:
                return {
                    'success': False,
                    'message': 'User identifier required'
                }, HTTP_STATUS['BAD_REQUEST']
            
            # Revoke access
            success = document.revoke_access(user_identifier)
            
            if success:
                return {
                    'success': True,
                    'message': 'Access revoked successfully'
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': 'Failed to revoke access'
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Revoke document access error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class DocumentStatsResource(Resource):
    """Document statistics endpoint."""
    
    @jwt_required()
    @require_permission('document.stats')
    def get(self):
        """Get document processing statistics."""
        try:
            user_id = get_jwt_identity()
            
            # Get statistics
            result = mineru_service.get_processing_stats(user_id)
            
            if result['success']:
                return {
                    'success': True,
                    'stats': result['stats']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Get document stats error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


# Register API resources
api.add_resource(DocumentListResource, '/')
api.add_resource(DocumentResource, '/<string:document_id>')
api.add_resource(DocumentContentResource, '/<string:document_id>/content')
api.add_resource(DocumentDownloadResource, '/<string:document_id>/download')
api.add_resource(DocumentProcessingResource, '/<string:document_id>/processing')
api.add_resource(DocumentShareResource, '/<string:document_id>/share')
api.add_resource(DocumentStatsResource, '/stats')


# Error handlers
@documents_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handle validation errors."""
    return {
        'success': False,
        'message': RESPONSE_MESSAGES['VALIDATION_ERROR'],
        'errors': e.messages
    }, HTTP_STATUS['BAD_REQUEST']


@documents_bp.errorhandler(MinerUError)
def handle_mineru_error(e):
    """Handle MinerU errors."""
    return {
        'success': False,
        'message': str(e)
    }, HTTP_STATUS['BAD_REQUEST']


@documents_bp.errorhandler(DocumentProcessingError)
def handle_processing_error(e):
    """Handle document processing errors."""
    return {
        'success': False,
        'message': str(e)
    }, HTTP_STATUS['BAD_REQUEST']


@documents_bp.errorhandler(Exception)
def handle_generic_error(e):
    """Handle generic errors."""
    current_app.logger.error(f"Unhandled error in documents API: {str(e)}")
    return {
        'success': False,
        'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
    }, HTTP_STATUS['INTERNAL_SERVER_ERROR']