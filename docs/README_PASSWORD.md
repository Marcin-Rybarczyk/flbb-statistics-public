# Password Generation and User Management Script

## Overview

The `generate_password.py` script provides comprehensive user management for the FLBB Statistics application. It allows administrators to create, manage, and delete user accounts with secure password generation.

## Features

- 🔐 **Secure Password Generation** - Cryptographically secure random passwords
- 👤 **User Management** - Create, update, and delete user accounts
- 📊 **User Listing** - View all registered users
- ⚙️ **Preference Setting** - Set user preferences during account creation
- 🛡️ **Security** - All passwords are hashed using werkzeug's secure hash functions

## Quick Start

### Generate a Password

```bash
# Generate a 12-character password (default)
python3 scripts/generate_password.py

# Generate a 16-character password
python3 scripts/generate_password.py --length 16
```

Output:
```
Generated secure password (12 characters):
kDi7I&S1Dt@i

To create a user with this password, use:
python3 scripts/generate_password.py --create-user <username> --password kDi7I&S1Dt@i
```

### Create a User

```bash
# Create with auto-generated password
python3 scripts/generate_password.py --create-user john_coach

# Create with custom password
python3 scripts/generate_password.py --create-user john_coach --password MyPass123

# Create with preferences
python3 scripts/generate_password.py --create-user john_coach \
    --password MyPass123 \
    --division "U12 - Minimes" \
    --team "BC Dudelange"
```

### List Users

```bash
python3 scripts/generate_password.py --list-users
```

Output:
```
====================================================================================================
ID    Username             Division                  Team                      Created        
====================================================================================================
1     coach_john           U12 - Minimes             BC Dudelange              2025-11-15     
2     fan_mary             Total League              Racing Luxembourg         2025-11-15     
====================================================================================================
Total users: 2
```

### Update Password

```bash
# Generate new password
python3 scripts/generate_password.py --update-password john_coach

# Set specific password
python3 scripts/generate_password.py --update-password john_coach --password NewPass123
```

### Delete User

```bash
python3 scripts/generate_password.py --delete-user john_coach
```

## Command Reference

### Password Generation Options

| Option | Description | Default |
|--------|-------------|---------|
| `--length LENGTH` | Password length (minimum 8) | 12 |

### User Management Options

| Option | Description |
|--------|-------------|
| `--create-user USERNAME` | Create a new user |
| `--password PASSWORD` | Specify password (otherwise generated) |
| `--division DIVISION` | Set preferred division for new user |
| `--team TEAM` | Set preferred team for new user |
| `--list-users` | List all users in the database |
| `--delete-user USERNAME` | Delete a user from the database |
| `--update-password USERNAME` | Update password for an existing user |
| `--init-db` | Initialize the database |

## Password Security

### Generated Password Characteristics

- Minimum length: 8 characters (default: 12)
- Includes uppercase letters (A-Z)
- Includes lowercase letters (a-z)
- Includes digits (0-9)
- Includes special characters (!@#$%^&*()_+-=)
- Cryptographically secure (uses `secrets` module)

### Password Hashing

- All passwords are hashed using `werkzeug.security.generate_password_hash`
- Uses pbkdf2:sha256 algorithm
- Passwords are never stored in plain text
- Minimum password length: 6 characters

## Examples

### Example 1: Creating Multiple Users

```bash
# Create users for different divisions
python3 scripts/generate_password.py --create-user coach_u12 \
    --division "U12 - Minimes" --team "BC Dudelange"

python3 scripts/generate_password.py --create-user coach_u14 \
    --division "U14 - Cadets" --team "Racing Luxembourg"

python3 scripts/generate_password.py --create-user admin_user \
    --division "Total League" --team "Arantia"
```

### Example 2: Password Reset Workflow

```bash
# 1. Generate a new password for user
python3 scripts/generate_password.py --update-password john_coach

# 2. The script will output:
# Generated password: xK9$mP2&qL8!
# ✓ Password updated successfully
# 
# New password: xK9$mP2&qL8!
# Please save this password - it cannot be recovered!

# 3. Send the password to the user securely
```

### Example 3: User Audit

```bash
# List all users to see who has access
python3 scripts/generate_password.py --list-users

# Check total user count (limit is 100)
```

## User Limit

The system supports up to **100 users**. When this limit is reached, the script will prevent creating new users:

```
✗ Error: Maximum number of users (100) reached
```

## Database Location

- **File:** `data/users.db`
- **Format:** SQLite 3
- **Gitignored:** Yes (to protect user data)

## Error Handling

The script provides clear error messages for common issues:

| Error | Cause | Solution |
|-------|-------|----------|
| Username already exists | Duplicate username | Choose a different username |
| Password too short | Password < 6 characters | Use a longer password |
| User not found | Invalid username | Check username spelling |
| Database locked | Concurrent access | Wait and try again |
| Maximum users reached | 100 users in database | Delete unused accounts |

## Integration with Flask

Users created with this script can immediately log in to the Flask application using their username and password. Their preferences (division and team) will be automatically loaded.

See the [User Database Documentation](USER_DATABASE.md) for more details on the database structure and Flask integration.

## Security Best Practices

1. **Use the password generator** - Don't use weak passwords
2. **Distribute passwords securely** - Don't email passwords in plain text
3. **Regular password rotation** - Update passwords periodically
4. **Monitor user accounts** - Review the user list regularly
5. **Remove inactive accounts** - Delete users who no longer need access
6. **Backup the database** - Regularly backup `data/users.db`

## Troubleshooting

### "Database is locked" Error

This usually means another process is accessing the database. Wait a moment and try again. If the problem persists:

```bash
# Check if any Python processes are running
ps aux | grep python

# Kill any stuck processes
kill <process_id>
```

### Database Not Found

If you get errors about the database not existing:

```bash
# Manually initialize the database
python3 scripts/generate_password.py --init-db
```

### Permission Denied

Ensure you have write permissions to the `data/` directory:

```bash
# Check permissions
ls -la data/

# Fix if needed (on Unix-like systems)
chmod 755 data/
```

## See Also

- [User Database Documentation](USER_DATABASE.md) - Complete database reference
- [Example Usage](../examples/user_database_demo.py) - Python examples
- [Flask Integration Tests](../tests/test_flask_user_database.py) - Integration examples
