import os
import re
import logging
import unicodedata
from urllib.parse import unquote
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import pandas as pd
from src.utils import (calculate_standings_by_division, get_highest_scoring_games, 
                   load_game_data, get_top_players_by_score, get_team_performance_stats,
                   get_top_scorers, get_highest_single_game_score, get_top_three_pointers, 
                   get_top_foulers, get_referee_statistics, get_referee_fouls_per_game,
                   get_referees_least_fouls_per_game, get_biggest_wins, get_biggest_leads,
                   get_most_tie_scores, get_most_lead_changes, get_longest_duration_games,
                   get_player_shooting_efficiency,
                   get_starting_five_vs_bench_stats, get_double_digit_scorers, get_consistent_scorers,
                   get_player_game_impact_analysis, get_player_foul_impact_analysis,
                   get_best_player_combinations, get_referee_game_impact_analysis, get_all_fixtures_data,
                   get_fixtures_matrix_data, get_data_source_info, get_season_info, 
                   get_website_config, list_available_archives, import_season_archive, export_season_archive,
                   get_all_players_list, get_player_detail_stats, get_game_details, get_referee_detail_stats,
                   get_team_detail_stats, get_all_referees_list, get_all_games_list,
                   get_player_hover_stats, get_team_hover_stats, get_referee_hover_stats, get_game_hover_stats,
                   calculate_referee_performance_index, get_closest_games_by_team, CSV_FILEPATH)
from src.version import get_version_info

app = Flask(__name__, template_folder='../templates', static_folder='../logos', static_url_path='/logos')

# Valid theme options for the application
VALID_THEMES = ['default', 'ocean', 'sunset', 'forest', 'minimal', 'cherry']

# Configure logging for tracking code validation
logger = logging.getLogger(__name__)

def validate_tracking_code(code):
    """
    Validate tracking code from environment variable for basic security.
    
    This function performs basic validation to ensure the tracking code:
    - Is not excessively long (prevents DoS)
    - Contains properly formatted script tags
    - Doesn't contain obvious malicious patterns
    
    Note: This is not a comprehensive XSS prevention mechanism. The tracking code
    should only be set from trusted sources (e.g., MyDevil panel). Never allow
    user input to set this value.
    
    Args:
        code (str): The tracking code to validate
        
    Returns:
        str: The validated code, or empty string if invalid
    """
    if not code or not isinstance(code, str):
        return ''
    
    # Check length (tracking codes shouldn't be huge)
    if len(code) > 10000:  # 10KB max
        logger.warning("MYDEVIL_STATS_CODE exceeds maximum length (10KB), ignoring")
        return ''
    
    # Validate script tag format - should have both opening and closing tags
    if '<script' not in code.lower():
        logger.warning("MYDEVIL_STATS_CODE doesn't contain <script> tag, ignoring")
        return ''
    
    if '</script>' not in code.lower():
        logger.warning("MYDEVIL_STATS_CODE doesn't contain closing </script> tag, ignoring")
        return ''
    
    # Check for dangerous patterns that could indicate XSS attempts
    # Note: This is a basic blocklist, not a comprehensive security mechanism
    dangerous_patterns = [
        'javascript:',      # javascript: protocol
        'data:',            # data: protocol
        'vbscript:',        # vbscript: protocol
        'onerror=',         # event handlers
        'onload=',
        'onclick=',
        'onmouseover=',
        'onfocus=',
        'onblur=',
        'onchange=',
        'onsubmit=',
        '<iframe',          # iframe injection
        'document.cookie',  # cookie theft
        'eval(',            # code execution
        'expression(',      # IE CSS expressions
    ]
    code_lower = code.lower()
    for pattern in dangerous_patterns:
        if pattern in code_lower:
            logger.warning(
                f"MYDEVIL_STATS_CODE contains potentially dangerous pattern '{pattern}', ignoring"
            )
            return ''
    
    return code

# Set secret key for session management
# In production, SECRET_KEY should be set via environment variable
# For development, generate a random key if not set
if not os.environ.get('SECRET_KEY'):
    import secrets
    app.secret_key = secrets.token_hex(32)
else:
    app.secret_key = os.environ.get('SECRET_KEY')

# Admin authentication
from functools import wraps

def is_admin_authenticated():
    """Check if the current user is authenticated as admin"""
    return session.get('admin_authenticated', False)

