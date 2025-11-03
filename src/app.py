import os
import re
from urllib.parse import unquote
from flask import Flask, render_template, request
import pandas as pd
from src.utils import (calculate_standings_by_division, get_highest_scoring_games, 
                   load_game_data, get_top_players_by_score, get_team_performance_stats,
                   get_top_scorers, get_highest_single_game_score, get_top_three_pointers, 
                   get_top_foulers, get_referee_statistics, get_referee_fouls_per_game,
                   get_referees_least_fouls_per_game, get_biggest_wins, get_biggest_leads,
                   get_most_tie_scores, get_most_lead_changes, get_player_shooting_efficiency,
                   get_starting_five_vs_bench_stats, get_double_digit_scorers, get_consistent_scorers,
                   get_player_game_impact_analysis, get_player_foul_impact_analysis,
                   get_best_player_combinations, get_referee_game_impact_analysis, get_all_fixtures_data,
                   get_fixtures_matrix_data, get_data_source_info, get_season_info, 
                   get_website_config, list_available_archives, import_season_archive,
                   get_all_players_list, get_player_detail_stats, get_game_details, get_referee_detail_stats,
                   get_team_detail_stats)
from src.version import get_version_info

app = Flask(__name__, template_folder='../templates', static_folder='../logos', static_url_path='/logos')

# Context processor to make season info available to all templates
@app.context_processor
def inject_season_info():
    """Make season information available to all templates"""
    season_info = get_season_info()
    website_config = get_website_config()
    version_info = get_version_info()
    return {
        'season_info': season_info,
        'website_config': website_config,
        'version_info': version_info
    }

# Logo utility functions
def normalize_team_name(team_name):
    """Normalize team name for file naming"""
    if not team_name:
        return ""
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', str(team_name))
    normalized = normalized.lower().replace(' ', '-')
    return normalized

def get_team_logo_url(team_name):
    """Get the logo URL for a given team name for use in templates"""
    if not team_name:
        return None
        
    normalized_name = normalize_team_name(team_name)
    logos_dir = "logos"
    
    # Check for PNG files (our standard format)
    png_file = f"{normalized_name}.png"
    png_path = os.path.join(logos_dir, png_file)
    if os.path.exists(png_path):
        return f"/logos/{png_file}"
    
    # Check for other formats
    for ext in ['.jpg', '.jpeg', '.gif', '.svg']:
        logo_file = f"{normalized_name}{ext}"
        logo_path = os.path.join(logos_dir, logo_file)
        if os.path.exists(logo_path):
            return f"/logos/{logo_file}"
    
    # Special case for Racing teams - check RAC.jpg
    if 'racing' in normalized_name.lower():
        rac_path = os.path.join(logos_dir, "RAC.jpg")
        if os.path.exists(rac_path):
            return "/logos/RAC.jpg"
    
    return None

# Make logo function available to templates
app.jinja_env.globals.update(get_team_logo_url=get_team_logo_url)

# Load and process the data
data = load_game_data()
data_source_info = get_data_source_info()

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
                         selected_division=selected_division,
                         data_source_info=data_source_info)

@app.route('/statistics')
def statistics():
    """Statistics page with comprehensive data analysis"""
    if data.empty:
        return render_template('statistics.html', 
                             error="No data available",
                             divisions=divisions,
                             data_source_info=data_source_info)
    
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
                         divisions=divisions,
                         data_source_info=data_source_info)

@app.route('/team-stats', methods=['GET', 'POST'])
def team_stats():
    """Complete team statistics page with division filter"""
    if data.empty:
        return render_template('team_stats.html', error="No data available", data_source_info=data_source_info)
    
    # Get selected division from form
    selected_division = request.form.get('division')
    
    # Get team performance stats
    team_performance = get_team_performance_stats(data)
    
    # Filter by division if selected
    filtered_data = data
    if selected_division:
        filtered_data = data[data['GameDivisionDisplay'] == selected_division]
        team_performance = get_team_performance_stats(filtered_data)
    
    return render_template('team_stats.html', 
                         team_stats=team_performance,
                         divisions=divisions,
                         selected_division=selected_division,
                         data_source_info=data_source_info)

