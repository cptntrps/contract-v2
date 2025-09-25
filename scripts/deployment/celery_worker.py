#!/usr/bin/env python3
"""
Celery worker startup script
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.main import create_app
from app.async_processing import configure_celery

if __name__ == '__main__':
    # Create Flask app for context
    app = create_app()
    
    # Configure Celery with Flask app context
    celery_app = configure_celery(app)
    
    # Start worker
    celery_app.start()