def login_required(f):
    """Decorator to require admin authentication for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_authenticated():
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Context processor to make season info available to all templates
@app.context_processor
def inject_season_info():
    """Make season information available to all templates"""
    season_info = get_season_info()
    website_config = get_website_config()
    version_info = get_version_info()
    
    # Get user preferences from session
    user_prefs = {
        'division': session.get('preferred_division'),
        'team': session.get('preferred_team'),
        'theme': session.get('preferred_theme', 'default')
    }
    
    # Get MyDevil statistics tracking code from environment variable and validate it
    mydevil_stats_code = validate_tracking_code(os.environ.get('MYDEVIL_STATS_CODE', ''))
    
    return {
        'season_info': season_info,
        'website_config': website_config,
        'version_info': version_info,
        'user_prefs': user_prefs,
        'mydevil_stats_code': mydevil_stats_code,
        'is_admin_authenticated': is_admin_authenticated()
    }

# Logo utility functions
def normalize_team_name(team_name):
    """Normalize team name for file naming
    
    Converts accented characters to their base form (é -> e, ä -> a, etc.)
    before removing remaining special characters and converting to lowercase.
    """
    if not team_name:
        return ""
    
    # First, normalize accents to their base characters
    # NFD = Canonical Decomposition (separates base character from accent)
    # Filter out combining marks (category 'Mn') to remove accents
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', str(team_name))
        if unicodedata.category(c) != 'Mn'
    )
    
    # Then remove any remaining special characters
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
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
    # Extract unique teams from player stats
    from src.utils import extract_all_player_stats
    player_stats = extract_all_player_stats(data)
    if not player_stats.empty:
        teams = sorted(player_stats['Team'].unique())
    else:
        teams = []
else:
    divisions = []
    teams = []

@app.route('/', methods=['GET', 'POST'])
def index():
    """Home page with navigation tiles"""
    return render_template('index.html', 
                         divisions=divisions,
                         data_source_info=data_source_info)

@app.route('/standings', methods=['GET', 'POST'])
def standings():
    """Division standings page"""
    # Get division from form, query params, or user preferences
    selected_division = request.form.get('division') or request.args.get('division') or session.get('preferred_division')
    standings = None

    if selected_division and not data.empty:
        # Calculate standings for the selected division
        standings = calculate_standings_by_division(data, selected_division)

    return render_template('standings.html', 
                         divisions=divisions, 
                         standings=standings,
                         selected_division=selected_division,
                         data_source_info=data_source_info)

@app.route('/statistics', methods=['GET', 'POST'])
def statistics():
    """Game Statistics page with division filtering"""
    if data.empty:
        return render_template('statistics.html', 
                             error="No data available",
                             divisions=divisions,
                             data_source_info=data_source_info)
    
    # Get selected division from form, query parameter, or user preferences
    selected_division = request.form.get('division') or request.args.get('division') or session.get('preferred_division')
    
    # Get game statistics with optional division filter
    highest_games = get_highest_scoring_games(data, 10, division=selected_division)
    biggest_wins = get_biggest_wins(data, 10, division=selected_division)
    biggest_leads = get_biggest_leads(data, 10, division=selected_division)
    most_ties = get_most_tie_scores(data, 10, division=selected_division)
    most_lead_changes = get_most_lead_changes(data, 10, division=selected_division)
    longest_duration_games = get_longest_duration_games(data, 20, division=selected_division)
    
    return render_template('statistics.html', 
                         highest_games=highest_games,
                         biggest_wins=biggest_wins,
                         biggest_leads=biggest_leads,
                         most_ties=most_ties,
                         most_lead_changes=most_lead_changes,
                         longest_duration_games=longest_duration_games,
                         divisions=divisions,
                         selected_division=selected_division,
                         data_source_info=data_source_info)

@app.route('/team-stats', methods=['GET', 'POST'])
def team_stats():
    """Complete team statistics page with division filter"""
    if data.empty:
        return render_template('team_stats.html', error="No data available", data_source_info=data_source_info)
    
    # Get selected division from form or user preferences
    selected_division = request.form.get('division') or session.get('preferred_division')
    
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
    
    # Get selected team from query parameter or user preferences
    team_name = request.args.get('team') or session.get('preferred_team')
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
    
    # Get selected division and team from form
    selected_division = request.form.get('division')
    selected_team = request.form.get('team')
    
    # Get comprehensive player statistics (filtered by division and team if selected)
    top_scorers = get_top_scorers(data, 50, division=selected_division, team=selected_team)  # Get top 50 for comprehensive view
    highest_single_scores = get_highest_single_game_score(data, 10, division=selected_division, team=selected_team)  # Now returns top 10
    top_three_pointers = get_top_three_pointers(data, 20, division=selected_division, team=selected_team)
    top_foulers = get_top_foulers(data, 20, division=selected_division, team=selected_team)
    
    # New basketball-specific statistics
    shooting_efficiency = get_player_shooting_efficiency(data, 20, division=selected_division, team=selected_team)
    starter_bench_stats = get_starting_five_vs_bench_stats(data, division=selected_division, team=selected_team)
    double_digit_scorers = get_double_digit_scorers(data, division=selected_division, team=selected_team)
    consistent_scorers = get_consistent_scorers(data, division=selected_division, team=selected_team)
    
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
                         teams=teams,
                         selected_division=selected_division,
                         selected_team=selected_team,
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

@app.route('/referee-detail')
def referee_detail():
    """Individual referee detail page with search and comprehensive statistics"""
    if data.empty:
        return render_template('referee_detail.html', error="No data available", data_source_info=data_source_info)
    
    # Get all referees for autocomplete
    all_referees = get_all_referees_list(data)
    
    # Get selected referee from query parameter
    referee_name = request.args.get('referee')
    referee_stats_detail = None
    
    if referee_name:
        referee_stats_detail = get_referee_detail_stats(data, referee_name)
    
    return render_template('referee_detail.html',
                         all_referees=all_referees,
                         referee_name=referee_name,
                         referee_stats=referee_stats_detail,
                         divisions=divisions,
                         data_source_info=data_source_info)

@app.route('/referee-performance-index')
def referee_performance_index():
    """Referee Performance Index (RPI) page with comprehensive rankings"""
    if data.empty:
        return render_template('referee_performance_index.html', error="No data available", data_source_info=data_source_info)
    
    # Calculate Referee Performance Index
    rpi_data = calculate_referee_performance_index(data)
    
    # Prepare data for visualizations
    scatter_data = []
    radar_data = []
    
    if not rpi_data.empty:
        # Scatter plot data: Fairness vs Consistency
        for _, ref in rpi_data.iterrows():
            scatter_data.append({
                'name': ref['RefereeName'],
                'fairness': ref['FairnessScore'],
                'consistency': ref['ConsistencyScore'],
                'rpi': ref['RPI'],
                'games': ref['GamesRefereed']
            })
        
        # Radar data for top 10 referees
        for _, ref in rpi_data.head(10).iterrows():
            radar_data.append({
                'name': ref['RefereeName'],
                'fairness': ref['FairnessScore'],
                'consistency': ref['ConsistencyScore'],
                'control': ref['GameControlScore'],
                'experience': ref['ExperienceScore']
            })
    
    return render_template('referee_performance_index.html',
                         rpi_data=rpi_data,
                         scatter_data=scatter_data,
                         radar_data=radar_data,
                         divisions=divisions,
                         data_source_info=data_source_info)

@app.route('/deeper-analysis')
def deeper_analysis():
    """Deep game analysis page with advanced metrics"""
    if data.empty:
        return render_template('deeper_analysis.html', error="No data available", divisions=divisions, data_source_info=data_source_info)
    
    # Get division filter from query parameters or user preferences
    division_filter = request.args.get('division') or session.get('preferred_division')
    
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
    
    # Get division filter from query parameters or user preferences
    # Default to "M-Division 1:" if no filter is provided (first time visit) and no preference set
    DEFAULT_DIVISION = "M-Division 1:"
    division_param = request.args.get('division')
    preferred_division = session.get('preferred_division')
    
    if division_param is None:
        # No explicit param - use preference or default
        if preferred_division:
            division_filter = preferred_division
            selected_division_param = preferred_division
        else:
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
    
    # Sort by date (oldest first)
    if not fixtures_data.empty and 'DateTime' in fixtures_data.columns:
        fixtures_data = fixtures_data.sort_values('DateTime', ascending=True)
    
    # Get closest games for each team
    closest_games = get_closest_games_by_team(data, division_filter)
    
    return render_template('fixtures.html',
                         fixtures=fixtures_data,
                         matrix_data=matrix_data,
                         divisions=divisions,
                         selected_division=selected_division_param,
                         data_source_info=data_source_info,
                         closest_games=closest_games)

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

@app.route('/game-details')
def game_details_search():
    """Game details search page with searchable functionality similar to player detail"""
    if data.empty:
        return render_template('game_details.html', error="No data available", data_source_info=data_source_info)
    
    # Get all games for autocomplete
    all_games = get_all_games_list(data)
    
    # Get selected game from query parameter
    game_id = request.args.get('game')
    game_details_data = None
    
    if game_id:
        game_details_data = get_game_details(data, game_id)
    
    return render_template('game_details.html',
                         all_games=all_games,
                         game_id=game_id,
                         game=game_details_data,
                         divisions=divisions,
                         data_source_info=data_source_info)

@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    """User preferences page for setting default filters"""
    if request.method == 'POST':
        # Save preferences to session
        session['preferred_division'] = request.form.get('division') or None
        session['preferred_team'] = request.form.get('team') or None
        
        # Validate and save theme preference
        theme = request.form.get('theme', 'default')
        if theme in VALID_THEMES:
            session['preferred_theme'] = theme
        else:
            session['preferred_theme'] = 'default'
        
        # Always redirect to preferences page (don't use user-provided URL)
        return redirect(url_for('preferences'))
    
    # Get all unique teams for dropdown
    home_teams = set(data['HomeTeamName'].unique()) if not data.empty else set()
    away_teams = set(data['AwayTeamName'].unique()) if not data.empty else set()
    all_teams = sorted(home_teams.union(away_teams))
    
    # Get current preferences from session
    current_prefs = {
        'division': session.get('preferred_division'),
        'team': session.get('preferred_team'),
        'theme': session.get('preferred_theme', 'default')
    }
    
    return render_template('preferences.html',
                         divisions=divisions,
                         all_teams=all_teams,
                         current_prefs=current_prefs,
                         data_source_info=data_source_info)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page and authentication"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        admin_password = os.environ.get('ADMIN_PASSWORD', '')
        
        # Check if admin password is configured
        if not admin_password:
            return render_template('admin_login.html', 
                                 error='Admin authentication is not configured. Please set ADMIN_PASSWORD environment variable.')
        
        # Verify password
        if password == admin_password:
            session['admin_authenticated'] = True
            session.permanent = True  # Make session persistent
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', 
                                 error='Invalid password. Please try again.')
    
    # GET request - show login form
    # If already authenticated, redirect to admin
    if is_admin_authenticated():
        return redirect(url_for('admin'))
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_authenticated', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    """Administration page with data statistics"""
    import os
    from datetime import datetime
    
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
        # Check full-game-stats.csv using the constant from utils.py
        if os.path.exists(CSV_FILEPATH):
            mod_time = os.path.getmtime(CSV_FILEPATH)
            file_stats['full-game-stats.csv'] = {
                'size': os.path.getsize(CSV_FILEPATH),
                'modified': datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            file_stats['full-game-stats.csv'] = None
        
        # Check file.csv in current directory (legacy check)
        file_csv_path = os.path.join(os.getcwd(), 'file.csv')
        if os.path.exists(file_csv_path):
            mod_time = os.path.getmtime(file_csv_path)
            file_stats['file.csv'] = {
                'size': os.path.getsize(file_csv_path),
                'modified': datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            file_stats['file.csv'] = None
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
@login_required
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

@app.route('/admin/export-season', methods=['POST'])
@login_required
def export_season_data():
    """Handle season data export"""
    import tempfile
    from flask import send_file
    
    try:
        # Get options from request
        include_raw = request.form.get('include_raw', 'false').lower() == 'true'
        
        # Create temporary file for export
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            tmp_path = tmp_file.name
        
        # Export the data
        result = export_season_archive(output_path=tmp_path, include_raw=include_raw)
        
        if result['success']:
            # Generate a nice filename
            from datetime import datetime
            season_id = result.get('season_id', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f"flbb-data-{season_id}-{timestamp}.zip"
            
            # Send file to user
            return send_file(
                tmp_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/zip'
            )
        else:
            # Log the full error for debugging
            logger.error(f"Export failed: {'; '.join(result['errors'])}")
            return {'success': False, 'error': 'Export failed. Please check server logs for details.'}, 400
            
    except Exception as e:
        # Log the full exception for debugging
        logger.error(f"Export failed with exception: {str(e)}", exc_info=True)
        return {'success': False, 'error': 'Export failed due to server error. Please contact administrator.'}, 500

# API endpoints for hover tooltips
@app.route('/api/hover/player/<player_name>')
def api_player_hover(player_name):
    """API endpoint to get player hover statistics"""
    if data.empty:
        return jsonify({'error': 'No data available'}), 404
    
    # URL decode the player name
    player_name = unquote(player_name)
    
    stats = get_player_hover_stats(data, player_name)
    if stats is None:
        return jsonify({'error': 'Player not found'}), 404
    
    return jsonify(stats)

@app.route('/api/hover/team/<team_name>')
def api_team_hover(team_name):
    """API endpoint to get team hover statistics"""
    if data.empty:
        return jsonify({'error': 'No data available'}), 404
    
    # URL decode the team name
    team_name = unquote(team_name)
    
    stats = get_team_hover_stats(data, team_name)
    if stats is None:
        return jsonify({'error': 'Team not found'}), 404
    
    return jsonify(stats)

@app.route('/api/hover/referee/<referee_name>')
def api_referee_hover(referee_name):
    """API endpoint to get referee hover statistics"""
    if data.empty:
        return jsonify({'error': 'No data available'}), 404
    
    # URL decode the referee name
    referee_name = unquote(referee_name)
    
    stats = get_referee_hover_stats(data, referee_name)
    if stats is None:
        return jsonify({'error': 'Referee not found'}), 404
    
    return jsonify(stats)

@app.route('/api/hover/game/<game_id>')
def api_game_hover(game_id):
    """API endpoint to get game hover statistics"""
    if data.empty:
        return jsonify({'error': 'No data available'}), 404
    
    stats = get_game_hover_stats(data, game_id)
    if stats is None:
        return jsonify({'error': 'Game not found'}), 404
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
