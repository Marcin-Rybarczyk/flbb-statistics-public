#!/usr/bin/env python3
"""
Google Drive Helper for FLBB Statistics

This module provides functionality to upload files to Google Drive
using the service account authentication.
"""

import os
import json
import tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account
import io

SERVICE_ACCOUNT_FILE = 'flbb-statistics-e9ab0e2a8b4c.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """
    Create and return a Google Drive service object.
    Supports both local service account file and environment variable credentials.
    """
    # Try to use environment variable first (for CI/CD)
    credentials_json = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
    if credentials_json:
        try:
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info, scopes=SCOPES
            )
            service = build('drive', 'v3', credentials=credentials)
            return service
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Invalid credentials in environment variable: {e}")
            print("Falling back to local service account file...")
    
    # Fallback to local service account file
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    
    service = build('drive', 'v3', credentials=credentials)
    return service

def upload_file_to_drive(file_path, folder_id=None, file_name=None):
    """
    Upload a file to Google Drive.
    
    Args:
        file_path (str): Path to the file to upload
        folder_id (str, optional): ID of the folder to upload to
        file_name (str, optional): Name for the file in Drive (defaults to filename)
    
    Returns:
        str: File ID of the uploaded file
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    service = get_drive_service()
    
    if not file_name:
        file_name = os.path.basename(file_path)
    
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    media = MediaFileUpload(file_path, resumable=True)
    
    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()
        
        print(f"File uploaded successfully:")
        print(f"  Name: {file.get('name')}")
        print(f"  ID: {file.get('id')}")
        print(f"  Link: {file.get('webViewLink')}")
        
        return file.get('id')
    
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise

def download_file_from_drive(file_id, output_path=None, file_name=None):
    """
    Download a file from Google Drive.
    
    Args:
        file_id (str): ID of the file to download
        output_path (str, optional): Directory to save the file (defaults to current directory)
        file_name (str, optional): Name for the downloaded file (defaults to original name)
    
    Returns:
        str: Path to the downloaded file
    """
    service = get_drive_service()
    
    try:
        # Get file metadata
        file_metadata = service.files().get(fileId=file_id).execute()
        original_name = file_metadata.get('name', 'downloaded_file')
        
        if not file_name:
            file_name = original_name
        
        if not output_path:
            output_path = '.'
        
        full_path = os.path.join(output_path, file_name)
        
        # Download file content
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%")
        
        # Write to file
        with open(full_path, 'wb') as f:
            f.write(fh.getvalue())
        
        print(f"File downloaded successfully:")
        print(f"  Original name: {original_name}")
        print(f"  Saved as: {full_path}")
        print(f"  Size: {len(fh.getvalue())} bytes")
        
        return full_path
    
    except Exception as e:
        print(f"Error downloading file: {e}")
        raise

def create_folder(folder_name, parent_folder_id=None):
    """
    Create a folder in Google Drive.
    
    Args:
        folder_name (str): Name of the folder to create
        parent_folder_id (str, optional): ID of the parent folder
    
    Returns:
        str: Folder ID of the created folder
    """
    service = get_drive_service()
    
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]
    
    try:
        folder = service.files().create(
            body=file_metadata,
            fields='id,name'
        ).execute()
        
        print(f"Folder created successfully:")
        print(f"  Name: {folder.get('name')}")
        print(f"  ID: {folder.get('id')}")
        
        return folder.get('id')
    
    except Exception as e:
        print(f"Error creating folder: {e}")
        raise

def list_files_in_folder(folder_id=None, name_pattern=None):
    """
    List files in a Google Drive folder.
    
    Args:
        folder_id (str, optional): ID of the folder to list (root if None)
        name_pattern (str, optional): Pattern to filter files by name
    
    Returns:
        list: List of file dictionaries
    """
    service = get_drive_service()
    
    query = []
    if folder_id:
        query.append(f"'{folder_id}' in parents")
    if name_pattern:
        query.append(f"name contains '{name_pattern}'")
    
    query_str = " and ".join(query) if query else None
    
    try:
        results = service.files().list(
            q=query_str,
            fields="files(id,name,createdTime,size,mimeType)"
        ).execute()
        
        files = results.get('files', [])
        return files
    
    except Exception as e:
        print(f"Error listing files: {e}")
        raise

def main():
    """
    Main function for command line usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Drive Helper for FLBB Statistics')
    parser.add_argument('action', choices=['upload', 'download', 'create-folder', 'list'], 
                       help='Action to perform')
    parser.add_argument('--file', '-f', help='File to upload')
    parser.add_argument('--file-id', help='File ID for download')
    parser.add_argument('--output-path', '-o', help='Output directory for downloads')
    parser.add_argument('--output-name', help='Name for downloaded file')
    parser.add_argument('--folder-id', '-i', help='Folder ID')
    parser.add_argument('--folder-name', '-n', help='Folder name')
    parser.add_argument('--pattern', '-p', help='Name pattern for listing')
    
    args = parser.parse_args()
    
    try:
        if args.action == 'upload':
            if not args.file:
                print("Error: --file is required for upload")
                return 1
            
            # Use environment variable for folder ID if not provided
            folder_id = args.folder_id or os.getenv('GOOGLE_DRIVE_FOLDER_ID')
            
            file_id = upload_file_to_drive(args.file, folder_id)
            print(f"Upload completed. File ID: {file_id}")
        
        elif args.action == 'download':
            if not args.file_id:
                print("Error: --file-id is required for download")
                return 1
            
            file_path = download_file_from_drive(
                args.file_id, 
                args.output_path, 
                args.output_name
            )
            print(f"Download completed. File saved: {file_path}")
        
        elif args.action == 'create-folder':
            if not args.folder_name:
                print("Error: --folder-name is required for create-folder")
                return 1
            
            folder_id = create_folder(args.folder_name, args.folder_id)
            print(f"Folder created. ID: {folder_id}")
        
        elif args.action == 'list':
            # Use environment variable for folder ID if not provided
            folder_id = args.folder_id or os.getenv('GOOGLE_DRIVE_FOLDER_ID')
            
            files = list_files_in_folder(folder_id, args.pattern)
            if files:
                print(f"Found {len(files)} files:")
                for file in files:
                    size = file.get('size', 'Unknown')
                    if size != 'Unknown':
                        size = f"{int(size):,} bytes"
                    print(f"  {file['name']} (ID: {file['id']}, Size: {size})")
            else:
                print("No files found.")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())