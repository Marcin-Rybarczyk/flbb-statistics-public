# MongoDB Setup Guide for MyDevil.net

This guide explains how to use MyDevil.net hosting as your MongoDB server for the FLBB Statistics application.

## Overview

MyDevil.net provides MongoDB as a service on their servers. You can connect to it via SSH tunnel from your local development environment or from the deployed Flask application.

## Prerequisites

1. **MyDevil.net Account**: Active hosting account with MongoDB access
2. **SSH Access**: Ability to SSH into your MyDevil.net server
3. **MongoDB Installed Locally** (optional, for testing): For local development testing

## Setup Instructions

### Step 1: Access MyDevil.net MongoDB

1. **Log in to MyDevil.net Panel**
   - Go to https://www.mydevil.net/
   - Log in with your credentials

2. **Check MongoDB Availability**
   - Navigate to: Bazy danych → MongoDB (Databases → MongoDB)
   - Note your MongoDB connection details:
     - Database name
     - Username (usually your MyDevil username)
     - Port (usually 27017)

3. **Get Your Server Address**
   - Your server address is typically: `sXX.mydevil.net` (e.g., `s1.mydevil.net`)
   - Check your welcome email or panel for the exact server name

### Step 2: Configure Environment Variables

**Copy the MyDevil environment template:**
```bash
cp .env.mydevil.example .env
```

**Edit `.env` file:**
```bash
# MongoDB Configuration
MONGODB_ENABLED=true
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=flbb-statistics

# Data Source
DATA_SOURCE=auto
```

**If MongoDB requires authentication** (check MyDevil panel):
```bash
MONGODB_URI=mongodb://username:password@localhost:27017/flbb-statistics
```

### Step 3: Create SSH Tunnel

#### Option A: Manual SSH Tunnel (Development/Testing)

Open a terminal and create the SSH tunnel:

```bash
# Basic tunnel
ssh -L 27017:localhost:27017 your-username@sXX.mydevil.net

# With keep-alive (recommended)
ssh -L 27017:localhost:27017 -o ServerAliveInterval=60 your-username@sXX.mydevil.net
```

Replace:
- `your-username` with your MyDevil.net username
- `sXX.mydevil.net` with your server address (e.g., `s1.mydevil.net`)

**Keep this terminal open** while working with the Flask app.

#### Option B: AutoSSH (Production - Recommended)

For production deployments, use AutoSSH to maintain a persistent tunnel:

1. **Install AutoSSH:**
   ```bash
   sudo apt-get update
   sudo apt-get install autossh
   ```

2. **Create persistent tunnel:**
   ```bash
   autossh -M 0 -f -N \
     -o ServerAliveInterval=60 \
     -o ServerAliveCountMax=3 \
     -L 27017:localhost:27017 \
     your-username@sXX.mydevil.net
   ```

3. **Verify tunnel is running:**
   ```bash
   ps aux | grep autossh
   netstat -tln | grep 27017
   ```

#### Option C: SSH Config (Alternative)

Create a permanent SSH configuration:

1. **Edit `~/.ssh/config`:**
   ```
   Host mydevil-mongodb
       HostName sXX.mydevil.net
       User your-username
       LocalForward 27017 localhost:27017
       ServerAliveInterval 60
       ServerAliveCountMax 3
       IdentityFile ~/.ssh/id_rsa
   ```

2. **Connect:**
   ```bash
   ssh -f -N mydevil-mongodb
   ```

### Step 4: Test MongoDB Connection

**Test with mongosh (if installed):**
```bash
mongosh mongodb://localhost:27017/
```

**Test with Python:**
```python
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
print("Connected successfully!")
print("Databases:", client.list_database_names())
client.close()
```

**Test with the Flask app:**
```bash
python tests/test_mongodb_data_source.py
```

Expected output:
```
✅ pymongo is installed
✅ MongoDB is enabled via environment variable
✅ Loaded X games from MongoDB
```

### Step 5: Export Data to MongoDB

Once the SSH tunnel is active and tested:

```bash
# Export from CSV
python scripts/export_csv_to_mongodb.py --source csv

# Or export from JSON files
python scripts/export_csv_to_mongodb.py --source json
```

Expected output:
```
============================================================
Export completed!
============================================================
✅ Inserted: 210
🔄 Updated: 0
❌ Failed: 0
📊 Total: 210
============================================================
```

### Step 6: Run the Flask Application

```bash
# Test mode
python tests/test_local_flask.py --test-only

# Run the app
python tests/test_local_flask.py
```

You should see in the logs:
```
Data source preference: auto
Loading game data from MongoDB...
✅ Loaded 210 games from MongoDB
```

## Production Deployment on MyDevil.net

