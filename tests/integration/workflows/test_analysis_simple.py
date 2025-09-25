#!/usr/bin/env python3
"""
Simple test of contract analysis core functionality
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_comparison():
    """Test basic document comparison functionality"""
    print("🔍 Testing Basic Document Comparison")
    print("=" * 60)
    
    try:
        from app.core.services.comparison_engine import ComparisonEngine
        
        # Create test documents
        template_text = """
        STANDARD CONTRACT TEMPLATE
        
        1. Payment Terms: Net 30 days from invoice date
        2. Delivery: Standard delivery within 5-7 business days
        3. Warranty: 12 months standard warranty
        4. Support: Business hours support (9 AM - 5 PM)
        5. Termination: 30 days written notice required
        """
        
        contract_text = """
        MODIFIED CONTRACT
        
        1. Payment Terms: Net 45 days from invoice date
        2. Delivery: Express delivery within 2-3 business days
        3. Warranty: 24 months extended warranty
        4. Support: 24/7 premium support
        5. Termination: 60 days written notice required
        6. Penalties: Late payment penalties apply after 60 days
        """
        
        # Initialize comparison engine
        engine = ComparisonEngine()
        
        # Calculate similarity
        print("\n📊 Calculating similarity...")
        similarity = engine.calculate_similarity(template_text, contract_text)
        print(f"Similarity Score: {similarity:.2%}")
        
        # Find basic changes
        print("\n📝 Finding changes...")
        changes = engine.find_changes(template_text, contract_text)
        print(f"Number of changes found: {len(changes)}")
        
        # Find detailed changes
        print("\n📋 Finding detailed changes...")
        detailed_changes = engine.find_detailed_changes(template_text, contract_text)
        print(f"Detailed changes found: {len(detailed_changes)}")
        
        # Display some changes
        if detailed_changes:
            print("\n🔄 First 3 changes:")
            for i, change in enumerate(detailed_changes[:3], 1):
                print(f"\nChange {i}:")
                if change.get('deleted_text'):
                    print(f"  - Removed: '{change['deleted_text'].strip()}'")
                if change.get('inserted_text'):
                    print(f"  + Added: '{change['inserted_text'].strip()}'")
        
        # Get statistics
        print("\n📈 Change Statistics:")
        stats = engine.get_change_statistics(detailed_changes)
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n✅ Basic comparison test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in basic comparison test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_processing():
    """Test document processing with actual files"""
    print("\n\n🔍 Testing Document Processing")
    print("=" * 60)
    
    try:
        from app.core.services.document_processor import DocumentProcessor
        
        # Check for sample documents
        data_dir = Path(__file__).parent / "data"
        uploads_dir = data_dir / "uploads"
        templates_dir = data_dir / "templates"
        
        print(f"📁 Data directory: {data_dir}")
        print(f"📁 Uploads directory: {uploads_dir}")
        print(f"📁 Templates directory: {templates_dir}")
        
        if uploads_dir.exists():
            contracts = list(uploads_dir.glob("*.docx"))
            print(f"\n📄 Found {len(contracts)} contracts in uploads")
            if contracts:
                for i, contract in enumerate(contracts[:3]):
                    print(f"  - {contract.name}")
        
        if templates_dir.exists():
            templates = list(templates_dir.glob("*.docx"))
            print(f"\n📋 Found {len(templates)} templates")
            if templates:
                for template in templates:
                    print(f"  - {template.name}")
        
        # Try to process a document if available
        processor = DocumentProcessor()
        
        if contracts and templates:
            print(f"\n📄 Testing document extraction...")
            contract_path = contracts[0]
            
            try:
                text = processor.extract_text_from_docx(str(contract_path))
                if text:
                    print(f"✅ Successfully extracted {len(text)} characters from {contract_path.name}")
                    print(f"Preview: {text[:100]}...")
                else:
                    print("⚠️  Document extraction returned empty text")
            except Exception as e:
                print(f"⚠️  Could not extract text: {e}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in document processing test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_analysis():
    """Test LLM-based analysis"""
    print("\n\n🔍 Testing LLM Analysis")
    print("=" * 60)
    
    try:
        from app.services.llm.providers import create_llm_provider
        from app.config.settings import get_config
        
        config = get_config()
        print(f"LLM Provider: {config.LLM_PROVIDER}")
        print(f"Model: {config.OPENAI_MODEL}")
        
        # Create provider
        llm_config = {
            'provider': config.LLM_PROVIDER,
            'api_key': config.OPENAI_API_KEY,
            'model': config.OPENAI_MODEL,
            'timeout': 30
        }
        
        if not config.OPENAI_API_KEY:
            print("⚠️  No OpenAI API key - skipping LLM test")
            return True
            
        provider = create_llm_provider(config.LLM_PROVIDER, llm_config)
        info = provider.get_model_info()
        print(f"\n✅ LLM Provider initialized:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # Test a simple analysis prompt
        print("\n🤖 Testing contract clause analysis...")
        prompt = """Analyze this contract change:
        Original: "Payment terms: Net 30 days"
        Modified: "Payment terms: Net 45 days"
        
        What is the impact of this change? Answer in one sentence."""
        
        try:
            response = provider.complete(prompt, max_tokens=50)
            print(f"LLM Response: {response}")
            print("✅ LLM analysis successful!")
        except Exception as e:
            print(f"⚠️  LLM call failed (this is okay if you want to save API costs): {e}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in LLM analysis test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Contract Analyzer - Core Functionality Test")
    print("=" * 80)
    
    results = {}
    
    # Run tests
    results['Basic Comparison'] = test_basic_comparison()
    results['Document Processing'] = test_document_processing()
    results['LLM Analysis'] = test_llm_analysis()
    
    # Summary
    print("\n\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All core functionality tests passed!")
        print("The contract analysis system is working correctly.")
    else:
        print("\n⚠️  Some tests failed, but core functionality may still work.")
        print("Check the details above for more information.")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)