# Google Drive Integration for FLBB Statistics

This document describes the Google Drive integration added to store raw information and generated CSV files in Google Drive.

> **📖 For GitHub Actions and Secrets Setup**: See the detailed guides in the `doc/` directory:
> - [`doc/GOOGLE_DRIVE_SECRETS_SETUP.md`](doc/GOOGLE_DRIVE_SECRETS_SETUP.md) - Complete setup guide for Google Cloud and GitHub Secrets
> - [`doc/GITHUB_ACTIONS_USAGE.md`](doc/GITHUB_ACTIONS_USAGE.md) - How to use the GitHub Actions workflows

## Overview

The system now automatically:
1. Downloads raw HTML data using `download-controller.ps1`
2. Generates `full-game-stats.csv` from processed data
3. Creates a timestamped archive containing all raw data and CSV
4. Uploads the archive to Google Drive

## Components

### Python Scripts

1. **`google_drive_helper.py`** - Google Drive API wrapper
   - Handles authentication using service account
   - Provides functions for uploading files and creating folders
   - Can be used standalone via command line

2. **`post_process.py`** - Main post-processing script
   - Generates CSV from JSON data (if needed)
   - Creates archive with raw data
   - Uploads to Google Drive
   - Handles errors gracefully

### Configuration

The `config.json` file now includes Google Drive settings:

```json
{
  "googleDrive": {
    "enabled": true,
    "folderId": "your-google-drive-folder-id",
    "serviceAccountFile": "flbb-statistics-e9ab0e2a8b4c.json"
  }
}
```

### PowerShell Integration

The `download-controller.ps1` script has been updated to:
- Call the Python post-processing script after downloading data
- Fallback to PowerShell archive creation if Python fails
- Handle errors gracefully

## Usage

### Automatic (via PowerShell)

Run the main download script as usual:
```powershell
.\download-controller.ps1
```

The script will automatically handle post-processing and Google Drive upload.

### Manual Post-Processing

You can run post-processing manually:
```bash
# Full workflow (CSV generation + archive + upload)
python post_process.py

# Skip CSV generation
python post_process.py --skip-csv

# Skip Google Drive upload
python post_process.py --skip-upload

# Archive only
python post_process.py --archive-only
```

### Google Drive Helper

Direct Google Drive operations:
```bash
# Upload a file
python google_drive_helper.py upload --file myfile.zip --folder-id YOUR_FOLDER_ID

# Upload with custom name
python google_drive_helper.py upload --file data.csv --file-name backup-2024-01-15.csv

# Download a file by ID
python google_drive_helper.py download --file-id FILE_ID --output-path ./downloads

# List files in a folder
python google_drive_helper.py list --folder-id YOUR_FOLDER_ID

# List files with name pattern
python google_drive_helper.py list --folder-id YOUR_FOLDER_ID --pattern ".csv"

# Create a folder
python google_drive_helper.py create-folder --folder-name "Season 2024-25"
```

**Environment Variables Support:**
The helper now supports environment variables for CI/CD usage:
- `GOOGLE_DRIVE_CREDENTIALS`: JSON service account credentials
- `GOOGLE_DRIVE_FOLDER_ID`: Default folder ID for operations

## Files Included in Archive

The archive contains:
- All raw HTML files from `game-schedule-raw/` directory
- All raw HTML files from `full-game-stats-raw/` directory  
- Generated `full-game-stats.csv` file
- Database files (`gamesDB.json`, `gameScheduleDB.json`)

## Authentication

Uses Google Service Account authentication via `flbb-statistics-e9ab0e2a8b4c.json`.

The service account needs the following permissions:
- Google Drive API access
- Write access to the target folder

## Error Handling

- If Python post-processing fails, falls back to PowerShell archive creation
- If Google Drive upload fails (e.g., no internet), continues with local archive
- All errors are logged and reported but don't stop the main workflow

## Dependencies

Added to `requirements.txt`:
- `google-api-python-client`
- `google-auth`
- `google-auth-oauthlib`
- `google-auth-httplib2`

## Archive Naming

Archives are named with timestamps: `raw-data-YYYYMMDDHHMMSS.zip`

This ensures unique filenames and easy identification of when data was collected.