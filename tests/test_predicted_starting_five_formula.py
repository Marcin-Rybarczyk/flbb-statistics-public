#!/usr/bin/env python3
"""
Unit tests for the improved predicted starting five formula.
Tests that the formula correctly weighs starting percentage, games played, and points.
"""

import sys
import os

# Add the root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import predict_starting_five


def test_formula_with_clear_starters():
    """Test that players with 100% starting percentage are always picked"""
    
    players = [
        {
            'Player Name': 'Star Player',
            'Starting Percentage': 100.0,
            'Games Played': 10,
            'Avg Points Per Game': 20.0
        },
        {
            'Player Name': 'Regular Starter',
            'Starting Percentage': 90.0,
            'Games Played': 10,
            'Avg Points Per Game': 15.0
        },
        {
            'Player Name': 'Sometimes Starter',
            'Starting Percentage': 50.0,
            'Games Played': 10,
            'Avg Points Per Game': 10.0
        },
        {
            'Player Name': 'Bench Player',
            'Starting Percentage': 10.0,
            'Games Played': 10,
            'Avg Points Per Game': 5.0
        },
        {
            'Player Name': 'Sub',
            'Starting Percentage': 0.0,
            'Games Played': 5,
            'Avg Points Per Game': 3.0
        },
        {
            'Player Name': 'Occasional Starter',
            'Starting Percentage': 80.0,
            'Games Played': 10,
            'Avg Points Per Game': 12.0
        },
        {
            'Player Name': 'Part Timer',
            'Starting Percentage': 70.0,
            'Games Played': 10,
            'Avg Points Per Game': 8.0
        },
    ]
    
    result = predict_starting_five(players)
    
    # Count how many players are marked as starting five
    starters = [p for p in result if p['Starting Five'] == 'true']
    bench = [p for p in result if p['Starting Five'] == 'false']
    
    print(f"\n✅ Test: Clear starters")
    print(f"   Starting Five ({len(starters)}):")
    for p in starters:
        print(f"      - {p['Player Name']}: {p['Starting Percentage']}% starting, {p['Games Played']} games, {p['Avg Points Per Game']} ppg")
    print(f"   Bench ({len(bench)}):")
    for p in bench:
        print(f"      - {p['Player Name']}: {p['Starting Percentage']}% starting, {p['Games Played']} games, {p['Avg Points Per Game']} ppg")
    
    assert len(starters) == 5, f"Expected 5 starters, got {len(starters)}"
    assert 'Star Player' in [p['Player Name'] for p in starters], "Star Player should be in starting five"
    
    return True


def test_formula_with_experience_factor():
    """Test that games played matters when starting percentages are similar"""
    
    players = [
        {
            'Player Name': 'Veteran A',
            'Starting Percentage': 80.0,
            'Games Played': 20,  # More experienced
            'Avg Points Per Game': 10.0
        },
        {
            'Player Name': 'Rookie A',
            'Starting Percentage': 80.0,
            'Games Played': 5,   # Less experienced
            'Avg Points Per Game': 10.0
        },
        {
            'Player Name': 'Veteran B',
            'Starting Percentage': 75.0,
            'Games Played': 25,
            'Avg Points Per Game': 10.0
        },
        {
            'Player Name': 'Rookie B',
            'Starting Percentage': 75.0,
            'Games Played': 4,
            'Avg Points Per Game': 10.0
        },
        {
            'Player Name': 'Mid Player',
            'Starting Percentage': 70.0,
            'Games Played': 15,
            'Avg Points Per Game': 10.0
        },
        {
            'Player Name': 'Bench Warmer',
            'Starting Percentage': 20.0,
            'Games Played': 10,
            'Avg Points Per Game': 5.0
        },
    ]
    
    result = predict_starting_five(players)
    starters = [p for p in result if p['Starting Five'] == 'true']
    
    print(f"\n✅ Test: Experience factor")
    print(f"   Starting Five:")
    for p in starters:
        print(f"      - {p['Player Name']}: {p['Starting Percentage']}% starting, {p['Games Played']} games")
    
    # Veterans should be preferred over rookies with same starting percentage
    starter_names = [p['Player Name'] for p in starters]
    assert 'Veteran A' in starter_names, "Veteran A should be preferred over Rookie A"
    assert 'Veteran B' in starter_names, "Veteran B should be preferred over Rookie B"
    
    return True


