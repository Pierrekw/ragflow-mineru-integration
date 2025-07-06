#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Celery Configuration for Ragflow-MinerU Integration

This module provides Celery task queue configuration and utilities.
"""

import os
from datetime import timedelta
from celery import Celery
from kombu import Queue, Exchange
from flask import Flask


def make_celery(app: Flask) -> Celery:
    """
    Create and configure Celery instance with Flask app context.
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Celery instance
    """
    # Create Celery instance
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND'),
        broker=app.config.get('CELERY_BROKER_URL')
    )
    
    # Update Celery configuration
    celery.conf.update(
        # Basic configuration
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone=app.config.get('TIMEZONE', 'UTC'),
        enable_utc=True,
        
        # Task routing
        task_routes=get_task_routes(),
        
        # Queue configuration
        task_default_queue='default',
        task_default_exchange='default',
        task_default_exchange_type='direct',
        task_default_routing_key='default',
        
        # Worker configuration
        worker_prefetch_multiplier=app.config.get('CELERY_WORKER_PREFETCH_MULTIPLIER', 1),
        worker_max_tasks_per_child=app.config.get('CELERY_WORKER_MAX_TASKS_PER_CHILD', 1000),
        worker_disable_rate_limits=False,
        
        # Task execution
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_ignore_result=False,
        
        # Result backend configuration
        result_expires=app.config.get('CELERY_RESULT_EXPIRES', 3600),  # 1 hour
        result_persistent=True,
        
        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,
        
        # Security
        worker_hijack_root_logger=False,
        worker_log_color=False,
        
        # Beat schedule (for periodic tasks)
        beat_schedule=get_beat_schedule(),
        beat_schedule_filename='celerybeat-schedule',
        
        # Task time limits
        task_soft_time_limit=app.config.get('CELERY_TASK_SOFT_TIME_LIMIT', 300),  # 5 minutes
        task_time_limit=app.config.get('CELERY_TASK_TIME_LIMIT', 600),  # 10 minutes
        
        # Retry configuration
        task_annotations={
            '*': {
                'rate_limit': '100/m',
                'max_retries': 3,
                'default_retry_delay': 60,
            },
            'backend.tasks.document_processing.*': {
                'rate_limit': '10/m',
                'max_retries': 2,
                'default_retry_delay': 120,
            },
            'backend.tasks.mineru_processing.*': {
                'rate_limit': '5/m',
                'max_retries': 1,
                'default_retry_delay': 300,
            }
        }
    )
    
    # Configure queues
    celery.conf.task_queues = get_task_queues()
    
    # Create task base class that runs in Flask app context
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    return celery


def get_task_queues():
    """
    Define task queues configuration.
    
    Returns:
        List of Queue objects
    """
    # Define exchanges
    default_exchange = Exchange('default', type='direct')
    document_exchange = Exchange('document', type='direct')
    mineru_exchange = Exchange('mineru', type='direct')
    priority_exchange = Exchange('priority', type='direct')
    
    return [
        # Default queue for general tasks
        Queue('default', default_exchange, routing_key='default'),
        
        # Document processing queues
        Queue('document_upload', document_exchange, routing_key='document.upload'),
        Queue('document_parse', document_exchange, routing_key='document.parse'),
        Queue('document_index', document_exchange, routing_key='document.index'),
        Queue('document_cleanup', document_exchange, routing_key='document.cleanup'),
        
        # MinerU processing queues
        Queue('mineru_extract', mineru_exchange, routing_key='mineru.extract'),
        Queue('mineru_ocr', mineru_exchange, routing_key='mineru.ocr'),
        Queue('mineru_layout', mineru_exchange, routing_key='mineru.layout'),
        Queue('mineru_formula', mineru_exchange, routing_key='mineru.formula'),
        
        # Priority queues
        Queue('high_priority', priority_exchange, routing_key='priority.high'),
        Queue('low_priority', priority_exchange, routing_key='priority.low'),
        
        # System maintenance queues
        Queue('cleanup', default_exchange, routing_key='system.cleanup'),
        Queue('monitoring', default_exchange, routing_key='system.monitoring'),
    ]


def get_task_routes():
    """
    Define task routing configuration.
    
    Returns:
        Dictionary of task routes
    """
    return {
        # Document processing tasks
        'backend.tasks.document_processing.upload_document': {
            'queue': 'document_upload',
            'routing_key': 'document.upload'
        },
        'backend.tasks.document_processing.parse_document': {
            'queue': 'document_parse',
            'routing_key': 'document.parse'
        },
        'backend.tasks.document_processing.index_document': {
            'queue': 'document_index',
            'routing_key': 'document.index'
        },
        'backend.tasks.document_processing.cleanup_document': {
            'queue': 'document_cleanup',
            'routing_key': 'document.cleanup'
        },
        
        # MinerU processing tasks
        'backend.tasks.mineru_processing.extract_content': {
            'queue': 'mineru_extract',
            'routing_key': 'mineru.extract'
        },
        'backend.tasks.mineru_processing.ocr_processing': {
            'queue': 'mineru_ocr',
            'routing_key': 'mineru.ocr'
        },
        'backend.tasks.mineru_processing.layout_analysis': {
            'queue': 'mineru_layout',
            'routing_key': 'mineru.layout'
        },
        'backend.tasks.mineru_processing.formula_recognition': {
            'queue': 'mineru_formula',
            'routing_key': 'mineru.formula'
        },
        
        # System tasks
        'backend.tasks.system.cleanup_temp_files': {
            'queue': 'cleanup',
            'routing_key': 'system.cleanup'
        },
        'backend.tasks.system.health_check': {
            'queue': 'monitoring',
            'routing_key': 'system.monitoring'
        },
        
        # Default routing for unspecified tasks
        '*': {
            'queue': 'default',
            'routing_key': 'default'
        }
    }


def get_beat_schedule():
    """
    Define periodic task schedule.
    
    Returns:
        Dictionary of scheduled tasks
    """
    return {
        # Cleanup temporary files every hour
        'cleanup-temp-files': {
            'task': 'backend.tasks.system.cleanup_temp_files',
            'schedule': timedelta(hours=1),
            'options': {'queue': 'cleanup'}
        },
        
        # Health check every 5 minutes
        'health-check': {
            'task': 'backend.tasks.system.health_check',
            'schedule': timedelta(minutes=5),
            'options': {'queue': 'monitoring'}
        },
        
        # Update document statistics every 30 minutes
        'update-document-stats': {
            'task': 'backend.tasks.system.update_document_statistics',
            'schedule': timedelta(minutes=30),
            'options': {'queue': 'default'}
        },
        
        # Cleanup old task results every 6 hours
        'cleanup-old-results': {
            'task': 'backend.tasks.system.cleanup_old_task_results',
            'schedule': timedelta(hours=6),
            'options': {'queue': 'cleanup'}
        },
        
        # Check failed tasks every 15 minutes
        'check-failed-tasks': {
            'task': 'backend.tasks.system.check_failed_tasks',
            'schedule': timedelta(minutes=15),
            'options': {'queue': 'monitoring'}
        },
        
        # Generate daily reports at midnight
        'daily-report': {
            'task': 'backend.tasks.system.generate_daily_report',
            'schedule': timedelta(days=1),
            'options': {'queue': 'default'}
        }
    }


def configure_celery_logging(celery_app: Celery, app: Flask):
    """
    Configure Celery logging.
    
    Args:
        celery_app: Celery application instance
        app: Flask application instance
    """
    import logging
    from celery.utils.log import get_task_logger
    
    # Configure Celery logger
    celery_logger = get_task_logger(__name__)
    celery_logger.setLevel(app.config.get('LOG_LEVEL', 'INFO'))
    
    # Add handler if not exists
    if not celery_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        celery_logger.addHandler(handler)
    
    # Configure Celery app logging
    celery_app.conf.update(
        worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
    )


def get_celery_worker_status(celery_app: Celery) -> dict:
    """
    Get Celery worker status.
    
    Args:
        celery_app: Celery application instance
        
    Returns:
        Worker status information
    """
    try:
        # Get active workers
        inspect = celery_app.control.inspect()
        
        # Get worker stats
        stats = inspect.stats()
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        
        return {
            'workers': list(stats.keys()) if stats else [],
            'worker_count': len(stats) if stats else 0,
            'active_tasks': sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0,
            'scheduled_tasks': sum(len(tasks) for tasks in scheduled_tasks.values()) if scheduled_tasks else 0,
            'reserved_tasks': sum(len(tasks) for tasks in reserved_tasks.values()) if reserved_tasks else 0,
            'stats': stats,
            'status': 'healthy' if stats else 'no_workers'
        }
    
    except Exception as e:
        return {
            'workers': [],
            'worker_count': 0,
            'active_tasks': 0,
            'scheduled_tasks': 0,
            'reserved_tasks': 0,
            'stats': None,
            'status': 'error',
            'error': str(e)
        }


def get_queue_status(celery_app: Celery) -> dict:
    """
    Get queue status information.
    
    Args:
        celery_app: Celery application instance
        
    Returns:
        Queue status information
    """
    try:
        # Get broker connection
        with celery_app.connection() as conn:
            # Get queue lengths
            queue_info = {}
            
            for queue in get_task_queues():
                try:
                    queue_obj = conn.SimpleQueue(queue.name)
                    queue_info[queue.name] = {
                        'name': queue.name,
                        'length': queue_obj.qsize(),
                        'routing_key': queue.routing_key,
                        'exchange': queue.exchange.name
                    }
                    queue_obj.close()
                except Exception as e:
                    queue_info[queue.name] = {
                        'name': queue.name,
                        'length': -1,
                        'error': str(e)
                    }
            
            return {
                'queues': queue_info,
                'total_queues': len(queue_info),
                'status': 'healthy'
            }
    
    except Exception as e:
        return {
            'queues': {},
            'total_queues': 0,
            'status': 'error',
            'error': str(e)
        }


def purge_queue(celery_app: Celery, queue_name: str) -> dict:
    """
    Purge all messages from a queue.
    
    Args:
        celery_app: Celery application instance
        queue_name: Name of queue to purge
        
    Returns:
        Purge result information
    """
    try:
        with celery_app.connection() as conn:
            queue_obj = conn.SimpleQueue(queue_name)
            purged_count = queue_obj.clear()
            queue_obj.close()
            
            return {
                'queue': queue_name,
                'purged_count': purged_count,
                'status': 'success'
            }
    
    except Exception as e:
        return {
            'queue': queue_name,
            'purged_count': 0,
            'status': 'error',
            'error': str(e)
        }


def revoke_task(celery_app: Celery, task_id: str, terminate: bool = False) -> dict:
    """
    Revoke a task.
    
    Args:
        celery_app: Celery application instance
        task_id: Task ID to revoke
        terminate: Whether to terminate the task if it's running
        
    Returns:
        Revoke result information
    """
    try:
        celery_app.control.revoke(task_id, terminate=terminate)
        
        return {
            'task_id': task_id,
            'terminated': terminate,
            'status': 'success'
        }
    
    except Exception as e:
        return {
            'task_id': task_id,
            'terminated': False,
            'status': 'error',
            'error': str(e)
        }


def get_task_info(celery_app: Celery, task_id: str) -> dict:
    """
    Get information about a specific task.
    
    Args:
        celery_app: Celery application instance
        task_id: Task ID
        
    Returns:
        Task information
    """
    try:
        result = celery_app.AsyncResult(task_id)
        
        return {
            'task_id': task_id,
            'state': result.state,
            'result': result.result,
            'traceback': result.traceback,
            'successful': result.successful(),
            'failed': result.failed(),
            'ready': result.ready(),
            'status': 'success'
        }
    
    except Exception as e:
        return {
            'task_id': task_id,
            'state': 'UNKNOWN',
            'status': 'error',
            'error': str(e)
        }


def health_check(celery_app: Celery) -> bool:
    """
    Check Celery health.
    
    Args:
        celery_app: Celery application instance
        
    Returns:
        True if healthy, False otherwise
    """
    try:
        # Check broker connection
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=3)
        
        # Check if workers are available
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        return bool(stats)
    
    except Exception:
        return False