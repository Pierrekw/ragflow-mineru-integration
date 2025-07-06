#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ragflow-MinerU Integration - Development Server Runner

This script provides a convenient way to start the development server
with proper environment setup and configuration.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app import create_app
from backend.config.database import init_db
from backend.database import db


def setup_environment():
    """Setup environment variables and configuration."""
    # Load environment variables from .env file if it exists
    env_file = project_root / '.env'
    if env_file.exists():
        print(f"Loading environment from {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())
    else:
        print("No .env file found, using default configuration")
        print("You can copy .env.example to .env and customize the settings")


def init_database_tables(app):
    """Initialize database tables and default data."""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Import models to ensure they're registered
            from backend.models.user import User
            from backend.models.role import Role
            from backend.models.permission import Permission
            from backend.models.document import Document
            from backend.models.task import Task
            
            # Check if we need to create default data
            if Role.query.count() == 0:
                print("Creating default roles and permissions...")
                create_default_data()
                print("✓ Default data created successfully")
            else:
                print("✓ Database already initialized")
                
        except Exception as e:
            print(f"✗ Database initialization failed: {e}")
            return False
    return True


def create_default_data():
    """Create default roles, permissions, and admin user."""
    from backend.models.user import User, AccessLevel
    from backend.models.role import Role
    from backend.models.permission import Permission, PermissionType
    
    # Create default permissions
    default_permissions = [
        ('auth.login', 'Login', 'User can login to the system', PermissionType.SYSTEM),
        ('auth.logout', 'Logout', 'User can logout from the system', PermissionType.SYSTEM),
        ('document.read', 'Read Documents', 'User can read documents', PermissionType.RESOURCE),
        ('document.create', 'Create Documents', 'User can create documents', PermissionType.RESOURCE),
        ('document.update', 'Update Documents', 'User can update documents', PermissionType.RESOURCE),
        ('document.delete', 'Delete Documents', 'User can delete documents', PermissionType.RESOURCE),
        ('system.admin', 'System Administration', 'Full system administration access', PermissionType.ADMIN),
    ]
    
    permissions = {}
    for name, display_name, description, perm_type in default_permissions:
        permission = Permission(
            name=name,
            display_name=display_name,
            description=description,
            permission_type=perm_type,
            is_system=True
        )
        db.session.add(permission)
        permissions[name] = permission
    
    # Create default roles
    admin_role = Role(
        name='admin',
        display_name='Administrator',
        description='System administrator with full access',
        access_level=AccessLevel.ADMIN,
        is_system=True
    )
    
    user_role = Role(
        name='user',
        display_name='User',
        description='Regular user with basic document access',
        access_level=AccessLevel.USER,
        is_system=True,
        is_default=True
    )
    
    db.session.add(admin_role)
    db.session.add(user_role)
    db.session.flush()  # Get role IDs
    
    # Create default admin user
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123456')
    
    admin_user = User(
        username='admin',
        email=admin_email,
        first_name='System',
        last_name='Administrator',
        is_active=True,
        is_verified=True,
        role_id=admin_role.id
    )
    admin_user.set_password(admin_password)
    db.session.add(admin_user)
    
    db.session.commit()
    print(f"✓ Default admin user created: {admin_email} / {admin_password}")


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_jwt_extended',
        'flask_cors',
        'marshmallow',
        'celery',
        'redis'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("✗ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install them using:")
        print(f"  pip install {' '.join(missing_packages)}")
        print("\nOr install all requirements:")
        print("  pip install -r requirements.txt")
        return False
    
    print("✓ All required packages are installed")
    return True


def run_development_server(host='127.0.0.1', port=5000, debug=True):
    """Run the development server."""
    print("\n" + "="*50)
    print("🚀 Starting Ragflow-MinerU Integration Server")
    print("="*50)
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create Flask app
    app = create_app('development')
    
    # Initialize database
    if not init_database_tables(app):
        sys.exit(1)
    
    print(f"\n📍 Server will start at: http://{host}:{port}")
    print(f"📍 API Base URL: http://{host}:{port}/api/v1")
    print(f"📍 Health Check: http://{host}:{port}/health")
    print(f"📍 App Info: http://{host}:{port}/info")
    
    print("\n📋 Available API Endpoints:")
    print("  • Authentication: /api/v1/auth")
    print("  • Documents: /api/v1/documents")
    print("  • Users: /api/v1/users")
    print("  • Permissions: /api/v1/permissions")
    print("  • MinerU: /api/v1/mineru")
    
    print("\n🔧 Development Tips:")
    print("  • Press Ctrl+C to stop the server")
    print("  • Check logs for debugging information")
    print("  • Use --help for more options")
    
    print("\n" + "="*50)
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n\n❌ Server error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Ragflow-MinerU Integration Development Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                          # Start with default settings
  python run.py --host 0.0.0.0          # Allow external connections
  python run.py --port 8000              # Use different port
  python run.py --no-debug               # Disable debug mode
  python run.py --init-db                # Initialize database only
        """
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind the server to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind the server to (default: 5000)'
    )
    
    parser.add_argument(
        '--no-debug',
        action='store_true',
        help='Disable debug mode'
    )
    
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database and exit'
    )
    
    args = parser.parse_args()
    
    if args.init_db:
        print("Initializing database...")
        setup_environment()
        app = create_app('development')
        if init_database_tables(app):
            print("✓ Database initialized successfully")
        else:
            print("✗ Database initialization failed")
            sys.exit(1)
        return
    
    # Run development server
    run_development_server(
        host=args.host,
        port=args.port,
        debug=not args.no_debug
    )


if __name__ == '__main__':
    main()