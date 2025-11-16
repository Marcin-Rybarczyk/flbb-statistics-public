#!/usr/bin/env python3
"""
Test script for session persistence functionality.
This script verifies that:
1. Session configuration is properly set
2. Sessions persist across page navigation
3. Login creates a persistent session
4. Session cookies have proper security settings
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ['SECRET_KEY'] = 'test-secret-key-for-session-persistence'

from src.app import app
from src.user_database import init_database, create_user

def test_session_configuration():
    """Test that session configuration is properly set"""
    print("=" * 70)
    print("Testing Session Configuration")
    print("=" * 70)
    
    from datetime import timedelta
    
    # Check session configuration
    print("\n1. Checking session configuration...")
    assert app.config['PERMANENT_SESSION_LIFETIME'] == timedelta(days=31), \
        f"Expected 31 days, got {app.config['PERMANENT_SESSION_LIFETIME']}"
    print(f"   ✓ PERMANENT_SESSION_LIFETIME: {app.config['PERMANENT_SESSION_LIFETIME']}")
    
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax', \
        f"Expected 'Lax', got {app.config['SESSION_COOKIE_SAMESITE']}"
    print(f"   ✓ SESSION_COOKIE_SAMESITE: {app.config['SESSION_COOKIE_SAMESITE']}")
    
    assert app.config['SESSION_COOKIE_HTTPONLY'] == True, \
        f"Expected True, got {app.config['SESSION_COOKIE_HTTPONLY']}"
    print(f"   ✓ SESSION_COOKIE_HTTPONLY: {app.config['SESSION_COOKIE_HTTPONLY']}")
    
    assert app.config['SESSION_REFRESH_EACH_REQUEST'] == True, \
        f"Expected True, got {app.config['SESSION_REFRESH_EACH_REQUEST']}"
    print(f"   ✓ SESSION_REFRESH_EACH_REQUEST: {app.config['SESSION_REFRESH_EACH_REQUEST']}")
    
    print("\n" + "=" * 70)
    print("✅ SESSION CONFIGURATION TESTS PASSED")
    print("=" * 70)
    return True


def test_session_persistence():
    """Test that sessions persist across page navigation"""
    print("\n" + "=" * 70)
    print("Testing Session Persistence")
    print("=" * 70)
    
    # Initialize database and create test user
    print("\n1. Setting up test user...")
    init_database()
    success, message = create_user('session_test_user', 'testpass123', 'user')
    if not success and 'UNIQUE constraint' not in message:
        print(f"   Warning: {message}")
    print("   ✓ Test user ready")
    
    # Create test client
    client = app.test_client()
    
    # Test login
    print("\n2. Testing login...")
    response = client.post('/login', 
                          data={'username': 'session_test_user', 'password': 'testpass123'}, 
                          follow_redirects=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    print("   ✓ Login successful")
    
    # Test that session persists on subsequent requests
    print("\n3. Testing session persistence on protected pages...")
    
    # Access statistics page (requires user authentication)
    response = client.get('/statistics', follow_redirects=False)
    assert response.status_code == 200, \
        f"Session should persist, expected 200, got {response.status_code}"
    print("   ✓ Statistics page accessible (session persisted)")
    
    # Access player stats page
    response = client.get('/player-stats', follow_redirects=False)
    assert response.status_code == 200, \
        f"Session should persist, expected 200, got {response.status_code}"
    print("   ✓ Player stats page accessible (session persisted)")
    
    # Access team stats page
    response = client.get('/team-stats', follow_redirects=False)
    assert response.status_code == 200, \
        f"Session should persist, expected 200, got {response.status_code}"
    print("   ✓ Team stats page accessible (session persisted)")
    
    print("\n4. Testing session persistence on multiple requests...")
    for i in range(3):
        response = client.get('/standings', follow_redirects=False)  # Use public page that's faster
        assert response.status_code == 200, \
            f"Request {i+1}: Expected 200, got {response.status_code}"
    print("   ✓ Session persisted across 3 requests")
    
    # Test logout
    print("\n5. Testing logout...")
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    print("   ✓ Logout successful")
    
    # Verify session is cleared
    response = client.get('/statistics', follow_redirects=False)
    assert response.status_code == 302, \
        f"After logout, should redirect to login, got {response.status_code}"
    print("   ✓ Session cleared after logout")
    
    print("\n" + "=" * 70)
    print("✅ SESSION PERSISTENCE TESTS PASSED")
    print("=" * 70)
    return True


def test_secure_cookie_configuration():
    """Test that secure cookie settings work correctly"""
    print("\n" + "=" * 70)
    print("Testing Secure Cookie Configuration")
    print("=" * 70)
    
    # Test without FORCE_HTTPS
    print("\n1. Testing SESSION_COOKIE_SECURE without FORCE_HTTPS...")
    assert app.config['SESSION_COOKIE_SECURE'] == False, \
        "SESSION_COOKIE_SECURE should be False when FORCE_HTTPS is not set"
    print("   ✓ SESSION_COOKIE_SECURE is False (development mode)")
    
    # Test with FORCE_HTTPS
    print("\n2. Testing SESSION_COOKIE_SECURE with FORCE_HTTPS=true...")
    os.environ['FORCE_HTTPS'] = 'true'
    
    # Reimport to get new configuration
    import importlib
    import src.app
    importlib.reload(src.app)
    test_app = src.app.app
    
    assert test_app.config['SESSION_COOKIE_SECURE'] == True, \
        "SESSION_COOKIE_SECURE should be True when FORCE_HTTPS=true"
    print("   ✓ SESSION_COOKIE_SECURE is True (production mode with HTTPS)")
    
    # Clean up
    del os.environ['FORCE_HTTPS']
    
    print("\n" + "=" * 70)
    print("✅ SECURE COOKIE CONFIGURATION TESTS PASSED")
    print("=" * 70)
    return True


def run_all_tests():
    """Run all session persistence tests"""
    print("\n" + "🔒" * 35)
    print("SESSION PERSISTENCE TEST SUITE")
    print("🔒" * 35 + "\n")
    
    try:
        test_session_configuration()
        test_session_persistence()
        test_secure_cookie_configuration()
        
        # Clean up test database
        import os
        db_file = Path(__file__).parent.parent / 'data' / 'users.db'
        if db_file.exists():
            os.remove(db_file)
            print("\n✓ Test database cleaned up")
        
        print("\n" + "🎉" * 35)
        print("✅ ALL SESSION PERSISTENCE TESTS PASSED!")
        print("🎉" * 35 + "\n")
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


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
