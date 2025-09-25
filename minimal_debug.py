#!/usr/bin/env python3
"""
Minimal debug script to test contracts visibility without complex dependencies
"""

import sqlite3
import json
from pathlib import Path

def test_database_directly():
    """Test database directly without ORM"""
    print("=== TESTING DATABASE DIRECTLY ===")
    
    db_path = Path('instance/contract_analyzer.db')
    if not db_path.exists():
        print("Database not found")
        return []
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all contracts
    cursor.execute("SELECT id, filename, original_filename, status, upload_timestamp FROM contracts")
    contracts = cursor.fetchall()
    
    print(f"Database contains {len(contracts)} contracts:")
    for contract in contracts[:5]:  # Show first 5
        print(f"  - {contract[0]}: {contract[2]} ({contract[3]})")
    
    conn.close()
    return contracts

def create_simple_dashboard_data(contracts):
    """Create simple dashboard data structure"""
    print("\n=== CREATING DASHBOARD DATA ===")
    
    # Convert database rows to dashboard format
    dashboard_contracts = []
    for contract in contracts:
        dashboard_contracts.append({
            'id': contract[0],
            'filename': contract[1], 
            'original_filename': contract[2],
            'status': contract[3],
            'upload_date': contract[4] if len(contract) > 4 else None
        })
    
    # Create metrics
    metrics = {
        'total_contracts': len(dashboard_contracts),
        'total_templates': 5,  # Mock count
        'total_analyses': 0,   # No analyses yet
        'pending_reviews': 0
    }
    
    # Create dashboard data structure
    dashboard_data = {
        'metrics': metrics,
        'contracts': dashboard_contracts,
        'analysis_results': [],  # Empty for now
        'templates': [
            {'id': 'TYPE_SOW_Standard_v1', 'filename': 'TYPE_SOW_Standard_v1.docx'},
            {'id': 'TYPE_CHANGEORDER_Standard_v1', 'filename': 'TYPE_CHANGEORDER_Standard_v1.docx'}
        ],
        'system_status': {'status': 'healthy'}
    }
    
    return dashboard_data

def create_mock_api_response(dashboard_data):
    """Create mock API response"""
    print("\n=== MOCK API RESPONSE ===")
    
    # Simulate /api/dashboard/data response
    api_response = {
        'success': True,
        'data': dashboard_data,
        'message': 'Dashboard data retrieved successfully'
    }
    
    print("API Response structure:")
    print(f"  - success: {api_response['success']}")
    print(f"  - contracts: {len(api_response['data']['contracts'])}")
    print(f"  - metrics: {api_response['data']['metrics']}")
    
    return api_response

def test_javascript_expectations():
    """Test what the JavaScript expects"""
    print("\n=== JAVASCRIPT EXPECTATIONS ===")
    
    # Based on dashboard.js, it expects:
    expected_structure = {
        'data': {
            'contracts': [],        # Array of contract objects
            'analysisResults': [],  # Array of analysis results  
            'metrics': {
                'total_contracts': 0,
                'total_templates': 0,
                'total_analyses': 0,
                'pending_reviews': 0
            },
            'systemStatus': {
                'status': 'healthy'
            }
        }
    }
    
    print("JavaScript expects this structure:")
    print(json.dumps(expected_structure, indent=2))

if __name__ == "__main__":
    print("Minimal Dashboard Debug")
    print("=" * 50)
    
    # Test database
    contracts = test_database_directly()
    
    if contracts:
        # Create dashboard data
        dashboard_data = create_simple_dashboard_data(contracts)
        
        # Create API response 
        api_response = create_mock_api_response(dashboard_data)
        
        # Show what JavaScript expects
        test_javascript_expectations()
        
        print("\n=== ISSUE ANALYSIS ===")
        print("The dashboard has contracts in the database but they're not showing up.")
        print("Key potential issues:")
        print("1. API endpoint not returning data in expected format")
        print("2. JavaScript not receiving/processing the data correctly") 
        print("3. Missing dependencies preventing API from working")
        print("4. Dashboard service not connecting to database properly")
        
        print(f"\nFound {len(contracts)} contracts in database")
        print("These should be visible on dashboard if API is working")
    else:
        print("No contracts found in database")