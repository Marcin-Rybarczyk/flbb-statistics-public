#!/usr/bin/env python3
"""
Example usage of the user database system.

This script demonstrates:
1. Creating users with the password generation script
2. Using the database API programmatically
3. Common user management tasks
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.user_database import (
    create_user, authenticate_user, get_user_preferences,
    update_user_preferences, list_users, delete_user, get_user_count
)


def demo_user_management():
    """Demonstrate user management functionality"""
    
    print("=" * 70)
    print("FLBB Statistics User Database - Example Usage")
    print("=" * 70)
    
    # Example 1: Create users
    print("\n📝 Example 1: Creating Users")
    print("-" * 70)
    
    users_to_create = [
        {
            'username': 'coach_john',
            'password': 'SecurePass123!',
            'division': 'U12 - Minimes',
            'team': 'BC Dudelange'
        },
        {
            'username': 'fan_mary',
            'password': 'Basketball2024',
            'division': 'Total League',
            'team': 'Racing Luxembourg'
        }
    ]
    
    for user in users_to_create:
        # Clean up if exists (for demo purposes)
        delete_user(user['username'])
        
        success, msg = create_user(
            username=user['username'],
            password=user['password'],
            division_name=user['division'],
            team_name=user['team']
        )
        
        if success:
            print(f"✓ Created: {user['username']}")
            print(f"  Division: {user['division']}")
            print(f"  Team: {user['team']}")
        else:
            print(f"✗ Failed to create {user['username']}: {msg}")
    
    # Example 2: List users
    print("\n📋 Example 2: Listing All Users")
    print("-" * 70)
    
    users = list_users()
    print(f"Total users: {get_user_count()}\n")
    
    for user in users:
        print(f"• {user['username']}")
        print(f"  Division: {user['division_name'] or 'Not set'}")
        print(f"  Team: {user['team_name'] or 'Not set'}")
        print(f"  Created: {user['created_at'][:10]}")
        print()
    
    # Example 3: Authenticate a user
    print("\n🔐 Example 3: User Authentication")
    print("-" * 70)
    
    username = 'coach_john'
    password = 'SecurePass123!'
    
    print(f"Attempting to authenticate: {username}")
    success, user_data = authenticate_user(username, password)
    
    if success:
        print("✓ Authentication successful!")
        print(f"  User ID: {user_data['id']}")
        print(f"  Username: {user_data['username']}")
        print(f"  Division: {user_data['division_name']}")
        print(f"  Team: {user_data['team_name']}")
    else:
        print("✗ Authentication failed")
    
    # Test wrong password
    print(f"\nAttempting with wrong password...")
    success, user_data = authenticate_user(username, 'WrongPassword')
    
    if success:
        print("✗ Should have failed!")
    else:
        print("✓ Correctly rejected invalid password")
    
    # Example 4: Update preferences
    print("\n⚙️  Example 4: Updating User Preferences")
    print("-" * 70)
    
    username = 'fan_mary'
    new_division = 'U14 - Cadets'
    new_team = 'Arantia'
    
    print(f"Updating preferences for: {username}")
    print(f"  New division: {new_division}")
    print(f"  New team: {new_team}")
    
    success, msg = update_user_preferences(
        username=username,
        division_name=new_division,
        team_name=new_team
    )
    
    if success:
        print(f"✓ {msg}")
        
        # Verify the update
        prefs = get_user_preferences(username)
        print(f"\nVerified preferences:")
        print(f"  Division: {prefs['division_name']}")
        print(f"  Team: {prefs['team_name']}")
    else:
        print(f"✗ {msg}")
    
    # Example 5: Using in a Flask application context
    print("\n🌐 Example 5: Flask Integration Pattern")
    print("-" * 70)
    
    print("""
In your Flask route, you would use it like this:

```python
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Try database authentication
    success, user_data = authenticate_user(username, password)
    
    if success:
        # Store in session
        session['user_authenticated'] = True
        session['username'] = user_data['username']
        session['preferred_division'] = user_data['division_name']
        session['preferred_team'] = user_data['team_name']
        
        return redirect(url_for('index'))
    else:
        return render_template('login.html', error='Invalid credentials')

@app.route('/preferences', methods=['POST'])
def update_prefs():
    if not session.get('user_authenticated'):
        return redirect(url_for('login'))
    
    username = session.get('username')
    division = request.form.get('division')
    team = request.form.get('team')
    
    # Update database
    update_user_preferences(username, division, team)
    
    # Update session
    session['preferred_division'] = division
    session['preferred_team'] = team
    
    return redirect(url_for('preferences'))
```
    """)
    
    # Clean up demo users
    print("\n🧹 Cleaning up demo users...")
    print("-" * 70)
    
    for user in users_to_create:
        success, msg = delete_user(user['username'])
        if success:
            print(f"✓ Deleted: {user['username']}")
    
    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)


def demo_command_line_tools():
    """Demonstrate command-line tools"""
    
    print("\n" + "=" * 70)
    print("Command-Line Tools Examples")
    print("=" * 70)
    
    print("""
1. Generate a random password:
   $ python3 scripts/generate_password.py

2. Generate a longer password (16 characters):
   $ python3 scripts/generate_password.py --length 16

3. Create a user with auto-generated password:
   $ python3 scripts/generate_password.py --create-user john_coach

4. Create a user with specific password and preferences:
   $ python3 scripts/generate_password.py \\
       --create-user john_coach \\
       --password MySecurePass123 \\
       --division "U12 - Minimes" \\
       --team "BC Dudelange"

5. List all users:
   $ python3 scripts/generate_password.py --list-users

6. Update a user's password:
   $ python3 scripts/generate_password.py --update-password john_coach

7. Delete a user:
   $ python3 scripts/generate_password.py --delete-user john_coach

8. Initialize the database (usually automatic):
   $ python3 scripts/generate_password.py --init-db
    """)


if __name__ == '__main__':
    print("\n")
    demo_user_management()
    print("\n")
    demo_command_line_tools()
    print("\n")