def test_formula_with_points_tiebreaker():
    """Test that points matter when starting percentage and games are similar"""
    
    players = [
        {
            'Player Name': 'Scorer A',
            'Starting Percentage': 80.0,
            'Games Played': 10,
            'Avg Points Per Game': 20.0  # High scorer
        },
        {
            'Player Name': 'Defender A',
            'Starting Percentage': 80.0,
            'Games Played': 10,
            'Avg Points Per Game': 5.0   # Low scorer
        },
        {
            'Player Name': 'Scorer B',
            'Starting Percentage': 75.0,
            'Games Played': 10,
            'Avg Points Per Game': 18.0
        },
        {
            'Player Name': 'Defender B',
            'Starting Percentage': 75.0,
            'Games Played': 10,
            'Avg Points Per Game': 6.0
        },
        {
            'Player Name': 'Average Player',
            'Starting Percentage': 70.0,
            'Games Played': 10,
            'Avg Points Per Game': 10.0
        },
        {
            'Player Name': 'Bench Player',
            'Starting Percentage': 30.0,
            'Games Played': 8,
            'Avg Points Per Game': 15.0
        },
    ]
    
    result = predict_starting_five(players)
    starters = [p for p in result if p['Starting Five'] == 'true']
    
    print(f"\n✅ Test: Points as tiebreaker")
    print(f"   Starting Five:")
    for p in starters:
        print(f"      - {p['Player Name']}: {p['Starting Percentage']}% starting, {p['Avg Points Per Game']} ppg")
    
    # Scorers should be slightly preferred over defenders with same starting % and games
    starter_names = [p['Player Name'] for p in starters]
    assert 'Scorer A' in starter_names, "Scorer A should be in starting five"
    assert 'Scorer B' in starter_names, "Scorer B should be in starting five"
    
    return True


def test_formula_balances_all_factors():
    """Test that the formula properly balances all three factors"""
    
    players = [
        {
            'Player Name': 'Complete Player',
            'Starting Percentage': 100.0,
            'Games Played': 20,
            'Avg Points Per Game': 25.0
        },
        {
            'Player Name': 'High Starter Low Points',
            'Starting Percentage': 90.0,
            'Games Played': 15,
            'Avg Points Per Game': 5.0
        },
        {
            'Player Name': 'Bench Scorer',
            'Starting Percentage': 20.0,
            'Games Played': 20,
            'Avg Points Per Game': 30.0  # Best scorer but rarely starts
        },
        {
            'Player Name': 'Experienced Bench',
            'Starting Percentage': 30.0,
            'Games Played': 30,  # Most games but low starting %
            'Avg Points Per Game': 8.0
        },
        {
            'Player Name': 'Regular Starter',
            'Starting Percentage': 85.0,
            'Games Played': 18,
            'Avg Points Per Game': 15.0
        },
        {
            'Player Name': 'Solid Starter',
            'Starting Percentage': 80.0,
            'Games Played': 20,
            'Avg Points Per Game': 12.0
        },
        {
            'Player Name': 'Frequent Starter',
            'Starting Percentage': 75.0,
            'Games Played': 16,
            'Avg Points Per Game': 10.0
        },
    ]
    
    result = predict_starting_five(players)
    starters = [p for p in result if p['Starting Five'] == 'true']
    bench = [p for p in result if p['Starting Five'] == 'false']
    
    print(f"\n✅ Test: Balanced formula")
    print(f"   Starting Five:")
    for p in starters:
        print(f"      - {p['Player Name']}: {p['Starting Percentage']}% starting, {p['Games Played']} games, {p['Avg Points Per Game']} ppg")
    print(f"   Bench:")
    for p in bench:
        print(f"      - {p['Player Name']}: {p['Starting Percentage']}% starting, {p['Games Played']} games, {p['Avg Points Per Game']} ppg")
    
    starter_names = [p['Player Name'] for p in starters]
    
    # Complete player should definitely be starting
    assert 'Complete Player' in starter_names, "Complete Player should be in starting five"
    
    # Starting percentage should be the primary factor, so high starters should be included
    assert 'Regular Starter' in starter_names, "Regular Starter should be in starting five"
    
    # Bench scorer shouldn't make it despite high points (starting % is too low)
    assert 'Bench Scorer' not in starter_names, "Bench Scorer shouldn't be in starting five (low starting %)"
    
    return True


