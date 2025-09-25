# Contract Analyzer Project Structure

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
