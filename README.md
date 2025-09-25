# Contract Analyzer

An enterprise-grade contract analysis application that compares contracts against templates using AI/LLM analysis and generates professional reports in multiple formats.

## Architecture

This application follows a **Domain-Driven Design (DDD)** architecture with clean separation of concerns:

- **Domain Layer**: Core business entities and logic
- **Application Layer**: Use cases and orchestration
- **Infrastructure Layer**: External dependencies and integrations
- **Presentation Layer**: API endpoints and web interface

## Project Structure

After comprehensive consolidation, the project follows this organized structure:

```
contract_analyzer/
├── app/                    # Core application code
│   ├── api/               # API routes and endpoints  
│   ├── core/              # Domain models and services
│   ├── services/          # Business logic services
│   ├── utils/             # Utility functions
│   └── database/          # Database models
│
├── tests/                  # All test files (organized)
│   ├── unit/              # Unit tests by component
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test fixtures and data
│
├── docs/                   # All documentation
│   ├── architecture/      # System design docs
│   ├── troubleshooting/   # Debug and issue guides
│   ├── api/              # API documentation  
│   └── development/      # Development guides
│
├── scripts/                # All utility scripts
│   ├── debug/            # Debug tools and diagnostics
│   ├── analysis/         # Analysis tools
│   ├── maintenance/      # Backup and migration
│   └── run_scripts.py    # Unified script runner
│
├── data/                   # Data files
│   ├── uploads/          # User uploads
│   ├── templates/        # Contract templates
│   └── reports/          # Generated reports
│
├── README.md              # This file
├── CONTRIBUTING.md        # Contribution guidelines  
├── requirements.txt       # Python dependencies
└── run_app.py            # Application entry point

## Quick Start

### 1. Setup
```bash
# Clone and setup
git clone <repository>
cd contract_analyzer

# Install dependencies  
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### 2. Run Application
```bash
# Start the application
python run_app.py

# Access at http://localhost:5000
```

### 3. Development Tools

```bash
# Run all tests
pytest tests/

# Access debug tools
python scripts/debug/quick_debug.py

# Use script menu
python scripts/run_scripts.py

# View documentation  
open docs/README.md
```

## Key Features

- **AI-Powered Analysis**: Contract comparison using OpenAI and local LLM models
- **Multiple Report Formats**: Excel, PDF, and Word document generation  
- **Enterprise Security**: Comprehensive input validation and audit logging
- **Clean Architecture**: Domain-driven design with clear separation of concerns
- **Comprehensive Testing**: Unit and integration test suites
- **Debug Tools**: Comprehensive debugging and diagnostic utilities

## Debug & Development

The application includes comprehensive debugging tools:

- **Quick Debug**: `python scripts/debug/quick_debug.py` - Fast system check
- **Full Debug**: `python scripts/debug/full_debug.py` - Complete system analysis  
- **Interactive Menu**: `python scripts/debug/debug_menu.py` - Menu-driven debugging
- **Script Runner**: `python scripts/run_scripts.py` - Unified script access

## Documentation

- **Architecture**: See `docs/architecture/` for system design
- **API Reference**: See `docs/api/` for endpoint documentation
- **Troubleshooting**: See `docs/troubleshooting/` for common issues
- **Development**: See `docs/development/` for contribution guidelines

## Support

For issues and questions:
1. Check `docs/troubleshooting/TROUBLESHOOTING_GUIDE.md`
2. Run debug tools for system analysis
3. Review logs in root directory

---

**Note**: This codebase has been comprehensively consolidated and organized for optimal maintainability and developer experience.
    ├── pytest.ini              # Test configuration
    ├── docker-compose.yml       # Local development stack
