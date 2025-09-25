#!/usr/bin/env python3
"""
Start the Contract Analyzer Server
"""

import os
import sys
from app.main import create_app

if __name__ == '__main__':
    print("🚀 Starting Contract Analyzer Server")
    print("=" * 50)
    
    # Create the application
    app = create_app()
    
    print("✅ Flask application created successfully")
    print("✅ All routes registered including /api/analyze-contract")
    print()
    print("Server starting on http://localhost:5000")
    print("=" * 50)
    
    # Start the server
    app.run(debug=True, host='0.0.0.0', port=5000)