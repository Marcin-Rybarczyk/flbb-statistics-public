#!/usr/bin/env python3
"""
Repository Structure Overview

This script provides a visual overview of the FLBB Statistics repository structure
after the organization improvements.
"""

import os
from pathlib import Path

def show_tree_structure(root_path='.', max_depth=2):
    """Display the repository structure in a tree format"""
    
    structure = {
        'src/': 'Main application source code',
        'scripts/': 'Data collection and processing scripts', 
        'deployment/': 'Deployment tools and configuration',
        'data/': 'Data files and configuration',
        'docs/': 'Comprehensive documentation',
        'tests/': 'Testing and validation',
        'templates/': 'HTML templates for web interface',
        'static_site/': 'Generated static files for GitHub Pages',
        '.github/workflows/': 'GitHub Actions automation'
    }
    
    print("📁 FLBB Statistics - Repository Structure")
    print("=" * 50)
    
    for directory, description in structure.items():
        path = Path(root_path) / directory
        if path.exists():
            print(f"📂 {directory:<25} - {description}")
            
            # Show key files in each directory
            if path.is_dir():
                files = [f for f in path.iterdir() if f.is_file()][:5]  # Show first 5 files
                for file in files:
                    print(f"   ├── {file.name}")
                if len(list(path.iterdir())) > 5:
                    print(f"   └── ... and {len(list(path.iterdir())) - 5} more files")
                print()
    
    print("🚀 Quick Commands:")
    print("-" * 20)
    print("🧪 Test application:     python3 tests/test_local_flask.py --test-only")
    print("🌐 Run locally:          python3 tests/test_local_flask.py")
    print("🚀 Deploy:               python3 deployment/deploy_flask.py")
    print("📚 Read documentation:   cat docs/README.md")

if __name__ == "__main__":
    show_tree_structure()