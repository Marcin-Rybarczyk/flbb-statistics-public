#!/usr/bin/env python3
"""
Test script for MongoDB integration

This script tests the MongoDB helper functionality for storing and retrieving
basketball game data.

Usage:
    python tests/test_mongodb.py
    python tests/test_mongodb.py --connection-string mongodb://localhost:27017/
    python tests/test_mongodb.py --database test-flbb
"""

import os
import sys
import json
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mongodb_helper import (
    is_mongodb_available,
    is_mongodb_enabled,
    MongoDBHelper,
    store_json_data_to_mongodb,
    load_json_data_from_mongodb
)


def test_mongodb_availability():
    """Test if MongoDB/pymongo is available."""
    print("Testing MongoDB availability...")
    
    if is_mongodb_available():
        print("✅ pymongo is installed")
        import pymongo
        print(f"   pymongo version: {pymongo.__version__}")
    else:
        print("❌ pymongo is not installed")
        print("   Install with: pip install pymongo")
        return False
    
    return True


def test_mongodb_connection(connection_string, database_name):
    """Test MongoDB connection."""
    print(f"\nTesting MongoDB connection...")
    print(f"Connection string: {connection_string}")
    print(f"Database: {database_name}")
    
    mongo = MongoDBHelper(connection_string, database_name)
    
    if mongo.connect():
        print("✅ Successfully connected to MongoDB")
        mongo.disconnect()
        return True
    else:
        print("❌ Failed to connect to MongoDB")
        print("   Make sure MongoDB is running and connection string is correct")
        return False


def test_store_single_game(connection_string, database_name):
    """Test storing a single game."""
    print("\nTesting single game storage...")
    
    # Sample game data
    sample_game = {
        "GameId": "TEST001",
        "GameDivisionName": "test-division",
        "HomeTeamName": "Test Home Team",
        "AwayTeamName": "Test Away Team",
        "FinalHomeScore": 85,
        "FinalAwayScore": 78,
        "SeasonId": "2025-2026",
        "GameStatus": "Finished"
    }
    
    mongo = MongoDBHelper(connection_string, database_name)
    
    if not mongo.connect():
        print("❌ Cannot connect to MongoDB")
        return False
    
    # Store the game
    if mongo.store_game_data(sample_game, 'test_games'):
        print("✅ Successfully stored test game")
        
        # Try to retrieve it
        retrieved = mongo.get_game_by_id('TEST001', 'test_games')
        if retrieved:
            print("✅ Successfully retrieved test game")
            print(f"   Game: {retrieved['HomeTeamName']} vs {retrieved['AwayTeamName']}")
            print(f"   Score: {retrieved['FinalHomeScore']} - {retrieved['FinalAwayScore']}")
        else:
            print("❌ Failed to retrieve test game")
            mongo.disconnect()
            return False
    else:
        print("❌ Failed to store test game")
        mongo.disconnect()
        return False
    
    mongo.disconnect()
    return True


def test_batch_storage(connection_string, database_name):
    """Test batch storage of multiple games."""
    print("\nTesting batch game storage...")
    
    # Sample games data
    sample_games = [
        {
            "GameId": "TEST002",
            "GameDivisionName": "test-division",
            "HomeTeamName": "Team A",
            "AwayTeamName": "Team B",
            "FinalHomeScore": 90,
            "FinalAwayScore": 85,
            "SeasonId": "2025-2026",
            "GameStatus": "Finished"
        },
        {
            "GameId": "TEST003",
            "GameDivisionName": "test-division",
            "HomeTeamName": "Team C",
            "AwayTeamName": "Team D",
            "FinalHomeScore": 75,
            "FinalAwayScore": 80,
            "SeasonId": "2025-2026",
            "GameStatus": "Finished"
        },
        {
            "GameId": "TEST004",
            "GameDivisionName": "test-division-2",
            "HomeTeamName": "Team E",
            "AwayTeamName": "Team F",
            "FinalHomeScore": 88,
            "FinalAwayScore": 82,
            "SeasonId": "2025-2026",
            "GameStatus": "Finished"
        }
    ]
    
    mongo = MongoDBHelper(connection_string, database_name)
    
    if not mongo.connect():
        print("❌ Cannot connect to MongoDB")
        return False
    
    # Store games in batch
    stats = mongo.store_games_batch(sample_games, 'test_games')
    print(f"✅ Batch storage complete:")
    print(f"   - Inserted: {stats['inserted']}")
    print(f"   - Updated: {stats['updated']}")
    print(f"   - Failed: {stats['failed']}")
    
    # Retrieve games by division
    division_games = mongo.get_games_by_division('test-division', 'test_games')
    print(f"✅ Retrieved {len(division_games)} games for 'test-division'")
    
    # Get total count
    total_count = mongo.get_games_count('test_games')
    print(f"✅ Total games in collection: {total_count}")
    
    mongo.disconnect()
    return True


