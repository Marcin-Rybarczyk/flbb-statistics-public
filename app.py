import os
from flask import Flask, render_template, request
import pandas as pd
from utils import (calculate_standings_by_division, get_highest_scoring_games, 
                   load_game_data, get_top_players_by_score, get_team_performance_stats,
                   get_top_scorers, get_highest_single_game_score, get_top_three_pointers, 
                   get_top_foulers, get_referee_statistics, get_referee_fouls_per_game,
                   get_referees_least_fouls_per_game, get_biggest_wins, get_biggest_leads,
                   get_most_tie_scores, get_most_lead_changes, get_player_shooting_efficiency,
                   get_starting_five_vs_bench_stats, get_double_digit_scorers, get_consistent_scorers,
                   get_player_game_impact_analysis, get_player_foul_impact_analysis,
                   get_best_player_combinations, get_referee_game_impact_analysis, get_all_fixtures_data,
                   get_fixtures_matrix_data)

app = Flask(__name__)

# Load and process the data
data = load_game_data()
if not data.empty:
    # Clean the data - remove unnamed column if it exists
    if 'Unnamed: 0' in data.columns:
        data = data.drop('Unnamed: 0', axis=1)
    # Extract unique divisions
    divisions = data['GameDivisionDisplay'].unique()
else:
    divisions = []

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_division = request.form.get('division')
    standings = None
    highest_games = None

    if selected_division and not data.empty:
        # Calculate standings for the selected division
        standings = calculate_standings_by_division(data, selected_division)
        # Get highest scoring games for the division
        division_data = data[data['GameDivisionDisplay'] == selected_division]
        highest_games = get_highest_scoring_games(division_data, 5)

    return render_template('index.html', 
                         divisions=divisions, 
                         standings=standings, 
                         highest_games=highest_games,
                         selected_division=selected_division)

@app.route('/statistics')
def statistics():
    """Statistics page with comprehensive data analysis"""
    if data.empty:
        return render_template('statistics.html', 
                             error="No data available",
                             divisions=divisions)
    
    # Get overall statistics
    highest_games = get_highest_scoring_games(data, 10)
    
    # Player Statistics
    top_scorers = get_top_scorers(data, 20)
    highest_single_score = get_highest_single_game_score(data)
    top_three_pointers = get_top_three_pointers(data, 10)
    top_foulers = get_top_foulers(data, 10)
    
    # Referee Statistics
    referee_stats = get_referee_statistics(data)
    referee_fouls = get_referee_fouls_per_game(data)
    referee_least_fouls = get_referees_least_fouls_per_game(data)
    
    # Game Statistics  
    biggest_wins = get_biggest_wins(data, 10)
    biggest_leads = get_biggest_leads(data, 10)
    most_ties = get_most_tie_scores(data, 10)
    most_lead_changes = get_most_lead_changes(data, 10)
    
    team_stats = get_team_performance_stats(data)
    
    return render_template('statistics.html', 
                         highest_games=highest_games,
                         top_scorers=top_scorers,
                         highest_single_score=highest_single_score,
                         top_three_pointers=top_three_pointers,
                         top_foulers=top_foulers,
                         referee_stats=referee_stats,
                         referee_fouls=referee_fouls,
                         referee_least_fouls=referee_least_fouls,
                         biggest_wins=biggest_wins,
                         biggest_leads=biggest_leads,
                         most_ties=most_ties,
                         most_lead_changes=most_lead_changes,
                         team_stats=team_stats,
                         divisions=divisions)

