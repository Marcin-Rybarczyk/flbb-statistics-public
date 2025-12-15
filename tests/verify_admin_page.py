#!/usr/bin/env python3
"""
Script to capture admin page HTML with login information
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ['SECRET_KEY'] = 'test-key-for-html-capture'

from src.app import app
from src.user_database import create_user

# Initialize app test client
client = app.test_client()

# Create an admin user for testing
create_user('htmltest_admin', 'testpass', 'admin')

# Set session as admin
with client.session_transaction() as sess:
    sess['user_level'] = 'admin'
    sess['username'] = 'htmltest_admin'

# Get admin page
response = client.get('/admin')

if response.status_code == 200:
    html = response.data.decode('utf-8')
    
    # Check for key sections
    checks = {
        'User Login Activity section': 'User Login Activity' in html or '👤 User Login Activity' in html,
        'Total Logins display': 'Total Logins' in html,
        'Last Login table': 'Last Login' in html,
        'Recent Login Activity': 'Recent Login Activity' in html,
        'Users table': 'Username' in html and 'User Level' in html,
    }
    
    print("\n" + "=" * 70)
    print("Admin Page HTML Content Verification")
    print("=" * 70)
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"{status} {check_name}: {'Present' if result else 'Missing'}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("✅ All required sections are present in the admin page!")
        
        # Extract and display the login activity section
        import re
        
        # Find the User Login Activity section
        pattern = r'User Login Activity.*?(?=<div class="stats-section">|$)'
        match = re.search(pattern, html, re.DOTALL)
        
        if match:
            print("\nSample of User Login Activity HTML:")
            print("-" * 70)
            section = match.group(0)[:500]  # First 500 chars
            print(section)
            print("...")
        
        sys.exit(0)
    else:
        print("❌ Some sections are missing from the admin page")
        sys.exit(1)
else:
    print(f"❌ Failed to load admin page: {response.status_code}")
    sys.exit(1)
