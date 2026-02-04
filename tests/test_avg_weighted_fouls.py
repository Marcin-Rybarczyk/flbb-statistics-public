#!/usr/bin/env python3
"""
Test script for verifying the average weighted fouls per game calculation.
"""

import os
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['ADMIN_PASSWORD'] = 'test123'

from src.utils import get_top_foulers, load_game_data


def test_avg_weighted_fouls_calculation():
    """Test that AvgWeightedFoulsPerGame is calculated correctly"""
    print("=" * 70)
    print("Testing Average Weighted Fouls Per Game Calculation")
    print("=" * 70)
    
    # Load game data
    print("\n1. Loading game data...")
    data = load_game_data()
    
    if data.empty:
        print("   ⚠️  No game data available, skipping test")
        return
    
    print(f"   ✓ Loaded {len(data)} games")
    
    # Get top foulers
    print("\n2. Getting top foulers...")
    top_foulers = get_top_foulers(data, top_n=10)
    
    if top_foulers.empty:
        print("   ⚠️  No fouler data available, skipping test")
        return
    
    print(f"   ✓ Retrieved {len(top_foulers)} top foulers")
    
    # Verify AvgWeightedFoulsPerGame column exists
    print("\n3. Verifying AvgWeightedFoulsPerGame column exists...")
    assert 'AvgWeightedFoulsPerGame' in top_foulers.columns, \
        "AvgWeightedFoulsPerGame column is missing!"
    print("   ✓ Column exists")
    
    # Verify calculation is correct
    print("\n4. Verifying calculation accuracy...")
    for index, row in top_foulers.iterrows():
        expected = round(row['WeightedTotalFouls'] / row['GamesPlayed'], 1)
        actual = row['AvgWeightedFoulsPerGame']
        
        # Allow for small floating point differences
        assert abs(expected - actual) < 0.01, \
            f"Calculation mismatch for {row['PlayerName']}: expected {expected}, got {actual}"
    
    print("   ✓ All calculations are correct")
    
    # Display sample results
    print("\n5. Sample results (top 3 foulers):")
    for index, row in top_foulers.head(3).iterrows():
        print(f"   {row['PlayerName']} ({row['Team']})")
        print(f"      Total Fouls: {row['TotalFouls']}")
        print(f"      Weighted Total Fouls: {row['WeightedTotalFouls']:.1f}")
        print(f"      Games Played: {row['GamesPlayed']}")
        print(f"      Avg Fouls/Game: {row['AvgFoulsPerGame']:.1f}")
        print(f"      Avg Weighted Fouls/Game: {row['AvgWeightedFoulsPerGame']:.1f}")
        print()
    
    print("=" * 70)
    print("✅ All Tests Passed!")
    print("=" * 70)


if __name__ == '__main__':
    try:
        test_avg_weighted_fouls_calculation()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
