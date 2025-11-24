#!/usr/bin/env python3
"""
Test MongoDB PowerShell Integration

This script tests the MongoDB PowerShell integration to ensure:
1. The Python bridge works correctly
2. The integration doesn't break existing workflows
3. All components are properly configured

Run with: python tests/test_mongodb_powershell_integration.py
"""

import os
import sys
import subprocess
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_python_bridge_help():
    """Test that the Python bridge shows help."""
    print("\n" + "="*60)
    print("TEST: Python Bridge Help")
    print("="*60)
    
    result = subprocess.run(
        ['python', 'scripts/mongodb_powershell_bridge.py', '--help'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and 'MongoDB PowerShell Bridge' in result.stdout:
        print("✅ PASS: Python bridge help works")
        return True
    else:
        print("❌ FAIL: Python bridge help failed")
        print(result.stderr)
        return False


def test_python_bridge_test_connection_without_mongodb():
    """Test that test-connection handles missing MongoDB gracefully."""
    print("\n" + "="*60)
    print("TEST: Test Connection Without MongoDB")
    print("="*60)
    
    result = subprocess.run(
        ['python', 'scripts/mongodb_powershell_bridge.py', 'test-connection'],
        capture_output=True,
        text=True
    )
    
    # Should fail with exit code 1 but not crash
    if result.returncode in [1, 2]:  # 1 = connection failed, 2 = pymongo not installed
        output = result.stdout + result.stderr
        if 'ERROR' in output or 'pymongo' in output:
            print("✅ PASS: Gracefully handles missing MongoDB/pymongo")
            print(f"   Output: {output[:100]}...")
            return True
    
    print("❌ FAIL: Should handle missing MongoDB gracefully")
    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")
    return False


def test_python_bridge_check_game():
    """Test the check-game command."""
    print("\n" + "="*60)
    print("TEST: Check Game Command")
    print("="*60)
    
    result = subprocess.run(
        ['python', 'scripts/mongodb_powershell_bridge.py', 'check-game', '--game-id', '99999', '--status', 'finished'],
        capture_output=True,
        text=True
    )
    
    # Should fail gracefully if MongoDB not available
    if result.returncode in [1, 2]:
        output = result.stdout + result.stderr
        print("✅ PASS: Check-game handles missing MongoDB gracefully")
        print(f"   Exit code: {result.returncode}")
        return True
    
    print("❌ FAIL: Check-game should handle missing MongoDB")
    return False


def test_mongodb_helper_exists():
    """Test that MongoDB helper files exist."""
    print("\n" + "="*60)
    print("TEST: MongoDB Helper Files Exist")
    print("="*60)
    
    files_to_check = [
        'scripts/mongodb_helper.ps1',
        'scripts/mongodb_powershell_bridge.py',
        'MONGODB_SETUP.md'
    ]
    
    all_exist = True
    for filepath in files_to_check:
        if os.path.exists(filepath):
            print(f"✅ {filepath} exists")
        else:
            print(f"❌ {filepath} missing")
            all_exist = False
    
    if all_exist:
        print("✅ PASS: All MongoDB helper files exist")
        return True
    else:
        print("❌ FAIL: Some files are missing")
        return False


def test_powershell_scripts_not_broken():
    """Test that PowerShell scripts exist and can be read."""
    print("\n" + "="*60)
    print("TEST: PowerShell Scripts Exist and Readable")
    print("="*60)
    
    scripts_to_check = [
        'scripts/download-controller.ps1',
        'scripts/extract-game.ps1',
        'scripts/mongodb_helper.ps1'
    ]
    
    all_valid = True
    for script in scripts_to_check:
        if os.path.exists(script):
            try:
                with open(script, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check that file is not empty and contains expected PowerShell syntax
                    if len(content) > 0 and ('function ' in content or 'param' in content):
                        print(f"✅ {script} - exists and contains PowerShell code")
                    else:
                        print(f"❌ {script} - file seems empty or invalid")
                        all_valid = False
            except Exception as e:
                print(f"❌ {script} - error reading file: {e}")
                all_valid = False
        else:
            print(f"❌ {script} - file not found")
            all_valid = False
    
    if all_valid:
        print("✅ PASS: All PowerShell scripts exist and are readable")
        return True
    else:
        print("❌ FAIL: Some scripts have issues")
        return False


def test_mongodb_integration_imports():
    """Test that MongoDB integration imports are present."""
    print("\n" + "="*60)
    print("TEST: MongoDB Integration Imports")
    print("="*60)
    
    scripts_and_imports = {
        'scripts/download-controller.ps1': '. "$ROOT\\mongodb_helper.ps1"',
        'scripts/extract-game.ps1': '. "$ROOT\\mongodb_helper.ps1"'
    }
    
    all_imports_found = True
    for script, import_line in scripts_and_imports.items():
        if os.path.exists(script):
            with open(script, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'mongodb_helper.ps1' in content:
                    print(f"✅ {script} - MongoDB helper import found")
                else:
                    print(f"❌ {script} - MongoDB helper import missing")
                    all_imports_found = False
        else:
            print(f"❌ {script} - file not found")
            all_imports_found = False
    
    if all_imports_found:
        print("✅ PASS: All scripts have MongoDB imports")
        return True
    else:
        print("❌ FAIL: Some scripts missing MongoDB imports")
        return False


def test_documentation_completeness():
    """Test that documentation is complete."""
    print("\n" + "="*60)
    print("TEST: Documentation Completeness")
    print("="*60)
    
    doc_file = 'MONGODB_SETUP.md'
    
    if not os.path.exists(doc_file):
        print(f"❌ FAIL: {doc_file} not found")
        return False
    
    with open(doc_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_sections = [
        'MongoDB Collection Schema',
        'Deduplication Logic',
        'Integration Workflow',
        'Configuration',
        'PowerShell Usage Examples',
        'Python Bridge Usage',
        'Parallel CSV/JSON Generation',
        'Troubleshooting'
    ]
    
    all_sections_found = True
    for section in required_sections:
        if section in content:
            print(f"✅ Section found: {section}")
        else:
            print(f"❌ Section missing: {section}")
            all_sections_found = False
    
    if all_sections_found:
        print("✅ PASS: Documentation is complete")
        return True
    else:
        print("❌ FAIL: Documentation is missing sections")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("MongoDB PowerShell Integration Test Suite")
    print("="*60)
    
    tests = [
        ("Helper Files Exist", test_mongodb_helper_exists),
        ("PowerShell Scripts Valid", test_powershell_scripts_not_broken),
        ("MongoDB Integration Imports", test_mongodb_integration_imports),
        ("Python Bridge Help", test_python_bridge_help),
        ("Test Connection Without MongoDB", test_python_bridge_test_connection_without_mongodb),
        ("Check Game Command", test_python_bridge_check_game),
        ("Documentation Completeness", test_documentation_completeness)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ EXCEPTION in {test_name}: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