@app.route('/team-detail')
def team_detail():
    """Individual team detail page with comprehensive statistics"""
    if data.empty:
        return render_template('team_detail.html', error="No data available", data_source_info=data_source_info)
    
    # Get all unique teams
    home_teams = set(data['HomeTeamName'].unique())
    away_teams = set(data['AwayTeamName'].unique())
    all_teams = sorted(home_teams.union(away_teams))
    
    # Get selected team from query parameter
    team_name = request.args.get('team')
    team_stats_detail = None
    
    if team_name:
        team_stats_detail = get_team_detail_stats(data, team_name)
    
    return render_template('team_detail.html',
                         all_teams=all_teams,
                         team_name=team_name,
                         team_stats=team_stats_detail,
                         divisions=divisions,
                         data_source_info=data_source_info)

@app.route('/player-stats', methods=['GET', 'POST'])
def player_stats():
    """Dedicated player statistics page"""
    if data.empty:
        return render_template('player_stats.html', error="No data available", data_source_info=data_source_info)
    
    # Get selected division from form
    selected_division = request.form.get('division')
    
    # Get comprehensive player statistics (filtered by division if selected)
    top_scorers = get_top_scorers(data, 50, division=selected_division)  # Get top 50 for comprehensive view
    highest_single_scores = get_highest_single_game_score(data, 10, division=selected_division)  # Now returns top 10
    top_three_pointers = get_top_three_pointers(data, 20, division=selected_division)
    top_foulers = get_top_foulers(data, 20, division=selected_division)
    
    # New basketball-specific statistics
    shooting_efficiency = get_player_shooting_efficiency(data, 20, division=selected_division)
    starter_bench_stats = get_starting_five_vs_bench_stats(data, division=selected_division)
    double_digit_scorers = get_double_digit_scorers(data, division=selected_division)
    consistent_scorers = get_consistent_scorers(data, division=selected_division)
    
    return render_template('player_stats.html',
                         top_scorers=top_scorers,
                         highest_single_scores=highest_single_scores,  # Updated variable name
                         top_three_pointers=top_three_pointers,
                         top_foulers=top_foulers,
                         shooting_efficiency=shooting_efficiency,
                         starter_bench_stats=starter_bench_stats,
                         double_digit_scorers=double_digit_scorers,
                         consistent_scorers=consistent_scorers,
                         divisions=divisions,
                         selected_division=selected_division,
                         data_source_info=data_source_info)

@app.route('/player-detail')
def player_detail():
    """Individual player detail page with search and comprehensive statistics"""
    if data.empty:
        return render_template('player_detail.html', error="No data available", data_source_info=data_source_info)
    
    # Get all players for autocomplete
    all_players = get_all_players_list(data)
    
    # Get selected player from query parameter
    player_name = request.args.get('player')
    player_stats_detail = None
    
    if player_name:
        player_stats_detail = get_player_detail_stats(data, player_name)
    
    return render_template('player_detail.html',
                         all_players=all_players,
                         player_name=player_name,
                         player_stats=player_stats_detail,
                         divisions=divisions,
                         data_source_info=data_source_info)

@app.route('/referee-stats')
def referee_stats():
    """Dedicated referee statistics page"""
    if data.empty:
        return render_template('referee_stats.html', error="No data available", data_source_info=data_source_info)
    
    # Get comprehensive referee statistics
    referee_stats_data = get_referee_statistics(data)
    referee_fouls = get_referee_fouls_per_game(data)
    referee_least_fouls = get_referees_least_fouls_per_game(data)
    referee_impact = get_referee_game_impact_analysis(data)
    
    return render_template('referee_stats.html',
                         referee_stats=referee_stats_data,
                         referee_fouls=referee_fouls,
                         referee_least_fouls=referee_least_fouls,
                         referee_impact=referee_impact,
                         divisions=divisions,
                         data_source_info=data_source_info)

