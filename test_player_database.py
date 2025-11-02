#!/usr/bin/env python3
"""
Test script to validate player database creation from JSON files.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
from utils import load_game_data, create_players_database, PLAYERS_DATABASE_CSV_FILEPATH

def test_player_database():
    """Test the player database creation functionality."""
    print("=" * 60)
    print("Testing Player Database Creation")
    print("=" * 60)
    
    # Load game data
    print("\n1. Loading game data...")
    data = load_game_data()
    
    if data.empty:
        print("❌ No game data available for testing")
        return False
    
    print(f"✅ Loaded {len(data)} game records")
    
    # Create player database
    print("\n2. Creating player database...")
    players_db = create_players_database(data)
    
    if players_db.empty:
        print("❌ Failed to create player database")
        return False
    
    print(f"✅ Created player database with {len(players_db)} player records")
    
    # Display sample data
    print("\n3. Sample player database records (top 10 scorers):")
    print("-" * 60)
    print(players_db.head(10).to_string(index=False))
    
    # Verify CSV file was created
    print("\n4. Verifying CSV file...")
    if os.path.exists(PLAYERS_DATABASE_CSV_FILEPATH):
        file_size = os.path.getsize(PLAYERS_DATABASE_CSV_FILEPATH)
        print(f"✅ Player database CSV created: {PLAYERS_DATABASE_CSV_FILEPATH}")
        print(f"   File size: {file_size:,} bytes")
        
        # Verify it can be read back
        try:
            verify_df = pd.read_csv(PLAYERS_DATABASE_CSV_FILEPATH)
            print(f"✅ CSV file verified: {len(verify_df)} records can be read")
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            return False
    else:
        print(f"❌ CSV file not found: {PLAYERS_DATABASE_CSV_FILEPATH}")
        return False
    
    # Display statistics
    print("\n5. Player Database Statistics:")
    print("-" * 60)
    print(f"Total unique players: {len(players_db)}")
    print(f"Total teams: {players_db['Team'].nunique()}")
    print(f"Average games per player: {players_db['GamesPlayed'].mean():.1f}")
    print(f"Average points per player: {players_db['TotalPoints'].mean():.1f}")
    print(f"Top scorer: {players_db.iloc[0]['PlayerName']} ({players_db.iloc[0]['TotalPoints']} points)")
    
    print("\n" + "=" * 60)
    print("✅ Player Database Test Completed Successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_player_database()
    sys.exit(0 if success else 1)
