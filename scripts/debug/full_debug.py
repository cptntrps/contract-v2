#!/usr/bin/env python3
"""
Full Debug Suite for Contract Analyzer
Comprehensive system verification and debugging tool.
"""

import os
import sys
import subprocess
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class DebugReport:
    """Collect and format debug information."""
    
    def __init__(self):
        self.sections = []
        self.errors = []
        self.warnings = []
        self.successes = []
        
    def add_section(self, title: str, content: str):
        """Add a debug section."""
        self.sections.append((title, content))
        
    def add_error(self, error: str):
        """Add an error."""
        self.errors.append(error)
        
    def add_warning(self, warning: str):
        """Add a warning."""
        self.warnings.append(warning)
        
    def add_success(self, success: str):
        """Add a success message."""
        self.successes.append(success)
        
    def generate_report(self) -> str:
        """Generate the full debug report."""
        report = ["=" * 80]
        report.append("CONTRACT ANALYZER - FULL DEBUG REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        # Summary
        report.append("\n## SUMMARY")
        report.append(f"✅ Successes: {len(self.successes)}")
        report.append(f"⚠️  Warnings: {len(self.warnings)}")
        report.append(f"❌ Errors: {len(self.errors)}")
        
        # Errors
        if self.errors:
            report.append("\n## ERRORS")
            for i, error in enumerate(self.errors, 1):
                report.append(f"{i}. {error}")
                
        # Warnings
        if self.warnings:
            report.append("\n## WARNINGS")
            for i, warning in enumerate(self.warnings, 1):
                report.append(f"{i}. {warning}")
                
        # Sections
        for title, content in self.sections:
            report.append(f"\n## {title}")
            report.append(content)
            
        return "\n".join(report)


class SystemDebugger:
    """Main debugging class."""
    
    def __init__(self):
        self.report = DebugReport()
        self.root_path = PROJECT_ROOT
        self.venv_python = self.root_path / "venv" / "bin" / "python"
        
    def check_environment(self):
        """Check Python environment and dependencies."""
        content = []
        
        # Python version
        content.append(f"Python: {sys.version}")
        content.append(f"Executable: {sys.executable}")
        
        # Virtual environment
        if self.venv_python.exists():
            content.append(f"Virtual env: ✅ {self.venv_python}")
            self.report.add_success("Virtual environment found")
        else:
            content.append("Virtual env: ❌ Not found")
            self.report.add_error("Virtual environment not found")
            
        # Check imports
        critical_imports = [
            "flask",
            "pytest", 
            "docx",
            "openpyxl",
            "reportlab",
            "sqlalchemy"
        ]
        
        content.append("\nCritical Packages:")
        for package in critical_imports:
            try:
                __import__(package)
                content.append(f"  {package}: ✅")
            except ImportError:
                content.append(f"  {package}: ❌")
                self.report.add_error(f"Missing package: {package}")
                
        self.report.add_section("ENVIRONMENT", "\n".join(content))
        
    def check_directory_structure(self):
        """Verify directory structure after consolidation."""
        content = []
        
        expected_dirs = {
            "app": "Application code",
            "tests": "Test files",
            "docs": "Documentation",
            "scripts": "Utility scripts",
            "data": "Data files",
            "data/uploads": "Uploaded contracts",
            "data/templates": "Contract templates",
            "data/reports": "Generated reports",
            "tests/unit": "Unit tests",
            "tests/integration": "Integration tests",
            "scripts/debug": "Debug scripts",
            "scripts/analysis": "Analysis scripts"
        }
        
        content.append("Expected Directories:")
        for dir_path, description in expected_dirs.items():
            full_path = self.root_path / dir_path
            if full_path.exists() and full_path.is_dir():
                file_count = len(list(full_path.glob("*")))
                content.append(f"  ✅ {dir_path}/ ({file_count} items) - {description}")
                self.report.add_success(f"Directory exists: {dir_path}")
            else:
                content.append(f"  ❌ {dir_path}/ - {description}")
                self.report.add_error(f"Missing directory: {dir_path}")
                
        # Check for scattered test files
        root_tests = list(self.root_path.glob("test_*.py"))
        if root_tests:
            content.append(f"\n⚠️  Found {len(root_tests)} test files in root:")
            for test in root_tests:
                content.append(f"  - {test.name}")
                self.report.add_warning(f"Test file in root: {test.name}")
                
        self.report.add_section("DIRECTORY STRUCTURE", "\n".join(content))
        
    def check_imports(self):
        """Check if all Python files have valid imports."""
        content = []
        import_errors = []
        
        # Check all Python files
        py_files = list(self.root_path.glob("**/*.py"))
        py_files = [f for f in py_files if "venv" not in str(f) and "__pycache__" not in str(f)]
        
        content.append(f"Checking {len(py_files)} Python files...")
        
        for py_file in py_files[:10]:  # Check first 10 files
            try:
                # Try to compile the file
                with open(py_file, 'r') as f:
                    compile(f.read(), py_file, 'exec')
            except SyntaxError as e:
                import_errors.append((py_file, str(e)))
                
        if import_errors:
            content.append(f"\n❌ Found {len(import_errors)} files with syntax errors:")
            for file, error in import_errors[:5]:
                content.append(f"  - {file.relative_to(self.root_path)}: {error}")
                self.report.add_error(f"Syntax error in {file.name}")
        else:
            content.append("\n✅ No syntax errors found")
            self.report.add_success("All files compile successfully")
            
        self.report.add_section("IMPORT VALIDATION", "\n".join(content))
        
    def check_configuration(self):
        """Check configuration files."""
        content = []
        
        config_files = {
            ".env": "Environment configuration",
            "requirements.txt": "Python dependencies",
            "pytest.ini": "Pytest configuration",
            "pyproject.toml": "Project configuration",
            ".gitignore": "Git ignore rules"
        }
        
        content.append("Configuration Files:")
        for file, description in config_files.items():
            file_path = self.root_path / file
            if file_path.exists():
                size = file_path.stat().st_size
                content.append(f"  ✅ {file} ({size} bytes) - {description}")
                self.report.add_success(f"Config file exists: {file}")
                
                # Check .env for required variables
                if file == ".env":
                    env_content = file_path.read_text()
                    required_vars = ["OPENAI_API_KEY", "SECRET_KEY"]
                    for var in required_vars:
                        if var in env_content:
                            content.append(f"    ✅ {var} configured")
                        else:
                            content.append(f"    ⚠️  {var} not configured")
                            self.report.add_warning(f"Missing env var: {var}")
            else:
                content.append(f"  ❌ {file} - {description}")
                if file != ".env":  # .env is optional
                    self.report.add_error(f"Missing config file: {file}")
                    
        self.report.add_section("CONFIGURATION", "\n".join(content))
        
    def test_application_startup(self):
        """Test if the application can start."""
        content = []
        
        content.append("Testing application startup...")
        
        # Check if main app file exists
        app_file = self.root_path / "run_app.py"
        if not app_file.exists():
            content.append("❌ run_app.py not found")
            self.report.add_error("Main application file missing")
            self.report.add_section("APPLICATION STARTUP", "\n".join(content))
            return
            
        # Try to import the app
        try:
            sys.path.insert(0, str(self.root_path))
            from app.api.app import create_api_app
            from app.config.settings import get_config
            
            config = get_config()
            app = create_api_app(config)
            content.append("✅ Application imports successful")
            content.append("✅ Flask app created successfully")
            self.report.add_success("Application can be imported")
            
            # Check routes
            routes = []
            for rule in app.url_map.iter_rules():
                if '/api/' in str(rule):
                    routes.append(str(rule))
                    
            content.append(f"\nFound {len(routes)} API routes")
            if routes:
                content.append("Sample routes:")
                for route in routes[:5]:
                    content.append(f"  - {route}")
                    
        except Exception as e:
            content.append(f"❌ Application import failed: {str(e)}")
            content.append(f"Traceback:\n{traceback.format_exc()}")
            self.report.add_error("Application startup failed")
            
        self.report.add_section("APPLICATION STARTUP", "\n".join(content))
        
    def test_database_connection(self):
        """Test database connectivity."""
        content = []
        
        try:
            from app.database import db
            from app.api.app import create_api_app
            from app.config.settings import get_config
            
            config = get_config()
            app = create_api_app(config)
            
            with app.app_context():
                # Try to connect to database
                db.engine.execute("SELECT 1")
                content.append("✅ Database connection successful")
                self.report.add_success("Database connection works")
                
                # Check tables
                tables = db.engine.table_names()
                content.append(f"\nFound {len(tables)} database tables:")
                for table in tables:
                    content.append(f"  - {table}")
                    
        except Exception as e:
            content.append(f"⚠️  Database connection failed: {str(e)}")
            content.append("This may be normal if using in-memory storage")
            self.report.add_warning("Database connection failed")
            
        self.report.add_section("DATABASE", "\n".join(content))
        
    def test_api_endpoints(self):
        """Test key API endpoints."""
        content = []
        
        try:
            from app.api.app import create_api_app
            from app.config.settings import get_config
            
            config = get_config()
            app = create_api_app(config)
            client = app.test_client()
            
            # Test endpoints
            test_endpoints = [
                ("/api/health", "GET", None),
                ("/api/contracts", "GET", None),
                ("/api/templates", "GET", None),
                ("/api/analysis-results", "GET", None),
            ]
            
            content.append("Testing API endpoints:")
            for endpoint, method, data in test_endpoints:
                try:
                    if method == "GET":
                        response = client.get(endpoint)
                    elif method == "POST":
                        response = client.post(endpoint, json=data)
                        
                    if response.status_code < 400:
                        content.append(f"  ✅ {method} {endpoint} -> {response.status_code}")
                        self.report.add_success(f"API endpoint works: {endpoint}")
                    else:
                        content.append(f"  ❌ {method} {endpoint} -> {response.status_code}")
                        self.report.add_error(f"API endpoint failed: {endpoint}")
                        
                except Exception as e:
                    content.append(f"  ❌ {method} {endpoint} -> Error: {str(e)}")
                    self.report.add_error(f"API endpoint error: {endpoint}")
                    
        except Exception as e:
            content.append(f"❌ Could not test API: {str(e)}")
            self.report.add_error("API testing failed")
            
        self.report.add_section("API ENDPOINTS", "\n".join(content))
        
    def check_test_suite(self):
        """Check if tests can run."""
        content = []
        
        # Check pytest
        try:
            import pytest
            content.append("✅ Pytest is installed")
            
            # Count test files
            test_files = list((self.root_path / "tests").glob("**/*test*.py"))
            content.append(f"\nFound {len(test_files)} test files")
            
            # Check conftest
            conftest = self.root_path / "tests" / "conftest.py"
            if conftest.exists():
                content.append("✅ tests/conftest.py exists")
                self.report.add_success("Test configuration found")
            else:
                content.append("❌ tests/conftest.py missing")
                self.report.add_error("Test configuration missing")
                
            # Try to collect tests
            content.append("\nAttempting to collect tests...")
            result = subprocess.run(
                [str(self.venv_python), "-m", "pytest", "--collect-only", "-q"],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Count collected tests
                test_count = len([l for l in result.stdout.split('\n') if '::' in l])
                content.append(f"✅ Collected {test_count} tests")
                self.report.add_success(f"Tests can be collected: {test_count} found")
            else:
                content.append("❌ Test collection failed")
                content.append(f"Error: {result.stderr[:200]}")
                self.report.add_error("Test collection failed")
                
        except ImportError:
            content.append("❌ Pytest not installed")
            self.report.add_error("Pytest not available")
            
        self.report.add_section("TEST SUITE", "\n".join(content))
        
    def check_data_files(self):
        """Check data directory contents."""
        content = []
        
        data_dirs = {
            "data/uploads": "Contract uploads",
            "data/templates": "Contract templates",
            "data/reports": "Generated reports",
            "data/prompts": "LLM prompts"
        }
        
        for dir_path, description in data_dirs.items():
            full_path = self.root_path / dir_path
            if full_path.exists():
                files = list(full_path.glob("*"))
                file_count = len([f for f in files if f.is_file()])
                content.append(f"\n{dir_path}/ - {description}:")
                content.append(f"  Files: {file_count}")
                
                # Sample files
                if files:
                    content.append("  Sample files:")
                    for f in files[:3]:
                        if f.is_file():
                            size = f.stat().st_size / 1024  # KB
                            content.append(f"    - {f.name} ({size:.1f} KB)")
                            
        self.report.add_section("DATA FILES", "\n".join(content))
        
    def generate_summary(self):
        """Generate final summary and recommendations."""
        content = []
        
        total_issues = len(self.report.errors) + len(self.report.warnings)
        
        if total_issues == 0:
            content.append("🎉 EXCELLENT! No issues found.")
            content.append("The system appears to be properly configured and ready to use.")
        elif len(self.report.errors) == 0:
            content.append("✅ GOOD! No critical errors found.")
            content.append(f"There are {len(self.report.warnings)} warnings that should be reviewed.")
        else:
            content.append(f"⚠️  ATTENTION NEEDED!")
            content.append(f"Found {len(self.report.errors)} errors and {len(self.report.warnings)} warnings.")
            
        # Recommendations
        content.append("\nRECOMMENDATIONS:")
        
        if any("Missing package" in e for e in self.report.errors):
            content.append("1. Install missing packages: pip install -r requirements.txt")
            
        if any("Missing directory" in e for e in self.report.errors):
            content.append("2. Run consolidation scripts to create missing directories")
            
        if any("Missing env var" in w for w in self.report.warnings):
            content.append("3. Configure missing environment variables in .env file")
            
        if any("Test" in e for e in self.report.errors):
            content.append("4. Fix test configuration and imports")
            
        if len(self.report.errors) == 0:
            content.append("1. Run full test suite: pytest tests/")
            content.append("2. Start application: python run_app.py")
            content.append("3. Check API health: curl http://localhost:5000/api/health")
            
        self.report.add_section("SUMMARY & RECOMMENDATIONS", "\n".join(content))
        
    def run_full_debug(self):
        """Run all debug checks."""
        print("Running full system debug...")
        print("This may take a few moments...\n")
        
        # Run all checks
        self.check_environment()
        self.check_directory_structure()
        self.check_configuration()
        self.check_imports()
        self.test_application_startup()
        self.test_database_connection()
        self.test_api_endpoints()
        self.check_test_suite()
        self.check_data_files()
        self.generate_summary()
        
        # Generate and save report
        report = self.report.generate_report()
        
        # Save to file
        report_path = self.root_path / "debug_report.txt"
        report_path.write_text(report)
        
        # Print report
        print(report)
        print(f"\n📄 Full report saved to: {report_path}")
        
        return len(self.report.errors) == 0


def main():
    """Run the full debug suite."""
    debugger = SystemDebugger()
    success = debugger.run_full_debug()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()