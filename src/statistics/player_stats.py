"""
Player Statistics Module

This module contains all functions related to individual player statistics
including scoring, shooting efficiency, fouls, and performance metrics.
"""

import pandas as pd


def extract_all_player_stats(data):
    """
    Extract all player statistics from the nested Teams data.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    DataFrame: Flattened player statistics across all games
    """
    if data.empty:
        return pd.DataFrame()
    
    all_players = []
    
    for _, game in data.iterrows():
        game_id = game['GameId']
        game_date = game['DateTime']
        
        # Parse Teams data (it's stored as string representation of list)
        try:
            if isinstance(game['Teams'], str):
                import ast
                teams_data = ast.literal_eval(game['Teams'])
            else:
                teams_data = game['Teams']
        except:
            continue
            
        if not isinstance(teams_data, list):
            continue
            
        # Extract player stats from each team
        for team in teams_data:
            if not isinstance(team, dict) or 'Players' not in team:
                continue
                
            team_name = team.get('Team Name', team.get('Team Name Short', 'Unknown'))
            
            for player in team.get('Players', []):
                if not isinstance(player, dict):
                    continue
                    
                player_record = {
                    'GameId': game_id,
                    'GameDate': game_date,
                    'PlayerName': player.get('Player Name', 'Unknown'),
                    'PlayerNumber': player.get('Player Number', 0),
                    'Team': team_name,
                    'TotalPoints': player.get('Total Points', 0),
                    '1PMadeShots': player.get('1P Made Shots', 0),
                    '2PMadeShots': player.get('2P Made Shots', 0),
                    '3PMadeShots': player.get('3P Made Shots', 0),
                    'TotalFouls': player.get('Total Fouls', 0),
                    'PFouls': player.get('P Fouls', 0),
                    'P1Fouls': player.get('P1 Fouls', 0),
                    'P2Fouls': player.get('P2 Fouls', 0),
                    'P3Fouls': player.get('P3 Fouls', 0),
                    'StartingFive': player.get('Starting Five', 'false') == 'true'
                }
                all_players.append(player_record)
    
    return pd.DataFrame(all_players)


def get_top_scorers(data, top_n=20):
    """
    Get top N scorers across all games.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of top scorers to return
    
    Returns:
    DataFrame: Top scorers with their statistics
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Group by player and calculate totals
    scorer_stats = player_stats.groupby(['PlayerName', 'Team']).agg({
        'TotalPoints': 'sum',
        '1PMadeShots': 'sum',
        '2PMadeShots': 'sum', 
        '3PMadeShots': 'sum',
        'GameId': 'count'  # Games played
    }).reset_index()
    
    scorer_stats.rename(columns={'GameId': 'GamesPlayed'}, inplace=True)
    scorer_stats['AvgPointsPerGame'] = (scorer_stats['TotalPoints'] / scorer_stats['GamesPlayed']).round(1)
    
    # Sort by total points and return top N
    return scorer_stats.sort_values('TotalPoints', ascending=False).head(top_n).reset_index(drop=True)


def get_highest_single_game_score(data, top_n=10):
    """
    Get the highest single game scores by any player.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of top single game scores to return
    
    Returns:
    DataFrame: Players with highest single game scores
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Sort by total points and return top N single game performances
    top_single_games = player_stats.nlargest(top_n, 'TotalPoints').reset_index(drop=True)
    
    return top_single_games


def get_player_shooting_efficiency(data, top_n=20):
    """
    Get player shooting efficiency statistics.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of top players to return
    
    Returns:
    DataFrame: Players with shooting efficiency statistics
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Group by player and calculate shooting stats
    efficiency_stats = player_stats.groupby(['PlayerName', 'Team']).agg({
        'TotalPoints': 'sum',
        '1PMadeShots': 'sum',
        '2PMadeShots': 'sum', 
        '3PMadeShots': 'sum',
        'GameId': 'count'  # Games played
    }).reset_index()
    
    efficiency_stats.rename(columns={'GameId': 'GamesPlayed'}, inplace=True)
    
    # Calculate shooting metrics
    efficiency_stats['TotalFieldGoals'] = (efficiency_stats['1PMadeShots'] + 
                                          efficiency_stats['2PMadeShots'] + 
                                          efficiency_stats['3PMadeShots'])
    efficiency_stats['PointsPerShot'] = (efficiency_stats['TotalPoints'] / 
                                        efficiency_stats['TotalFieldGoals'].replace(0, 1)).round(2)
    efficiency_stats['AvgPointsPerGame'] = (efficiency_stats['TotalPoints'] / 
                                           efficiency_stats['GamesPlayed']).round(1)
    efficiency_stats['ShotsPerGame'] = (efficiency_stats['TotalFieldGoals'] / 
                                       efficiency_stats['GamesPlayed']).round(1)
    
    # Filter players with at least 5 games and 10 total shots
    efficiency_stats = efficiency_stats[
        (efficiency_stats['GamesPlayed'] >= 5) & 
        (efficiency_stats['TotalFieldGoals'] >= 10)
    ]
    
    return efficiency_stats.sort_values('PointsPerShot', ascending=False).head(top_n).reset_index(drop=True)


def get_starting_five_vs_bench_stats(data):
    """
    Compare starting five players vs bench players statistics.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    dict: Statistics comparing starters vs bench
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return {}
    
    # Separate starters and bench players
    starters = player_stats[player_stats['StartingFive'] == True]
    bench = player_stats[player_stats['StartingFive'] == False]
    
    def get_group_stats(group, label):
        if group.empty:
            return {}
        return {
            f'{label}_total_players': len(group['PlayerName'].unique()),
            f'{label}_total_games': len(group),
            f'{label}_avg_points': group['TotalPoints'].mean().round(1),
            f'{label}_total_points': group['TotalPoints'].sum(),
            f'{label}_avg_fouls': group['TotalFouls'].mean().round(1),
            f'{label}_total_shots': (group['1PMadeShots'] + group['2PMadeShots'] + group['3PMadeShots']).sum(),
            f'{label}_avg_shots_per_game': ((group['1PMadeShots'] + group['2PMadeShots'] + group['3PMadeShots']).mean()).round(1)
        }
    
    starter_stats = get_group_stats(starters, 'starters')
    bench_stats = get_group_stats(bench, 'bench')
    
    return {**starter_stats, **bench_stats}


