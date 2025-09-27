#!/usr/bin/env python3
"""
Test script for Google Drive functionality

This script tests the Google Drive integration without requiring the full workflow.
"""

import os
import json
import tempfile
from google_drive_helper import get_drive_service, upload_file_to_drive, list_files_in_folder

def test_google_drive_connection():
    """Test if we can connect to Google Drive."""
    print("Testing Google Drive connection...")
    
    try:
        service = get_drive_service()
        print("✓ Successfully connected to Google Drive")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to Google Drive: {e}")
        return False

def test_folder_listing():
    """Test listing files in the configured folder."""
    print("Testing folder listing...")
    
    # Load config
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        folder_id = config.get("googleDrive", {}).get("folderId")
        if folder_id:
            try:
                files = list_files_in_folder(folder_id)
                print(f"✓ Successfully listed {len(files)} files in folder")
                return True
            except Exception as e:
                print(f"✗ Failed to list files: {e}")
                return False
        else:
            print("✗ No folder ID configured")
            return False
    else:
        print("✗ Config file not found")
        return False

def test_file_upload():
    """Test uploading a small test file."""
    print("Testing file upload...")
    
    # Create a temporary test file
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test file for Google Drive upload\n")
            f.write(f"Generated at: {os.popen('date').read().strip()}\n")
            test_file = f.name
        
        # Load config
        config_file = "config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            folder_id = config.get("googleDrive", {}).get("folderId")
            
            # Upload the file
            file_id = upload_file_to_drive(test_file, folder_id, "test-upload.txt")
            
            # Clean up
            os.unlink(test_file)
            
            print(f"✓ Successfully uploaded test file (ID: {file_id})")
            return True
        else:
            print("✗ Config file not found")
            return False
            
    except Exception as e:
        print(f"✗ Failed to upload test file: {e}")
        try:
            os.unlink(test_file)
        except:
            pass
        return False

def main():
    """Run all tests."""
    print("Google Drive Integration Test")
    print("=" * 40)
    
    tests = [
        test_google_drive_connection,
        test_folder_listing,
        test_file_upload
    ]
    
    results = []
    for test in tests:
        print()
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print()
    print("=" * 40)
    print("Test Results:")
    print(f"Connection test: {'PASS' if results[0] else 'FAIL'}")
    print(f"Folder listing: {'PASS' if results[1] else 'FAIL'}")
    print(f"File upload: {'PASS' if results[2] else 'FAIL'}")
    
    if all(results):
        print("\n✓ All tests passed! Google Drive integration is working.")
        return 0
    else:
        print("\n✗ Some tests failed. Check configuration and network connectivity.")
        return 1

if __name__ == '__main__':
    exit(main())