# Authentication and Authorization System

The FLBB Statistics application implements a 3-level authorization system to control access to different features of the application.

## Authorization Levels

### 1. Guest (Unauthenticated)
Guests can access:
- **Home** - Main landing page with overview of all features
- **Standings** - Division standings and team rankings
- **Fixtures** - Game schedules and fixture matrix

### 2. Logged-in User (Authenticated, Non-Admin)
Logged-in users can access all pages except Admin:
- All guest-accessible pages
- **Game Stats** - Comprehensive game statistics
- **Player Stats** - Individual player performance analysis
- **Player Detail** - Detailed player search and statistics
- **Team Stats** - Team performance analysis
- **Team Detail** - Detailed team search and statistics
- **Game Details** - Detailed game search and information
- **Referee Stats** - Referee performance data
- **Referee Detail** - Detailed referee search and statistics
- **Referee Performance Index** - Referee RPI rankings
- **Deep Analysis** - Advanced analytics and insights
- **Preferences** - User preferences and settings

### 3. Admin (Authenticated Admin User)
Admins can access all pages including:
- All user-accessible pages
- **Admin** - Administrative tools, data statistics, and season management

## Setup

### 1. Install Dependencies

The authentication system uses Flask-Login for session management. Install with:

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

Authentication credentials are configured via environment variables.

#### Default Admin Credentials

If no environment variables are set, the default admin credentials are:
- **Username:** `admin`
- **Password:** `admin`

⚠️ **Important:** Change these credentials in production!

#### Setting Custom Admin Credentials

1. Generate a password hash:
```python
python3 -c "import hashlib; print(hashlib.sha256('your_password'.encode()).hexdigest())"
```

2. Set environment variables:
```bash
export ADMIN_USERNAME=youradmin
export ADMIN_PASSWORD_HASH=<hash_from_step_1>
```

#### Adding Regular Users

1. Generate password hashes for each user:
```python
python3 -c "import hashlib; print(hashlib.sha256('user1pass'.encode()).hexdigest())"
python3 -c "import hashlib; print(hashlib.sha256('user2pass'.encode()).hexdigest())"
```

2. Set the USER_CREDENTIALS environment variable:
```bash
export USER_CREDENTIALS="user1:hash1,user2:hash2"
```

Format: `username1:hash1,username2:hash2,...`

#### Session Secret Key

For production, set a secure secret key:

```bash
# Generate a secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Set it as an environment variable
export SECRET_KEY=<generated_key>
```

### 3. Environment Variables Summary

Add these to your `.env` file or set them in your deployment environment:

```bash
# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<sha256_hash>

# Regular user credentials (comma-separated)
USER_CREDENTIALS=user1:<hash1>,user2:<hash2>

# Session secret key (required for production)
SECRET_KEY=<random_hex_string>
```

## Usage

### Logging In

1. Navigate to the login page by clicking "🔑 Login" in the top-right corner
2. Enter your username and password
3. Click "Login"

Upon successful login:
- You'll be redirected to the page you were trying to access (or home)
- Your username will appear in the top-right corner
- Admin users will see "(Admin)" next to their username
- A "🚪 Logout" button will replace the "🔑 Login" button
- The navigation menu will show all accessible pages

### Logging Out

Click the "🚪 Logout" button in the top-right corner to log out.

### Access Control

The system automatically:
- Shows only accessible pages in the navigation menu
- Redirects unauthenticated users to the login page when accessing protected pages
- Displays appropriate error messages for unauthorized access attempts

## Security Considerations

1. **Change Default Credentials:** Always change the default admin credentials in production
2. **Use Strong Passwords:** Enforce strong password policies for all users
3. **Secure Password Storage:** Passwords are hashed using SHA-256 (consider using stronger algorithms like bcrypt for production)
4. **HTTPS:** Always use HTTPS in production to protect credentials in transit
5. **Session Management:** Set a secure SECRET_KEY for session encryption
6. **Environment Variables:** Never commit credentials to version control; use environment variables

## Testing

Run the authorization tests to verify the system works correctly:

```bash
python3 tests/test_authorization.py
```

Expected output:
```
============================================================
FLBB Statistics - Authorization Tests
============================================================
Testing password hashing...
✓ Password hashing works correctly

Testing credential verification...
✓ Admin authentication works
✓ Admin authentication rejects wrong password
✓ User1 authentication works
✓ User2 authentication works
✓ User authentication rejects wrong password
✓ Non-existent user authentication fails

Testing User object...
✓ Regular user object works correctly
✓ Admin user object works correctly

Testing access control...
  Testing guest access...
  ✓ Guest pages configured correctly
  ✓ User pages configured correctly
  ✓ Admin pages configured correctly

Testing default admin credentials...
✓ Default admin credentials work

============================================================
✅ ALL TESTS PASSED!
============================================================
```

## Implementation Details

The authentication system is implemented in `src/auth.py` and integrated into `src/app.py`:

- **Authentication Module:** `src/auth.py`
  - User class for Flask-Login
  - Credential verification functions
  - Authorization decorators
  - Access control helpers

- **Application Integration:** `src/app.py`
  - Flask-Login initialization
  - Login and logout routes
  - Route protection with decorators
  - Context processors for templates

- **Templates:**
  - `templates/login.html` - Login page
  - `templates/base.html` - Updated to show/hide navigation based on authorization level

## Troubleshooting

### Cannot log in with default credentials

Make sure no environment variables are overriding the defaults:
```bash
unset ADMIN_USERNAME
unset ADMIN_PASSWORD_HASH
unset USER_CREDENTIALS
```

### "Please log in to access this page" appears when accessing any page

Check that:
1. You're logged in (check for username in top-right corner)
2. Your user account has the required authorization level
3. The session hasn't expired (try logging in again)

### Admin page not accessible even when logged in as admin

Verify that:
1. The ADMIN_PASSWORD_HASH matches your username
2. You're logged in with the admin account
3. The admin username matches the ADMIN_USERNAME environment variable

## Future Enhancements

Potential improvements for the authentication system:

1. **User Database:** Store users in a database instead of environment variables
2. **Password Strength:** Use bcrypt or Argon2 instead of SHA-256
3. **Password Reset:** Implement password reset functionality
4. **User Registration:** Allow users to self-register
5. **Role-Based Access Control:** More granular permissions system
6. **Session Timeout:** Configure session timeouts
7. **Audit Logging:** Log authentication and authorization events
8. **Two-Factor Authentication:** Add 2FA support for additional security
