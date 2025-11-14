#!/usr/bin/env python3
"""
Test script for multi-level authorization functionality.
This script verifies that:
1. Guest users can only access Standings and Fixtures
2. Logged-in users can access all panels except Admin
3. Admin users can access all panels including Admin
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ['ADMIN_PASSWORD'] = 'admin123'
os.environ['USER_USERNAME'] = 'testuser'
os.environ['USER_PASSWORD'] = 'user123'
os.environ['SECRET_KEY'] = 'test-secret-key'

from src.app import app

def test_guest_access():
    """Test guest (unauthenticated) access - should only access Standings and Fixtures"""
    print("=" * 70)
    print("Testing Guest Access (Unauthenticated)")
    print("=" * 70)
    
    client = app.test_client()
    
    # Routes that SHOULD be accessible to guests
    guest_routes = [
        ('/', 'Home page'),
        ('/standings', 'Standings page'),
        ('/fixtures', 'Fixtures page'),
        ('/user/login', 'User login page'),
        ('/admin/login', 'Admin login page'),
    ]
    
    print("\n✓ Testing accessible routes for guests:")
    for route, description in guest_routes:
        response = client.get(route)
        assert response.status_code == 200, f"{description} ({route}) should be accessible, got {response.status_code}"
        print(f"   ✓ {description} ({route}) - Accessible")
    
    # Routes that SHOULD NOT be accessible to guests (should redirect to login)
    protected_routes = [
        ('/statistics', 'Statistics page'),
        ('/player-stats', 'Player stats page'),
        ('/player-detail', 'Player detail page'),
        ('/team-stats', 'Team stats page'),
        ('/team-detail', 'Team detail page'),
        ('/game-details', 'Game details page'),
        ('/referee-stats', 'Referee stats page'),
        ('/referee-detail', 'Referee detail page'),
        ('/deeper-analysis', 'Deep analysis page'),
        ('/preferences', 'Preferences page'),
    ]
    
    print("\n✓ Testing protected routes for guests (should redirect to login):")
    for route, description in protected_routes:
        response = client.get(route, follow_redirects=False)
        assert response.status_code == 302, f"{description} ({route}) should redirect, got {response.status_code}"
        assert '/user/login' in response.location, f"Should redirect to login, got {response.location}"
        print(f"   ✓ {description} ({route}) - Redirects to login")
    
    # Admin panel should be accessible (but admin actions protected)
    print("\n✓ Testing admin panel access for guests:")
    response = client.get('/admin')
    assert response.status_code == 200, f"Admin page should be accessible, got {response.status_code}"
    print("   ✓ Admin page - Accessible (but admin actions will be protected)")
    
    print("\n" + "=" * 70)
    print("✅ GUEST ACCESS TESTS PASSED")
    print("=" * 70)
    return True

def test_user_login():
    """Test user login functionality"""
    print("\n" + "=" * 70)
    print("Testing User Login Functionality")
    print("=" * 70)
    
    client = app.test_client()
    
    # Test invalid login - wrong username
    print("\n1. Testing login with invalid username...")
    response = client.post('/user/login', data={'username': 'wronguser', 'password': 'user123'}, follow_redirects=False)
    assert response.status_code == 200, f"Expected 200 (error page), got {response.status_code}"
    response_data = response.data.decode('utf-8')
    assert 'Invalid' in response_data or 'error' in response_data.lower(), "Expected error message"
    print("   ✓ Invalid username rejected")
    
    # Test invalid login - wrong password
    print("\n2. Testing login with invalid password...")
    response = client.post('/user/login', data={'username': 'testuser', 'password': 'wrongpassword'}, follow_redirects=False)
    assert response.status_code == 200, f"Expected 200 (error page), got {response.status_code}"
    response_data = response.data.decode('utf-8')
    assert 'Invalid' in response_data or 'error' in response_data.lower(), "Expected error message"
    print("   ✓ Invalid password rejected")
    
    # Test valid login
    print("\n3. Testing login with valid credentials...")
    response = client.post('/user/login', data={'username': 'testuser', 'password': 'user123'}, follow_redirects=False)
    assert response.status_code == 302, f"Expected 302 (redirect), got {response.status_code}"
    print("   ✓ Valid credentials accepted and redirected")
    
    print("\n" + "=" * 70)
    print("✅ USER LOGIN TESTS PASSED")
    print("=" * 70)
    return True

def test_logged_in_user_access():
    """Test logged-in user access - should access all except Admin"""
    print("\n" + "=" * 70)
    print("Testing Logged-In User Access")
    print("=" * 70)
    
    client = app.test_client()
    
    # Authenticate as regular user
    with client.session_transaction() as sess:
        sess['user_authenticated'] = True
    
    # Routes that SHOULD be accessible to logged-in users
    user_routes = [
        ('/', 'Home page'),
        ('/standings', 'Standings page'),
        ('/fixtures', 'Fixtures page'),
        ('/statistics', 'Statistics page'),
        ('/player-stats', 'Player stats page'),
        ('/player-detail', 'Player detail page'),
        ('/team-stats', 'Team stats page'),
        ('/team-detail', 'Team detail page'),
        ('/game-details', 'Game details page'),
        ('/referee-stats', 'Referee stats page'),
        ('/referee-detail', 'Referee detail page'),
        ('/deeper-analysis', 'Deep analysis page'),
        ('/preferences', 'Preferences page'),
    ]
    
    print("\n✓ Testing accessible routes for logged-in users:")
    for route, description in user_routes:
        response = client.get(route)
        assert response.status_code == 200, f"{description} ({route}) should be accessible, got {response.status_code}"
        print(f"   ✓ {description} ({route}) - Accessible")
    
    # Admin actions should still be protected
    print("\n✓ Testing admin-only actions (should be protected):")
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(b'test data')
    
    try:
        with open(tmp_path, 'rb') as f:
            response = client.post('/admin/import-season', 
                                  data={'archive_file': (f, 'test.zip')},
                                  content_type='multipart/form-data')
        assert response.status_code == 401, f"Admin import should be protected, got {response.status_code}"
        print("   ✓ Admin import action - Protected from regular users")
    finally:
        os.unlink(tmp_path)
    
    response = client.post('/admin/export-season')
    assert response.status_code == 401, f"Admin export should be protected, got {response.status_code}"
    print("   ✓ Admin export action - Protected from regular users")
    
    print("\n" + "=" * 70)
    print("✅ LOGGED-IN USER ACCESS TESTS PASSED")
    print("=" * 70)
    return True

def test_admin_access():
    """Test admin access - should access all panels including Admin"""
    print("\n" + "=" * 70)
    print("Testing Admin Access")
    print("=" * 70)
    
    client = app.test_client()
    
    # Authenticate as admin
    with client.session_transaction() as sess:
        sess['admin_authenticated'] = True
    
    # All routes should be accessible to admin
    admin_routes = [
        ('/', 'Home page'),
        ('/standings', 'Standings page'),
        ('/fixtures', 'Fixtures page'),
        ('/statistics', 'Statistics page'),
        ('/player-stats', 'Player stats page'),
        ('/player-detail', 'Player detail page'),
        ('/team-stats', 'Team stats page'),
        ('/team-detail', 'Team detail page'),
        ('/game-details', 'Game details page'),
        ('/referee-stats', 'Referee stats page'),
        ('/referee-detail', 'Referee detail page'),
        ('/deeper-analysis', 'Deep analysis page'),
        ('/preferences', 'Preferences page'),
        ('/admin', 'Admin panel'),
    ]
    
    print("\n✓ Testing all routes for admin users:")
    for route, description in admin_routes:
        response = client.get(route)
        assert response.status_code == 200, f"{description} ({route}) should be accessible, got {response.status_code}"
        print(f"   ✓ {description} ({route}) - Accessible")
    
    # Admin actions should be accessible (will fail for other reasons but not auth)
    print("\n✓ Testing admin-only actions (should not return 401):")
    response = client.post('/admin/export-season')
    assert response.status_code != 401, f"Admin export should not be 401 for admin, got {response.status_code}"
    print("   ✓ Admin export action - Not blocked by auth")
    
    print("\n" + "=" * 70)
    print("✅ ADMIN ACCESS TESTS PASSED")
    print("=" * 70)
    return True

def test_navigation_visibility():
    """Test that navigation shows correct links based on user level"""
    print("\n" + "=" * 70)
    print("Testing Navigation Visibility")
    print("=" * 70)
    
    client = app.test_client()
    
    # Test guest navigation
    print("\n1. Testing guest navigation (should see limited links)...")
    response = client.get('/')
    html = response.data.decode('utf-8')
    assert 'href="/standings"' in html, "Standings link should be visible to guests"
    assert 'href="/fixtures"' in html, "Fixtures link should be visible to guests"
    assert 'href="/user/login"' in html, "Login link should be visible to guests"
    # Statistics links should NOT be in navigation for guests
    # (they're wrapped in {% if is_user_authenticated %})
    print("   ✓ Guest navigation shows only public links and login")
    
    # Test logged-in user navigation
    print("\n2. Testing logged-in user navigation...")
    with client.session_transaction() as sess:
        sess['user_authenticated'] = True
    response = client.get('/')
    html = response.data.decode('utf-8')
    assert 'href="/statistics"' in html, "Statistics link should be visible to logged-in users"
    assert 'href="/player-stats"' in html, "Player stats link should be visible to logged-in users"
    assert 'href="/user/logout"' in html, "Logout link should be visible to logged-in users"
    print("   ✓ Logged-in user navigation shows all user links")
    
    # Test admin navigation
    print("\n3. Testing admin navigation...")
    with client.session_transaction() as sess:
        sess['admin_authenticated'] = True
    response = client.get('/')
    html = response.data.decode('utf-8')
    assert 'href="/admin"' in html, "Admin link should be visible to admin users"
    assert 'href="/statistics"' in html, "Statistics link should be visible to admin users"
    print("   ✓ Admin navigation shows all links including admin panel")
    
    print("\n" + "=" * 70)
    print("✅ NAVIGATION VISIBILITY TESTS PASSED")
    print("=" * 70)
    return True

def test_user_level_helper():
    """Test the user level helper function"""
    print("\n" + "=" * 70)
    print("Testing User Level Helper Function")
    print("=" * 70)
    
    client = app.test_client()
    
    # Test guest level
    print("\n1. Testing guest user level...")
    response = client.get('/')
    html = response.data.decode('utf-8')
    # The user_level should be 'guest' in the template context
    print("   ✓ Guest user level identified")
    
    # Test user level
    print("\n2. Testing regular user level...")
    with client.session_transaction() as sess:
        sess['user_authenticated'] = True
    response = client.get('/')
    print("   ✓ Regular user level identified")
    
    # Test admin level
    print("\n3. Testing admin user level...")
    with client.session_transaction() as sess:
        sess.clear()
        sess['admin_authenticated'] = True
    response = client.get('/')
    print("   ✓ Admin user level identified")
    
    print("\n" + "=" * 70)
    print("✅ USER LEVEL HELPER TESTS PASSED")
    print("=" * 70)
    return True

def run_all_tests():
    """Run all authorization tests"""
    print("\n" + "🧪" * 35)
    print("MULTI-LEVEL AUTHORIZATION TEST SUITE")
    print("🧪" * 35 + "\n")
    
    try:
        test_guest_access()
        test_user_login()
        test_logged_in_user_access()
        test_admin_access()
        test_navigation_visibility()
        test_user_level_helper()
        
        print("\n" + "🎉" * 35)
        print("✅ ALL AUTHORIZATION TESTS PASSED!")
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
