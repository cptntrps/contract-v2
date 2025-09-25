#!/usr/bin/env python3
"""
Debug Menu - Interactive debugging interface for Contract Analyzer
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class DebugMenu:
    """Interactive debug menu."""
    
    def __init__(self):
        self.root_path = PROJECT_ROOT
        self.venv_python = self.root_path / "venv" / "bin" / "python"
        
    def run_command(self, cmd, description=""):
        """Run a command and show output."""
        print(f"\n🔧 {description}")
        print("="*50)
        try:
            if isinstance(cmd, str):
                result = subprocess.run(cmd, shell=True, cwd=self.root_path, capture_output=True, text=True)
            else:
                result = subprocess.run(cmd, cwd=self.root_path, capture_output=True, text=True)
                
            print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
            print(f"Return code: {result.returncode}")
            
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
                
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
                
        except Exception as e:
            print(f"Error running command: {e}")
            
        input("\nPress Enter to continue...")
        
    def quick_status(self):
        """Show quick system status."""
        os.system("python scripts/debug/quick_debug.py")
        input("\nPress Enter to continue...")
        
    def full_debug(self):
        """Run full debug suite."""
        self.run_command([str(self.venv_python), "scripts/debug/full_debug.py"], "Full Debug Suite")
        
    def test_imports(self):
        """Test critical imports."""
        print("\n🔍 Testing Critical Imports")
        print("="*50)
        
        imports_to_test = [
            "import flask",
            "import pytest",
            "from app.api.app import create_api_app",
            "from app.config.settings import get_config",
            "from app.core.services.analyzer import ContractAnalyzer",
            "from app.utils.security.validators import SecurityValidator"
        ]
        
        for import_stmt in imports_to_test:
            try:
                exec(import_stmt)
                print(f"✅ {import_stmt}")
            except Exception as e:
                print(f"❌ {import_stmt} -> {e}")
                
        input("\nPress Enter to continue...")
        
    def run_tests(self):
        """Run test suite options."""
        print("\n🧪 Test Options")
        print("="*30)
        print("1. Run all tests")
        print("2. Run unit tests only") 
        print("3. Run integration tests only")
        print("4. Run specific test file")
        print("5. Collect tests only")
        print("0. Back to main menu")
        
        choice = input("\nSelect test option: ").strip()
        
        if choice == "1":
            self.run_command([str(self.venv_python), "-m", "pytest", "tests/", "-v"], "All Tests")
        elif choice == "2":
            self.run_command([str(self.venv_python), "-m", "pytest", "tests/unit/", "-v"], "Unit Tests")
        elif choice == "3":
            self.run_command([str(self.venv_python), "-m", "pytest", "tests/integration/", "-v"], "Integration Tests")
        elif choice == "4":
            test_file = input("Enter test file path: ").strip()
            if test_file:
                self.run_command([str(self.venv_python), "-m", "pytest", test_file, "-v"], f"Test: {test_file}")
        elif choice == "5":
            self.run_command([str(self.venv_python), "-m", "pytest", "--collect-only"], "Collect Tests")
        elif choice == "0":
            return
            
    def check_api(self):
        """Test API endpoints."""
        print("\n🌐 API Testing")
        print("="*50)
        
        try:
            from app.api.app import create_api_app
            from app.config.settings import get_config
            
            config = get_config()
            app = create_api_app(config)
            client = app.test_client()
            
            endpoints = [
                "/api/health",
                "/api/contracts", 
                "/api/templates",
                "/api/analysis-results",
                "/api/prompts"
            ]
            
            print("Testing endpoints:")
            for endpoint in endpoints:
                try:
                    response = client.get(endpoint)
                    status = "✅" if response.status_code < 400 else "❌"
                    print(f"{status} GET {endpoint} -> {response.status_code}")
                except Exception as e:
                    print(f"❌ GET {endpoint} -> Error: {e}")
                    
        except Exception as e:
            print(f"Failed to create app: {e}")
            
        input("\nPress Enter to continue...")
        
    def analyze_structure(self):
        """Analyze project structure."""
        self.run_command([str(self.venv_python), "scripts/analyze_codebase.py"], "Codebase Analysis")
        
    def check_data_files(self):
        """Check data directory contents."""
        print("\n📁 Data Directory Analysis")
        print("="*50)
        
        data_dirs = {
            "uploads": "Contract uploads",
            "templates": "Contract templates", 
            "reports": "Generated reports",
            "prompts": "LLM prompts"
        }
        
        for dir_name, description in data_dirs.items():
            dir_path = self.root_path / "data" / dir_name
            if dir_path.exists():
                files = [f for f in dir_path.iterdir() if f.is_file()]
                print(f"\n{dir_name}/ - {description}")
                print(f"  Files: {len(files)}")
                
                if files:
                    print("  Recent files:")
                    for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                        size = f.stat().st_size / 1024
                        print(f"    - {f.name} ({size:.1f} KB)")
            else:
                print(f"\n{dir_name}/ - Missing!")
                
        input("\nPress Enter to continue...")
        
    def start_app_debug(self):
        """Start application in debug mode."""
        print("\n🚀 Starting Application in Debug Mode")
        print("="*50)
        print("The app will start and you can test it at http://localhost:5000")
        print("Press Ctrl+C to stop the app and return to menu\n")
        
        try:
            subprocess.run([str(self.venv_python), "run_app.py"], cwd=self.root_path)
        except KeyboardInterrupt:
            print("\nApp stopped.")
            
        input("\nPress Enter to continue...")
        
    def show_logs(self):
        """Show recent log files."""
        print("\n📋 Recent Log Files")
        print("="*50)
        
        log_files = [
            "app.log",
            "server.log", 
            "security_audit.log",
            "debug_report.txt"
        ]
        
        for log_file in log_files:
            log_path = self.root_path / log_file
            if log_path.exists():
                size = log_path.stat().st_size / 1024
                print(f"\n{log_file} ({size:.1f} KB):")
                try:
                    lines = log_path.read_text().split('\n')
                    # Show last 10 lines
                    for line in lines[-10:]:
                        if line.strip():
                            print(f"  {line}")
                except Exception as e:
                    print(f"  Error reading file: {e}")
            else:
                print(f"\n{log_file}: Not found")
                
        input("\nPress Enter to continue...")
        
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        print("\n🧹 Cleaning Temporary Files")
        print("="*50)
        
        # Find temp files
        temp_patterns = [
            "**/*.tmp",
            "**/*.log.*",
            "**/__pycache__",
            "**/*.pyc",
            "**/codebase_analysis.json",
            "**/*_CONSOLIDATION_SUMMARY.md"
        ]
        
        files_to_clean = []
        for pattern in temp_patterns:
            files_to_clean.extend(self.root_path.glob(pattern))
            
        if files_to_clean:
            print(f"Found {len(files_to_clean)} temporary files:")
            for f in files_to_clean[:10]:  # Show first 10
                print(f"  - {f.relative_to(self.root_path)}")
                
            if len(files_to_clean) > 10:
                print(f"  ... and {len(files_to_clean) - 10} more")
                
            confirm = input("\nDelete these files? (y/N): ").lower().strip()
            if confirm == 'y':
                deleted = 0
                for f in files_to_clean:
                    try:
                        if f.is_file():
                            f.unlink()
                            deleted += 1
                        elif f.is_dir():
                            import shutil
                            shutil.rmtree(f)
                            deleted += 1
                    except Exception as e:
                        print(f"Error deleting {f}: {e}")
                        
                print(f"Deleted {deleted} files/directories")
        else:
            print("No temporary files found")
            
        input("\nPress Enter to continue...")
        
    def show_menu(self):
        """Display the main debug menu."""
        os.system('clear' if os.name == 'posix' else 'cls')
        print("🔧 CONTRACT ANALYZER - DEBUG MENU")
        print("="*50)
        print()
        print("  [1] Quick Status Check")
        print("  [2] Full Debug Suite")
        print("  [3] Test Critical Imports")
        print("  [4] Run Tests")
        print("  [5] Check API Endpoints")
        print("  [6] Analyze Project Structure")
        print("  [7] Check Data Files")
        print("  [8] Start App (Debug Mode)")
        print("  [9] Show Recent Logs")
        print("  [10] Cleanup Temp Files")
        print()
        print("  [q] Quit")
        print("="*50)
        
    def run(self):
        """Run the debug menu."""
        while True:
            self.show_menu()
            choice = input("\nSelect option: ").strip().lower()
            
            if choice == 'q':
                print("Exiting debug menu...")
                break
            elif choice == '1':
                self.quick_status()
            elif choice == '2':
                self.full_debug()
            elif choice == '3':
                self.test_imports()
            elif choice == '4':
                self.run_tests()
            elif choice == '5':
                self.check_api()
            elif choice == '6':
                self.analyze_structure()
            elif choice == '7':
                self.check_data_files()
            elif choice == '8':
                self.start_app_debug()
            elif choice == '9':
                self.show_logs()
            elif choice == '10':
                self.cleanup_temp_files()
            else:
                print(f"Invalid option: {choice}")
                input("Press Enter to continue...")

def main():
    """Run the debug menu."""
    menu = DebugMenu()
    menu.run()

if __name__ == "__main__":
    main()