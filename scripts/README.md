# Scripts Directory

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
