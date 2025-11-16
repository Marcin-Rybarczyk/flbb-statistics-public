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
    """Test that forfeit games are correctly marked with 'F' in Last 5 Games for the forfeiting team"""
    
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
            'GameEvents': '[]',  # Regular game
            'GameLocation': 'Hall A'
        },
        {
            'HomeTeamName': 'Team A',
            'AwayTeamName': 'Team C',
            'FinalHomeScore': 0,
            'FinalAwayScore': 0,
            'HomeTeamLeaguePoints': 2,
            'AwayTeamLeaguePoints': 0,
            'GameId': 'game2',
            'DateTime': '2025-01-08 18:00:00',
            'GameEvents': "[{'EventAction': 'Forfeit', 'EventDateTime': '2025-01-08', 'EventActor': '* System *'}]",  # Forfeit game
            'GameLocation': 'Hall B - FORFAIT Team C'  # Team C forfeited
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
            'GameEvents': '[]',  # Regular game
            'GameLocation': 'Hall C'
        }
    ])
    
    # Calculate standings
    standings = calculate_standings(test_data)
    
    print("Testing forfeit detection in standings calculation...")
    print("\nStandings table:")
    print(standings[['Team Name', 'Games', 'W', 'L', 'Points']])
    
    # Check Team A's last 5 games (won by forfeit)
    team_a_row = standings[standings['Team Name'] == 'Team A']
    team_c_row = standings[standings['Team Name'] == 'Team C']
    
    success = True
    
    if not team_a_row.empty:
        last_5_games = team_a_row['Last 5 Games'].iloc[0]
        print(f"\nTeam A's Last 5 Games (most recent first):")
        for game in last_5_games:
            print(f"  Game {game['game_id']}: {game['result']}")
        
        results = [game['result'] for game in last_5_games]
        # Team A won by forfeit, should have 'W' for game2
        game2_result = next((g['result'] for g in last_5_games if g['game_id'] == 'game2'), None)
        if game2_result == 'W':
            print("\n✓ SUCCESS: Team A (winner by forfeit) correctly marked with 'W'")
        else:
            print(f"\n✗ FAILURE: Team A should have 'W' for forfeit win, got: {game2_result}")
            success = False
    else:
        print("\n✗ FAILURE: Team A not found in standings")
        success = False
    
    if not team_c_row.empty:
        last_5_games_c = team_c_row['Last 5 Games'].iloc[0]
        print(f"\nTeam C's Last 5 Games (most recent first):")
        for game in last_5_games_c:
            print(f"  Game {game['game_id']}: {game['result']}")
        
        # Team C forfeited, should have 'F' for game2
        game2_result = next((g['result'] for g in last_5_games_c if g['game_id'] == 'game2'), None)
        if game2_result == 'F':
            print("\n✓ SUCCESS: Team C (forfeited) correctly marked with 'F'")
        else:
            print(f"\n✗ FAILURE: Team C should have 'F' for forfeit, got: {game2_result}")
            success = False
    else:
        print("\n✗ FAILURE: Team C not found in standings")
        success = False
    
    return success

if __name__ == '__main__':
    success = test_forfeit_detection()
    sys.exit(0 if success else 1)
