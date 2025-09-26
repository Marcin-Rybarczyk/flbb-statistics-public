# GitHub Action: CSV Generation and Google Drive Upload

This document describes the automated workflow that generates CSV files from basketball statistics and uploads them to Google Drive.

## Overview

The workflow performs the following steps:
1. **Downloads game data** using `download-controller.ps1`
2. **Extracts statistics** using `extract-game.ps1`  
3. **Generates CSV files** from the processed data
4. **Uploads files to Google Drive** automatically

## Workflow Details

### File: `.github/workflows/run.yml`

**Name:** Generate CSV and Upload to Google Drive

**Triggers:**
- **Scheduled:** Daily at midnight UTC (`0 0 * * *`)
- **Manual:** Can be triggered manually via GitHub Actions interface

**Requirements:**
- Windows runner (required for PowerShell scripts)
- Python 3.11 with dependencies from `requirements.txt`
- Google Drive service account credentials (stored as GitHub secrets)

### Required GitHub Secrets

The workflow requires these secrets to be configured in the repository:

1. **`GOOGLE_DRIVE_CREDENTIALS`** - JSON content of the Google Drive service account file
2. **`GOOGLE_DRIVE_FOLDER_ID`** - Target folder ID in Google Drive where files will be uploaded

### Workflow Steps

1. **Setup Environment**
   - Checkout repository 
   - Install Python 3.11 and dependencies
   - Create service account credentials file

2. **Data Processing**
   - Execute `download-controller.ps1` (downloads game data from basketball website)
   - Execute `extract-game.ps1` (processes raw data into JSON format)
   - Generate CSV files from processed data (fallback if scripts fail)

3. **Upload Results**
   - Upload generated CSV file to Google Drive
   - Upload ZIP archive with raw data to Google Drive
   - Save files as GitHub Actions artifacts (30-day retention)

4. **Cleanup**
   - Remove service account credentials file for security

### Output Files

The workflow generates and uploads:

- **`full-game-stats.csv`** - Main statistics file with all game data
- **`raw-data-YYYYMMDDHHMMSS.zip`** - Archive containing raw downloaded data

### Error Handling

The workflow is designed to be resilient:
- Individual script failures don't stop the entire workflow
- Fallback CSV generation if PowerShell scripts fail
- Files are uploaded even if some steps fail
- All files are saved as GitHub Actions artifacts for backup

### Monitoring

To check workflow status:
1. Go to the **Actions** tab in GitHub
2. Select **Generate CSV and Upload to Google Drive**
3. View run history and detailed logs

### Manual Execution

To run the workflow manually:
1. Go to **Actions** → **Generate CSV and Upload to Google Drive**
2. Click **Run workflow**
3. Click **Run workflow** button to confirm

## Troubleshooting

### Common Issues

1. **Missing secrets**: Ensure `GOOGLE_DRIVE_CREDENTIALS` and `GOOGLE_DRIVE_FOLDER_ID` are configured
2. **Network timeouts**: The scripts download data from external websites which may occasionally fail
3. **PowerShell errors**: The workflow includes fallback mechanisms for script failures

### Logs

Detailed execution logs are available in the GitHub Actions interface for each run.