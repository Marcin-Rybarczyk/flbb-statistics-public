#!/usr/bin/env python3
"""
Test script to verify forfeit detection in standings calculation.
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
from utils import calculate_standings

def test_forfeit_detection():
    """Test that forfeit games are correctly marked with 'F' in Last 5 Games"""
    
    # Create sample data with a forfeit game
    test_data = pd.DataFrame([
        {
            'HomeTeamName': 'Team A',
            'AwayTeamName': 'Team B',
            'FinalHomeScore': 80,
            'FinalAwayScore': 70,
            'HomeTeamLeaguePoints': 2,
            'AwayTeamLeaguePoints': 1,
            'GameId': 'game1',
            'DateTime': '2025-01-01 18:00:00',
            'GameEvents': '[]'  # Regular game
        },
        {
            'HomeTeamName': 'Team A',
            'AwayTeamName': 'Team C',
            'FinalHomeScore': 0,
            'FinalAwayScore': 0,
            'HomeTeamLeaguePoints': 1,
            'AwayTeamLeaguePoints': 1,
            'GameId': 'game2',
            'DateTime': '2025-01-08 18:00:00',
            'GameEvents': "[{'EventAction': 'Forfeit', 'EventDateTime': '2025-01-08', 'EventActor': '* System *'}]"  # Forfeit game
        },
        {
            'HomeTeamName': 'Team A',
            'AwayTeamName': 'Team D',
            'FinalHomeScore': 75,
            'FinalAwayScore': 85,
            'HomeTeamLeaguePoints': 1,
            'AwayTeamLeaguePoints': 2,
            'GameId': 'game3',
            'DateTime': '2025-01-15 18:00:00',
            'GameEvents': '[]'  # Regular game
        }
    ])
    
    # Calculate standings
    standings = calculate_standings(test_data)
    
    print("Testing forfeit detection in standings calculation...")
    print("\nStandings table:")
    print(standings[['Team Name', 'Games', 'W', 'L', 'Points']])
    
    # Check Team A's last 5 games
    team_a_row = standings[standings['Team Name'] == 'Team A']
    if not team_a_row.empty:
        last_5_games = team_a_row['Last 5 Games'].iloc[0]
        print(f"\nTeam A's Last 5 Games (most recent first):")
        for game in last_5_games:
            print(f"  Game {game['game_id']}: {game['result']}")
        
        # Verify forfeit is marked with 'F'
        results = [game['result'] for game in last_5_games]
        if 'F' in results:
            print("\n✓ SUCCESS: Forfeit game correctly marked with 'F'")
            forfeit_index = results.index('F')
            forfeit_game = last_5_games[forfeit_index]
            print(f"  Forfeit game ID: {forfeit_game['game_id']}")
            return True
        else:
            print("\n✗ FAILURE: Forfeit game not marked with 'F'")
            print(f"  Expected 'F' in results, got: {results}")
            return False
    else:
        print("\n✗ FAILURE: Team A not found in standings")
        return False

if __name__ == '__main__':
    success = test_forfeit_detection()
    sys.exit(0 if success else 1)
