#!/usr/bin/env python3
"""
Test script for MongoDB data source functionality

This script tests the ability of the Flask app to load data from MongoDB
as an alternative to CSV files.

Usage:
    python tests/test_mongodb_data_source.py
    python tests/test_mongodb_data_source.py --setup-test-data
"""

import os
import sys
import argparse
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mongodb_helper import (
    is_mongodb_available,
    is_mongodb_enabled,
    MongoDBHelper
)
from src.utils import (
    get_data_source_preference,
    load_game_data,
    load_game_data_from_mongodb_source,
    DATA_SOURCE_CSV,
    DATA_SOURCE_MONGODB,
    DATA_SOURCE_AUTO
)


def test_data_source_configuration():
    """Test data source configuration reading."""
    print("="*60)
    print("Testing Data Source Configuration")
    print("="*60)
    
    # Test default (should be auto)
    pref = get_data_source_preference()
    print(f"Default preference: {pref}")
    assert pref in [DATA_SOURCE_CSV, DATA_SOURCE_MONGODB, DATA_SOURCE_AUTO], \
        f"Invalid data source preference: {pref}"
    print(f"✅ Data source preference is valid")
    
    # Test environment variable override
    old_value = os.environ.get('DATA_SOURCE')
    
    os.environ['DATA_SOURCE'] = 'csv'
    pref = get_data_source_preference()
    assert pref == DATA_SOURCE_CSV, f"Expected 'csv', got '{pref}'"
    print(f"✅ Environment variable override works (csv)")
    
    os.environ['DATA_SOURCE'] = 'mongodb'
    pref = get_data_source_preference()
    assert pref == DATA_SOURCE_MONGODB, f"Expected 'mongodb', got '{pref}'"
    print(f"✅ Environment variable override works (mongodb)")
    
    os.environ['DATA_SOURCE'] = 'auto'
    pref = get_data_source_preference()
    assert pref == DATA_SOURCE_AUTO, f"Expected 'auto', got '{pref}'"
    print(f"✅ Environment variable override works (auto)")
    
    # Restore original value
    if old_value:
        os.environ['DATA_SOURCE'] = old_value
    else:
        os.environ.pop('DATA_SOURCE', None)
    
    print()
    return True


def test_csv_only_mode():
    """Test loading data in CSV-only mode."""
    print("="*60)
    print("Testing CSV-Only Mode")
    print("="*60)
    
    # Set to CSV mode
    old_value = os.environ.get('DATA_SOURCE')
    os.environ['DATA_SOURCE'] = 'csv'
    
    try:
        data = load_game_data()
        
        if data.empty:
            print("⚠️  No CSV data available (this may be expected)")
            return True
        else:
            print(f"✅ Loaded {len(data)} games from CSV sources")
            print(f"   Columns: {list(data.columns)[:5]}...")
            return True
            
    except Exception as e:
        print(f"❌ Error in CSV mode: {e}")
        return False
    finally:
        # Restore original value
        if old_value:
            os.environ['DATA_SOURCE'] = old_value
        else:
            os.environ.pop('DATA_SOURCE', None)
    
    print()


def test_mongodb_availability_for_data_source():
    """Test MongoDB availability for use as data source."""
    print("="*60)
    print("Testing MongoDB Availability as Data Source")
    print("="*60)
    
    if not is_mongodb_available():
        print("⚠️  pymongo not installed - MongoDB data source unavailable")
        print("   This is okay if you only use CSV sources")
        return True
    
    print("✅ pymongo is installed")
    
    # Test if enabled
    if is_mongodb_enabled():
        print("✅ MongoDB is enabled via environment variable")
    else:
        print("⚠️  MongoDB not enabled (MONGODB_ENABLED not set to true)")
        print("   Set MONGODB_ENABLED=true to use MongoDB as data source")
    
    print()
    return True


def setup_test_mongodb_data(connection_string=None, database_name=None):
    """Set up test data in MongoDB for testing data source functionality."""
    print("="*60)
    print("Setting Up Test Data in MongoDB")
    print("="*60)
    
    if not is_mongodb_available():
        print("❌ Cannot set up test data: pymongo not installed")
        return False
    
    try:
        # Create some sample game data
        sample_games = [
            {
                "GameId": "DATASOURCE_TEST_001",
                "GameDivisionName": "test-division-1",
                "GameDivisionDisplay": "Test Division 1",
                "HomeTeamName": "Test Team A",
                "AwayTeamName": "Test Team B",
                "FinalHomeScore": 85,
                "FinalAwayScore": 78,
                "SeasonId": "2025-2026",
                "GameStatus": "Finished",
                "DateTime": "2025-01-15 19:00:00"
            },
            {
                "GameId": "DATASOURCE_TEST_002",
                "GameDivisionName": "test-division-1",
                "GameDivisionDisplay": "Test Division 1",
                "HomeTeamName": "Test Team C",
                "AwayTeamName": "Test Team D",
                "FinalHomeScore": 92,
                "FinalAwayScore": 88,
                "SeasonId": "2025-2026",
                "GameStatus": "Finished",
                "DateTime": "2025-01-16 20:00:00"
            },
            {
                "GameId": "DATASOURCE_TEST_003",
                "GameDivisionName": "test-division-2",
                "GameDivisionDisplay": "Test Division 2",
                "HomeTeamName": "Test Team E",
                "AwayTeamName": "Test Team F",
                "FinalHomeScore": 75,
                "FinalAwayScore": 72,
                "SeasonId": "2025-2026",
                "GameStatus": "Finished",
                "DateTime": "2025-01-17 18:00:00"
            }
        ]
        
        # Connect to MongoDB
        mongo = MongoDBHelper(connection_string, database_name)
        if not mongo.connect():
            print("❌ Failed to connect to MongoDB")
            return False
        
        # Store test games
        print(f"Storing {len(sample_games)} test games...")
        stats = mongo.store_games_batch(sample_games, 'games')
        
        print(f"✅ Test data setup complete:")
        print(f"   Inserted: {stats['inserted']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Failed: {stats['failed']}")
        
        # Create indexes
        mongo.create_indexes('games')
        
        mongo.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()


