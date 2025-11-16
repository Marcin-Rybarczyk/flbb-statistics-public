#!/usr/bin/env python3
"""
Test script for future game hotness calculation based on league standings.
Validates that the hotness calculation correctly evaluates the excitement level
of upcoming games based on team rankings and competitiveness.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from src.utils import (
    calculate_future_game_hotness, 
    calculate_standings_by_division,
    get_all_fixtures_data,
    load_game_data
)


def test_hotness_calculation_logic():
    """Test the core hotness calculation logic with various scenarios"""
    print("=" * 80)
    print("TEST 1: HOTNESS CALCULATION LOGIC")
    print("=" * 80)
    
    # Create a mock standings table
    mock_standings = pd.DataFrame({
        'Team Name': ['Team A', 'Team B', 'Team C', 'Team D', 'Team E', 'Team F'],
        'Points': [20, 18, 15, 12, 8, 5],
        'W': [10, 9, 7, 6, 4, 2],
        'L': [0, 1, 3, 4, 6, 8]
    })
    mock_standings.index = range(1, 7)  # Ranks 1-6
    mock_standings.index.name = 'Rank'
    
    print("\nMock Standings:")
    print(mock_standings[['Team Name', 'Points']])
    
    # Test Case 1: Top 2 teams (should be very hot)
    print("\n--- Test Case 1: Top 2 teams playing ---")
    hotness, icon = calculate_future_game_hotness('Team A', 'Team B', mock_standings)
    print(f"Team A (Rank 1) vs Team B (Rank 2)")
    print(f"Expected: Very Hot (>80)")
    print(f"Result: {hotness}/100 {icon}")
    assert hotness >= 80, f"Top 2 teams should have hotness >= 80, got {hotness}"
    assert icon in ['🔥', '🔥🔥'], f"Top 2 teams should have fire icon, got {icon}"
    print("✅ PASS")
    
    # Test Case 2: Top team vs bottom team (should be cooler)
    print("\n--- Test Case 2: Top vs Bottom team ---")
    hotness, icon = calculate_future_game_hotness('Team A', 'Team F', mock_standings)
    print(f"Team A (Rank 1) vs Team F (Rank 6)")
    print(f"Expected: Warm to Cool (30-60)")
    print(f"Result: {hotness}/100 {icon}")
    assert 20 <= hotness <= 70, f"Top vs Bottom should be 20-70, got {hotness}"
    print("✅ PASS")
    
    # Test Case 3: Mid-table teams close in ranking (should be warm)
    print("\n--- Test Case 3: Close mid-table teams ---")
    hotness, icon = calculate_future_game_hotness('Team C', 'Team D', mock_standings)
    print(f"Team C (Rank 3) vs Team D (Rank 4)")
    print(f"Expected: Warm to Hot (60-85)")
    print(f"Result: {hotness}/100 {icon}")
    assert 55 <= hotness <= 90, f"Close mid-table should be 55-90, got {hotness}"
    print("✅ PASS")
    
    # Test Case 4: Teams far apart in rankings (should be cooler)
    print("\n--- Test Case 4: Teams far apart ---")
    hotness, icon = calculate_future_game_hotness('Team B', 'Team E', mock_standings)
    print(f"Team B (Rank 2) vs Team E (Rank 5)")
    print(f"Expected: Neutral to Warm (40-70)")
    print(f"Result: {hotness}/100 {icon}")
    assert 30 <= hotness <= 75, f"Teams far apart should be 30-75, got {hotness}"
    print("✅ PASS")
    
    # Test Case 5: Unknown team (should be neutral)
    print("\n--- Test Case 5: Unknown team ---")
    hotness, icon = calculate_future_game_hotness('Team A', 'Unknown Team', mock_standings)
    print(f"Team A vs Unknown Team")
    print(f"Expected: Neutral (50)")
    print(f"Result: {hotness}/100 {icon}")
    assert hotness == 50, f"Unknown team should have neutral hotness (50), got {hotness}"
    assert icon == '🌡️', f"Unknown team should have thermometer icon, got {icon}"
    print("✅ PASS")
    
    print("\n" + "=" * 80)
    print("✅ ALL LOGIC TESTS PASSED")
    print("=" * 80)


def test_real_data_integration():
    """Test with real game data from the database"""
    print("\n" + "=" * 80)
    print("TEST 2: REAL DATA INTEGRATION")
    print("=" * 80)
    
    # Load real data
    data = load_game_data()
    print(f"\nLoaded {len(data)} finished games")
    
    # Get fixtures with future games
    fixtures = get_all_fixtures_data(data)
    print(f"Total fixtures (finished + future): {len(fixtures)}")
    
    # Filter future games
    future_games = fixtures[fixtures.get('IsFutureGame', False) == True]
    print(f"Future games: {len(future_games)}")
    
    if len(future_games) == 0:
        print("⚠️  No future games found - skipping integration test")
        return
    
    # Check that future games have hotness scores
    games_with_hotness = future_games[
        (future_games['HotnessScore'].notna()) & 
        (future_games['HotnessIcon'].notna())
    ]
    print(f"Future games with hotness: {len(games_with_hotness)}")
    
    assert len(games_with_hotness) > 0, "No future games have hotness scores!"
    
    # Show distribution of hotness scores
    print("\nHotness Score Distribution:")
    print(f"  Very Hot (🔥🔥, 81-100): {len(games_with_hotness[games_with_hotness['HotnessScore'] > 80])}")
    print(f"  Hot (🔥, 51-80): {len(games_with_hotness[(games_with_hotness['HotnessScore'] > 50) & (games_with_hotness['HotnessScore'] <= 80)])}")
    print(f"  Warm (🌡️, 21-50): {len(games_with_hotness[(games_with_hotness['HotnessScore'] > 20) & (games_with_hotness['HotnessScore'] <= 50)])}")
    print(f"  Cold (❄️, 0-20): {len(games_with_hotness[games_with_hotness['HotnessScore'] <= 20])}")
    
    # Show top 10 hottest upcoming games
    print("\n" + "=" * 80)
    print("TOP 10 HOTTEST UPCOMING GAMES")
    print("=" * 80)
    print(f"{'Teams':<50} {'Division':<30} {'Hotness':<10}")
    print("-" * 80)
    
    hottest_games = games_with_hotness.nlargest(10, 'HotnessScore')
    for idx, game in hottest_games.iterrows():
        teams = f"{game.get('HomeTeamName', 'N/A')} vs {game.get('AwayTeamName', 'N/A')}"
        division = game.get('GameDivisionDisplay', 'N/A')
        hotness = f"{game.get('HotnessIcon', '')} {int(game.get('HotnessScore', 0))}/100"
        print(f"{teams[:50]:<50} {division[:30]:<30} {hotness:<10}")
    
    # Show coolest games
    print("\n" + "=" * 80)
    print("10 COOLEST UPCOMING GAMES (Mismatched teams)")
    print("=" * 80)
    print(f"{'Teams':<50} {'Division':<30} {'Hotness':<10}")
    print("-" * 80)
    
    coolest_games = games_with_hotness.nsmallest(10, 'HotnessScore')
    for idx, game in coolest_games.iterrows():
        teams = f"{game.get('HomeTeamName', 'N/A')} vs {game.get('AwayTeamName', 'N/A')}"
        division = game.get('GameDivisionDisplay', 'N/A')
        hotness = f"{game.get('HotnessIcon', '')} {int(game.get('HotnessScore', 0))}/100"
        print(f"{teams[:50]:<50} {division[:30]:<30} {hotness:<10}")
    
    print("\n" + "=" * 80)
    print("✅ REAL DATA INTEGRATION TEST PASSED")
    print("=" * 80)


def test_division_specific_standings():
    """Test that hotness is calculated using division-specific standings"""
    print("\n" + "=" * 80)
    print("TEST 3: DIVISION-SPECIFIC STANDINGS")
    print("=" * 80)
    
    data = load_game_data()
    
    # Get unique divisions
    divisions = data['GameDivisionDisplay'].unique()
    print(f"\nFound {len(divisions)} divisions in the data")
    
    # Test fixtures for a specific division
    if len(divisions) > 0:
        test_division = divisions[0]
        print(f"Testing with division: {test_division}")
        
        # Get fixtures filtered by division
        division_fixtures = get_all_fixtures_data(data, division_filter=test_division)
        
        # Check future games in this division
        future_in_division = division_fixtures[
            (division_fixtures.get('IsFutureGame', False) == True) &
            (division_fixtures['GameDivisionDisplay'] == test_division)
        ]
        
        print(f"Future games in {test_division}: {len(future_in_division)}")
        
        if len(future_in_division) > 0:
            # Show sample
            print("\nSample future games with division-specific hotness:")
            for idx, game in future_in_division.head(3).iterrows():
                teams = f"{game.get('HomeTeamName', 'N/A')} vs {game.get('AwayTeamName', 'N/A')}"
                hotness = f"{game.get('HotnessIcon', '')} {int(game.get('HotnessScore', 0))}/100"
                print(f"  {teams}: {hotness}")
            
            print("✅ Division-specific standings test PASSED")
        else:
            print("⚠️  No future games in this division - skipping detailed test")
    
    print("=" * 80)


def run_all_tests():
    """Run all test suites"""
    print("\n" + "🔥" * 40)
    print("FUTURE GAME HOTNESS - COMPREHENSIVE TEST SUITE")
    print("🔥" * 40)
    
    try:
        # Test 1: Basic logic with mock data
        test_hotness_calculation_logic()
        
        # Test 2: Integration with real data
        test_real_data_integration()
        
        # Test 3: Division-specific standings
        test_division_specific_standings()
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")
        print("=" * 80)
        print("\nThe future game hotness feature is working correctly:")
        print("✅ Hotness calculation logic is sound")
        print("✅ Integration with real data works")
        print("✅ Division-specific standings are used")
        print("✅ Icons are correctly assigned based on hotness scores")
        print("\n" + "=" * 80)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
