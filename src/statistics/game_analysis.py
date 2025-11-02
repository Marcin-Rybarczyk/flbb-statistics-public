"""
Game Analysis Module

This module contains functions for analyzing game events, tracking ties,
lead changes, biggest leads, and win margins.
"""

import pandas as pd


def analyze_game_events(data):
    """
    Analyze game events to extract tie scores, lead changes, biggest leads, etc.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    DataFrame: Game analysis with tie scores, lead changes, biggest leads
    """
    if data.empty:
        return pd.DataFrame()
    
    game_analyses = []
    
    for _, game in data.iterrows():
        game_id = game['GameId']
        home_team = game['HomeTeamName']
        away_team = game['AwayTeamName']
        final_home_score = game['FinalHomeScore']
        final_away_score = game['FinalAwayScore']
        
        # Parse game events
        try:
            if isinstance(game['GameEvents'], str):
                import ast
                events_data = ast.literal_eval(game['GameEvents'])
            else:
                events_data = game['GameEvents']
        except:
            events_data = []
        
        if not isinstance(events_data, list):
            events_data = []
        
        # Analyze score progression
        tie_count = 0
        lead_changes = 0
        max_home_lead = 0
        max_away_lead = 0
        current_advantage = 0
        previous_leader = None
        
        for event in events_data:
            if not isinstance(event, dict):
                continue
                
            # Track advantages (leads)
            advantage = event.get('EventAdvantage')
            if advantage is not None:
                current_advantage = advantage
                
                # Check for ties
                if advantage == 0:
                    tie_count += 1
                
                # Track biggest leads
                if advantage > 0:  # Home team leading
                    max_home_lead = max(max_home_lead, advantage)
                    current_leader = 'home'
                elif advantage < 0:  # Away team leading
                    max_away_lead = max(max_away_lead, abs(advantage))
                    current_leader = 'away'
                else:
                    current_leader = None
                
                # Count lead changes
                if previous_leader is not None and current_leader != previous_leader and current_leader is not None:
                    lead_changes += 1
                    
                if current_leader is not None:
                    previous_leader = current_leader
        
        # Calculate biggest win margin
        win_margin = abs(final_home_score - final_away_score)
        winner = home_team if final_home_score > final_away_score else away_team
        
        game_analysis = {
            'GameId': game_id,
            'HomeTeam': home_team,
            'AwayTeam': away_team,
            'FinalHomeScore': final_home_score,
            'FinalAwayScore': final_away_score,
            'TieScores': tie_count,
            'LeadChanges': lead_changes,
            'MaxHomeLead': max_home_lead,
            'MaxAwayLead': max_away_lead,
            'BiggestLead': max(max_home_lead, max_away_lead),
            'WinMargin': win_margin,
            'Winner': winner
        }
        
        game_analyses.append(game_analysis)
    
    return pd.DataFrame(game_analyses)


def get_most_tie_scores(data, top_n=10):
    """
    Get games with the most tie scores.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of games to return
    
    Returns:
    DataFrame: Games with most tie scores
    """
    game_analysis = analyze_game_events(data)
    
    if game_analysis.empty:
        return pd.DataFrame()
    
    return game_analysis.nlargest(top_n, 'TieScores')


def get_most_lead_changes(data, top_n=10):
    """
    Get games with the most lead changes.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of games to return
    
    Returns:
    DataFrame: Games with most lead changes
    """
    game_analysis = analyze_game_events(data)
    
    if game_analysis.empty:
        return pd.DataFrame()
    
    return game_analysis.nlargest(top_n, 'LeadChanges')


def get_biggest_leads(data, top_n=10):
    """
    Get games with the biggest leads.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of games to return
    
    Returns:
    DataFrame: Games with biggest leads
    """
    game_analysis = analyze_game_events(data)
    
    if game_analysis.empty:
        return pd.DataFrame()
    
    return game_analysis.nlargest(top_n, 'BiggestLead')


def get_biggest_wins(data, top_n=10):
    """
    Get games with the biggest win margins.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of games to return
    
    Returns:
    DataFrame: Games with biggest win margins
    """
    game_analysis = analyze_game_events(data)
    
    if game_analysis.empty:
        return pd.DataFrame()
    
    return game_analysis.nlargest(top_n, 'WinMargin')
