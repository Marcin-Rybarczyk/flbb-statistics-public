#!/usr/bin/env python3
"""
Storage Helper for FLBB Statistics

This module provides a unified interface for different storage backends
(Google Drive, MyDevil.net SFTP, local filesystem).
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
from abc import ABC, abstractmethod

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def upload_file(self, local_path: str, remote_name: Optional[str] = None) -> Optional[str]:
        """Upload a file to storage. Returns file ID/path or None on failure."""
        pass
    
    @abstractmethod
    def download_file(self, file_id: str, output_path: str, file_name: Optional[str] = None) -> bool:
        """Download a file from storage. Returns True on success."""
        pass
    
    @abstractmethod
    def list_files(self, name_pattern: Optional[str] = None) -> List[Dict]:
        """List files in storage. Returns list of file metadata."""
        pass
    
    @abstractmethod
    def find_latest_file(self, name_pattern: str) -> Optional[str]:
        """Find the latest file matching pattern. Returns file ID/path or None."""
        pass


class GoogleDriveStorage(StorageBackend):
    """Google Drive storage backend."""
    
    def __init__(self, folder_id: Optional[str] = None):
        self.folder_id = folder_id or os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        try:
            from src.google_drive_helper import (
                upload_file_to_drive,
                download_file_from_drive,
                list_files_in_folder
            )
            self.upload_func = upload_file_to_drive
            self.download_func = download_file_from_drive
            self.list_func = list_files_in_folder
        except ImportError as e:
            raise ImportError(f"Google Drive helper not available: {e}")
    
    def upload_file(self, local_path: str, remote_name: Optional[str] = None) -> Optional[str]:
        """Upload file to Google Drive."""
        try:
            return self.upload_func(local_path, self.folder_id, remote_name)
        except Exception as e:
            print(f"Error uploading to Google Drive: {e}")
            return None
    
    def download_file(self, file_id: str, output_path: str, file_name: Optional[str] = None) -> bool:
        """Download file from Google Drive."""
        try:
            self.download_func(file_id, output_path, file_name)
            return True
        except Exception as e:
            print(f"Error downloading from Google Drive: {e}")
            return False
    
    def list_files(self, name_pattern: Optional[str] = None) -> List[Dict]:
        """List files in Google Drive folder."""
        try:
            return self.list_func(self.folder_id, name_pattern)
        except Exception as e:
            print(f"Error listing Google Drive files: {e}")
            return []
    
    def find_latest_file(self, name_pattern: str) -> Optional[str]:
        """Find latest file in Google Drive."""
        files = self.list_files(name_pattern)
        if not files:
            return None
        files.sort(key=lambda x: x.get('createdTime', ''), reverse=True)
        return files[0]['id']


class MyDevilStorage(StorageBackend):
    """MyDevil.net SFTP storage backend."""
    
    def __init__(self, 
                 host: Optional[str] = None,
                 username: Optional[str] = None,
                 remote_path: Optional[str] = None,
                 ssh_key_path: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Initialize MyDevil.net storage.
        
        Args:
            host: MyDevil server hostname (e.g., 'panel77.mydevil.net')
            username: SSH username
            remote_path: Remote directory path for cache storage
            ssh_key_path: Path to SSH private key (preferred over password)
            password: SSH password (only if key not available)
        """
        self.host = host or os.getenv('MYDEVIL_HOST')
        self.username = username or os.getenv('MYDEVIL_USERNAME')
        self.remote_path = remote_path or os.getenv('MYDEVIL_CACHE_PATH', '~/cache')
        self.ssh_key_path = ssh_key_path or os.getenv('MYDEVIL_SSH_KEY')
        self.password = password or os.getenv('MYDEVIL_PASSWORD')
        
        if not self.host or not self.username:
            raise ValueError("MyDevil host and username are required")
        
        try:
            import paramiko
            self.paramiko = paramiko
        except ImportError:
            raise ImportError("paramiko is required for MyDevil.net storage. Install with: pip install paramiko")
    
    def _get_sftp_client(self):
        """Create and return SFTP client."""
        ssh = self.paramiko.SSHClient()
        ssh.set_missing_host_key_policy(self.paramiko.AutoAddPolicy())
        
        connect_kwargs = {
            'hostname': self.host,
            'username': self.username,
        }
        
        if self.ssh_key_path and os.path.exists(self.ssh_key_path):
            connect_kwargs['key_filename'] = self.ssh_key_path
        elif self.password:
            connect_kwargs['password'] = self.password
        else:
            raise ValueError("Either SSH key or password is required for MyDevil.net")
        
        ssh.connect(**connect_kwargs)
        sftp = ssh.open_sftp()
        
        # Ensure remote directory exists
        try:
            sftp.stat(self.remote_path)
        except IOError:
            sftp.mkdir(self.remote_path)
        
        return ssh, sftp
    
    def upload_file(self, local_path: str, remote_name: Optional[str] = None) -> Optional[str]:
        """Upload file to MyDevil.net via SFTP."""
        try:
            ssh, sftp = self._get_sftp_client()
            
            if not remote_name:
                remote_name = os.path.basename(local_path)
            
            remote_file_path = f"{self.remote_path}/{remote_name}"
            
            print(f"Uploading to MyDevil.net: {remote_file_path}")
            sftp.put(local_path, remote_file_path)
            
            sftp.close()
            ssh.close()
            
            print(f"✓ File uploaded successfully to MyDevil.net")
            return remote_file_path
            
        except Exception as e:
            print(f"Error uploading to MyDevil.net: {e}")
            return None
    
    def download_file(self, file_id: str, output_path: str, file_name: Optional[str] = None) -> bool:
        """Download file from MyDevil.net via SFTP."""
        try:
            ssh, sftp = self._get_sftp_client()
            
            # file_id is the remote path for MyDevil storage
            remote_file_path = file_id
            
            if not file_name:
                file_name = os.path.basename(remote_file_path)
            
            local_file_path = os.path.join(output_path, file_name)
            
            print(f"Downloading from MyDevil.net: {remote_file_path}")
            sftp.get(remote_file_path, local_file_path)
            
            sftp.close()
            ssh.close()
            
            print(f"✓ File downloaded successfully from MyDevil.net")
            return True
            
        except Exception as e:
            print(f"Error downloading from MyDevil.net: {e}")
            return False
    
    def list_files(self, name_pattern: Optional[str] = None) -> List[Dict]:
        """List files in MyDevil.net remote directory."""
        try:
            ssh, sftp = self._get_sftp_client()
            
            files = []
            for entry in sftp.listdir_attr(self.remote_path):
                if name_pattern and name_pattern not in entry.filename:
                    continue
                
                files.append({
                    'id': f"{self.remote_path}/{entry.filename}",
                    'name': entry.filename,
                    'size': str(entry.st_size),
                    'mtime': str(entry.st_mtime)
                })
            
            sftp.close()
            ssh.close()
            
            return files
            
        except Exception as e:
            print(f"Error listing MyDevil.net files: {e}")
            return []
    
    def find_latest_file(self, name_pattern: str) -> Optional[str]:
        """Find latest file in MyDevil.net storage."""
        files = self.list_files(name_pattern)
        if not files:
            return None
        files.sort(key=lambda x: float(x.get('mtime', 0)), reverse=True)
        return files[0]['id']


