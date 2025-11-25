"""
MongoDB Helper Module for FLBB Statistics

This module provides utilities for storing and retrieving basketball statistics data
from MongoDB. It supports both local MongoDB instances and MongoDB Atlas cloud service.

Features:
- Connection management with environment variables
- Store extracted JSON game data
- Query game data by various criteria
- Batch operations for efficient data storage
- Error handling and logging

Environment Variables:
- MONGODB_URI: MongoDB connection string (default: mongodb://localhost:27017/)
- MONGODB_DATABASE: Database name (default: flbb-statistics)
- MONGODB_ENABLED: Enable MongoDB storage (default: False)
"""

import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

# Constants for configuration
TRUTHY_VALUES = ['true', '1', 'yes']
DEFAULT_MONGODB_URI = 'mongodb://localhost:27017/'
DEFAULT_MONGODB_DATABASE = 'flbb-statistics'
DEFAULT_CONNECTION_TIMEOUT_MS = 5000


def is_mongodb_available():
    """
    Check if pymongo is installed.
    
    Returns:
        bool: True if pymongo is available, False otherwise
    """
    try:
        import pymongo
        return True
    except ImportError:
        return False


def is_mongodb_enabled():
    """
    Check if MongoDB storage is enabled via configuration or environment.
    
    Returns:
        bool: True if MongoDB is enabled, False otherwise
    """
    # Check environment variable
    enabled = os.environ.get('MONGODB_ENABLED', 'false').lower() in TRUTHY_VALUES
    
    # Also check if pymongo is available
    if enabled and not is_mongodb_available():
        print("Warning: MongoDB is enabled but pymongo is not installed")
        print("Install with: pip install pymongo")
        return False
    
    return enabled


