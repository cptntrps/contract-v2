#!/usr/bin/env python3
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
        "8": ("Quick Debug Check", "scripts/debug/quick_debug.py"),
        "9": ("Full Debug Suite", "scripts/debug/full_debug.py"),
        "10": ("Interactive Debug Menu", "scripts/debug/debug_menu.py"),
        "11": ("Debug Contracts", "scripts/debug/debug_contracts.py"),
        "12": ("Debug Analysis Errors", "scripts/debug/debug_analysis_error.py"),
    },
    "Deployment": {
        "13": ("Start Full System", "scripts/deployment/start_full_system.sh"),
        "14": ("Start Celery Worker", "scripts/deployment/celery_worker.py"),
    }
}

def show_menu():
    """Display the script menu."""
    print("\n" + "="*50)
    print("Contract Analyzer - Script Runner")
    print("="*50)
    
    for category, scripts in SCRIPTS.items():
        print(f"\n{category}:")
        for key, (name, path) in scripts.items():
            print(f"  [{key}] {name}")
    
    print("\n  [q] Quit")
    print("="*50)

def run_script(script_path):
    """Run the selected script."""
    full_path = ROOT_DIR / script_path
    
    if not full_path.exists():
        print(f"\nError: Script not found: {script_path}")
        return
    
    print(f"\nRunning: {script_path}")
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
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"\nError running script: {e}")

def main():
    """Main script runner loop."""
    while True:
        show_menu()
        choice = input("\nSelect option: ").strip().lower()
        
        if choice == 'q':
            print("\nExiting script runner...")
            break
        
        # Find selected script
        found = False
        for category, scripts in SCRIPTS.items():
            if choice in scripts:
                _, script_path = scripts[choice]
                run_script(script_path)
                found = True
                input("\nPress Enter to continue...")
                break
        
        if not found:
            print(f"\nInvalid option: {choice}")

if __name__ == "__main__":
    main()
