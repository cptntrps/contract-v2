# Debug Tools Documentation

This directory contains comprehensive debugging tools for the Contract Analyzer application.

## Available Debug Tools

### 1. Quick Debug (`quick_debug.py`)
**Purpose**: Fast system health check
**Use case**: Daily development checks, CI/CD validation

```bash
python scripts/debug/quick_debug.py
```

**Features**:
- ✅ Virtual environment check
- ✅ Directory structure validation  
- ✅ Core file existence check
- ✅ Application import test
- ✅ API health verification
- ✅ Test file count
- ✅ Data file inventory

### 2. Full Debug Suite (`full_debug.py`)
**Purpose**: Comprehensive system analysis
**Use case**: Troubleshooting, system validation, onboarding

```bash
python scripts/debug/full_debug.py
```

**Features**:
- 🔍 Environment analysis (Python, packages, venv)
- 📁 Directory structure verification
- ⚙️ Configuration file validation
- 📦 Import validation (605+ Python files)
- 🚀 Application startup testing
- 🗄️ Database connection testing
- 🌐 API endpoint testing
- 🧪 Test suite validation
- 📊 Data file analysis
- 📋 Comprehensive report generation

### 3. Interactive Debug Menu (`debug_menu.py`)
**Purpose**: Interactive debugging interface
**Use case**: Development debugging, system exploration

```bash
python scripts/debug/debug_menu.py
```

**Features**:
- 📋 Menu-driven interface
- 🔧 All debug tools in one place
- 🧪 Test execution options
- 🌐 API testing
- 📁 Data analysis
- 🚀 Debug mode app startup
- 📋 Log file viewing
- 🧹 Temporary file cleanup

### 4. Legacy Debug Scripts
- `debug_contracts.py` - Contract-specific debugging
- `debug_analysis_error.py` - Analysis error debugging

## Usage Scenarios

### Daily Development
```bash
# Quick health check
python scripts/debug/quick_debug.py

# If issues found, run full debug
python scripts/debug/full_debug.py
```

### Troubleshooting
```bash
# Interactive debugging
python scripts/debug/debug_menu.py

# Select option 2 for full suite
# Select option 5 for API testing
# Select option 4 for test execution
```

### System Validation
```bash
# Complete system check with report
python scripts/debug/full_debug.py > system_validation.txt
```

### CI/CD Integration
```bash
# Exit code 0 = success, 1 = issues found
python scripts/debug/full_debug.py
echo $?  # Check exit code
```

## Debug Report Output

The full debug suite generates reports with:

### Summary Section
- ✅ Successes count
- ⚠️ Warnings count  
- ❌ Errors count

### Detailed Sections
- **Environment**: Python version, packages, virtual environment
- **Directory Structure**: All required directories and file counts
- **Configuration**: Config files and environment variables
- **Import Validation**: Python file syntax checking
- **Application Startup**: Flask app creation and route registration
- **Database**: Connection testing and table inventory
- **API Endpoints**: HTTP endpoint testing
- **Test Suite**: Pytest configuration and test collection
- **Data Files**: Uploads, templates, reports inventory

### Recommendations
- Specific action items based on found issues
- Quick commands for common fixes
- Next steps for system setup

## Integration with Main Scripts

Access debug tools through the unified script runner:

```bash
python scripts/run_scripts.py
```

Then select from Debug section:
- [8] Quick Debug Check
- [9] Full Debug Suite  
- [10] Interactive Debug Menu

## Troubleshooting Common Issues

### Import Errors
```bash
# Test specific imports
python scripts/debug/debug_menu.py
# Select option 3: Test Critical Imports
```

### Test Failures
```bash
# Test suite diagnosis
python scripts/debug/debug_menu.py  
# Select option 4: Run Tests
```

### API Issues
```bash
# API endpoint testing
python scripts/debug/debug_menu.py
# Select option 5: Check API Endpoints
```

### Performance Issues
```bash
# Full system analysis
python scripts/debug/full_debug.py
```

## Debug Output Files

- `debug_report.txt` - Full system debug report
- `app.log` - Application runtime logs
- `server.log` - Server operation logs
- `security_audit.log` - Security event logs

## Best Practices

1. **Run quick debug daily** during development
2. **Use full debug** when encountering issues
3. **Check debug reports** for patterns in CI/CD
4. **Clean temp files regularly** using cleanup option
5. **Review logs** for runtime issues

## Adding New Debug Tools

To add new debug functionality:

1. Create script in `/scripts/debug/`
2. Add to `debug_menu.py` options
3. Update `run_scripts.py` entries
4. Document in this README

---

**Note**: All debug tools respect the virtual environment and run from project root for consistent behavior.