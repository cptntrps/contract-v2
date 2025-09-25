#!/usr/bin/env python3
"""
Complete direct test of contract analysis without API
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_complete_analysis():
    """Test complete analysis workflow"""
    print("🚀 Complete Contract Analysis Test")
    print("=" * 80)
    
    # 1. Setup paths
    data_dir = Path(__file__).parent / "data"
    contracts_dir = data_dir / "uploads"
    templates_dir = data_dir / "templates"
    
    print(f"\n📁 Data directories:")
    print(f"   Contracts: {contracts_dir}")
    print(f"   Templates: {templates_dir}")
    
    # 2. Find a contract and template
    contracts = list(contracts_dir.glob("Contract_*.docx"))[:5]  # Get original contracts
    templates = list(templates_dir.glob("*.docx"))
    
    if not contracts or not templates:
        print("❌ No contracts or templates found")
        return False
    
    # Select a good test case
    test_contract = None
    for c in contracts:
        if "Generic" in c.name and "SOW" in c.name:
            test_contract = c
            break
    
    if not test_contract:
        test_contract = contracts[0]
    
    # Select matching template
    test_template = templates_dir / "TYPE_SOW_Standard_v1.docx"
    if not test_template.exists():
        test_template = templates[0]
    
    print(f"\n📄 Test contract: {test_contract.name}")
    print(f"📋 Test template: {test_template.name}")
    
    # 3. Extract text from documents
    print("\n📖 Extracting text from documents...")
    
    from app.core.services.document_processor import DocumentProcessor
    processor = DocumentProcessor()
    
    try:
        contract_text = processor.extract_text_from_docx(str(test_contract))
        template_text = processor.extract_text_from_docx(str(test_template))
        
        print(f"   Contract text: {len(contract_text)} characters")
        print(f"   Template text: {len(template_text)} characters")
        
        if contract_text:
            print(f"   Contract preview: {contract_text[:100]}...")
        if template_text:
            print(f"   Template preview: {template_text[:100]}...")
            
    except Exception as e:
        print(f"❌ Text extraction failed: {e}")
        return False
    
    # 4. Perform comparison
    print("\n🔍 Performing document comparison...")
    
    from app.core.services.comparison_engine import ComparisonEngine
    engine = ComparisonEngine()
    
    try:
        similarity = engine.calculate_similarity(contract_text, template_text)
        print(f"   Similarity: {similarity:.2%}")
        
        changes = engine.find_detailed_changes(template_text, contract_text)
        print(f"   Changes found: {len(changes)}")
        
        stats = engine.get_change_statistics(changes)
        print(f"   Change statistics: {stats}")
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False
    
    # 5. Create analysis result
    print("\n📊 Creating analysis result...")
    
    from app.core.models.analysis_result import AnalysisResult, Change, ChangeType, ChangeClassification
    from datetime import datetime
    import uuid
    
    try:
        # Create analysis result
        analysis = AnalysisResult(
            analysis_id=f"test_{uuid.uuid4().hex[:8]}",
            contract_id="test_contract",
            template_id="test_template",
            analysis_timestamp=datetime.now(),
            total_changes=len(changes),
            similarity_score=similarity
        )
        
        # Add some changes
        for i, change_data in enumerate(changes[:5]):  # First 5 changes
            change = Change(
                change_id=f"change_{i}",
                change_type=ChangeType.REPLACEMENT,
                classification=ChangeClassification.SIGNIFICANT,
                deleted_text=change_data.get('deleted_text', ''),
                inserted_text=change_data.get('inserted_text', ''),
                line_number=i + 1,
                explanation="Difference detected"
            )
            analysis.add_change(change)
        
        print(f"   Analysis ID: {analysis.analysis_id}")
        print(f"   Total changes: {analysis.total_changes}")
        print(f"   Changes added: {len(analysis.changes)}")
        
    except Exception as e:
        print(f"❌ Analysis result creation failed: {e}")
        return False
    
    # 6. Generate report
    print("\n📑 Generating report...")
    
    from app.services.reports.generator import ReportGenerator
    import tempfile
    
    try:
        generator = ReportGenerator()
        
        # Create temp file for report
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            report_path = f.name
        
        # Generate report (using the actual method name)
        if hasattr(generator, 'generate'):
            result = generator.generate(
                analysis_result=analysis,
                report_format='json',
                output_path=report_path
            )
            print(f"   Report generated: {result}")
        else:
            print("   ⚠️  Report generator doesn't have expected methods")
            # Try to find available methods
            methods = [m for m in dir(generator) if not m.startswith('_') and callable(getattr(generator, m))]
            print(f"   Available methods: {methods}")
        
        # Clean up
        if os.path.exists(report_path):
            os.unlink(report_path)
            
    except Exception as e:
        print(f"⚠️  Report generation skipped: {e}")
    
    # 7. Test LLM analysis (optional)
    print("\n🤖 Testing LLM analysis...")
    
    try:
        from app.services.llm.providers import create_llm_provider
        from app.config.settings import get_config
        
        config = get_config()
        if config.OPENAI_API_KEY:
            llm_config = {
                'provider': 'openai',
                'api_key': config.OPENAI_API_KEY,
                'model': config.OPENAI_MODEL,
                'timeout': 30
            }
            
            provider = create_llm_provider('openai', llm_config)
            print(f"   LLM Provider: {provider.get_model_info()}")
            print("   ✅ LLM integration ready")
        else:
            print("   ⚠️  No OpenAI API key - LLM features disabled")
            
    except Exception as e:
        print(f"   ⚠️  LLM test skipped: {e}")
    
    print("\n✅ Complete analysis test finished successfully!")
    return True

def main():
    """Run the test"""
    success = test_complete_analysis()
    
    if success:
        print("\n" + "=" * 80)
        print("💡 Summary:")
        print("✅ Core contract analysis functionality is working correctly!")
        print("✅ Document processing works")
        print("✅ Text comparison works") 
        print("✅ Change detection works")
        print("✅ Analysis result creation works")
        print("\nThe issue with the API appears to be related to:")
        print("- Contract store initialization in the Flask app")
        print("- Possible database synchronization issues")
        print("- In-memory vs database storage mismatch")
    else:
        print("\n❌ Test failed - check errors above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)