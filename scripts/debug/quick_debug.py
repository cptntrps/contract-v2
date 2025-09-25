#!/usr/bin/env python3
"""
Quick Debug - Fast system status check for Contract Analyzer
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def print_status(title, status, details=""):
    """Print status with consistent formatting."""
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {title}")
    if details:
        print(f"   {details}")

def quick_check():
    """Run quick system checks."""
    print("🔍 CONTRACT ANALYZER - QUICK DEBUG")
    print("="*50)
    
    # 1. Check Python and venv
    venv_python = PROJECT_ROOT / "venv" / "bin" / "python"
    print_status("Virtual Environment", venv_python.exists(), str(venv_python))
    
    # 2. Check main directories
    required_dirs = ["app", "tests", "docs", "scripts", "data"]
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        print_status(f"Directory: {dir_name}/", dir_path.exists())
    
    # 3. Check main files
    required_files = ["run_app.py", "requirements.txt", "README.md"]
    for file_name in required_files:
        file_path = PROJECT_ROOT / file_name
        print_status(f"File: {file_name}", file_path.exists())
    
    # 4. Test app import
    try:
        from app.api.app import create_api_app
        from app.config.settings import get_config
        print_status("App Import", True, "Application can be imported")
        
        # 5. Test app creation
        config = get_config()
        app = create_api_app(config)
        print_status("App Creation", True, f"Flask app created with {len(list(app.url_map.iter_rules()))} routes")
        
    except Exception as e:
        print_status("App Import/Creation", False, str(e))
    
    # 6. Test API endpoints
    try:
        client = app.test_client()
        health_response = client.get('/api/health')
        print_status("API Health", health_response.status_code == 200, f"Status: {health_response.status_code}")
    except Exception as e:
        print_status("API Health", False, str(e))
    
    # 7. Count test files
    test_files = list((PROJECT_ROOT / "tests").glob("**/*test*.py"))
    print_status("Test Files", len(test_files) > 0, f"Found {len(test_files)} test files")
    
    # 8. Check data
    uploads = len(list((PROJECT_ROOT / "data" / "uploads").glob("*.docx")))
    templates = len(list((PROJECT_ROOT / "data" / "templates").glob("*.docx")))
    print_status("Data Files", uploads + templates > 0, f"{uploads} contracts, {templates} templates")
    
    print("\n🚀 QUICK ACTIONS:")
    print("   Start app: python run_app.py")
    print("   Run tests: pytest tests/")
    print("   Full debug: python scripts/debug/full_debug.py")
    print("   Script menu: python scripts/run_scripts.py")

if __name__ == "__main__":
    quick_check()