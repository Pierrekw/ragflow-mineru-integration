#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database configuration and initialization for Ragflow-MinerU Integration

This module handles database connections, migrations, and initialization.
"""

import os
import logging
from typing import Optional
from peewee import *
from playhouse.pool import PooledMySQLDatabase, PooledPostgresqlDatabase
from playhouse.sqlite_ext import SqliteExtDatabase
from flask import Flask

from backend.config.settings import BaseConfig

# Global database instance
db = None

logger = logging.getLogger(__name__)


def create_database_connection(config: BaseConfig) -> Database:
    """
    Create database connection based on configuration.
    
    Args:
        config (BaseConfig): Configuration instance
        
    Returns:
        Database: Peewee database instance
    """
    if config.DB_TYPE == 'mysql':
        return PooledMySQLDatabase(
            config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT,
            charset=config.DB_CHARSET,
            max_connections=config.DB_POOL_SIZE,
            stale_timeout=config.DB_POOL_TIMEOUT,
            timeout=config.DB_POOL_TIMEOUT,
            autocommit=True,
            autorollback=True,
            sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'
        )
    
    elif config.DB_TYPE == 'postgresql':
        return PooledPostgresqlDatabase(
            config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT,
            max_connections=config.DB_POOL_SIZE,
            stale_timeout=config.DB_POOL_TIMEOUT
        )
    
    elif config.DB_TYPE == 'sqlite':
        db_path = config.DB_NAME if config.DB_NAME != ':memory:' else ':memory:'
        return SqliteExtDatabase(
            db_path,
            pragmas={
                'journal_mode': 'wal',
                'cache_size': -1024 * 64,  # 64MB cache
                'foreign_keys': 1,
                'ignore_check_constraints': 0,
                'synchronous': 0
            }
        )
    
    else:
        raise ValueError(f"Unsupported database type: {config.DB_TYPE}")


def init_db(app: Flask) -> None:
    """
    Initialize database connection and register teardown handlers.
    
    Args:
        app (Flask): Flask application instance
    """
    global db
    
    config = app.config
    
    # Create database connection
    db = create_database_connection(config)
    
    # Store database instance in app config
    app.config['DATABASE'] = db
    
    # Register request handlers
    @app.before_request
    def before_request():
        """Connect to database before each request."""
        if db.is_closed():
            db.connect()
    
    @app.teardown_request
    def teardown_request(exception):
        """Close database connection after each request."""
        if not db.is_closed():
            db.close()
    
    # Register CLI commands
    register_cli_commands(app)
    
    logger.info(f"Database initialized: {config.DB_TYPE}://{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")


def get_db() -> Database:
    """
    Get the current database instance.
    
    Returns:
        Database: Current database instance
    """
    global db
    if db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db


def create_tables() -> None:
    """
    Create all database tables.
    """
    from backend.models.user import User, UserRole, UserSession
    from backend.models.document import Document, DocumentChunk, DocumentVersion
    from backend.models.knowledgebase import Knowledgebase, KnowledgebaseDocument
    from backend.models.task import ParseTask, TaskLog
    from backend.models.permission import UserKnowledgebasePermission, RolePermission
    from backend.models.file import File, FileMetadata
    from backend.models.audit import AuditLog
    
    models = [
        # User models
        User, UserRole, UserSession,
        # Document models
        Document, DocumentChunk, DocumentVersion,
        # Knowledgebase models
        Knowledgebase, KnowledgebaseDocument,
        # Task models
        ParseTask, TaskLog,
        # Permission models
        UserKnowledgebasePermission, RolePermission,
        # File models
        File, FileMetadata,
        # Audit models
        AuditLog
    ]
    
    db.create_tables(models, safe=True)
    logger.info(f"Created {len(models)} database tables")


def drop_tables() -> None:
    """
    Drop all database tables.
    """
    from backend.models.user import User, UserRole, UserSession
    from backend.models.document import Document, DocumentChunk, DocumentVersion
    from backend.models.knowledgebase import Knowledgebase, KnowledgebaseDocument
    from backend.models.task import ParseTask, TaskLog
    from backend.models.permission import UserKnowledgebasePermission, RolePermission
    from backend.models.file import File, FileMetadata
    from backend.models.audit import AuditLog
    
    models = [
        # Reverse order for foreign key constraints
        AuditLog,
        FileMetadata, File,
        RolePermission, UserKnowledgebasePermission,
        TaskLog, ParseTask,
        KnowledgebaseDocument, Knowledgebase,
        DocumentVersion, DocumentChunk, Document,
        UserSession, UserRole, User
    ]
    
    db.drop_tables(models, safe=True)
    logger.info(f"Dropped {len(models)} database tables")


def migrate_database() -> None:
    """
    Run database migrations.
    """
    # Check if migration table exists
    if not db.table_exists('migration_history'):
        # Create migration history table
        db.execute_sql("""
            CREATE TABLE migration_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                version VARCHAR(50) NOT NULL UNIQUE,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_version (version)
            )
        """)
        logger.info("Created migration_history table")
    
    # Get current migration version
    try:
        cursor = db.execute_sql("SELECT version FROM migration_history ORDER BY applied_at DESC LIMIT 1")
        current_version = cursor.fetchone()
        current_version = current_version[0] if current_version else None
    except:
        current_version = None
    
    # Define migrations
    migrations = [
        ('001_initial_schema', 'Create initial database schema', _migration_001_initial_schema),
        ('002_add_indexes', 'Add database indexes for performance', _migration_002_add_indexes),
        ('003_add_audit_log', 'Add audit logging table', _migration_003_add_audit_log),
        ('004_add_file_metadata', 'Add file metadata table', _migration_004_add_file_metadata),
    ]
    
    # Apply pending migrations
    for version, description, migration_func in migrations:
        if current_version is None or version > current_version:
            logger.info(f"Applying migration {version}: {description}")
            try:
                migration_func()
                # Record migration
                db.execute_sql(
                    "INSERT INTO migration_history (version, description) VALUES (%s, %s)",
                    (version, description)
                )
                logger.info(f"Migration {version} applied successfully")
            except Exception as e:
                logger.error(f"Migration {version} failed: {e}")
                raise


def _migration_001_initial_schema():
    """Initial schema migration."""
    create_tables()


def _migration_002_add_indexes():
    """Add database indexes for performance."""
    indexes = [
        "CREATE INDEX idx_user_email ON user (email)",
        "CREATE INDEX idx_user_is_active ON user (is_active)",
        "CREATE INDEX idx_document_kb_id ON document (kb_id)",
        "CREATE INDEX idx_document_status ON document (status)",
        "CREATE INDEX idx_document_created_at ON document (created_at)",
        "CREATE INDEX idx_parse_task_user_id ON parse_task (user_id)",
        "CREATE INDEX idx_parse_task_status ON parse_task (status)",
        "CREATE INDEX idx_parse_task_created_at ON parse_task (created_at)",
        "CREATE INDEX idx_kb_permission_user_kb ON user_kb_permission (user_id, kb_id)",
        "CREATE INDEX idx_file_parent_id ON file (parent_id)",
        "CREATE INDEX idx_file_created_by ON file (created_by)",
    ]
    
    for index_sql in indexes:
        try:
            db.execute_sql(index_sql)
        except Exception as e:
            # Index might already exist
            logger.warning(f"Index creation failed (might already exist): {e}")


def _migration_003_add_audit_log():
    """Add audit logging table."""
    # This will be handled by create_tables() if the table doesn't exist
    pass


def _migration_004_add_file_metadata():
    """Add file metadata table."""
    # This will be handled by create_tables() if the table doesn't exist
    pass


def seed_database() -> None:
    """
    Seed database with initial data.
    """
    from backend.models.user import User, UserRole
    from backend.models.permission import RolePermission
    
    # Create default roles
    roles_data = [
        {
            'name': 'admin',
            'display_name': '管理员',
            'description': '系统管理员，拥有所有权限',
            'permissions': [
                'user.create', 'user.read', 'user.update', 'user.delete',
                'kb.create', 'kb.read', 'kb.update', 'kb.delete',
                'document.create', 'document.read', 'document.update', 'document.delete',
                'task.create', 'task.read', 'task.update', 'task.delete',
                'system.manage'
            ]
        },
        {
            'name': 'user',
            'display_name': '普通用户',
            'description': '普通用户，拥有基本权限',
            'permissions': [
                'kb.create', 'kb.read', 'kb.update',
                'document.create', 'document.read', 'document.update',
                'task.create', 'task.read'
            ]
        },
        {
            'name': 'viewer',
            'display_name': '查看者',
            'description': '只读用户，只能查看内容',
            'permissions': [
                'kb.read', 'document.read', 'task.read'
            ]
        }
    ]
    
    for role_data in roles_data:
        role, created = UserRole.get_or_create(
            name=role_data['name'],
            defaults={
                'display_name': role_data['display_name'],
                'description': role_data['description'],
                'is_active': True
            }
        )
        
        if created:
            logger.info(f"Created role: {role.name}")
            
            # Create role permissions
            for permission in role_data['permissions']:
                RolePermission.create(
                    role_id=role.id,
                    permission=permission,
                    granted=True
                )
    
    # Create default admin user
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@ragflow-mineru.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    admin_role = UserRole.get(UserRole.name == 'admin')
    
    admin_user, created = User.get_or_create(
        email=admin_email,
        defaults={
            'username': 'admin',
            'nickname': '系统管理员',
            'role_id': admin_role.id,
            'is_active': True,
            'is_superuser': True
        }
    )
    
    if created:
        admin_user.set_password(admin_password)
        admin_user.save()
        logger.info(f"Created admin user: {admin_email}")
    
    logger.info("Database seeding completed")


def register_cli_commands(app: Flask) -> None:
    """
    Register CLI commands for database management.
    
    Args:
        app (Flask): Flask application instance
    """
    @app.cli.command()
    def init_database():
        """Initialize database tables."""
        create_tables()
        print("Database tables created successfully")
    
    @app.cli.command()
    def drop_database():
        """Drop all database tables."""
        drop_tables()
        print("Database tables dropped successfully")
    
    @app.cli.command()
    def migrate():
        """Run database migrations."""
        migrate_database()
        print("Database migrations completed")
    
    @app.cli.command()
    def seed():
        """Seed database with initial data."""
        seed_database()
        print("Database seeded successfully")
    
    @app.cli.command()
    def reset_database():
        """Reset database (drop, create, migrate, seed)."""
        drop_tables()
        create_tables()
        migrate_database()
        seed_database()
        print("Database reset completed")


def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is working, False otherwise
    """
    try:
        db.execute_sql("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Get database information.
    
    Returns:
        dict: Database information
    """
    try:
        # Get database version
        if isinstance(db, PooledMySQLDatabase):
            cursor = db.execute_sql("SELECT VERSION()")
            version = cursor.fetchone()[0]
            db_type = 'MySQL'
        elif isinstance(db, PooledPostgresqlDatabase):
            cursor = db.execute_sql("SELECT version()")
            version = cursor.fetchone()[0]
            db_type = 'PostgreSQL'
        elif isinstance(db, SqliteExtDatabase):
            cursor = db.execute_sql("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            db_type = 'SQLite'
        else:
            version = 'Unknown'
            db_type = 'Unknown'
        
        # Get table count
        if isinstance(db, (PooledMySQLDatabase, PooledPostgresqlDatabase)):
            cursor = db.execute_sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()")
        else:
            cursor = db.execute_sql("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        
        table_count = cursor.fetchone()[0]
        
        return {
            'type': db_type,
            'version': version,
            'table_count': table_count,
            'connection_status': 'connected' if not db.is_closed() else 'disconnected'
        }
    
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            'type': 'Unknown',
            'version': 'Unknown',
            'table_count': 0,
            'connection_status': 'error',
            'error': str(e)
        }