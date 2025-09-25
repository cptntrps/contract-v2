#!/usr/bin/env python3
"""
Debug the analysis endpoint error
"""

import sys
import os
import traceback
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_analysis_components():
    """Test individual components that might cause the 500 error"""
    
    print("🔍 Debugging Analysis Endpoint Components")
    print("=" * 60)
    
    # Test 1: Basic imports
    print("\n1. Testing imports...")
    try:
        from app.core.services.analyzer import create_contract_analyzer, ContractAnalysisError
        from app.core.models.contract import Contract
        from app.utils.errors.exceptions import ValidationError, NotFoundError
        from app.utils.errors.validators import ValidationHandler
        print("   ✅ All imports successful")
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        traceback.print_exc()
        return False
    
    # Test 2: Create analyzer with config
    print("\n2. Testing analyzer creation...")
    try:
        config = {
            'llm_settings': {
                'provider': 'openai',
                'model': 'gpt-4o',
                'temperature': 0.1,
                'max_tokens': 2048
            },
            'analysis_settings': {
                'include_llm_analysis': False,  # Disable LLM for testing
                'batch_size': 10,
                'similarity_threshold': 0.7
            },
            'nlp_settings': {}  # Add NLP settings for semantic analysis
        }
        
        analyzer = create_contract_analyzer(config)
        print("   ✅ Analyzer created successfully")
        print(f"   • Type: {type(analyzer)}")
        print(f"   • Has semantic analyzer: {hasattr(analyzer, 'semantic_analyzer')}")
        print(f"   • Has NLP components: {all(hasattr(analyzer, attr) for attr in ['entity_extractor', 'clause_classifier', 'risk_analyzer'])}")
        
    except Exception as e:
        print(f"   ❌ Analyzer creation error: {e}")
        traceback.print_exc()
        return False
    
    # Test 3: Contract validation
    print("\n3. Testing contract validation...")
    try:
        # Test contract ID validation
        test_contract_id = "contract_12345678"
        validated_id = ValidationHandler.validate_contract_id(test_contract_id)
        print(f"   ✅ Contract ID validation successful: {validated_id}")
        
        # Create a mock contract
        from datetime import datetime
        
        contract = Contract(
            id=test_contract_id,
            filename="test_contract.docx",
            original_filename="Test Contract.docx",
            file_path="/mock/path/test.docx",
            file_size=1024,
            upload_timestamp=datetime.now(),
            status="uploaded"
        )
        print("   ✅ Contract object created successfully")
        print(f"   • Display name: {contract.get_display_name()}")
        print(f"   • Status: {contract.status}")
        
        # Test status changes
        contract.mark_processing()
        print(f"   • Status after mark_processing: {contract.status}")
        
        contract.mark_analyzed(
            template_used="test_template.docx",
            changes_count=5,
            similarity_score=0.75,
            risk_level="MEDIUM"
        )
        print(f"   • Status after mark_analyzed: {contract.status}")
        
    except Exception as e:
        print(f"   ❌ Contract validation error: {e}")
        traceback.print_exc()
        return False
    
    # Test 4: Document processor
    print("\n4. Testing document processor...")
    try:
        from app.core.services.document_processor import DocumentProcessor
        
        doc_processor = DocumentProcessor()
        print("   ✅ Document processor created successfully")
        
        # Test with a real file if it exists
        test_files = [
            "data/uploads/Contract_001_Generic_SOW_20240115.docx",
            "data/templates/TYPE_SOW_Standard_v1.docx"
        ]
        
        for test_file in test_files:
            if Path(test_file).exists():
                try:
                    text = doc_processor.extract_text_from_docx(test_file)
                    print(f"   ✅ Successfully extracted {len(text)} characters from {test_file}")
                    break
                except Exception as e:
                    print(f"   ⚠️ Could not extract from {test_file}: {e}")
            
    except Exception as e:
        print(f"   ❌ Document processor error: {e}")
        traceback.print_exc()
        return False
    
    # Test 5: Template finding logic
    print("\n5. Testing template finding...")
    try:
        templates_dir = Path("data/templates")
        if templates_dir.exists():
            template_files = list(templates_dir.glob('*.docx'))
            print(f"   ✅ Found {len(template_files)} templates")
            for template in template_files[:3]:
                print(f"      • {template.name}")
        else:
            print("   ⚠️ Templates directory not found")
            
    except Exception as e:
        print(f"   ❌ Template finding error: {e}")
        return False
    
    # Test 6: NLP Components (new semantic analysis)
    print("\n6. Testing NLP Components...")
    try:
        # Test if NLP components can be imported
        from app.services.nlp import SemanticAnalyzer, EntityExtractor, ClauseClassifier, RiskAnalyzer
        
        semantic_analyzer = SemanticAnalyzer()
        entity_extractor = EntityExtractor()
        clause_classifier = ClauseClassifier()
        risk_analyzer = RiskAnalyzer()
        
        print("   ✅ All NLP components created successfully")
        print(f"   • SemanticAnalyzer: {type(semantic_analyzer)}")
        print(f"   • EntityExtractor: {type(entity_extractor)}")
        print(f"   • ClauseClassifier: {type(clause_classifier)}")
        print(f"   • RiskAnalyzer: {type(risk_analyzer)}")
        
    except Exception as e:
        print(f"   ❌ NLP components error: {e}")
        traceback.print_exc()
        return False
    
    print(f"\n{'='*60}")
    print("🎉 All component tests passed!")
    print("✅ Analysis endpoint should work correctly")
    print("\n💡 The 500 error might be due to:")
    print("   • Missing template files")
    print("   • Database connection issues")
    print("   • File permissions")
    print("   • Missing contract in contracts_store")
    
    return True


if __name__ == "__main__":
    success = test_analysis_components()
    if not success:
        print(f"\n{'='*60}")
        print("❌ Component testing failed")
        print("🔧 Fix the identified issues before testing the API")
        sys.exit(1)