# Cache Storage Configuration

## Overview

The cache manager supports multiple storage backends for storing raw HTML and JSON files:
- **Google Drive** - Cloud storage via Google Drive API (default)
- **MyDevil.net** - SFTP storage on MyDevil.net hosting
- **Local** - Local filesystem storage (for testing)

## Configuration

### Selecting Storage Backend

Set the `CACHE_STORAGE_BACKEND` environment variable:

```bash
# Use Google Drive (default)
export CACHE_STORAGE_BACKEND=gdrive

# Use MyDevil.net SFTP
export CACHE_STORAGE_BACKEND=mydevil

# Use local storage (testing only)
export CACHE_STORAGE_BACKEND=local
```

### Google Drive Setup

**Required Secrets:**
- `GOOGLE_DRIVE_CREDENTIALS` - Service account JSON credentials
- `GOOGLE_DRIVE_FOLDER_ID` - Google Drive folder ID for cache

**Example:**
```bash
export GOOGLE_DRIVE_CREDENTIALS='{"type": "service_account", ...}'
export GOOGLE_DRIVE_FOLDER_ID='1Z4Z3Z2Z1Z0Z9Z8Z7Z6Z5'
```

### MyDevil.net Setup

**Required Secrets:**
- `MYDEVIL_HOST` - MyDevil server hostname (e.g., 'panel77.mydevil.net')
- `MYDEVIL_USERNAME` - SSH username
- `MYDEVIL_SSH_KEY` - SSH private key content (preferred) OR
- `MYDEVIL_PASSWORD` - SSH password (if no key)

**Optional:**
- `MYDEVIL_CACHE_PATH` - Remote directory path (default: '~/cache')

**Example with SSH key:**
```bash
export MYDEVIL_HOST=panel77.mydevil.net
export MYDEVIL_USERNAME=your_username
export MYDEVIL_SSH_KEY="-----BEGIN OPENSSH PRIVATE KEY-----
...your private key content...
-----END OPENSSH PRIVATE KEY-----"
export MYDEVIL_CACHE_PATH=~/flbb-cache
```

**Example with password (less secure):**
```bash
export MYDEVIL_HOST=panel77.mydevil.net
export MYDEVIL_USERNAME=your_username
export MYDEVIL_PASSWORD=your_password
export MYDEVIL_CACHE_PATH=~/flbb-cache
```

### Local Storage Setup

**Optional:**
- `LOCAL_CACHE_PATH` - Local directory path (default: './cache')

**Example:**
```bash
export CACHE_STORAGE_BACKEND=local
export LOCAL_CACHE_PATH=/tmp/flbb-cache
```

## GitHub Actions Configuration

Add secrets to your GitHub repository settings:

### For Google Drive:
1. Go to Settings → Secrets and variables → Actions
2. Add repository secrets:
   - `CACHE_STORAGE_BACKEND` = `gdrive`
   - `GOOGLE_DRIVE_CREDENTIALS` = (service account JSON)
   - `GOOGLE_DRIVE_FOLDER_ID` = (folder ID)

### For MyDevil.net:
1. Go to Settings → Secrets and variables → Actions
2. Add repository secrets:
   - `CACHE_STORAGE_BACKEND` = `mydevil`
   - `MYDEVIL_HOST` = `panel77.mydevil.net` (your server)
   - `MYDEVIL_USERNAME` = (your SSH username)
   - `MYDEVIL_SSH_KEY` = (your SSH private key) OR
   - `MYDEVIL_PASSWORD` = (your SSH password)
   - `MYDEVIL_CACHE_PATH` = `~/flbb-cache` (optional)

## Usage

### Command Line

```bash
# Upload with specific backend
python3 src/cache_manager.py upload --storage mydevil

# Download with specific backend
python3 src/cache_manager.py download --storage mydevil

# List finished games
python3 src/cache_manager.py list-finished --storage mydevil
```

### PowerShell

The PowerShell scripts automatically use the configured backend from environment variables:

```powershell
# Respects CACHE_STORAGE_BACKEND environment variable
. .\scripts\cache_helper.ps1
Invoke-DownloadCache
Invoke-UploadCache
```

## MyDevil.net SSH Key Setup

### Generate SSH Key (if you don't have one)

