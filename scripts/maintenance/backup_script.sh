#!/bin/bash

# Contract Analyzer Auto-Backup Script
# Automatically creates a backup after each commit

echo "Creating automatic backup..."

# Get current commit info
CURRENT_COMMIT=$(git rev-parse --short HEAD)
CURRENT_DATE=$(date +%Y%m%d_%H%M%S)

# Extract version from latest commit message
VERSION=$(git log --oneline -1 | grep -o "v[0-9]\+\.[0-9]\+\.[0-9]\+" | head -1)
if [ -z "$VERSION" ]; then
    VERSION="backup"
fi

# Create backup directory
BACKUP_DIR="backups/${VERSION}_${CURRENT_COMMIT}_${CURRENT_DATE}"
mkdir -p "$BACKUP_DIR"

echo "Backing up to: $BACKUP_DIR"

# Copy application files
cp -r app/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r static/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r templates/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r data/ "$BACKUP_DIR/" 2>/dev/null || true

# Copy configuration files
cp *.py "$BACKUP_DIR/" 2>/dev/null || true
cp .env "$BACKUP_DIR/" 2>/dev/null || true
cp requirements.txt "$BACKUP_DIR/" 2>/dev/null || true
cp config.py "$BACKUP_DIR/" 2>/dev/null || true

# Create backup metadata
cat > "$BACKUP_DIR/BACKUP_INFO.md" << EOF
# Contract Analyzer Backup

- **Version**: $VERSION
- **Commit**: $CURRENT_COMMIT
- **Date**: $(date)
- **Git Log**: $(git log --oneline -1)

## Backup Contents
- Complete application source code
- Configuration files
- Static assets and templates
- Data directory (if exists)

## Restore Instructions
1. Copy contents to project directory
2. Install dependencies: pip install -r requirements.txt
3. Run application: python start_dashboard.py

## Backup Creation
This backup was automatically created using the backup_script.sh
EOF

# Create backup summary
TOTAL_FILES=$(find "$BACKUP_DIR" -type f | wc -l)
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo "Backup completed successfully!"
echo "   Directory: $BACKUP_DIR"
echo "   Files: $TOTAL_FILES"
echo "   Size: $BACKUP_SIZE"
echo ""

# Clean up old backups (keep last 10)
BACKUP_COUNT=$(ls -1 backups/ | wc -l)
if [ "$BACKUP_COUNT" -gt 10 ]; then
    echo "Cleaning up old backups (keeping 10 most recent)..."
    cd backups && ls -1t | tail -n +11 | xargs -r rm -rf
    cd ..
fi

echo "Backup process complete!"