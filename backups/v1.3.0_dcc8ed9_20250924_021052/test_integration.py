#!/usr/bin/env python3
"""
Integration tests for Contract Analyzer Application
"""

import os
import sys
import requests
import time
import threading
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def start_flask_app():
    """Start Flask application in background thread"""
    try:
        from app.main import create_app
        app = create_app()
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")

def wait_for_app_startup(url="http://localhost:5000", timeout=30):
    """Wait for application to start up"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    return False

def test_api_health():
    """Test API health endpoint"""
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=10)
        print(f"✅ Health endpoint - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health response: {data}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_dashboard_loading():
    """Test that dashboard loads"""
    try:
        response = requests.get("http://localhost:5000/", timeout=10)
        print(f"✅ Dashboard endpoint - Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            if "Contract Review Dashboard" in content:
                print("✅ Dashboard content loaded correctly")
                return True
            else:
                print("❌ Dashboard content not found")
                return False
        return False
    except Exception as e:
        print(f"❌ Dashboard loading failed: {e}")
        return False

def test_api_contracts_list():
    """Test contracts listing API"""
    try:
        response = requests.get("http://localhost:5000/api/contracts", timeout=10)
        print(f"✅ Contracts API - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Contracts found: {len(data.get('contracts', []))}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Contracts API failed: {e}")
        return False

def test_api_templates_list():
    """Test templates listing API"""
    try:
        response = requests.get("http://localhost:5000/api/templates", timeout=10)
        print(f"✅ Templates API - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Templates found: {len(data.get('templates', []))}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Templates API failed: {e}")
        return False

def test_static_resources():
    """Test static resources loading"""
    try:
        # Test CSS
        css_response = requests.get("http://localhost:5000/static/css/dashboard.css", timeout=10)
        print(f"✅ CSS loading - Status: {css_response.status_code}")
        
        # Test JS
        js_response = requests.get("http://localhost:5000/static/js/dashboard.js", timeout=10)
        print(f"✅ JS loading - Status: {js_response.status_code}")
        
        return css_response.status_code == 200 and js_response.status_code == 200
    except Exception as e:
        print(f"❌ Static resources failed: {e}")
        return False

def test_file_upload_endpoint():
    """Test file upload endpoint"""
    try:
        # Test without file (should fail gracefully)
        response = requests.post("http://localhost:5000/api/contracts/upload", timeout=10)
        print(f"✅ Upload endpoint (no file) - Status: {response.status_code}")
        
        # Should return 400 for bad request
        return response.status_code == 400
    except Exception as e:
        print(f"❌ Upload endpoint failed: {e}")
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("🔍 Starting integration tests...")
    print("=" * 50)
    
    # Start Flask app in background
    print("🚀 Starting Flask application...")
    flask_thread = threading.Thread(target=start_flask_app, daemon=True)
    flask_thread.start()
    
    # Wait for app to start
    print("⏳ Waiting for application startup...")
    if not wait_for_app_startup():
        print("❌ Application failed to start within timeout")
        return False
    
    print("✅ Application started successfully!")
    
    # Run tests
    tests = [
        ("API Health Check", test_api_health),
        ("Dashboard Loading", test_dashboard_loading),
        ("Contracts API", test_api_contracts_list),
        ("Templates API", test_api_templates_list),
        ("Static Resources", test_static_resources),
        ("File Upload Endpoint", test_file_upload_endpoint),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Integration Test Results:")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Total: {len(tests)} tests, {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("⚠️  Some integration tests failed.")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    
    # Keep the app running for further testing
    if success:
        print("\n🔄 Application is running on http://localhost:5000")
        print("Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
    
    sys.exit(0 if success else 1)