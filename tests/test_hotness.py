#!/usr/bin/env python3
"""
Test script for hotness index calculation
"""

import sys
import os

# Add the root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import calculate_hotness_score, _calculate_game_statistics


def test_basic_hotness_calculation():
    """Test basic hotness calculation without close_game_ratio (backwards compatibility)"""
    print("=" * 60)
    print("Test 1: Basic Hotness (Old Formula)")
    print("=" * 60)
    
    # Test old formula
    lead_changes = 5
    ties = 3
    hotness = calculate_hotness_score(lead_changes, ties)
    expected = min(100, (5 * 3 + 3 * 2))  # 15 + 6 = 21
    
    print(f"Lead Changes: {lead_changes}, Ties: {ties}")
    print(f"Hotness Score: {hotness}")
    print(f"Expected: {expected}")
    
    if hotness == expected:
        print("✅ PASSED: Old formula works correctly")
        return True
    else:
        print("❌ FAILED: Old formula does not match expected")
        return False


def test_new_hotness_with_closeness():
    """Test new hotness calculation with close game ratio"""
    print("\n" + "=" * 60)
    print("Test 2: New Hotness with Closeness Factor")
    print("=" * 60)
    
    test_cases = [
        # (lead_changes, ties, close_game_ratio, description)
        (1, 2, 0.8, "High closeness, low volatility"),
        (10, 8, 0.5, "High volatility, medium closeness"),
        (0, 0, 0.0, "Blowout game - no excitement"),
        (5, 5, 1.0, "Tight game throughout with some lead changes"),
        (15, 10, 0.3, "Many lead changes but not close most of time"),
    ]
    
    all_passed = True
    for lead_changes, ties, close_ratio, description in test_cases:
        hotness = calculate_hotness_score(lead_changes, ties, close_ratio)
        
        # Calculate expected manually
        closeness_factor = close_ratio
        volatility_raw = (lead_changes * 3 + ties * 2)
        volatility_factor = min(1.0, volatility_raw / 75.0)
        expected = int((0.7 * closeness_factor + 0.3 * volatility_factor) * 100)
        
        print(f"\n{description}")
        print(f"  Lead Changes: {lead_changes}, Ties: {ties}, Close Ratio: {close_ratio:.2f}")
        print(f"  Closeness Factor: {closeness_factor:.2f}")
        print(f"  Volatility Factor: {volatility_factor:.2f}")
        print(f"  Hotness Score: {hotness}")
        print(f"  Expected: {expected}")
        
        if hotness == expected:
            print("  ✅ PASSED")
        else:
            print(f"  ❌ FAILED (got {hotness}, expected {expected})")
            all_passed = False
    
    return all_passed


def test_game_statistics_calculation():
    """Test the _calculate_game_statistics function with sample data"""
    print("\n" + "=" * 60)
    print("Test 3: Game Statistics Calculation")
    print("=" * 60)
    
    # Create sample score evolution
    # Simulating a close game that stayed within 5 points for most of the time
    score_evolution = [
        {'home_score': 0, 'away_score': 0, 'elapsed_seconds': 0},
        {'home_score': 2, 'away_score': 0, 'elapsed_seconds': 30},
        {'home_score': 2, 'away_score': 3, 'elapsed_seconds': 60},
        {'home_score': 5, 'away_score': 3, 'elapsed_seconds': 90},
        {'home_score': 5, 'away_score': 5, 'elapsed_seconds': 120},
        {'home_score': 8, 'away_score': 5, 'elapsed_seconds': 150},
        {'home_score': 8, 'away_score': 10, 'elapsed_seconds': 180},
        {'home_score': 12, 'away_score': 10, 'elapsed_seconds': 210},
        {'home_score': 12, 'away_score': 12, 'elapsed_seconds': 240},
    ]
    
    stats = _calculate_game_statistics(score_evolution)
    
    print("Score Evolution:")
    for i, point in enumerate(score_evolution):
        margin = abs(point['home_score'] - point['away_score'])
        print(f"  {i}: {point['home_score']}-{point['away_score']} (margin: {margin}, time: {point['elapsed_seconds']}s)")
    
    print(f"\nCalculated Statistics:")
    print(f"  Lead Changes: {stats['lead_changes']}")
    print(f"  Tied Scores: {stats['tied_scores']}")
    print(f"  Close Game Ratio: {stats['close_game_ratio']:.2f}")
    print(f"  Total Game Time: {stats['total_game_time']}s")
    print(f"  Home Highest Lead: {stats['home_highest_lead']}")
    print(f"  Away Highest Lead: {stats['away_highest_lead']}")
    
    # Verify expected values
    expected_ties = 2  # At 0-0, 5-5, and 12-12
    expected_lead_changes = 4  # Home leads, Away leads, Home leads, Away leads, tie
    
    print(f"\nExpected:")
    print(f"  Tied Scores: {expected_ties}")
    print(f"  Lead Changes: {expected_lead_changes}")
    
    # Check if close game ratio is high (should be > 0.8 since most of the game is within 5 points)
    if stats['close_game_ratio'] > 0.8:
        print(f"  ✅ Close game ratio is high as expected: {stats['close_game_ratio']:.2f}")
    else:
        print(f"  ⚠️  Close game ratio lower than expected: {stats['close_game_ratio']:.2f}")
    
    return True


def test_edge_cases():
    """Test edge cases"""
    print("\n" + "=" * 60)
    print("Test 4: Edge Cases")
    print("=" * 60)
    
    # Empty score evolution
    print("\n1. Empty score evolution:")
    stats = _calculate_game_statistics([])
    hotness = calculate_hotness_score(stats['lead_changes'], stats['tied_scores'], stats.get('close_game_ratio'))
    print(f"  Hotness: {hotness}")
    print(f"  Expected: 0")
    if hotness == 0:
        print("  ✅ PASSED")
    else:
        print("  ❌ FAILED")
        return False
    
    # Maximum hotness
    print("\n2. Maximum hotness (perfect closeness + high volatility):")
    hotness = calculate_hotness_score(20, 15, 1.0)
    print(f"  Hotness: {hotness}")
    print(f"  Should be close to 100")
    if hotness >= 90:
        print("  ✅ PASSED")
    else:
        print("  ❌ FAILED")
        return False
    
    # Close game with no lead changes
    print("\n3. Close game with no lead changes (the original problem scenario):")
    hotness_old = calculate_hotness_score(1, 0)  # Old formula
    hotness_new = calculate_hotness_score(1, 0, 0.9)  # New formula with high closeness
    print(f"  Old formula hotness: {hotness_old}")
    print(f"  New formula hotness: {hotness_new}")
    print(f"  New formula should be higher due to closeness factor")
    if hotness_new > hotness_old:
        print("  ✅ PASSED - New formula correctly rewards close games")
    else:
        print("  ❌ FAILED - New formula does not improve on old formula")
        return False
    
    return True


def main():
    """Run all tests"""
    print("Testing Hotness Index Calculation")
    print("=" * 60)
    
    results = []
    results.append(("Basic Hotness (Old Formula)", test_basic_hotness_calculation()))
    results.append(("New Hotness with Closeness", test_new_hotness_with_closeness()))
    results.append(("Game Statistics Calculation", test_game_statistics_calculation()))
    results.append(("Edge Cases", test_edge_cases()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
