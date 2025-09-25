#!/usr/bin/env python3
"""
Test contract initialization and storage
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_contract_initialization():
    """Test how contracts are initialized"""
    print("🔍 Testing Contract Store Initialization")
    print("=" * 80)
    
    # Import the contracts module
    from app.api.routes.contracts import contracts_store, initialize_contracts_from_uploads
    from pathlib import Path
    
    # Check initial state
    print(f"\nInitial contracts in store: {len(contracts_store)}")
    if contracts_store:
        print("First 5 contracts:")
        for i, (cid, contract) in enumerate(list(contracts_store.items())[:5]):
            print(f"  {cid}: {contract.filename}")
    
    # Manually initialize with Flask context
    from app.api.app import create_api_app
    from app.config.settings import get_config
    
    config = get_config()
    app = create_api_app(config)
    
    with app.app_context():
        print("\n🔄 Running initialize_contracts_from_uploads()...")
        initialize_contracts_from_uploads()
        
        print(f"\nContracts in store after init: {len(contracts_store)}")
        if contracts_store:
            print("\nAll contracts in store:")
            print("-" * 60)
            for cid, contract in contracts_store.items():
                print(f"{cid}: {contract.filename}")
        
        # Check uploads directory
        upload_dir = Path(app.config.get('UPLOAD_FOLDER', 'data/uploads'))
        print(f"\n📁 Upload directory: {upload_dir}")
        print(f"Directory exists: {upload_dir.exists()}")
        
        if upload_dir.exists():
            docx_files = list(upload_dir.glob('*.docx'))
            print(f"DOCX files in directory: {len(docx_files)}")
            print("\nFirst 5 files:")
            for f in docx_files[:5]:
                print(f"  - {f.name}")
    
    return True

if __name__ == "__main__":
    test_contract_initialization()