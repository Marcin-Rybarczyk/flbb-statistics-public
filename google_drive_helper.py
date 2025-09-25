#!/usr/bin/env python3
"""
Google Drive Helper for FLBB Statistics

This module provides functionality to upload files to Google Drive
using the service account authentication.
"""

import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = 'flbb-statistics-e9ab0e2a8b4c.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """
    Create and return a Google Drive service object.
    """
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
    parser.add_argument('action', choices=['upload', 'create-folder', 'list'], 
                       help='Action to perform')
    parser.add_argument('--file', '-f', help='File to upload')
    parser.add_argument('--folder-id', '-i', help='Folder ID')
    parser.add_argument('--folder-name', '-n', help='Folder name')
    parser.add_argument('--pattern', '-p', help='Name pattern for listing')
    
    args = parser.parse_args()
    
    try:
        if args.action == 'upload':
            if not args.file:
                print("Error: --file is required for upload")
                return 1
            
            file_id = upload_file_to_drive(args.file, args.folder_id)
            print(f"Upload completed. File ID: {file_id}")
        
        elif args.action == 'create-folder':
            if not args.folder_name:
                print("Error: --folder-name is required for create-folder")
                return 1
            
            folder_id = create_folder(args.folder_name, args.folder_id)
            print(f"Folder created. ID: {folder_id}")
        
        elif args.action == 'list':
            files = list_files_in_folder(args.folder_id, args.pattern)
            if files:
                print(f"Found {len(files)} files:")
                for file in files:
                    print(f"  {file['name']} (ID: {file['id']})")
            else:
                print("No files found.")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())