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
from datetime import datetime

logger = logging.getLogger(__name__)

# Database file location - stored in data directory
DB_DIR = Path(__file__).parent.parent / 'data'
DB_FILE = DB_DIR / 'users.db'

# Log file location - stored in logs directory
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOGIN_LOG_FILE = LOG_DIR / 'user_logins.log'


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


def setup_login_logging():
    """
    Setup file-based logging for user logins.
    
    Creates logs directory if it doesn't exist and configures a file handler
    for login events.
    """
    # Ensure logs directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create a dedicated logger for login events
    login_logger = logging.getLogger('user_login')
    login_logger.setLevel(logging.INFO)
    
    # Check if handler already exists to avoid duplicates
    if not login_logger.handlers:
        # Create file handler
        file_handler = logging.FileHandler(LOGIN_LOG_FILE)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        login_logger.addHandler(file_handler)
    
    return login_logger


def log_user_login(username: str, ip_address: str = None, user_agent: str = None):
    """
    Log a user login event to file.
    
    Args:
        username: Username that logged in
        ip_address: IP address of the user (optional)
        user_agent: User agent string (optional)
    """
    login_logger = setup_login_logging()
    
    log_message = f"User '{username}' logged in"
    if ip_address:
        log_message += f" from IP: {ip_address}"
    if user_agent:
        log_message += f" | User-Agent: {user_agent}"
    
    login_logger.info(log_message)


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
    - last_login_at: Timestamp of the last login (nullable)
    
    Also creates a login_logs table for detailed login history.
    
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login_at TIMESTAMP
            )
        ''')
        
        # Create login_logs table for detailed login history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create index on username for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_username ON users(username)
        ''')
        
        # Create index on login_logs for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_login_logs_user_id ON login_logs(user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_login_logs_login_time ON login_logs(login_time DESC)
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
            
            # Refresh columns list after schema change
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
        
        # Migrate existing tables to add last_login_at column if it doesn't exist
        if 'last_login_at' not in columns:
            logger.info("Adding last_login_at column to existing users table")
            cursor.execute('''
                ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP
            ''')
            conn.commit()
            logger.info("last_login_at column added successfully")
        
        conn.commit()
        logger.info(f"Database initialized successfully at {DB_FILE}")
        
        # Close the connection before calling ensure_default_admin
        # which will create its own connection
        conn.close()
        conn = None
        
        # Ensure default admin user exists
        ensure_default_admin()
        
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


def authenticate_user(username: str, password: str, ip_address: str = None, user_agent: str = None) -> Tuple[bool, Optional[Dict]]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: Username to authenticate
        password: Plain text password to verify
        ip_address: IP address of the user (optional, for logging)
        user_agent: User agent string (optional, for logging)
        
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
            user_id = user['id']
            
            # Update last_login_at timestamp
            cursor.execute('''
                UPDATE users
                SET last_login_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))
            
            # Insert login log entry
            cursor.execute('''
                INSERT INTO login_logs (user_id, username, ip_address, user_agent)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, ip_address, user_agent))
            
            conn.commit()
            
            # Log to file
            log_user_login(username, ip_address, user_agent)
            
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
            SELECT id, username, user_level, division_name, team_name, created_at, updated_at, last_login_at
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
                'updated_at': row['updated_at'],
                'last_login_at': row['last_login_at'] if 'last_login_at' in row else None
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


def ensure_default_admin() -> bool:
    """
    Ensure a default admin user exists in the database.
    
    Creates a default admin user if no admin exists in the database.
    This provides a failsafe login option for administrators.
    
    Default credentials:
        Username: admin
        Password: kurwa
        User Level: admin
    
    Returns:
        bool: True if default admin exists or was created, False on error
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if any admin user exists
        cursor.execute('''
            SELECT COUNT(*) as count FROM users WHERE user_level = 'admin'
        ''')
        result = cursor.fetchone()
        admin_count = result['count'] if result else 0
        
        # If no admin exists, create the default one
        if admin_count == 0:
            logger.info("No admin user found, creating default admin user")
            
            # Create default admin with well-known credentials
            password_hash = generate_password_hash('kurwa')
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, user_level)
                VALUES (?, ?, ?)
            ''', ('admin', password_hash, 'admin'))
            
            conn.commit()
            logger.info("Default admin user created successfully (username: admin)")
            return True
        else:
            logger.debug(f"Admin user(s) already exist (count: {admin_count})")
            return True
        
    except Exception as e:
        logger.error(f"Failed to ensure default admin: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_users_with_login_info() -> List[Dict]:
    """
    Get all users with their last login information.
    
    Returns:
        List[Dict]: List of user dictionaries including last login time
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, user_level, division_name, team_name, 
                   created_at, updated_at, last_login_at
            FROM users
            ORDER BY last_login_at DESC NULLS LAST, username
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
                'updated_at': row['updated_at'],
                'last_login_at': row['last_login_at']
            })
        
        return users
        
    except Exception as e:
        logger.error(f"Error getting users with login info: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_recent_login_logs(limit: int = 50) -> List[Dict]:
    """
    Get recent login logs from the database.
    
    Args:
        limit: Maximum number of login records to return (default: 50)
        
    Returns:
        List[Dict]: List of login log entries
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, username, login_time, ip_address, user_agent
            FROM login_logs
            ORDER BY login_time DESC
            LIMIT ?
        ''', (limit,))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'username': row['username'],
                'login_time': row['login_time'],
                'ip_address': row['ip_address'],
                'user_agent': row['user_agent']
            })
        
        return logs
        
    except Exception as e:
        logger.error(f"Error getting recent login logs: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_login_statistics() -> Dict:
    """
    Get login statistics for the admin dashboard.
    
    Returns:
        Dict: Dictionary with login statistics
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total login count
        cursor.execute('SELECT COUNT(*) as count FROM login_logs')
        total_logins = cursor.fetchone()['count']
        
        # Unique users who have logged in
        cursor.execute('SELECT COUNT(DISTINCT user_id) as count FROM login_logs')
        unique_users = cursor.fetchone()['count']
        
        # Logins in last 24 hours
        cursor.execute('''
            SELECT COUNT(*) as count FROM login_logs
            WHERE login_time >= datetime('now', '-1 day')
        ''')
        logins_24h = cursor.fetchone()['count']
        
        # Logins in last 7 days
        cursor.execute('''
            SELECT COUNT(*) as count FROM login_logs
            WHERE login_time >= datetime('now', '-7 days')
        ''')
        logins_7d = cursor.fetchone()['count']
        
        # Most active user
        cursor.execute('''
            SELECT username, COUNT(*) as login_count
            FROM login_logs
            GROUP BY username
            ORDER BY login_count DESC
            LIMIT 1
        ''')
        most_active_row = cursor.fetchone()
        most_active_user = most_active_row['username'] if most_active_row else None
        most_active_count = most_active_row['login_count'] if most_active_row else 0
        
        return {
            'total_logins': total_logins,
            'unique_users': unique_users,
            'logins_24h': logins_24h,
            'logins_7d': logins_7d,
            'most_active_user': most_active_user,
            'most_active_count': most_active_count
        }
        
    except Exception as e:
        logger.error(f"Error getting login statistics: {e}")
        return {
            'total_logins': 0,
            'unique_users': 0,
            'logins_24h': 0,
            'logins_7d': 0,
            'most_active_user': None,
            'most_active_count': 0
        }
    finally:
        if conn:
            conn.close()


# Initialize database on module import
if __name__ != '__main__':
    # Auto-initialize database when module is imported (unless running as script)
    init_database()
