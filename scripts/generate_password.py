#!/usr/bin/env python3
"""
Password generation script for FLBB Statistics user management.

This script provides utilities to:
1. Generate secure random passwords
2. Create new users with generated passwords
3. Manage user database

Usage:
    # Generate a random password
    python3 scripts/generate_password.py

    # Generate a password with specific length
    python3 scripts/generate_password.py --length 16

    # Create a user with generated password
    python3 scripts/generate_password.py --create-user username

    # Create a user with custom password
    python3 scripts/generate_password.py --create-user username --password mypass

    # List all users
    python3 scripts/generate_password.py --list-users

    # Delete a user
    python3 scripts/generate_password.py --delete-user username
"""

import sys
import os
import secrets
import string
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.user_database import (
    create_user, delete_user, list_users, get_user_count,
    update_user_password, init_database
)


def generate_secure_password(length: int = 12) -> str:
    """
    Generate a cryptographically secure random password.
    
    The password includes:
    - Uppercase letters
    - Lowercase letters
    - Digits
    - Special characters (!@#$%^&*()_+-=)
    
    Args:
        length: Password length (minimum 8, default 12)
        
    Returns:
        str: Generated password
    """
    if length < 8:
        length = 8
    
    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*()_+-="
    
    # Combine all characters
    all_chars = uppercase + lowercase + digits + special
    
    # Ensure password has at least one of each type
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Fill remaining length with random characters
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle the password characters
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    
    return ''.join(password_list)


def print_user_table(users):
    """Print users in a formatted table."""
    if not users:
        print("No users found in database.")
        return
    
    print("\n" + "=" * 100)
    print(f"{'ID':<5} {'Username':<20} {'Division':<25} {'Team':<25} {'Created':<15}")
    print("=" * 100)
    
    for user in users:
        user_id = user.get('id', '')
        username = user.get('username', '')[:20]
        division = (user.get('division_name') or '')[:25]
        team = (user.get('team_name') or '')[:25]
        created = user.get('created_at', '')[:10]
        
        print(f"{user_id:<5} {username:<20} {division:<25} {team:<25} {created:<15}")
    
    print("=" * 100)
    print(f"Total users: {len(users)}\n")


def main():
    """Main entry point for the password generation script."""
    parser = argparse.ArgumentParser(
        description='Password generation and user management for FLBB Statistics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Password generation options
    parser.add_argument('--length', type=int, default=12,
                       help='Password length (minimum 8, default 12)')
    
    # User management options
    parser.add_argument('--create-user', metavar='USERNAME',
                       help='Create a new user with specified username')
    parser.add_argument('--password', metavar='PASSWORD',
                       help='Specify password for user creation (otherwise generated)')
    parser.add_argument('--division', metavar='DIVISION',
                       help='Set preferred division for new user')
    parser.add_argument('--team', metavar='TEAM',
                       help='Set preferred team for new user')
    
    parser.add_argument('--list-users', action='store_true',
                       help='List all users in the database')
    parser.add_argument('--delete-user', metavar='USERNAME',
                       help='Delete a user from the database')
    parser.add_argument('--update-password', metavar='USERNAME',
                       help='Update password for an existing user')
    
    parser.add_argument('--init-db', action='store_true',
                       help='Initialize the database (creates table if not exists)')
    
    args = parser.parse_args()
    
    # Initialize database if requested
    if args.init_db:
        print("Initializing database...")
        if init_database():
            print("✓ Database initialized successfully")
        else:
            print("✗ Failed to initialize database")
            sys.exit(1)
        return
    
    # List users
    if args.list_users:
        users = list_users()
        print_user_table(users)
        return
    
    # Delete user
    if args.delete_user:
        username = args.delete_user
        print(f"Deleting user '{username}'...")
        success, message = delete_user(username)
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            sys.exit(1)
        return
    
    # Update password
    if args.update_password:
        username = args.update_password
        
        if args.password:
            new_password = args.password
        else:
            new_password = generate_secure_password(args.length)
            print(f"Generated password: {new_password}")
        
        print(f"Updating password for user '{username}'...")
        success, message = update_user_password(username, new_password)
        if success:
            print(f"✓ {message}")
            if not args.password:
                print(f"\nNew password: {new_password}")
                print("Please save this password - it cannot be recovered!")
        else:
            print(f"✗ {message}")
            sys.exit(1)
        return
    
    # Create user
    if args.create_user:
        username = args.create_user
        
        # Check user limit (100 users)
        user_count = get_user_count()
        if user_count >= 100:
            print("✗ Error: Maximum number of users (100) reached")
            sys.exit(1)
        
        # Use provided password or generate one
        if args.password:
            password = args.password
            print(f"Creating user '{username}' with provided password...")
        else:
            password = generate_secure_password(args.length)
            print(f"Creating user '{username}' with generated password...")
            print(f"Generated password: {password}")
        
        # Create the user
        success, message = create_user(
            username=username,
            password=password,
            division_name=args.division,
            team_name=args.team
        )
        
        if success:
            print(f"✓ {message}")
            if not args.password:
                print(f"\nUsername: {username}")
                print(f"Password: {password}")
                print("\nPlease save these credentials - the password cannot be recovered!")
            
            if args.division:
                print(f"Preferred division: {args.division}")
            if args.team:
                print(f"Preferred team: {args.team}")
        else:
            print(f"✗ {message}")
            sys.exit(1)
        return
    
    # Default: just generate a password
    password = generate_secure_password(args.length)
    print(f"Generated secure password ({args.length} characters):")
    print(password)
    print("\nTo create a user with this password, use:")
    print(f"python3 scripts/generate_password.py --create-user <username> --password {password}")


if __name__ == '__main__':
    main()
