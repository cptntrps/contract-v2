#!/usr/bin/env python3
"""
Debug contract storage issues
"""
import requests
import json

def debug_contracts():
    """Debug contract storage and IDs"""
    print("🔍 Debugging Contract Storage")
    print("=" * 80)
    
    base_url = "http://localhost:5000/api"
    
    # 1. Get contracts list
    print("\n📄 Fetching contracts...")
    response = requests.get(f"{base_url}/contracts")
    
    if response.status_code != 200:
        print(f"❌ Failed to get contracts: {response.status_code}")
        return
    
    data = response.json()
    contracts = data.get('contracts', [])
    
    print(f"\nFound {len(contracts)} contracts:")
    print("\nContract ID Mapping:")
    print("-" * 60)
    print(f"{'ID':<20} {'Filename':<40}")
    print("-" * 60)
    
    for contract in contracts[:10]:  # Show first 10
        contract_id = contract.get('id', 'N/A')
        filename = contract.get('filename', 'N/A')
        print(f"{contract_id:<20} {filename:<40}")
    
    # 2. Try to get a specific contract
    if contracts:
        test_id = contracts[0]['id']
        print(f"\n\n🔍 Testing GET /api/contracts/{test_id}")
        
        response = requests.get(f"{base_url}/contracts/{test_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Contract retrieval works")
            contract_data = response.json()
            print(f"Contract: {contract_data.get('filename', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
    
    # 3. Test analysis with correct ID
    if contracts:
        # Find a good test contract
        test_contract = None
        for c in contracts:
            if 'Generic' in c['filename'] and 'SOW' in c['filename']:
                test_contract = c
                break
        
        if not test_contract:
            test_contract = contracts[0]
        
        test_id = test_contract['id']
        print(f"\n\n🔍 Testing analysis with contract ID: {test_id}")
        print(f"   Filename: {test_contract['filename']}")
        
        # Get templates first
        templates_response = requests.get(f"{base_url}/templates")
        if templates_response.status_code == 200:
            templates = templates_response.json().get('templates', [])
            print(f"   Available templates: {len(templates)}")
        
        # Try analysis
        payload = {'contract_id': test_id}
        print(f"\n   Sending POST /api/analyze-contract")
        print(f"   Payload: {json.dumps(payload)}")
        
        response = requests.post(
            f"{base_url}/analyze-contract",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Analysis successful!")
                analysis = result.get('result', {})
                print(f"   Template: {analysis.get('template', 'N/A')}")
                print(f"   Similarity: {analysis.get('similarity', 0):.2f}%")
            else:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown')}")
        else:
            print(f"❌ HTTP Error: {response.text[:200]}")

if __name__ == "__main__":
    debug_contracts()