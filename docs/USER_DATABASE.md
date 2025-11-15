# User Database Documentation

## Overview

The FLBB Statistics application now includes a SQLite database for managing user accounts and preferences. This database supports up to 100 users and stores:

- User credentials (username and securely hashed password)
- User preferences (preferred division and team)
- Account metadata (creation and update timestamps)

## Database Schema

The user database (`data/users.db`) contains a single table:

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| username | TEXT | Unique username (max 50 characters) |
| password_hash | TEXT | Hashed password using werkzeug |
| division_name | TEXT | Preferred division (nullable) |
| team_name | TEXT | Preferred team (nullable) |
| created_at | TIMESTAMP | Account creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

**Index:** `idx_username` on the `username` column for fast lookups

## Password Security

- Passwords are never stored in plain text
- All passwords are hashed using `werkzeug.security.generate_password_hash`
- Password hashing uses the default secure algorithm (pbkdf2:sha256)
- Minimum password length: 6 characters
- Generated passwords include uppercase, lowercase, digits, and special characters

## Password Generation Script

The `scripts/generate_password.py` script provides comprehensive user management functionality.

### Generate a Random Password

```bash
python3 scripts/generate_password.py
```

This generates a 12-character secure random password.

### Generate Password with Custom Length

```bash
python3 scripts/generate_password.py --length 16
```

### Create a New User

```bash
# With auto-generated password
python3 scripts/generate_password.py --create-user john_doe

# With custom password
python3 scripts/generate_password.py --create-user john_doe --password MySecurePass123

# With preferences
python3 scripts/generate_password.py --create-user john_doe \
    --division "U12 - Minimes" \
    --team "BC Dudelange"
```

### List All Users

```bash
python3 scripts/generate_password.py --list-users
```

### Update User Password

```bash
# Generate new password
python3 scripts/generate_password.py --update-password john_doe

# Set specific password
python3 scripts/generate_password.py --update-password john_doe --password NewPass123
```

### Delete a User

```bash
python3 scripts/generate_password.py --delete-user john_doe
```

### Initialize Database

```bash
python3 scripts/generate_password.py --init-db
```

This manually initializes the database (normally done automatically on first import).

## Authentication Flow

### 1. Database Authentication (Primary)

When a user logs in, the system:

1. Checks the SQLite database for the username
2. Verifies the password using werkzeug's `check_password_hash`
3. If successful, loads user preferences into the session
4. Stores the username in the session for preference updates

### 2. Environment Variable Fallback (Legacy)

For backward compatibility, if database authentication fails, the system falls back to checking environment variables:

- `USER_USERNAME` - Single predefined username
- `USER_PASSWORD` - Single predefined password

This allows existing deployments to continue working without changes.

## User Preferences

### Automatic Loading

When a user logs in with database credentials:
- Their preferred division and team are automatically loaded into the session
- These preferences are immediately applied to the application

### Automatic Saving

When a user updates their preferences:
- Changes are saved to both the session and the database
- The database is updated asynchronously
- If the update fails, a warning is logged but the user experience is not affected

### Session Management

The username is stored in the session (`session['username']`) to:
- Enable preference updates to the correct database record
- Identify the currently logged-in user
- Persist preferences across page loads

## Database File Location

- **Path:** `data/users.db`
- **Format:** SQLite 3
- **Mode:** WAL (Write-Ahead Logging) for better concurrent access
- **Gitignored:** Yes (to protect user data)

## Security Considerations

### Password Requirements

- Minimum length: 6 characters
- No maximum length enforced
- Best practice: Use the password generator for strong passwords

### Database Security

- The database file should be protected with appropriate file permissions
- In production, ensure `data/users.db` is readable/writable only by the application user
- Never commit the database file to version control (included in `.gitignore`)

### Connection Handling

- All database connections use a 10-second timeout to prevent locks
- WAL mode is enabled for better concurrent access
- All connections are properly closed using try-finally blocks

## User Limit

