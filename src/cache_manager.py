#!/usr/bin/env python3
"""
Cache Manager for FLBB Statistics

This module manages caching of raw HTML and JSON files for finished games
on remote storage (Google Drive, MyDevil.net, etc.) to avoid re-downloading 
them from the FLBB website.
"""

import os
import json
import zipfile
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .storage_helper import get_storage_backend


class CacheManager:
    """Manages caching of raw HTML and JSON files for finished games."""
    
    def __init__(self, data_root: str, scripts_root: str, 
                 storage_backend: Optional[str] = None):
        """
        Initialize the cache manager.
        
        Args:
            data_root: Root directory for data files
            scripts_root: Root directory for scripts
            storage_backend: Storage backend type ('gdrive', 'mydevil', 'local')
                           If None, reads from CACHE_STORAGE_BACKEND env var
        """
        self.data_root = Path(data_root)
        self.scripts_root = Path(scripts_root)
        self.storage = get_storage_backend(storage_backend)
        
        # Load configuration
        self.config = self._load_config()
        
        # Set up paths
        self.game_schedule_raw_dir = self.data_root / self.config['directories']['gameScheduleRaw']
        self.full_game_stats_raw_dir = self.data_root / self.config['directories']['fullGameStatsRaw']
        self.full_game_stats_output_dir = self.data_root / self.config['directories']['fullGameStatsOutput']
        self.games_db_path = self.data_root / self.config['files']['gamesDb']
        
        # Cache metadata
        self.cache_metadata_file = self.data_root / 'cache_metadata.json'
        self.cache_metadata = self._load_cache_metadata()
    
    def _load_config(self) -> dict:
        """Load configuration from config.json."""
        config_path = self.scripts_root / 'config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                'directories': {
                    'gameScheduleRaw': 'game-schedule-raw',
                    'fullGameStatsRaw': 'full-game-stats-raw',
                    'fullGameStatsOutput': 'full-game-stats-output'
                },
                'files': {
                    'gamesDb': 'gamesDB.json'
                }
            }
    
    def _load_cache_metadata(self) -> dict:
        """Load cache metadata from file."""
        if self.cache_metadata_file.exists():
            with open(self.cache_metadata_file, 'r') as f:
                return json.load(f)
        return {
            'last_updated': None,
            'cached_games': {},
            'drive_file_id': None
        }
    
    def _save_cache_metadata(self):
        """Save cache metadata to file."""
        with open(self.cache_metadata_file, 'w') as f:
            json.dump(self.cache_metadata, f, indent=2)
    
    def get_finished_games(self) -> List[Dict]:
        """Get list of finished games from gamesDB.json."""
        if not self.games_db_path.exists():
            return []
        
        with open(self.games_db_path, 'r') as f:
            games = json.load(f)
        
        # Filter for finished games
        finished_games = [g for g in games if g.get('GameStatus') == 'Finished']
        return finished_games
    
    def get_files_to_cache(self) -> Dict[str, List[Path]]:
        """
        Get list of files that should be cached for finished games.
        
        Returns:
            Dictionary with 'html' and 'json' keys containing lists of file paths
        """
        finished_games = self.get_finished_games()
        files_to_cache = {'html': [], 'json': []}
        
        for game in finished_games:
            game_id = game.get('GameId')
            division_name = game.get('GameDivisionName')
            
            if not game_id or not division_name:
                continue
            
            # HTML file path
            html_file = self.full_game_stats_raw_dir / division_name / f'full-game-stats-{game_id}.html'
            if html_file.exists():
                files_to_cache['html'].append(html_file)
            
            # JSON file path
            json_file = self.full_game_stats_output_dir / division_name / f'full-game-stats-{game_id}.json'
            if json_file.exists():
                files_to_cache['json'].append(json_file)
        
        return files_to_cache
    
    def create_cache_archive(self, output_path: Optional[Path] = None) -> Path:
        """
        Create a ZIP archive of all files that should be cached.
        
        Args:
            output_path: Path for the output ZIP file (optional)
            
        Returns:
            Path to the created ZIP file
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            season_id = self.config.get('seasonId', 'unknown')
            output_path = self.data_root / f'cache-{season_id}-{timestamp}.zip'
        
        files_to_cache = self.get_files_to_cache()
        
        print(f"Creating cache archive: {output_path}")
        print(f"  HTML files: {len(files_to_cache['html'])}")
        print(f"  JSON files: {len(files_to_cache['json'])}")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add HTML files
            for html_file in files_to_cache['html']:
                arcname = html_file.relative_to(self.data_root)
                zipf.write(html_file, arcname)
            
            # Add JSON files
            for json_file in files_to_cache['json']:
                arcname = json_file.relative_to(self.data_root)
                zipf.write(json_file, arcname)
            
            # Add cache metadata
            metadata = {
                'created': datetime.now().isoformat(),
                'season_id': self.config.get('seasonId', 'unknown'),
                'html_files_count': len(files_to_cache['html']),
                'json_files_count': len(files_to_cache['json'])
            }
            zipf.writestr('cache_info.json', json.dumps(metadata, indent=2))
        
        print(f"Cache archive created: {output_path}")
        print(f"  Archive size: {output_path.stat().st_size:,} bytes")
        
        return output_path
    
    def upload_cache_to_storage(self) -> Optional[str]:
        """
        Create and upload cache archive to remote storage.
        
        Returns:
            File ID/path of the uploaded archive or None on failure
        """
        try:
            # Create cache archive
            cache_archive = self.create_cache_archive()
            
            # Upload to storage
            print(f"Uploading cache to remote storage...")
            file_id = self.storage.upload_file(
                str(cache_archive),
                file_name=cache_archive.name
            )
            
            if file_id:
                # Update cache metadata
                self.cache_metadata['last_updated'] = datetime.now().isoformat()
                self.cache_metadata['storage_file_id'] = file_id
                self._save_cache_metadata()
                
                # Clean up local archive
                cache_archive.unlink()
                
                print(f"Cache uploaded successfully. File ID/path: {file_id}")
            
            return file_id
            
        except Exception as e:
            print(f"Error uploading cache to storage: {e}")
            return None
    
    def download_cache_from_storage(self, file_id: Optional[str] = None) -> bool:
        """
        Download and extract cache archive from remote storage.
        
        Args:
            file_id: File ID/path to download (uses latest from storage if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine which file to download
            if file_id is None:
                file_id = self._find_latest_cache_file()
            
            if file_id is None:
                print("No cache file found in remote storage")
                return False
            
            print(f"Downloading cache from remote storage (ID: {file_id})...")
            
            # Download to temporary location
            with tempfile.TemporaryDirectory() as tmpdir:
                cache_archive = Path(tmpdir) / 'cache.zip'
                success = self.storage.download_file(
                    file_id, 
                    output_path=tmpdir, 
                    file_name='cache.zip'
                )
                
                if not success:
                    return False
                
                # Extract archive
                print("Extracting cache archive...")
                with zipfile.ZipFile(cache_archive, 'r') as zipf:
                    zipf.extractall(self.data_root)
                
                # Read cache info
                cache_info_path = self.data_root / 'cache_info.json'
                if cache_info_path.exists():
                    with open(cache_info_path, 'r') as f:
                        cache_info = json.load(f)
                    print(f"Cache restored:")
                    print(f"  Created: {cache_info.get('created')}")
                    print(f"  Season: {cache_info.get('season_id')}")
                    print(f"  HTML files: {cache_info.get('html_files_count')}")
                    print(f"  JSON files: {cache_info.get('json_files_count')}")
                    cache_info_path.unlink()
            
            # Update metadata
            self.cache_metadata['storage_file_id'] = file_id
            self._save_cache_metadata()
            
            print("Cache download and extraction completed successfully")
            return True
            
        except Exception as e:
            print(f"Error downloading cache from storage: {e}")
            return False
    
    def _find_latest_cache_file(self) -> Optional[str]:
        """
        Find the latest cache file in remote storage.
        
        Returns:
            File ID/path of the latest cache file or None if not found
        """
        try:
            # First check metadata
            if self.cache_metadata.get('storage_file_id'):
                return self.cache_metadata['storage_file_id']
            
            # Otherwise search in storage
            file_id = self.storage.find_latest_file('cache-')
            
            if not files:
                return None
            
            if file_id:
                print(f"Found latest cache file (ID/path: {file_id})")
            
            return file_id
            
        except Exception as e:
            print(f"Error finding latest cache file: {e}")
            return None
    
    def get_cached_game_ids(self) -> Set[str]:
        """
        Get set of game IDs that are currently cached locally.
        
        Returns:
            Set of game IDs that have cached files
        """
        cached_ids = set()
        
        if self.full_game_stats_raw_dir.exists():
            for division_dir in self.full_game_stats_raw_dir.iterdir():
                if division_dir.is_dir():
                    for html_file in division_dir.glob('full-game-stats-*.html'):
                        # Extract game ID from filename
                        game_id = html_file.stem.replace('full-game-stats-', '')
                        cached_ids.add(game_id)
        
        return cached_ids


def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cache Manager for FLBB Statistics')
    parser.add_argument('action', choices=['upload', 'download', 'create', 'list-finished'],
                       help='Action to perform')
    parser.add_argument('--data-root', default='data',
                       help='Root directory for data files')
    parser.add_argument('--scripts-root', default='scripts',
                       help='Root directory for scripts')
    parser.add_argument('--storage', choices=['gdrive', 'mydevil', 'local'],
                       help='Storage backend (default: from CACHE_STORAGE_BACKEND env var)')
    parser.add_argument('--file-id', help='File ID/path for download')
    parser.add_argument('--output', '-o', help='Output path for cache archive')
    
    args = parser.parse_args()
    
    # Initialize cache manager
    cache_mgr = CacheManager(
        data_root=args.data_root,
        scripts_root=args.scripts_root,
        storage_backend=args.storage
    )
    
    try:
        if args.action == 'upload':
            file_id = cache_mgr.upload_cache_to_storage()
            if file_id:
                print(f"✓ Cache uploaded successfully. File ID/path: {file_id}")
                return 0
            else:
                print("✗ Failed to upload cache")
                return 1
        
        elif args.action == 'download':
            success = cache_mgr.download_cache_from_storage(args.file_id)
            if success:
                print("✓ Cache downloaded and extracted successfully")
                return 0
            else:
                print("✗ Failed to download cache")
                return 1
        
        elif args.action == 'create':
            output_path = Path(args.output) if args.output else None
            archive_path = cache_mgr.create_cache_archive(output_path)
            print(f"✓ Cache archive created: {archive_path}")
            return 0
        
        elif args.action == 'list-finished':
            finished_games = cache_mgr.get_finished_games()
            cached_ids = cache_mgr.get_cached_game_ids()
            
            print(f"Total finished games: {len(finished_games)}")
            print(f"Cached game files: {len(cached_ids)}")
            print(f"Missing cache files: {len(finished_games) - len(cached_ids)}")
            
            # Show sample of finished games
            if finished_games:
                print(f"\nSample finished games:")
                for game in finished_games[:5]:
                    game_id = game.get('GameId')
                    status = "✓ cached" if game_id in cached_ids else "✗ not cached"
                    print(f"  {game_id}: {game.get('GameDivisionName')} - {status}")
            
            return 0
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
