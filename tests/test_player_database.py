#!/usr/bin/env python3
"""
Test script for player database creation functionality.

This script tests the player database CSV generation from game data,
including validation of data structure, completeness, and accuracy.
"""
import os
import sys

# Add the root directory to Python path so we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from src.utils import (
    load_game_data, 
    create_players_database, 
    PLAYERS_DATABASE_CSV_FILEPATH,
    extract_all_player_stats
)

def test_player_database_creation():
    """Test that player database can be created from game data."""
    print("\n" + "=" * 60)
    print("Test 1: Player Database Creation")
    print("=" * 60)
    
    # Load game data
    data = load_game_data()
    
    if data.empty:
        print("❌ FAIL: No game data available")
        return False
    
    print(f"✅ PASS: Loaded {len(data)} game records")
    
    # Create player database
    players_db = create_players_database(data)
    
    if players_db.empty:
        print("❌ FAIL: Player database is empty")
        return False
    
    print(f"✅ PASS: Created player database with {len(players_db)} player records")
    return True

def test_player_database_structure():
    """Test that player database has expected columns and structure."""
    print("\n" + "=" * 60)
    print("Test 2: Player Database Structure")
    print("=" * 60)
    
    # Load the CSV file
    if not os.path.exists(PLAYERS_DATABASE_CSV_FILEPATH):
        print(f"❌ FAIL: CSV file not found: {PLAYERS_DATABASE_CSV_FILEPATH}")
        return False
    
    try:
        players_db = pd.read_csv(PLAYERS_DATABASE_CSV_FILEPATH)
    except Exception as e:
        print(f"❌ FAIL: Error reading CSV: {e}")
        return False
    
    # Check expected columns
    expected_columns = [
        'PlayerName', 'Team', 'PlayerNumber', 'GamesPlayed', 'GamesStarted',
        'StartingPercentage', 'TotalPoints', 'AvgPointsPerGame',
        '1PMadeShots', '2PMadeShots', '3PMadeShots', 'TotalFieldGoalsMade',
        'AvgShotsPerGame', 'PointsPerShot', 'TotalFouls', 'AvgFoulsPerGame',
        'PFouls', 'P1Fouls', 'P2Fouls', 'P3Fouls'
    ]
    
    missing_columns = [col for col in expected_columns if col not in players_db.columns]
    if missing_columns:
        print(f"❌ FAIL: Missing columns: {missing_columns}")
        return False
    
    print(f"✅ PASS: All {len(expected_columns)} expected columns present")
    
    # Check data types
    if not pd.api.types.is_numeric_dtype(players_db['TotalPoints']):
        print("❌ FAIL: TotalPoints should be numeric")
        return False
    
    if not pd.api.types.is_numeric_dtype(players_db['GamesPlayed']):
        print("❌ FAIL: GamesPlayed should be numeric")
        return False
    
    print("✅ PASS: Column data types are correct")
    return True

def test_player_database_data_integrity():
    """Test data integrity and logical consistency."""
    print("\n" + "=" * 60)
    print("Test 3: Player Database Data Integrity")
    print("=" * 60)
    
    try:
        players_db = pd.read_csv(PLAYERS_DATABASE_CSV_FILEPATH)
    except Exception as e:
        print(f"❌ FAIL: Error reading CSV: {e}")
        return False
    
    # Test 1: No null values in critical columns
    critical_columns = ['PlayerName', 'Team', 'GamesPlayed', 'TotalPoints']
    null_counts = players_db[critical_columns].isnull().sum()
    
    if null_counts.any():
        print(f"❌ FAIL: Found null values in critical columns: {null_counts[null_counts > 0]}")
        return False
    
    print("✅ PASS: No null values in critical columns")
    
    # Test 2: Games played should be >= games started
    invalid_games = players_db[players_db['GamesPlayed'] < players_db['GamesStarted']]
    if len(invalid_games) > 0:
        print(f"❌ FAIL: Found {len(invalid_games)} players with more games started than games played")
        return False
    
    print("✅ PASS: Games played >= games started for all players")
    
    # Test 3: Starting percentage should be between 0 and 100
    invalid_percentage = players_db[
        (players_db['StartingPercentage'] < 0) | 
        (players_db['StartingPercentage'] > 100)
    ]
    if len(invalid_percentage) > 0:
        print(f"❌ FAIL: Found {len(invalid_percentage)} players with invalid starting percentage")
        return False
    
    print("✅ PASS: All starting percentages are valid (0-100%)")
    
    # Test 4: Average points per game calculation
    calculated_avg = (players_db['TotalPoints'] / players_db['GamesPlayed']).round(2)
    diff = abs(calculated_avg - players_db['AvgPointsPerGame'])
    
    # Allow small floating point differences
    if (diff > 0.01).any():
        print(f"❌ FAIL: Average points per game calculation is incorrect")
        return False
    
    print("✅ PASS: Average points per game calculated correctly")
    
    # Test 5: Total field goals should equal sum of made shots
    calculated_total = (
        players_db['1PMadeShots'] + 
        players_db['2PMadeShots'] + 
        players_db['3PMadeShots']
    )
    diff = abs(calculated_total - players_db['TotalFieldGoalsMade'])
    
    if (diff > 0).any():
        print(f"❌ FAIL: Total field goals calculation is incorrect")
        return False
    
    print("✅ PASS: Total field goals calculated correctly")
    
    return True