class LocalStorage(StorageBackend):
    """Local filesystem storage backend (for testing)."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or os.getenv('LOCAL_CACHE_PATH', './cache'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def upload_file(self, local_path: str, remote_name: Optional[str] = None) -> Optional[str]:
        """Copy file to local storage directory."""
        try:
            import shutil
            
            if not remote_name:
                remote_name = os.path.basename(local_path)
            
            dest_path = self.storage_path / remote_name
            shutil.copy2(local_path, dest_path)
            
            print(f"✓ File copied to local storage: {dest_path}")
            return str(dest_path)
            
        except Exception as e:
            print(f"Error copying to local storage: {e}")
            return None
    
    def download_file(self, file_id: str, output_path: str, file_name: Optional[str] = None) -> bool:
        """Copy file from local storage directory."""
        try:
            import shutil
            
            source_path = Path(file_id)
            
            if not file_name:
                file_name = source_path.name
            
            dest_path = Path(output_path) / file_name
            shutil.copy2(source_path, dest_path)
            
            print(f"✓ File copied from local storage: {dest_path}")
            return True
            
        except Exception as e:
            print(f"Error copying from local storage: {e}")
            return False
    
    def list_files(self, name_pattern: Optional[str] = None) -> List[Dict]:
        """List files in local storage directory."""
        try:
            files = []
            for file_path in self.storage_path.glob('*'):
                if file_path.is_file():
                    if name_pattern and name_pattern not in file_path.name:
                        continue
                    
                    stat = file_path.stat()
                    files.append({
                        'id': str(file_path),
                        'name': file_path.name,
                        'size': str(stat.st_size),
                        'mtime': str(stat.st_mtime)
                    })
            
            return files
            
        except Exception as e:
            print(f"Error listing local storage files: {e}")
            return []
    
    def find_latest_file(self, name_pattern: str) -> Optional[str]:
        """Find latest file in local storage."""
        files = self.list_files(name_pattern)
        if not files:
            return None
        files.sort(key=lambda x: float(x.get('mtime', 0)), reverse=True)
        return files[0]['id']


def get_storage_backend(backend_type: Optional[str] = None) -> StorageBackend:
    """
    Factory function to get the appropriate storage backend.
    
    Args:
        backend_type: Type of storage ('gdrive', 'mydevil', 'local')
                     If None, reads from CACHE_STORAGE_BACKEND env var
    
    Returns:
        StorageBackend instance
    """
    if backend_type is None:
        backend_type = os.getenv('CACHE_STORAGE_BACKEND', 'gdrive').lower()
    
    if backend_type == 'gdrive':
        return GoogleDriveStorage()
    elif backend_type == 'mydevil':
        return MyDevilStorage()
    elif backend_type == 'local':
        return LocalStorage()
    else:
        raise ValueError(f"Unknown storage backend: {backend_type}. Use 'gdrive', 'mydevil', or 'local'")


if __name__ == '__main__':
    # Simple CLI for testing
    import argparse
    
    parser = argparse.ArgumentParser(description='Storage Helper for FLBB Statistics')
    parser.add_argument('action', choices=['test', 'list'], help='Action to perform')
    parser.add_argument('--backend', choices=['gdrive', 'mydevil', 'local'], 
                       help='Storage backend to use')
    parser.add_argument('--pattern', help='File name pattern for listing')
    
    args = parser.parse_args()
    
    try:
        storage = get_storage_backend(args.backend)
        
        if args.action == 'test':
            print(f"✓ Successfully initialized {args.backend} storage backend")
            print(f"  Backend type: {type(storage).__name__}")
        
        elif args.action == 'list':
            files = storage.list_files(args.pattern)
            if files:
                print(f"Found {len(files)} files:")
                for f in files:
                    print(f"  {f['name']} (Size: {f.get('size', 'unknown')})")
            else:
                print("No files found")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
