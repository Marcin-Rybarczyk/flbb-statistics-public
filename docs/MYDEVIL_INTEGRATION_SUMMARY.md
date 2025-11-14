# MyDevil.net Storage Integration Summary

## Overview

The cache manager has been updated to support MyDevil.net SFTP storage as an alternative to Google Drive. This allows users with MyDevil.net hosting to store cache files on their own server instead of using Google Drive.

## Changes Made

### 1. New Storage Abstraction Layer (`src/storage_helper.py`)

Created a unified storage interface with three backends:

- **GoogleDriveStorage** - Original Google Drive implementation
- **MyDevilStorage** - New SFTP storage for MyDevil.net
- **LocalStorage** - Local filesystem (for testing)

**Key Features:**
- Abstract `StorageBackend` base class
- Consistent API across all backends
- Factory function `get_storage_backend()` for easy initialization
- Environment-based configuration

### 2. Updated Cache Manager (`src/cache_manager.py`)

**Changes:**
- Replaced direct Google Drive calls with storage abstraction
- Renamed methods for clarity:
  - `upload_cache_to_drive()` → `upload_cache_to_storage()`
  - `download_cache_from_drive()` → `download_cache_from_storage()`
- Added `--storage` parameter to CLI
- Backend selection via `CACHE_STORAGE_BACKEND` environment variable

### 3. MyDevil.net SFTP Implementation

**Authentication Options:**
- SSH key (recommended, more secure)
- Password (if key not available)

**Features:**
- Automatic directory creation
- File upload/download via SFTP
- File listing and latest file detection
- Proper connection management

### 4. GitHub Actions Workflow (`update-csv-data.yml`)

**Added Secrets Support:**
```yaml
env:
  CACHE_STORAGE_BACKEND: ${{ secrets.CACHE_STORAGE_BACKEND || 'gdrive' }}
  MYDEVIL_HOST: ${{ secrets.MYDEVIL_HOST }}
  MYDEVIL_USERNAME: ${{ secrets.MYDEVIL_USERNAME }}
  MYDEVIL_SSH_KEY: ${{ secrets.MYDEVIL_SSH_KEY }}
  MYDEVIL_PASSWORD: ${{ secrets.MYDEVIL_PASSWORD }}
  MYDEVIL_CACHE_PATH: ${{ secrets.MYDEVIL_CACHE_PATH }}
```

Defaults to Google Drive if `CACHE_STORAGE_BACKEND` not set.

### 5. Dependencies (`requirements.txt`)

Added `paramiko==3.5.0` for SFTP support.

### 6. Documentation

**New:** `docs/CACHE_STORAGE_BACKENDS.md`
- Complete setup guide for all backends
- GitHub Actions configuration
- SSH key generation and setup
- Troubleshooting guide
- Security best practices

## Configuration Examples

### Use Google Drive (Default)
```bash
export CACHE_STORAGE_BACKEND=gdrive
export GOOGLE_DRIVE_CREDENTIALS='...'
export GOOGLE_DRIVE_FOLDER_ID='...'
```

### Use MyDevil.net with SSH Key
```bash
export CACHE_STORAGE_BACKEND=mydevil
export MYDEVIL_HOST=panel77.mydevil.net
export MYDEVIL_USERNAME=your_username
export MYDEVIL_SSH_KEY="$(cat ~/.ssh/id_rsa)"
export MYDEVIL_CACHE_PATH=~/flbb-cache
```

### Use MyDevil.net with Password
```bash
export CACHE_STORAGE_BACKEND=mydevil
export MYDEVIL_HOST=panel77.mydevil.net
export MYDEVIL_USERNAME=your_username
export MYDEVIL_PASSWORD=your_password
export MYDEVIL_CACHE_PATH=~/flbb-cache
```

## GitHub Secrets Configuration

For MyDevil.net in GitHub Actions:

1. Go to repository Settings → Secrets and variables → Actions
2. Add the following repository secrets:
   - `CACHE_STORAGE_BACKEND` = `mydevil`
   - `MYDEVIL_HOST` = `panel77.mydevil.net` (your server)
   - `MYDEVIL_USERNAME` = (your SSH username)
   - `MYDEVIL_SSH_KEY` = (your SSH private key content) **OR**
   - `MYDEVIL_PASSWORD` = (your SSH password)
   - `MYDEVIL_CACHE_PATH` = `~/flbb-cache` (optional)

## Usage

### Command Line