def test_player_database_statistics():
    """Test and display player database statistics."""
    print("\n" + "=" * 60)
    print("Test 4: Player Database Statistics")
    print("=" * 60)
    
    try:
        players_db = pd.read_csv(PLAYERS_DATABASE_CSV_FILEPATH)
    except Exception as e:
        print(f"❌ FAIL: Error reading CSV: {e}")
        return False
    
    print(f"Total players: {len(players_db)}")
    print(f"Total teams: {players_db['Team'].nunique()}")
    print(f"Average games per player: {players_db['GamesPlayed'].mean():.1f}")
    print(f"Average points per player: {players_db['TotalPoints'].mean():.1f}")
    print(f"Average fouls per player: {players_db['TotalFouls'].mean():.1f}")
    
    # Top scorer - explicitly sort to ensure correctness
    top_scorer = players_db.nlargest(1, 'TotalPoints').iloc[0]
    print(f"\nTop scorer: {top_scorer['PlayerName']} ({top_scorer['Team']})")
    print(f"  - Total Points: {top_scorer['TotalPoints']}")
    print(f"  - Games Played: {top_scorer['GamesPlayed']}")
    print(f"  - Avg Points/Game: {top_scorer['AvgPointsPerGame']}")
    
    # Player with most games
    most_games = players_db.nlargest(1, 'GamesPlayed').iloc[0]
    print(f"\nMost games played: {most_games['PlayerName']} ({most_games['Team']})")
    print(f"  - Games Played: {most_games['GamesPlayed']}")
    
    print("\n✅ PASS: Statistics calculated and displayed")
    return True

def test_player_database_comparison():
    """Compare player database with extracted player stats."""
    print("\n" + "=" * 60)
    print("Test 5: Player Database vs Raw Stats Comparison")
    print("=" * 60)
    
    # Load game data
    data = load_game_data()
    
    if data.empty:
        print("❌ FAIL: No game data available")
        return False
    
    # Extract raw player stats
    raw_player_stats = extract_all_player_stats(data)
    
    if raw_player_stats.empty:
        print("❌ FAIL: No raw player stats available")
        return False
    
    # Load player database
    try:
        players_db = pd.read_csv(PLAYERS_DATABASE_CSV_FILEPATH)
    except Exception as e:
        print(f"❌ FAIL: Error reading CSV: {e}")
        return False
    
    # Compare total number of game-player records
    raw_record_count = len(raw_player_stats)
    aggregated_record_count = len(players_db)
    
    print(f"Raw player-game records: {raw_record_count}")
    print(f"Aggregated player records: {aggregated_record_count}")
    
    # The aggregated count should be less than raw count (players appear in multiple games)
    if aggregated_record_count >= raw_record_count:
        print("❌ FAIL: Aggregated records should be less than raw records")
        return False
    
    print("✅ PASS: Aggregation reduced records as expected")
    
    # Verify total points match between raw and aggregated data
    raw_total_points = raw_player_stats['TotalPoints'].sum()
    db_total_points = players_db['TotalPoints'].sum()
    
    if abs(raw_total_points - db_total_points) > 1:  # Allow for rounding differences
        print(f"❌ FAIL: Total points mismatch - Raw: {raw_total_points}, DB: {db_total_points}")
        return False
    
    print(f"✅ PASS: Total points match (Raw: {raw_total_points}, DB: {db_total_points})")
    
    return True

def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "#" * 60)
    print("# PLAYER DATABASE TEST SUITE")
    print("#" * 60)
    
    tests = [
        test_player_database_creation,
        test_player_database_structure,
        test_player_database_data_integrity,
        test_player_database_statistics,
        test_player_database_comparison
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test.__name__}: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED!")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
