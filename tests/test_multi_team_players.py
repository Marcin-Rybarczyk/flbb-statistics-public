"""
Test multi-team player functionality in team detail stats.

This test verifies that the system correctly identifies players who play
for multiple teams and provides this information in the team detail stats.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import load_game_data, get_team_detail_stats, _get_multi_team_players


def test_multi_team_player_detection():
    """Test that multi-team players are correctly identified."""
    print("Testing multi-team player detection...")
    
    # Load data
    data = load_game_data()
    assert not data.empty, "Data should not be empty"
    print(f"✓ Loaded {len(data)} games")
    
    # Get multi-team players
    multi_team_players = _get_multi_team_players(data)
    assert isinstance(multi_team_players, dict), "Should return a dictionary"
    assert len(multi_team_players) > 0, "Should find multi-team players"
    print(f"✓ Found {len(multi_team_players)} multi-team players")
    
    # Verify structure
    for player_name, teams in multi_team_players.items():
        assert isinstance(teams, list), f"Teams for {player_name} should be a list"
        assert len(teams) > 1, f"{player_name} should play for multiple teams"
    print("✓ Multi-team player structure is correct")


def test_team_detail_includes_multi_team_info():
    """Test that team detail stats include multi-team player information."""
    print("\nTesting team detail stats include multi-team info...")
    
    # Load data
    data = load_game_data()
    
    # Get team stats for a team known to have multi-team players
    team_stats = get_team_detail_stats(data, 'Racing Luxembourg C')
    assert team_stats is not None, "Should return team stats"
    assert 'player_stats' in team_stats, "Should include player_stats"
    
    players = team_stats['player_stats']['all_players']
    assert len(players) > 0, "Should have players"
    print(f"✓ Team has {len(players)} players")
    
    # Check that player dictionaries include multi-team fields
    for player in players:
        assert 'plays_multiple_teams' in player, "Player should have plays_multiple_teams field"
        assert 'other_teams' in player, "Player should have other_teams field"
        assert isinstance(player['plays_multiple_teams'], bool), "plays_multiple_teams should be boolean"
        assert isinstance(player['other_teams'], list), "other_teams should be a list"
    print("✓ All players have multi-team fields")
    
    # Check that at least some players are identified as multi-team
    multi_team_count = sum(1 for p in players if p['plays_multiple_teams'])
    assert multi_team_count > 0, "Should have at least one multi-team player"
    print(f"✓ Found {multi_team_count} multi-team players in team")


def test_specific_multi_team_player():
    """Test specific known multi-team player."""
    print("\nTesting specific multi-team player...")
    
    data = load_game_data()
    team_stats = get_team_detail_stats(data, 'Racing Luxembourg C')
    players = team_stats['player_stats']['all_players']
    
    # Find BAH Sofiane Amadou (known multi-team player)
    bah = next((p for p in players if p['name'] == 'BAH Sofiane Amadou'), None)
    
    if bah:
        assert bah['plays_multiple_teams'] == True, "BAH should play for multiple teams"
        assert len(bah['other_teams']) > 0, "BAH should have other teams listed"
        print(f"✓ BAH Sofiane Amadou plays for multiple teams: {bah['other_teams']}")
    else:
        print("⚠ BAH Sofiane Amadou not found in team (data may have changed)")


def test_non_multi_team_player():
    """Test that players with only one team are correctly identified."""
    print("\nTesting non-multi-team player...")
    
    data = load_game_data()
    team_stats = get_team_detail_stats(data, 'Racing Luxembourg C')
    players = team_stats['player_stats']['all_players']
    
    # Find a player who plays for only one team
    single_team_players = [p for p in players if not p['plays_multiple_teams']]
    
    if single_team_players:
        player = single_team_players[0]
        assert player['plays_multiple_teams'] == False, "Player should not be multi-team"
        assert len(player['other_teams']) == 0, "Player should have no other teams"
        print(f"✓ {player['name']} plays for only one team")
    else:
        print("⚠ All players in this team play for multiple teams")


if __name__ == '__main__':
    print("=" * 60)
    print("Multi-Team Player Functionality Tests")
    print("=" * 60)
    
    try:
        test_multi_team_player_detection()
        test_team_detail_includes_multi_team_info()
        test_specific_multi_team_player()
        test_non_multi_team_player()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
