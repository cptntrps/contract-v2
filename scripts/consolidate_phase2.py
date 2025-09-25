#!/usr/bin/env python3
"""
Phase 2 Implementation: Documentation Consolidation
Organizes all documentation into a coherent structure.
"""

import os
import shutil
from pathlib import Path
import sys

class DocumentationConsolidator:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.root_path = Path(__file__).parent.parent
        self.docs_path = self.root_path / 'docs'
        self.moved_files = []
        self.errors = []
        
    def create_docs_structure(self):
        """Create the documentation directory structure."""
        directories = [
            'docs/architecture',
            'docs/api', 
            'docs/deployment',
            'docs/development',
            'docs/user-guide',
            'docs/troubleshooting'
        ]
        
        for dir_path in directories:
            full_path = self.root_path / dir_path
            if self.dry_run:
                print(f"[DRY RUN] Would create: {dir_path}")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created: {dir_path}")
                
    def categorize_doc_file(self, filename):
        """Determine which subdirectory a documentation file should go to."""
        name_lower = filename.lower()
        
        # Architecture docs
        if any(x in name_lower for x in ['architecture', 'design', 'structure', 'components']):
            return 'docs/architecture'
            
        # API docs
        if any(x in name_lower for x in ['api', 'endpoint', 'route']):
            return 'docs/api'
            
        # Deployment docs
        if any(x in name_lower for x in ['deploy', 'install', 'setup', 'docker']):
            return 'docs/deployment'
            
        # Development docs
        if any(x in name_lower for x in ['contributing', 'development', 'coding', 'standards']):
            return 'docs/development'
            
        # Troubleshooting docs
        if any(x in name_lower for x in ['debug', 'issue', 'resolution', 'fix', 'error']):
            return 'docs/troubleshooting'
            
        # User guide
        if any(x in name_lower for x in ['guide', 'usage', 'tutorial']):
            return 'docs/user-guide'
            
        # Default to architecture
        return 'docs/architecture'
        
    def move_documentation_files(self):
        """Move documentation files to appropriate directories."""
        # Docs to move (keep README.md and CONTRIBUTING.md in root)
        docs_to_move = [
            'CHANGELOG.md',
            'DEBUG_404_SOLUTION.md',
            'DEBUGGING_IMPROVEMENTS.md',
            'FINAL_404_FIX.md',
            'ISSUE_RESOLUTION_SUMMARY.md',
            'SEMANTIC_ANALYSIS_SUMMARY.md',
            'CODEBASE_CONSOLIDATION_PLAN.md',
            'TEST_CONSOLIDATION_SUMMARY.md'
        ]
        
        print(f"\nMoving documentation files...")
        
        for doc_file in docs_to_move:
            source_path = self.root_path / doc_file
            if source_path.exists():
                target_dir = self.categorize_doc_file(doc_file)
                target_path = self.root_path / target_dir / doc_file
                
                if self.dry_run:
                    print(f"[DRY RUN] Would move: {doc_file} -> {target_dir}/")
                else:
                    try:
                        shutil.move(str(source_path), str(target_path))
                        print(f"Moved: {doc_file} -> {target_dir}/")
                        self.moved_files.append((doc_file, target_dir))
                    except Exception as e:
                        print(f"ERROR moving {doc_file}: {e}")
                        self.errors.append((doc_file, str(e)))
                        
    def consolidate_similar_docs(self):
        """Consolidate similar documentation into unified files."""
        consolidations = [
            {
                'name': 'TROUBLESHOOTING_GUIDE.md',
                'target': 'docs/troubleshooting',
                'merge_files': [
                    'docs/troubleshooting/DEBUG_404_SOLUTION.md',
                    'docs/troubleshooting/DEBUGGING_IMPROVEMENTS.md',
                    'docs/troubleshooting/FINAL_404_FIX.md',
                    'docs/troubleshooting/ISSUE_RESOLUTION_SUMMARY.md'
                ]
            }
        ]
        
        for consolidation in consolidations:
            if self.dry_run:
                print(f"\n[DRY RUN] Would consolidate into: {consolidation['name']}")
                for f in consolidation['merge_files']:
                    print(f"  - Would merge: {f}")
            else:
                # Merge content
                merged_content = f"# {consolidation['name'].replace('.md', '').replace('_', ' ')}\n\n"
                merged_content += "This document consolidates various troubleshooting guides.\n\n"
                
                for file_path in consolidation['merge_files']:
                    full_path = self.root_path / file_path
                    if full_path.exists():
                        content = full_path.read_text()
                        merged_content += f"\n\n---\n\n## From {full_path.name}\n\n{content}"
                        
                # Save consolidated file
                target_path = self.root_path / consolidation['target'] / consolidation['name']
                target_path.write_text(merged_content)
                print(f"\nCreated consolidated: {target_path}")
                
    def create_index_files(self):
        """Create index README files for each documentation section."""
        index_contents = {
            'docs/README.md': '''# Contract Analyzer Documentation

Welcome to the Contract Analyzer documentation. This directory contains all project documentation organized by topic.

## Documentation Structure

- **[Architecture](./architecture/)** - System design and architecture documentation
- **[API](./api/)** - API endpoints and usage documentation
- **[Deployment](./deployment/)** - Installation and deployment guides
- **[Development](./development/)** - Development guides and standards
- **[User Guide](./user-guide/)** - End-user documentation
- **[Troubleshooting](./troubleshooting/)** - Debugging and issue resolution

## Quick Links

- [Getting Started](./user-guide/getting-started.md)
- [API Reference](./api/endpoints.md)
- [Architecture Overview](./architecture/README.md)
- [Troubleshooting Guide](./troubleshooting/TROUBLESHOOTING_GUIDE.md)
''',
            'docs/architecture/README.md': '''# Architecture Documentation

This section contains documentation about the system architecture and design.

## Contents

- System Architecture Overview
- Component Design
- Data Flow
- Security Architecture
- Performance Considerations
''',
            'docs/troubleshooting/README.md': '''# Troubleshooting Documentation

This section contains guides for debugging and resolving common issues.

## Contents

- [Troubleshooting Guide](./TROUBLESHOOTING_GUIDE.md) - Consolidated troubleshooting information
- Common Issues and Solutions
- Debug Scripts Usage
- Error Code Reference
'''
        }
        
        for file_path, content in index_contents.items():
            full_path = self.root_path / file_path
            
            if self.dry_run:
                print(f"[DRY RUN] Would create: {file_path}")
            else:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                print(f"Created: {file_path}")
                
    def create_summary(self):
        """Create summary of documentation changes."""
        summary_content = f'''# Documentation Consolidation Summary

## Files Moved: {len(self.moved_files)}

### Documentation Files:
'''
        for filename, target in self.moved_files:
            summary_content += f"- {filename} -> {target}/\n"
                
        if self.errors:
            summary_content += f"\n## Errors: {len(self.errors)}\n"
            for filename, error in self.errors:
                summary_content += f"- {filename}: {error}\n"
                
        summary_path = self.root_path / 'DOCUMENTATION_CONSOLIDATION_SUMMARY.md'
        
        if not self.dry_run:
            summary_path.write_text(summary_content)
            print(f"\nCreated summary: DOCUMENTATION_CONSOLIDATION_SUMMARY.md")
        
        return summary_content

def main():
    """Run documentation consolidation."""
    print("Documentation Consolidation - Phase 2")
    print("="*50)
    
    # Check if dry run
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("DRY RUN MODE - No files will be moved")
    else:
        response = input("This will move documentation files. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
            
    consolidator = DocumentationConsolidator(dry_run=dry_run)
    
    # Execute steps
    consolidator.create_docs_structure()
    consolidator.move_documentation_files()
    consolidator.consolidate_similar_docs()
    consolidator.create_index_files()
    
    # Summary
    summary = consolidator.create_summary()
    print("\n" + "="*50)
    print(summary)
    
    if dry_run:
        print("\nTo execute changes, run without --dry-run flag")

if __name__ == "__main__":
    main()