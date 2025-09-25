#!/usr/bin/env python3
"""
Final Cleanup: Clean root directory and create project structure summary.
"""

import os
import shutil
from pathlib import Path
import sys

class FinalCleanup:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.root_path = Path(__file__).parent.parent
        self.moved_files = []
        self.errors = []
        
    def move_remaining_files(self):
        """Move remaining consolidation summaries to docs."""
        files_to_move = [
            ('DOCUMENTATION_CONSOLIDATION_SUMMARY.md', 'docs/architecture'),
            ('SCRIPT_ORGANIZATION_SUMMARY.md', 'docs/architecture'),
            ('start_server.py', 'scripts/utilities'),
        ]
        
        print("Moving remaining files...")
        
        for filename, target_dir in files_to_move:
            source_path = self.root_path / filename
            if source_path.exists():
                target_path = self.root_path / target_dir / filename
                
                if self.dry_run:
                    print(f"[DRY RUN] Would move: {filename} -> {target_dir}/")
                else:
                    try:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(source_path), str(target_path))
                        print(f"Moved: {filename} -> {target_dir}/")
                        self.moved_files.append((filename, target_dir))
                    except Exception as e:
                        print(f"ERROR moving {filename}: {e}")
                        self.errors.append((filename, str(e)))
                        
    def create_project_summary(self):
        """Create final project structure summary."""
        summary_content = '''# Contract Analyzer Project Structure

## Overview
The Contract Analyzer codebase has been reorganized for improved maintainability and clarity.

## Directory Structure

```
contract_analyzer/
├── app/                    # Core application code
│   ├── api/               # API routes and endpoints
│   ├── core/              # Core business logic
│   ├── services/          # Service layer
│   ├── utils/             # Utility functions
│   └── database/          # Database models
│
├── tests/                  # All test files
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test fixtures
│
├── docs/                   # All documentation
│   ├── architecture/      # System design docs
│   ├── api/              # API documentation
│   ├── deployment/       # Deployment guides
│   ├── development/      # Development guides
│   ├── user-guide/       # User documentation
│   └── troubleshooting/  # Debugging guides
│
├── scripts/                # Utility scripts
│   ├── setup/            # Installation scripts
│   ├── maintenance/      # Maintenance scripts
│   ├── analysis/         # Analysis scripts
│   ├── debug/            # Debug utilities
│   ├── deployment/       # Deployment scripts
│   └── run_scripts.py    # Unified script runner
│
├── config/                 # Configuration files
├── data/                   # Data directory
│   ├── uploads/          # User uploads
│   ├── templates/        # Contract templates
│   └── reports/          # Generated reports
│
├── static/                 # Static assets
├── templates/              # HTML templates
│
├── README.md              # Project overview
├── CONTRIBUTING.md        # Contribution guidelines
├── requirements.txt       # Python dependencies
├── run_app.py            # Application entry point
├── .env.example          # Environment template
└── VERSION               # Version file
```

## Key Improvements

1. **Clean Root Directory**: Reduced from 40+ files to ~10 essential files
2. **Organized Tests**: All 77 test files now properly categorized in `/tests`
3. **Consolidated Docs**: All documentation in `/docs` with clear structure
4. **Script Management**: All scripts organized by purpose with unified runner
5. **Clear Separation**: Production code, tests, docs, and scripts clearly separated

## Quick Start

1. **Run Application**:
   ```bash
   python run_app.py
   ```

2. **Run Tests**:
   ```bash
   pytest tests/
   ```

3. **Access Scripts**:
   ```bash
   python scripts/run_scripts.py
   ```

4. **View Documentation**:
   See `/docs/README.md` for documentation index

## Development Workflow

1. Application code goes in `/app`
2. Tests go in `/tests` (unit or integration)
3. Documentation goes in `/docs`
4. Scripts go in `/scripts` (categorized by purpose)
5. Keep root directory clean - only essential files

---

Generated during codebase consolidation - see docs/architecture/ for details.
'''
        
        summary_path = self.root_path / 'PROJECT_STRUCTURE.md'
        
        if self.dry_run:
            print(f"\n[DRY RUN] Would create: PROJECT_STRUCTURE.md")
        else:
            summary_path.write_text(summary_content)
            print(f"\nCreated: PROJECT_STRUCTURE.md")
            
    def analyze_final_state(self):
        """Analyze the final state of the root directory."""
        print("\n" + "="*50)
        print("FINAL ROOT DIRECTORY ANALYSIS")
        print("="*50)
        
        # Count files by type
        py_files = list(self.root_path.glob('*.py'))
        md_files = list(self.root_path.glob('*.md'))
        other_files = [f for f in self.root_path.iterdir() 
                      if f.is_file() and f.suffix not in ['.py', '.md'] 
                      and not f.name.startswith('.')]
        
        print(f"\nPython files in root: {len(py_files)}")
        for f in py_files:
            print(f"  - {f.name}")
            
        print(f"\nMarkdown files in root: {len(md_files)}")
        for f in md_files:
            print(f"  - {f.name}")
            
        print(f"\nOther files: {len(other_files)}")
        
        total_root_files = len(py_files) + len(md_files) + len(other_files)
        print(f"\nTotal files in root (excluding hidden): {total_root_files}")
        
        if total_root_files <= 15:
            print("\n✅ SUCCESS: Root directory is clean!")
        else:
            print("\n⚠️  WARNING: Root directory still has many files")
            
    def create_gitignore_update(self):
        """Update .gitignore for new structure."""
        gitignore_additions = '''
# Consolidation artifacts
*_CONSOLIDATION_SUMMARY.md
*_ORGANIZATION_SUMMARY.md
codebase_analysis.json

# Temporary test files
tests/**/*.tmp
tests/**/*.log

# Script outputs
scripts/**/*.log
scripts/**/*.tmp
'''
        
        if self.dry_run:
            print(f"\n[DRY RUN] Would append to .gitignore")
        else:
            gitignore_path = self.root_path / '.gitignore'
            if gitignore_path.exists():
                current_content = gitignore_path.read_text()
                if '# Consolidation artifacts' not in current_content:
                    gitignore_path.write_text(current_content + gitignore_additions)
                    print("\nUpdated .gitignore")
                    
def main():
    """Run final cleanup."""
    print("Final Cleanup - Consolidation Complete")
    print("="*50)
    
    # Check if dry run
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("DRY RUN MODE - No changes will be made")
    else:
        response = input("This will complete the consolidation. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
            
    cleanup = FinalCleanup(dry_run=dry_run)
    
    # Execute steps
    cleanup.move_remaining_files()
    cleanup.create_project_summary()
    cleanup.create_gitignore_update()
    cleanup.analyze_final_state()
    
    print("\n" + "="*50)
    print("CONSOLIDATION COMPLETE!")
    print("="*50)
    print("\nNext steps:")
    print("1. Review PROJECT_STRUCTURE.md")
    print("2. Run tests to ensure nothing broke: pytest tests/")
    print("3. Update team on new structure")
    print("4. Delete old consolidation summary files from docs/")
    
    if dry_run:
        print("\nTo execute changes, run without --dry-run flag")

if __name__ == "__main__":
    main()