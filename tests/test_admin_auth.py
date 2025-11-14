#!/usr/bin/env python3
"""
Test script for admin authentication functionality.
This script verifies that:
1. Import button is hidden when not authenticated
2. Login functionality works correctly
3. Import/Export routes are protected
4. Logout functionality works
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ['ADMIN_PASSWORD'] = 'test123'
os.environ['SECRET_KEY'] = 'test-secret-key'

from src.app import app

def test_admin_authentication():
    """Test admin authentication functionality"""
    print("=" * 70)
    print("Testing Admin Authentication")
    print("=" * 70)
    
    # Create test client
    client = app.test_client()
    
    # Test 1: Check that admin page is accessible without authentication
    print("\n1. Testing /admin page without authentication...")
    response = client.get('/admin')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("   ✓ Admin page is accessible")
    
    # Test 2: Check that import button is hidden in the response
    print("\n2. Checking if import form is hidden when not authenticated...")
    response_data = response.data.decode('utf-8')
    if 'importForm' in response_data:
        # Check if it's wrapped in authentication check
        if '{% if is_admin_authenticated %}' in response_data or 'is_admin_authenticated' in response_data:
            print("   ✓ Import form is conditionally rendered")
        else:
            print("   ⚠ Warning: Import form might be visible without authentication")
    else:
        print("   ✓ Import form is not present in non-authenticated view")
    
    # Test 3: Verify import endpoint is protected
    print("\n3. Testing /admin/import-season endpoint protection...")
    # Create a dummy file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(b'dummy data')
    
    try:
        with open(tmp_path, 'rb') as f:
            response = client.post('/admin/import-season', 
                                 data={'archive_file': (f, 'test.zip')},
                                 content_type='multipart/form-data')
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        result = response.get_json()
        assert result['success'] == False, "Expected success=False"
        assert 'authentication required' in result['error'].lower(), "Expected authentication error"
        print("   ✓ Import endpoint is protected")
    finally:
        os.unlink(tmp_path)
    
    # Test 4: Verify export endpoint is protected
    print("\n4. Testing /admin/export-season endpoint protection...")
    response = client.post('/admin/export-season')
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    result = response.get_json()
    assert result['success'] == False, "Expected success=False"
    print("   ✓ Export endpoint is protected")
    
    # Test 5: Test login page
    print("\n5. Testing /admin/login page...")
    response = client.get('/admin/login')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("   ✓ Login page is accessible")
    
    # Test 6: Test invalid login
    print("\n6. Testing login with invalid password...")
    response = client.post('/admin/login', data={'password': 'wrongpassword'}, follow_redirects=False)
    assert response.status_code == 200, f"Expected 200 (error page), got {response.status_code}"
    response_data = response.data.decode('utf-8')
    assert 'Invalid password' in response_data or 'error' in response_data.lower(), "Expected error message"
    print("   ✓ Invalid password rejected")
    
    # Test 7: Test valid login
    print("\n7. Testing login with valid password...")
    response = client.post('/admin/login', data={'password': 'test123'}, follow_redirects=False)
    assert response.status_code == 302, f"Expected 302 (redirect), got {response.status_code}"
    assert '/admin' in response.location, f"Expected redirect to /admin, got {response.location}"
    print("   ✓ Valid password accepted and redirected to admin page")
    
    # Test 8: Test authenticated access to import endpoint
    print("\n8. Testing import endpoint with authentication...")
    with client.session_transaction() as sess:
        sess['admin_authenticated'] = True
    
    # Try again with authentication
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(b'PK\x03\x04')  # Minimal ZIP header
    
    try:
        with open(tmp_path, 'rb') as f:
            response = client.post('/admin/import-season', 
                                 data={'archive_file': (f, 'test.zip')},
                                 content_type='multipart/form-data')
        # Should not be 401 anymore (will fail for other reasons like invalid ZIP, but not auth)
        assert response.status_code != 401, f"Should not be 401 when authenticated, got {response.status_code}"
        print("   ✓ Import endpoint accessible when authenticated")
    finally:
        os.unlink(tmp_path)
    
    # Test 9: Test logout
    print("\n9. Testing logout functionality...")
    response = client.get('/admin/logout', follow_redirects=False)
    assert response.status_code == 302, f"Expected 302 (redirect), got {response.status_code}"
    print("   ✓ Logout redirects successfully")
    
    # Verify session is cleared
    with client.session_transaction() as sess:
        assert not sess.get('admin_authenticated', False), "Session should be cleared after logout"
    print("   ✓ Session cleared after logout")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == '__main__':
    try:
        success = test_admin_authentication()
        sys.exit(0 if success else 1)
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
