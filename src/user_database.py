"""
User database module for managing user preferences in SQLite.

This module provides functionality for:
- Creating and initializing the user database
- Managing user accounts (create, read, update, delete)
- Storing user preferences (division, team)
- Secure password hashing and verification

Database is designed for up to 100 users.
"""

import sqlite3
import os
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

# Database file location - stored in data directory
DB_DIR = Path(__file__).parent.parent / 'data'
DB_FILE = DB_DIR / 'users.db'


def get_db_connection():
    """
    Get a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection with Row factory enabled
    """
    # Ensure data directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # Use a timeout to handle concurrent access
    conn = sqlite3.connect(str(DB_FILE), timeout=10.0)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    # Enable WAL mode for better concurrent access
    conn.execute('PRAGMA journal_mode=WAL')
    
    return conn


def init_database():
    """
    Initialize the user database with the required schema.
    
    Creates the users table if it doesn't exist with the following columns:
    - id: Primary key (auto-increment)
    - username: Unique username (max 50 characters)
    - password_hash: Hashed password (using werkzeug)
    - user_level: Authorization level (guest/user/admin), defaults to 'user'
    - division_name: Preferred division (nullable)
    - team_name: Preferred team (nullable)
    - created_at: Timestamp when user was created
    - updated_at: Timestamp when user was last updated
    
    Returns:
        bool: True if successful, False otherwise
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                user_level TEXT DEFAULT 'user' CHECK(user_level IN ('guest', 'user', 'admin')),
                division_name TEXT,
                team_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index on username for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_username ON users(username)
        ''')
        
        # Migrate existing tables to add user_level column if it doesn't exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'user_level' not in columns:
            logger.info("Adding user_level column to existing users table")
            cursor.execute('''
                ALTER TABLE users ADD COLUMN user_level TEXT DEFAULT 'user' CHECK(user_level IN ('guest', 'user', 'admin'))
            ''')
            conn.commit()
            logger.info("user_level column added successfully")
        
        conn.commit()
        logger.info(f"Database initialized successfully at {DB_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False
    finally:
        if conn:
            conn.close()


def create_user(username: str, password: str, user_level: str = 'user',
                division_name: Optional[str] = None, team_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Create a new user in the database.
    
    Args:
        username: Unique username (max 50 characters)
        password: Plain text password (will be hashed)
        user_level: Authorization level ('guest', 'user', or 'admin'), defaults to 'user'
        division_name: Optional preferred division
        team_name: Optional preferred team
        
    Returns:
        Tuple[bool, str]: (Success status, Message or error description)
    """
    if not username or len(username) > 50:
        return False, "Username must be between 1 and 50 characters"
    
    if not password or len(password) < 5:
        return False, "Password must be at least 5 characters"
    
    if user_level not in ('guest', 'user', 'admin'):
        return False, "User level must be 'guest', 'user', or 'admin'"
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        # Insert user
        cursor.execute('''
            INSERT INTO users (username, password_hash, user_level, division_name, team_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password_hash, user_level, division_name, team_name))
        
        conn.commit()
        logger.info(f"User created successfully: {username} with level {user_level}")
        return True, f"User '{username}' created successfully with level '{user_level}'"
        
    except sqlite3.IntegrityError:
        return False, f"Username '{username}' already exists"
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return False, f"Database error: {str(e)}"
    finally:
        if conn:
            conn.close()


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[Dict]]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: Username to authenticate
        password: Plain text password to verify
        
    Returns:
        Tuple[bool, Optional[Dict]]: (Success status, User data dict if successful)
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user by username
        cursor.execute('''
            SELECT id, username, password_hash, user_level, division_name, team_name
            FROM users
            WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        
        if not user:
            return False, None
        
        # Verify password
        if check_password_hash(user['password_hash'], password):
            # Return user data (without password hash)
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'user_level': user['user_level'] if user['user_level'] else 'user',
                'division_name': user['division_name'],
                'team_name': user['team_name']
            }
            return True, user_data
        else:
            return False, None
            
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False, None
    finally:
        if conn:
            conn.close()


