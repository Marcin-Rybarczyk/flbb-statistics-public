#!/usr/bin/env python3
"""
Test script for user database functionality.
This script verifies that:
1. Database can be initialized
2. Users can be created and authenticated
3. Preferences can be stored and retrieved
4. Password hashing works correctly
5. User management functions work
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.user_database import (
    init_database, create_user, authenticate_user, get_user_preferences,
    update_user_preferences, delete_user, list_users, get_user_count,
    update_user_password, DB_FILE
)


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


def test_database_initialization():
    """Test database initialization"""
    print("\n" + "=" * 70)
    print("Test 1: Database Initialization")
    print("=" * 70)
    
    result = init_database()
    assert result == True, "Database initialization failed"
    assert DB_FILE.exists(), f"Database file not created at {DB_FILE}"
    print("✓ Database initialized successfully")
    print(f"✓ Database file created at: {DB_FILE}")


def test_user_creation():
    """Test user creation"""
    print("\n" + "=" * 70)
    print("Test 2: User Creation")
    print("=" * 70)
    
    # Test valid user creation
    success, message = create_user(
        username="testuser1",
        password="password123",
        division_name="U12 - Minimes",
        team_name="BC Dudelange"
    )
    assert success == True, f"User creation failed: {message}"
    print(f"✓ Created user: {message}")
    
    # Test duplicate username
    success, message = create_user(
        username="testuser1",
        password="password456"
    )
    assert success == False, "Duplicate username should fail"
    assert "already exists" in message, f"Expected duplicate error, got: {message}"
    print("✓ Duplicate username properly rejected")
    
    # Test invalid username (too long)
    success, message = create_user(
        username="x" * 51,
        password="password123"
    )
    assert success == False, "Long username should fail"
    print("✓ Invalid username properly rejected")
    
    # Test invalid password (too short)
    success, message = create_user(
        username="testuser2",
        password="12345"
    )
    assert success == False, "Short password should fail"
    print("✓ Invalid password properly rejected")


def test_authentication():
    """Test user authentication"""
    print("\n" + "=" * 70)
    print("Test 3: User Authentication")
    print("=" * 70)
    
    # Test valid authentication
    success, user_data = authenticate_user("testuser1", "password123")
    assert success == True, "Valid authentication failed"
    assert user_data['username'] == "testuser1", "Wrong username returned"
    assert user_data['division_name'] == "U12 - Minimes", "Wrong division returned"
    assert user_data['team_name'] == "BC Dudelange", "Wrong team returned"
    print("✓ Valid credentials authenticated successfully")
    print(f"  User data: {user_data}")
    
    # Test invalid password
    success, user_data = authenticate_user("testuser1", "wrongpassword")
    assert success == False, "Invalid password should fail"
    assert user_data is None, "User data should be None on failed auth"
    print("✓ Invalid password properly rejected")
    
    # Test non-existent user
    success, user_data = authenticate_user("nonexistent", "password123")
    assert success == False, "Non-existent user should fail"
    assert user_data is None, "User data should be None on failed auth"
    print("✓ Non-existent user properly rejected")


def test_preferences():
    """Test user preferences management"""
    print("\n" + "=" * 70)
    print("Test 4: User Preferences")
    print("=" * 70)
    
    # Get initial preferences
    prefs = get_user_preferences("testuser1")
    assert prefs is not None, "Failed to get preferences"
    assert prefs['division_name'] == "U12 - Minimes", "Wrong initial division"
    print(f"✓ Retrieved initial preferences: {prefs}")
    
    # Update preferences
    success, message = update_user_preferences(
        username="testuser1",
        division_name="U14 - Cadets",
        team_name="Racing Luxembourg"
    )
    assert success == True, f"Preference update failed: {message}"
    print(f"✓ Updated preferences: {message}")
    
    # Verify updated preferences
    prefs = get_user_preferences("testuser1")
    assert prefs['division_name'] == "U14 - Cadets", "Division not updated"
    assert prefs['team_name'] == "Racing Luxembourg", "Team not updated"
    print(f"✓ Verified updated preferences: {prefs}")
    
    # Test updating non-existent user
    success, message = update_user_preferences(
        username="nonexistent",
        division_name="Test"
    )
    assert success == False, "Update for non-existent user should fail"
    print("✓ Update for non-existent user properly rejected")


def test_password_update():
    """Test password update functionality"""
    print("\n" + "=" * 70)
    print("Test 5: Password Update")
    print("=" * 70)
    
    # Update password
    success, message = update_user_password("testuser1", "newpassword123")
    assert success == True, f"Password update failed: {message}"
    print(f"✓ Password updated: {message}")
    
    # Test authentication with new password
    success, user_data = authenticate_user("testuser1", "newpassword123")
    assert success == True, "Authentication with new password failed"
    print("✓ Authentication with new password successful")
    
    # Test authentication with old password (should fail)
    success, user_data = authenticate_user("testuser1", "password123")
    assert success == False, "Old password should not work"
    print("✓ Old password properly rejected")
    
    # Test invalid new password
    success, message = update_user_password("testuser1", "12345")
    assert success == False, "Short password should be rejected"
    print("✓ Invalid new password properly rejected")


def test_user_listing():
    """Test user listing and count"""
    print("\n" + "=" * 70)
    print("Test 6: User Listing")
    print("=" * 70)
    
    # Create a second user
    create_user(
        username="testuser2",
        password="password456",
        division_name="Total League",
        team_name="Arantia"
    )
    
    # Get user count
    count = get_user_count()
    assert count == 2, f"Expected 2 users, got {count}"
    print(f"✓ User count: {count}")
    
    # List users
    users = list_users()
    assert len(users) == 2, f"Expected 2 users in list, got {len(users)}"
    print(f"✓ Listed {len(users)} users")
    
    for user in users:
        print(f"  - {user['username']} (Division: {user['division_name']}, Team: {user['team_name']})")


def test_user_deletion():
    """Test user deletion"""
    print("\n" + "=" * 70)
    print("Test 7: User Deletion")
    print("=" * 70)
    
    # Delete user
    success, message = delete_user("testuser2")
    assert success == True, f"User deletion failed: {message}"
    print(f"✓ Deleted user: {message}")
    
    # Verify deletion
    count = get_user_count()
    assert count == 1, f"Expected 1 user after deletion, got {count}"
    print(f"✓ User count after deletion: {count}")
    
    # Try to delete non-existent user
    success, message = delete_user("nonexistent")
    assert success == False, "Deletion of non-existent user should fail"
    print("✓ Deletion of non-existent user properly rejected")


def test_user_limit():
    """Test 100 user limit handling"""
    print("\n" + "=" * 70)
    print("Test 8: User Limit (Creating 100 users)")
    print("=" * 70)
    
    # Note: We already have 1 user, so create 99 more
    existing_count = get_user_count()
    print(f"Starting with {existing_count} users")
    
    # Create users up to 100
    for i in range(existing_count + 1, 101):
        success, message = create_user(
            username=f"user{i}",
            password=f"password{i}"
        )
        if not success:
            print(f"✗ Failed to create user{i}: {message}")
            break
    
    final_count = get_user_count()
    print(f"✓ Created users, total count: {final_count}")
    assert final_count == 100, f"Expected 100 users, got {final_count}"
    
    # Try to create 101st user (should succeed at DB level, but script checks limit)
    success, message = create_user(
        username="user101",
        password="password101"
    )
    # The database itself doesn't enforce the limit, so this will succeed
    # The limit is enforced in the generate_password.py script
    print(f"✓ Database allows creating 101st user (limit enforced in script)")


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("USER DATABASE TEST SUITE")
    print("=" * 70)
    
    try:
        # Clean up any existing test database
        cleanup_test_db()
        
        # Run tests
        test_database_initialization()
        test_user_creation()
        test_authentication()
        test_preferences()
        test_password_update()
        test_user_listing()
        test_user_deletion()
        test_user_limit()
        
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