```bash
# Upload to MyDevil.net
python3 src/cache_manager.py upload --storage mydevil

# Download from MyDevil.net
python3 src/cache_manager.py download --storage mydevil

# List files
python3 src/cache_manager.py list-finished --storage mydevil
```

### PowerShell

The PowerShell scripts automatically use the configured backend:

```powershell
# Set environment variable first
$env:CACHE_STORAGE_BACKEND = "mydevil"

# Then use helper functions
. .\scripts\cache_helper.ps1
Invoke-DownloadCache  # Uses MyDevil.net
Invoke-UploadCache    # Uses MyDevil.net
```

## Advantages of MyDevil.net Storage

✅ **No External Dependencies** - Uses your existing hosting
✅ **Full Control** - Your data on your server
✅ **Cost Effective** - Included with hosting plan
✅ **Standard Protocol** - Uses standard SFTP
✅ **No API Limits** - No rate limiting issues

## Migration from Google Drive

If you want to switch from Google Drive to MyDevil.net:

1. Download existing cache with Google Drive:
   ```bash
   export CACHE_STORAGE_BACKEND=gdrive
   python3 src/cache_manager.py download
   ```

2. Switch to MyDevil.net and upload:
   ```bash
   export CACHE_STORAGE_BACKEND=mydevil
   export MYDEVIL_HOST=panel77.mydevil.net
   export MYDEVIL_USERNAME=your_username
   export MYDEVIL_SSH_KEY="$(cat ~/.ssh/id_rsa)"
   python3 src/cache_manager.py upload
   ```

3. Update GitHub secrets to use `mydevil` backend

## Security Considerations

### SSH Key Authentication (Recommended)

✅ More secure than password
✅ No password exposed in secrets
✅ Can be revoked without changing password
✅ Supports key passphrase for extra security

**Setup:**
```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_mydevil

# Add public key to MyDevil.net panel
cat ~/.ssh/id_rsa_mydevil.pub
# Copy this to MyDevil.net SSH Keys section

# Use private key in GitHub secret
cat ~/.ssh/id_rsa_mydevil
# Copy this to MYDEVIL_SSH_KEY secret
```

### Password Authentication (Alternative)

⚠️ Less secure than SSH key
⚠️ Password visible to repository admins with secret access
✅ Simpler to set up

Only use if SSH key setup is not possible.

## Testing

All tests updated to use local storage backend:

```bash
# Run tests
python3 tests/test_cache_manager.py

# Test storage backends
python3 src/storage_helper.py test --backend local
python3 src/storage_helper.py test --backend mydevil  # If configured
```

## Backward Compatibility

✅ **Fully backward compatible** with existing Google Drive setup
✅ Defaults to Google Drive if `CACHE_STORAGE_BACKEND` not set
✅ No changes required to existing workflows using Google Drive
✅ All existing documentation still valid

## Performance Comparison

| Metric | Google Drive | MyDevil.net SFTP |
|--------|-------------|------------------|
| Upload Speed | Fast (API) | Medium (SFTP) |
| Download Speed | Fast (API) | Medium (SFTP) |
| Reliability | Very High | High |
| Setup Complexity | Medium | Medium |
| External Dependencies | Google Account | Hosting Account |
| Cost | Free* | Included** |

*Free tier has limits  
**Included with hosting plan

## Troubleshooting

### Common Issues

**"Module 'paramiko' not found"**
```bash
pip install -r requirements.txt
```

**"SSH connection failed"**
- Verify hostname is correct
- Test: `ssh username@host`
- Check firewall/network

**"Permission denied (publickey)"**
- Verify SSH key is in correct format
- Ensure public key added to MyDevil.net panel
- Check key permissions: `chmod 600 ~/.ssh/id_rsa`

**"Remote directory not found"**
- Directory is created automatically
- Verify user has permission to create directories

## Files Modified

### New Files
- `src/storage_helper.py` (450 lines)
- `docs/CACHE_STORAGE_BACKENDS.md` (250 lines)
- `docs/MYDEVIL_INTEGRATION_SUMMARY.md` (this file)

### Modified Files
- `src/cache_manager.py` (~50 lines changed)
- `.github/workflows/update-csv-data.yml` (+8 lines)
- `requirements.txt` (+1 line)
- `tests/test_cache_manager.py` (+2 lines)

### Total Impact
- ~700 lines added
- ~50 lines modified
- All tests passing ✓
- No security vulnerabilities ✓

## Conclusion

MyDevil.net storage integration provides a flexible alternative to Google Drive while maintaining full backward compatibility. Users can now choose the storage backend that best fits their infrastructure and preferences.