class MongoDBHelper:
    """
    Helper class for MongoDB operations.
    """
    
    def __init__(self, connection_string: Optional[str] = None, database_name: Optional[str] = None):
        """
        Initialize MongoDB helper.
        
        Args:
            connection_string (str, optional): MongoDB connection string
            database_name (str, optional): Database name
        """
        if not is_mongodb_available():
            raise ImportError("pymongo is not installed. Install with: pip install pymongo")
        
        import pymongo
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
        
        self.pymongo = pymongo
        self.ConnectionFailure = ConnectionFailure
        self.ServerSelectionTimeoutError = ServerSelectionTimeoutError
        
        # Get connection details from environment or use defaults
        self.connection_string = connection_string or os.environ.get(
            'MONGODB_URI', DEFAULT_MONGODB_URI
        )
        self.database_name = database_name or os.environ.get(
            'MONGODB_DATABASE', DEFAULT_MONGODB_DATABASE
        )
        
        self.client = None
        self.db = None
        self._connected = False
    
    def connect(self) -> bool:
        """
        Connect to MongoDB.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Set a shorter timeout for connection attempts
            self.client = self.pymongo.MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=DEFAULT_CONNECTION_TIMEOUT_MS
            )
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self._connected = True
            print(f"✅ Connected to MongoDB database: {self.database_name}")
            return True
        except (self.ConnectionFailure, self.ServerSelectionTimeoutError) as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            self._connected = False
            return False
        except Exception as e:
            print(f"❌ Unexpected error connecting to MongoDB: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._connected = False
            print("MongoDB connection closed")
    
    def is_connected(self) -> bool:
        """
        Check if connected to MongoDB.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected
    
    def store_game_data(self, game_data: Dict[str, Any], collection_name: str = 'games') -> bool:
        """
        Store a single game data document in MongoDB.
        
        Args:
            game_data (dict): Game data to store
            collection_name (str): Collection name (default: 'games')
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            print("Not connected to MongoDB")
            return False
        
        try:
            collection = self.db[collection_name]
            
            # Add metadata
            game_data_copy = game_data.copy()
            game_data_copy['_stored_at'] = datetime.utcnow()
            
            # Use composite key (GameId + SeasonId) as unique identifier
            game_id = game_data_copy.get('GameId')
            season_id = game_data_copy.get('SeasonId')
            
            if game_id and season_id:
                # Update or insert based on composite key (GameId + SeasonId)
                result = collection.update_one(
                    {'GameId': game_id, 'SeasonId': season_id},
                    {'$set': game_data_copy},
                    upsert=True
                )
                return True
            elif game_id:
                # Fallback: If SeasonId is not provided, warn and use GameId only
                print(f"WARNING: SeasonId not provided for GameId {game_id}. Using GameId only (not recommended).")
                result = collection.update_one(
                    {'GameId': game_id},
                    {'$set': game_data_copy},
                    upsert=True
                )
                return True
            else:
                # Insert without keys (not recommended)
                print("WARNING: Neither GameId nor SeasonId provided. Inserting without unique key.")
                collection.insert_one(game_data_copy)
                return True
        except Exception as e:
            print(f"Error storing game data: {e}")
            return False
    
    def store_games_batch(self, games_data: List[Dict[str, Any]], 
                         collection_name: str = 'games') -> Dict[str, int]:
        """
        Store multiple game data documents in MongoDB using batch operation.
        
        Args:
            games_data (list): List of game data dictionaries
            collection_name (str): Collection name (default: 'games')
        
        Returns:
            dict: Statistics with 'inserted', 'updated', 'failed' counts
        """
        if not self.is_connected():
            print("Not connected to MongoDB")
            return {'inserted': 0, 'updated': 0, 'failed': len(games_data)}
        
        stats = {'inserted': 0, 'updated': 0, 'failed': 0}
        
        try:
            collection = self.db[collection_name]
            
            for game_data in games_data:
                try:
                    # Add metadata
                    game_data_copy = game_data.copy()
                    game_data_copy['_stored_at'] = datetime.utcnow()
                    
                    # Use composite key (GameId + SeasonId) as unique identifier
                    game_id = game_data_copy.get('GameId')
                    season_id = game_data_copy.get('SeasonId')
                    
                    if game_id and season_id:
                        result = collection.update_one(
                            {'GameId': game_id, 'SeasonId': season_id},
                            {'$set': game_data_copy},
                            upsert=True
                        )
                        if result.upserted_id:
                            stats['inserted'] += 1
                        else:
                            stats['updated'] += 1
                    elif game_id:
                        # Fallback: If SeasonId is not provided, use GameId only
                        print(f"WARNING: SeasonId not provided for GameId {game_id}")
                        result = collection.update_one(
                            {'GameId': game_id},
                            {'$set': game_data_copy},
                            upsert=True
                        )
                        if result.upserted_id:
                            stats['inserted'] += 1
                        else:
                            stats['updated'] += 1
                    else:
                        collection.insert_one(game_data_copy)
                        stats['inserted'] += 1
                except Exception as e:
                    print(f"Error storing game: {e}")
                    stats['failed'] += 1
            
            return stats
        except Exception as e:
            print(f"Error in batch operation: {e}")
            stats['failed'] = len(games_data)
            return stats
    
    def get_game_by_id(self, game_id: str, season_id: Optional[str] = None, 
                       collection_name: str = 'games') -> Optional[Dict[str, Any]]:
        """
        Retrieve a game by GameId and optionally SeasonId.
        
        Args:
            game_id (str): Game ID
            season_id (str, optional): Season ID for composite key lookup
            collection_name (str): Collection name (default: 'games')
        
        Returns:
            dict or None: Game data if found, None otherwise
            
        Note:
            If season_id is provided, uses composite key (GameId + SeasonId).
            If season_id is None, returns first match by GameId only (not recommended).
        """
        if not self.is_connected():
            print("Not connected to MongoDB")
            return None
        
        try:
            collection = self.db[collection_name]
            
            if season_id:
                # Use composite key for precise lookup
                game = collection.find_one({'GameId': game_id, 'SeasonId': season_id})
            else:
                # Fallback to GameId only (may return wrong game if same ID exists in multiple seasons)
                print(f"WARNING: Querying GameId {game_id} without SeasonId. This may return incorrect results.")
                game = collection.find_one({'GameId': game_id})
            
            if game:
                # Remove MongoDB's _id field for cleaner output
                game.pop('_id', None)
            return game
        except Exception as e:
            print(f"Error retrieving game: {e}")
            return None
    
    def get_game_by_composite_key(self, game_id: str, season_id: str,
                                   collection_name: str = 'games') -> Optional[Dict[str, Any]]:
        """
        Retrieve a game by composite key (GameId + SeasonId).
        
        Args:
            game_id (str): Game ID
            season_id (str): Season ID
            collection_name (str): Collection name (default: 'games')
        
        Returns:
            dict or None: Game data if found, None otherwise
        """
        return self.get_game_by_id(game_id, season_id, collection_name)
    
    def get_games_by_division(self, division_name: str, 
                              collection_name: str = 'games') -> List[Dict[str, Any]]:
        """
        Retrieve all games for a specific division.
        
        Args:
            division_name (str): Division name
            collection_name (str): Collection name (default: 'games')
        
        Returns:
            list: List of game data dictionaries
        """
        if not self.is_connected():
            print("Not connected to MongoDB")
            return []
        
        try:
            collection = self.db[collection_name]
            games = list(collection.find({'GameDivisionName': division_name}))
            # Remove MongoDB's _id field
            for game in games:
                game.pop('_id', None)
            return games
        except Exception as e:
            print(f"Error retrieving games: {e}")
            return []
    
    def get_all_games(self, collection_name: str = 'games', 
                     limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all games from the collection.
        
        Args:
            collection_name (str): Collection name (default: 'games')
            limit (int, optional): Limit number of results
        
        Returns:
            list: List of game data dictionaries
        """
        if not self.is_connected():
            print("Not connected to MongoDB")
            return []
        
        try:
            collection = self.db[collection_name]
            cursor = collection.find()
            if limit:
                cursor = cursor.limit(limit)
            games = list(cursor)
            # Remove MongoDB's _id field
            for game in games:
                game.pop('_id', None)
            return games
        except Exception as e:
            print(f"Error retrieving games: {e}")
            return []
    
    def get_games_count(self, collection_name: str = 'games') -> int:
        """
        Get the total count of games in the collection.
        
        Args:
            collection_name (str): Collection name (default: 'games')
        
        Returns:
            int: Number of games
        """
        if not self.is_connected():
            print("Not connected to MongoDB")
            return 0
        
        try:
            collection = self.db[collection_name]
            return collection.count_documents({})
        except Exception as e:
            print(f"Error counting games: {e}")
            return 0
    
    def delete_all_games(self, collection_name: str = 'games') -> int:
        """
        Delete all games from the collection.
        
        Args:
            collection_name (str): Collection name (default: 'games')
        
        Returns:
            int: Number of deleted documents
        """
        if not self.is_connected():
            print("Not connected to MongoDB")
            return 0
        
        try:
            collection = self.db[collection_name]
            result = collection.delete_many({})
            return result.deleted_count
        except Exception as e:
            print(f"Error deleting games: {e}")
            return 0
    
    def create_indexes(self, collection_name: str = 'games'):
        """
        Create indexes for better query performance.
        
        Args:
            collection_name (str): Collection name (default: 'games')
        """
        if not self.is_connected():
            print("Not connected to MongoDB")
            return
        
        try:
            collection = self.db[collection_name]
            
            # Create composite unique index on GameId + SeasonId (primary key)
            try:
                collection.create_index(
                    [('GameId', 1), ('SeasonId', 1)],
                    unique=True,
                    background=True,
                    name='GameId_SeasonId_unique'
                )
                print("✅ Created composite unique index on GameId + SeasonId")
            except Exception as e:
                # Index might already exist, which is fine
                if 'already exists' not in str(e).lower():
                    print(f"Note: Composite index: {e}")
            
            # Index on GameId alone for queries that don't specify season
            try:
                collection.create_index('GameId', background=True)
            except Exception as e:
                if 'already exists' not in str(e).lower():
                    print(f"Note: GameId index: {e}")
            
            # Index on status for filtering
            try:
                collection.create_index('status', background=True)
            except Exception as e:
                if 'already exists' not in str(e).lower():
                    print(f"Note: status index: {e}")
            
            # Index on GameDivisionName for division queries
            try:
                collection.create_index('GameDivisionName', background=True)
            except Exception as e:
                if 'already exists' not in str(e).lower():
                    print(f"Note: GameDivisionName index: {e}")
            
            # Index on SeasonId for season queries
            try:
                collection.create_index('SeasonId', background=True)
            except Exception as e:
                if 'already exists' not in str(e).lower():
                    print(f"Note: SeasonId index: {e}")
            
            # Compound index for efficient game + season + status checks
            try:
                collection.create_index(
                    [('GameId', 1), ('SeasonId', 1), ('status', 1)],
                    background=True,
                    name='GameId_SeasonId_status_compound'
                )
            except Exception as e:
                if 'already exists' not in str(e).lower():
                    print(f"Note: Compound status index: {e}")
            
            print(f"✅ Indexes created/verified on collection: {collection_name}")
        except Exception as e:
            print(f"Error creating indexes: {e}")


