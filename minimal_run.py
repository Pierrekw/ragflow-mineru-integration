#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal development server runner for Ragflow-MinerU Integration
"""

import os
import sys
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """Setup basic environment variables."""
    # Set basic environment variables
    os.environ.setdefault('ENVIRONMENT', 'development')
    os.environ.setdefault('SECRET_KEY', 'dev-secret-key-for-testing')
    os.environ.setdefault('JWT_SECRET_KEY', 'dev-jwt-secret-key')
    
    print("✓ Environment setup complete")

def create_minimal_app():
    """Create a minimal Flask app without database."""
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['DEBUG'] = True
    
    # Enable CORS
    CORS(app, origins=['http://localhost:5173'], supports_credentials=True)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'environment': 'development'
        })
    
    # API info endpoint
    @app.route('/api/v1/info')
    def api_info():
        return jsonify({
            'name': 'Ragflow-MinerU Integration API',
            'version': '1.0.0',
            'status': 'running'
        })
    
    # Test auth endpoint
    @app.route('/api/v1/auth/test')
    def auth_test():
        return jsonify({
            'message': 'Auth service is running',
            'authenticated': False
        })
    
    return app

def run_minimal_server():
    """Run a minimal development server."""
    print("\n" + "="*50)
    print("🚀 Starting Minimal Ragflow-MinerU Server")
    print("="*50)
    
    # Setup environment
    setup_environment()
    
    try:
        # Create minimal app
        app = create_minimal_app()
        
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
    run_minimal_server()