def get_user_preferences(username: str) -> Optional[Dict]:
    """
    Get user preferences by username.
    
    Args:
        username: Username to look up
        
    Returns:
        Optional[Dict]: User preferences dict or None if not found
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, user_level, division_name, team_name
            FROM users
            WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        
        if user:
            return {
                'username': user['username'],
                'user_level': user['user_level'] if user['user_level'] else 'user',
                'division_name': user['division_name'],
                'team_name': user['team_name']
            }
        return None
        
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        return None
    finally:
        if conn:
            conn.close()


def update_user_preferences(username: str, division_name: Optional[str] = None, 
                           team_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Update user preferences.
    
    Args:
        username: Username to update
        division_name: New preferred division (or None to keep existing)
        team_name: New preferred team (or None to keep existing)
        
    Returns:
        Tuple[bool, str]: (Success status, Message or error description)
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build update query based on provided parameters
        updates = []
        params = []
        
        if division_name is not None:
            updates.append("division_name = ?")
            params.append(division_name)
        
        if team_name is not None:
            updates.append("team_name = ?")
            params.append(team_name)
        
        if not updates:
            return True, "No changes to update"
        
        # Always update the updated_at timestamp
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(username)
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE username = ?"
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            return False, f"User '{username}' not found"
        
        conn.commit()
        logger.info(f"Preferences updated for user: {username}")
        return True, "Preferences updated successfully"
        
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        return False, f"Database error: {str(e)}"
    finally:
        if conn:
            conn.close()


def update_user_level(username: str, user_level: str) -> Tuple[bool, str]:
    """
    Update user authorization level.
    
    Args:
        username: Username to update
        user_level: New authorization level ('guest', 'user', or 'admin')
        
    Returns:
        Tuple[bool, str]: (Success status, Message or error description)
    """
    if user_level not in ('guest', 'user', 'admin'):
        return False, "User level must be 'guest', 'user', or 'admin'"
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET user_level = ?, updated_at = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (user_level, username))
        
        if cursor.rowcount == 0:
            return False, f"User '{username}' not found"
        
        conn.commit()
        logger.info(f"User level updated for user: {username} to {user_level}")
        return True, f"User level updated successfully to '{user_level}'"
        
    except Exception as e:
        logger.error(f"Error updating user level: {e}")
        return False, f"Database error: {str(e)}"
    finally:
        if conn:
            conn.close()


def update_user_password(username: str, new_password: str) -> Tuple[bool, str]:
    """
    Update user password.
    
    Args:
        username: Username to update
        new_password: New plain text password (will be hashed)
        
    Returns:
        Tuple[bool, str]: (Success status, Message or error description)
    """
    if not new_password or len(new_password) < 5:
        return False, "Password must be at least 5 characters"
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hash the new password
        password_hash = generate_password_hash(new_password)
        
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (password_hash, username))
        
        if cursor.rowcount == 0:
            return False, f"User '{username}' not found"
        
        conn.commit()
        logger.info(f"Password updated for user: {username}")
        return True, "Password updated successfully"
        
    except Exception as e:
        logger.error(f"Error updating password: {e}")
        return False, f"Database error: {str(e)}"
    finally:
        if conn:
            conn.close()


def delete_user(username: str) -> Tuple[bool, str]:
    """
    Delete a user from the database.
    
    Args:
        username: Username to delete
        
    Returns:
        Tuple[bool, str]: (Success status, Message or error description)
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        
        if cursor.rowcount == 0:
            return False, f"User '{username}' not found"
        
        conn.commit()
        logger.info(f"User deleted: {username}")
        return True, f"User '{username}' deleted successfully"
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return False, f"Database error: {str(e)}"
    finally:
        if conn:
            conn.close()


def list_users() -> List[Dict]:
    """
    List all users in the database (without password hashes).
    
    Returns:
        List[Dict]: List of user dictionaries
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, user_level, division_name, team_name, created_at, updated_at
            FROM users
            ORDER BY username
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row['id'],
                'username': row['username'],
                'user_level': row['user_level'] if row['user_level'] else 'user',
                'division_name': row['division_name'],
                'team_name': row['team_name'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return users
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_user_count() -> int:
    """
    Get the total number of users in the database.
    
    Returns:
        int: Number of users
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM users')
        result = cursor.fetchone()
        
        return result['count'] if result else 0
        
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        return 0
    finally:
        if conn:
            conn.close()


# Initialize database on module import
if __name__ != '__main__':
    # Auto-initialize database when module is imported (unless running as script)
    init_database()
