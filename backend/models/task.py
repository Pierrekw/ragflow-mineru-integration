#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task models for Ragflow-MinerU Integration

This module contains task-related database models for document processing and job management.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from peewee import *

from backend.models.base import BaseModel, SoftDeleteModel, JSONField, StatusMixin


class TaskType(Enum):
    """Task type enumeration."""
    DOCUMENT_PARSE = 'document_parse'
    DOCUMENT_EXTRACT = 'document_extract'
    DOCUMENT_CONVERT = 'document_convert'
    BATCH_PROCESS = 'batch_process'
    SYSTEM_MAINTENANCE = 'system_maintenance'
    USER_EXPORT = 'user_export'
    DATA_MIGRATION = 'data_migration'
    OTHER = 'other'


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = 'pending'
    QUEUED = 'queued'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    RETRY = 'retry'
    TIMEOUT = 'timeout'


class TaskPriority(Enum):
    """Task priority enumeration."""
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'


class Task(BaseModel, StatusMixin):
    """Task model for managing background jobs and document processing tasks."""
    
    # Basic task information
    name = CharField(max_length=255, index=True)
    description = TextField(null=True)
    task_type = CharField(max_length=50, default=TaskType.OTHER.value, index=True)
    
    # Task configuration
    task_data = JSONField(default=dict)  # Input data for the task
    task_config = JSONField(default=dict)  # Task configuration parameters
    
    # Task execution
    celery_task_id = CharField(max_length=255, null=True, unique=True, index=True)
    worker_id = CharField(max_length=100, null=True, index=True)
    queue_name = CharField(max_length=50, default='default', index=True)
    
    # Task status and progress
    task_status = CharField(max_length=20, default=TaskStatus.PENDING.value, index=True)
    priority = CharField(max_length=20, default=TaskPriority.NORMAL.value, index=True)
    progress = IntegerField(default=0)  # 0-100
    
    # Timing information
    scheduled_at = DateTimeField(null=True, index=True)  # When task should run
    started_at = DateTimeField(null=True, index=True)
    completed_at = DateTimeField(null=True, index=True)
    
    # Retry configuration
    max_retries = IntegerField(default=3)
    retry_count = IntegerField(default=0)
    retry_delay = IntegerField(default=60)  # Seconds
    
    # Timeout configuration
    timeout_seconds = IntegerField(null=True)
    
    # Results and errors
    result = JSONField(default=dict)
    error_message = TextField(null=True)
    error_traceback = TextField(null=True)
    
    # Ownership and access
    created_by = CharField(max_length=36, index=True)
    assigned_to = CharField(max_length=36, null=True, index=True)
    
    # Dependencies
    depends_on = JSONField(default=list)  # List of task IDs this task depends on
    
    # Resource requirements
    cpu_requirement = FloatField(default=1.0)
    memory_requirement = IntegerField(default=512)  # MB
    gpu_requirement = BooleanField(default=False)
    
    # Metadata
    tags = JSONField(default=list)
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'task'
        indexes = (
            (('task_status', 'priority', 'created_at'), False),
            (('created_by', 'task_status'), False),
            (('queue_name', 'task_status'), False),
            (('scheduled_at', 'task_status'), False),
            (('celery_task_id',), True),
        )
    
    @property
    def creator(self):
        """Get task creator."""
        from backend.models.user import User
        try:
            return User.get_by_id(self.created_by)
        except User.DoesNotExist:
            return None
    
    @property
    def assignee(self):
        """Get task assignee."""
        if not self.assigned_to:
            return None
        
        from backend.models.user import User
        try:
            return User.get_by_id(self.assigned_to)
        except User.DoesNotExist:
            return None
    
    @property
    def is_pending(self) -> bool:
        """Check if task is pending."""
        return self.task_status in [TaskStatus.PENDING.value, TaskStatus.QUEUED.value]
    
    @property
    def is_running(self) -> bool:
        """Check if task is running."""
        return self.task_status == TaskStatus.RUNNING.value
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.task_status == TaskStatus.COMPLETED.value
    
    @property
    def is_failed(self) -> bool:
        """Check if task is failed."""
        return self.task_status in [TaskStatus.FAILED.value, TaskStatus.TIMEOUT.value]
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.is_failed and self.retry_count < self.max_retries
    
    @property
    def execution_time(self) -> Optional[timedelta]:
        """Get task execution time."""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now()
        return end_time - self.started_at
    
    @property
    def wait_time(self) -> Optional[timedelta]:
        """Get task wait time (from creation to start)."""
        if not self.started_at:
            return datetime.now() - self.created_at
        
        return self.started_at - self.created_at
    
    def start_task(self, worker_id: str = None, celery_task_id: str = None) -> None:
        """
        Mark task as started.
        
        Args:
            worker_id (str, optional): Worker ID executing the task
            celery_task_id (str, optional): Celery task ID
        """
        self.task_status = TaskStatus.RUNNING.value
        self.started_at = datetime.now()
        self.progress = 0
        
        if worker_id:
            self.worker_id = worker_id
        
        if celery_task_id:
            self.celery_task_id = celery_task_id
        
        self.save()
    
    def complete_task(self, result: Dict = None) -> None:
        """
        Mark task as completed.
        
        Args:
            result (Dict, optional): Task result data
        """
        self.task_status = TaskStatus.COMPLETED.value
        self.completed_at = datetime.now()
        self.progress = 100
        self.error_message = None
        self.error_traceback = None
        
        if result:
            self.result = result
        
        self.save()
    
    def fail_task(self, error: str, traceback: str = None, can_retry: bool = True) -> None:
        """
        Mark task as failed.
        
        Args:
            error (str): Error message
            traceback (str, optional): Error traceback
            can_retry (bool): Whether task can be retried
        """
        self.error_message = error
        self.error_traceback = traceback
        
        if can_retry and self.can_retry:
            self.task_status = TaskStatus.RETRY.value
            self.retry_count += 1
        else:
            self.task_status = TaskStatus.FAILED.value
            self.completed_at = datetime.now()
        
        self.save()
    
    def cancel_task(self, reason: str = None) -> None:
        """
        Cancel the task.
        
        Args:
            reason (str, optional): Cancellation reason
        """
        self.task_status = TaskStatus.CANCELLED.value
        self.completed_at = datetime.now()
        
        if reason:
            self.error_message = f"Cancelled: {reason}"
        
        self.save()
    
    def timeout_task(self) -> None:
        """
        Mark task as timed out.
        """
        self.task_status = TaskStatus.TIMEOUT.value
        self.completed_at = datetime.now()
        self.error_message = "Task execution timed out"
        self.save()
    
    def update_progress(self, progress: int, message: str = None) -> None:
        """
        Update task progress.
        
        Args:
            progress (int): Progress percentage (0-100)
            message (str, optional): Progress message
        """
        self.progress = max(0, min(100, progress))
        
        if message:
            if not isinstance(self.metadata, dict):
                self.metadata = {}
            self.metadata['progress_message'] = message
        
        self.save()
    
    def add_dependency(self, task_id: str) -> None:
        """
        Add task dependency.
        
        Args:
            task_id (str): ID of task this task depends on
        """
        if not isinstance(self.depends_on, list):
            self.depends_on = []
        
        if task_id not in self.depends_on:
            self.depends_on.append(task_id)
            self.save()
    
    def remove_dependency(self, task_id: str) -> None:
        """
        Remove task dependency.
        
        Args:
            task_id (str): ID of task to remove from dependencies
        """
        if isinstance(self.depends_on, list) and task_id in self.depends_on:
            self.depends_on.remove(task_id)
            self.save()
    
    def check_dependencies(self) -> bool:
        """
        Check if all dependencies are completed.
        
        Returns:
            bool: True if all dependencies are completed
        """
        if not isinstance(self.depends_on, list) or not self.depends_on:
            return True
        
        for task_id in self.depends_on:
            try:
                dep_task = Task.get_by_id(task_id)
                if not dep_task.is_completed:
                    return False
            except Task.DoesNotExist:
                # Dependency task not found, consider it completed
                continue
        
        return True
    
    def add_tag(self, tag: str) -> None:
        """
        Add tag to task.
        
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
        Remove tag from task.
        
        Args:
            tag (str): Tag to remove
        """
        if isinstance(self.tags, list):
            tag = tag.strip().lower()
            if tag in self.tags:
                self.tags.remove(tag)
                self.save()
    
    @classmethod
    def get_by_celery_id(cls, celery_task_id: str) -> Optional['Task']:
        """
        Get task by Celery task ID.
        
        Args:
            celery_task_id (str): Celery task ID
            
        Returns:
            Task: Task instance or None
        """
        try:
            return cls.get(cls.celery_task_id == celery_task_id)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_pending_tasks(cls, queue_name: str = None, limit: int = 100) -> List['Task']:
        """
        Get pending tasks ready for execution.
        
        Args:
            queue_name (str, optional): Filter by queue name
            limit (int): Maximum number of tasks to return
            
        Returns:
            List[Task]: List of pending tasks
        """
        query = cls.select().where(
            cls.task_status.in_([TaskStatus.PENDING.value, TaskStatus.QUEUED.value, TaskStatus.RETRY.value])
        )
        
        if queue_name:
            query = query.where(cls.queue_name == queue_name)
        
        # Filter by scheduled time
        now = datetime.now()
        query = query.where(
            (cls.scheduled_at.is_null()) |
            (cls.scheduled_at <= now)
        )
        
        # Order by priority and creation time
        priority_order = {
            TaskPriority.URGENT.value: 1,
            TaskPriority.HIGH.value: 2,
            TaskPriority.NORMAL.value: 3,
            TaskPriority.LOW.value: 4
        }
        
        tasks = list(query.order_by(cls.created_at.asc()).limit(limit))
        
        # Sort by priority
        tasks.sort(key=lambda t: (priority_order.get(t.priority, 5), t.created_at))
        
        # Filter tasks with satisfied dependencies
        ready_tasks = []
        for task in tasks:
            if task.check_dependencies():
                ready_tasks.append(task)
        
        return ready_tasks
    
    @classmethod
    def get_running_tasks(cls, worker_id: str = None) -> List['Task']:
        """
        Get currently running tasks.
        
        Args:
            worker_id (str, optional): Filter by worker ID
            
        Returns:
            List[Task]: List of running tasks
        """
        query = cls.select().where(cls.task_status == TaskStatus.RUNNING.value)
        
        if worker_id:
            query = query.where(cls.worker_id == worker_id)
        
        return list(query.order_by(cls.started_at.asc()))
    
    @classmethod
    def get_user_tasks(cls, user_id: str, status: str = None, limit: int = 50) -> List['Task']:
        """
        Get tasks for a specific user.
        
        Args:
            user_id (str): User ID
            status (str, optional): Filter by task status
            limit (int): Maximum number of tasks to return
            
        Returns:
            List[Task]: List of user tasks
        """
        query = cls.select().where(
            (cls.created_by == user_id) |
            (cls.assigned_to == user_id)
        )
        
        if status:
            query = query.where(cls.task_status == status)
        
        return list(query.order_by(cls.created_at.desc()).limit(limit))
    
    @classmethod
    def cleanup_old_tasks(cls, days: int = 30) -> int:
        """
        Clean up old completed/failed tasks.
        
        Args:
            days (int): Number of days to keep tasks
            
        Returns:
            int: Number of cleaned up tasks
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        old_tasks = cls.select().where(
            (cls.task_status.in_([
                TaskStatus.COMPLETED.value,
                TaskStatus.FAILED.value,
                TaskStatus.CANCELLED.value,
                TaskStatus.TIMEOUT.value
            ])) &
            (cls.completed_at < cutoff_date)
        )
        
        count = old_tasks.count()
        
        # Delete old tasks
        cls.delete().where(
            cls.id.in_([task.id for task in old_tasks])
        ).execute()
        
        return count
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert task to dictionary.
        
        Args:
            include_sensitive (bool): Whether to include sensitive fields
            
        Returns:
            Dict[str, Any]: Task data dictionary
        """
        exclude_fields = []
        if not include_sensitive:
            exclude_fields.extend(['error_traceback', 'task_data'])
        
        data = super().to_dict(exclude=exclude_fields)
        
        # Add computed fields
        data['is_pending'] = self.is_pending
        data['is_running'] = self.is_running
        data['is_completed'] = self.is_completed
        data['is_failed'] = self.is_failed
        data['can_retry'] = self.can_retry
        
        if self.execution_time:
            data['execution_time_seconds'] = self.execution_time.total_seconds()
        
        if self.wait_time:
            data['wait_time_seconds'] = self.wait_time.total_seconds()
        
        # Add creator information
        if self.creator:
            data['creator'] = {
                'id': self.creator.id,
                'username': self.creator.username,
                'display_name': self.creator.display_name
            }
        
        # Add assignee information
        if self.assignee:
            data['assignee'] = {
                'id': self.assignee.id,
                'username': self.assignee.username,
                'display_name': self.assignee.display_name
            }
        
        return data
    
    def __str__(self) -> str:
        return f"Task: {self.name} ({self.task_status})"


