"""
Authentication and authorization module for FLBB Statistics application.

This module implements a simple username/password authentication system with
three authorization levels:
1. Guest (unauthenticated) - Access to Standings and Fixtures only
2. Logged-in (authenticated) - Access to all pages except Admin
3. Admin (authenticated admin) - Access to all pages including Admin
"""

import os
import hashlib
from functools import wraps
from flask import session, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user


# Authorization levels
AUTH_LEVEL_GUEST = 'guest'
AUTH_LEVEL_USER = 'user'
AUTH_LEVEL_ADMIN = 'admin'

# Pages accessible to each authorization level
GUEST_PAGES = ['index', 'standings', 'fixtures']
USER_PAGES = GUEST_PAGES + [
    'statistics', 'team_stats', 'team_detail', 'player_stats', 'player_detail',
    'referee_stats', 'referee_detail', 'referee_performance_index',
    'deeper_analysis', 'game_details_search', 'game_detail',
    'preferences', 'api_player_hover', 'api_team_hover', 'api_referee_hover', 'api_game_hover'
]
ADMIN_PAGES = USER_PAGES + ['admin', 'import_season_data']


class User(UserMixin):
    """Simple user class for Flask-Login"""
    def __init__(self, username, is_admin=False):
        self.id = username
        self.username = username
        self.is_admin = is_admin
    
    def get_auth_level(self):
        """Get the authorization level for this user"""
        if self.is_admin:
            return AUTH_LEVEL_ADMIN
        return AUTH_LEVEL_USER


def hash_password(password):
    """
    Hash a password using SHA-256.
    
    Note: SHA-256 is used for simplicity and compatibility. For production use,
    consider using bcrypt, scrypt, or Argon2 which are specifically designed
    for password hashing and include built-in salt and iteration counts to
    protect against brute force attacks.
    
    Example with bcrypt:
        import bcrypt
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_credentials(username, password):
    """
    Verify username and password against environment variables.
    
    Returns:
        tuple: (is_valid, is_admin) - whether credentials are valid and if user is admin
    """
    # Get credentials from environment variables
    # Format: USERNAME:PASSWORD_HASH for regular users
    #         ADMIN_USERNAME:ADMIN_PASSWORD_HASH for admin
    
    # Check admin credentials
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password_hash = os.environ.get('ADMIN_PASSWORD_HASH', '')
    
    # If no admin password is set, create a default hash for 'admin'
    if not admin_password_hash:
        admin_password_hash = hash_password('admin')
    
    if username == admin_username and hash_password(password) == admin_password_hash:
        return True, True
    
    # Check regular user credentials
    user_credentials = os.environ.get('USER_CREDENTIALS', '')
    if user_credentials:
        # Format: "username1:hash1,username2:hash2,..."
        for cred in user_credentials.split(','):
            if ':' in cred:
                stored_username, stored_hash = cred.strip().split(':', 1)
                if username == stored_username and hash_password(password) == stored_hash:
                    return True, False
    
    return False, False


def init_login_manager(app):
    """Initialize Flask-Login for the application"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID (username)"""
        # Check if this is an admin user
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        if user_id == admin_username:
            return User(user_id, is_admin=True)
        return User(user_id, is_admin=False)
    
    return login_manager


def get_user_auth_level():
    """Get the current user's authorization level"""
    if current_user.is_authenticated:
        return current_user.get_auth_level()
    return AUTH_LEVEL_GUEST


def requires_auth_level(level):
    """
    Decorator to require a specific authorization level for a route.
    
    Args:
        level: One of AUTH_LEVEL_GUEST, AUTH_LEVEL_USER, or AUTH_LEVEL_ADMIN
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_level = get_user_auth_level()
            
            # Check if user has required permission
            if level == AUTH_LEVEL_ADMIN:
                if not current_user.is_authenticated or not current_user.is_admin:
                    flash('Admin access required.', 'error')
                    return redirect(url_for('login', next=request.url))
            elif level == AUTH_LEVEL_USER:
                if not current_user.is_authenticated:
                    flash('Please log in to access this page.', 'error')
                    return redirect(url_for('login', next=request.url))
            # GUEST level requires no authentication
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def can_access_endpoint(endpoint_name):
    """
    Check if the current user can access a given endpoint.
    
    Args:
        endpoint_name: The Flask endpoint name
        
    Returns:
        bool: True if user can access, False otherwise
    """
    if not endpoint_name:
        return True
    
    # Get current user's authorization level
    current_level = get_user_auth_level()
    
    # Check access based on level
    if current_level == AUTH_LEVEL_ADMIN:
        return True
    elif current_level == AUTH_LEVEL_USER:
        return endpoint_name in USER_PAGES
    else:  # GUEST
        return endpoint_name in GUEST_PAGES
