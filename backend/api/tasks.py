#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Management API for Ragflow-MinerU Integration

This module provides task management API endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from functools import wraps
from datetime import datetime, timedelta

from backend.services.task_service import TaskService
from backend.services.auth_service import AuthService
from backend.services.permission_service import PermissionService
from backend.models.task import Task, TaskType, TaskStatus, TaskPriority
from backend.models.user import User
from backend.api import HTTP_STATUS, RESPONSE_MESSAGES
from backend.api.auth import require_permission


# Create blueprint
tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/v1/tasks')
api = Api(tasks_bp)

# Initialize services
task_service = TaskService()
auth_service = AuthService()
permission_service = PermissionService()


# Validation schemas
class TaskCreateSchema(Schema):
    """Task creation validation schema."""
    name = fields.Str(required=True, validate=lambda x: len(x) <= 255)
    description = fields.Str(allow_none=True, validate=lambda x: len(x) <= 1000 if x else True)
    task_type = fields.Str(required=True, validate=lambda x: x in [t.value for t in TaskType])
    priority = fields.Str(load_default='normal', validate=lambda x: x in [p.value for p in TaskPriority])
    data = fields.Dict(load_default={})
    config = fields.Dict(load_default={})
    queue_name = fields.Str(load_default='default')
    scheduled_at = fields.DateTime(allow_none=True)
    max_retries = fields.Int(load_default=3, validate=lambda x: 0 <= x <= 10)
    timeout_seconds = fields.Int(load_default=3600, validate=lambda x: x > 0)
    dependencies = fields.List(fields.Str(), load_default=[])
    tags = fields.List(fields.Str(), load_default=[])


class TaskSearchSchema(Schema):
    """Task search validation schema."""
    query = fields.Str(allow_none=True)
    task_type = fields.Str(allow_none=True, validate=lambda x: x in [t.value for t in TaskType] if x else True)
    status = fields.Str(allow_none=True, validate=lambda x: x in [s.value for s in TaskStatus] if x else True)
    priority = fields.Str(allow_none=True, validate=lambda x: x in [p.value for p in TaskPriority] if x else True)
    queue_name = fields.Str(allow_none=True)
    created_by = fields.Str(allow_none=True)
    assigned_to = fields.Str(allow_none=True)
    tags = fields.List(fields.Str(), load_default=[])
    created_after = fields.DateTime(allow_none=True)
    created_before = fields.DateTime(allow_none=True)
    scheduled_after = fields.DateTime(allow_none=True)
    scheduled_before = fields.DateTime(allow_none=True)
    page = fields.Int(load_default=1, validate=lambda x: x > 0)
    per_page = fields.Int(load_default=20, validate=lambda x: 1 <= x <= 100)
    sort_by = fields.Str(load_default='created_at', validate=lambda x: x in ['created_at', 'updated_at', 'scheduled_at', 'priority'])
    sort_order = fields.Str(load_default='desc', validate=lambda x: x in ['asc', 'desc'])


class TaskUpdateSchema(Schema):
    """Task update validation schema."""
    name = fields.Str(allow_none=True, validate=lambda x: len(x) <= 255 if x else True)
    description = fields.Str(allow_none=True, validate=lambda x: len(x) <= 1000 if x else True)
    priority = fields.Str(allow_none=True, validate=lambda x: x in [p.value for p in TaskPriority] if x else True)
    assigned_to = fields.Str(allow_none=True)
    scheduled_at = fields.DateTime(allow_none=True)
    config = fields.Dict(allow_none=True)
    tags = fields.List(fields.Str(), allow_none=True)


class TaskProgressSchema(Schema):
    """Task progress update validation schema."""
    progress = fields.Int(required=True, validate=lambda x: 0 <= x <= 100)
    message = fields.Str(allow_none=True)
    metadata = fields.Dict(load_default={})


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