class TaskQueue(BaseModel):
    """Task queue model for managing different processing queues."""
    
    name = CharField(max_length=50, unique=True, index=True)
    display_name = CharField(max_length=100)
    description = TextField(null=True)
    
    # Queue configuration
    max_workers = IntegerField(default=1)
    max_tasks_per_worker = IntegerField(default=1)
    priority = IntegerField(default=0, index=True)
    
    # Resource limits
    max_cpu = FloatField(null=True)
    max_memory = IntegerField(null=True)  # MB
    requires_gpu = BooleanField(default=False)
    
    # Queue status
    is_active = BooleanField(default=True, index=True)
    is_paused = BooleanField(default=False)
    
    # Statistics
    total_tasks = IntegerField(default=0)
    completed_tasks = IntegerField(default=0)
    failed_tasks = IntegerField(default=0)
    
    # Timing
    last_task_at = DateTimeField(null=True)
    
    class Meta:
        table_name = 'task_queue'
        indexes = (
            (('name',), True),
            (('is_active', 'priority'), False),
        )
    
    @property
    def pending_tasks_count(self) -> int:
        """Get number of pending tasks in this queue."""
        return Task.select().where(
            (Task.queue_name == self.name) &
            (Task.task_status.in_([
                TaskStatus.PENDING.value,
                TaskStatus.QUEUED.value,
                TaskStatus.RETRY.value
            ]))
        ).count()
    
    @property
    def running_tasks_count(self) -> int:
        """Get number of running tasks in this queue."""
        return Task.select().where(
            (Task.queue_name == self.name) &
            (Task.task_status == TaskStatus.RUNNING.value)
        ).count()
    
    @property
    def success_rate(self) -> float:
        """Get queue success rate."""
        if self.total_tasks == 0:
            return 0.0
        
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def can_accept_tasks(self) -> bool:
        """Check if queue can accept new tasks."""
        if not self.is_active or self.is_paused:
            return False
        
        # Check if queue has capacity
        running_count = self.running_tasks_count
        max_concurrent = self.max_workers * self.max_tasks_per_worker
        
        return running_count < max_concurrent
    
    def update_statistics(self) -> None:
        """
        Update queue statistics.
        """
        tasks = Task.select().where(Task.queue_name == self.name)
        
        self.total_tasks = tasks.count()
        self.completed_tasks = tasks.where(
            Task.task_status == TaskStatus.COMPLETED.value
        ).count()
        self.failed_tasks = tasks.where(
            Task.task_status.in_([
                TaskStatus.FAILED.value,
                TaskStatus.TIMEOUT.value,
                TaskStatus.CANCELLED.value
            ])
        ).count()
        
        # Get last task time
        last_task = tasks.order_by(Task.created_at.desc()).first()
        if last_task:
            self.last_task_at = last_task.created_at
        
        self.save()
    
    def pause_queue(self) -> None:
        """
        Pause the queue.
        """
        self.is_paused = True
        self.save()
    
    def resume_queue(self) -> None:
        """
        Resume the queue.
        """
        self.is_paused = False
        self.save()
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional['TaskQueue']:
        """
        Get queue by name.
        
        Args:
            name (str): Queue name
            
        Returns:
            TaskQueue: Queue instance or None
        """
        try:
            return cls.get(cls.name == name)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_active_queues(cls) -> List['TaskQueue']:
        """
        Get all active queues.
        
        Returns:
            List[TaskQueue]: List of active queues
        """
        return list(
            cls.select().where(
                (cls.is_active == True) &
                (cls.is_paused == False)
            ).order_by(cls.priority.desc(), cls.name.asc())
        )
    
    def __str__(self) -> str:
        return f"Queue: {self.display_name} ({self.name})"


