#!/usr/bin/env python3
"""
Test script for Cache Manager

This script tests the cache manager functionality without requiring Google Drive credentials.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache_manager import CacheManager


def create_test_data(test_data_root):
    """Create test data structure for testing."""
    print("Creating test data structure...")
    
    # Create directories
    data_root = Path(test_data_root)
    data_root.mkdir(exist_ok=True)
    
    scripts_root = data_root / "scripts"
    scripts_root.mkdir(exist_ok=True)
    
    # Create config.json
    config = {
        "seasonId": "2025-2026",
        "directories": {
            "gameScheduleRaw": "game-schedule-raw",
            "fullGameStatsRaw": "full-game-stats-raw",
            "fullGameStatsOutput": "full-game-stats-output"
        },
        "files": {
            "gamesDb": "gamesDB.json"
        }
    }
    
    import json
    with open(scripts_root / "config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    # Create sample gamesDB.json
    games_db = [
        {
            "GameId": "1001",
            "GameStatus": "Finished",
            "GameDivisionName": "division-1-hommes",
            "SeasonId": "2025-2026"
        },
        {
            "GameId": "1002",
            "GameStatus": "Finished",
            "GameDivisionName": "division-1-hommes",
            "SeasonId": "2025-2026"
        },
        {
            "GameId": "1003",
            "GameStatus": "NotStarted",
            "GameDivisionName": "division-1-hommes",
            "SeasonId": "2025-2026"
        }
    ]
    
    with open(data_root / "gamesDB.json", 'w') as f:
        json.dump(games_db, f, indent=2)
    
    # Create sample raw HTML files
    raw_dir = data_root / "full-game-stats-raw" / "division-1-hommes"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    for game_id in ["1001", "1002"]:
        html_file = raw_dir / f"full-game-stats-{game_id}.html"
        html_file.write_text(f"<html>Sample game {game_id}</html>")
    
    # Create sample JSON files
    output_dir = data_root / "full-game-stats-output" / "division-1-hommes"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for game_id in ["1001", "1002"]:
        json_file = output_dir / f"full-game-stats-{game_id}.json"
        json_file.write_text(json.dumps({"GameId": game_id, "test": True}))
    
    print(f"✓ Test data created in: {test_data_root}")
    return str(data_root), str(scripts_root)


def test_cache_manager():
    """Test cache manager functionality."""
    print("\n" + "="*60)
    print("Testing Cache Manager")
    print("="*60 + "\n")
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Test directory: {tmpdir}\n")
        
        # Create test data
        data_root, scripts_root = create_test_data(tmpdir)
        
        # Initialize cache manager with local storage for testing
        print("\n1. Initializing Cache Manager with local storage...")
        cache_mgr = CacheManager(
            data_root=data_root,
            scripts_root=scripts_root,
            storage_backend='local'
        )
        print("✓ Cache manager initialized")
        
        # Test: Get finished games
        print("\n2. Getting finished games...")
        finished_games = cache_mgr.get_finished_games()
        print(f"✓ Found {len(finished_games)} finished games")
        assert len(finished_games) == 2, "Expected 2 finished games"
        
        # Test: Get files to cache
        print("\n3. Getting files to cache...")
        files_to_cache = cache_mgr.get_files_to_cache()
        print(f"✓ HTML files to cache: {len(files_to_cache['html'])}")
        print(f"✓ JSON files to cache: {len(files_to_cache['json'])}")
        assert len(files_to_cache['html']) == 2, "Expected 2 HTML files"
        assert len(files_to_cache['json']) == 2, "Expected 2 JSON files"
        
        # Test: Get cached game IDs
        print("\n4. Getting cached game IDs...")
        cached_ids = cache_mgr.get_cached_game_ids()
        print(f"✓ Cached game IDs: {sorted(cached_ids)}")
        assert len(cached_ids) == 2, "Expected 2 cached games"
        assert "1001" in cached_ids, "Expected game 1001 to be cached"
        assert "1002" in cached_ids, "Expected game 1002 to be cached"
        
        # Test: Create cache archive
        print("\n5. Creating cache archive...")
        archive_path = cache_mgr.create_cache_archive()
        print(f"✓ Archive created: {archive_path}")
        assert archive_path.exists(), "Archive should exist"
        print(f"✓ Archive size: {archive_path.stat().st_size:,} bytes")
        
        # Test: Verify archive contents
        print("\n6. Verifying archive contents...")
        import zipfile
        with zipfile.ZipFile(archive_path, 'r') as zipf:
            files_in_archive = zipf.namelist()
            print(f"✓ Files in archive: {len(files_in_archive)}")
            
            # Check for expected files
            expected_files = [
                'full-game-stats-raw/division-1-hommes/full-game-stats-1001.html',
                'full-game-stats-raw/division-1-hommes/full-game-stats-1002.html',
                'full-game-stats-output/division-1-hommes/full-game-stats-1001.json',
                'full-game-stats-output/division-1-hommes/full-game-stats-1002.json',
                'cache_info.json'
            ]
            
            for expected_file in expected_files:
                # Normalize path separators
                normalized = expected_file.replace('/', os.sep)
                found = any(normalized in f or expected_file in f for f in files_in_archive)
                if found:
                    print(f"  ✓ {expected_file}")
                else:
                    print(f"  ✗ Missing: {expected_file}")
                    print(f"    Available files: {files_in_archive}")
        
        # Test: Extract and restore
        print("\n7. Testing cache extraction...")
        # Clear the cache directories
        shutil.rmtree(Path(data_root) / "full-game-stats-raw")
        shutil.rmtree(Path(data_root) / "full-game-stats-output")
        
        # Extract archive
        with zipfile.ZipFile(archive_path, 'r') as zipf:
            zipf.extractall(data_root)
        
        # Verify files were restored
        restored_cached_ids = cache_mgr.get_cached_game_ids()
        print(f"✓ Restored game IDs: {sorted(restored_cached_ids)}")
        assert len(restored_cached_ids) == 2, "Expected 2 restored games"
        
        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60 + "\n")


def main():
    """Run tests."""
    try:
        test_cache_manager()
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