def test_edge_case_empty_list():
    """Test that function handles empty player list"""
    result = predict_starting_five([])
    assert result == [], "Empty list should return empty list"
    print("\n✅ Test: Empty list handled correctly")
    return True


def test_edge_case_fewer_than_five():
    """Test that function handles fewer than 5 players"""
    players = [
        {'Player Name': 'Player 1', 'Starting Percentage': 80.0, 'Games Played': 10, 'Avg Points Per Game': 10.0},
        {'Player Name': 'Player 2', 'Starting Percentage': 70.0, 'Games Played': 8, 'Avg Points Per Game': 8.0},
        {'Player Name': 'Player 3', 'Starting Percentage': 60.0, 'Games Played': 6, 'Avg Points Per Game': 6.0},
    ]
    
    result = predict_starting_five(players)
    starters = [p for p in result if p['Starting Five'] == 'true']
    
    print(f"\n✅ Test: Fewer than 5 players")
    print(f"   All {len(starters)} players marked as starters")
    
    assert len(starters) == 3, "All 3 players should be marked as starters"
    return True


def test_edge_case_all_zeros():
    """Test that function handles players with all zero stats"""
    players = [
        {'Player Name': 'New Player 1', 'Starting Percentage': 0.0, 'Games Played': 0, 'Avg Points Per Game': 0.0},
        {'Player Name': 'New Player 2', 'Starting Percentage': 0.0, 'Games Played': 0, 'Avg Points Per Game': 0.0},
        {'Player Name': 'New Player 3', 'Starting Percentage': 0.0, 'Games Played': 0, 'Avg Points Per Game': 0.0},
        {'Player Name': 'New Player 4', 'Starting Percentage': 0.0, 'Games Played': 0, 'Avg Points Per Game': 0.0},
        {'Player Name': 'New Player 5', 'Starting Percentage': 0.0, 'Games Played': 0, 'Avg Points Per Game': 0.0},
        {'Player Name': 'New Player 6', 'Starting Percentage': 0.0, 'Games Played': 0, 'Avg Points Per Game': 0.0},
    ]
    
    result = predict_starting_five(players)
    starters = [p for p in result if p['Starting Five'] == 'true']
    bench = [p for p in result if p['Starting Five'] == 'false']
    
    print(f"\n✅ Test: All players with zero stats")
    print(f"   {len(starters)} players marked as starters, {len(bench)} on bench")
    
    # Should still select exactly 5 as starters (or all if fewer than 5)
    assert len(starters) == 5, "Should select 5 starters even with all zeros"
    assert len(bench) == 1, "Should have 1 bench player"
    return True


def main():
    """Run all tests"""
    print("=" * 70)
    print("Testing Improved Predicted Starting Five Formula")
    print("=" * 70)
    
    tests = [
        test_formula_with_clear_starters,
        test_formula_with_experience_factor,
        test_formula_with_points_tiebreaker,
        test_formula_balances_all_factors,
        test_edge_case_empty_list,
        test_edge_case_fewer_than_five,
        test_edge_case_all_zeros,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except AssertionError as e:
            print(f"\n❌ Test failed: {test.__name__}")
            print(f"   Error: {str(e)}")
            results.append(False)
        except Exception as e:
            print(f"\n❌ Test error: {test.__name__}")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 70)
    if all(results):
        print("✅ All tests passed!")
        print("=" * 70)
        return 0
    else:
        print(f"❌ {results.count(False)} test(s) failed")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
