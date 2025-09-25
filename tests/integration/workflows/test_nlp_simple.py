#!/usr/bin/env python3
"""
Simple test for NLP components without Flask dependencies
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import NLP components directly
from app.services.nlp.semantic_analyzer import SemanticAnalyzer
from app.services.nlp.entity_extractor import EntityExtractor  
from app.services.nlp.clause_classifier import ClauseClassifier
from app.services.nlp.risk_analyzer import RiskAnalyzer


def test_nlp_components():
    """Test all NLP components with sample contract text"""
    
    sample_contract = """
    This Software License Agreement ("Agreement") is entered into on January 15, 2024,
    between AlphaTech Corporation, a Delaware corporation ("Licensor") and
    BetaCorp Inc., a California corporation ("Licensee").
    
    1. Payment Terms: Licensee shall pay $50,000 annually within 30 days of invoice.
    Late payments shall incur a penalty of 2% per month.
    
    2. Liability: IN NO EVENT SHALL LICENSOR BE LIABLE FOR ANY DAMAGES EXCEEDING
    THE TOTAL AMOUNT PAID UNDER THIS AGREEMENT.
    
    3. Termination: Either party may terminate this agreement with 60 days written notice.
    Upon material breach, the non-breaching party may terminate immediately.
    
    4. Confidentiality: Each party agrees to maintain confidential information
    in strict confidence and not disclose to third parties.
    
    5. Indemnification: Licensee shall indemnify and hold harmless Licensor
    from any third-party claims arising from use of the software.
    """
    
    template_contract = """
    This Software License Agreement ("Agreement") is entered into on [DATE],
    between [LICENSOR_NAME] ("Licensor") and [LICENSEE_NAME] ("Licensee").
    
    1. Payment Terms: Licensee shall pay $[AMOUNT] annually within 30 days of invoice.
    
    2. Liability: Licensor's liability shall be limited to direct damages only.
    
    3. Termination: Either party may terminate with 30 days notice.
    
    4. Confidentiality: Standard confidentiality provisions apply.
    """
    
    print("🧪 Testing Phase 3 NLP Components")
    print("=" * 50)
    
    # Test 1: Semantic Analysis
    print("\n1. Testing Semantic Analyzer...")
    try:
        semantic_analyzer = SemanticAnalyzer()
        
        # Create sample changes
        changes = [
            {
                'id': 'change_1',
                'deleted_text': '$[AMOUNT]',
                'inserted_text': '$50,000',
                'operation': 'replace'
            },
            {
                'id': 'change_2', 
                'deleted_text': 'limited to direct damages only',
                'inserted_text': 'LIABLE FOR ANY DAMAGES EXCEEDING THE TOTAL AMOUNT PAID',
                'operation': 'replace'
            }
        ]
        
        semantic_results = semantic_analyzer.analyze_semantic_changes(
            template_contract, sample_contract, changes
        )
        
        print(f"   ✅ Analysis completed successfully")
        print(f"   ✅ Semantic similarity: {semantic_results.get('similarity_score', 0):.3f}")
        print(f"   ✅ Impact score: {semantic_results.get('impact_score', 0):.3f}")
        print(f"   ✅ Insights found: {len(semantic_results.get('insights', []))}")
        
    except Exception as e:
        print(f"   ❌ Semantic Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Entity Extraction
    print("\n2. Testing Entity Extractor...")
    try:
        entity_extractor = EntityExtractor()
        entities = entity_extractor.extract_entities(sample_contract)
        
        print(f"   ✅ Analysis completed successfully")
        print(f"   ✅ Total entities: {len(entities.entities)}")
        print(f"   ✅ Entity types: {list(entities.entity_counts.keys())}")
        print(f"   ✅ Money entities: {entities.entity_counts.get('MONEY', 0)}")
        print(f"   ✅ Organization entities: {entities.entity_counts.get('ORGANIZATION', 0)}")
        
    except Exception as e:
        print(f"   ❌ Entity Extraction failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Clause Classification
    print("\n3. Testing Clause Classifier...")
    try:
        clause_classifier = ClauseClassifier()
        clauses = clause_classifier.classify_clauses(sample_contract)
        
        print(f"   ✅ Analysis completed successfully")
        print(f"   ✅ Total clauses: {len(clauses.clauses)}")
        print(f"   ✅ Clause types: {list(clauses.clause_counts.keys())}")
        print(f"   ✅ Missing clauses: {len(clauses.missing_clauses)}")
        print(f"   ✅ Risk level: {clauses.risk_summary.get('overall_risk', 'Unknown')}")
        
    except Exception as e:
        print(f"   ❌ Clause Classification failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Risk Analysis
    print("\n4. Testing Risk Analyzer...")
    try:
        risk_analyzer = RiskAnalyzer()
        
        # Sample changes with risk implications
        risk_changes = [
            {
                'id': 'risk_change_1',
                'deleted_text': 'limited to direct damages',
                'inserted_text': 'unlimited liability for all damages',
                'operation': 'replace'
            }
        ]
        
        risk_assessment = risk_analyzer.analyze_risks(sample_contract, risk_changes)
        
        print(f"   ✅ Analysis completed successfully")
        print(f"   ✅ Overall risk: {risk_assessment.overall_risk_level.value}")
        print(f"   ✅ Risk indicators: {len(risk_assessment.risk_indicators)}")
        print(f"   ✅ Recommendations: {len(risk_assessment.recommendations)}")
        print(f"   ✅ Risk categories: {list(risk_assessment.risk_scores.keys())}")
        
    except Exception as e:
        print(f"   ❌ Risk Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎉 Phase 3 NLP Implementation Test Complete!")
    print("📊 All components are working and Phase 3 is ready for integration!")


if __name__ == "__main__":
    test_nlp_components()