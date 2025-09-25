#!/usr/bin/env python3
"""
Basic functionality test for Contract Analyzer
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

def test_environment_setup():
    """Test that environment variables are loaded"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"✅ Environment setup - API key configured: {'Yes' if api_key else 'No'}")
    return api_key is not None

def test_config_loading():
    """Test configuration loading"""
    try:
        from app.config.settings import get_config
        config = get_config()
        print(f"✅ Config loading - Environment: {config.ENV}")
        print(f"✅ Config loading - Debug: {config.DEBUG}")
        print(f"✅ Config loading - LLM Provider: {config.LLM_PROVIDER}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

def test_document_processing():
    """Test document processing functionality"""
    try:
        from app.core.services.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        print("✅ Document processor initialized")
        return True
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        return False

def test_comparison_engine():
    """Test comparison engine functionality"""
    try:
        from app.core.services.comparison_engine import ComparisonEngine
        engine = ComparisonEngine()
        
        # Test basic similarity calculation
        text1 = "This is a sample contract"
        text2 = "This is a sample contract with changes"
        similarity = engine.calculate_similarity(text1, text2)
        print(f"✅ Comparison engine - Similarity: {similarity:.3f}")
        
        # Test change detection
        changes = engine.find_changes(text1, text2)
        print(f"✅ Comparison engine - Changes detected: {len(changes)}")
        return True
    except Exception as e:
        print(f"❌ Comparison engine failed: {e}")
        return False

def test_llm_provider():
    """Test LLM provider functionality"""
    try:
        from app.services.llm.providers import create_llm_provider
        from app.config.settings import get_config
        
        config = get_config()
        llm_config = {
            'provider': 'openai',
            'api_key': config.OPENAI_API_KEY,
            'model': config.OPENAI_MODEL,
            'timeout': 30
        }
        
        provider = create_llm_provider('openai', llm_config)
        print(f"✅ LLM provider created - Model: {provider.model}")
        
        # Test health check (without making API call)
        model_info = provider.get_model_info()
        print(f"✅ LLM provider info - Provider: {model_info['provider']}")
        return True
    except Exception as e:
        print(f"❌ LLM provider failed: {e}")
        return False

def test_security_validation():
    """Test security validation"""
    try:
        from app.utils.security.validators import SecurityValidator
        validator = SecurityValidator()
        
        # Test filename validation
        valid_filename = validator.validate_filename("test_contract.docx")
        print(f"✅ Security validation - Valid filename: {valid_filename}")
        
        return True
    except Exception as e:
        print(f"❌ Security validation failed: {e}")
        return False

def test_report_generation():
    """Test report generation setup"""
    try:
        from app.services.reports.generator import ReportGenerator
        generator = ReportGenerator()
        print("✅ Report generator initialized")
        return True
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False

def test_flask_app_creation():
    """Test Flask app creation"""
    try:
        from app.config.settings import get_config
        from app.api.app import create_api_app
        
        config = get_config()
        app = create_api_app(config)
        print(f"✅ Flask app created - Name: {app.name}")
        return True
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return False

def main():
    """Run all basic functionality tests"""
    print("🔍 Running basic functionality tests...")
    print("=" * 50)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Config Loading", test_config_loading),
        ("Document Processing", test_document_processing),
        ("Comparison Engine", test_comparison_engine),
        ("LLM Provider", test_llm_provider),
        ("Security Validation", test_security_validation),
        ("Report Generation", test_report_generation),
        ("Flask App Creation", test_flask_app_creation),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
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
        print("🎉 All basic functionality tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)