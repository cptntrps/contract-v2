#!/usr/bin/env python3
"""
Phase 1 Implementation: Test Consolidation
Safely moves test files to proper directory structure.
"""

import os
import shutil
from pathlib import Path
import sys

class TestConsolidator:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.root_path = Path(__file__).parent.parent
        self.tests_path = self.root_path / 'tests'
        self.moved_files = []
        self.errors = []
        
    def create_test_structure(self):
        """Create the test directory structure."""
        directories = [
            'tests/unit/models',
            'tests/unit/services', 
            'tests/unit/utils',
            'tests/unit/api',
            'tests/integration/analysis',
            'tests/integration/reports',
            'tests/integration/workflows',
            'tests/fixtures/contracts',
            'tests/fixtures/templates',
        ]
        
        for dir_path in directories:
            full_path = self.root_path / dir_path
            if self.dry_run:
                print(f"[DRY RUN] Would create: {dir_path}")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created: {dir_path}")
                
    def categorize_test_file(self, filename):
        """Determine which subdirectory a test file should go to."""
        name_lower = filename.lower()
        
        # Integration tests
        if any(x in name_lower for x in ['integration', 'api', 'workflow', 'full', 'complete']):
            if 'analysis' in name_lower:
                return 'tests/integration/analysis'
            elif 'report' in name_lower:
                return 'tests/integration/reports'
            else:
                return 'tests/integration/workflows'
        
        # Unit tests by component
        if any(x in name_lower for x in ['model', 'contract', 'template']):
            return 'tests/unit/models'
        elif any(x in name_lower for x in ['service', 'analyzer', 'processor']):
            return 'tests/unit/services'
        elif any(x in name_lower for x in ['util', 'helper', 'validator']):
            return 'tests/unit/utils'
        elif any(x in name_lower for x in ['route', 'endpoint', 'api']):
            return 'tests/unit/api'
        
        # Default to integration
        return 'tests/integration/workflows'
        
    def move_test_files(self):
        """Move test files from root to appropriate test directories."""
        test_files = [f for f in self.root_path.glob('test_*.py')]
        
        print(f"\nFound {len(test_files)} test files in root directory")
        
        for test_file in test_files:
            target_dir = self.categorize_test_file(test_file.name)
            target_path = self.root_path / target_dir / test_file.name
            
            if self.dry_run:
                print(f"[DRY RUN] Would move: {test_file.name} -> {target_dir}/")
            else:
                try:
                    shutil.move(str(test_file), str(target_path))
                    print(f"Moved: {test_file.name} -> {target_dir}/")
                    self.moved_files.append((test_file.name, target_dir))
                except Exception as e:
                    print(f"ERROR moving {test_file.name}: {e}")
                    self.errors.append((test_file.name, str(e)))
                    
    def move_debug_scripts(self):
        """Move debug scripts to scripts/debug/."""
        debug_dir = self.root_path / 'scripts' / 'debug'
        
        if not self.dry_run:
            debug_dir.mkdir(parents=True, exist_ok=True)
            
        debug_files = list(self.root_path.glob('debug_*.py'))
        debug_files.extend([
            f for f in self.root_path.glob('*.py') 
            if 'debug' in f.name.lower() and f.name != 'debug_runner.py'
        ])
        
        print(f"\nFound {len(debug_files)} debug files")
        
        for debug_file in debug_files:
            target_path = debug_dir / debug_file.name
            
            if self.dry_run:
                print(f"[DRY RUN] Would move: {debug_file.name} -> scripts/debug/")
            else:
                try:
                    shutil.move(str(debug_file), str(target_path))
                    print(f"Moved: {debug_file.name} -> scripts/debug/")
                    self.moved_files.append((debug_file.name, 'scripts/debug'))
                except Exception as e:
                    print(f"ERROR moving {debug_file.name}: {e}")
                    self.errors.append((debug_file.name, str(e)))
                    
    def create_test_config(self):
        """Create pytest configuration file."""
        conftest_content = '''"""
Pytest configuration and shared fixtures.
"""

import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import application for testing
from app.api.app import create_api_app
from app.config.settings import get_test_config

@pytest.fixture
def app():
    """Create application for testing."""
    config = get_test_config()
    app = create_api_app(config)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def sample_contract_data():
    """Sample contract data for testing."""
    return {
        'filename': 'test_contract.docx',
        'content': b'Test contract content',
        'size': 1024
    }
'''
        
        conftest_path = self.tests_path / 'conftest.py'
        
        if self.dry_run:
            print(f"\n[DRY RUN] Would create: tests/conftest.py")
        else:
            conftest_path.write_text(conftest_content)
            print(f"\nCreated: tests/conftest.py")
            
    def create_summary(self):
        """Create summary of changes."""
        summary_content = f'''# Test Consolidation Summary

## Files Moved: {len(self.moved_files)}

### Test Files:
'''
        for filename, target in self.moved_files:
            if filename.startswith('test_'):
                summary_content += f"- {filename} -> {target}/\n"
                
        summary_content += "\n### Debug Scripts:\n"
        for filename, target in self.moved_files:
            if 'debug' in filename.lower():
                summary_content += f"- {filename} -> {target}/\n"
                
        if self.errors:
            summary_content += f"\n## Errors: {len(self.errors)}\n"
            for filename, error in self.errors:
                summary_content += f"- {filename}: {error}\n"
                
        summary_path = self.root_path / 'TEST_CONSOLIDATION_SUMMARY.md'
        
        if not self.dry_run:
            summary_path.write_text(summary_content)
            print(f"\nCreated summary: TEST_CONSOLIDATION_SUMMARY.md")
        
        return summary_content
        
def main():
    """Run test consolidation."""
    print("Test Consolidation - Phase 1")
    print("="*50)
    
    # Check if dry run
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("DRY RUN MODE - No files will be moved")
    else:
        response = input("This will move files. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
            
    consolidator = TestConsolidator(dry_run=dry_run)
    
    # Execute steps
    consolidator.create_test_structure()
    consolidator.move_test_files()
    consolidator.move_debug_scripts()
    consolidator.create_test_config()
    
    # Summary
    summary = consolidator.create_summary()
    print("\n" + "="*50)
    print(summary)
    
    if dry_run:
        print("\nTo execute changes, run without --dry-run flag")

if __name__ == "__main__":
    main()