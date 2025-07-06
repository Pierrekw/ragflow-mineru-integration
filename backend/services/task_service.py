#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Service for Ragflow-MinerU Integration

This module provides task management and queue processing services.
"""

import json
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from flask import current_app
from celery import Celery
from celery.result import AsyncResult

from backend.models.task import Task, TaskQueue, WorkerNode, TaskType, TaskStatus, TaskPriority
from backend.models.user import User


class TaskError(Exception):
    """Task related errors."""
    pass


class QueueError(Exception):
    """Queue related errors."""
    pass


class TaskService:
    """Task management and queue processing service."""
    
    def __init__(self, celery_app: Celery = None):
        self.celery_app = celery_app
        self.default_timeout = 3600  # 1 hour
        self.max_retries = 3
        self.retry_delay = 60  # 1 minute
    
    def create_task(self, 
                   name: str,
                   task_type: TaskType,
                   data: Dict[str, Any],
                   created_by: str,
                   description: str = None,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   queue_name: str = 'default',
                   scheduled_at: datetime = None,
                   timeout: int = None,
                   max_retries: int = None,
                   dependencies: List[str] = None,
                   tags: List[str] = None) -> Dict[str, Any]:
        """
        Create a new task.
        
        Args:
            name (str): Task name
            task_type (TaskType): Task type
            data (Dict[str, Any]): Task data
            created_by (str): Creator user ID
            description (str, optional): Task description
            priority (TaskPriority): Task priority
            queue_name (str): Queue name
            scheduled_at (datetime, optional): Scheduled execution time
            timeout (int, optional): Task timeout in seconds
            max_retries (int, optional): Maximum retry attempts
            dependencies (List[str], optional): Task dependencies
            tags (List[str], optional): Task tags
            
        Returns:
            Dict[str, Any]: Created task info
            
        Raises:
            TaskError: If task creation fails
        """
        try:
            # Validate creator
            creator = User.get_by_id(created_by)
            if not creator:
                raise TaskError("Creator user not found")
            
            # Validate queue
            queue = TaskQueue.get_by_name(queue_name)
            if not queue:
                raise TaskError(f"Queue '{queue_name}' not found")
            
            if not queue.is_active:
                raise TaskError(f"Queue '{queue_name}' is not active")
            
            # Validate dependencies
            if dependencies:
                for dep_id in dependencies:
                    dep_task = Task.get_by_id(dep_id)
                    if not dep_task:
                        raise TaskError(f"Dependency task '{dep_id}' not found")
            
            # Create task
            task = Task.create(
                name=name,
                description=description,
                type=task_type,
                data=data,
                priority=priority,
                queue_name=queue_name,
                scheduled_at=scheduled_at,
                timeout=timeout or self.default_timeout,
                max_retries=max_retries or self.max_retries,
                created_by=created_by,
                tags=tags or []
            )
            
            # Add dependencies
            if dependencies:
                for dep_id in dependencies:
                    task.add_dependency(dep_id)
            
            # Submit to queue if not scheduled
            if not scheduled_at or scheduled_at <= datetime.now():
                self._submit_task(task)
            
            current_app.logger.info(f"Task created: {task.id} ({name}) by {created_by}")
            
            return {
                'success': True,
                'message': 'Task created successfully',
                'task': task.to_dict()
            }
            
        except Exception as e:
            current_app.logger.error(f"Task creation error: {str(e)}")
            raise TaskError(str(e))
    
    def get_task(self, task_id: str, user_id: str = None) -> Dict[str, Any]:
        """
        Get task information.
        
        Args:
            task_id (str): Task ID
            user_id (str, optional): User ID for access control
            
        Returns:
            Dict[str, Any]: Task information
        """
        try:
            task = Task.get_by_id(task_id)
            if not task:
                return {
                    'success': False,
                    'message': 'Task not found'
                }
            
            # Check access if user_id provided
            if user_id and task.created_by != user_id and task.assigned_to != user_id:
                # Check if user is admin or has task view permission
                user = User.get_by_id(user_id)
                if not user or not user.is_superuser:
                    return {
                        'success': False,
                        'message': 'Access denied'
                    }
            
            # Get Celery task status if available
            celery_status = None
            if task.celery_task_id and self.celery_app:
                try:
                    celery_result = AsyncResult(task.celery_task_id, app=self.celery_app)
                    celery_status = {
                        'state': celery_result.state,
                        'info': celery_result.info,
                        'traceback': celery_result.traceback
                    }
                except Exception as e:
                    current_app.logger.warning(f"Failed to get Celery status for task {task_id}: {str(e)}")
            
            task_dict = task.to_dict()
            if celery_status:
                task_dict['celery_status'] = celery_status
            
            return {
                'success': True,
                'task': task_dict
            }
            
        except Exception as e:
            current_app.logger.error(f"Get task error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to get task information'
            }
    
    def update_task_progress(self, task_id: str, progress: int, message: str = None) -> bool:
        """
        Update task progress.
        
        Args:
            task_id (str): Task ID
            progress (int): Progress percentage (0-100)
            message (str, optional): Progress message
            
        Returns:
            bool: True if update successful
        """
        try:
            task = Task.get_by_id(task_id)
            if not task:
                return False
            
            task.update_progress(progress, message)
            
            current_app.logger.debug(f"Task progress updated: {task_id} - {progress}%")
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Update task progress error: {str(e)}")
            return False
    
    def complete_task(self, task_id: str, result: Dict[str, Any] = None) -> bool:
        """
        Mark task as completed.
        
        Args:
            task_id (str): Task ID
            result (Dict[str, Any], optional): Task result
            
        Returns:
            bool: True if completion successful
        """
        try:
            task = Task.get_by_id(task_id)
            if not task:
                return False
            
            task.complete(result)
            
            # Update queue statistics
            queue = TaskQueue.get_by_name(task.queue_name)
            if queue:
                queue.update_stats()
            
            # Update worker statistics
            if task.worker_node_id:
                worker = WorkerNode.get_by_worker_id(task.worker_node_id)
                if worker:
                    worker.record_task_completion(True)
            
            current_app.logger.info(f"Task completed: {task_id}")
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Complete task error: {str(e)}")
            return False
    
    def fail_task(self, task_id: str, error: str, retry: bool = True) -> bool:
        """
        Mark task as failed.
        
        Args:
            task_id (str): Task ID
            error (str): Error message
            retry (bool): Whether to retry the task
            
        Returns:
            bool: True if failure handling successful
        """
        try:
            task = Task.get_by_id(task_id)
            if not task:
                return False
            
            # Check if task should be retried
            if retry and task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.error_message = f"Retry {task.retry_count}/{task.max_retries}: {error}"
                task.save()
                
                # Reschedule task
                retry_at = datetime.now() + timedelta(seconds=self.retry_delay * task.retry_count)
                task.scheduled_at = retry_at
                task.save()
                
                current_app.logger.info(f"Task scheduled for retry: {task_id} (attempt {task.retry_count})")
                
                return True
            else:
                # Mark as failed
                task.fail(error)
                
                # Update queue statistics
                queue = TaskQueue.get_by_name(task.queue_name)
                if queue:
                    queue.update_stats()
                
                # Update worker statistics
                if task.worker_node_id:
                    worker = WorkerNode.get_by_worker_id(task.worker_node_id)
                    if worker:
                        worker.record_task_completion(False)
                
                current_app.logger.error(f"Task failed: {task_id} - {error}")
                
                return True
            
        except Exception as e:
            current_app.logger.error(f"Fail task error: {str(e)}")
            return False
    
    def cancel_task(self, task_id: str, user_id: str = None) -> Dict[str, Any]:
        """
        Cancel a task.
        
        Args:
            task_id (str): Task ID
            user_id (str, optional): User ID for access control
            
        Returns:
            Dict[str, Any]: Cancellation result
        """
        try:
            task = Task.get_by_id(task_id)
            if not task:
                return {
                    'success': False,
                    'message': 'Task not found'
                }
            
            # Check access
            if user_id and task.created_by != user_id:
                user = User.get_by_id(user_id)
                if not user or not user.is_superuser:
                    return {
                        'success': False,
                        'message': 'Access denied'
                    }
            
            # Check if task can be cancelled
            if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                return {
                    'success': False,
                    'message': f'Cannot cancel task in {task.status.value} status'
                }
            
            # Cancel Celery task if exists
            if task.celery_task_id and self.celery_app:
                try:
                    self.celery_app.control.revoke(task.celery_task_id, terminate=True)
                except Exception as e:
                    current_app.logger.warning(f"Failed to revoke Celery task {task.celery_task_id}: {str(e)}")
            
            # Mark task as cancelled
            task.cancel()
            
            current_app.logger.info(f"Task cancelled: {task_id} by {user_id}")
            
            return {
                'success': True,
                'message': 'Task cancelled successfully'
            }
            
        except Exception as e:
            current_app.logger.error(f"Cancel task error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to cancel task'
            }
    
    def get_user_tasks(self, 
                      user_id: str,
                      status: TaskStatus = None,
                      task_type: TaskType = None,
                      page: int = 1,
                      per_page: int = 20) -> Dict[str, Any]:
        """
        Get user's tasks.
        
        Args:
            user_id (str): User ID
            status (TaskStatus, optional): Filter by status
            task_type (TaskType, optional): Filter by type
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            Dict[str, Any]: User tasks
        """
        try:
            results = Task.get_by_user(
                user_id=user_id,
                status=status,
                task_type=task_type,
                page=page,
                per_page=per_page
            )
            
            return {
                'success': True,
                'tasks': [task.to_dict() for task in results['tasks']],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': results['total'],
                    'pages': results['pages']
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Get user tasks error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to get user tasks',
                'tasks': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0
                }
            }
    
    def get_queue_status(self, queue_name: str = None) -> Dict[str, Any]:
        """
        Get queue status information.
        
        Args:
            queue_name (str, optional): Specific queue name
            
        Returns:
            Dict[str, Any]: Queue status
        """
        try:
            if queue_name:
                queue = TaskQueue.get_by_name(queue_name)
                if not queue:
                    return {
                        'success': False,
                        'message': 'Queue not found'
                    }
                
                return {
                    'success': True,
                    'queue': self._get_queue_info(queue)
                }
            else:
                # Get all active queues
                queues = TaskQueue.get_active_queues()
                return {
                    'success': True,
                    'queues': [self._get_queue_info(queue) for queue in queues]
                }
                
        except Exception as e:
            current_app.logger.error(f"Get queue status error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to get queue status'
            }
    
    def get_worker_status(self, worker_id: str = None) -> Dict[str, Any]:
        """
        Get worker status information.
        
        Args:
            worker_id (str, optional): Specific worker ID
            
        Returns:
            Dict[str, Any]: Worker status
        """
        try:
            if worker_id:
                worker = WorkerNode.get_by_worker_id(worker_id)
                if not worker:
                    return {
                        'success': False,
                        'message': 'Worker not found'
                    }
                
                return {
                    'success': True,
                    'worker': self._get_worker_info(worker)
                }
            else:
                # Get all available workers
                workers = WorkerNode.get_available_workers()
                return {
                    'success': True,
                    'workers': [self._get_worker_info(worker) for worker in workers]
                }
                
        except Exception as e:
            current_app.logger.error(f"Get worker status error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to get worker status'
            }
    
    def get_task_statistics(self, 
                           start_date: datetime = None,
                           end_date: datetime = None) -> Dict[str, Any]:
        """
        Get task processing statistics.
        
        Args:
            start_date (datetime, optional): Start date
            end_date (datetime, optional): End date
            
        Returns:
            Dict[str, Any]: Task statistics
        """
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=7)
            if not end_date:
                end_date = datetime.now()
            
            # Build query
            query = Task.select().where(
                Task.created_at.between(start_date, end_date)
            )
            
            stats = {
                'total_tasks': query.count(),
                'by_status': {},
                'by_type': {},
                'by_queue': {},
                'success_rate': 0,
                'average_execution_time': 0,
                'average_wait_time': 0
            }
            
            # Count by status
            for status in TaskStatus:
                count = query.where(Task.status == status).count()
                stats['by_status'][status.value] = count
            
            # Count by type
            for task_type in TaskType:
                count = query.where(Task.type == task_type).count()
                stats['by_type'][task_type.value] = count
            
            # Count by queue
            queues = TaskQueue.select()
            for queue in queues:
                count = query.where(Task.queue_name == queue.name).count()
                stats['by_queue'][queue.name] = count
            
            # Calculate success rate
            completed_count = stats['by_status'].get('completed', 0)
            failed_count = stats['by_status'].get('failed', 0)
            total_finished = completed_count + failed_count
            
            if total_finished > 0:
                stats['success_rate'] = (completed_count / total_finished) * 100
            
            # Calculate average times
            completed_tasks = query.where(
                (Task.status == TaskStatus.COMPLETED) &
                (Task.started_at.is_null(False)) &
                (Task.completed_at.is_null(False))
            )
            
            total_execution_time = 0
            total_wait_time = 0
            count = 0
            
            for task in completed_tasks:
                if task.started_at and task.completed_at:
                    execution_time = (task.completed_at - task.started_at).total_seconds()
                    total_execution_time += execution_time
                    
                    wait_time = (task.started_at - task.created_at).total_seconds()
                    total_wait_time += wait_time
                    
                    count += 1
            
            if count > 0:
                stats['average_execution_time'] = total_execution_time / count
                stats['average_wait_time'] = total_wait_time / count
            
            return {
                'success': True,
                'statistics': stats,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Get task statistics error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to get task statistics'
            }
    
    def process_scheduled_tasks(self) -> int:
        """
        Process scheduled tasks that are ready to run.
        
        Returns:
            int: Number of tasks processed
        """
        try:
            # Find scheduled tasks that are ready
            ready_tasks = Task.select().where(
                (Task.status == TaskStatus.PENDING) &
                (Task.scheduled_at.is_null(False)) &
                (Task.scheduled_at <= datetime.now())
            )
            
            processed_count = 0
            for task in ready_tasks:
                try:
                    # Check dependencies
                    if task.check_dependencies():
                        self._submit_task(task)
                        processed_count += 1
                except Exception as e:
                    current_app.logger.error(f"Failed to process scheduled task {task.id}: {str(e)}")
            
            if processed_count > 0:
                current_app.logger.info(f"Processed {processed_count} scheduled tasks")
            
            return processed_count
            
        except Exception as e:
            current_app.logger.error(f"Process scheduled tasks error: {str(e)}")
            return 0
    
    def _submit_task(self, task: Task) -> bool:
        """
        Submit task to processing queue.
        
        Args:
            task (Task): Task to submit
            
        Returns:
            bool: True if submission successful
        """
        try:
            # Check queue capacity
            queue = TaskQueue.get_by_name(task.queue_name)
            if not queue or not queue.can_accept_task():
                current_app.logger.warning(f"Queue '{task.queue_name}' cannot accept new tasks")
                return False
            
            # Submit to Celery if available
            if self.celery_app:
                celery_task = self.celery_app.send_task(
                    f'{task.type.value}_task',
                    args=[task.id],
                    queue=task.queue_name,
                    priority=task.priority.value,
                    time_limit=task.timeout
                )
                
                task.celery_task_id = celery_task.id
                task.start()
                
                current_app.logger.info(f"Task submitted to Celery: {task.id} (celery_id: {celery_task.id})")
            else:
                # Mark as started (for non-Celery processing)
                task.start()
                current_app.logger.info(f"Task marked as started: {task.id}")
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Submit task error: {str(e)}")
            return False
    
    def _get_queue_info(self, queue: TaskQueue) -> Dict[str, Any]:
        """
        Get detailed queue information.
        
        Args:
            queue (TaskQueue): Queue instance
            
        Returns:
            Dict[str, Any]: Queue information
        """
        queue_dict = queue.to_dict()
        
        # Add current task counts
        queue_dict['current_stats'] = {
            'pending_tasks': queue.get_pending_count(),
            'running_tasks': queue.get_running_count(),
            'success_rate': queue.get_success_rate()
        }
        
        return queue_dict
    
    def _get_worker_info(self, worker: WorkerNode) -> Dict[str, Any]:
        """
        Get detailed worker information.
        
        Args:
            worker (WorkerNode): Worker instance
            
        Returns:
            Dict[str, Any]: Worker information
        """
        worker_dict = worker.to_dict()
        
        # Add current status
        worker_dict['current_stats'] = {
            'is_online': worker.is_online,
            'current_tasks': worker.get_current_task_count(),
            'can_accept_tasks': worker.can_accept_task(),
            'success_rate': worker.get_success_rate(),
            'average_processing_time': worker.get_average_processing_time()
        }
        
        return worker_dict
    
    @staticmethod
    def cleanup_old_tasks(days: int = 30) -> Dict[str, int]:
        """
        Clean up old completed/failed tasks.
        
        Args:
            days (int): Number of days to keep tasks
            
        Returns:
            Dict[str, int]: Cleanup statistics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Clean up old tasks
            old_tasks = Task.select().where(
                (Task.completed_at < cutoff_date) &
                (Task.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]))
            )
            
            tasks_cleaned = 0
            for task in old_tasks:
                task.delete_instance()
                tasks_cleaned += 1
            
            # Clean up offline workers
            offline_workers = WorkerNode.cleanup_offline_workers()
            
            current_app.logger.info(
                f"Task cleanup completed: {tasks_cleaned} tasks, {offline_workers} workers"
            )
            
            return {
                'tasks_cleaned': tasks_cleaned,
                'workers_cleaned': offline_workers
            }
            
        except Exception as e:
            current_app.logger.error(f"Task cleanup error: {str(e)}")
            return {
                'tasks_cleaned': 0,
                'workers_cleaned': 0
            }