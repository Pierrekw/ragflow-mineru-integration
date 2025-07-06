#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Package for Ragflow-MinerU Integration

This package contains all API endpoints and controllers for the Ragflow-MinerU integration project.
It provides RESTful APIs for authentication, document processing, task management, and more.

Modules:
    - auth: Authentication and authorization endpoints
    - documents: Document upload, processing, and management endpoints
    - tasks: Task management and monitoring endpoints
    - users: User management endpoints
    - admin: Administrative endpoints
    - health: Health check and system status endpoints

The API follows RESTful conventions and uses Flask-RESTful for endpoint organization.
All endpoints support JSON request/response format and include proper error handling.
"""

__version__ = '1.0.0'
__author__ = 'Ragflow-MinerU Integration Team'
__description__ = 'RESTful API layer for Ragflow-MinerU integration'

# API version and configuration
API_VERSION = 'v1'
API_PREFIX = f'/api/{API_VERSION}'

# Default pagination settings
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Response status codes
HTTP_STATUS = {
    'OK': 200,
    'CREATED': 201,
    'ACCEPTED': 202,
    'NO_CONTENT': 204,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'METHOD_NOT_ALLOWED': 405,
    'CONFLICT': 409,
    'UNPROCESSABLE_ENTITY': 422,
    'TOO_MANY_REQUESTS': 429,
    'INTERNAL_SERVER_ERROR': 500,
    'SERVICE_UNAVAILABLE': 503
}

# Common response messages
RESPONSE_MESSAGES = {
    'SUCCESS': 'Operation completed successfully',
    'CREATED': 'Resource created successfully',
    'UPDATED': 'Resource updated successfully',
    'DELETED': 'Resource deleted successfully',
    'NOT_FOUND': 'Resource not found',
    'UNAUTHORIZED': 'Authentication required',
    'FORBIDDEN': 'Access denied',
    'BAD_REQUEST': 'Invalid request data',
    'VALIDATION_ERROR': 'Validation failed',
    'INTERNAL_ERROR': 'Internal server error',
    'SERVICE_UNAVAILABLE': 'Service temporarily unavailable'
}

# API rate limiting settings
RATE_LIMITS = {
    'default': '100/hour',
    'auth': '10/minute',
    'upload': '20/hour',
    'download': '50/hour',
    'search': '200/hour'
}

# File upload settings
UPLOAD_SETTINGS = {
    'max_file_size': 100 * 1024 * 1024,  # 100MB
    'allowed_extensions': {
        'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
        'txt', 'md', 'rtf', 'html', 'htm',
        'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'
    },
    'upload_folder': 'uploads',
    'processed_folder': 'processed'
}

# API documentation settings
API_DOC_SETTINGS = {
    'title': 'Ragflow-MinerU Integration API',
    'description': 'RESTful API for document processing and management using MinerU',
    'version': API_VERSION,
    'contact': {
        'name': 'API Support',
        'email': 'support@ragflow-mineru.com'
    },
    'license': {
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/MIT'
    }
}