def get_double_digit_scorers(data, min_points=10):
    """
    Get players with double-digit scoring games.
    
    Parameters:
    data (DataFrame): The game data
    min_points (int): Minimum points for double-digit game
    
    Returns:
    DataFrame: Players with double-digit scoring statistics
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Filter games with double-digit scoring
    double_digit_games = player_stats[player_stats['TotalPoints'] >= min_points]
    
    # Group by player and calculate double-digit stats
    double_digit_stats = double_digit_games.groupby(['PlayerName', 'Team']).agg({
        'TotalPoints': ['count', 'mean', 'max'],
        'GameId': 'nunique'  # Total unique games for this player
    }).reset_index()
    
    # Flatten column names
    double_digit_stats.columns = ['PlayerName', 'Team', 'DoubleDigitGames', 'AvgInDoubleDigitGames', 'HighestScore', 'TotalGamesPlayed']
    
    # Get total games played for each player from all games
    all_player_games = player_stats.groupby(['PlayerName', 'Team']).size().reset_index(name='TotalGamesActual')
    double_digit_stats = double_digit_stats.merge(all_player_games, on=['PlayerName', 'Team'], how='left')
    
    # Calculate percentage of double-digit games
    double_digit_stats['DoubleDigitPercentage'] = (
        (double_digit_stats['DoubleDigitGames'] / double_digit_stats['TotalGamesActual']) * 100
    ).round(1)
    
    # Round averages
    double_digit_stats['AvgInDoubleDigitGames'] = double_digit_stats['AvgInDoubleDigitGames'].round(1)
    
    return double_digit_stats.sort_values('DoubleDigitGames', ascending=False).head(20).reset_index(drop=True)


def get_consistent_scorers(data, min_games=5):
    """
    Get players who consistently score well across multiple games.
    
    Parameters:
    data (DataFrame): The game data
    min_games (int): Minimum games to be considered
    
    Returns:
    DataFrame: Most consistent scorers
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Group by player and calculate consistency metrics
    player_groups = player_stats.groupby(['PlayerName', 'Team'])
    
    consistency_stats = []
    for (player, team), group in player_groups:
        if len(group) >= min_games:
            points = group['TotalPoints']
            consistency_stats.append({
                'PlayerName': player,
                'Team': team,
                'GamesPlayed': len(group),
                'AvgPoints': points.mean().round(1),
                'StdDevPoints': points.std().round(1),
                'MinPoints': points.min(),
                'MaxPoints': points.max(),
                'ConsistencyScore': (points.mean() / (points.std() + 0.1)).round(2)  # Higher is more consistent
            })
    
    consistency_df = pd.DataFrame(consistency_stats)
    if consistency_df.empty:
        return pd.DataFrame()
        
    return consistency_df.sort_values('ConsistencyScore', ascending=False).head(20).reset_index(drop=True)


def get_top_three_pointers(data, top_n=10):
    """
    Get top N three-point shooters.
    
    Parameters:
    data (DataFrame): The game data  
    top_n (int): Number of top three-point shooters to return
    
    Returns:
    DataFrame: Top three-point shooters with their statistics
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Group by player and calculate three-point totals
    three_point_stats = player_stats.groupby(['PlayerName', 'Team']).agg({
        '3PMadeShots': 'sum',
        'GameId': 'count',  # Games played
        'TotalPoints': 'sum'
    }).reset_index()
    
    three_point_stats.rename(columns={'GameId': 'GamesPlayed'}, inplace=True)
    three_point_stats['AvgThreePointsPerGame'] = (three_point_stats['3PMadeShots'] / three_point_stats['GamesPlayed']).round(1)
    
    # Sort by total three-pointers made and return top N
    return three_point_stats.sort_values('3PMadeShots', ascending=False).head(top_n).reset_index(drop=True)


def get_top_foulers(data, top_n=10):
    """
    Get players with the most fouls.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of top foulers to return
    
    Returns:
    DataFrame: Top foulers with their statistics
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Group by player and calculate foul totals
    foul_stats = player_stats.groupby(['PlayerName', 'Team']).agg({
        'TotalFouls': 'sum',
        'PFouls': 'sum',
        'P1Fouls': 'sum',
        'P2Fouls': 'sum',
        'P3Fouls': 'sum',
        'GameId': 'count',  # Games played
        'TotalPoints': 'sum'
    }).reset_index()
    
    foul_stats.rename(columns={'GameId': 'GamesPlayed'}, inplace=True)
    foul_stats['AvgFoulsPerGame'] = (foul_stats['TotalFouls'] / foul_stats['GamesPlayed']).round(1)
    
    # Sort by total fouls and return top N
    return foul_stats.sort_values('TotalFouls', ascending=False).head(top_n).reset_index(drop=True)


def get_top_players_by_score(data, top_n=50):
    """
    Get top N players by average score per game.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of top players to return
    
    Returns:
    DataFrame: Top players with their average scores
    """
    return get_top_scorers(data, top_n)
