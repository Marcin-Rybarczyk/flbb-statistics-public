"""
Referee Statistics Module

This module contains all functions related to referee performance statistics
including games officiated, fouls called, and other referee-related metrics.
"""

import pandas as pd


def extract_referee_stats(data):
    """
    Extract referee statistics from game data.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    DataFrame: Referee statistics across all games
    """
    if data.empty:
        return pd.DataFrame()
    
    referee_stats = []
    
    for _, game in data.iterrows():
        game_id = game['GameId']
        
        # Parse referee data
        try:
            if isinstance(game['Referres'], str):
                import ast
                refs_data = ast.literal_eval(game['Referres'])
            else:
                refs_data = game['Referres']
        except:
            continue
            
        if not isinstance(refs_data, list):
            continue
        
        # Count total fouls in this game
        total_fouls = 0
        try:
            if isinstance(game['GameEvents'], str):
                import ast
                events_data = ast.literal_eval(game['GameEvents'])
                
                # Count foul events
                for event in events_data:
                    if isinstance(event, dict) and 'EventAction' in event:
                        if 'Foul Added' in event['EventAction']:
                            total_fouls += 1
        except:
            pass
        
        # Record stats for each referee in this game
        for ref in refs_data:
            if isinstance(ref, dict) and 'Referee Name' in ref:
                referee_record = {
                    'RefereeName': ref['Referee Name'],
                    'GameId': game_id,
                    'FoulsCalledInGame': total_fouls,  # This will be divided by number of refs
                    'GamesRefereed': 1
                }
                referee_stats.append(referee_record)
    
    return pd.DataFrame(referee_stats)


def get_referee_statistics(data):
    """
    Get comprehensive referee statistics.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    DataFrame: Referee statistics including games, fouls called, etc.
    """
    ref_stats = extract_referee_stats(data)
    
    if ref_stats.empty:
        return pd.DataFrame()
    
    # Group by referee and calculate statistics
    referee_summary = ref_stats.groupby('RefereeName').agg({
        'GamesRefereed': 'sum',
        'FoulsCalledInGame': 'sum',
        'GameId': 'count'
    }).reset_index()
    
    # Calculate averages (note: fouls are shared among all refs in a game)
    referee_summary['AvgFoulsPerGame'] = (referee_summary['FoulsCalledInGame'] / referee_summary['GamesRefereed']).round(1)
    referee_summary.drop('GameId', axis=1, inplace=True)
    
    return referee_summary.sort_values('GamesRefereed', ascending=False)


def get_referee_fouls_per_game(data):
    """
    Get referee statistics focusing on fouls called per game.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    DataFrame: Referees sorted by average fouls per game
    """
    ref_stats = get_referee_statistics(data)
    
    if ref_stats.empty:
        return pd.DataFrame()
    
    return ref_stats.sort_values('AvgFoulsPerGame', ascending=False)


def get_referees_least_fouls_per_game(data):
    """
    Get referees with the least fouls per game.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    DataFrame: Referees sorted by least fouls per game
    """
    ref_stats = get_referee_statistics(data)
    
    if ref_stats.empty:
        return pd.DataFrame()
    
    # Only include referees who have officiated at least 2 games to be meaningful
    qualified_refs = ref_stats[ref_stats['GamesRefereed'] >= 2]
    
    return qualified_refs.sort_values('AvgFoulsPerGame', ascending=True)
