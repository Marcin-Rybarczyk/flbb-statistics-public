# Google Drive Secrets Setup for GitHub Actions

This document provides detailed instructions for setting up Google Drive API access and storing secret values in GitHub Secrets.

## Prerequisites

1. Google Cloud Console account
2. Repository admin access for GitHub Secrets management
3. Google Drive folder where files will be stored

## Step 1: Create Google Cloud Project and Enable Drive API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

## Step 2: Create Service Account

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - **Name**: `flbb-statistics-github-actions`
   - **Description**: `Service account for FLBB Statistics GitHub Actions`
4. Click "Create and Continue"
5. Skip role assignment (click "Continue")
6. Skip user access (click "Done")

## Step 3: Generate Service Account Key

1. In the Credentials page, find your service account
2. Click on the service account email
3. Go to the "Keys" tab
4. Click "Add Key" > "Create new key"
5. Select "JSON" format and click "Create"
6. The JSON file will download automatically - **keep this secure!**

## Step 4: Configure Google Drive Access

1. Open the downloaded JSON file and copy the `client_email` value
2. Go to Google Drive in your browser
3. Navigate to the folder where you want to store files
4. Right-click the folder and select "Share"
5. Add the service account email (from step 1) with "Editor" permissions
6. Copy the folder ID from the URL (e.g., in `https://drive.google.com/drive/folders/1ABC123XYZ`, the ID is `1ABC123XYZ`)

## Step 5: Store Secrets in GitHub

1. Go to your GitHub repository
2. Navigate to "Settings" > "Secrets and variables" > "Actions"
3. Add the following repository secrets:

### Required Secrets:

#### `GOOGLE_DRIVE_CREDENTIALS`
- **Value**: The entire contents of the downloaded JSON service account key file
- **Description**: Service account credentials for Google Drive API access
- **Usage**: Used by GitHub Actions to authenticate with Google Drive

#### `GOOGLE_DRIVE_FOLDER_ID`  
- **Value**: The Google Drive folder ID where files should be stored
- **Description**: Target folder ID for file uploads
- **Usage**: Specifies the destination folder for uploads

### Optional Secrets:

#### `GOOGLE_DRIVE_SERVICE_ACCOUNT_EMAIL`
- **Value**: The service account email address (from the JSON file)
- **Description**: Service account email for logging/debugging purposes
- **Usage**: Can be used for verification in GitHub Actions

## Step 6: Verify Setup

You can test the setup by running the GitHub Actions workflows or by creating a temporary JSON file locally:

```bash
# Create a temporary service account file for testing
echo '${{ secrets.GOOGLE_DRIVE_CREDENTIALS }}' > temp-service-account.json

# Test connection
python3 google_drive_helper.py list --folder-id ${{ secrets.GOOGLE_DRIVE_FOLDER_ID }}

# Clean up
rm temp-service-account.json
```

## Security Best Practices

1. **Never commit service account keys to the repository**
2. **Use repository secrets instead of environment secrets when possible**
3. **Regularly rotate service account keys (recommended every 90 days)**
4. **Monitor service account usage in Google Cloud Console**
5. **Use minimal permissions (only Google Drive access needed)**

## Troubleshooting

### Common Issues:

1. **"Service account file not found"**
   - Ensure `GOOGLE_DRIVE_CREDENTIALS` secret is set correctly
   - Verify the JSON format is valid

2. **"Permission denied" errors**
   - Check that the service account email has access to the target folder
   - Verify the folder ID is correct

3. **"API not enabled" errors**
   - Ensure Google Drive API is enabled in Google Cloud Console
   - Check that you're using the correct project

4. **"Invalid credentials" errors**
   - Verify the service account key hasn't expired
   - Ensure the JSON content is complete and valid

## GitHub Actions Environment Variables

The following environment variables are automatically available in GitHub Actions:

- `GOOGLE_DRIVE_CREDENTIALS`: Service account JSON credentials
- `GOOGLE_DRIVE_FOLDER_ID`: Target folder ID
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_EMAIL`: Service account email (optional)

## Example Usage in GitHub Actions

```yaml
steps:
  - name: Setup Google Drive credentials
    run: echo '${{ secrets.GOOGLE_DRIVE_CREDENTIALS }}' > service-account.json
    
  - name: Upload file to Google Drive
    run: |
      python3 google_drive_helper.py upload \
        --file myfile.csv \
        --folder-id ${{ secrets.GOOGLE_DRIVE_FOLDER_ID }}
    env:
      GOOGLE_APPLICATION_CREDENTIALS: service-account.json
      
  - name: Cleanup credentials
    run: rm -f service-account.json
```

## Support

For issues related to:
- **Google Cloud setup**: Check [Google Cloud documentation](https://cloud.google.com/docs)
- **Google Drive API**: Check [Google Drive API documentation](https://developers.google.com/drive/api)
- **GitHub Secrets**: Check [GitHub documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)