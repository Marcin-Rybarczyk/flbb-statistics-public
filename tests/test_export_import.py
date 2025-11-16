#!/usr/bin/env python3
"""
Test script for export/import functionality.

This script tests the export_data.py and import_data.py scripts to ensure
they work correctly with the FLBB Statistics data.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import export_season_archive, import_season_archive, validate_season_archive


def test_export():
    """Test the export functionality."""
    print("=" * 70)
    print("Testing Export Functionality")
    print("=" * 70)
    
    # Create a temporary file for export
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Export data
        print("\n1. Testing export_season_archive()...")
        result = export_season_archive(output_path=tmp_path, include_raw=False)
        
        if result['success']:
            print(f"   ✓ Export successful")
            print(f"   - Files added: {result['files_added']}")
            print(f"   - Archive size: {result['archive_size'] / 1024:.2f} KB")
            print(f"   - Season ID: {result.get('season_id', 'unknown')}")
        else:
            print(f"   ✗ Export failed: {result['errors']}")
            return False
        
        # Validate the archive
        print("\n2. Testing validate_season_archive()...")
        validation = validate_season_archive(tmp_path)
        
        if validation['valid']:
            print(f"   ✓ Archive validation successful")
            print(f"   - Season ID: {validation['season_id']}")
            print(f"   - Files found: {len(validation['files_found'])}")
        else:
            print(f"   ✗ Validation failed: {validation['errors']}")
            return False
        
        return True
        
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_import():
    """Test the import functionality."""
    print("\n" + "=" * 70)
    print("Testing Import Functionality")
    print("=" * 70)
    
    # Create a temporary archive
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        archive_path = tmp.name
    
    # Create a temporary directory for import
    import_dir = tempfile.mkdtemp(prefix='test-import-')
    
    try:
        # First, export data to create an archive
        print("\n1. Creating test archive...")
        export_result = export_season_archive(output_path=archive_path, include_raw=False)
        
        if not export_result['success']:
            print(f"   ✗ Failed to create test archive")
            return False
        
        print(f"   ✓ Test archive created: {archive_path}")
        
        # Now test import
        print("\n2. Testing import_season_archive()...")
        import_result = import_season_archive(archive_path, target_season_dir=import_dir)
        
        if import_result['success']:
            print(f"   ✓ Import successful")
            print(f"   - Files imported: {len(import_result['imported_files'])}")
            print(f"   - Target directory: {import_result['target_directory']}")
            
            # Verify files were extracted
            print("\n3. Verifying extracted files...")
            expected_files = [
                'data/full-game-stats.csv',
                'data/gamesDB.json',
                'data/gameScheduleDB.json',
                'data/players-database.csv'
            ]
            
            all_found = True
            for file_path in expected_files:
                full_path = os.path.join(import_dir, file_path)
                if os.path.exists(full_path):
                    size = os.path.getsize(full_path)
                    print(f"   ✓ Found: {file_path} ({size} bytes)")
                else:
                    print(f"   ✗ Missing: {file_path}")
                    all_found = False
            
            return all_found
        else:
            print(f"   ✗ Import failed: {import_result['errors']}")
            return False
        
    finally:
        # Clean up
        if os.path.exists(archive_path):
            os.unlink(archive_path)
        if os.path.exists(import_dir):
            shutil.rmtree(import_dir)


def test_scripts():
    """Test the command-line scripts."""
    print("\n" + "=" * 70)
    print("Testing Command-Line Scripts")
    print("=" * 70)
    
    import subprocess
    
    # Test export script help
    print("\n1. Testing export_data.py --help...")
    result = subprocess.run(
        ['python3', 'scripts/export_data.py', '--help'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("   ✓ Export script help works")
    else:
        print("   ✗ Export script help failed")
        return False
    
    # Test import script help
    print("\n2. Testing import_data.py --help...")
    result = subprocess.run(
        ['python3', 'scripts/import_data.py', '--help'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("   ✓ Import script help works")
    else:
        print("   ✗ Import script help failed")
        return False
    
    # Test export script with temporary file
    print("\n3. Testing export_data.py execution...")
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        result = subprocess.run(
            ['python3', 'scripts/export_data.py', '-o', tmp_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and os.path.exists(tmp_path):
            size = os.path.getsize(tmp_path)
            print(f"   ✓ Export script executed successfully ({size} bytes)")
            
            # Test import script validation
            print("\n4. Testing import_data.py --validate-only...")
            result = subprocess.run(
                ['python3', 'scripts/import_data.py', tmp_path, '--validate-only'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("   ✓ Import script validation works")
                return True
            else:
                print("   ✗ Import script validation failed")
                print(f"   Output: {result.stderr}")
                return False
        else:
            print("   ✗ Export script failed")
            print(f"   Output: {result.stderr}")
            return False
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "FLBB Statistics Export/Import Tests" + " " * 17 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    tests = [
        ("Export", test_export),
        ("Import", test_import),
        ("Scripts", test_scripts),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test {test_name} raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
