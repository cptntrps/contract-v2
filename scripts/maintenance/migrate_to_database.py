#!/usr/bin/env python3
"""
Database migration script to move from in-memory storage to SQLAlchemy database
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flask import Flask
from app.database import init_app, db
from app.database.repositories import ContractRepository, AnalysisRepository

# Legacy stores will be empty initially - we'll populate from files
contracts_store = {}
analysis_results_store = {}

def create_migration_app():
    """Create Flask app for migration"""
    app = Flask(__name__)
    
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///contract_analyzer.db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'migration-key'
    })
    
    # Initialize database
    init_app(app)
    
    return app

def migrate_data():
    """Migrate data from in-memory stores to database"""
    print("🔄 Starting database migration...")
    
    app = create_migration_app()
    
    with app.app_context():
        try:
            # Create all database tables
            print("📋 Creating database tables...")
            db.create_all()
            
            # Initialize repositories
            contract_repo = ContractRepository()
            analysis_repo = AnalysisRepository()
            
            # Migrate contracts
            print(f"📦 Migrating {len(contracts_store)} contracts...")
            migrated_contracts = contract_repo.migrate_from_memory_store(contracts_store)
            print(f"✅ Migrated {migrated_contracts} contracts to database")
            
            # Migrate analysis results
            print(f"🔍 Migrating {len(analysis_results_store)} analysis results...")
            migrated_analyses = analysis_repo.migrate_from_memory_store(analysis_results_store)
            print(f"✅ Migrated {migrated_analyses} analysis results to database")
            
            # Verify migration
            total_contracts = contract_repo.count()
            total_analyses = analysis_repo.count()
            
            print(f"\n📊 Migration Summary:")
            print(f"   📁 Total Contracts: {total_contracts}")
            print(f"   🔍 Total Analyses: {total_analyses}")
            print(f"   🎯 Migration completed successfully!")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def verify_migration():
    """Verify migration was successful"""
    print("\n🔍 Verifying migration...")
    
    app = create_migration_app()
    
    with app.app_context():
        try:
            contract_repo = ContractRepository()
            analysis_repo = AnalysisRepository()
            
            # Get database statistics
            contracts = contract_repo.get_all()
            analyses = analysis_repo.get_all()
            
            print(f"✅ Database verification:")
            print(f"   📁 Contracts in database: {len(contracts)}")
            print(f"   🔍 Analyses in database: {len(analyses)}")
            
            # Show recent items
            if contracts:
                recent_contracts = contract_repo.get_recent(3)
                print(f"   📋 Recent contracts:")
                for contract in recent_contracts:
                    print(f"      - {contract.id}: {contract.original_filename}")
            
            if analyses:
                recent_analyses = analysis_repo.get_recent(3)
                print(f"   📋 Recent analyses:")
                for analysis in recent_analyses:
                    print(f"      - {analysis.id}: {analysis.contract_id} ({analysis.overall_risk_level})")
            
            return True
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

def main():
    """Main migration function"""
    print("🚀 Contract Analyzer Database Migration")
    print("=" * 50)
    
    # Check if database exists
    db_path = Path("contract_analyzer.db")
    if db_path.exists():
        response = input(f"Database {db_path} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Migration cancelled")
            return False
        
        # Backup existing database
        backup_path = db_path.with_suffix('.db.backup')
        db_path.rename(backup_path)
        print(f"📋 Backed up existing database to {backup_path}")
    
    # Perform migration
    success = migrate_data()
    
    if success:
        # Verify migration
        verify_migration()
        print("\n🎉 Migration completed successfully!")
        print(f"📊 Database created: {db_path.absolute()}")
        return True
    else:
        print("\n❌ Migration failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)