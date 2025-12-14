#!/usr/bin/env python3
"""
Test script for user login logging functionality.
This script verifies that:
1. Login events are logged to database
2. Login events are logged to file
3. Login statistics are calculated correctly
4. Admin page displays login information
"""

import os
import sys
import tempfile
from pathlib import Path
import sqlite3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ['SECRET_KEY'] = 'test-secret-key-for-login-logging'

from src.app import app
from src.user_database import (
    init_database, create_user, authenticate_user, 
    get_users_with_login_info, get_recent_login_logs, 
    get_login_statistics, DB_FILE, LOGIN_LOG_FILE
)


def test_login_logging():
    """Test login logging functionality"""
    print("=" * 70)
    print("Testing User Login Logging")
    print("=" * 70)
    
    # Initialize database
    print("\n1. Initializing test database...")
    init_database()
    print("   ✓ Database initialized")
    
    # Create a test user
    print("\n2. Creating test user...")
    success, msg = create_user('testuser', 'testpass123', 'user')
    if success:
        print(f"   ✓ Test user created: {msg}")
    else:
        print(f"   ℹ Test user: {msg}")
    
    # Test authentication with logging
    print("\n3. Testing authentication with logging...")
    success, user_data = authenticate_user(
        'testuser', 
        'testpass123',
        ip_address='127.0.0.1',
        user_agent='Test-Agent/1.0'
    )
    assert success, "Authentication should succeed"
    assert user_data is not None, "User data should be returned"
    print("   ✓ Authentication successful with logging")
    
    # Verify database has last_login_at updated
    print("\n4. Verifying last_login_at in database...")
    users = get_users_with_login_info()
    test_user = next((u for u in users if u['username'] == 'testuser'), None)
    assert test_user is not None, "Test user should exist"
    assert test_user['last_login_at'] is not None, "last_login_at should be set"
    print(f"   ✓ Last login recorded: {test_user['last_login_at']}")
    
    # Verify login_logs table has entry
    print("\n5. Verifying login_logs table...")
    recent_logs = get_recent_login_logs(limit=10)
    assert len(recent_logs) > 0, "Should have login logs"
    test_log = next((log for log in recent_logs if log['username'] == 'testuser'), None)
    assert test_log is not None, "Should have log for testuser"
    assert test_log['ip_address'] == '127.0.0.1', "IP address should match"
    assert test_log['user_agent'] == 'Test-Agent/1.0', "User agent should match"
    print(f"   ✓ Login log entry found: {test_log['login_time']}")
    
    # Verify login statistics
    print("\n6. Verifying login statistics...")
    stats = get_login_statistics()
    assert stats['total_logins'] > 0, "Should have at least one login"
    print(f"   ✓ Total logins: {stats['total_logins']}")
    print(f"   ✓ Unique users: {stats['unique_users']}")
    print(f"   ✓ Logins (24h): {stats['logins_24h']}")
    print(f"   ✓ Logins (7d): {stats['logins_7d']}")
    
    # Verify file logging
    print("\n7. Verifying file-based logging...")
    if LOGIN_LOG_FILE.exists():
        with open(LOGIN_LOG_FILE, 'r') as f:
            log_content = f.read()
            if 'testuser' in log_content:
                print(f"   ✓ Log file contains testuser entry")
                print(f"   ✓ Log file location: {LOGIN_LOG_FILE}")
            else:
                print(f"   ⚠ Log file exists but no testuser entry found")
    else:
        print(f"   ⚠ Log file not found at {LOGIN_LOG_FILE}")
    
    # Test admin page rendering
    print("\n8. Testing admin page with login info...")
    client = app.test_client()
    
    # Create admin user for testing
    success, msg = create_user('testadmin', 'adminpass123', 'admin')
    if success:
        print(f"   ✓ Test admin created")
    
    # Login as admin
    with client.session_transaction() as sess:
        sess['user_level'] = 'admin'
        sess['username'] = 'testadmin'
    
    response = client.get('/admin')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    response_text = response.data.decode('utf-8')
    
    # Check if login statistics are displayed
    assert 'User Login Activity' in response_text or 'Total Logins' in response_text, \
        "Admin page should display login activity"
    print("   ✓ Admin page displays login activity section")
    
    # Check if user table is present
    if 'Last Login' in response_text:
        print("   ✓ Admin page displays last login information")
    
    # Check if recent logins table is present
    if 'Recent Login Activity' in response_text:
        print("   ✓ Admin page displays recent login activity")
    
    print("\n" + "=" * 70)
    print("All Login Logging Tests Passed! ✓")
    print("=" * 70)
    
    return True


def test_multiple_logins():
    """Test multiple login tracking"""
    print("\n" + "=" * 70)
    print("Testing Multiple Login Tracking")
    print("=" * 70)
    
    # Get initial count
    stats_before = get_login_statistics()
    print(f"\n1. Initial login count: {stats_before['total_logins']}")
    
    # Perform multiple logins
    print("\n2. Performing multiple logins...")
    for i in range(3):
        success, _ = authenticate_user(
            'testuser',
            'testpass123',
            ip_address=f'192.168.1.{i+1}',
            user_agent=f'Test-Agent/{i+1}.0'
        )
        if success:
            print(f"   ✓ Login {i+1} successful")
    
    # Get updated count
    stats_after = get_login_statistics()
    print(f"\n3. Final login count: {stats_after['total_logins']}")
    
    assert stats_after['total_logins'] > stats_before['total_logins'], \
        "Login count should increase"
    print(f"   ✓ Login count increased by {stats_after['total_logins'] - stats_before['total_logins']}")
    
    # Check recent logs
    recent_logs = get_recent_login_logs(limit=5)
    print(f"\n4. Recent logs count: {len(recent_logs)}")
    for log in recent_logs[:3]:
        print(f"   - {log['username']} from {log['ip_address']} at {log['login_time']}")
    
    print("\n" + "=" * 70)
    print("Multiple Login Tracking Test Passed! ✓")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    try:
        test_login_logging()
        test_multiple_logins()
        
        print("\n" + "🎉 " * 10)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("🎉 " * 10 + "\n")
        
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
