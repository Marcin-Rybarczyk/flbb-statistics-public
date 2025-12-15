# User Login Logging Feature

## Overview

This feature implements comprehensive user login logging to track all user authentication events. It provides both file-based logging and database tracking for security auditing and user activity monitoring.

## Features

### 1. Database Tracking

The system maintains two types of login data in SQLite database:

#### Users Table Enhancement
- Added `last_login_at` column to track the most recent login time for each user
- Automatically updated on every successful authentication

#### Login Logs Table
Complete history of all login events with the following information:
- `user_id` - Reference to the user
- `username` - Username that logged in
- `login_time` - Timestamp of the login
- `ip_address` - IP address of the user
- `user_agent` - Browser/client user agent string

### 2. File-Based Logging

All login events are also logged to `logs/user_logins.log` with structured format:
```
2025-12-14 10:01:05,759 - INFO - User 'username' logged in from IP: 192.168.1.100 | User-Agent: Mozilla/5.0...
```

The log file provides:
- Easy text-based searching and analysis
- External log aggregation tool compatibility
- Backup audit trail independent of database

### 3. Admin Dashboard Display

The admin page (`/admin`) displays comprehensive login activity when logged in as admin:

#### Login Statistics Summary
- Total number of logins
- Number of unique users who have logged in
- Login count in last 24 hours
- Login count in last 7 days
- Most active user

#### Users - Last Login Table
Shows all users with:
- Username
- User level (Admin/User/Guest)
- Last login timestamp
- Status indicator (Active/Inactive)

#### Recent Login Activity Table
Displays the last 20 login events with:
- Login time
- Username
- IP address
- User agent (browser/client info)

## Implementation Details

### Modified Files

1. **src/user_database.py**
   - Added `last_login_at` column to users table
   - Created `login_logs` table with indexes
   - Implemented `setup_login_logging()` for file logging
   - Added `log_user_login()` to write to log file
   - Created functions to retrieve login data:
     - `get_users_with_login_info()`
     - `get_recent_login_logs(limit)`
     - `get_login_statistics()`

2. **src/app.py**
   - Updated `authenticate_user()` to accept IP address and user agent
   - Modified login route to capture `request.remote_addr` and `User-Agent` header
   - Pass login statistics to admin template

3. **templates/admin.html**
   - Added "User Login Activity" section
   - Created tables for users and recent logins
   - Display statistics cards

### Database Schema

```sql
-- Users table (existing, with new column)
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;

-- New login_logs table
CREATE TABLE login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX idx_login_logs_user_id ON login_logs(user_id);
CREATE INDEX idx_login_logs_login_time ON login_logs(login_time DESC);
```

## Usage

### For Administrators

1. Navigate to the Admin page after logging in as admin
2. Scroll to the "User Login Activity" section
3. View statistics, user login times, and recent activity

### For Developers

```python
from src.user_database import (
    get_users_with_login_info,
    get_recent_login_logs,
    get_login_statistics
)

# Get all users with last login times
users = get_users_with_login_info()

# Get recent 50 logins
recent = get_recent_login_logs(limit=50)

# Get statistics
stats = get_login_statistics()
print(f"Total logins: {stats['total_logins']}")
```

## Testing

### Automated Tests

Run the comprehensive test suite:
```bash
python3 tests/test_login_logging.py
```

### Manual Demo

Run the demo script to see the feature in action:
```bash
python3 tests/demo_login_logging.py
```

### Verify Admin Page

Check that admin page displays login information:
```bash
python3 tests/verify_admin_page.py
```

## Security Considerations

1. **Log File Protection**: The `logs/` directory is excluded from git via `.gitignore`
2. **Database Security**: User database is excluded from git via `.gitignore`
3. **IP Address Logging**: IP addresses are logged for security auditing
4. **User Agent Logging**: Full user agent strings are stored for security analysis
5. **Admin Only Access**: Login information is only visible to admin users

## Privacy Notice

This feature logs:
- Username
- Login timestamps
- IP addresses
- Browser/client information (user agent)

Ensure compliance with:
- GDPR (if applicable)
- Local privacy laws
- Your organization's privacy policy

Consider adding a privacy notice to your login page informing users that login activity is logged.

## Maintenance

### Log File Rotation

The log file (`logs/user_logins.log`) will grow over time. Consider implementing log rotation:

```python
# Using Python's RotatingFileHandler
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    LOGIN_LOG_FILE,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

### Database Cleanup

For long-running systems, consider periodic cleanup of old login logs:

```sql
-- Delete login logs older than 90 days
DELETE FROM login_logs 
WHERE login_time < datetime('now', '-90 days');
```

## Future Enhancements

Potential improvements:
1. Failed login attempt tracking
2. Suspicious activity detection
3. Login location mapping
4. Export login reports to CSV
5. Real-time login notifications
6. Session management and tracking
7. Multi-factor authentication logging

## Troubleshooting

### Log file not created
- Check that `logs/` directory exists and is writable
- Verify application has permissions to create files

### Database errors
- Ensure database migrations ran successfully
- Check that `data/users.db` is not corrupted
- Verify SQLite is properly installed

### Missing login data in admin page
- Confirm you're logged in as admin
- Verify that users have logged in at least once
- Check browser console for JavaScript errors

## Support

For issues or questions:
1. Check test scripts for examples
2. Review database schema
3. Check application logs
4. Contact system administrator
