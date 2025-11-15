#!/usr/bin/env python3
"""
Test script for admin user management functionality.
This script verifies that:
1. Admin can view user list
2. Admin can create users with default password
3. Admin can reset user passwords
4. Admin can delete users
5. Users can change their own passwords
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Flask app
from src.app import app
from src.user_database import (
    init_database, create_user, delete_user, DB_FILE,
    authenticate_user, list_users, get_user_count
)

# Default password from requirements
DEFAULT_PASSWORD = "kurwa"


def cleanup_test_db():
    """Remove test database if it exists"""
    import time
    import gc
    
    # Force garbage collection to close any lingering connections
    gc.collect()
    time.sleep(0.1)
    
    if DB_FILE.exists():
        try:
            # Also clean up WAL files if they exist
            wal_file = Path(str(DB_FILE) + '-wal')
            shm_file = Path(str(DB_FILE) + '-shm')
            
            DB_FILE.unlink()
            if wal_file.exists():
                wal_file.unlink()
            if shm_file.exists():
                shm_file.unlink()
                
            print(f"Removed existing test database: {DB_FILE}")
        except Exception as e:
            print(f"Warning: Could not remove database: {e}")


def setup_test_environment():
    """Set up test environment"""
    # Initialize database
    init_database()
    
    # Create a test admin (admin password is from env, not in database)
    # Create a test user for testing
    create_user("testuser1", "password123", "U12 - Minimes", "BC Dudelange")
    create_user("testuser2", "password456", "Total League", "Arantia")
    
    print("✓ Test environment set up")


def test_admin_user_list():
    """Test admin can view user list"""
    print("\n" + "=" * 70)
    print("Test 1: Admin User List")
    print("=" * 70)
    
    with app.test_client() as client:
        # Set up admin session
        with client.session_transaction() as sess:
            sess['admin_authenticated'] = True
        
        # Access user management page
        response = client.get('/admin/users')
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert b'User Management' in response.data, "User management page not loaded"
        assert b'testuser1' in response.data, "Test user not visible"
        
        print("✓ Admin can view user list")


def test_admin_create_user():
    """Test admin can create user with default password"""
    print("\n" + "=" * 70)
    print("Test 2: Admin Create User")
    print("=" * 70)
    
    with app.test_client() as client:
        # Set up admin session
        with client.session_transaction() as sess:
            sess['admin_authenticated'] = True
        
        # Create new user
        response = client.post('/admin/users/create', data={
            'username': 'newuser',
            'division_name': 'U14 - Cadets',
            'team_name': 'Racing Luxembourg'
        })
        
        if response.status_code != 200:
            data = response.get_json()
            print(f"Error response: {data}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.get_json()
        assert data['success'] == True, f"Expected success, got: {data}"
        
        # Verify user can login with default password
        success, user_data = authenticate_user('newuser', DEFAULT_PASSWORD)
        assert success == True, "User cannot login with default password"
        assert user_data['division_name'] == 'U14 - Cadets', "Division not set correctly"
        
        print(f"✓ Admin created user with default password '{DEFAULT_PASSWORD}'")
        print(f"✓ User can login with default password")


def test_admin_reset_password():
    """Test admin can reset user password"""
    print("\n" + "=" * 70)
    print("Test 3: Admin Reset Password")
    print("=" * 70)
    
    with app.test_client() as client:
        # Set up admin session
        with client.session_transaction() as sess:
            sess['admin_authenticated'] = True
        
        # Reset password for testuser1
        response = client.post('/admin/users/reset-password', data={
            'username': 'testuser1'
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.get_json()
        assert data['success'] == True, f"Expected success, got: {data}"
        
        # Verify old password doesn't work
        success, _ = authenticate_user('testuser1', 'password123')
        assert success == False, "Old password should not work"
        
        # Verify default password works
        success, _ = authenticate_user('testuser1', DEFAULT_PASSWORD)
        assert success == True, "Default password should work after reset"
        
        print(f"✓ Admin reset password to default '{DEFAULT_PASSWORD}'")
        print(f"✓ Old password no longer works")
        print(f"✓ Default password works")


def test_user_change_password():
    """Test user can change their own password"""
    print("\n" + "=" * 70)
    print("Test 4: User Change Password")
    print("=" * 70)
    
    with app.test_client() as client:
        # Set up user session
        with client.session_transaction() as sess:
            sess['user_authenticated'] = True
            sess['username'] = 'testuser2'
        
        # Change password
        response = client.post('/user/change-password', data={
            'current_password': 'password456',
            'new_password': 'mynewpassword123',
            'confirm_password': 'mynewpassword123'
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert b'Password changed successfully' in response.data, "Success message not found"
        
        # Verify new password works
        success, _ = authenticate_user('testuser2', 'mynewpassword123')
        assert success == True, "New password should work"
        
        # Verify old password doesn't work
        success, _ = authenticate_user('testuser2', 'password456')
        assert success == False, "Old password should not work"
        
        print("✓ User changed password successfully")
        print("✓ New password works")
        print("✓ Old password no longer works")


def test_password_validation():
    """Test password validation in user change password"""
    print("\n" + "=" * 70)
    print("Test 5: Password Validation")
    print("=" * 70)
    
    with app.test_client() as client:
        # Set up user session
        with client.session_transaction() as sess:
            sess['user_authenticated'] = True
            sess['username'] = 'testuser1'
        
        # Test password mismatch
        response = client.post('/user/change-password', data={
            'current_password': DEFAULT_PASSWORD,
            'new_password': 'newpass123',
            'confirm_password': 'different123'
        })
        assert b'do not match' in response.data, "Should detect password mismatch"
        print("✓ Password mismatch detected")
        
        # Test short password
        response = client.post('/user/change-password', data={
            'current_password': DEFAULT_PASSWORD,
            'new_password': '1234',
            'confirm_password': '1234'
        })
        assert b'at least 5 characters' in response.data, "Should detect short password"
        print("✓ Short password rejected")
        
        # Test wrong current password
        response = client.post('/user/change-password', data={
            'current_password': 'wrongpassword',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        assert b'Current password is incorrect' in response.data, "Should detect wrong current password"
        print("✓ Wrong current password detected")


def test_admin_delete_user():
    """Test admin can delete user"""
    print("\n" + "=" * 70)
    print("Test 6: Admin Delete User")
    print("=" * 70)
    
    initial_count = get_user_count()
    
    with app.test_client() as client:
        # Set up admin session
        with client.session_transaction() as sess:
            sess['admin_authenticated'] = True
        
        # Delete user
        response = client.post('/admin/users/delete', data={
            'username': 'newuser'
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.get_json()
        assert data['success'] == True, f"Expected success, got: {data}"
        
        # Verify user count decreased
        final_count = get_user_count()
        assert final_count == initial_count - 1, f"Expected count {initial_count - 1}, got {final_count}"
        
        print("✓ Admin deleted user successfully")
        print(f"✓ User count decreased from {initial_count} to {final_count}")


def test_unauthorized_access():
    """Test that unauthorized users cannot access admin features"""
    print("\n" + "=" * 70)
    print("Test 7: Unauthorized Access Prevention")
    print("=" * 70)
    
    with app.test_client() as client:
        # Try to access admin user management without auth
        response = client.get('/admin/users')
        # Should redirect to login
        assert response.status_code in [302, 401], f"Expected redirect or 401, got {response.status_code}"
        print("✓ Unauthorized access to admin users prevented")
        
        # Try to create user without auth
        response = client.post('/admin/users/create', data={'username': 'hacker'})
        assert response.status_code in [302, 401], f"Expected redirect or 401, got {response.status_code}"
        print("✓ Unauthorized user creation prevented")
        
        # Try to access password change without auth
        response = client.get('/user/change-password')
        assert response.status_code in [302, 401], f"Expected redirect or 401, got {response.status_code}"
        print("✓ Unauthorized password change prevented")


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("ADMIN USER MANAGEMENT TEST SUITE")
    print("=" * 70)
    
    # Set secret key for sessions
    app.config['SECRET_KEY'] = 'test-secret-key-for-testing'
    app.config['TESTING'] = True
    
    try:
        # Clean up any existing test database
        cleanup_test_db()
        
        # Set up test environment
        setup_test_environment()
        
        # Run tests
        test_admin_user_list()
        test_admin_create_user()
        test_admin_reset_password()
        test_user_change_password()
        test_password_validation()
        test_admin_delete_user()
        test_unauthorized_access()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test database
        print(f"\nCleaning up test database...")
        cleanup_test_db()
        print("Test database cleaned up")


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