The system is designed for up to 100 users. The password generation script enforces this limit:

```python
user_count = get_user_count()
if user_count >= 100:
    print("✗ Error: Maximum number of users (100) reached")
    sys.exit(1)
```

Note: The database itself does not enforce this limit; it's a soft limit in the management script.

## API Reference

### Database Functions

```python
from src.user_database import (
    create_user,
    authenticate_user,
    get_user_preferences,
    update_user_preferences,
    update_user_password,
    delete_user,
    list_users,
    get_user_count,
    init_database
)
```

#### create_user(username, password, division_name=None, team_name=None)

Create a new user in the database.

**Returns:** `Tuple[bool, str]` - (Success status, Message or error description)

#### authenticate_user(username, password)

Authenticate a user with username and password.

**Returns:** `Tuple[bool, Optional[Dict]]` - (Success status, User data dict if successful)

#### get_user_preferences(username)

Get user preferences by username.

**Returns:** `Optional[Dict]` - User preferences dict or None if not found

#### update_user_preferences(username, division_name=None, team_name=None)

Update user preferences.

**Returns:** `Tuple[bool, str]` - (Success status, Message or error description)

#### update_user_password(username, new_password)

Update user password.

**Returns:** `Tuple[bool, str]` - (Success status, Message or error description)

#### delete_user(username)

Delete a user from the database.

**Returns:** `Tuple[bool, str]` - (Success status, Message or error description)

#### list_users()

List all users in the database (without password hashes).

**Returns:** `List[Dict]` - List of user dictionaries

#### get_user_count()

Get the total number of users in the database.

**Returns:** `int` - Number of users

#### init_database()

Initialize the user database with the required schema.

**Returns:** `bool` - True if successful, False otherwise

## Testing

### Unit Tests

Run the database unit tests:

```bash
python3 tests/test_user_database.py
```

This tests all database functions including:
- Database initialization
- User creation and validation
- Authentication
- Preference management
- Password updates
- User deletion
- User listing and counting
- 100-user limit

### Integration Tests

Run the Flask integration tests:

```bash
python3 tests/test_flask_user_database.py
```

This tests the integration with Flask including:
- Database authentication in Flask routes
- Preference loading from database
- Preference saving to database
- Session management
- Environment variable fallback

## Migration Guide

### From Environment Variables to Database

If you're currently using `USER_USERNAME` and `USER_PASSWORD` environment variables:

1. **Keep the environment variables** (for backward compatibility)
2. **Create database users** for your users:
   ```bash
   python3 scripts/generate_password.py --create-user <username>
   ```
3. **Distribute credentials** to your users
4. **Monitor usage** to ensure smooth transition
5. **Optional:** Remove environment variables after all users have migrated

### Backup and Restore

To backup the user database:

```bash
cp data/users.db data/users.db.backup
```

To restore:

```bash
cp data/users.db.backup data/users.db
```

For production, consider regular automated backups of the `data/users.db` file.

## Troubleshooting

### Database Lock Errors

If you encounter "database is locked" errors:

1. Check that no other processes are accessing the database
2. Ensure WAL mode is enabled (automatic on module import)
3. Verify the database file has proper permissions

### User Cannot Login

1. Verify the user exists:
   ```bash
   python3 scripts/generate_password.py --list-users
   ```
2. Try resetting the password:
   ```bash
   python3 scripts/generate_password.py --update-password <username>
   ```
3. Check application logs for authentication errors

### Preferences Not Saving

1. Verify the user is logged in with a database account (has `session['username']`)
2. Check write permissions on `data/users.db`
3. Review application logs for database errors

## Best Practices

1. **Use the password generator** for all new users to ensure strong passwords
2. **Keep the database backed up** regularly
3. **Don't commit the database** to version control
4. **Set proper file permissions** on the database file in production
5. **Monitor user count** to stay within the 100-user limit
6. **Log authentication failures** for security monitoring
7. **Regularly review user accounts** and remove inactive users