@app.route('/referee-detail/<referee_name>')
def referee_detail(referee_name):
    """Individual referee detail page with comprehensive statistics"""
    # URL decode the referee name to handle special characters
    referee_name = unquote(referee_name)
    
    if data.empty:
        return render_template('referee_detail.html', error="No data available", data_source_info=data_source_info)
    
    # Get referee details
    referee_stats_detail = get_referee_detail_stats(data, referee_name)
    
    if not referee_stats_detail:
        return render_template('referee_detail.html', error=f"Referee '{referee_name}' not found", data_source_info=data_source_info)
    
    return render_template('referee_detail.html',
                         referee_name=referee_name,
                         referee_stats=referee_stats_detail,
                         divisions=divisions,
                         data_source_info=data_source_info)

@app.route('/deeper-analysis')
def deeper_analysis():
    """Deep game analysis page with advanced metrics"""
    if data.empty:
        return render_template('deeper_analysis.html', error="No data available", divisions=divisions, data_source_info=data_source_info)
    
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
                         selected_division=division_filter,
                         data_source_info=data_source_info)

@app.route('/fixtures')
def fixtures():
    """Fixtures page with games displayed as a matrix table"""
    if data.empty:
        return render_template('fixtures.html', error="No data available", divisions=divisions, data_source_info=data_source_info)
    
    # Get division filter from query parameters
    # Default to "M-Division 1:" if no filter is provided (first time visit)
    DEFAULT_DIVISION = "M-Division 1:"
    division_param = request.args.get('division')
    
    if division_param is None:
        # First time visit - default to "M-Division 1:"
        division_filter = DEFAULT_DIVISION
        selected_division_param = DEFAULT_DIVISION
    elif division_param == "ALL":
        # User explicitly selected "All Divisions" - show all
        division_filter = None
        selected_division_param = "ALL"
    else:
        # Specific division selected
        division_filter = division_param
        selected_division_param = division_param
    
    # Get matrix data for fixtures
    matrix_data = get_fixtures_matrix_data(data, division_filter)
    
    # Also get traditional table data with filter applied
    fixtures_data = get_all_fixtures_data(data, division_filter)
    
    # Sort by date (most recent first)
    if not fixtures_data.empty and 'DateTime' in fixtures_data.columns:
        fixtures_data = fixtures_data.sort_values('DateTime', ascending=False)
    
    return render_template('fixtures.html',
                         fixtures=fixtures_data,
                         matrix_data=matrix_data,
                         divisions=divisions,
                         selected_division=selected_division_param,
                         data_source_info=data_source_info)

@app.route('/game-detail/<game_id>')
def game_detail(game_id):
    """Game detail page showing comprehensive information about a specific game"""
    if data.empty:
        return render_template('game_detail.html', error="No data available", data_source_info=data_source_info)
    
    # Get game details
    game_details = get_game_details(data, game_id)
    
    if not game_details:
        return render_template('game_detail.html', error=f"Game {game_id} not found", data_source_info=data_source_info)
    
    return render_template('game_detail.html',
                         game=game_details,
                         data_source_info=data_source_info)

@app.route('/admin')
def admin():
    """Administration page with data statistics"""
    import os
    
    # Get season information
    season_info = get_season_info()
    website_config = get_website_config()
    
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
    
    # List available season archives
    available_archives = list_available_archives()
    
    return render_template('admin.html',
                         data_stats=data_stats,
                         file_stats=file_stats,
                         data_source_info=data_source_info,
                         divisions=divisions,
                         season_info=season_info,
                         website_config=website_config,
                         available_archives=available_archives)

@app.route('/admin/import-season', methods=['POST'])
def import_season_data():
    """Handle season archive import"""
    import os
    import tempfile
    
    if 'archive_file' not in request.files:
        return {'success': False, 'error': 'No file provided'}, 400
    
    file = request.files['archive_file']
    if file.filename == '':
        return {'success': False, 'error': 'No file selected'}, 400
    
    if not file.filename.endswith('.zip'):
        return {'success': False, 'error': 'Please upload a ZIP file'}, 400
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            file.save(tmp_file.name)
            
            # Import the archive
            result = import_season_archive(tmp_file.name)
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
            
            if result['success']:
                return {
                    'success': True,
                    'message': f"Successfully imported {len(result['imported_files'])} files",
                    'season_id': result['season_id'],
                    'target_directory': result['target_directory']
                }
            else:
                return {'success': False, 'error': '; '.join(result['errors'])}, 400
                
    except Exception as e:
        return {'success': False, 'error': f'Import failed: {str(e)}'}, 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
