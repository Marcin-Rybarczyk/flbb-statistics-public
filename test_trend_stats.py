#!/usr/bin/env python3
"""
Test script for the enhanced team fouls trend functionality.
This tests the calculate_fouls_trend_statistics function.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils import calculate_fouls_trend_statistics

def test_trend_statistics():
    """Test the trend statistics calculation."""
    print("Testing calculate_fouls_trend_statistics function...")
    print("=" * 60)
    
    # Test case 1: Improving trend (decreasing fouls)
    print("\nTest 1: Improving trend (decreasing fouls)")
    fouls_improving = [25, 24, 22, 21, 20, 18, 17, 16]
    stats = calculate_fouls_trend_statistics(fouls_improving)
    print(f"Input: {fouls_improving}")
    print(f"Average: {stats['average']}")
    print(f"Trend direction: {stats['trend_direction']} {stats['trend_indicator']}")
    print(f"Slope: {stats['slope']}")
    print(f"First half avg: {stats['first_half_avg']}")
    print(f"Second half avg: {stats['second_half_avg']}")
    print(f"Change: {stats['change_percent']}%")
    assert stats['trend_direction'] == 'improving', "Should detect improving trend"
    assert stats['slope'] < 0, "Slope should be negative for improving trend"
    print("✓ Test 1 passed!")
    
    # Test case 2: Worsening trend (increasing fouls)
    print("\nTest 2: Worsening trend (increasing fouls)")
    fouls_worsening = [15, 16, 18, 19, 21, 22, 24, 25]
    stats = calculate_fouls_trend_statistics(fouls_worsening)
    print(f"Input: {fouls_worsening}")
    print(f"Average: {stats['average']}")
    print(f"Trend direction: {stats['trend_direction']} {stats['trend_indicator']}")
    print(f"Slope: {stats['slope']}")
    print(f"First half avg: {stats['first_half_avg']}")
    print(f"Second half avg: {stats['second_half_avg']}")
    print(f"Change: {stats['change_percent']}%")
    assert stats['trend_direction'] == 'worsening', "Should detect worsening trend"
    assert stats['slope'] > 0, "Slope should be positive for worsening trend"
    print("✓ Test 2 passed!")
    
    # Test case 3: Stable trend
    print("\nTest 3: Stable trend")
    fouls_stable = [20, 19, 21, 20, 20, 21, 19, 20]
    stats = calculate_fouls_trend_statistics(fouls_stable)
    print(f"Input: {fouls_stable}")
    print(f"Average: {stats['average']}")
    print(f"Trend direction: {stats['trend_direction']} {stats['trend_indicator']}")
    print(f"Slope: {stats['slope']}")
    print(f"First half avg: {stats['first_half_avg']}")
    print(f"Second half avg: {stats['second_half_avg']}")
    print(f"Change: {stats['change_percent']}%")
    assert stats['trend_direction'] == 'stable', "Should detect stable trend"
    assert abs(stats['slope']) < 0.1, "Slope should be near zero for stable trend"
    print("✓ Test 3 passed!")
    
    # Test case 4: Empty list
    print("\nTest 4: Empty list")
    fouls_empty = []
    stats = calculate_fouls_trend_statistics(fouls_empty)
    print(f"Input: {fouls_empty}")
    print(f"Result: {stats}")
    assert stats['average'] == 0, "Empty list should return zero average"
    print("✓ Test 4 passed!")
    
    # Test case 5: Single value
    print("\nTest 5: Single value")
    fouls_single = [20]
    stats = calculate_fouls_trend_statistics(fouls_single)
    print(f"Input: {fouls_single}")
    print(f"Average: {stats['average']}")
    print(f"Trend direction: {stats['trend_direction']}")
    assert stats['average'] == 20, "Single value should return that value as average"
    print("✓ Test 5 passed!")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")

if __name__ == '__main__':
    test_trend_statistics()
