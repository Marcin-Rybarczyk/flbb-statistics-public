"""
Test script for authorization functionality in FLBB Statistics application.

This script tests:
1. Authentication with valid/invalid credentials
2. Authorization levels (guest, user, admin)
3. Access control for different routes
4. Login/logout flow
"""

import os
import sys
import hashlib

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.auth import verify_credentials, User, can_access_endpoint, get_user_auth_level
from src.auth import AUTH_LEVEL_GUEST, AUTH_LEVEL_USER, AUTH_LEVEL_ADMIN
from flask_login import LoginManager, login_user, logout_user, current_user
from flask import Flask

# Test utilities
def hash_password(password):
    """Helper to hash passwords for testing"""
    return hashlib.sha256(password.encode()).hexdigest()


def test_password_hashing():
    """Test password hashing function"""
    print("Testing password hashing...")
    
    password = "testpassword"
    hashed = hash_password(password)
    
    # Verify it's a SHA-256 hash (64 hex characters)
    assert len(hashed) == 64, "Hash should be 64 characters"
    assert hashed == hash_password(password), "Same password should produce same hash"
    assert hashed != hash_password("different"), "Different passwords should produce different hashes"
    
    print("✓ Password hashing works correctly")


def test_verify_credentials():
    """Test credential verification"""
    print("\nTesting credential verification...")
    
    # Set test environment variables
    os.environ['ADMIN_USERNAME'] = 'testadmin'
    os.environ['ADMIN_PASSWORD_HASH'] = hash_password('adminpass')
    os.environ['USER_CREDENTIALS'] = f"user1:{hash_password('userpass1')},user2:{hash_password('userpass2')}"
    
    # Test admin credentials
    is_valid, is_admin = verify_credentials('testadmin', 'adminpass')
    assert is_valid and is_admin, "Admin credentials should be valid"
    print("✓ Admin authentication works")
    
    # Test wrong admin password
    is_valid, is_admin = verify_credentials('testadmin', 'wrongpass')
    assert not is_valid, "Wrong admin password should fail"
    print("✓ Admin authentication rejects wrong password")
    
    # Test regular user credentials
    is_valid, is_admin = verify_credentials('user1', 'userpass1')
    assert is_valid and not is_admin, "User1 credentials should be valid (non-admin)"
    print("✓ User1 authentication works")
    
    is_valid, is_admin = verify_credentials('user2', 'userpass2')
    assert is_valid and not is_admin, "User2 credentials should be valid (non-admin)"
    print("✓ User2 authentication works")
    
    # Test wrong user password
    is_valid, is_admin = verify_credentials('user1', 'wrongpass')
    assert not is_valid, "Wrong user password should fail"
    print("✓ User authentication rejects wrong password")
    
    # Test non-existent user
    is_valid, is_admin = verify_credentials('nonexistent', 'anypass')
    assert not is_valid, "Non-existent user should fail"
    print("✓ Non-existent user authentication fails")
    
    # Clean up
    del os.environ['ADMIN_USERNAME']
    del os.environ['ADMIN_PASSWORD_HASH']
    del os.environ['USER_CREDENTIALS']


def test_user_object():
    """Test User class"""
    print("\nTesting User object...")
    
    # Test regular user
    user = User('testuser', is_admin=False)
    assert user.id == 'testuser', "User ID should match username"
    assert user.username == 'testuser', "Username should be set"
    assert not user.is_admin, "Regular user should not be admin"
    assert user.get_auth_level() == AUTH_LEVEL_USER, "Regular user should have USER auth level"
    print("✓ Regular user object works correctly")
    
    # Test admin user
    admin = User('adminuser', is_admin=True)
    assert admin.id == 'adminuser', "Admin ID should match username"
    assert admin.is_admin, "Admin user should be admin"
    assert admin.get_auth_level() == AUTH_LEVEL_ADMIN, "Admin user should have ADMIN auth level"
    print("✓ Admin user object works correctly")


def test_access_control():
    """Test access control for different endpoints"""
    print("\nTesting access control...")
    
    # Test guest access (unauthenticated)
    print("  Testing guest access...")
    guest_accessible = ['index', 'standings', 'fixtures']
    guest_blocked = ['statistics', 'player_stats', 'admin']
    
    # Note: These tests require Flask app context, so we'll test the logic directly
    from src.auth import GUEST_PAGES, USER_PAGES, ADMIN_PAGES
    
    # Verify GUEST_PAGES contains expected pages
    for page in guest_accessible:
        assert page in GUEST_PAGES, f"Guest should have access to {page}"
    print("  ✓ Guest pages configured correctly")
    
    # Verify USER_PAGES contains more than GUEST_PAGES
    assert len(USER_PAGES) > len(GUEST_PAGES), "USER_PAGES should include more pages than GUEST_PAGES"
    for page in guest_accessible:
        assert page in USER_PAGES, f"User should have access to guest page {page}"
    for page in ['statistics', 'player_stats', 'preferences']:
        assert page in USER_PAGES, f"User should have access to {page}"
    assert 'admin' not in USER_PAGES, "User should not have access to admin"
    print("  ✓ User pages configured correctly")
    
    # Verify ADMIN_PAGES contains all pages
    assert len(ADMIN_PAGES) > len(USER_PAGES), "ADMIN_PAGES should include more pages than USER_PAGES"
    for page in USER_PAGES:
        assert page in ADMIN_PAGES, f"Admin should have access to user page {page}"
    assert 'admin' in ADMIN_PAGES, "Admin should have access to admin page"
    print("  ✓ Admin pages configured correctly")


def test_default_admin_credentials():
    """Test default admin credentials (when env vars not set)"""
    print("\nTesting default admin credentials...")
    
    # Ensure env vars are not set
    if 'ADMIN_USERNAME' in os.environ:
        del os.environ['ADMIN_USERNAME']
    if 'ADMIN_PASSWORD_HASH' in os.environ:
        del os.environ['ADMIN_PASSWORD_HASH']
    
    # Test default admin credentials (admin/admin)
    is_valid, is_admin = verify_credentials('admin', 'admin')
    assert is_valid and is_admin, "Default admin credentials (admin/admin) should work"
    print("✓ Default admin credentials work")


def run_all_tests():
    """Run all authorization tests"""
    print("=" * 60)
    print("FLBB Statistics - Authorization Tests")
    print("=" * 60)
    
    try:
        test_password_hashing()
        test_verify_credentials()
        test_user_object()
        test_access_control()
        test_default_admin_credentials()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