def test_cleanup(connection_string, database_name):
    """Clean up test data."""
    print("\nCleaning up test data...")
    
    mongo = MongoDBHelper(connection_string, database_name)
    
    if not mongo.connect():
        print("❌ Cannot connect to MongoDB")
        return False
    
    deleted_count = mongo.delete_all_games('test_games')
    print(f"✅ Deleted {deleted_count} test games")
    
    mongo.disconnect()
    return True


def test_real_data_storage(connection_string, database_name):
    """Test storing real game data from gamesDB.json."""
    print("\nTesting storage of real game data...")
    
    # Try to load gamesDB.json
    gamesdb_path = 'data/gamesDB.json'
    if not os.path.exists(gamesdb_path):
        print(f"⚠️  {gamesdb_path} not found, skipping real data test")
        return True
    
    # Save original environment value
    original_enabled = os.environ.get('MONGODB_ENABLED')
    
    try:
        with open(gamesdb_path, 'r', encoding='utf-8') as f:
            games_data = json.load(f)
        
        print(f"Loaded {len(games_data)} games from {gamesdb_path}")
        
        # Take only first 5 games for testing
        test_games = games_data[:5]
        
        # Set environment to enable MongoDB
        os.environ['MONGODB_ENABLED'] = 'true'
        
        # Use convenience function
        success = store_json_data_to_mongodb(
            test_games,
            connection_string=connection_string,
            database_name=database_name,
            collection_name='test_real_games'
        )
        
        if success:
            print("✅ Successfully stored real game data")
            
            # Try to retrieve it
            mongo = MongoDBHelper(connection_string, database_name)
            if mongo.connect():
                count = mongo.get_games_count('test_real_games')
                print(f"✅ Verified {count} games in test_real_games collection")
                
                # Clean up
                mongo.delete_all_games('test_real_games')
                print("✅ Cleaned up test data")
                
                mongo.disconnect()
        else:
            print("❌ Failed to store real game data")
            return False
        
    except Exception as e:
        print(f"❌ Error testing real data: {e}")
        return False
    finally:
        # Restore original environment value
        if original_enabled is None:
            os.environ.pop('MONGODB_ENABLED', None)
        else:
            os.environ['MONGODB_ENABLED'] = original_enabled
    
    return True


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Test MongoDB integration')
    parser.add_argument('--connection-string', 
                       default=os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/'),
                       help='MongoDB connection string')
    parser.add_argument('--database', 
                       default=os.environ.get('MONGODB_DATABASE', 'flbb-statistics-test'),
                       help='Database name (will use test database)')
    parser.add_argument('--skip-cleanup', action='store_true',
                       help='Skip cleanup of test data')
    
    args = parser.parse_args()
    
    print("="*60)
    print("FLBB Statistics - MongoDB Integration Tests")
    print("="*60)
    
    # Test 1: Check if MongoDB is available
    if not test_mongodb_availability():
        print("\n❌ MongoDB tests cannot run without pymongo")
        print("Install with: pip install pymongo")
        return 1
    
    # Test 2: Check connection
    if not test_mongodb_connection(args.connection_string, args.database):
        print("\n❌ MongoDB connection tests failed")
        print("Make sure MongoDB is running and accessible")
        return 1
    
    # Test 3: Single game storage
    if not test_store_single_game(args.connection_string, args.database):
        print("\n❌ Single game storage test failed")
        return 1
    
    # Test 4: Batch storage
    if not test_batch_storage(args.connection_string, args.database):
        print("\n❌ Batch storage test failed")
        return 1
    
    # Test 5: Real data storage
    if not test_real_data_storage(args.connection_string, args.database):
        print("\n❌ Real data storage test failed")
        return 1
    
    # Clean up
    if not args.skip_cleanup:
        test_cleanup(args.connection_string, args.database)
    
    print("\n" + "="*60)
    print("✅ All MongoDB tests passed!")
    print("="*60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
