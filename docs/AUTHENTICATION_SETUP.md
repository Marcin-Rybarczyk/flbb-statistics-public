# User Authentication Setup Guide

This guide explains how to set up user authentication for the FLBB Statistics application.

## Overview

The application supports two levels of authentication:
- **User Authentication** - For accessing statistics and analysis features
- **Admin Authentication** - For accessing import/export and admin features

## Quick Setup

### Step 1: Create `.env` File

Copy the example environment file to create your own `.env` file:

```bash
cp .env.example .env
```

### Step 2: Configure Authentication Credentials

Edit the `.env` file and set your credentials:

```bash
# User Authentication (Required for accessing statistics and analysis)
USER_USERNAME=your-username-here
USER_PASSWORD=your-secure-password-here

# Admin Authentication (Required for Import/Export features)
ADMIN_PASSWORD=your-secure-admin-password-here
```

**Important Security Notes:**
- Use strong, unique passwords
- Never commit the `.env` file to version control (it's already in `.gitignore`)
- Store credentials securely

### Step 3: Restart the Application

After creating/updating the `.env` file, restart the Flask application:

```bash
# Development
python3 src/app.py

# Production (with Gunicorn)
gunicorn --bind 0.0.0.0:5001 wsgi:application
```

## What Happens

1. When the Flask application starts, it automatically loads environment variables from the `.env` file using `python-dotenv`
2. The application reads `USER_USERNAME` and `USER_PASSWORD` for user authentication
3. The application reads `ADMIN_PASSWORD` for admin authentication

## Access Levels

### Guest Users (No Login)
- Can view: Standings, Fixtures
- Cannot access: Statistics, Player Stats, Team Stats, Referee Stats, Deep Analysis, Admin Panel

### Logged-in Users
- Can view: All guest features + Statistics, Player Stats, Team Stats, Referee Stats, Deep Analysis, Preferences
- Cannot access: Admin Panel (Import/Export)

### Admin Users
- Can view: All features including Admin Panel
- Can perform: Import/Export of season data

## Login Pages

- **User Login**: `/user/login`
- **Admin Login**: `/admin/login`

## Troubleshooting

### Error: "User authentication is not configured"

This error appears when you try to login but the `.env` file doesn't have `USER_USERNAME` and `USER_PASSWORD` set.

**Solution:**
1. Make sure you created a `.env` file in the repository root
2. Verify that `USER_USERNAME` and `USER_PASSWORD` are uncommented and set in the `.env` file
3. Restart the Flask application

### Login Works Locally but Not on Server

**Solution:**
1. On most hosting platforms (Render, Railway, Heroku, etc.), you should set environment variables through the platform's dashboard, not via a `.env` file
2. For platforms like MyDevil.net that support `.env` files, ensure the file is uploaded to the server
3. Check that the application has read permissions on the `.env` file

### Environment Variables Not Loading

**Solution:**
1. Verify the `.env` file is in the same directory as `src/app.py` (repository root)
2. Make sure `python-dotenv` is installed: `pip install python-dotenv`
3. Check that there are no syntax errors in the `.env` file (no spaces around `=`)
4. Restart the application after making changes

## Platform-Specific Setup

### Render.com / Railway / Heroku
Set environment variables in the platform dashboard:
- Go to your app settings
- Add environment variables:
  - `USER_USERNAME`: your-username
  - `USER_PASSWORD`: your-password
  - `ADMIN_PASSWORD`: your-admin-password
- The application will use these instead of the `.env` file

### MyDevil.net
1. Upload the `.env` file to your application directory
2. Or set environment variables in the `passenger_wsgi.py` file
3. Restart the application using: `touch tmp/restart.txt`

## Example `.env` File

```bash
# Flask Configuration
FLASK_ENV=production
DEBUG=False
SECRET_KEY=your-randomly-generated-secret-key-here

# User Authentication
USER_USERNAME=basketballuser
USER_PASSWORD=MySecurePassword123!

# Admin Authentication
ADMIN_PASSWORD=AdminSecurePassword456!

# Optional: MongoDB Configuration
# MONGODB_ENABLED=true
# MONGODB_URI=mongodb://localhost:27017/
# MONGODB_DATABASE=flbb-statistics

# Optional: Data Source
# DATA_SOURCE=auto
```

## Security Best Practices

1. **Use Strong Passwords**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, and symbols
   - Don't use common words or patterns

2. **Keep Credentials Secret**
   - Never share your `.env` file
   - Never commit the `.env` file to version control
   - Use different credentials for development and production

3. **Regular Updates**
   - Change passwords periodically
   - Update credentials if you suspect they've been compromised

4. **Production Deployment**
   - Use environment variables from your hosting platform
   - Enable HTTPS/SSL for your application
   - Consider using a secrets management service for sensitive data

## Brute-Force Protection

The application includes built-in protection against brute-force login attacks:

### Rate Limiting Features
- **Maximum Attempts**: 5 login attempts per 15 minutes per IP address
- **Applied To**: Both `/user/login` and `/admin/login` endpoints
- **Scope**: POST requests only (viewing the login page doesn't count)
- **Lockout Duration**: 15 minutes after 5 failed attempts
- **Error Response**: HTTP 429 (Too Many Requests) with user-friendly message

### How It Works
1. Each IP address can make up to 5 login POST requests within a 15-minute window
2. Both successful and failed login attempts count toward the limit
3. After 5 attempts, the IP is blocked from making further login attempts for 15 minutes
4. Users will see a clear error message: "Too many login attempts. Please try again in 15 minutes."
5. The rate limit automatically resets after the time window expires

### Important Notes
- Rate limits are tracked per IP address, protecting against both single-source and distributed attacks
- The limit applies regardless of whether credentials are correct or incorrect
- GET requests to login pages are not rate-limited, so users can still view the login form
- This protection is applied at the application level and works on any hosting platform

### For System Administrators
If you need to customize the rate limiting behavior:

1. **Adjust Rate Limits**: Edit `src/app.py` and modify the `@limiter.limit()` decorator:
   ```python
   @limiter.limit("5 per 15 minutes", methods=["POST"])  # Current setting
   # Change to, for example:
   @limiter.limit("3 per 30 minutes", methods=["POST"])  # Stricter
   @limiter.limit("10 per 15 minutes", methods=["POST"]) # More lenient
   ```

2. **Production Considerations**: For high-traffic deployments or multi-instance setups, consider:
   - Using Redis or Memcached as the rate limit storage backend instead of in-memory storage
   - Implementing additional security measures like CAPTCHA for repeated failures
   - Monitoring login attempt patterns for security analysis

### Testing Rate Limiting
You can test the rate limiting functionality using the provided test suite:
```bash
python3 tests/test_rate_limiting.py
```

## Related Documentation

- [Deployment Guide](README_DEPLOYMENT.md) - Full deployment instructions
- [README](../README.md) - Main project documentation
- [.env.example](../.env.example) - Template for environment variables

## Support

If you encounter issues with authentication setup, please:
1. Check the troubleshooting section above
2. Review the application logs for specific error messages
3. Verify your `.env` file syntax
4. Ensure `python-dotenv` is installed and up to date
