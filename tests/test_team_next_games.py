#!/usr/bin/env python3
"""
Unit tests for team next games functionality
Tests that the next 5 games are correctly retrieved and formatted.
"""

import sys
import os

# Add the root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import load_game_data, get_team_detail_stats, get_team_next_games


def test_get_team_next_games():
    """Test that get_team_next_games returns correct structure and data"""
    
    # Load data
    data = load_game_data()
    if data.empty:
        print("⚠️  No data available, skipping test")
        return True
    
    # Test with a known team
    test_team = "AB Contern"
    print(f"\n📅 Testing next games for: {test_team}")
    
    next_games = get_team_next_games(test_team, limit=5)
    
    print(f"   Found {len(next_games)} upcoming games")
    
    # Check that we got results (may be 0 if no future games)
    assert isinstance(next_games, list), "next_games should be a list"
    assert len(next_games) <= 5, "Should return at most 5 games"
    
    # If we have games, check their structure
    if next_games:
        game = next_games[0]
        
        # Check required fields
        required_fields = ['game_id', 'date', 'division', 'opponent', 'is_home', 'location', 'game_url']
        for field in required_fields:
            assert field in game, f"Missing required field: {field}"
        
        # Check data types
        assert isinstance(game['is_home'], bool), "is_home should be boolean"
        assert game['location'] in ['Home', 'Away'], "location should be 'Home' or 'Away'"
        
        # Check that games are sorted by date (if dates are available)
        dates = [g['date'] for g in next_games if g['date']]
        if len(dates) > 1:
            assert dates == sorted(dates), "Games should be sorted by date (earliest first)"
        
        print(f"   ✅ First game: {game['date']} vs {game['opponent']} ({game['location']})")
    else:
        print(f"   ℹ️  No upcoming games found for {test_team}")
    
    return True


def test_team_detail_stats_includes_next_games():
    """Test that get_team_detail_stats includes next_games field"""
    
    # Load data
    data = load_game_data()
    if data.empty:
        print("⚠️  No data available, skipping test")
        return True
    
    # Test with a known team
    test_team = "AB Contern"
    print(f"\n📊 Testing team detail stats for: {test_team}")
    
    team_stats = get_team_detail_stats(data, test_team)
    
    if not team_stats:
        print("⚠️  No stats found for team, skipping test")
        return True
    
    # Check that next_games field exists
    assert 'next_games' in team_stats, "team_stats should include 'next_games' field"
    assert isinstance(team_stats['next_games'], list), "next_games should be a list"
    
    print(f"   ✅ Team stats include {len(team_stats['next_games'])} upcoming games")
    
    return True


def test_multiple_teams():
    """Test next games functionality across multiple teams"""
    
    # Load data
    data = load_game_data()
    if data.empty:
        print("⚠️  No data available, skipping test")
        return True
    
    print(f"\n🔄 Testing multiple teams...")
    
    # Get some teams
    teams = set()
    for _, row in data.head(100).iterrows():
        teams.add(row['HomeTeamName'])
        teams.add(row['AwayTeamName'])
        if len(teams) >= 3:
            break
    
    success_count = 0
    for team in list(teams)[:3]:
        team_stats = get_team_detail_stats(data, team)
        if team_stats and 'next_games' in team_stats:
            next_games = team_stats['next_games']
            print(f"   {team}: {len(next_games)} upcoming games")
            success_count += 1
    
    assert success_count > 0, "Should successfully get next games for at least one team"
    print(f"   ✅ Successfully tested {success_count} teams")
    
    return True


def main():
    """Run all tests"""
    print("=" * 70)
    print("Testing Team Next Games Functionality")
    print("=" * 70)
    
    tests = [
        test_get_team_next_games,
        test_team_detail_stats_includes_next_games,
        test_multiple_teams
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
