#!/usr/bin/env python3
"""
Test script to verify .env file loading functionality.
This script verifies that environment variables are correctly loaded from .env file.
"""

import os
import sys
import tempfile
from pathlib import Path

# Save current directory
original_dir = os.getcwd()

def test_env_loading():
    """Test that .env file is loaded correctly"""
    print("=" * 70)
    print("Testing .env File Loading")
    print("=" * 70)
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        
        # Create a test .env file
        env_file = test_dir / '.env'
        env_file.write_text("""TEST_USER_USERNAME=test_env_user
TEST_USER_PASSWORD=test_env_pass
TEST_ADMIN_PASSWORD=test_env_admin
SECRET_KEY=test-secret-key
""")
        
        print(f"\n1. Created test .env file at: {env_file}")
        print("   Contents:")
        print("   " + "\n   ".join(env_file.read_text().strip().split('\n')))
        
        # Change to test directory
        os.chdir(test_dir)
        
        # Clear any existing env vars
        for key in ['TEST_USER_USERNAME', 'TEST_USER_PASSWORD', 'TEST_ADMIN_PASSWORD']:
            os.environ.pop(key, None)
        
        # Import dotenv and load
        from dotenv import load_dotenv
        result = load_dotenv(dotenv_path=env_file)
        
        print(f"   load_dotenv() returned: {result}")
        
        print("\n2. Testing environment variable loading...")
        
        # Check if variables are loaded
        test_user = os.environ.get('TEST_USER_USERNAME')
        test_pass = os.environ.get('TEST_USER_PASSWORD')
        test_admin = os.environ.get('TEST_ADMIN_PASSWORD')
        
        assert test_user == 'test_env_user', f"Expected 'test_env_user', got '{test_user}'"
        print(f"   ✓ TEST_USER_USERNAME loaded correctly: {test_user}")
        
        assert test_pass == 'test_env_pass', f"Expected 'test_env_pass', got '{test_pass}'"
        print(f"   ✓ TEST_USER_PASSWORD loaded correctly: {test_pass}")
        
        assert test_admin == 'test_env_admin', f"Expected 'test_env_admin', got '{test_admin}'"
        print(f"   ✓ TEST_ADMIN_PASSWORD loaded correctly: {test_admin}")
        
        # Change back to original directory
        os.chdir(original_dir)
    
    print("\n" + "=" * 70)
    print("✅ .ENV FILE LOADING TEST PASSED")
    print("=" * 70)
    return True

def test_app_imports_dotenv():
    """Test that app.py correctly imports and uses dotenv"""
    print("\n" + "=" * 70)
    print("Testing app.py dotenv Integration")
    print("=" * 70)
    
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Check if app.py contains dotenv import
    app_path = Path(__file__).parent.parent / 'src' / 'app.py'
    app_content = app_path.read_text()
    
    print("\n1. Checking if app.py imports dotenv...")
    assert 'from dotenv import load_dotenv' in app_content, "app.py should import load_dotenv"
    print("   ✓ dotenv import found in app.py")
    
    print("\n2. Checking if app.py calls load_dotenv()...")
    assert 'load_dotenv()' in app_content, "app.py should call load_dotenv()"
    print("   ✓ load_dotenv() call found in app.py")
    
    # Check that it's called before Flask imports
    lines = app_content.split('\n')
    dotenv_line = None
    flask_line = None
    
    for i, line in enumerate(lines):
        if 'load_dotenv()' in line:
            dotenv_line = i
        if 'from flask import' in line:
            flask_line = i
        if dotenv_line and flask_line:
            break
    
    print("\n3. Checking if load_dotenv() is called before Flask imports...")
    assert dotenv_line < flask_line, f"load_dotenv() (line {dotenv_line}) should be called before Flask import (line {flask_line})"
    print(f"   ✓ load_dotenv() at line {dotenv_line} is before Flask import at line {flask_line}")
    
    print("\n" + "=" * 70)
    print("✅ APP.PY DOTENV INTEGRATION TEST PASSED")
    print("=" * 70)
    return True

def test_real_env_file():
    """Test that the actual .env file in repository works"""
    print("\n" + "=" * 70)
    print("Testing Real .env File in Repository")
    print("=" * 70)
    
    # Check if .env file exists
    env_path = Path(__file__).parent.parent / '.env'
    
    if not env_path.exists():
        print("\n⚠️  No .env file found in repository (this is OK for testing)")
        print("   In production, user should create .env from .env.example")
        return True
    
    print(f"\n1. Found .env file at: {env_path}")
    
    # Load it
    os.chdir(Path(__file__).parent.parent)
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if USER_USERNAME and USER_PASSWORD are set
    user_username = os.environ.get('USER_USERNAME')
    user_password = os.environ.get('USER_PASSWORD')
    
    print("\n2. Checking environment variables from .env file...")
    
    if user_username:
        print(f"   ✓ USER_USERNAME is set: {user_username}")
    else:
        print("   ℹ USER_USERNAME is not set in .env (OK if not needed)")
    
    if user_password:
        print(f"   ✓ USER_PASSWORD is set: {'*' * len(user_password)}")
    else:
        print("   ℹ USER_PASSWORD is not set in .env (OK if not needed)")
    
    print("\n" + "=" * 70)
    print("✅ REAL .ENV FILE TEST PASSED")
    print("=" * 70)
    
    # Clean up by changing back
    os.chdir(original_dir)
    return True

if __name__ == '__main__':
    try:
        print("\n" + "🧪" * 35)
        print(".ENV FILE LOADING TEST SUITE")
        print("🧪" * 35)
        
        test_env_loading()
        test_app_imports_dotenv()
        test_real_env_file()
        
        print("\n" + "🎉" * 35)
        print("✅ ALL .ENV TESTS PASSED!")
        print("🎉" * 35 + "\n")
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
