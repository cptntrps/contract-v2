#!/usr/bin/env python3
"""
Simple debug script to test dashboard functionality without complex logging
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment to disable complex logging
os.environ['FLASK_ENV'] = 'testing'

def debug_contracts_store():
    """Debug the contracts store directly"""
    print("=== DEBUGGING CONTRACTS STORE ===")
    
    try:
        from app.api.routes.contracts import contracts_store
        print(f"Contracts store type: {type(contracts_store)}")
        print(f"Contracts store length: {len(contracts_store)}")
        print(f"Contracts store keys: {list(contracts_store.keys())[:5]}")
        
        if contracts_store:
            first_contract_id = list(contracts_store.keys())[0]
            first_contract = contracts_store[first_contract_id]
            print(f"Sample contract: {first_contract}")
            print(f"Sample contract type: {type(first_contract)}")
            if hasattr(first_contract, '__dict__'):
                print(f"Sample contract attributes: {first_contract.__dict__}")
        
    except Exception as e:
        print(f"Error accessing contracts store: {e}")
        import traceback
        traceback.print_exc()

def debug_analysis_results():
    """Debug the analysis results store"""
    print("\n=== DEBUGGING ANALYSIS RESULTS ===")
    
    try:
        from app.api.routes.analysis import analysis_results_store
        print(f"Analysis results store type: {type(analysis_results_store)}")
        print(f"Analysis results store length: {len(analysis_results_store)}")
        print(f"Analysis results store keys: {list(analysis_results_store.keys())}")
        
    except Exception as e:
        print(f"Error accessing analysis results store: {e}")
        import traceback
        traceback.print_exc()

def debug_dashboard_service():
    """Debug the dashboard service"""
    print("\n=== DEBUGGING DASHBOARD SERVICE ===")
    
    try:
        from app.application.services.dashboard_service import DashboardService
        
        dashboard_service = DashboardService()
        print("Dashboard service created successfully")
        
        # Test getting contracts count
        try:
            contracts_count = dashboard_service._get_contracts_count()
            print(f"Contracts count: {contracts_count}")
        except Exception as e:
            print(f"Error getting contracts count: {e}")
        
        # Test getting analysis results
        try:
            analysis_results = dashboard_service._get_analysis_results()
            print(f"Analysis results count: {len(analysis_results)}")
            print(f"Sample analysis result: {analysis_results[0] if analysis_results else 'None'}")
        except Exception as e:
            print(f"Error getting analysis results: {e}")
            import traceback
            traceback.print_exc()
        
        # Test getting dashboard metrics
        try:
            metrics = dashboard_service.get_dashboard_metrics()
            print(f"Dashboard metrics: {metrics}")
        except Exception as e:
            print(f"Error getting dashboard metrics: {e}")
            import traceback
            traceback.print_exc()
        
        # Test getting full dashboard data
        try:
            dashboard_data = dashboard_service.get_dashboard_data()
            print(f"Full dashboard data keys: {dashboard_data.keys()}")
            print(f"Metrics: {dashboard_data.get('metrics', {})}")
            print(f"Analysis results count: {len(dashboard_data.get('analysis_results', []))}")
            print(f"Contracts count: {len(dashboard_data.get('contracts', []))}")
        except Exception as e:
            print(f"Error getting dashboard data: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"Error creating dashboard service: {e}")
        import traceback
        traceback.print_exc()

def debug_database():
    """Debug database content"""
    print("\n=== DEBUGGING DATABASE ===")
    
    try:
        import sqlite3
        
        db_path = project_root / 'instance' / 'contract_analyzer.db'
        if not db_path.exists():
            print(f"Database not found at {db_path}")
            return
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check contracts table
        cursor.execute("SELECT COUNT(*) FROM contracts")
        contracts_count = cursor.fetchone()[0]
        print(f"Database contracts count: {contracts_count}")
        
        # Check analysis_results table
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        analysis_count = cursor.fetchone()[0]
        print(f"Database analysis results count: {analysis_count}")
        
        # Sample contracts
        cursor.execute("SELECT id, original_filename, status FROM contracts LIMIT 3")
        sample_contracts = cursor.fetchall()
        print(f"Sample contracts: {sample_contracts}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error accessing database: {e}")
        import traceback
        traceback.print_exc()

def debug_contract_repository():
    """Debug the contract repository"""
    print("\n=== DEBUGGING CONTRACT REPOSITORY ===")
    
    try:
        from app.database.repositories import ContractRepository
        
        repo = ContractRepository()
        print("Contract repository created successfully")
        
        # Test getting recent contracts
        try:
            contracts = repo.get_recent(limit=5)
            print(f"Recent contracts count: {len(contracts)}")
            if contracts:
                sample_contract = contracts[0]
                print(f"Sample contract: {sample_contract}")
                print(f"Sample contract type: {type(sample_contract)}")
                if hasattr(sample_contract, 'get_summary'):
                    print(f"Sample contract summary: {sample_contract.get_summary()}")
        except Exception as e:
            print(f"Error getting recent contracts: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"Error creating contract repository: {e}")
        import traceback
        traceback.print_exc()

def debug_file_initialization():
    """Debug contract file initialization"""
    print("\n=== DEBUGGING FILE INITIALIZATION ===")
    
    try:
        # Check if uploads directory exists
        uploads_dir = project_root / 'data' / 'uploads'
        print(f"Uploads directory exists: {uploads_dir.exists()}")
        if uploads_dir.exists():
            docx_files = list(uploads_dir.glob('*.docx'))
            print(f"DOCX files in uploads: {len(docx_files)}")
            print(f"Sample files: {[f.name for f in docx_files[:5]]}")
        
        # Test initialization function
        from app.api.routes.contracts import initialize_contracts_from_uploads
        
        # Create a mock Flask app context
        from flask import Flask
        app = Flask(__name__)
        app.config['UPLOAD_FOLDER'] = str(uploads_dir)
        
        with app.app_context():
            initialize_contracts_from_uploads()
            
            # Check contracts store after initialization
            from app.api.routes.contracts import contracts_store
            print(f"Contracts store after initialization: {len(contracts_store)} contracts")
        
    except Exception as e:
        print(f"Error in file initialization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting Dashboard Debug...")
    
    debug_database()
    debug_contract_repository() 
    debug_file_initialization()
    debug_contracts_store()
    debug_analysis_results()
    debug_dashboard_service()
    
    print("\nDebug completed!")