```bash
# On your local machine
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
# Save to: ~/.ssh/id_rsa_mydevil

# Copy public key to MyDevil.net
cat ~/.ssh/id_rsa_mydevil.pub
```

### Add Public Key to MyDevil.net

1. Log into MyDevil.net panel
2. Go to SSH → SSH Keys
3. Paste your public key
4. Save

### Use Private Key in GitHub Actions

1. Copy private key content:
   ```bash
   cat ~/.ssh/id_rsa_mydevil
   ```

2. Add to GitHub Secrets as `MYDEVIL_SSH_KEY`

### Test Connection

```bash
ssh -i ~/.ssh/id_rsa_mydevil username@panel77.mydevil.net
```

## Security Best Practices

### Google Drive
- ✓ Use service account credentials (not user credentials)
- ✓ Grant minimum required permissions to service account
- ✓ Store credentials as GitHub secrets
- ✓ Use private folder with restricted access

### MyDevil.net
- ✓ Use SSH key authentication (preferred over password)
- ✓ Use strong SSH key (RSA 4096 or Ed25519)
- ✓ Store SSH key as GitHub secret
- ✓ Never commit private keys to repository
- ✓ Set appropriate file permissions on server (~/.ssh/authorized_keys)

### Local Storage
- ⚠️ For testing only - not suitable for production
- ✓ Use temporary directories
- ✓ Clean up after testing

## Troubleshooting

### Google Drive Issues

**Problem:** "Credentials not found"
- Solution: Ensure `GOOGLE_DRIVE_CREDENTIALS` is set correctly
- Check: `echo $GOOGLE_DRIVE_CREDENTIALS` (should show JSON)

**Problem:** "Permission denied"
- Solution: Verify service account has access to folder
- Check folder sharing settings in Google Drive

### MyDevil.net Issues

**Problem:** "SSH connection failed"
- Solution: Verify hostname, username are correct
- Test: `ssh username@host` manually
- Check: Firewall not blocking port 22

**Problem:** "Permission denied (publickey)"
- Solution: Verify SSH key is correctly configured
- Check: Key format is correct (begins with -----BEGIN)
- Ensure: Public key is added to MyDevil.net panel

**Problem:** "Remote directory not found"
- Solution: Cache manager creates directory automatically
- Check: Username has permission to create directories
- Verify: `MYDEVIL_CACHE_PATH` is valid path

**Problem:** "SFTP connection timeout"
- Solution: Check network connectivity
- Verify: MyDevil.net server is accessible
- Test: `ping panel77.mydevil.net`

### General Issues

**Problem:** "Module 'paramiko' not found"
- Solution: Install dependencies
  ```bash
  pip install -r requirements.txt
  ```

**Problem:** "Unknown storage backend"
- Solution: Check `CACHE_STORAGE_BACKEND` value
- Valid values: 'gdrive', 'mydevil', 'local'

## Performance Comparison

| Backend | Upload Speed | Download Speed | Reliability | Cost |
|---------|-------------|----------------|-------------|------|
| Google Drive | Fast (API) | Fast (API) | Very High | Free* |
| MyDevil.net | Medium (SFTP) | Medium (SFTP) | High | Included** |
| Local | Instant | Instant | N/A | N/A |

*Free tier has storage limits
**Included with MyDevil.net hosting plan

## Migration Between Backends

### From Google Drive to MyDevil.net

1. Download existing cache:
   ```bash
   export CACHE_STORAGE_BACKEND=gdrive
   python3 src/cache_manager.py download
   ```

2. Switch backend and upload:
   ```bash
   export CACHE_STORAGE_BACKEND=mydevil
   python3 src/cache_manager.py upload
   ```

### From MyDevil.net to Google Drive

Same process, reverse the backends.

## Advantages by Backend

### Google Drive
- ✅ No server management required
- ✅ High reliability and uptime
- ✅ Fast API access
- ✅ Built-in versioning
- ❌ Requires Google account
- ❌ API rate limits

### MyDevil.net
- ✅ Included with existing hosting
- ✅ Full control over data
- ✅ No external dependencies
- ✅ Standard SFTP protocol
- ❌ Requires hosting account
- ❌ Depends on server uptime

### Local
- ✅ Fastest performance
- ✅ No network dependency
- ✅ Good for testing
- ❌ Not suitable for production
- ❌ No remote access
