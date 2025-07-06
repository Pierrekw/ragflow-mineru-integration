#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Services Configuration for Ragflow-MinerU Integration

This module provides configuration for external services integration.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """
    Base service configuration.
    """
    enabled: bool = False
    host: str = 'localhost'
    port: int = 80
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1


@dataclass
class ElasticsearchConfig(ServiceConfig):
    """
    Elasticsearch service configuration.
    """
    port: int = 9200
    index_prefix: str = 'ragflow_mineru'
    use_ssl: bool = False
    verify_certs: bool = True
    ca_certs: Optional[str] = None
    client_cert: Optional[str] = None
    client_key: Optional[str] = None
    max_retries: int = 3
    sniff_on_start: bool = False
    sniff_on_connection_fail: bool = False
    sniffer_timeout: int = 60
    
    def get_hosts(self) -> List[Dict[str, Any]]:
        """
        Get Elasticsearch hosts configuration.
        
        Returns:
            List of host configurations
        """
        return [{
            'host': self.host,
            'port': self.port,
            'use_ssl': self.use_ssl,
            'verify_certs': self.verify_certs,
            'ca_certs': self.ca_certs,
            'client_cert': self.client_cert,
            'client_key': self.client_key
        }]


@dataclass
class MinIOConfig(ServiceConfig):
    """
    MinIO/S3 service configuration.
    """
    port: int = 9000
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    bucket_name: str = 'ragflow-mineru'
    region: str = 'us-east-1'
    use_ssl: bool = False
    endpoint_url: Optional[str] = None
    
    def get_endpoint_url(self) -> str:
        """
        Get MinIO endpoint URL.
        
        Returns:
            Endpoint URL
        """
        if self.endpoint_url:
            return self.endpoint_url
        
        protocol = 'https' if self.use_ssl else 'http'
        return f"{protocol}://{self.host}:{self.port}"


@dataclass
class MinerUConfig(ServiceConfig):
    """
    MinerU service configuration.
    """
    port: int = 8080
    api_version: str = 'v1'
    api_key: Optional[str] = None
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    supported_formats: List[str] = None
    processing_timeout: int = 300  # 5 minutes
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['pdf', 'docx', 'doc', 'txt', 'html']
    
    def get_api_url(self, endpoint: str = '') -> str:
        """
        Get MinerU API URL.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Full API URL
        """
        base_url = f"http://{self.host}:{self.port}/api/{self.api_version}"
        return f"{base_url}/{endpoint.lstrip('/')}"


@dataclass
class RagflowConfig(ServiceConfig):
    """
    Ragflow service configuration.
    """
    port: int = 9380
    api_version: str = 'v1'
    api_key: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    def get_api_url(self, endpoint: str = '') -> str:
        """
        Get Ragflow API URL.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Full API URL
        """
        base_url = f"http://{self.host}:{self.port}/api/{self.api_version}"
        return f"{base_url}/{endpoint.lstrip('/')}"


@dataclass
class EmailConfig(ServiceConfig):
    """
    Email service configuration.
    """
    port: int = 587
    use_tls: bool = True
    use_ssl: bool = False
    sender_email: Optional[str] = None
    sender_name: str = 'Ragflow-MinerU Integration'
    
    def get_smtp_config(self) -> Dict[str, Any]:
        """
        Get SMTP configuration.
        
        Returns:
            SMTP configuration
        """
        return {
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'use_tls': self.use_tls,
            'use_ssl': self.use_ssl,
            'timeout': self.timeout
        }