class WorkerNode(BaseModel):
    """Worker node model for tracking processing workers."""
    
    # Worker identification
    worker_id = CharField(max_length=100, unique=True, index=True)
    hostname = CharField(max_length=255, index=True)
    process_id = IntegerField(null=True)
    
    # Worker configuration
    queue_names = JSONField(default=list)  # Queues this worker processes
    max_concurrent_tasks = IntegerField(default=1)
    
    # Resource information
    cpu_cores = IntegerField(null=True)
    memory_total = IntegerField(null=True)  # MB
    memory_available = IntegerField(null=True)  # MB
    gpu_available = BooleanField(default=False)
    gpu_info = JSONField(default=dict)
    
    # Worker status
    is_active = BooleanField(default=True, index=True)
    is_busy = BooleanField(default=False)
    last_heartbeat = DateTimeField(default=datetime.now, index=True)
    
    # Statistics
    tasks_processed = IntegerField(default=0)
    tasks_failed = IntegerField(default=0)
    total_processing_time = IntegerField(default=0)  # Seconds
    
    # Version and metadata
    worker_version = CharField(max_length=50, null=True)
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'worker_node'
        indexes = (
            (('worker_id',), True),
            (('is_active', 'last_heartbeat'), False),
            (('hostname', 'is_active'), False),
        )
    
    @property
    def is_online(self) -> bool:
        """
        Check if worker is online (recent heartbeat).
        
        Returns:
            bool: True if worker is online
        """
        if not self.is_active:
            return False
        
        # Consider worker offline if no heartbeat in last 5 minutes
        threshold = datetime.now() - timedelta(minutes=5)
        return self.last_heartbeat > threshold
    
    @property
    def current_tasks_count(self) -> int:
        """
        Get number of currently running tasks on this worker.
        
        Returns:
            int: Number of running tasks
        """
        return Task.select().where(
            (Task.worker_id == self.worker_id) &
            (Task.task_status == TaskStatus.RUNNING.value)
        ).count()
    
    @property
    def can_accept_tasks(self) -> bool:
        """
        Check if worker can accept new tasks.
        
        Returns:
            bool: True if worker can accept tasks
        """
        if not self.is_online or self.is_busy:
            return False
        
        return self.current_tasks_count < self.max_concurrent_tasks
    
    @property
    def success_rate(self) -> float:
        """
        Get worker success rate.
        
        Returns:
            float: Success rate percentage
        """
        if self.tasks_processed == 0:
            return 0.0
        
        successful_tasks = self.tasks_processed - self.tasks_failed
        return (successful_tasks / self.tasks_processed) * 100
    
    @property
    def average_processing_time(self) -> float:
        """
        Get average processing time per task.
        
        Returns:
            float: Average processing time in seconds
        """
        if self.tasks_processed == 0:
            return 0.0
        
        return self.total_processing_time / self.tasks_processed
    
    def update_heartbeat(self, metadata: Dict = None) -> None:
        """
        Update worker heartbeat.
        
        Args:
            metadata (Dict, optional): Additional metadata to update
        """
        self.last_heartbeat = datetime.now()
        
        if metadata:
            if not isinstance(self.metadata, dict):
                self.metadata = {}
            self.metadata.update(metadata)
        
        self.save()
    
    def update_resources(self, 
                        memory_available: int = None,
                        cpu_usage: float = None,
                        gpu_info: Dict = None) -> None:
        """
        Update worker resource information.
        
        Args:
            memory_available (int, optional): Available memory in MB
            cpu_usage (float, optional): CPU usage percentage
            gpu_info (Dict, optional): GPU information
        """
        if memory_available is not None:
            self.memory_available = memory_available
        
        if cpu_usage is not None:
            if not isinstance(self.metadata, dict):
                self.metadata = {}
            self.metadata['cpu_usage'] = cpu_usage
        
        if gpu_info is not None:
            self.gpu_info = gpu_info
        
        self.save()
    
    def record_task_completion(self, success: bool, processing_time: int) -> None:
        """
        Record task completion statistics.
        
        Args:
            success (bool): Whether task completed successfully
            processing_time (int): Processing time in seconds
        """
        self.tasks_processed += 1
        self.total_processing_time += processing_time
        
        if not success:
            self.tasks_failed += 1
        
        self.save()
    
    def set_busy(self, busy: bool = True) -> None:
        """
        Set worker busy status.
        
        Args:
            busy (bool): Whether worker is busy
        """
        self.is_busy = busy
        self.save()
    
    def deactivate(self) -> None:
        """
        Deactivate the worker.
        """
        self.is_active = False
        self.save()
    
    @classmethod
    def get_by_worker_id(cls, worker_id: str) -> Optional['WorkerNode']:
        """
        Get worker by worker ID.
        
        Args:
            worker_id (str): Worker ID
            
        Returns:
            WorkerNode: Worker instance or None
        """
        try:
            return cls.get(cls.worker_id == worker_id)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_available_workers(cls, queue_name: str = None) -> List['WorkerNode']:
        """
        Get available workers for task assignment.
        
        Args:
            queue_name (str, optional): Filter by queue name
            
        Returns:
            List[WorkerNode]: List of available workers
        """
        # Get online workers
        threshold = datetime.now() - timedelta(minutes=5)
        query = cls.select().where(
            (cls.is_active == True) &
            (cls.last_heartbeat > threshold) &
            (cls.is_busy == False)
        )
        
        workers = list(query)
        
        # Filter by queue if specified
        if queue_name:
            workers = [
                w for w in workers
                if isinstance(w.queue_names, list) and queue_name in w.queue_names
            ]
        
        # Filter workers that can accept tasks
        available_workers = [w for w in workers if w.can_accept_tasks]
        
        # Sort by load (fewer current tasks first)
        available_workers.sort(key=lambda w: w.current_tasks_count)
        
        return available_workers
    
    @classmethod
    def cleanup_offline_workers(cls, hours: int = 24) -> int:
        """
        Clean up workers that have been offline for too long.
        
        Args:
            hours (int): Hours threshold for cleanup
            
        Returns:
            int: Number of cleaned up workers
        """
        threshold = datetime.now() - timedelta(hours=hours)
        
        offline_workers = cls.select().where(
            cls.last_heartbeat < threshold
        )
        
        count = offline_workers.count()
        
        # Deactivate offline workers
        cls.update(is_active=False).where(
            cls.last_heartbeat < threshold
        ).execute()
        
        return count
    
    def __str__(self) -> str:
        return f"Worker: {self.worker_id} ({self.hostname})"