@app.route('/team-stats', methods=['GET', 'POST'])
def team_stats():
    """Detailed team statistics page with team selection"""
    if data.empty:
        return render_template('team_stats.html', error="No data available")
    
    # Get all unique teams
    home_teams = set(data['HomeTeamName'].unique())
    away_teams = set(data['AwayTeamName'].unique())
    all_teams = sorted(home_teams.union(away_teams))
    
    selected_team = request.form.get('team')
    team_performance = get_team_performance_stats(data)
    team_games = None
    team_specific_stats = None
    
    if selected_team:
        # Get games for the selected team
        team_games = data[
            (data['HomeTeamName'] == selected_team) | 
            (data['AwayTeamName'] == selected_team)
        ].copy()
        
        # Process team-specific statistics
        if not team_games.empty:
            team_specific_stats = team_performance[team_performance['Team'] == selected_team].iloc[0].to_dict()
            
            # Add game-by-game analysis
            team_games['IsHome'] = team_games['HomeTeamName'] == selected_team
            team_games['TeamScore'] = team_games.apply(
                lambda row: row['FinalHomeScore'] if row['IsHome'] else row['FinalAwayScore'], 
                axis=1
            )
            team_games['OpponentScore'] = team_games.apply(
                lambda row: row['FinalAwayScore'] if row['IsHome'] else row['FinalHomeScore'], 
                axis=1
            )
            team_games['Opponent'] = team_games.apply(
                lambda row: row['AwayTeamName'] if row['IsHome'] else row['HomeTeamName'], 
                axis=1
            )
            team_games['Result'] = team_games.apply(
                lambda row: 'W' if row['TeamScore'] > row['OpponentScore'] else 'L', 
                axis=1
            )
            team_games['Margin'] = team_games['TeamScore'] - team_games['OpponentScore']
    
    return render_template('team_stats.html', 
                         team_stats=team_performance,
                         all_teams=all_teams,
                         selected_team=selected_team,
                         team_games=team_games,
                         team_specific_stats=team_specific_stats,
                         divisions=divisions)

@app.route('/player-stats')
def player_stats():
    """Dedicated player statistics page"""
    if data.empty:
        return render_template('player_stats.html', error="No data available")
    
    # Get comprehensive player statistics
    top_scorers = get_top_scorers(data, 50)  # Get top 50 for comprehensive view
    highest_single_scores = get_highest_single_game_score(data, 10)  # Now returns top 10
    top_three_pointers = get_top_three_pointers(data, 20)
    top_foulers = get_top_foulers(data, 20)
    
    # New basketball-specific statistics
    shooting_efficiency = get_player_shooting_efficiency(data, 20)
    starter_bench_stats = get_starting_five_vs_bench_stats(data)
    double_digit_scorers = get_double_digit_scorers(data)
    consistent_scorers = get_consistent_scorers(data)
    
    return render_template('player_stats.html',
                         top_scorers=top_scorers,
                         highest_single_scores=highest_single_scores,  # Updated variable name
                         top_three_pointers=top_three_pointers,
                         top_foulers=top_foulers,
                         shooting_efficiency=shooting_efficiency,
                         starter_bench_stats=starter_bench_stats,
                         double_digit_scorers=double_digit_scorers,
                         consistent_scorers=consistent_scorers,
                         divisions=divisions)

@app.route('/deeper-analysis')
def deeper_analysis():
    """Deep game analysis page with advanced metrics"""
    if data.empty:
        return render_template('deeper_analysis.html', error="No data available", divisions=divisions)
    
    # Get division filter from query parameters
    division_filter = request.args.get('division')
    
    # Apply division filter if provided
    filtered_data = data.copy()
    if division_filter:
        filtered_data = filtered_data[filtered_data['GameDivisionDisplay'] == division_filter]
    
    # Get comprehensive deeper analysis with filtered data
    player_impact = get_player_game_impact_analysis(filtered_data, 20)
    foul_impact = get_player_foul_impact_analysis(filtered_data, 15) 
    player_combinations = get_best_player_combinations(filtered_data, 3)
    referee_impact = get_referee_game_impact_analysis(filtered_data)
    
    return render_template('deeper_analysis.html',
                         player_impact=player_impact,
                         foul_impact=foul_impact,
                         player_combinations=player_combinations,
                         referee_impact=referee_impact,
                         divisions=divisions,
                         selected_division=division_filter)

