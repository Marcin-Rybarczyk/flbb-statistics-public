#!/usr/bin/env python3
"""
Post-processing script for FLBB Statistics

This script handles the post-processing workflow after PowerShell scripts have downloaded data:
1. Generate full-game-stats.csv from JSON data
2. Create archive with raw data
3. Upload to Google Drive

Usage:
    python post_process.py [--skip-csv] [--skip-upload] [--config CONFIG_FILE]
"""

import os
import sys
import json
import zipfile
import argparse
from datetime import datetime
from pathlib import Path

data_root = Path(__file__).parent.parent / "data"
print(f"Data root directory: {data_root}")

archive_root = Path(__file__).parent.parent / "archives"
if not os.path.exists(archive_root):
    os.makedirs(archive_root)

# Check for required dependencies first
def check_dependencies():
    """Check if all required Python packages are installed."""
    missing_packages = []
    
    try:
        import pandas
    except ImportError:
        missing_packages.append('pandas')
    
    try:
        from googleapiclient.discovery import build
    except ImportError:
        missing_packages.append('google-api-python-client')
    
    if missing_packages:
        print("ERROR: Missing required Python packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nTo fix this issue, run:")
        print("  pip install -r requirements.txt")
        print("\nOr install individual packages:")
        for package in missing_packages:
            print(f"  pip install {package}")
        return False
    
    return True

# Check dependencies before importing other modules
if not check_dependencies():
    sys.exit(1)

# Add the root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import our utilities
from src.utils import create_csv_from_json_data, load_data_from_directories
from src.google_drive_helper import upload_file_to_drive

# Try to import MongoDB helper (optional dependency)
try:
    from src.mongodb_helper import (
        is_mongodb_enabled, 
        is_mongodb_available, 
        store_json_data_to_mongodb
    )
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("Note: MongoDB helper not available. MongoDB storage disabled.")

def load_config(config_file="config.json"):
    """Load configuration from JSON file."""
    if not os.path.exists(config_file):
        print(f"Warning: Config file {config_file} not found, using defaults")
        return {}
    
    with open(config_file, 'r') as f:
        return json.load(f)

def generate_csv_from_json(config):
    """Generate full-game-stats.csv from JSON files."""
    print("Starting CSV generation from JSON files...")

    # display current directory
    print(f"Current directory: {os.getcwd()}")

    # Create output directory if it doesn't exist
    output_dir = data_root / config.get("directories", {}).get("fullGameStatsOutput", "full-game-stats-output")
    csv_filepath = data_root / config.get("files", {}).get("outputCsv", "full-game-stats.csv")
    
    if not os.path.exists(output_dir):
        print(f"Error: Output directory {output_dir} not found")
        print("Please run extract-game.ps1 first to generate JSON files")
        return False
    
    return create_csv_from_json_data(output_dir, csv_filepath)

def create_archive(config):
    """Create a zip archive with raw data."""
    print("Creating archive with raw data...")
    
    # Get directories from config
    game_schedule_dir = data_root / config.get("directories", {}).get("gameScheduleRaw", "game-schedule-raw")
    full_game_stats_dir = data_root / config.get("directories", {}).get("fullGameStatsRaw", "full-game-stats-raw")

    # Create season-aware filename with timestamp
    season_id = config.get("seasonId", "unknown")
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    if season_id != "unknown":
        zip_filepath = archive_root / f"raw-data-{season_id}-{timestamp}.zip"
    else:
        zip_filepath = archive_root / f"raw-data-{timestamp}.zip"

    print(f"Creating archive: {zip_filepath}")
    
    try:
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add files from game schedule directory
            if os.path.exists(game_schedule_dir):
                print(f"Adding files from {game_schedule_dir}...")
                for root, dirs, files in os.walk(game_schedule_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path)
                        zipf.write(file_path, arcname)
            else:
                print(f"Warning: Directory {game_schedule_dir} not found")
            
            # Add files from full game stats directory
            if os.path.exists(full_game_stats_dir):
                print(f"Adding files from {full_game_stats_dir}...")
                for root, dirs, files in os.walk(full_game_stats_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path)
                        zipf.write(file_path, arcname)
            else:
                print(f"Warning: Directory {full_game_stats_dir} not found")
            
            # Add CSV file if it exists
            csv_filepath = data_root / config.get("files", {}).get("outputCsv", "full-game-stats.csv")
            if os.path.exists(csv_filepath):
                print(f"Adding {csv_filepath}...")
                zipf.write(csv_filepath)
            
            # Add database files if they exist
            games_db = data_root    /    config.get("files", {}).get("gamesDb", "gamesDB.json")
            if os.path.exists(games_db):
                print(f"Adding {games_db}...")
                zipf.write(games_db)
            
            schedule_db = data_root / config.get("files", {}).get("gameScheduleDb", "gameScheduleDB.json")
            if os.path.exists(schedule_db):
                print(f"Adding {schedule_db}...")
                zipf.write(schedule_db)
        
        print(f"Successfully created archive: {zip_filepath}")
        return zip_filepath
        
    except Exception as e:
        print(f"Error creating archive: {e}")
        return None

