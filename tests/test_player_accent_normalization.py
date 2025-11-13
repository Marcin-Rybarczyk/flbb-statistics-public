#!/usr/bin/env python3
"""
Test accent normalization in player name matching.
This ensures that player names with accents (é, ô, etc.) work correctly
when used in URLs and lookups.
"""

import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import (
    normalize_name_for_matching,
    load_game_data,
    get_player_hover_stats,
    get_player_detail_stats
)


# Test data constants
NORMALIZE_TEST_CASES = [
    ("KAFER Jérôme Charel", "KAFER Jerome Charel"),
    ("Sébastien HOMMEL", "Sebastien HOMMEL"),
    ("François VILLAIN", "Francois VILLAIN"),
    ("René WOLZFELD", "Rene WOLZFELD"),
    ("Racing Luxembourg", "Racing Luxembourg"),  # No accents
]

PLAYER_HOVER_TEST_PLAYERS = [
    ("KAFER Jérôme Charel", "KAFER Jerome Charel"),
]


def test_normalize_function():
    """Test the normalize_name_for_matching function"""
    print("\n" + "="*70)
    print("Testing normalize_name_for_matching function")
    print("="*70)
    
    all_passed = True
    for original, expected in NORMALIZE_TEST_CASES:
        result = normalize_name_for_matching(original)
        passed = result == expected
        status = "✅" if passed else "❌"
        print(f"{status} '{original}' -> '{result}'")
        if not passed:
            print(f"   Expected: '{expected}'")
            all_passed = False
    
    return all_passed


def test_player_hover_stats():
    """Test that player hover stats work with both accented and non-accented names"""
    print("\n" + "="*70)
    print("Testing get_player_hover_stats with accented player names")
    print("="*70)
    
    # Load data
    data = load_game_data()
    
    all_passed = True
    for accented, non_accented in PLAYER_HOVER_TEST_PLAYERS:
        print(f"\n🔍 Testing: {accented}")
        
        # Test with accented name
        stats_accented = get_player_hover_stats(data, accented)
        # Test with non-accented name
        stats_non_accented = get_player_hover_stats(data, non_accented)
        
        if not stats_accented:
            print(f"   ❌ Failed to find player with accented name: '{accented}'")
            all_passed = False
            continue
            
        if not stats_non_accented:
            print(f"   ❌ Failed to find player with non-accented name: '{non_accented}'")
            all_passed = False
            continue
        
        # Compare results
        games_match = stats_accented['games_played'] == stats_non_accented['games_played']
        score_match = stats_accented['avg_score'] == stats_non_accented['avg_score']
        
        if games_match and score_match:
            print(f"   ✅ Both versions found the same player")
            print(f"      Games played: {stats_accented['games_played']}")
            print(f"      Avg score: {stats_accented['avg_score']}")
            print(f"      Team: {stats_accented['team']}")
        else:
            print(f"   ❌ Results don't match!")
            print(f"      Accented: {stats_accented['games_played']} games, {stats_accented['avg_score']} avg")
            print(f"      Non-accented: {stats_non_accented['games_played']} games, {stats_non_accented['avg_score']} avg")
            all_passed = False
    
    return all_passed


def test_player_detail_stats():
    """Test that player detail stats work with both accented and non-accented names"""
    print("\n" + "="*70)
    print("Testing get_player_detail_stats with accented player names")
    print("="*70)
    
    # Load data
    data = load_game_data()
    
    all_passed = True
    for accented, non_accented in PLAYER_HOVER_TEST_PLAYERS:
        print(f"\n🔍 Testing: {accented}")
        
        # Test with accented name
        stats_accented = get_player_detail_stats(data, accented)
        # Test with non-accented name
        stats_non_accented = get_player_detail_stats(data, non_accented)
        
        if not stats_accented:
            print(f"   ❌ Failed to find player with accented name: '{accented}'")
            all_passed = False
            continue
            
        if not stats_non_accented:
            print(f"   ❌ Failed to find player with non-accented name: '{non_accented}'")
            all_passed = False
            continue
        
        # Compare results
        basic_accented = stats_accented.get('basic_stats', {})
        basic_non_accented = stats_non_accented.get('basic_stats', {})
        
        games_match = basic_accented.get('games_played') == basic_non_accented.get('games_played')
        points_match = basic_accented.get('total_points') == basic_non_accented.get('total_points')
        
        if games_match and points_match:
            print(f"   ✅ Both versions found the same player")
            print(f"      Games played: {basic_accented.get('games_played')}")
            print(f"      Total points: {basic_accented.get('total_points')}")
        else:
            print(f"   ❌ Results don't match!")
            print(f"      Accented: {basic_accented.get('games_played')} games, {basic_accented.get('total_points')} pts")
            print(f"      Non-accented: {basic_non_accented.get('games_played')} games, {basic_non_accented.get('total_points')} pts")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("PLAYER ACCENT NORMALIZATION TEST SUITE")
    print("="*70)
    print("\nTesting that player names with accents work correctly in all lookups")
    
    test_results = []
    
    # Run all tests
    test_results.append(("Normalize Function", test_normalize_function()))
    test_results.append(("Player Hover Stats", test_player_hover_stats()))
    test_results.append(("Player Detail Stats", test_player_detail_stats()))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
