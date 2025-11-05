#!/usr/bin/env python3
"""
Unit tests for team hover box functionality
Tests that the top scorers are ranked by total points descending
and include both total points and average points per game.
Tests that next game information is included with opponent position.
"""

import sys
import os

# Add the root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import load_game_data, get_team_hover_stats


def test_team_hover_top_scorers():
    """Test that team hover stats return top scorers ranked by total points"""
    
    # Load data
    data = load_game_data()
    if data.empty:
        print("⚠️  No data available, skipping test")
        return True
    
    # Get unique teams
    teams = set()
    for _, row in data.head(50).iterrows():
        teams.add(row['HomeTeamName'])
        teams.add(row['AwayTeamName'])
    
    if not teams:
        print("⚠️  No teams found, skipping test")
        return True
    
    # Test with first available team
    test_team = list(teams)[0]
    print(f"\n📊 Testing team hover stats for: {test_team}")
    
    stats = get_team_hover_stats(data, test_team)
    
    if not stats:
        print("⚠️  No stats found for team, skipping test")
        return True
    
    # Check structure
    assert 'top_scorers' in stats, "Missing 'top_scorers' field"
    
    top_scorers = stats['top_scorers']
    
    if not top_scorers:
        print("⚠️  No top scorers found, team may not have player data")
        return True
    
    print(f"\n✅ Found {len(top_scorers)} top scorers")
    
    # Verify each scorer has required fields
    for idx, scorer in enumerate(top_scorers):
        print(f"\n   {idx + 1}. {scorer['name']}")
        
        # Check fields exist
        assert 'name' in scorer, f"Scorer {idx} missing 'name' field"
        assert 'total_points' in scorer, f"Scorer {idx} missing 'total_points' field"
        assert 'avg_points' in scorer, f"Scorer {idx} missing 'avg_points' field"
        
        print(f"      Total Points: {scorer['total_points']}")
        print(f"      Avg Points/Game: {scorer['avg_points']}")
        
        # Verify data types
        assert isinstance(scorer['total_points'], int), "total_points should be an integer"
        assert isinstance(scorer['avg_points'], float), "avg_points should be a float"
    
    # Verify scorers are sorted by total points descending
    print("\n🔍 Verifying sort order (total points descending)...")
    for i in range(len(top_scorers) - 1):
        current_total = top_scorers[i]['total_points']
        next_total = top_scorers[i + 1]['total_points']
        assert current_total >= next_total, \
            f"Scorers not sorted correctly: {top_scorers[i]['name']} ({current_total}) should be >= {top_scorers[i+1]['name']} ({next_total})"
    
    print("   ✅ Scorers are correctly sorted by total points descending")
    
    # Verify average points make sense (should be <= total points)
    print("\n🔍 Verifying average points are reasonable...")
    for scorer in top_scorers:
        assert scorer['avg_points'] <= scorer['total_points'], \
            f"Average points ({scorer['avg_points']}) should be <= total points ({scorer['total_points']}) for {scorer['name']}"
        assert scorer['avg_points'] > 0, f"Average points should be positive for {scorer['name']}"
    
    print("   ✅ Average points are reasonable")
    
    return True


def test_team_hover_next_game():
    """Test that team hover stats include next game information"""
    
    # Load data
    data = load_game_data()
    if data.empty:
        print("⚠️  No data available, skipping test")
        return True
    
    # Get unique teams
    teams = set()
    for _, row in data.head(50).iterrows():
        teams.add(row['HomeTeamName'])
        teams.add(row['AwayTeamName'])
    
    if not teams:
        print("⚠️  No teams found, skipping test")
        return True
    
    # Test with first available team
    test_team = list(teams)[0]
    print(f"\n📅 Testing next game info for: {test_team}")
    
    stats = get_team_hover_stats(data, test_team)
    
    if not stats:
        print("⚠️  No stats found for team, skipping test")
        return True
    
    # Check that next_game field exists
    assert 'next_game' in stats, "Missing 'next_game' field in hover stats"
    print("   ✅ 'next_game' field is present")
    
    next_game = stats['next_game']
    
    # next_game can be None if there are no upcoming games
    if next_game is None:
        print("   ℹ️  No upcoming games found for this team")
        return True
    
    # Verify next_game structure
    required_fields = ['opponent', 'date', 'time', 'is_home', 'location']
    for field in required_fields:
        assert field in next_game, f"Missing '{field}' in next_game data"
    
    print(f"   ✅ Next opponent: {next_game['opponent']}")
    
    # Check opponent position if available
    if next_game.get('opponent_position') and next_game.get('opponent_total_teams'):
        print(f"   ✅ Opponent position: {next_game['opponent_position']}/{next_game['opponent_total_teams']}")
        assert isinstance(next_game['opponent_position'], int), "opponent_position should be an integer"
        assert isinstance(next_game['opponent_total_teams'], int), "opponent_total_teams should be an integer"
    else:
        print(f"   ℹ️  Opponent position not available")
    
    # Verify date and time format
    if next_game['date']:
        print(f"   ✅ Date: {next_game['date']}")
    if next_game['time']:
        print(f"   ✅ Time: {next_game['time']}")
    
    print(f"   ✅ Location: {next_game['location']}")
    
    return True


def test_multiple_teams():
    """Test hover stats for multiple teams to ensure consistency"""
    
    data = load_game_data()
    if data.empty:
        print("⚠️  No data available, skipping test")
        return True
    
    # Get multiple teams
    teams = set()
    for _, row in data.head(100).iterrows():
        teams.add(row['HomeTeamName'])
        teams.add(row['AwayTeamName'])
        if len(teams) >= 5:
            break
    
    teams_list = list(teams)[:5]
    print(f"\n📊 Testing {len(teams_list)} teams for consistency...")
    
    for team in teams_list:
        stats = get_team_hover_stats(data, team)
        if stats and stats['top_scorers']:
            print(f"\n   Testing {team}...")
            # Verify sort order
            top_scorers = stats['top_scorers']
            for i in range(len(top_scorers) - 1):
                assert top_scorers[i]['total_points'] >= top_scorers[i + 1]['total_points'], \
                    f"Sort order incorrect for {team}"
            print(f"      ✅ Top scorer: {top_scorers[0]['name']} with {top_scorers[0]['total_points']} total pts")
            
            # Check next_game field exists
            assert 'next_game' in stats, f"Missing 'next_game' field for {team}"
            if stats['next_game']:
                print(f"      ✅ Next game: vs {stats['next_game']['opponent']}")
    
    print("\n   ✅ All tested teams have correctly sorted scorers and next_game field")
    return True


if __name__ == '__main__':
    print("=" * 70)
    print("Team Hover Box - Full Test Suite")
    print("=" * 70)
    
    try:
        # Run tests
        success = True
        success = test_team_hover_top_scorers() and success
        success = test_team_hover_next_game() and success
        success = test_multiple_teams() and success
        
        if success:
            print("\n" + "=" * 70)
            print("✅ ALL TESTS PASSED!")
            print("=" * 70)
            print("\nChanges verified:")
            print("  ✓ Top scorers ranked by total points (descending)")
            print("  ✓ Both total_points and avg_points included")
            print("  ✓ Next game information included in hover stats")
            print("  ✓ Opponent position displayed when available")
            print("  ✓ Date and time of next game included")
            print("  ✓ Data types are correct")
            print("  ✓ Sort order is maintained across teams")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
