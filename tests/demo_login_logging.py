#!/usr/bin/env python3
"""
Manual demonstration script for user login logging.
This script creates a test user and demonstrates the login logging feature.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ['SECRET_KEY'] = 'demo-secret-key'

from src.user_database import (
    init_database, create_user, authenticate_user,
    get_users_with_login_info, get_recent_login_logs,
    get_login_statistics, LOGIN_LOG_FILE
)


def main():
    """Demonstrate login logging functionality"""
    print("\n" + "=" * 70)
    print("User Login Logging - Manual Demonstration")
    print("=" * 70)
    
    # Initialize database
    print("\n📚 Step 1: Initializing database...")
    init_database()
    print("   ✓ Database initialized")
    
    # Create demo users if they don't exist
    print("\n👤 Step 2: Creating demo users...")
    users_to_create = [
        ('demo_user', 'password123', 'user'),
        ('demo_admin', 'admin123', 'admin'),
    ]
    
    for username, password, level in users_to_create:
        success, msg = create_user(username, password, level)
        if success:
            print(f"   ✓ Created {level}: {username}")
        else:
            print(f"   ℹ {username}: {msg}")
    
    # Simulate login events
    print("\n🔐 Step 3: Simulating login events...")
    login_scenarios = [
        ('demo_user', 'password123', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
        ('demo_admin', 'admin123', '10.0.0.50', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'),
        ('demo_user', 'password123', '192.168.1.101', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)'),
    ]
    
    for username, password, ip, user_agent in login_scenarios:
        success, user_data = authenticate_user(username, password, ip, user_agent)
        if success:
            print(f"   ✓ {username} logged in from {ip}")
    
    # Display login statistics
    print("\n📊 Step 4: Login Statistics")
    print("-" * 70)
    stats = get_login_statistics()
    print(f"   Total Logins:        {stats['total_logins']}")
    print(f"   Unique Users:        {stats['unique_users']}")
    print(f"   Logins (24h):        {stats['logins_24h']}")
    print(f"   Logins (7 days):     {stats['logins_7d']}")
    if stats['most_active_user']:
        print(f"   Most Active User:    {stats['most_active_user']} ({stats['most_active_count']} logins)")
    
    # Display users with last login
    print("\n👥 Step 5: Users - Last Login Information")
    print("-" * 70)
    users = get_users_with_login_info()
    print(f"   {'Username':<20} {'Level':<10} {'Last Login':<25}")
    print("   " + "-" * 70)
    for user in users[:10]:  # Show first 10 users
        level_icon = "👑" if user['user_level'] == 'admin' else "👤"
        last_login = user['last_login_at'] if user['last_login_at'] else 'Never'
        print(f"   {level_icon} {user['username']:<18} {user['user_level']:<10} {last_login}")
    
    # Display recent logins
    print("\n🔄 Step 6: Recent Login Activity")
    print("-" * 70)
    recent_logins = get_recent_login_logs(limit=10)
    print(f"   {'Time':<25} {'Username':<15} {'IP Address':<18}")
    print("   " + "-" * 70)
    for login in recent_logins:
        print(f"   {login['login_time']:<25} {login['username']:<15} {login['ip_address'] or 'N/A':<18}")
    
    # Display log file location
    print("\n📝 Step 7: Log File Information")
    print("-" * 70)
    print(f"   Log file location: {LOGIN_LOG_FILE}")
    if LOGIN_LOG_FILE.exists():
        log_size = LOGIN_LOG_FILE.stat().st_size
        print(f"   Log file size:     {log_size} bytes")
        print(f"   ✓ Log file exists and is being written")
        
        # Show last 5 lines of log file
        print("\n   Last 5 log entries:")
        with open(LOGIN_LOG_FILE, 'r') as f:
            lines = f.readlines()
            for line in lines[-5:]:
                print(f"   │ {line.rstrip()}")
    else:
        print("   ⚠ Log file not found")
    
    print("\n" + "=" * 70)
    print("✅ Demonstration Complete!")
    print("=" * 70)
    print("\nTo view this information in the web interface:")
    print("1. Start the Flask application: python3 src/app.py")
    print("2. Login as admin (default: username='admin', check .env for password)")
    print("3. Navigate to the Admin page")
    print("4. Scroll to the 'User Login Activity' section")
    print("\n")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
