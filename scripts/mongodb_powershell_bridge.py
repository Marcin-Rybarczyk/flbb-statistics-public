#!/usr/bin/env python3
"""
MongoDB PowerShell Bridge

This script provides a command-line interface for PowerShell scripts to interact
with MongoDB for game data storage and deduplication.

Usage:
    # Check if a game exists with status 'finished'
    python mongodb_powershell_bridge.py check-game --game-id 12345
    
    # Insert or update a game document
    python mongodb_powershell_bridge.py upsert-game --game-id 12345 --json-file game.json --status finished
    
    # Query games by status
    python mongodb_powershell_bridge.py query-games --status finished
    
    # Get game count
    python mongodb_powershell_bridge.py count-games
    
    # Test MongoDB connection
    python mongodb_powershell_bridge.py test-connection

Environment Variables:
    MONGODB_ENABLED - Enable MongoDB operations (default: false)
    MONGODB_URI - MongoDB connection string (default: mongodb://localhost:27017/)
    MONGODB_DATABASE - Database name (default: flbb-statistics)
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mongodb_helper import (
    is_mongodb_available,
    is_mongodb_enabled,
    MongoDBHelper
)


def check_game_exists(args):
    """
    Check if a game exists with a specific status.
    
    Returns:
        0 - Game exists with matching status (or status not specified)
        1 - Game does not exist or status doesn't match
        2 - Error occurred
    """
    if not is_mongodb_available():
        print("ERROR: pymongo not installed", file=sys.stderr)
        return 2
    
    try:
        mongo = MongoDBHelper(args.uri, args.database)
        if not mongo.connect():
            print("ERROR: Failed to connect to MongoDB", file=sys.stderr)
            return 2
        
        game = mongo.get_game_by_id(args.game_id, args.collection)
        
        if not game:
            print(f"NOTFOUND: Game {args.game_id} does not exist")
            mongo.disconnect()
            return 1
        
        # Check status if specified
        if args.status:
            game_status = game.get('status', '').lower()
            if game_status == args.status.lower():
                print(f"EXISTS: Game {args.game_id} exists with status '{game_status}'")
                mongo.disconnect()
                return 0
            else:
                print(f"STATUS_MISMATCH: Game {args.game_id} exists but status is '{game_status}' (expected '{args.status}')")
                mongo.disconnect()
                return 1
        else:
            print(f"EXISTS: Game {args.game_id} exists")
            mongo.disconnect()
            return 0
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


def upsert_game(args):
    """
    Insert or update a game document in MongoDB.
    
    Returns:
        0 - Success
        1 - Validation error
        2 - Database error
    """
    if not is_mongodb_available():
        print("ERROR: pymongo not installed", file=sys.stderr)
        return 2
    
    try:
        # Load JSON data
        game_data = {}
        if args.json_file:
            if not os.path.exists(args.json_file):
                print(f"ERROR: JSON file not found: {args.json_file}", file=sys.stderr)
                return 1
            
            with open(args.json_file, 'r', encoding='utf-8') as f:
                game_data = json.load(f)
        elif args.json_data:
            game_data = json.loads(args.json_data)
        
        # Ensure GameId is set
        if not game_data.get('GameId'):
            game_data['GameId'] = args.game_id
        
        # Add metadata fields
        if args.status:
            game_data['status'] = args.status
        
        if args.csv_generated is not None:
            game_data['csv_generated'] = args.csv_generated
        
        # Add processing metadata
        game_data['_last_updated'] = datetime.utcnow().isoformat()
        game_data['_processed_by'] = 'PowerShell Script'
        
        # Connect and store
        mongo = MongoDBHelper(args.uri, args.database)
        if not mongo.connect():
            print("ERROR: Failed to connect to MongoDB", file=sys.stderr)
            return 2
        
        success = mongo.store_game_data(game_data, args.collection)
        
        if success:
            print(f"SUCCESS: Game {args.game_id} stored/updated in MongoDB")
            mongo.disconnect()
            return 0
        else:
            print(f"ERROR: Failed to store game {args.game_id}", file=sys.stderr)
            mongo.disconnect()
            return 2
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


def query_games(args):
    """
    Query games by various criteria.
    
    Returns:
        0 - Success (prints JSON array of games)
        2 - Error occurred
    """
    if not is_mongodb_available():
        print("ERROR: pymongo not installed", file=sys.stderr)
        return 2
    
    try:
        mongo = MongoDBHelper(args.uri, args.database)
        if not mongo.connect():
            print("ERROR: Failed to connect to MongoDB", file=sys.stderr)
            return 2
        
        collection = mongo.db[args.collection]
        
        # Build query filter
        query_filter = {}
        if args.status:
            query_filter['status'] = args.status
        if args.division:
            query_filter['GameDivisionDisplay'] = args.division
        if args.season:
            query_filter['SeasonId'] = args.season
        
        # Execute query
        games = list(collection.find(query_filter))
        
        # Remove MongoDB _id field
        for game in games:
            game.pop('_id', None)
        
        # Output as JSON
        print(json.dumps(games, default=str, indent=2))
        
        mongo.disconnect()
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


def count_games(args):
    """
    Count games in the collection.
    
    Returns:
        0 - Success (prints count)
        2 - Error occurred
    """
    if not is_mongodb_available():
        print("ERROR: pymongo not installed", file=sys.stderr)
        return 2
    
    try:
        mongo = MongoDBHelper(args.uri, args.database)
        if not mongo.connect():
            print("ERROR: Failed to connect to MongoDB", file=sys.stderr)
            return 2
        
        count = mongo.get_games_count(args.collection)
        print(f"COUNT: {count}")
        
        mongo.disconnect()
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


def test_connection(args):
    """
    Test MongoDB connection.
    
    Returns:
        0 - Connection successful
        1 - Connection failed
    """
    if not is_mongodb_available():
        print("ERROR: pymongo not installed", file=sys.stderr)
        print("INSTALL: pip install pymongo", file=sys.stderr)
        return 1
    
    try:
        print(f"Testing connection to {args.uri}")
        mongo = MongoDBHelper(args.uri, args.database)
        
        if mongo.connect():
            print(f"SUCCESS: Connected to MongoDB database '{args.database}'")
            count = mongo.get_games_count(args.collection)
            print(f"INFO: Collection '{args.collection}' contains {count} games")
            mongo.disconnect()
            return 0
        else:
            print("ERROR: Connection failed", file=sys.stderr)
            return 1
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='MongoDB PowerShell Bridge - CLI interface for MongoDB operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check if a game exists with status 'finished'
  python mongodb_powershell_bridge.py check-game --game-id 12345 --status finished
  
  # Insert/update a game from JSON file
  python mongodb_powershell_bridge.py upsert-game --game-id 12345 --json-file game.json --status finished
  
  # Query all finished games
  python mongodb_powershell_bridge.py query-games --status finished
  
  # Count total games
  python mongodb_powershell_bridge.py count-games
  
  # Test connection
  python mongodb_powershell_bridge.py test-connection
        """
    )
    
    # Common arguments for all commands
    parser.add_argument('--uri',
                       default=os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/'),
                       help='MongoDB connection string (default: from MONGODB_URI env or mongodb://localhost:27017/)')
    
    parser.add_argument('--database',
                       default=os.environ.get('MONGODB_DATABASE', 'flbb-statistics'),
                       help='MongoDB database name (default: from MONGODB_DATABASE env or flbb-statistics)')
    
    parser.add_argument('--collection',
                       default='games',
                       help='MongoDB collection name (default: games)')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    subparsers.required = True
    
    # check-game command
    check_parser = subparsers.add_parser('check-game', help='Check if a game exists')
    check_parser.add_argument('--game-id', required=True, help='Game ID to check')
    check_parser.add_argument('--status', help='Check if game has this status (e.g., finished)')
    check_parser.set_defaults(func=check_game_exists)
    
    # upsert-game command
    upsert_parser = subparsers.add_parser('upsert-game', help='Insert or update a game')
    upsert_parser.add_argument('--game-id', required=True, help='Game ID')
    upsert_parser.add_argument('--json-file', help='Path to JSON file with game data')
    upsert_parser.add_argument('--json-data', help='JSON data as string')
    upsert_parser.add_argument('--status', help='Game status (e.g., finished, pending)')
    upsert_parser.add_argument('--csv-generated', type=lambda x: x.lower() == 'true',
                              help='Whether CSV was generated (true/false)')
    upsert_parser.set_defaults(func=upsert_game)
    
    # query-games command
    query_parser = subparsers.add_parser('query-games', help='Query games')
    query_parser.add_argument('--status', help='Filter by status')
    query_parser.add_argument('--division', help='Filter by division')
    query_parser.add_argument('--season', help='Filter by season')
    query_parser.set_defaults(func=query_games)
    
    # count-games command
    count_parser = subparsers.add_parser('count-games', help='Count games in collection')
    count_parser.set_defaults(func=count_games)
    
    # test-connection command
    test_parser = subparsers.add_parser('test-connection', help='Test MongoDB connection')
    test_parser.set_defaults(func=test_connection)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
