#!/usr/bin/env python3
"""
Export CSV Game Data to MongoDB

This script exports basketball game statistics from CSV files to MongoDB database.
It can export both from full-game-stats.csv and from JSON files in full-game-stats-output directory.

Usage:
    # Export from CSV file
    python scripts/export_csv_to_mongodb.py --source csv
    
    # Export from JSON files
    python scripts/export_csv_to_mongodb.py --source json
    
    # Export from both (default)
    python scripts/export_csv_to_mongodb.py
    
    # Specify custom MongoDB connection
    python scripts/export_csv_to_mongodb.py --uri mongodb://localhost:27017/ --database my-stats

Requirements:
    - pymongo installed (pip install pymongo)
    - MongoDB running (local or Atlas)
    - MONGODB_ENABLED=true environment variable (or use --force flag)
"""

import os
import sys
import argparse
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mongodb_helper import (
    is_mongodb_available,
    is_mongodb_enabled,
    MongoDBHelper
)
from src.utils import (
    load_data_from_directories,
    CSV_FILEPATH,
    FULL_GAME_STATS_OUTPUT_DIR
)
import pandas as pd


def export_csv_to_mongodb(csv_path, mongo_uri=None, database_name=None, collection_name='games', force=False):
    """
    Export data from CSV file to MongoDB.
    
    Args:
        csv_path (str): Path to CSV file
        mongo_uri (str, optional): MongoDB connection string
        database_name (str, optional): Database name
        collection_name (str): Collection name (default: 'games')
        force (bool): Force export even if MongoDB not enabled
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if MongoDB is available
    if not is_mongodb_available():
        print("❌ Error: pymongo is not installed")
        print("Install with: pip install pymongo")
        return False
    
    # Check if enabled (unless forced)
    if not force and not is_mongodb_enabled():
        print("❌ Error: MongoDB is not enabled")
        print("Set MONGODB_ENABLED=true or use --force flag")
        return False
    
    # Check if CSV file exists
    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found: {csv_path}")
        return False
    
    try:
        # Load CSV data
        print(f"Loading data from {csv_path}...")
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} records from CSV")
        
        if df.empty:
            print("⚠️  Warning: CSV file is empty")
            return False
        
        # Convert DataFrame to list of dictionaries
        games_data = df.to_dict('records')
        
        # Connect to MongoDB
        print("Connecting to MongoDB...")
        mongo = MongoDBHelper(mongo_uri, database_name)
        if not mongo.connect():
            print("❌ Error: Failed to connect to MongoDB")
            return False
        
        # Store data in batch
        print(f"Storing {len(games_data)} games to MongoDB collection '{collection_name}'...")
        stats = mongo.store_games_batch(games_data, collection_name)
        
        print("\n" + "="*60)
        print("Export completed!")
        print("="*60)
        print(f"✅ Inserted: {stats['inserted']}")
        print(f"🔄 Updated: {stats['updated']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"📊 Total: {len(games_data)}")
        print("="*60)
        
        # Create indexes
        print("\nCreating indexes for better performance...")
        mongo.create_indexes(collection_name)
        
        # Get final count
        total_count = mongo.get_games_count(collection_name)
        print(f"\n✅ MongoDB collection '{collection_name}' now contains {total_count} games")
        
        mongo.disconnect()
        return stats['failed'] == 0
        
    except Exception as e:
        print(f"❌ Error exporting to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_json_to_mongodb(json_dir, mongo_uri=None, database_name=None, collection_name='games', force=False):
    """
    Export data from JSON files to MongoDB.
    
    Args:
        json_dir (str): Directory containing JSON files
        mongo_uri (str, optional): MongoDB connection string
        database_name (str, optional): Database name
        collection_name (str): Collection name (default: 'games')
        force (bool): Force export even if MongoDB not enabled
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if MongoDB is available
    if not is_mongodb_available():
        print("❌ Error: pymongo is not installed")
        print("Install with: pip install pymongo")
        return False
    
    # Check if enabled (unless forced)
    if not force and not is_mongodb_enabled():
        print("❌ Error: MongoDB is not enabled")
        print("Set MONGODB_ENABLED=true or use --force flag")
        return False
    
    # Check if directory exists
    if not os.path.exists(json_dir):
        print(f"❌ Error: Directory not found: {json_dir}")
        return False
    
    try:
        # Load JSON data
        print(f"Loading JSON files from {json_dir}...")
        games_data = load_data_from_directories(json_dir)
        
        if not games_data:
            print("⚠️  Warning: No JSON files found")
            return False
        
        print(f"Loaded {len(games_data)} records from JSON files")
        
        # Connect to MongoDB
        print("Connecting to MongoDB...")
        mongo = MongoDBHelper(mongo_uri, database_name)
        if not mongo.connect():
            print("❌ Error: Failed to connect to MongoDB")
            return False
        
        # Store data in batch
        print(f"Storing {len(games_data)} games to MongoDB collection '{collection_name}'...")
        stats = mongo.store_games_batch(games_data, collection_name)
        
        print("\n" + "="*60)
        print("Export completed!")
        print("="*60)
        print(f"✅ Inserted: {stats['inserted']}")
        print(f"🔄 Updated: {stats['updated']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"📊 Total: {len(games_data)}")
        print("="*60)
        
        # Create indexes
        print("\nCreating indexes for better performance...")
        mongo.create_indexes(collection_name)
        
        # Get final count
        total_count = mongo.get_games_count(collection_name)
        print(f"\n✅ MongoDB collection '{collection_name}' now contains {total_count} games")
        
        mongo.disconnect()
        return stats['failed'] == 0
        
    except Exception as e:
        print(f"❌ Error exporting to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to parse arguments and run export."""
    parser = argparse.ArgumentParser(
        description='Export basketball game data from CSV/JSON to MongoDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export from CSV file
  python scripts/export_csv_to_mongodb.py --source csv
  
  # Export from JSON files
  python scripts/export_csv_to_mongodb.py --source json
  
  # Export from both sources (default)
  python scripts/export_csv_to_mongodb.py
  
  # Force export even if MongoDB not enabled
  python scripts/export_csv_to_mongodb.py --force
  
  # Use custom MongoDB connection
  python scripts/export_csv_to_mongodb.py --uri mongodb://localhost:27017/ --database my-stats
        """
    )
    
    parser.add_argument('--source', 
                       choices=['csv', 'json', 'both'],
                       default='both',
                       help='Data source to export (default: both)')
    
    parser.add_argument('--csv-path',
                       default=CSV_FILEPATH,
                       help=f'Path to CSV file (default: {CSV_FILEPATH})')
    
    parser.add_argument('--json-dir',
                       default=FULL_GAME_STATS_OUTPUT_DIR,
                       help=f'Directory with JSON files (default: {FULL_GAME_STATS_OUTPUT_DIR})')
    
    parser.add_argument('--uri',
                       help='MongoDB connection string (default: from env MONGODB_URI)')
    
    parser.add_argument('--database',
                       help='MongoDB database name (default: from env MONGODB_DATABASE)')
    
    parser.add_argument('--collection',
                       default='games',
                       help='MongoDB collection name (default: games)')
    
    parser.add_argument('--force',
                       action='store_true',
                       help='Force export even if MONGODB_ENABLED is not set')
    
    args = parser.parse_args()
    
    # Print header
    print("="*60)
    print("CSV/JSON to MongoDB Export Tool")
    print("="*60)
    print(f"Source: {args.source}")
    print(f"Collection: {args.collection}")
    if args.uri:
        print(f"MongoDB URI: {args.uri}")
    if args.database:
        print(f"Database: {args.database}")
    print("="*60)
    print()
    
    success = True
    
    # Export from CSV
    if args.source in ['csv', 'both']:
        print("\n📄 Exporting from CSV...")
        print("-" * 60)
        if not export_csv_to_mongodb(
            args.csv_path,
            args.uri,
            args.database,
            args.collection,
            args.force
        ):
            success = False
            if args.source == 'csv':
                sys.exit(1)
    
    # Export from JSON
    if args.source in ['json', 'both']:
        print("\n📁 Exporting from JSON files...")
        print("-" * 60)
        if not export_json_to_mongodb(
            args.json_dir,
            args.uri,
            args.database,
            args.collection,
            args.force
        ):
            success = False
            if args.source == 'json':
                sys.exit(1)
    
    # Final summary
    print("\n" + "="*60)
    if success:
        print("✅ All exports completed successfully!")
    else:
        print("⚠️  Some exports failed - check messages above")
    print("="*60)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
