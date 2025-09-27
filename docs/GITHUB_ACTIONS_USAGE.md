# GitHub Actions for Google Drive Integration

This document explains how to use the GitHub Actions workflows for Google Drive operations.

## Available Workflows

### 1. Upload to Google Drive (`google-drive-upload.yml`)

**Purpose**: Upload files from the repository to Google Drive

**Triggers**:
- Manual trigger (workflow_dispatch) with customizable parameters
- Automatic trigger on push when `full-game-stats.csv` or `*.zip` files change

**Parameters** (for manual trigger):
- `file_path` (required): Path to file to upload (default: `full-game-stats.csv`)
- `folder_id` (optional): Google Drive folder ID (uses `GOOGLE_DRIVE_FOLDER_ID` secret if not provided)
- `file_name` (optional): Custom name for uploaded file

**Usage**:
1. Go to "Actions" tab in your repository
2. Select "Upload to Google Drive"
3. Click "Run workflow"
4. Fill in the parameters and click "Run workflow"

**Example**:
- Upload CSV file: `file_path = full-game-stats.csv`
- Upload with custom name: `file_path = data.zip, file_name = backup-2024-01-15.zip`

### 2. Download from Google Drive (`upload-to-gdrive.yml`)

**Purpose**: Download files from Google Drive to the repository

**Triggers**:
- Manual trigger (workflow_dispatch) only

**Parameters**:
- `file_id` (required): Google Drive file ID to download
- `output_path` (optional): Output directory (default: repository root)
- `output_name` (optional): Name for downloaded file (uses original name if not provided)

**Usage**:
1. Get the file ID from Google Drive (see "Getting File IDs" section below)
2. Go to "Actions" tab in your repository
3. Select "Download from Google Drive"
4. Click "Run workflow"
5. Enter the file ID and other parameters
6. The downloaded file will be available as a workflow artifact

**Example**:
- Download to root: `file_id = 1ABC123XYZ`
- Download to specific folder: `file_id = 1ABC123XYZ, output_path = downloads`

### 3. List Google Drive Files (`google-drive-list.yml`)

**Purpose**: List files in a Google Drive folder

**Triggers**:
- Manual trigger (workflow_dispatch) only

**Parameters**:
- `folder_id` (optional): Google Drive folder ID (uses `GOOGLE_DRIVE_FOLDER_ID` secret if not provided)
- `name_pattern` (optional): File name pattern to filter by

**Usage**:
1. Go to "Actions" tab in your repository
2. Select "List Google Drive Files"
3. Click "Run workflow"
4. Optionally specify folder ID and/or name pattern
5. Check the workflow logs to see the file list

**Example**:
- List all files: (leave parameters empty)
- List CSV files: `name_pattern = .csv`
- List files in specific folder: `folder_id = 1ABC123XYZ`

## Getting File IDs

To get a Google Drive file ID:

1. Open Google Drive in your browser
2. Right-click on the file you want to download
3. Select "Get link"
4. The URL will look like: `https://drive.google.com/file/d/FILE_ID_HERE/view`
5. Copy the `FILE_ID_HERE` part

Alternatively, you can use the "List Google Drive Files" workflow to see all files with their IDs.

## Required Secrets

Before using these workflows, ensure you have set up the following GitHub Secrets (see `GOOGLE_DRIVE_SECRETS_SETUP.md` for detailed instructions):

### Required:
- `GOOGLE_DRIVE_CREDENTIALS`: Service account JSON credentials
- `GOOGLE_DRIVE_FOLDER_ID`: Default folder ID for uploads and listings

### Optional:
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_EMAIL`: Service account email (for logging)

## Workflow Status and Logs

To check the status of your workflows:

1. Go to the "Actions" tab in your repository
2. Click on the workflow run you want to check
3. Click on the job name (e.g., "upload", "download", "list")
4. Expand the steps to see detailed logs

## Common Use Cases

### 1. Automated Backups
Set up automatic uploads when data files are updated:
- The upload workflow automatically triggers when `full-game-stats.csv` changes
- ZIP files are also automatically uploaded when they change

### 2. Data Synchronization
Download updated data files from Google Drive:
1. Someone updates a file in Google Drive
2. Use the download workflow to get the latest version
3. The file becomes available as a workflow artifact

### 3. File Management
Use the list workflow to:
- See what files are available in your Google Drive folder
- Find file IDs for downloads
- Check file sizes and modification dates

## Security Considerations

1. **File Artifacts**: Downloaded files are stored as GitHub Actions artifacts for 30 days
2. **Credentials**: Service account credentials are securely handled and cleaned up after each workflow
3. **Access Control**: Only repository collaborators with write access can trigger manual workflows
4. **Audit Trail**: All operations are logged in the Actions tab

## Troubleshooting

### Common Issues:

1. **"Error: Service account file not found"**
   - Check that `GOOGLE_DRIVE_CREDENTIALS` secret is set
   - Verify the JSON format is valid

2. **"Permission denied" errors**
   - Ensure the service account has access to the target folder
   - Check that the folder ID is correct

3. **"File not found" errors**
   - Verify the file path exists in the repository
   - Check file permissions

4. **Workflow doesn't trigger automatically**
   - Ensure you're pushing changes to the correct files (`full-game-stats.csv`, `*.zip`)
   - Check that the files actually changed in the commit

### Getting Help:

1. Check the workflow logs for detailed error messages
2. Verify your secrets are configured correctly
3. Test with the List workflow first to ensure basic connectivity
4. Refer to the main documentation in `GOOGLE_DRIVE_SECRETS_SETUP.md`

## Example Workflow Run

Here's what a successful upload looks like:

```
✓ Set up Python
✓ Install dependencies  
✓ Create service account credentials file
✓ Upload file to Google Drive
  Uploading file: full-game-stats.csv
  Target folder ID: 1ABC123XYZ456
  File uploaded successfully:
    Name: full-game-stats.csv
    ID: 1DEF789GHI012
    Link: https://drive.google.com/file/d/1DEF789GHI012/view
  Upload completed. File ID: 1DEF789GHI012
✓ Clean up credentials
```