def upload_to_google_drive(file_path, config):
    """Upload file to Google Drive."""
    print(f"Uploading {file_path} to Google Drive...")
    
    # Check if Google Drive is enabled
    drive_config = config.get("googleDrive", {})
    if not drive_config.get("enabled", False):
        print("Google Drive upload is disabled in configuration")
        return False
    
    folder_id = drive_config.get("folderId")
    
    try:
        file_id = upload_file_to_drive(file_path, folder_id)
        print(f"Successfully uploaded to Google Drive. File ID: {file_id}")
        return True
        
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
        print("Note: This might be due to network restrictions or authentication issues")
        return False

def store_to_mongodb(config):
    """Store JSON data to MongoDB."""
    print("Storing data to MongoDB...")
    
    # Check if MongoDB is available and enabled
    if not MONGODB_AVAILABLE:
        print("MongoDB helper not available. Skipping MongoDB storage.")
        return False
    
    if not is_mongodb_available():
        print("pymongo package not installed. Skipping MongoDB storage.")
        print("To enable MongoDB: pip install pymongo")
        return False
    
    # Check if MongoDB is enabled in config
    mongo_config = config.get("mongodb", {})
    config_enabled = mongo_config.get("enabled", False)
    
    # Also check environment variable
    import os
    env_enabled = os.environ.get('MONGODB_ENABLED', '').lower() in ['true', '1', 'yes']
    
    if not config_enabled and not env_enabled:
        print("MongoDB storage is disabled in configuration")
        return False
    
    # Load JSON data from output directory
    output_dir = data_root / config.get("directories", {}).get("fullGameStatsOutput", "full-game-stats-output")
    
    if not os.path.exists(output_dir):
        print(f"Error: Output directory {output_dir} not found")
        return False
    
    print(f"Loading JSON files from {output_dir}...")
    all_data = load_data_from_directories(output_dir)
    
    if not all_data:
        print("No JSON data found to store")
        return False
    
    print(f"Found {len(all_data)} game records to store")
    
    # Get MongoDB configuration
    connection_string = mongo_config.get("connectionString") or os.environ.get('MONGODB_URI')
    database_name = mongo_config.get("database") or os.environ.get('MONGODB_DATABASE')
    collection_name = mongo_config.get("collections", {}).get("games", "games")
    
    # Store data to MongoDB
    try:
        success = store_json_data_to_mongodb(
            all_data,
            connection_string=connection_string,
            database_name=database_name,
            collection_name=collection_name
        )
        
        if success:
            print("✅ Successfully stored data to MongoDB")
        else:
            print("⚠️  MongoDB storage completed with some errors")
        
        return success
        
    except Exception as e:
        print(f"Error storing data to MongoDB: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Post-process FLBB Statistics data')
    parser.add_argument('--skip-csv', action='store_true', 
                       help='Skip CSV generation step')
    parser.add_argument('--skip-upload', action='store_true', 
                       help='Skip Google Drive upload step')
    parser.add_argument('--skip-mongodb', action='store_true',
                       help='Skip MongoDB storage step')
    parser.add_argument('--mongodb-only', action='store_true',
                       help='Only store data to MongoDB, skip other steps')
    parser.add_argument('--config', default='config.json', 
                       help='Configuration file path')
    parser.add_argument('--archive-only', action='store_true',
                       help='Only create archive, skip CSV generation and upload')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    success = True
    
    # MongoDB-only mode
    if args.mongodb_only:
        print("\n" + "="*60)
        print("MongoDB-only mode: Storing data to MongoDB")
        print("="*60 + "\n")
        if not store_to_mongodb(config):
            print("MongoDB storage failed")
            return 1
        print("\n" + "="*60)
        print("MongoDB storage completed successfully!")
        return 0
    
    # Step 1: Generate CSV from JSON files
    if not args.skip_csv and not args.archive_only:
        if not generate_csv_from_json(config):
            print("CSV generation failed")
            success = False
    
    # Step 2: Store to MongoDB (if enabled)
    if not args.skip_mongodb and not args.archive_only:
        print("\n" + "="*60)
        store_to_mongodb(config)  # Don't fail on MongoDB errors
    
    # Step 3: Create archive
    print("\n" + "="*60)
    zip_filepath = create_archive(config)
    if not zip_filepath:
        print("Archive creation failed")
        success = False
    
    # Step 4: Upload to Google Drive
    if zip_filepath and not args.skip_upload and not args.archive_only:
        print("\n" + "="*60)
        if not upload_to_google_drive(zip_filepath, config):
            print("Google Drive upload failed")
            # Don't mark as failure since network might not be available
    
    if success:
        print("\n" + "="*60)
        print("Post-processing completed successfully!")
        if zip_filepath:
            print(f"Archive created: {zip_filepath}")
    else:
        print("\nPost-processing completed with errors")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())