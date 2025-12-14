#!/usr/bin/env python3
"""
Test script for login redirect functionality.
This script verifies that:
1. Users are redirected to login when accessing protected pages
2. After successful login, users are redirected back to the originally requested page
3. The next parameter is preserved through GET and POST requests
4. Both user_required and admin_required decorators properly redirect with next parameter
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ['SECRET_KEY'] = 'test-secret-key-for-login-redirect'

from src.app import app
from src.user_database import init_database, create_user


def test_login_redirect_flow():
    """Test that login redirects back to the originally requested page"""
    print("=" * 70)
    print("Testing Login Redirect Functionality")
    print("=" * 70)
    
    # Initialize database and create test users
    print("\n1. Setting up test users...")
    init_database()
    
    # Create regular user
    success, message = create_user('redirect_test_user', 'testpass123', 'user')
    if not success and 'UNIQUE constraint' not in message:
        print(f"   Warning: {message}")
    
    # Create admin user
    success, message = create_user('redirect_test_admin', 'adminpass123', 'admin')
    if not success and 'UNIQUE constraint' not in message:
        print(f"   Warning: {message}")
    
    print("   ✓ Test users ready")
    
    # Create test client
    client = app.test_client()
    
    # Test 1: Access protected page without authentication (user_required)
    print("\n2. Testing redirect to login when accessing protected page (user_required)...")
    response = client.get('/statistics', follow_redirects=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert '/login' in response.location, f"Expected redirect to /login, got {response.location}"
    assert 'next=' in response.location, f"Expected 'next' parameter in redirect: {response.location}"
    assert '%2Fstatistics' in response.location or '/statistics' in response.location, \
        f"Expected '/statistics' in next parameter: {response.location}"
    print("   ✓ Redirected to login with next parameter")
    
    # Test 2: Follow the redirect and verify login page receives next parameter
    print("\n3. Testing that login page receives next parameter...")
    response = client.get('/login?next=/statistics', follow_redirects=False)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    response_data = response.data.decode('utf-8')
    assert 'name="next"' in response_data or 'next' in response_data, \
        "Login page should have next parameter in form"
    print("   ✓ Login page received next parameter")
    
    # Test 3: Submit login form with next parameter
    print("\n4. Testing login with next parameter redirects to requested page...")
    response = client.post('/login?next=/statistics',
                          data={'username': 'redirect_test_user', 'password': 'testpass123'},
                          follow_redirects=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert '/statistics' in response.location, \
        f"Expected redirect to /statistics, got {response.location}"
    print("   ✓ Successfully redirected to /statistics after login")
    
    # Test 4: Verify session persists and page is accessible
    print("\n5. Testing that redirected page is now accessible...")
    response = client.get('/statistics', follow_redirects=False)
    assert response.status_code == 200, \
        f"After login, page should be accessible, got {response.status_code}"
    print("   ✓ Statistics page accessible after login")
    
    # Logout for next test
    client.get('/logout')
    
    # Test 5: Test with admin_required decorator
    print("\n6. Testing redirect for admin-only pages...")
    response = client.get('/admin', follow_redirects=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert '/login' in response.location, f"Expected redirect to /login, got {response.location}"
    assert 'next=' in response.location, f"Expected 'next' parameter in redirect: {response.location}"
    print("   ✓ Admin page redirected to login with next parameter")
    
    # Test 6: Login as admin and verify redirect to admin page
    print("\n7. Testing admin login redirect to requested page...")
    response = client.post('/login?next=/admin',
                          data={'username': 'redirect_test_admin', 'password': 'adminpass123'},
                          follow_redirects=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert '/admin' in response.location, \
        f"Expected redirect to /admin, got {response.location}"
    print("   ✓ Successfully redirected to /admin after admin login")
    
    # Test 7: Test failed login preserves next parameter
    client.get('/logout')
    print("\n8. Testing that failed login preserves next parameter...")
    response = client.post('/login?next=/statistics',
                          data={'username': 'redirect_test_user', 'password': 'wrongpassword'},
                          follow_redirects=False)
    assert response.status_code == 200, f"Expected 200 (error page), got {response.status_code}"
    response_data = response.data.decode('utf-8')
    assert 'Invalid' in response_data or 'error' in response_data.lower(), \
        "Expected error message"
    assert 'name="next"' in response_data or 'value="/statistics"' in response_data, \
        "Next parameter should be preserved in form after failed login"
    print("   ✓ Failed login preserves next parameter")
    
    # Test 8: Multiple protected pages
    print("\n9. Testing various protected pages redirect properly...")
    protected_pages = [
        '/player-stats',
        '/team-stats',
        '/deeper-analysis',
        '/referee-stats'
    ]
    
    for page in protected_pages:
        response = client.get(page, follow_redirects=False)
        assert response.status_code == 302, \
            f"Page {page}: Expected 302 redirect, got {response.status_code}"
        assert '/login' in response.location, \
            f"Page {page}: Expected redirect to /login, got {response.location}"
        assert 'next=' in response.location, \
            f"Page {page}: Expected 'next' parameter in redirect: {response.location}"
    print("   ✓ All protected pages redirect with next parameter")
    
    # Test 9: Test that next parameter is ignored for external URLs (security check)
    print("\n10. Testing security: external URLs in next parameter are ignored...")
    response = client.post('/login',
                          data={
                              'username': 'redirect_test_user',
                              'password': 'testpass123',
                              'next': 'http://evil.com/phishing'
                          },
                          follow_redirects=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    # Should redirect to index, not to external URL
    assert 'evil.com' not in response.location, \
        "External URLs should be ignored in next parameter"
    assert '/' in response.location, \
        f"Expected redirect to internal page, got {response.location}"
    print("   ✓ External URLs in next parameter are properly ignored")
    
    print("\n" + "=" * 70)
    print("✅ ALL LOGIN REDIRECT TESTS PASSED")
    print("=" * 70)
    return True


def run_all_tests():
    """Run all login redirect tests"""
    print("\n" + "🔄" * 35)
    print("LOGIN REDIRECT TEST SUITE")
    print("🔄" * 35 + "\n")
    
    try:
        test_login_redirect_flow()
        
        # Clean up test database
        import os
        db_file = Path(__file__).parent.parent / 'data' / 'users.db'
        if db_file.exists():
            os.remove(db_file)
            print("\n✓ Test database cleaned up")
        
        print("\n" + "🎉" * 35)
        print("✅ ALL LOGIN REDIRECT TESTS PASSED!")
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
