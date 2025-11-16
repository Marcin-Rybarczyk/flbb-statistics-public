# User Database Storage Options

This document provides recommendations for storing user credentials in a database for the FLBB Statistics application.

## Current Implementation

The application currently uses **environment variables** for user authentication:
- `USER_USERNAME` - Username for the single predefined user
- `USER_PASSWORD` - Password for the single predefined user
- `ADMIN_PASSWORD` - Password for admin access

This approach is simple and suitable for:
- Single user scenarios
- Quick deployment
- Minimal infrastructure requirements

## Database Options for Multiple Users

If you need to support **multiple users** with different credentials, here are recommended database solutions:

### 1. SQLite (Recommended for Small Scale)

**Best for**: Small deployments, testing, or applications with < 100 users

**Pros**:
- ✅ No separate database server required
- ✅ File-based, easy to backup
- ✅ Built into Python (no additional dependencies)
- ✅ Perfect for development and testing
- ✅ Easy to migrate data

**Cons**:
- ❌ Not suitable for high concurrency
- ❌ Limited scalability
- ❌ Single file can be a point of failure

**Implementation**:
```python
import sqlite3
import hashlib

# Create users table
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Add a user
def add_user(username, password, role='user'):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                   (username, password_hash, role))
    conn.commit()
```

### 2. PostgreSQL (Recommended for Production)

**Best for**: Production deployments, multiple users, scalability

**Pros**:
- ✅ Robust and reliable
- ✅ Excellent for concurrent access
- ✅ ACID compliant
- ✅ Advanced features (JSON support, full-text search)
- ✅ Free and open source
- ✅ Available on most hosting platforms

**Cons**:
- ❌ Requires separate database server
- ❌ More complex setup
- ❌ Additional maintenance

**Implementation**:
```python
import psycopg2
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=os.environ.get('DB_HOST'),
    database=os.environ.get('DB_NAME'),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD')
)

# Create users table
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
```

### 3. MongoDB (Good for Flexibility)

**Best for**: Applications needing flexible schema, JSON-like data

**Pros**:
- ✅ Flexible document structure
- ✅ Easy to scale horizontally
- ✅ Good for storing user preferences with varying fields
- ✅ Already used in FLBB Statistics for game data

**Cons**:
- ❌ Overkill for simple user management
- ❌ Requires MongoDB server or Atlas account
- ❌ Additional dependency (pymongo)

**Implementation**:
```python
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

# Connect to MongoDB
client = MongoClient(os.environ.get('MONGODB_URI'))
db = client[os.environ.get('MONGODB_DATABASE')]
users_collection = db.users

# Create user
def create_user(username, password, role='user'):
    user = {
        'username': username,
        'password_hash': generate_password_hash(password),
        'role': role,
        'created_at': datetime.utcnow()
    }
    users_collection.insert_one(user)

# Authenticate user
def authenticate_user(username, password):
    user = users_collection.find_one({'username': username})
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None
```

### 4. MySQL/MariaDB

**Best for**: Traditional relational database users, shared hosting

**Pros**:
- ✅ Widely available on hosting platforms
- ✅ Good performance
- ✅ Easy to find support and documentation
- ✅ ACID compliant

**Cons**:
- ❌ Requires separate database server
- ❌ Similar complexity to PostgreSQL

**Implementation**: Similar to PostgreSQL, using `mysql-connector-python` or `pymysql`

## Recommendation for FLBB Statistics

Based on your requirements and current infrastructure:

### **Short-term (Current Setup)**
✅ **Environment Variables** - Perfect for single user
- Simple, secure when properly configured
- Store credentials in GitHub Secrets
- No database overhead

### **If You Need 2-10 Users**
✅ **SQLite** - Simple file-based database
- Easy to implement
- No infrastructure changes needed
- Can be committed to repository (without passwords) or stored separately

### **If You Need Many Users (10+)**
✅ **PostgreSQL** - Production-ready solution
- Available on most hosting platforms (Render, Railway, Heroku)
- Better for concurrent access
- Professional and scalable

### **If You Want to Integrate with Existing MongoDB**
✅ **MongoDB** - Leverage existing setup
- You already use MongoDB for game data
- Consistent technology stack
- Good if you expand to store user preferences, favorites, etc.

## Security Best Practices

Regardless of which database you choose:

1. **Never store passwords in plain text**
   - Use `werkzeug.security.generate_password_hash()` for hashing
   - Use `check_password_hash()` for verification

2. **Use environment variables for credentials**
   - Database connection strings in `.env` files
   - Never commit credentials to repository

3. **Implement rate limiting**
   - Prevent brute force attacks on login

4. **Use HTTPS in production**
   - Encrypt data in transit

5. **Regular backups**
   - Backup user database separately from game data

6. **Session management**
   - Use Flask's built-in session management
   - Set appropriate session timeout

## Migration Path

If you decide to migrate from environment variables to database:

1. Create database schema
2. Add migration script to import existing user
3. Update authentication functions in `src/app.py`
4. Test thoroughly
5. Update documentation
6. Deploy with database connection configured

## Example: Adding SQLite Support

```python
# In src/app.py

import sqlite3
from werkzeug.security import check_password_hash

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def authenticate_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        return {'username': user['username'], 'role': user['role']}
    return None

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = authenticate_user(username, password)
        if user:
            session['user_authenticated'] = True
            session['username'] = user['username']
            session['role'] = user['role']
            session.permanent = True
            return redirect(url_for('index'))
        else:
            return render_template('user_login.html', 
                                 error='Invalid username or password.')
    
    return render_template('user_login.html')
```

## Conclusion

For the FLBB Statistics application with one predefined user:
- **Current solution (environment variables) is optimal**
- Admin password in GitHub Secrets ✅
- User credentials in environment variables ✅
- Simple, secure, and maintainable

Consider database storage only if you need to support multiple users with different access levels.
