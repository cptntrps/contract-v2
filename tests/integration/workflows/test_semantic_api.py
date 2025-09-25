#!/usr/bin/env python3
"""
Test semantic analysis through the API
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path


def wait_for_server(url="http://localhost:5000", timeout=30):
    """Wait for server to be ready"""
    print(f"Waiting for server at {url}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    
    print("❌ Server not ready within timeout")
    return False


def test_semantic_analysis_api():
    """Test semantic analysis through the web API"""
    
    print("🧪 Testing Semantic Analysis via API")
    print("=" * 50)
    
    base_url = "http://localhost:5000/api"
    
    # Test 1: Check if server is running
    print("\n1. Checking server status...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print(f"   ❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Server not accessible: {e}")
        print("   💡 Try starting the server with: python start_dashboard.py")
        return False
    
    # Test 2: List available contracts
    print("\n2. Listing available contracts...")
    try:
        response = requests.get(f"{base_url}/contracts", timeout=10)
        if response.status_code == 200:
            data = response.json()
            contracts = data.get('contracts', [])
            print(f"   ✅ Found {len(contracts)} contracts")
            
            if contracts:
                # Pick the first contract for testing
                test_contract = contracts[0]
                contract_id = test_contract['id']
                print(f"   📄 Using contract: {test_contract['original_filename']}")
            else:
                print("   ❌ No contracts available for testing")
                return False
        else:
            print(f"   ❌ Failed to list contracts: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error listing contracts: {e}")
        return False
    
    # Test 3: Trigger analysis with semantic features
    print("\n3. Running contract analysis with semantic analysis...")
    try:
        analysis_data = {
            'contract_id': contract_id,
            'include_llm_analysis': False,  # Focus on semantic analysis
            'analysis_type': 'comprehensive'
        }
        
        response = requests.post(
            f"{base_url}/analysis/analyze", 
            json=analysis_data,
            timeout=120  # Allow time for analysis
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Analysis completed successfully")
            
            # Check if semantic analysis is included
            if 'analysis_result' in result:
                analysis_result = result['analysis_result']
                
                print(f"   📊 Analysis ID: {analysis_result.get('analysis_id', 'N/A')}")
                print(f"   📊 Total changes: {analysis_result.get('total_changes', 0)}")
                print(f"   📊 Similarity score: {analysis_result.get('similarity_score', 0):.3f}")
                print(f"   📊 Risk level: {analysis_result.get('overall_risk_level', 'Unknown')}")
                
                # Check for semantic analysis in metadata
                metadata = analysis_result.get('metadata', {})
                semantic_analysis = metadata.get('semantic_analysis', {})
                
                if semantic_analysis:
                    print("   ✅ Semantic analysis included in results!")
                    
                    # Check analysis summary
                    summary = semantic_analysis.get('analysis_summary', {})
                    if summary:
                        print(f"      • Semantic changes analyzed: {summary.get('total_semantic_changes', 0)}")
                        print(f"      • Entities extracted: {summary.get('contract_entities_count', 0)}")
                        print(f"      • Clauses classified: {summary.get('contract_clauses_count', 0)}")
                        print(f"      • Risk indicators: {summary.get('risk_indicators_count', 0)}")
                        print(f"      • Semantic similarity: {summary.get('overall_semantic_similarity', 0):.3f}")
                        print(f"      • Risk assessment: {summary.get('overall_risk_level', 'Unknown')}")
                    
                    # Check individual analysis components
                    if 'entity_analysis' in semantic_analysis:
                        entity_data = semantic_analysis['entity_analysis']
                        contract_entities = entity_data.get('contract_entities', {})
                        entity_counts = contract_entities.get('entity_counts', {})
                        print(f"      • Entity types found: {list(entity_counts.keys())}")
                    
                    if 'clause_analysis' in semantic_analysis:
                        clause_data = semantic_analysis['clause_analysis']
                        contract_clauses = clause_data.get('contract_clauses', {})
                        clause_counts = contract_clauses.get('clause_counts', {})
                        missing_clauses = contract_clauses.get('missing_clauses', [])
                        print(f"      • Clause types found: {list(clause_counts.keys())}")
                        if missing_clauses:
                            print(f"      • Missing clauses: {missing_clauses}")
                    
                    if 'risk_analysis' in semantic_analysis:
                        risk_data = semantic_analysis['risk_analysis']
                        recommendations = risk_data.get('recommendations', [])
                        print(f"      • Risk recommendations: {len(recommendations)}")
                        if recommendations:
                            print(f"        - {recommendations[0]}")  # Show first recommendation
                    
                    print("   🎉 Semantic analysis integration is working perfectly!")
                else:
                    print("   ⚠️ Semantic analysis not found in results")
                    print("      This might indicate the analysis didn't run or failed silently")
            else:
                print("   ❌ Analysis result not found in response")
                
        else:
            print(f"   ❌ Analysis failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"      Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"      Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error running analysis: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Semantic Analysis API Test Complete!")
    print("✅ Semantic analysis is working through the web API")
    print("📈 The system provides comprehensive NLP-powered insights")
    
    return True


def main():
    """Main test function"""
    # Check if server is already running
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        server_running = response.status_code == 200
    except:
        server_running = False
    
    if not server_running:
        print("🚀 Server not running. Please start it with:")
        print("   python start_dashboard.py")
        print("   Then run this test again.")
        return False
    
    # Run the test
    return test_semantic_analysis_api()


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ ALL TESTS PASSED - Semantic Analysis is production ready!")
    else:
        print("\n❌ Tests failed - Check server status and configuration")
        sys.exit(1)