def get_task_or_404(task_id, user_id=None, check_access=True):
    """Get task by ID or return 404."""
    task = Task.get_by_id(task_id)
    if not task:
        return None, {
            'success': False,
            'message': RESPONSE_MESSAGES['NOT_FOUND']
        }, HTTP_STATUS['NOT_FOUND']
    
    if check_access and user_id:
        # Check if user has access to task
        if task.created_by != user_id and task.assigned_to != user_id:
            # Check if user has admin permission
            user = User.get_by_id(user_id)
            if not auth_service.check_permission(user, 'task.admin'):
                return None, {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
    
    return task, None, None


# API Resources
class TaskListResource(Resource):
    """Task list endpoint."""
    
    @jwt_required()
    @require_permission('task.read')
    def get(self):
        """Get tasks with search and filtering."""
        try:
            user_id = get_jwt_identity()
            user = User.get_by_id(user_id)
            
            # Parse query parameters
            parser = reqparse.RequestParser()
            parser.add_argument('query', type=str, location='args')
            parser.add_argument('task_type', type=str, location='args')
            parser.add_argument('status', type=str, location='args')
            parser.add_argument('priority', type=str, location='args')
            parser.add_argument('queue_name', type=str, location='args')
            parser.add_argument('created_by', type=str, location='args')
            parser.add_argument('assigned_to', type=str, location='args')
            parser.add_argument('tags', type=str, action='append', location='args')
            parser.add_argument('created_after', type=str, location='args')
            parser.add_argument('created_before', type=str, location='args')
            parser.add_argument('scheduled_after', type=str, location='args')
            parser.add_argument('scheduled_before', type=str, location='args')
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
            
            # Check if user can see all tasks or only their own
            if not auth_service.check_permission(user, 'task.admin'):
                # Non-admin users can only see their own tasks
                if not args['created_by'] and not args['assigned_to']:
                    args['created_by'] = user_id
            
            # Get tasks
            result = task_service.get_user_tasks(
                user_id=user_id if not auth_service.check_permission(user, 'task.admin') else None,
                task_type=args['task_type'],
                status=args['status'],
                priority=args['priority'],
                queue_name=args['queue_name'],
                created_by=args['created_by'],
                assigned_to=args['assigned_to'],
                tags=args['tags'] or [],
                created_after=args['created_after'],
                created_before=args['created_before'],
                scheduled_after=args['scheduled_after'],
                scheduled_before=args['scheduled_before'],
                page=args['page'],
                per_page=args['per_page'],
                sort_by=args['sort_by'],
                sort_order=args['sort_order']
            )
            
            return {
                'success': True,
                'tasks': result['tasks'],
                'pagination': result['pagination']
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get tasks error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('task.create')
    @validate_json(TaskCreateSchema)
    def post(self, data):
        """Create a new task."""
        try:
            user_id = get_jwt_identity()
            
            # Create task
            result = task_service.create_task(
                name=data['name'],
                description=data.get('description'),
                task_type=data['task_type'],
                priority=data.get('priority', 'normal'),
                data=data.get('data', {}),
                config=data.get('config', {}),
                created_by=user_id,
                assigned_to=data.get('assigned_to'),
                queue_name=data.get('queue_name', 'default'),
                scheduled_at=data.get('scheduled_at'),
                max_retries=data.get('max_retries', 3),
                timeout_seconds=data.get('timeout_seconds', 3600),
                dependencies=data.get('dependencies', []),
                tags=data.get('tags', [])
            )
            
            if result['success']:
                return {
                    'success': True,
                    'message': RESPONSE_MESSAGES['CREATED'],
                    'task': result['task']
                }, HTTP_STATUS['CREATED']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Create task error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class TaskResource(Resource):
    """Individual task endpoint."""
    
    @jwt_required()
    @require_permission('task.read')
    def get(self, task_id):
        """Get task details."""
        try:
            user_id = get_jwt_identity()
            task, error_response, status_code = get_task_or_404(task_id, user_id)
            
            if error_response:
                return error_response, status_code
            
            task_data = task.to_dict()
            
            # Add additional info if available
            if task.celery_task_id:
                status_result = task_service.get_task_status(task_id)
                if status_result['success']:
                    task_data['celery_status'] = status_result['status']
            
            return {
                'success': True,
                'task': task_data
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Get task error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('task.update')
    @validate_json(TaskUpdateSchema)
    def put(self, data, task_id):
        """Update task."""
        try:
            user_id = get_jwt_identity()
            task, error_response, status_code = get_task_or_404(task_id, user_id)
            
            if error_response:
                return error_response, status_code
            
            # Check if user can update task
            user = User.get_by_id(user_id)
            if (task.created_by != user_id and task.assigned_to != user_id and 
                not auth_service.check_permission(user, 'task.admin')):
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
            
            # Check if task can be updated
            if task.status in [TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED]:
                return {
                    'success': False,
                    'message': 'Cannot update task in current status'
                }, HTTP_STATUS['BAD_REQUEST']
            
            # Update fields
            updated = False
            for field, value in data.items():
                if value is not None and hasattr(task, field):
                    setattr(task, field, value)
                    updated = True
            
            if updated:
                task.updated_at = datetime.utcnow()
                task.save()
            
            return {
                'success': True,
                'message': RESPONSE_MESSAGES['UPDATED'],
                'task': task.to_dict()
            }, HTTP_STATUS['OK']
            
        except Exception as e:
            current_app.logger.error(f"Update task error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']
    
    @jwt_required()
    @require_permission('task.delete')
    def delete(self, task_id):
        """Delete/cancel task."""
        try:
            user_id = get_jwt_identity()
            task, error_response, status_code = get_task_or_404(task_id, user_id)
            
            if error_response:
                return error_response, status_code
            
            # Check if user can delete task
            user = User.get_by_id(user_id)
            if (task.created_by != user_id and 
                not auth_service.check_permission(user, 'task.admin')):
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
            
            # Cancel task
            result = task_service.cancel_task(task_id, user_id)
            
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
                
        except Exception as e:
            current_app.logger.error(f"Delete task error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class TaskProgressResource(Resource):
    """Task progress endpoint."""
    
    @jwt_required()
    @require_permission('task.update')
    @validate_json(TaskProgressSchema)
    def post(self, data, task_id):
        """Update task progress."""
        try:
            user_id = get_jwt_identity()
            task, error_response, status_code = get_task_or_404(task_id, user_id)
            
            if error_response:
                return error_response, status_code
            
            # Check if user can update task progress
            user = User.get_by_id(user_id)
            if (task.created_by != user_id and task.assigned_to != user_id and 
                not auth_service.check_permission(user, 'task.admin')):
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
            
            # Update progress
            result = task_service.update_task_progress(
                task_id=task_id,
                progress=data['progress'],
                message=data.get('message'),
                metadata=data.get('metadata', {})
            )
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Progress updated',
                    'task': result['task']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Update task progress error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class TaskRetryResource(Resource):
    """Task retry endpoint."""
    
    @jwt_required()
    @require_permission('task.retry')
    def post(self, task_id):
        """Retry failed task."""
        try:
            user_id = get_jwt_identity()
            task, error_response, status_code = get_task_or_404(task_id, user_id)
            
            if error_response:
                return error_response, status_code
            
            # Check if user can retry task
            user = User.get_by_id(user_id)
            if (task.created_by != user_id and task.assigned_to != user_id and 
                not auth_service.check_permission(user, 'task.admin')):
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES['FORBIDDEN']
                }, HTTP_STATUS['FORBIDDEN']
            
            # Check if task can be retried
            if task.status not in [TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return {
                    'success': False,
                    'message': 'Task cannot be retried in current status'
                }, HTTP_STATUS['BAD_REQUEST']
            
            # Retry task
            result = task_service.retry_task(task_id, user_id)
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Task queued for retry',
                    'task': result['task']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Retry task error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class TaskQueueResource(Resource):
    """Task queue management endpoint."""
    
    @jwt_required()
    @require_permission('task.admin')
    def get(self):
        """Get queue status."""
        try:
            result = task_service.get_queue_status()
            
            if result['success']:
                return {
                    'success': True,
                    'queues': result['queues']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Get queue status error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class TaskWorkerResource(Resource):
    """Task worker management endpoint."""
    
    @jwt_required()
    @require_permission('task.admin')
    def get(self):
        """Get worker status."""
        try:
            result = task_service.get_worker_status()
            
            if result['success']:
                return {
                    'success': True,
                    'workers': result['workers']
                }, HTTP_STATUS['OK']
            else:
                return {
                    'success': False,
                    'message': result['message']
                }, HTTP_STATUS['BAD_REQUEST']
                
        except Exception as e:
            current_app.logger.error(f"Get worker status error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


class TaskStatsResource(Resource):
    """Task statistics endpoint."""
    
    @jwt_required()
    @require_permission('task.stats')
    def get(self):
        """Get task statistics."""
        try:
            user_id = get_jwt_identity()
            user = User.get_by_id(user_id)
            
            # Check if user can see all stats or only their own
            show_all = auth_service.check_permission(user, 'task.admin')
            
            result = task_service.get_task_stats(
                user_id=None if show_all else user_id
            )
            
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
            current_app.logger.error(f"Get task stats error: {str(e)}")
            return {
                'success': False,
                'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
            }, HTTP_STATUS['INTERNAL_SERVER_ERROR']


# Register API resources
api.add_resource(TaskListResource, '/')
api.add_resource(TaskResource, '/<string:task_id>')
api.add_resource(TaskProgressResource, '/<string:task_id>/progress')
api.add_resource(TaskRetryResource, '/<string:task_id>/retry')
api.add_resource(TaskQueueResource, '/queues')
api.add_resource(TaskWorkerResource, '/workers')
api.add_resource(TaskStatsResource, '/stats')


# Error handlers
@tasks_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handle validation errors."""
    return {
        'success': False,
        'message': RESPONSE_MESSAGES['VALIDATION_ERROR'],
        'errors': e.messages
    }, HTTP_STATUS['BAD_REQUEST']


@tasks_bp.errorhandler(Exception)
def handle_generic_error(e):
    """Handle generic errors."""
    current_app.logger.error(f"Unhandled error in tasks API: {str(e)}")
    return {
        'success': False,
        'message': RESPONSE_MESSAGES['INTERNAL_ERROR']
    }, HTTP_STATUS['INTERNAL_SERVER_ERROR']