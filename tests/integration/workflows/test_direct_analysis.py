#!/usr/bin/env python3
"""
Direct test of contract analysis functionality without API server
"""
import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and initialization"""
    try:
        from app.database.database import get_db_session, init_database
        
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        
        # Test getting a session
        session = get_db_session()
        logger.info("✅ Database connection successful")
        session.close()
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def test_contract_analysis():
    """Test contract analysis directly"""
    try:
        from app.core.services.analyzer import ContractAnalyzer
        from app.core.services.document_processor import DocumentProcessor
        from app.services.storage.file_manager import FileManager
        from app.config.settings import get_config
        
        # Get configuration
        config = get_config()
        
        # Initialize services
        logger.info("Initializing services...")
        file_manager = FileManager(config)
        document_processor = DocumentProcessor()
        analyzer = ContractAnalyzer(config)
        
        # Find sample contracts and templates
        data_dir = Path(__file__).parent / "data"
        uploads_dir = data_dir / "uploads"
        templates_dir = data_dir / "templates"
        
        if not uploads_dir.exists():
            logger.error(f"❌ Uploads directory not found: {uploads_dir}")
            return False
            
        if not templates_dir.exists():
            logger.error(f"❌ Templates directory not found: {templates_dir}")
            return False
        
        # Get first contract and template
        contracts = list(uploads_dir.glob("*.docx"))
        templates = list(templates_dir.glob("*.docx"))
        
        if not contracts:
            logger.error("❌ No contracts found in uploads directory")
            return False
            
        if not templates:
            logger.error("❌ No templates found in templates directory")
            return False
        
        contract_path = contracts[0]
        template_path = templates[0]
        
        logger.info(f"📄 Contract: {contract_path.name}")
        logger.info(f"📋 Template: {template_path.name}")
        
        # Extract text from documents
        logger.info("Extracting text from documents...")
        contract_text = document_processor.extract_text_from_docx(str(contract_path))
        template_text = document_processor.extract_text_from_docx(str(template_path))
        
        if not contract_text:
            logger.warning("Contract text extraction returned empty - trying direct read")
            with open(contract_path, 'rb') as f:
                contract_text = f"[Binary content - {len(f.read())} bytes]"
                
        if not template_text:
            logger.warning("Template text extraction returned empty - trying direct read")
            with open(template_path, 'rb') as f:
                template_text = f"[Binary content - {len(f.read())} bytes]"
        
        logger.info(f"Contract text length: {len(contract_text)} chars")
        logger.info(f"Template text length: {len(template_text)} chars")
        
        # Test comparison engine directly
        from app.core.services.comparison_engine import ComparisonEngine
        comparison_engine = ComparisonEngine()
        
        # Calculate similarity
        logger.info("Calculating similarity...")
        similarity = comparison_engine.calculate_similarity(contract_text, template_text)
        logger.info(f"📊 Similarity score: {similarity:.2%}")
        
        # Find changes
        logger.info("Finding changes...")
        changes = comparison_engine.find_changes(contract_text, template_text)
        logger.info(f"📝 Number of changes found: {len(changes)}")
        
        # Get detailed changes
        detailed_changes = comparison_engine.find_detailed_changes(contract_text, template_text)
        logger.info(f"📋 Detailed changes found: {len(detailed_changes)}")
        
        # Get statistics
        stats = comparison_engine.get_change_statistics(detailed_changes)
        logger.info(f"📈 Change statistics: {stats}")
        
        logger.info("✅ Contract analysis test successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Contract analysis test failed: {e}")
        logger.exception("Full exception details:")
        return False

def test_llm_integration():
    """Test LLM provider integration"""
    try:
        from app.services.llm.providers import create_llm_provider
        from app.config.settings import get_config
        
        config = get_config()
        logger.info(f"LLM Provider: {config.LLM_PROVIDER}")
        logger.info(f"OpenAI Model: {config.OPENAI_MODEL}")
        
        # Create LLM provider
        llm_config = {
            'provider': config.LLM_PROVIDER,
            'api_key': config.OPENAI_API_KEY,
            'model': config.OPENAI_MODEL,
            'timeout': 30
        }
        
        if not config.OPENAI_API_KEY:
            logger.warning("⚠️  No OpenAI API key found - LLM features will be limited")
            return True
            
        provider = create_llm_provider(config.LLM_PROVIDER, llm_config)
        logger.info(f"✅ LLM provider created: {provider.get_model_info()}")
        
        # Test simple completion (optional - costs money)
        # response = provider.complete("What is 2+2?", max_tokens=10)
        # logger.info(f"LLM Response: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM integration test failed: {e}")
        return False

def test_report_generation():
    """Test report generation capabilities"""
    try:
        from app.services.reports.generator import ReportGenerator
        from app.core.models.analysis_result import AnalysisResult, Change, ChangeType, ChangeClassification
        from datetime import datetime
        import tempfile
        
        # Create test analysis result
        analysis = AnalysisResult(
            analysis_id="test_001",
            contract_id="contract_001",
            template_id="template_001",
            analysis_timestamp=datetime.now(),
            total_changes=3,
            similarity_score=0.85
        )
        
        # Add sample changes
        change1 = Change(
            change_id="change_001",
            change_type=ChangeType.REPLACEMENT,
            classification=ChangeClassification.SIGNIFICANT,
            deleted_text="30 days",
            inserted_text="45 days",
            line_number=10,
            explanation="Payment terms changed"
        )
        analysis.add_change(change1)
        
        # Initialize report generator
        generator = ReportGenerator()
        
        # Test JSON report generation
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json_path = f.name
            
        success = generator.generate_json_report(analysis, json_path)
        logger.info(f"✅ JSON report generated: {success}")
        
        # Clean up
        os.unlink(json_path)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Report generation test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🔍 Starting direct contract analysis tests...")
    logger.info("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Contract Analysis", test_contract_analysis),
        ("LLM Integration", test_llm_integration),
        ("Report Generation", test_report_generation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Testing {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Results Summary:")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status:8} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\n📈 Total: {len(tests)} tests, {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All tests passed!")
        return True
    else:
        logger.info("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)