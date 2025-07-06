#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database instance for backward compatibility
"""

# This is a compatibility module for existing imports
# The actual database initialization is in backend.config.database

from backend.config.database import get_db

# Create a proxy object that will get the database when needed
class DatabaseProxy:
    def __getattr__(self, name):
        try:
            db = get_db()
            return getattr(db, name)
        except RuntimeError:
            # Database not initialized yet
            return None
    
    def __bool__(self):
        try:
            get_db()
            return True
        except RuntimeError:
            return False

# Create the proxy instance
db = DatabaseProxy()