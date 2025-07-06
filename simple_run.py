#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple development server runner for Ragflow-MinerU Integration
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """Setup basic environment variables."""
    # Set basic environment variables
    os.environ.setdefault('ENVIRONMENT', 'development')
    os.environ.setdefault('DB_TYPE', 'sqlite')
    os.environ.setdefault('DB_NAME', 'ragflow_mineru_dev')
    os.environ.setdefault('SECRET_KEY', 'dev-secret-key-for-testing')
    os.environ.setdefault('JWT_SECRET_KEY', 'dev-jwt-secret-key')
    
    print("✓ Environment setup complete")

def run_simple_server():
    """Run a simple development server without complex initialization."""
    print("\n" + "="*50)
    print("🚀 Starting Simple Ragflow-MinerU Server")
    print("="*50)
    
    # Setup environment
    setup_environment()
    
    try:
        # Import and create app
        from backend.app import create_app
        app = create_app('development')
        
        print(f"\n📍 Server starting at: http://127.0.0.1:5000")
        print(f"📍 API Base URL: http://127.0.0.1:5000/api/v1")
        print(f"📍 Health Check: http://127.0.0.1:5000/health")
        
        # Run the server
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=False  # Disable reloader to avoid issues
        )
        
    except Exception as e:
        print(f"✗ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_simple_server()