class ServicesManager:
    """
    Services configuration manager.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.elasticsearch = None
        self.minio = None
        self.mineru = None
        self.ragflow = None
        self.email = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize services with Flask app.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Load service configurations
        self._load_elasticsearch_config(app)
        self._load_minio_config(app)
        self._load_mineru_config(app)
        self._load_ragflow_config(app)
        self._load_email_config(app)
        
        # Store in app config
        app.config['SERVICES'] = self
        
        logger.info("Services configuration loaded")
    
    def _load_elasticsearch_config(self, app):
        """
        Load Elasticsearch configuration.
        
        Args:
            app: Flask application instance
        """
        self.elasticsearch = ElasticsearchConfig(
            enabled=app.config.get('ELASTICSEARCH_ENABLED', False),
            host=app.config.get('ELASTICSEARCH_HOST', 'localhost'),
            port=app.config.get('ELASTICSEARCH_PORT', 9200),
            username=app.config.get('ELASTICSEARCH_USERNAME'),
            password=app.config.get('ELASTICSEARCH_PASSWORD'),
            timeout=app.config.get('ELASTICSEARCH_TIMEOUT', 30),
            retry_attempts=app.config.get('ELASTICSEARCH_RETRY_ATTEMPTS', 3),
            retry_delay=app.config.get('ELASTICSEARCH_RETRY_DELAY', 1),
            index_prefix=app.config.get('ELASTICSEARCH_INDEX_PREFIX', 'ragflow_mineru'),
            use_ssl=app.config.get('ELASTICSEARCH_USE_SSL', False),
            verify_certs=app.config.get('ELASTICSEARCH_VERIFY_CERTS', True),
            ca_certs=app.config.get('ELASTICSEARCH_CA_CERTS'),
            client_cert=app.config.get('ELASTICSEARCH_CLIENT_CERT'),
            client_key=app.config.get('ELASTICSEARCH_CLIENT_KEY'),
            max_retries=app.config.get('ELASTICSEARCH_MAX_RETRIES', 3),
            sniff_on_start=app.config.get('ELASTICSEARCH_SNIFF_ON_START', False),
            sniff_on_connection_fail=app.config.get('ELASTICSEARCH_SNIFF_ON_CONNECTION_FAIL', False),
            sniffer_timeout=app.config.get('ELASTICSEARCH_SNIFFER_TIMEOUT', 60)
        )
    
    def _load_minio_config(self, app):
        """
        Load MinIO configuration.
        
        Args:
            app: Flask application instance
        """
        self.minio = MinIOConfig(
            enabled=app.config.get('MINIO_ENABLED', False),
            host=app.config.get('MINIO_HOST', 'localhost'),
            port=app.config.get('MINIO_PORT', 9000),
            timeout=app.config.get('MINIO_TIMEOUT', 30),
            retry_attempts=app.config.get('MINIO_RETRY_ATTEMPTS', 3),
            retry_delay=app.config.get('MINIO_RETRY_DELAY', 1),
            access_key=app.config.get('MINIO_ACCESS_KEY'),
            secret_key=app.config.get('MINIO_SECRET_KEY'),
            bucket_name=app.config.get('MINIO_BUCKET_NAME', 'ragflow-mineru'),
            region=app.config.get('MINIO_REGION', 'us-east-1'),
            use_ssl=app.config.get('MINIO_USE_SSL', False),
            endpoint_url=app.config.get('MINIO_ENDPOINT_URL')
        )
    
    def _load_mineru_config(self, app):
        """
        Load MinerU configuration.
        
        Args:
            app: Flask application instance
        """
        supported_formats = app.config.get('MINERU_SUPPORTED_FORMATS')
        if isinstance(supported_formats, str):
            supported_formats = [fmt.strip() for fmt in supported_formats.split(',')]
        
        self.mineru = MinerUConfig(
            enabled=app.config.get('MINERU_ENABLED', False),
            host=app.config.get('MINERU_HOST', 'localhost'),
            port=app.config.get('MINERU_PORT', 8080),
            timeout=app.config.get('MINERU_TIMEOUT', 30),
            retry_attempts=app.config.get('MINERU_RETRY_ATTEMPTS', 3),
            retry_delay=app.config.get('MINERU_RETRY_DELAY', 1),
            api_version=app.config.get('MINERU_API_VERSION', 'v1'),
            api_key=app.config.get('MINERU_API_KEY'),
            max_file_size=app.config.get('MINERU_MAX_FILE_SIZE', 100 * 1024 * 1024),
            supported_formats=supported_formats,
            processing_timeout=app.config.get('MINERU_PROCESSING_TIMEOUT', 300)
        )
    
    def _load_ragflow_config(self, app):
        """
        Load Ragflow configuration.
        
        Args:
            app: Flask application instance
        """
        self.ragflow = RagflowConfig(
            enabled=app.config.get('RAGFLOW_ENABLED', False),
            host=app.config.get('RAGFLOW_HOST', 'localhost'),
            port=app.config.get('RAGFLOW_PORT', 9380),
            timeout=app.config.get('RAGFLOW_TIMEOUT', 30),
            retry_attempts=app.config.get('RAGFLOW_RETRY_ATTEMPTS', 3),
            retry_delay=app.config.get('RAGFLOW_RETRY_DELAY', 1),
            api_version=app.config.get('RAGFLOW_API_VERSION', 'v1'),
            api_key=app.config.get('RAGFLOW_API_KEY'),
            knowledge_base_id=app.config.get('RAGFLOW_KNOWLEDGE_BASE_ID'),
            chunk_size=app.config.get('RAGFLOW_CHUNK_SIZE', 512),
            chunk_overlap=app.config.get('RAGFLOW_CHUNK_OVERLAP', 50)
        )
    
    def _load_email_config(self, app):
        """
        Load email configuration.
        
        Args:
            app: Flask application instance
        """
        self.email = EmailConfig(
            enabled=app.config.get('EMAIL_ENABLED', False),
            host=app.config.get('EMAIL_HOST', 'localhost'),
            port=app.config.get('EMAIL_PORT', 587),
            username=app.config.get('EMAIL_USERNAME'),
            password=app.config.get('EMAIL_PASSWORD'),
            timeout=app.config.get('EMAIL_TIMEOUT', 30),
            retry_attempts=app.config.get('EMAIL_RETRY_ATTEMPTS', 3),
            retry_delay=app.config.get('EMAIL_RETRY_DELAY', 1),
            use_tls=app.config.get('EMAIL_USE_TLS', True),
            use_ssl=app.config.get('EMAIL_USE_SSL', False),
            sender_email=app.config.get('EMAIL_SENDER_EMAIL'),
            sender_name=app.config.get('EMAIL_SENDER_NAME', 'Ragflow-MinerU Integration')
        )
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all services.
        
        Returns:
            Service status information
        """
        return {
            'elasticsearch': {
                'enabled': self.elasticsearch.enabled,
                'host': self.elasticsearch.host,
                'port': self.elasticsearch.port,
                'status': self._check_elasticsearch_status()
            },
            'minio': {
                'enabled': self.minio.enabled,
                'host': self.minio.host,
                'port': self.minio.port,
                'bucket': self.minio.bucket_name,
                'status': self._check_minio_status()
            },
            'mineru': {
                'enabled': self.mineru.enabled,
                'host': self.mineru.host,
                'port': self.mineru.port,
                'api_version': self.mineru.api_version,
                'status': self._check_mineru_status()
            },
            'ragflow': {
                'enabled': self.ragflow.enabled,
                'host': self.ragflow.host,
                'port': self.ragflow.port,
                'api_version': self.ragflow.api_version,
                'status': self._check_ragflow_status()
            },
            'email': {
                'enabled': self.email.enabled,
                'host': self.email.host,
                'port': self.email.port,
                'sender': self.email.sender_email,
                'status': self._check_email_status()
            }
        }
    
    def _check_elasticsearch_status(self) -> str:
        """
        Check Elasticsearch service status.
        
        Returns:
            Service status
        """
        if not self.elasticsearch.enabled:
            return 'disabled'
        
        try:
            import requests
            url = f"http://{self.elasticsearch.host}:{self.elasticsearch.port}/_cluster/health"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                health = response.json()
                return health.get('status', 'unknown')
            else:
                return 'error'
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return 'unreachable'
    
    def _check_minio_status(self) -> str:
        """
        Check MinIO service status.
        
        Returns:
            Service status
        """
        if not self.minio.enabled:
            return 'disabled'
        
        try:
            from minio import Minio
            client = Minio(
                f"{self.minio.host}:{self.minio.port}",
                access_key=self.minio.access_key,
                secret_key=self.minio.secret_key,
                secure=self.minio.use_ssl
            )
            # Try to list buckets
            list(client.list_buckets())
            return 'healthy'
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return 'unreachable'
    
    def _check_mineru_status(self) -> str:
        """
        Check MinerU service status.
        
        Returns:
            Service status
        """
        if not self.mineru.enabled:
            return 'disabled'
        
        try:
            import requests
            url = self.mineru.get_api_url('health')
            headers = {}
            if self.mineru.api_key:
                headers['Authorization'] = f'Bearer {self.mineru.api_key}'
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return 'healthy'
            else:
                return 'error'
        except Exception as e:
            logger.error(f"MinerU health check failed: {e}")
            return 'unreachable'
    
    def _check_ragflow_status(self) -> str:
        """
        Check Ragflow service status.
        
        Returns:
            Service status
        """
        if not self.ragflow.enabled:
            return 'disabled'
        
        try:
            import requests
            url = self.ragflow.get_api_url('health')
            headers = {}
            if self.ragflow.api_key:
                headers['Authorization'] = f'Bearer {self.ragflow.api_key}'
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return 'healthy'
            else:
                return 'error'
        except Exception as e:
            logger.error(f"Ragflow health check failed: {e}")
            return 'unreachable'
    
    def _check_email_status(self) -> str:
        """
        Check email service status.
        
        Returns:
            Service status
        """
        if not self.email.enabled:
            return 'disabled'
        
        try:
            import smtplib
            import socket
            
            # Try to connect to SMTP server
            if self.email.use_ssl:
                server = smtplib.SMTP_SSL(self.email.host, self.email.port, timeout=5)
            else:
                server = smtplib.SMTP(self.email.host, self.email.port, timeout=5)
                if self.email.use_tls:
                    server.starttls()
            
            if self.email.username and self.email.password:
                server.login(self.email.username, self.email.password)
            
            server.quit()
            return 'healthy'
        
        except Exception as e:
            logger.error(f"Email health check failed: {e}")
            return 'unreachable'
    
    def validate_configurations(self) -> Dict[str, List[str]]:
        """
        Validate all service configurations.
        
        Returns:
            Validation errors by service
        """
        errors = {}
        
        # Validate Elasticsearch
        es_errors = []
        if self.elasticsearch.enabled:
            if not self.elasticsearch.host:
                es_errors.append('Host is required')
            if not (1 <= self.elasticsearch.port <= 65535):
                es_errors.append('Port must be between 1 and 65535')
        if es_errors:
            errors['elasticsearch'] = es_errors
        
        # Validate MinIO
        minio_errors = []
        if self.minio.enabled:
            if not self.minio.host:
                minio_errors.append('Host is required')
            if not self.minio.access_key:
                minio_errors.append('Access key is required')
            if not self.minio.secret_key:
                minio_errors.append('Secret key is required')
            if not self.minio.bucket_name:
                minio_errors.append('Bucket name is required')
        if minio_errors:
            errors['minio'] = minio_errors
        
        # Validate MinerU
        mineru_errors = []
        if self.mineru.enabled:
            if not self.mineru.host:
                mineru_errors.append('Host is required')
            if not (1 <= self.mineru.port <= 65535):
                mineru_errors.append('Port must be between 1 and 65535')
        if mineru_errors:
            errors['mineru'] = mineru_errors
        
        # Validate Ragflow
        ragflow_errors = []
        if self.ragflow.enabled:
            if not self.ragflow.host:
                ragflow_errors.append('Host is required')
            if not (1 <= self.ragflow.port <= 65535):
                ragflow_errors.append('Port must be between 1 and 65535')
        if ragflow_errors:
            errors['ragflow'] = ragflow_errors
        
        # Validate Email
        email_errors = []
        if self.email.enabled:
            if not self.email.host:
                email_errors.append('Host is required')
            if not self.email.sender_email:
                email_errors.append('Sender email is required')
            if self.email.username and not self.email.password:
                email_errors.append('Password is required when username is provided')
        if email_errors:
            errors['email'] = email_errors
        
        return errors


# Global services manager instance
services = ServicesManager()


def get_service_config(service_name: str) -> Optional[ServiceConfig]:
    """
    Get configuration for a specific service.
    
    Args:
        service_name: Name of the service
        
    Returns:
        Service configuration or None
    """
    return getattr(services, service_name, None)


def is_service_enabled(service_name: str) -> bool:
    """
    Check if a service is enabled.
    
    Args:
        service_name: Name of the service
        
    Returns:
        True if enabled, False otherwise
    """
    config = get_service_config(service_name)
    return config.enabled if config else False


def get_all_service_configs() -> Dict[str, ServiceConfig]:
    """
    Get all service configurations.
    
    Returns:
        Dictionary of service configurations
    """
    return {
        'elasticsearch': services.elasticsearch,
        'minio': services.minio,
        'mineru': services.mineru,
        'ragflow': services.ragflow,
        'email': services.email
    }