def store_json_data_to_mongodb(json_data: List[Dict[str, Any]], 
                               connection_string: Optional[str] = None,
                               database_name: Optional[str] = None,
                               collection_name: str = 'games') -> bool:
    """
    Convenience function to store JSON data to MongoDB.
    
    Args:
        json_data (list): List of game data dictionaries
        connection_string (str, optional): MongoDB connection string
        database_name (str, optional): Database name
        collection_name (str): Collection name (default: 'games')
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not is_mongodb_enabled():
        print("MongoDB storage is not enabled")
        return False
    
    try:
        mongo = MongoDBHelper(connection_string, database_name)
        
        if not mongo.connect():
            return False
        
        print(f"Storing {len(json_data)} games to MongoDB...")
        stats = mongo.store_games_batch(json_data, collection_name)
        
        print(f"✅ MongoDB storage complete:")
        print(f"   - Inserted: {stats['inserted']}")
        print(f"   - Updated: {stats['updated']}")
        print(f"   - Failed: {stats['failed']}")
        
        # Create indexes for better performance
        mongo.create_indexes(collection_name)
        
        mongo.disconnect()
        return stats['failed'] == 0
        
    except Exception as e:
        print(f"Error storing data to MongoDB: {e}")
        return False


def load_json_data_from_mongodb(connection_string: Optional[str] = None,
                                database_name: Optional[str] = None,
                                collection_name: str = 'games',
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to load JSON data from MongoDB.
    
    Args:
        connection_string (str, optional): MongoDB connection string
        database_name (str, optional): Database name
        collection_name (str): Collection name (default: 'games')
        limit (int, optional): Limit number of results
    
    Returns:
        list: List of game data dictionaries
    """
    if not is_mongodb_enabled():
        print("MongoDB storage is not enabled")
        return []
    
    try:
        mongo = MongoDBHelper(connection_string, database_name)
        
        if not mongo.connect():
            return []
        
        games = mongo.get_all_games(collection_name, limit)
        print(f"✅ Loaded {len(games)} games from MongoDB")
        
        mongo.disconnect()
        return games
        
    except Exception as e:
        print(f"Error loading data from MongoDB: {e}")
        return []
