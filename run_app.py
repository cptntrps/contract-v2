#!/usr/bin/env python3
"""
Application runner script for database-enabled contract analyzer
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.main import create_app

if __name__ == "__main__":
    # Create and run the application
    app = create_app()
    
    # Run in debug mode for development
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )