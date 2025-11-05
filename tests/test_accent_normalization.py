#!/usr/bin/env python3
"""
Test accent normalization in team name matching.
This ensures that team names with accents (é, ë, etc.) work correctly
when used in URLs and lookups.
"""

import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import (
    normalize_team_name_for_matching,
    load_game_data,
    get_team_detail_stats,
    get_team_hover_stats
)


# Test data constants
NORMALIZE_TEST_CASES = [
    ("Gréngewald Hueschtert B", "Grengewald Hueschtert B"),
    ("BBC Käldall", "BBC Kaldall"),
    ("Résidence Walferdange", "Residence Walferdange"),
    ("Rebound Préizerdaul", "Rebound Preizerdaul"),
    ("Racing Luxembourg", "Racing Luxembourg"),  # No accents
]

TEAM_DETAIL_TEST_TEAMS = [
    ("Gréngewald Hueschtert B", "Grengewald Hueschtert B"),
    ("Résidence Walferdange", "Residence Walferdange"),
    ("BBC Käldall", "BBC Kaldall"),
]

TEAM_HOVER_TEST_TEAMS = [
    ("Gréngewald Hueschtert B", "Grengewald Hueschtert B"),
    ("Rebound Préizerdaul", "Rebound Preizerdaul"),
]


def test_normalize_function():
    """Test the normalize_team_name_for_matching function"""
    print("\n" + "="*70)
    print("Testing normalize_team_name_for_matching function")
    print("="*70)
    
    all_passed = True
    for original, expected in NORMALIZE_TEST_CASES:
        result = normalize_team_name_for_matching(original)
        passed = result == expected
        status = "✅" if passed else "❌"
        print(f"{status} '{original}' -> '{result}'")
        if not passed:
            print(f"   Expected: '{expected}'")
            all_passed = False
    
    return all_passed


def test_team_detail_stats():
    """Test that team detail stats work with both accented and non-accented names"""
    print("\n" + "="*70)
    print("Testing get_team_detail_stats with accented team names")
    print("="*70)
    
    # Load data
    data = load_game_data()
    
    all_passed = True
    for accented, non_accented in TEAM_DETAIL_TEST_TEAMS:
        print(f"\n🔍 Testing: {accented}")
        
        # Test with accented name
        stats_accented = get_team_detail_stats(data, accented)
        # Test with non-accented name
        stats_non_accented = get_team_detail_stats(data, non_accented)
        
        if not stats_accented:
            print(f"   ❌ Failed to find team with accented name: '{accented}'")
            all_passed = False
            continue
            
        if not stats_non_accented:
            print(f"   ❌ Failed to find team with non-accented name: '{non_accented}'")
            all_passed = False
            continue
        
        # Compare results
        games_match = (stats_accented['basic_stats']['total_games'] == 
                      stats_non_accented['basic_stats']['total_games'])
        
        if games_match:
            print(f"   ✅ Both versions found the same team")
            print(f"      Games played: {stats_accented['basic_stats']['total_games']}")
            print(f"      Wins: {stats_accented['basic_stats']['wins']}")
        else:
            print(f"   ❌ Results don't match!")
            print(f"      Accented: {stats_accented['basic_stats']['total_games']} games")
            print(f"      Non-accented: {stats_non_accented['basic_stats']['total_games']} games")
            all_passed = False
    
    return all_passed


def test_team_hover_stats():
    """Test that team hover stats work with both accented and non-accented names"""
    print("\n" + "="*70)
    print("Testing get_team_hover_stats with accented team names")
    print("="*70)
    
    # Load data
    data = load_game_data()
    
    all_passed = True
    for accented, non_accented in TEAM_HOVER_TEST_TEAMS:
        print(f"\n🔍 Testing: {accented}")
        
        # Test with accented name
        stats_accented = get_team_hover_stats(data, accented)
        # Test with non-accented name
        stats_non_accented = get_team_hover_stats(data, non_accented)
        
        if not stats_accented:
            print(f"   ❌ Failed to find team with accented name: '{accented}'")
            all_passed = False
            continue
            
        if not stats_non_accented:
            print(f"   ❌ Failed to find team with non-accented name: '{non_accented}'")
            all_passed = False
            continue
        
        # Compare results
        wins_match = stats_accented['wins'] == stats_non_accented['wins']
        losses_match = stats_accented['losses'] == stats_non_accented['losses']
        
        if wins_match and losses_match:
            print(f"   ✅ Both versions found the same team")
            print(f"      Record: {stats_accented['wins']}-{stats_accented['losses']}")
        else:
            print(f"   ❌ Results don't match!")
            print(f"      Accented: {stats_accented['wins']}-{stats_accented['losses']}")
            print(f"      Non-accented: {stats_non_accented['wins']}-{stats_non_accented['losses']}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("ACCENT NORMALIZATION TEST SUITE")
    print("="*70)
    print("\nTesting that team names with accents work correctly in all lookups")
    
    test_results = []
    
    # Run all tests
    test_results.append(("Normalize Function", test_normalize_function()))
    test_results.append(("Team Detail Stats", test_team_detail_stats()))
    test_results.append(("Team Hover Stats", test_team_hover_stats()))
    
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