### Method 1: SSH Tunnel from MyDevil Server to Itself

When deploying Flask on MyDevil.net, you can connect directly or use a local tunnel:

1. **Deploy Flask app to MyDevil.net** (see `docs/README_DEPLOYMENT.md`)

2. **Create systemd service for SSH tunnel** (if needed):
   ```bash
   # On MyDevil server, create tunnel to localhost
   # This may not be necessary if MongoDB is on the same server
   ```

3. **Configure `.env` on server:**
   ```bash
   MONGODB_ENABLED=true
   MONGODB_URI=mongodb://localhost:27017/
   MONGODB_DATABASE=flbb-statistics
   DATA_SOURCE=auto
   ```

### Method 2: Direct Connection (If Available)

If MyDevil.net allows direct MongoDB connections without tunnel:

```bash
MONGODB_ENABLED=true
MONGODB_URI=mongodb://username:password@localhost:27017/flbb-statistics
MONGODB_DATABASE=flbb-statistics
DATA_SOURCE=auto
```

## Troubleshooting

### Connection Refused

**Problem:** Cannot connect to MongoDB

**Solutions:**
1. Verify SSH tunnel is active: `netstat -tln | grep 27017`
2. Check SSH connection: `ssh your-username@sXX.mydevil.net`
3. Verify MongoDB is running on MyDevil server
4. Check firewall rules

### Authentication Failed

**Problem:** Authentication error when connecting

**Solutions:**
1. Check credentials in MyDevil panel
2. Update `MONGODB_URI` with username and password
3. Ensure database name matches what's in panel

### SSH Tunnel Keeps Disconnecting

**Problem:** Tunnel disconnects frequently

**Solutions:**
1. Use AutoSSH instead of regular SSH
2. Add keep-alive settings to SSH config:
   ```
   ServerAliveInterval 60
   ServerAliveCountMax 3
   ```
3. Check network stability

### Flask App Can't Find MongoDB

**Problem:** App falls back to CSV despite tunnel being active

**Solutions:**
1. Verify `MONGODB_ENABLED=true` in `.env`
2. Check tunnel is forwarding to correct port
3. Test connection manually: `mongosh mongodb://localhost:27017/`
4. Check Flask app logs for error messages

## SSH Tunnel Management

### Start Tunnel on Boot (Linux)

Create systemd service `/etc/systemd/system/mydevil-mongo-tunnel.service`:

```ini
[Unit]
Description=SSH Tunnel to MyDevil.net MongoDB
After=network.target

[Service]
Type=simple
User=your-local-username
ExecStart=/usr/bin/autossh -M 0 -N -L 27017:localhost:27017 your-username@sXX.mydevil.net
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mydevil-mongo-tunnel
sudo systemctl start mydevil-mongo-tunnel
sudo systemctl status mydevil-mongo-tunnel
```

### Check Tunnel Status

```bash
# Check if tunnel is active
ps aux | grep ssh | grep 27017

# Check if port is listening
netstat -tln | grep 27017

# Test connection
mongosh mongodb://localhost:27017/ --eval "db.adminCommand('ping')"
```

### Stop Tunnel

```bash
# Find SSH tunnel process
ps aux | grep "ssh.*27017"

# Kill the process
kill <PID>

# Or if using autossh
killall autossh
```

## Security Best Practices

1. **Use SSH Keys**: Set up SSH key authentication instead of passwords
2. **Restrict Access**: Only allow connections from trusted IPs if possible
3. **Strong Passwords**: Use strong MongoDB passwords if authentication is enabled
4. **Monitor Access**: Regularly check MongoDB access logs
5. **Backup Data**: Regularly export data as backup

## Alternative: MongoDB Atlas

If SSH tunnels are problematic, consider MongoDB Atlas:

1. **Free Tier**: 512MB storage, perfect for this app
2. **No SSH Needed**: Direct connection via internet
3. **Better Reliability**: Professional infrastructure
4. **Easy Setup**: See `docs/MONGODB_INTEGRATION.md`

## Support

For MyDevil.net-specific issues:
- **MyDevil Support**: https://www.mydevil.net/support
- **MongoDB Docs**: https://docs.mongodb.com/
- **This Project**: Create GitHub issue with details

## Summary

**Quick Start for MyDevil.net:**

```bash
# 1. Create SSH tunnel
ssh -L 27017:localhost:27017 username@sXX.mydevil.net

# 2. Configure environment
cp .env.mydevil.example .env
# Edit .env with your settings

# 3. Export data
python scripts/export_csv_to_mongodb.py

# 4. Run Flask app
python tests/test_local_flask.py
```

---

**Last Updated:** 2025-11-08  
**Compatible with:** MyDevil.net MongoDB service
