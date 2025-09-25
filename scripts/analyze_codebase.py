#!/usr/bin/env python3
"""
Analyze current codebase structure to support consolidation efforts.
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import json

def analyze_directory(root_path):
    """Analyze directory structure and file organization."""
    
    analysis = {
        'root_files': {'py': [], 'md': [], 'other': []},
        'test_files': {'root': [], 'tests_dir': [], 'other_locations': []},
        'debug_files': [],
        'config_files': [],
        'directories': defaultdict(int),
        'file_counts': defaultdict(int),
        'issues': []
    }
    
    # Analyze root directory
    for item in Path(root_path).iterdir():
        if item.is_file():
            if item.suffix == '.py':
                analysis['root_files']['py'].append(item.name)
                if item.name.startswith('test_'):
                    analysis['test_files']['root'].append(item.name)
                elif item.name.startswith('debug_'):
                    analysis['debug_files'].append(item.name)
            elif item.suffix == '.md':
                analysis['root_files']['md'].append(item.name)
            else:
                analysis['root_files']['other'].append(item.name)
    
    # Analyze subdirectories
    for root, dirs, files in os.walk(root_path):
        rel_path = os.path.relpath(root, root_path)
        
        # Skip hidden directories and venv
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv' and d != '__pycache__']
        
        # Count files by directory
        if files:
            analysis['directories'][rel_path] = len([f for f in files if not f.startswith('.')])
        
        # Find test files in wrong locations
        for file in files:
            if file.endswith('.py'):
                analysis['file_counts']['total_py'] += 1
                
                if file.startswith('test_'):
                    if 'tests' in rel_path:
                        analysis['test_files']['tests_dir'].append(os.path.join(rel_path, file))
                    else:
                        analysis['test_files']['other_locations'].append(os.path.join(rel_path, file))
                
                if file.startswith('debug_'):
                    if rel_path != '.':
                        analysis['debug_files'].append(os.path.join(rel_path, file))
    
    # Identify issues
    if len(analysis['root_files']['py']) > 5:
        analysis['issues'].append(f"Too many Python files in root: {len(analysis['root_files']['py'])}")
    
    if analysis['test_files']['root']:
        analysis['issues'].append(f"Test files in root directory: {len(analysis['test_files']['root'])}")
    
    if analysis['test_files']['other_locations']:
        analysis['issues'].append(f"Test files outside tests directory: {len(analysis['test_files']['other_locations'])}")
    
    if len(analysis['debug_files']) > 3:
        analysis['issues'].append(f"Many debug files scattered: {len(analysis['debug_files'])}")
    
    return analysis

def print_analysis(analysis):
    """Print analysis results in a formatted way."""
    
    print("\n" + "="*60)
    print("CODEBASE STRUCTURE ANALYSIS")
    print("="*60)
    
    print("\n📁 ROOT DIRECTORY FILES:")
    print(f"  Python files: {len(analysis['root_files']['py'])}")
    print(f"  Markdown files: {len(analysis['root_files']['md'])}")
    print(f"  Other files: {len(analysis['root_files']['other'])}")
    
    print("\n🧪 TEST FILE DISTRIBUTION:")
    print(f"  Tests in root: {len(analysis['test_files']['root'])}")
    print(f"  Tests in tests/: {len(analysis['test_files']['tests_dir'])}")
    print(f"  Tests elsewhere: {len(analysis['test_files']['other_locations'])}")
    
    print("\n🔧 DEBUG FILES:")
    print(f"  Total debug files: {len(analysis['debug_files'])}")
    
    print("\n📊 DIRECTORY STATISTICS:")
    sorted_dirs = sorted(analysis['directories'].items(), key=lambda x: x[1], reverse=True)[:10]
    for dir_path, count in sorted_dirs:
        if count > 5:  # Only show directories with significant files
            print(f"  {dir_path}: {count} files")
    
    print("\n⚠️  ISSUES FOUND:")
    if analysis['issues']:
        for issue in analysis['issues']:
            print(f"  - {issue}")
    else:
        print("  No major issues found!")
    
    print("\n💡 RECOMMENDATIONS:")
    print("  1. Move test files from root to tests/")
    print("  2. Consolidate debug scripts into scripts/debug/")
    print("  3. Organize documentation into docs/")
    print("  4. Clean up root directory to essential files only")
    print("  5. Create proper configuration management")
    
    # Save detailed analysis
    with open('codebase_analysis.json', 'w') as f:
        # Convert defaultdict to regular dict for JSON serialization
        analysis['directories'] = dict(analysis['directories'])
        analysis['file_counts'] = dict(analysis['file_counts'])
        json.dump(analysis, f, indent=2)
    print(f"\n📄 Detailed analysis saved to: codebase_analysis.json")

def main():
    """Run the analysis."""
    root_path = Path(__file__).parent.parent
    analysis = analyze_directory(root_path)
    print_analysis(analysis)

if __name__ == "__main__":
    main()