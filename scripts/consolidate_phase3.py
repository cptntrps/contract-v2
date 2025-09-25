#!/usr/bin/env python3
"""
Phase 3 Implementation: Script Organization
Organizes utility scripts into proper categories.
"""

import os
import shutil
from pathlib import Path
import sys

class ScriptOrganizer:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.root_path = Path(__file__).parent.parent
        self.scripts_path = self.root_path / 'scripts'
        self.moved_files = []
        self.errors = []
        
    def create_script_structure(self):
        """Create the script directory structure."""
        directories = [
            'scripts/setup',
            'scripts/maintenance', 
            'scripts/analysis',
            'scripts/utilities',
            'scripts/deployment'
        ]
        
        for dir_path in directories:
            full_path = self.root_path / dir_path
            if self.dry_run:
                print(f"[DRY RUN] Would create: {dir_path}")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created: {dir_path}")
                
    def categorize_script_file(self, filename):
        """Determine which subdirectory a script should go to."""
        name_lower = filename.lower()
        
        # Setup scripts
        if any(x in name_lower for x in ['install', 'init', 'setup']):
            return 'scripts/setup'
            
        # Maintenance scripts
        if any(x in name_lower for x in ['migrate', 'backup', 'cleanup', 'maintenance']):
            return 'scripts/maintenance'
            
        # Analysis scripts
        if any(x in name_lower for x in ['analyze', 'semantic', 'validate', 'check']):
            return 'scripts/analysis'
            
        # Deployment scripts
        if any(x in name_lower for x in ['deploy', 'start_full', 'celery']):
            return 'scripts/deployment'
            
        # Default to utilities
        return 'scripts/utilities'
        
    def move_script_files(self):
        """Move script files to appropriate directories."""
        # Scripts to move
        scripts_to_move = [
            'migrate_to_database.py',
            'semantic_analysis_validation.py',
            'refactored_analyze_contract.py',
            'celery_worker.py',
            'start_full_system.sh',
            'backup_script.sh'
        ]
        
        print(f"\nMoving script files...")
        
        for script_file in scripts_to_move:
            source_path = self.root_path / script_file
            if source_path.exists():
                target_dir = self.categorize_script_file(script_file)
                target_path = self.root_path / target_dir / script_file
                
                if self.dry_run:
                    print(f"[DRY RUN] Would move: {script_file} -> {target_dir}/")
                else:
                    try:
                        shutil.move(str(source_path), str(target_path))
                        print(f"Moved: {script_file} -> {target_dir}/")
                        self.moved_files.append((script_file, target_dir))
                    except Exception as e:
                        print(f"ERROR moving {script_file}: {e}")
                        self.errors.append((script_file, str(e)))
                        
    def create_unified_runner(self):
        """Create a unified script runner for easy access."""
        runner_content = '''#!/usr/bin/env python3
"""
Unified Script Runner
Provides easy access to all utility scripts in the project.
"""

import os
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent

SCRIPTS = {
    "Setup": {
        "1": ("Initialize Database", "scripts/setup/init_database.py"),
        "2": ("Setup Development Environment", "scripts/setup/setup_dev.sh"),
    },
    "Maintenance": {
        "3": ("Migrate Database", "scripts/maintenance/migrate_to_database.py"),
        "4": ("Backup System", "scripts/maintenance/backup_script.sh"),
    },
    "Analysis": {
        "5": ("Validate Semantic Analysis", "scripts/analysis/semantic_analysis_validation.py"),
        "6": ("Analyze Codebase", "scripts/analyze_codebase.py"),
        "7": ("Analyze Contract", "scripts/analysis/refactored_analyze_contract.py"),
    },
    "Debug": {
        "8": ("Debug Contracts", "scripts/debug/debug_contracts.py"),
        "9": ("Debug Analysis Errors", "scripts/debug/debug_analysis_error.py"),
    },
    "Deployment": {
        "10": ("Start Full System", "scripts/deployment/start_full_system.sh"),
        "11": ("Start Celery Worker", "scripts/deployment/celery_worker.py"),
    }
}

def show_menu():
    """Display the script menu."""
    print("\\n" + "="*50)
    print("Contract Analyzer - Script Runner")
    print("="*50)
    
    for category, scripts in SCRIPTS.items():
        print(f"\\n{category}:")
        for key, (name, path) in scripts.items():
            print(f"  [{key}] {name}")
    
    print("\\n  [q] Quit")
    print("="*50)

def run_script(script_path):
    """Run the selected script."""
    full_path = ROOT_DIR / script_path
    
    if not full_path.exists():
        print(f"\\nError: Script not found: {script_path}")
        return
    
    print(f"\\nRunning: {script_path}")
    print("-"*50)
    
    try:
        if script_path.endswith('.py'):
            # Use virtual environment Python if available
            venv_python = ROOT_DIR / 'venv' / 'bin' / 'python'
            if venv_python.exists():
                subprocess.run([str(venv_python), str(full_path)])
            else:
                subprocess.run([sys.executable, str(full_path)])
        elif script_path.endswith('.sh'):
            subprocess.run(['bash', str(full_path)])
        else:
            print(f"Unknown script type: {script_path}")
    except KeyboardInterrupt:
        print("\\nScript interrupted by user")
    except Exception as e:
        print(f"\\nError running script: {e}")

def main():
    """Main script runner loop."""
    while True:
        show_menu()
        choice = input("\\nSelect option: ").strip().lower()
        
        if choice == 'q':
            print("\\nExiting script runner...")
            break
        
        # Find selected script
        found = False
        for category, scripts in SCRIPTS.items():
            if choice in scripts:
                _, script_path = scripts[choice]
                run_script(script_path)
                found = True
                input("\\nPress Enter to continue...")
                break
        
        if not found:
            print(f"\\nInvalid option: {choice}")

if __name__ == "__main__":
    main()
'''
        
        runner_path = self.scripts_path / 'run_scripts.py'
        
        if self.dry_run:
            print(f"\n[DRY RUN] Would create unified runner: scripts/run_scripts.py")
        else:
            runner_path.write_text(runner_content)
            runner_path.chmod(0o755)  # Make executable
            print(f"\nCreated unified runner: scripts/run_scripts.py")
            
    def create_script_readme(self):
        """Create README for scripts directory."""
        readme_content = '''# Scripts Directory

This directory contains all utility scripts for the Contract Analyzer project.

## Directory Structure

- **setup/** - Installation and initialization scripts
- **maintenance/** - Database migrations, backups, and cleanup scripts
- **analysis/** - Analysis and validation scripts
- **debug/** - Debugging utilities
- **deployment/** - Deployment and system startup scripts
- **utilities/** - General utility scripts

## Quick Access

Use the unified script runner for easy access to all scripts:

```bash
python scripts/run_scripts.py
```

## Script Categories

### Setup Scripts
- Initialize database
- Setup development environment

### Maintenance Scripts
- `migrate_to_database.py` - Migrate data to database
- `backup_script.sh` - System backup utility

### Analysis Scripts
- `semantic_analysis_validation.py` - Validate semantic analysis
- `refactored_analyze_contract.py` - Contract analysis script

### Debug Scripts
- `debug_contracts.py` - Debug contract issues
- `debug_analysis_error.py` - Debug analysis errors

### Deployment Scripts
- `start_full_system.sh` - Start complete system
- `celery_worker.py` - Start Celery worker
'''
        
        readme_path = self.scripts_path / 'README.md'
        
        if self.dry_run:
            print(f"[DRY RUN] Would create: scripts/README.md")
        else:
            readme_path.write_text(readme_content)
            print(f"Created: scripts/README.md")
                
    def create_summary(self):
        """Create summary of script organization."""
        summary_content = f'''# Script Organization Summary

## Files Moved: {len(self.moved_files)}

### Script Files:
'''
        for filename, target in self.moved_files:
            summary_content += f"- {filename} -> {target}/\n"
                
        if self.errors:
            summary_content += f"\n## Errors: {len(self.errors)}\n"
            for filename, error in self.errors:
                summary_content += f"- {filename}: {error}\n"
                
        summary_path = self.root_path / 'SCRIPT_ORGANIZATION_SUMMARY.md'
        
        if not self.dry_run:
            summary_path.write_text(summary_content)
            print(f"\nCreated summary: SCRIPT_ORGANIZATION_SUMMARY.md")
        
        return summary_content

def main():
    """Run script organization."""
    print("Script Organization - Phase 3")
    print("="*50)
    
    # Check if dry run
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("DRY RUN MODE - No files will be moved")
    else:
        response = input("This will organize script files. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
            
    organizer = ScriptOrganizer(dry_run=dry_run)
    
    # Execute steps
    organizer.create_script_structure()
    organizer.move_script_files()
    organizer.create_unified_runner()
    organizer.create_script_readme()
    
    # Summary
    summary = organizer.create_summary()
    print("\n" + "="*50)
    print(summary)
    
    if dry_run:
        print("\nTo execute changes, run without --dry-run flag")

if __name__ == "__main__":
    main()