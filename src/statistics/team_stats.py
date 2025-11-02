"""
Team Statistics Module

This module contains all functions related to team performance statistics
including standings, win/loss records, and scoring statistics.
"""

import pandas as pd
from collections import defaultdict


def calculate_standings(df):
    """
    Calculate standings from game data.
    
    Parameters:
    df (DataFrame): Game data
    
    Returns:
    DataFrame: Standings table with wins, losses, points, etc.
    """
    standings = defaultdict(lambda: {
        'Games': 0, 'W': 0, 'L': 0, 'F': 0, 'A': 0, 'Points': 0
    })

    for _, row in df.iterrows():
        home_team = row['HomeTeamName']
        away_team = row['AwayTeamName']
        home_score = row['FinalHomeScore']
        away_score = row['FinalAwayScore']

        standings[home_team]['Games'] += 1
        standings[away_team]['Games'] += 1

        standings[home_team]['F'] += home_score
        standings[away_team]['F'] += away_score

        standings[home_team]['A'] += away_score
        standings[away_team]['A'] += home_score

        if home_score > away_score:  # Home team wins
            standings[home_team]['W'] += 1
            standings[away_team]['L'] += 1
            standings[home_team]['Points'] += 2
            standings[away_team]['Points'] += 1
        else:  # Away team wins
            standings[home_team]['L'] += 1
            standings[away_team]['W'] += 1
            standings[home_team]['Points'] += 1
            standings[away_team]['Points'] += 2

    # Convert to a DataFrame
    standings_df = pd.DataFrame.from_dict(standings, orient='index').reset_index()
    standings_df.rename(columns={'index': 'Team Name'}, inplace=True)
    standings_df['Points Diff'] = standings_df['F'] - standings_df['A']

    # Sort by Points, then Points Diff
    standings_df.sort_values(by=['Points', 'Points Diff'], ascending=[False, False], inplace=True)
    standings_df.reset_index(drop=True, inplace=True)
    standings_df.index += 1
    standings_df.index.name = 'Rank'
    return standings_df


def calculate_standings_by_division(data, division_name):
    """
    Calculate standings for a specific division.
    
    Parameters:
    data (DataFrame): The game data
    division_name (str): The division name to filter by
    
    Returns:
    DataFrame: The standings table for the division
    """
    division_filtered_data = data[data['GameDivisionDisplay'] == division_name]
    return calculate_standings(division_filtered_data)


def get_team_performance_stats(data):
    """
    Get comprehensive team performance statistics.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    DataFrame: Team performance statistics
    """
    if data.empty:
        return pd.DataFrame()
    
    team_stats = {}
    
    # Process home and away games for each team
    for _, row in data.iterrows():
        home_team = row['HomeTeamName']
        away_team = row['AwayTeamName']
        home_score = row['FinalHomeScore']
        away_score = row['FinalAwayScore']
        
        # Initialize team stats if not exists
        for team in [home_team, away_team]:
            if team not in team_stats:
                team_stats[team] = {
                    'Team': team,
                    'TotalGames': 0,
                    'HomeGames': 0,
                    'AwayGames': 0,
                    'Wins': 0,
                    'Losses': 0,
                    'TotalPointsScored': 0,
                    'TotalPointsAllowed': 0,
                    'HighestScore': 0,
                    'LowestScore': float('inf'),
                    'WinStreak': 0,
                    'CurrentStreak': 0
                }
        
        # Update home team stats
        team_stats[home_team]['TotalGames'] += 1
        team_stats[home_team]['HomeGames'] += 1
        team_stats[home_team]['TotalPointsScored'] += home_score
        team_stats[home_team]['TotalPointsAllowed'] += away_score
        team_stats[home_team]['HighestScore'] = max(team_stats[home_team]['HighestScore'], home_score)
        team_stats[home_team]['LowestScore'] = min(team_stats[home_team]['LowestScore'], home_score)
        
        # Update away team stats
        team_stats[away_team]['TotalGames'] += 1
        team_stats[away_team]['AwayGames'] += 1
        team_stats[away_team]['TotalPointsScored'] += away_score
        team_stats[away_team]['TotalPointsAllowed'] += home_score
        team_stats[away_team]['HighestScore'] = max(team_stats[away_team]['HighestScore'], away_score)
        team_stats[away_team]['LowestScore'] = min(team_stats[away_team]['LowestScore'], away_score)
        
        # Update wins/losses
        if home_score > away_score:
            team_stats[home_team]['Wins'] += 1
            team_stats[away_team]['Losses'] += 1
        else:
            team_stats[away_team]['Wins'] += 1
            team_stats[home_team]['Losses'] += 1
    
    # Convert to DataFrame and add calculated fields
    team_df = pd.DataFrame.from_dict(team_stats, orient='index')
    if not team_df.empty:
        team_df['AvgPointsScored'] = team_df['TotalPointsScored'] / team_df['TotalGames']
        team_df['AvgPointsAllowed'] = team_df['TotalPointsAllowed'] / team_df['TotalGames']
        team_df['PointsDifferential'] = team_df['TotalPointsScored'] - team_df['TotalPointsAllowed']
        team_df['WinPercentage'] = (team_df['Wins'] / team_df['TotalGames'] * 100).round(1)
        team_df['HomeWinPercentage'] = 0  # Would need game-by-game analysis
        team_df['AwayWinPercentage'] = 0  # Would need game-by-game analysis
        
        # Fix infinite values for teams that haven't played
        team_df['LowestScore'] = team_df['LowestScore'].replace(float('inf'), 0)
    
    return team_df.sort_values('WinPercentage', ascending=False)


def get_highest_scoring_games(data, top_n=10):
    """
    Get games with highest total scores.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of games to return
    
    Returns:
    DataFrame: Games with highest scores
    """
    # Create a copy to avoid modifying the original data
    data_copy = data.copy()
    data_copy['TotalScore'] = data_copy['FinalHomeScore'] + data_copy['FinalAwayScore']
    highest_games = data_copy.nlargest(top_n, 'TotalScore')
    return highest_games[['GameId', 'HomeTeamName', 'AwayTeamName', 'FinalHomeScore', 'FinalAwayScore', 'TotalScore', 'GameDivisionDisplay']]