def test_mongodb_data_loading():
    """Test loading data from MongoDB."""
    print("="*60)
    print("Testing MongoDB Data Loading")
    print("="*60)
    
    if not is_mongodb_available():
        print("⚠️  Skipping: pymongo not installed")
        return True
    
    if not is_mongodb_enabled():
        print("⚠️  Skipping: MongoDB not enabled")
        print("   Set MONGODB_ENABLED=true to test MongoDB data loading")
        return True
    
    try:
        print("Attempting to load data from MongoDB...")
        data = load_game_data_from_mongodb_source()
        
        if data.empty:
            print("⚠️  No data in MongoDB (this may be expected if no data has been exported)")
            print("   Run with --setup-test-data to add test data")
            return True
        else:
            print(f"✅ Loaded {len(data)} games from MongoDB")
            print(f"   Columns: {list(data.columns)[:10]}...")
            
            # Check that data was converted properly
            if 'GameId' in data.columns and 'HomeTeamName' in data.columns:
                print("✅ Data structure looks correct")
                return True
            else:
                print("❌ Data structure missing expected columns")
                return False
                
    except Exception as e:
        print(f"❌ Error loading from MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()


def test_auto_mode():
    """Test auto mode (try MongoDB, fallback to CSV)."""
    print("="*60)
    print("Testing Auto Mode (MongoDB → CSV fallback)")
    print("="*60)
    
    # Set to auto mode
    old_value = os.environ.get('DATA_SOURCE')
    os.environ['DATA_SOURCE'] = 'auto'
    
    try:
        data = load_game_data()
        
        if data.empty:
            print("⚠️  No data available from either source")
            return True
        else:
            print(f"✅ Loaded {len(data)} games in auto mode")
            
            # Check which source was used
            from src.utils import get_data_source_info
            source_info = get_data_source_info()
            print(f"   Data source: {source_info['source']}")
            print(f"   Description: {source_info['source_description']}")
            return True
            
    except Exception as e:
        print(f"❌ Error in auto mode: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original value
        if old_value:
            os.environ['DATA_SOURCE'] = old_value
        else:
            os.environ.pop('DATA_SOURCE', None)
    
    print()


def cleanup_test_data(connection_string=None, database_name=None):
    """Clean up test data from MongoDB."""
    print("="*60)
    print("Cleaning Up Test Data")
    print("="*60)
    
    if not is_mongodb_available():
        print("⚠️  Skipping cleanup: pymongo not installed")
        return True
    
    try:
        mongo = MongoDBHelper(connection_string, database_name)
        if not mongo.connect():
            print("⚠️  Cannot connect to MongoDB for cleanup")
            return True
        
        # Delete test games
        collection = mongo.db['games']
        result = collection.delete_many({'GameId': {'$regex': '^DATASOURCE_TEST_'}})
        print(f"✅ Deleted {result.deleted_count} test games")
        
        mongo.disconnect()
        return True
        
    except Exception as e:
        print(f"⚠️  Error during cleanup: {e}")
        return True  # Don't fail on cleanup errors
    
    print()


def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description='Test MongoDB data source functionality')
    parser.add_argument('--setup-test-data',
                       action='store_true',
                       help='Set up test data in MongoDB before running tests')
    parser.add_argument('--connection-string',
                       help='MongoDB connection string (default: from env)')
    parser.add_argument('--database',
                       help='MongoDB database name (default: from env)')
    parser.add_argument('--cleanup',
                       action='store_true',
                       help='Clean up test data after tests')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("MongoDB Data Source Test Suite")
    print("="*60)
    print()
    
    # Set up test data if requested
    if args.setup_test_data:
        if not setup_test_mongodb_data(args.connection_string, args.database):
            print("\n❌ Failed to set up test data")
            sys.exit(1)
        print()
    
    # Run tests
    results = []
    
    results.append(("Configuration", test_data_source_configuration()))
    results.append(("CSV-Only Mode", test_csv_only_mode()))
    results.append(("MongoDB Availability", test_mongodb_availability_for_data_source()))
    results.append(("MongoDB Data Loading", test_mongodb_data_loading()))
    results.append(("Auto Mode", test_auto_mode()))
    
    # Clean up if requested
    if args.cleanup:
        cleanup_test_data(args.connection_string, args.database)
    
    # Summary
    print("="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)
    
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