@app.route('/fixtures')
def fixtures():
    """Fixtures page with games displayed as a matrix table"""
    if data.empty:
        return render_template('fixtures.html', error="No data available", divisions=divisions)
    
    # Get division filter from query parameters
    division_filter = request.args.get('division')
    
    # Get matrix data for fixtures
    matrix_data = get_fixtures_matrix_data(data, division_filter)
    
    # Also get traditional table data for compatibility/comparison (if needed)
    fixtures_data = get_all_fixtures_data(data)
    
    # Sort by date (most recent first)
    if not fixtures_data.empty and 'DateTime' in fixtures_data.columns:
        fixtures_data = fixtures_data.sort_values('DateTime', ascending=False)
    
    return render_template('fixtures.html',
                         fixtures=fixtures_data,
                         matrix_data=matrix_data,
                         divisions=divisions)

@app.route('/admin')
def admin():
    """Administration page with data statistics"""
    import os
    
    # Calculate data statistics
    data_stats = {}
    
    if not data.empty:
        # Basic data statistics
        data_stats['total_games'] = len(data)
        data_stats['total_teams'] = len(set(list(data['HomeTeamName'].unique()) + list(data['AwayTeamName'].unique())))
        data_stats['total_divisions'] = len(data['GameDivisionDisplay'].unique())
        data_stats['total_data_points'] = len(data) * len(data.columns)
        data_stats['data_columns'] = len(data.columns)
        
        # Player statistics
        if 'PlayerName' in data.columns:
            data_stats['total_players'] = len(data['PlayerName'].unique())
        else:
            data_stats['total_players'] = 'N/A'
            
        # Date range
        if 'GameDate' in data.columns:
            try:
                data_stats['date_range_start'] = data['GameDate'].min()
                data_stats['date_range_end'] = data['GameDate'].max()
            except:
                data_stats['date_range_start'] = 'N/A'
                data_stats['date_range_end'] = 'N/A'
        else:
            data_stats['date_range_start'] = 'N/A'
            data_stats['date_range_end'] = 'N/A'
            
        # Score statistics
        if 'FinalHomeScore' in data.columns and 'FinalAwayScore' in data.columns:
            data_stats['avg_home_score'] = data['FinalHomeScore'].mean()
            data_stats['avg_away_score'] = data['FinalAwayScore'].mean()
            data_stats['highest_scoring_game'] = (data['FinalHomeScore'] + data['FinalAwayScore']).max()
        else:
            data_stats['avg_home_score'] = 'N/A'
            data_stats['avg_away_score'] = 'N/A'
            data_stats['highest_scoring_game'] = 'N/A'
            
        # Division statistics
        division_games = data.groupby('GameDivisionDisplay').size().to_dict()
        data_stats['division_games'] = division_games
        
    else:
        data_stats = {
            'total_games': 0,
            'total_teams': 0,
            'total_divisions': 0,
            'total_players': 0,
            'total_data_points': 0,
            'data_columns': 0,
            'date_range_start': 'N/A',
            'date_range_end': 'N/A',
            'avg_home_score': 'N/A',
            'avg_away_score': 'N/A',
            'highest_scoring_game': 'N/A',
            'division_games': {}
        }
    
    # File system statistics
    try:
        file_stats = {}
        for file_name in ['full-game-stats.csv', 'file.csv']:
            file_path = os.path.join(os.getcwd(), file_name)
            if os.path.exists(file_path):
                file_stats[file_name] = {
                    'size': os.path.getsize(file_path),
                    'modified': os.path.getmtime(file_path)
                }
            else:
                file_stats[file_name] = None
    except:
        file_stats = {}
    
    return render_template('admin.html',
                         data_stats=data_stats,
                         file_stats=file_stats,
                         divisions=divisions)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
