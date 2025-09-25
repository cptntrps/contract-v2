#!/usr/bin/env python3
"""
Test analyzing a specific contract through the API
"""
import requests
import json
import time

def test_analyze_specific_contract():
    """Test analyzing a specific contract"""
    print("🚀 Testing Contract Analysis")
    print("=" * 80)
    
    base_url = "http://localhost:5000/api"
    
    # 1. Get contracts
    print("\n📄 Getting contracts list...")
    response = requests.get(f"{base_url}/contracts")
    if response.status_code != 200:
        print(f"❌ Failed to get contracts: {response.text}")
        return False
        
    contracts = response.json().get('contracts', [])
    print(f"Found {len(contracts)} contracts")
    
    if not contracts:
        print("❌ No contracts available")
        return False
    
    # Find a good test contract
    test_contract = None
    for contract in contracts:
        if 'SOW' in contract['filename'] and 'Generic' in contract['filename']:
            test_contract = contract
            break
    
    if not test_contract:
        test_contract = contracts[0]  # Use first contract as fallback
    
    contract_id = test_contract['id']
    contract_name = test_contract['filename']
    
    print(f"\n📄 Selected contract: {contract_name}")
    print(f"   ID: {contract_id}")
    
    # 2. Analyze the contract
    print(f"\n🔍 Starting analysis...")
    start_time = time.time()
    
    analyze_payload = {
        'contract_id': contract_id
    }
    
    print(f"   Payload: {json.dumps(analyze_payload)}")
    
    try:
        response = requests.post(
            f"{base_url}/analyze-contract",
            json=analyze_payload,
            headers={'Content-Type': 'application/json'},
            timeout=120
        )
        
        elapsed = time.time() - start_time
        print(f"   Response time: {elapsed:.2f}s")
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                result = data.get('result', {})
                print("\n✅ Analysis successful!")
                
                # Display results
                print("\n📊 Analysis Results:")
                print(f"   Analysis ID: {result.get('analysis_id', 'N/A')}")
                print(f"   Template matched: {result.get('template', 'N/A')}")
                print(f"   Similarity score: {result.get('similarity', 0):.2f}%")
                print(f"   Total changes: {result.get('total_changes', 0)}")
                print(f"   Status: {result.get('status', 'N/A')}")
                
                # Show template selection reasoning
                if result.get('template_selection'):
                    print(f"\n🧠 Template Selection:")
                    selection = result['template_selection']
                    print(f"   Method: {selection.get('method', 'N/A')}")
                    print(f"   Reason: {selection.get('reason', 'N/A')}")
                
                # Show some changes
                changes = result.get('changes', [])
                if changes:
                    print(f"\n📝 Sample changes (showing first 3):")
                    for i, change in enumerate(changes[:3], 1):
                        print(f"\n   Change {i}:")
                        print(f"     Type: {change.get('type', 'N/A')}")
                        print(f"     Category: {change.get('category', 'N/A')}")
                        if change.get('old_text'):
                            print(f"     Old: \"{change['old_text'][:60]}...\"")
                        if change.get('new_text'):
                            print(f"     New: \"{change['new_text'][:60]}...\"")
                        if change.get('explanation'):
                            print(f"     Explanation: {change['explanation']}")
                
                return True
            else:
                error = data.get('error', 'Unknown error')
                print(f"\n❌ Analysis failed: {error}")
                
                # Check for specific error types
                if 'not found' in error.lower():
                    print("\n⚠️  Contract not found. This might be a database sync issue.")
                    print("   Try uploading a new contract or clearing the cache.")
                elif 'database' in error.lower():
                    print("\n⚠️  Database error. The system may be using in-memory storage.")
                
                return False
        else:
            print(f"\n❌ HTTP error {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.Timeout:
        print(f"\n❌ Request timed out after {elapsed:.2f}s")
        print("   The analysis may be taking longer than expected.")
        return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def test_templates():
    """Test template listing"""
    print("\n\n📋 Testing Template Management")
    print("=" * 80)
    
    response = requests.get("http://localhost:5000/api/templates")
    if response.status_code == 200:
        data = response.json()
        templates = data.get('templates', [])
        print(f"Found {len(templates)} templates:")
        
        for template in templates:
            print(f"  - {template.get('filename', 'N/A')} ({template.get('file_size', 0):,} bytes)")
        
        return True
    else:
        print(f"❌ Failed to get templates: {response.status_code}")
        return False

def main():
    """Run the tests"""
    print("🧪 Contract Analysis API Test")
    print("=" * 80)
    
    # Check server health first
    try:
        health = requests.get("http://localhost:5000/api/health", timeout=2)
        if health.status_code != 200:
            print("❌ API server not healthy")
            return False
    except:
        print("❌ API server not running. Start it with:")
        print("   source venv/bin/activate && python run_app.py")
        return False
    
    # Run tests
    results = {
        'Templates': test_templates(),
        'Analysis': test_analyze_specific_contract()
    }
    
    # Summary
    print("\n\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)