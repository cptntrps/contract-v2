#!/usr/bin/env python3
"""
Test contract analysis with a known working contract ID
"""
import requests
import json
import time

def test_analysis():
    """Test analysis with specific contract IDs that should work"""
    print("🚀 Testing Contract Analysis with Known IDs")
    print("=" * 80)
    
    base_url = "http://localhost:5000/api"
    
    # These are contract IDs we know exist from the initialization test
    test_contracts = [
        ("contract_015", "Contract_015_Generic_SOW_MODIFIED_20240301.docx"),
        ("contract_001", "Contract_001_Generic_SOW_20240115.docx"),
        ("contract_008", "Contract_008_Capgemini_SOW_20240208.docx")
    ]
    
    success_count = 0
    
    for contract_id, filename in test_contracts:
        print(f"\n📄 Testing: {filename}")
        print(f"   ID: {contract_id}")
        
        # Check if contract exists first
        response = requests.get(f"{base_url}/contracts/{contract_id}")
        if response.status_code != 200:
            print(f"   ⚠️  Contract GET returned {response.status_code}")
        
        # Try analysis
        payload = {'contract_id': contract_id}
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/analyze-contract",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            elapsed = time.time() - start_time
            
            print(f"   Response time: {elapsed:.2f}s")
            print(f"   Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data.get('result', {})
                    print("   ✅ Analysis successful!")
                    print(f"   Template: {result.get('template', 'N/A')}")
                    print(f"   Similarity: {result.get('similarity', 0):.2f}%")
                    print(f"   Changes: {result.get('total_changes', 0)}")
                    success_count += 1
                else:
                    print(f"   ❌ Analysis failed: {data.get('error', 'Unknown')}")
            else:
                print(f"   ❌ HTTP error: {response.status_code}")
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {'error': response.text[:200]}
                print(f"   Error: {error_data.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n📊 Summary: {success_count}/{len(test_contracts)} analyses succeeded")
    
    # If all failed, try to trigger initialization
    if success_count == 0:
        print("\n🔄 All analyses failed. Trying to reinitialize contracts...")
        
        # Try to clear and reload
        response = requests.post(f"{base_url}/contracts/clear")
        print(f"Clear contracts: {response.status_code}")
        
        # Wait a moment
        time.sleep(1)
        
        # Check contracts again
        response = requests.get(f"{base_url}/contracts")
        if response.status_code == 200:
            contracts = response.json().get('contracts', [])
            print(f"Contracts after clear: {len(contracts)}")
            
            if contracts:
                # Try one more analysis
                test_id = contracts[0]['id']
                print(f"\n🔄 Retrying with: {test_id}")
                
                response = requests.post(
                    f"{base_url}/analyze-contract",
                    json={'contract_id': test_id},
                    timeout=30
                )
                
                if response.status_code == 200 and response.json().get('success'):
                    print("✅ Analysis worked after reinitialization!")
                else:
                    print("❌ Still failing after reinitialization")
                    print("\n💡 Possible issues:")
                    print("   1. The Flask app may need to be restarted")
                    print("   2. The contracts store may not be shared between requests")
                    print("   3. There may be a database connection issue")
    
    return success_count > 0

if __name__ == "__main__":
    success = test_analysis()
    import sys
    sys.exit(0 if success else 1)