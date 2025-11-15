#!/usr/bin/env python3
"""
Test script for Flask integration with user database.
This script verifies that:
1. User login works with database authentication
2. User preferences are loaded from database
3. User preferences are saved to database
4. Session management works correctly
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ['SECRET_KEY'] = 'test-secret-key-for-flask-integration'
os.environ['ADMIN_PASSWORD'] = 'admin123'

from src.app import app
from src.user_database import create_user, delete_user, get_user_preferences


def test_database_authentication():
    """Test user authentication with database"""
    print("=" * 70)
    print("Testing Database Authentication Integration")
    print("=" * 70)
    
    # Create test client
    client = app.test_client()
    
    # Create a test user if not exists
    print("\n1. Creating test user...")
    delete_user("flasktest")  # Clean up if exists
    success, msg = create_user(
        username="flasktest",
        password="testpass123",
        division_name="U14 - Cadets",
        team_name="Racing Luxembourg"
    )
    print(f"   {msg}")
    assert success, f"Failed to create test user: {msg}"
    
    # Test login with database credentials
    print("\n2. Testing login with database credentials...")
    response = client.post('/user/login', data={
        'username': 'flasktest',
        'password': 'testpass123'
    }, follow_redirects=False)
    
    assert response.status_code == 302, f"Expected redirect (302), got {response.status_code}"
    assert '/' in response.location, f"Expected redirect to /, got {response.location}"
    print("   ✓ Login successful with database credentials")
    
    # Test that invalid password fails
    print("\n3. Testing login with invalid password...")
    response = client.post('/user/login', data={
        'username': 'flasktest',
        'password': 'wrongpassword'
    }, follow_redirects=False)
    
    assert response.status_code == 200, f"Expected 200 (error page), got {response.status_code}"
    response_data = response.data.decode('utf-8')
    assert 'Invalid username or password' in response_data, "Expected error message"
    print("   ✓ Invalid password properly rejected")
    
    # Test that preferences are loaded from database
    print("\n4. Testing preference loading from database...")
    with client.session_transaction() as sess:
        sess['user_authenticated'] = True
        sess['username'] = 'flasktest'
    
    # Check that preferences were loaded (simulate login)
    response = client.post('/user/login', data={
        'username': 'flasktest',
        'password': 'testpass123'
    }, follow_redirects=False)
    
    # Check session has preferences
    with client.session_transaction() as sess:
        assert sess.get('preferred_division') == "U14 - Cadets", "Division not loaded from database"
        assert sess.get('preferred_team') == "Racing Luxembourg", "Team not loaded from database"
        assert sess.get('username') == 'flasktest', "Username not stored in session"
    
    print("   ✓ Preferences loaded from database into session")
    print(f"     Division: {sess.get('preferred_division')}")
    print(f"     Team: {sess.get('preferred_team')}")
    
    # Test updating preferences
    print("\n5. Testing preference updates to database...")
    response = client.post('/preferences', data={
        'division': 'Total League',
        'team': 'Arantia',
        'theme': 'ocean'
    }, follow_redirects=False)
    
    # Verify preferences were saved to database
    prefs = get_user_preferences('flasktest')
    assert prefs is not None, "Preferences not found in database"
    assert prefs['division_name'] == 'Total League', "Division not updated in database"
    assert prefs['team_name'] == 'Arantia', "Team not updated in database"
    print("   ✓ Preferences updated in database")
    print(f"     New Division: {prefs['division_name']}")
    print(f"     New Team: {prefs['team_name']}")
    
    # Test logout
    print("\n6. Testing logout...")
    response = client.get('/user/logout', follow_redirects=False)
    assert response.status_code == 302, f"Expected redirect (302), got {response.status_code}"
    
    with client.session_transaction() as sess:
        assert not sess.get('user_authenticated', False), "User should not be authenticated after logout"
        assert not sess.get('username'), "Username should be cleared after logout"
    print("   ✓ Logout successful, session cleared")
    
    # Clean up test user
    print("\n7. Cleaning up test user...")
    success, msg = delete_user("flasktest")
    print(f"   {msg}")
    
    print("\n" + "=" * 70)
    print("✅ ALL FLASK INTEGRATION TESTS PASSED")
    print("=" * 70)
    return True


def test_environment_variable_fallback():
    """Test that environment variable authentication still works as fallback"""
    print("\n" + "=" * 70)
    print("Testing Environment Variable Fallback")
    print("=" * 70)
    
    # Set environment variables
    os.environ['USER_USERNAME'] = 'envuser'
    os.environ['USER_PASSWORD'] = 'envpass123'
    
    # Create test client
    client = app.test_client()
    
    print("\n1. Testing login with environment variables...")
    response = client.post('/user/login', data={
        'username': 'envuser',
        'password': 'envpass123'
    }, follow_redirects=False)
    
    assert response.status_code == 302, f"Expected redirect (302), got {response.status_code}"
    print("   ✓ Environment variable authentication works")
    
    # Clean up
    with client.session_transaction() as sess:
        sess.clear()
    
    del os.environ['USER_USERNAME']
    del os.environ['USER_PASSWORD']
    
    print("\n" + "=" * 70)
    print("✅ ENVIRONMENT VARIABLE FALLBACK TEST PASSED")
    print("=" * 70)
    return True


if __name__ == '__main__':
    try:
        success1 = test_database_authentication()
        success2 = test_environment_variable_fallback()
        
        sys.exit(0 if (success1 and success2) else 1)
        
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
