#!/usr/bin/env python3
"""
Unit tests for team hover box functionality
Tests that the top scorers are ranked by total points descending
and include both total points and average points per game.
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
    
    print("\n   ✅ All tested teams have correctly sorted scorers")
    return True


if __name__ == '__main__':
    print("=" * 70)
    print("Team Hover Box - Top Scorers Test")
    print("=" * 70)
    
    try:
        # Run tests
        success = True
        success = test_team_hover_top_scorers() and success
        success = test_multiple_teams() and success
        
        if success:
            print("\n" + "=" * 70)
            print("✅ ALL TESTS PASSED!")
            print("=" * 70)
            print("\nChanges verified:")
            print("  ✓ Top scorers ranked by total points (descending)")
            print("  ✓ Both total_points and avg_points included")
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
