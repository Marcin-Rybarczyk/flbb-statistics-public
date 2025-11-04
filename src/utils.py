import os
import pandas as pd
import json
from collections import defaultdict
import zipfile
import tempfile
from datetime import datetime
import html


FULL_GAME_STATS_OUTPUT_DIR = "full-game-stats-output"
CSV_FILEPATH = "data/full-game-stats.csv"
PLAYERS_DATABASE_CSV_FILEPATH = "data/players-database.csv"
FORCE_TO_CREATE_CSV = True
# Flag to control automatic player database CSV generation during data load
# Set to False to disable automatic generation (can still be called manually)
AUTO_CREATE_PLAYER_DATABASE = False

# Date format constants
GAMESDB_DATE_FORMAT = '%A, %B %d, %Y %I:%M:%S %p'  # Format used in gamesDB.json
ISO_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  # Format used in CSV and for display

# Foul visualization settings
MAX_FOUL_BLOCKS_DISPLAY = 20  # Maximum number of visual blocks (■) to display for a single foul type

# Configuration file paths
CONFIG_FILEPATH = "data/config.json"
DEFAULT_CONFIG_FILEPATH = "config.json"

# Global variables to track data source and last update
_data_source_info = {
    'source': 'unknown',  # 'new_data', 'backup_csv', 'none'
    'last_update': None,
    'source_description': 'Unknown data source'
}

# Global variable to cache config
_cached_config = None

def get_data_source_info():
    """
    Get information about the current data source and last update.
    
    Returns:
    dict: Dictionary containing source, last_update, and source_description
    """
    return _data_source_info.copy()

def load_config():
    """
    Load configuration from config.json file.
    First tries data/config.json, then config.json, then returns defaults.
    
    Returns:
    dict: Configuration dictionary
    """
    global _cached_config
    
    if _cached_config is not None:
        return _cached_config
    
    # Try data/config.json first
    for config_path in [CONFIG_FILEPATH, DEFAULT_CONFIG_FILEPATH]:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    _cached_config = config
                    return config
            except Exception as e:
                print(f"Error loading config from {config_path}: {e}")
                continue
    
    # Return default config if no file found
    default_config = {
        "eventName": "FLBB Basketball Season",
        "seasonId": "unknown",
        "dataSource": {
            "baseUrl": "https://www.luxembourg.basketball",
            "allCompetitionsUrl": "https://www.luxembourg.basketball/c/categorie/all"
        },
        "website": {
            "title": "FLBB Basketball Statistics",
            "description": "Basketball statistics for Luxembourg Basketball Federation"
        }
    }
    _cached_config = default_config
    return default_config

def get_season_info():
    """
    Get season information from configuration.
    
    Returns:
    dict: Dictionary containing season ID, event name, and derived info
    """
    config = load_config()
    season_id = config.get('seasonId', 'unknown')
    event_name = config.get('eventName', 'FLBB Basketball Season')
    
    # Extract year information from season ID
    season_year = None
    season_display = season_id
    
    if season_id != 'unknown' and '-' in season_id:
        try:
            years = season_id.split('-')
            if len(years) >= 2:
                season_year = int(years[0])
                season_display = f"{years[0]}-{years[1]}"
        except ValueError:
            pass
    
    return {
        'season_id': season_id,
        'season_display': season_display,
        'season_year': season_year,
        'event_name': event_name,
        'full_name': f"{event_name} ({season_display})" if season_display != 'unknown' else event_name
    }

def get_season_archive_filename(base_name="raw-data"):
    """
    Generate a season-specific archive filename with timestamp.
    
    Parameters:
    base_name (str): Base name for the archive file
    
    Returns:
    str: Formatted filename with season and timestamp
    """
    season_info = get_season_info()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    if season_info['season_id'] != 'unknown':
        return f"{base_name}-{season_info['season_id']}-{timestamp}.zip"
    else:
        return f"{base_name}-{timestamp}.zip"

def extract_last_update_from_data(data):
    """
    Extract the most recent update date from the game data.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    str or None: The most recent date/time found in the data
    """
    if data.empty:
        return None
    
    # Check for DateTime column first
    if 'DateTime' in data.columns:
        try:
            # Convert to datetime and find the maximum
            datetime_series = pd.to_datetime(data['DateTime'], errors='coerce')
            max_datetime = datetime_series.max()
            if pd.notna(max_datetime):
                return max_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
    
    # Fallback to GameEvents column if it contains timestamps
    if 'GameEvents' in data.columns:
        try:
            latest_event_date = None
            for events in data['GameEvents'].dropna():
                # Parse JSON events if they exist
                if isinstance(events, str) and events.startswith('['):
                    import json
                    try:
                        event_list = json.loads(events)
                        for event in event_list:
                            if isinstance(event, dict) and 'EventDateTime' in event:
                                event_date = pd.to_datetime(event['EventDateTime'], errors='coerce')
                                if pd.notna(event_date):
                                    if latest_event_date is None or event_date > latest_event_date:
                                        latest_event_date = event_date
                    except:
                        continue
            
            if latest_event_date:
                return latest_event_date.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
    
    return None

def load_json_data_with_bom_handling(file_path):
    """
    Load data from a JSON file with UTF-8 BOM handling.

    Parameters:
    file_path (str): The path to the JSON file.

    Returns:
    dict: The data loaded from the JSON file, or None if an error occurred.
    """
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def load_data_from_directories(root_dir):
    """
    Load data from files in directories and subdirectories into a pandas DataFrame.

    Parameters:
    root_dir (str): The root directory to search for files.

    Returns:
    pandas.DataFrame: A DataFrame containing the data from all files.
    """

    all_data = []
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(subdir, file)
            #print(f"Loading data from: {file_path}")  # Debugging line
            data = load_json_data_with_bom_handling(file_path)
            if data:
                all_data.append(data)
    print(f"Total files loaded: {len(all_data)}")  # Debugging line
    return all_data


# root_dir = os.path.join(os.getcwd(), FULL_GAME_STATS_OUTPUT_DIR)
# all_data = load_data_from_directories(root_dir) 
# data = pd.DataFrame(all_data)

# data.to_csv(CSV_FILEPATH)

# Function to calculate standings
def calculate_standings(df):
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

def flatten_df(df):
    # Flatten nested 'Teams' and 'Players'
    # Explode 'Teams' first
    df = df.explode('Teams').reset_index(drop=True)
    df_teams = df['Teams'].apply(pd.Series)
    df = pd.concat([df.drop('Teams', axis=1), df_teams], axis=1)

    # Now explode 'Players'
    df = df.explode('Players').reset_index(drop=True)
    df_players = df['Players'].apply(pd.Series)
    df_final = pd.concat([df.drop('Players', axis=1), df_players], axis=1)

    # Now df_final should be flattened, and we can adjust the columns as needed
    # Example: setting the 'Starting Five' as a string 'TRUE'/'FALSE' for CSV
    df_final['Starting Five'] = df_final['Starting Five'].map({True: 'TRUE', False: 'FALSE'})
    df_final['GameEvents'] = ''
    df_final['GameLocation'] = df_final['GameLocation'].str.get('Name')
    df_final['Referres'] = ''
    
    # Export to CSV
    df_final.to_csv('output.csv', index=False)

    # Print the DataFrame to check the output format (optional)
    print(df_final.head())

def load_data_from_directories(root_dir):
    """
    Load data from files in directories and subdirectories into a pandas DataFrame.

    Parameters:
    root_dir (str): The root directory to search for files.

    Returns:
    pandas.DataFrame: A DataFrame containing the data from all files.
    """

    all_data = []
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(subdir, file)
            print(f"Loading data from: {file_path}")  # Debugging line
            data = load_json_data_with_bom_handling(file_path)
            if data:
                all_data.append(data)
    print(f"Total files loaded: {len(all_data)}")  # Debugging line
    return all_data

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
        game_division = game.get('GameDivisionDisplay', 'Unknown')
        home_team = game.get('HomeTeamName', 'Unknown')
        away_team = game.get('AwayTeamName', 'Unknown')
        
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
            
            # Determine opponent team
            opponent_team = 'Unknown'
            if team_name == home_team:
                opponent_team = away_team
            elif team_name == away_team:
                opponent_team = home_team
            
            for player in team.get('Players', []):
                if not isinstance(player, dict):
                    continue
                    
                player_record = {
                    'GameId': game_id,
                    'GameDate': game_date,
                    'GameDivision': game_division,
                    'PlayerName': player.get('Player Name', 'Unknown'),
                    'PlayerNumber': player.get('Player Number', 0),
                    'Team': team_name,
                    'OpponentTeam': opponent_team,
                    'TotalPoints': player.get('Total Points', 0),
                    '1PMadeShots': player.get('1P Made Shots', 0),
                    '2PMadeShots': player.get('2P Made Shots', 0),
                    '3PMadeShots': player.get('3P Made Shots', 0),
                    'TotalFouls': player.get('Total Fouls', 0),
                    'PFouls': player.get('P Fouls', 0),
                    'P1Fouls': player.get('P1 Fouls', 0),
                    'P2Fouls': player.get('P2 Fouls', 0),
                    'P3Fouls': player.get('P3 Fouls', 0),
                    'T1Fouls': player.get('T1 Fouls', 0),
                    'U1Fouls': player.get('U1 Fouls', 0),
                    'U2Fouls': player.get('U2 Fouls', 0),
                    'U3Fouls': player.get('U3 Fouls', 0),
                    'GDFouls': player.get('GD Fouls', 0),
                    'StartingFive': player.get('Starting Five', 'false') == 'true'
                }
                all_players.append(player_record)
    
    return pd.DataFrame(all_players)

def create_players_database(data, output_filepath=None):
    """
    Create a comprehensive player database CSV with aggregated statistics.
    
    Parameters:
    data (DataFrame): The game data
    output_filepath (str): Path for the output CSV file. If None, uses PLAYERS_DATABASE_CSV_FILEPATH
    
    Returns:
    DataFrame: Aggregated player statistics
    """
    if output_filepath is None:
        output_filepath = PLAYERS_DATABASE_CSV_FILEPATH
    
    # Extract all player stats from games
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        print("No player data to create database")
        return pd.DataFrame()
    
    # Aggregate statistics for each player
    # Group by PlayerName and Team (a player might play for different teams)
    player_aggregations = {
        'PlayerNumber': lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0],  # Most common player number
        'GameId': 'count',  # Total games played
        'TotalPoints': 'sum',
        '1PMadeShots': 'sum',
        '2PMadeShots': 'sum',
        '3PMadeShots': 'sum',
        'TotalFouls': 'sum',
        'PFouls': 'sum',
        'P1Fouls': 'sum',
        'P2Fouls': 'sum',
        'P3Fouls': 'sum',
        'T1Fouls': 'sum',
        'U1Fouls': 'sum',
        'U2Fouls': 'sum',
        'U3Fouls': 'sum',
        'GDFouls': 'sum',
        'StartingFive': 'sum'  # Count how many games they started
    }
    
    players_db = player_stats.groupby(['PlayerName', 'Team']).agg(player_aggregations).reset_index()
    
    # Rename columns for clarity
    players_db.rename(columns={
        'GameId': 'GamesPlayed',
        'StartingFive': 'GamesStarted'
    }, inplace=True)
    
    # Calculate derived statistics
    players_db['AvgPointsPerGame'] = (players_db['TotalPoints'] / players_db['GamesPlayed']).round(2)
    players_db['AvgFoulsPerGame'] = (players_db['TotalFouls'] / players_db['GamesPlayed']).round(2)
    players_db['TotalFieldGoalsMade'] = (players_db['1PMadeShots'] + 
                                         players_db['2PMadeShots'] + 
                                         players_db['3PMadeShots'])
    players_db['AvgShotsPerGame'] = (players_db['TotalFieldGoalsMade'] / players_db['GamesPlayed']).round(2)
    players_db['StartingPercentage'] = ((players_db['GamesStarted'] / players_db['GamesPlayed']) * 100).round(1)
    
    # Calculate points per shot (efficiency metric)
    # Set to 0 for players with no field goals made (more accurate than division by 1)
    players_db['PointsPerShot'] = 0.0
    mask = players_db['TotalFieldGoalsMade'] > 0
    players_db.loc[mask, 'PointsPerShot'] = (
        players_db.loc[mask, 'TotalPoints'] / players_db.loc[mask, 'TotalFieldGoalsMade']
    ).round(2)
    
    # Sort by total points (most productive players first)
    players_db = players_db.sort_values('TotalPoints', ascending=False).reset_index(drop=True)
    
    # Reorder columns for better readability
    column_order = [
        'PlayerName', 'Team', 'PlayerNumber', 'GamesPlayed', 'GamesStarted', 'StartingPercentage',
        'TotalPoints', 'AvgPointsPerGame', 
        '1PMadeShots', '2PMadeShots', '3PMadeShots', 'TotalFieldGoalsMade', 
        'AvgShotsPerGame', 'PointsPerShot',
        'TotalFouls', 'AvgFoulsPerGame', 'PFouls', 'P1Fouls', 'P2Fouls', 'P3Fouls', 'T1Fouls', 'U1Fouls', 'U2Fouls', 'U3Fouls', 'GDFouls'
    ]
    
    players_db = players_db[column_order]
    
    # Save to CSV
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        players_db.to_csv(output_filepath, index=False, encoding='utf-8')
        print(f"✅ Player database created: {output_filepath} with {len(players_db)} player records")
    except Exception as e:
        print(f"⚠️  Error saving player database to {output_filepath}: {e}")
    
    return players_db

def get_top_scorers(data, top_n=20, division=None, team=None):
    """
    Get top N scorers across all games.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of top scorers to return
    division (str): Optional division filter
    team (str): Optional team filter
    
    Returns:
    DataFrame: Top scorers with their statistics
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Filter by team if specified
    if team:
        player_stats = player_stats[player_stats['Team'] == team]
    
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

def get_highest_single_game_score(data, top_n=10, division=None, team=None):
    """
    Get the highest single game scores by any player, with one entry per player (their best game).
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of top single game scores to return
    division (str): Optional division filter
    team (str): Optional team filter
    
    Returns:
    DataFrame: Players with highest single game scores (unique players)
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Filter by team if specified
    if team:
        player_stats = player_stats[player_stats['Team'] == team]
    
    # Get the highest score for each player (eliminate duplicates)
    # Group by player and get the row with max points for each player
    idx = player_stats.groupby('PlayerName')['TotalPoints'].idxmax()
    top_single_games = player_stats.loc[idx].nlargest(top_n, 'TotalPoints').reset_index(drop=True)
    
    return top_single_games

def get_player_shooting_efficiency(data, top_n=20, division=None, team=None):
    """
    Get player free throw statistics (leaders by total free throws made).
    
    Note: This function name is kept for backward compatibility, but it now shows
    free throw production instead of shooting efficiency, since per-player shot
    attempts data is not available in the dataset.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of top players to return
    division (str): Optional division filter
    team (str): Optional team filter
    
    Returns:
    DataFrame: Players with free throw statistics
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Filter by team if specified
    if team:
        player_stats = player_stats[player_stats['Team'] == team]
    
    # Group by player and calculate free throw stats
    ft_stats = player_stats.groupby(['PlayerName', 'Team']).agg({
        '1PMadeShots': 'sum',
        'TotalPoints': 'sum',
        'GameId': 'count'  # Games played
    }).reset_index()
    
    ft_stats.rename(columns={
        'GameId': 'GamesPlayed',
        '1PMadeShots': 'TotalFreeThrowsMade'
    }, inplace=True)
    
    # Calculate average free throws per game
    ft_stats['AvgFreeThrowsPerGame'] = (ft_stats['TotalFreeThrowsMade'] / 
                                         ft_stats['GamesPlayed']).round(2)
    ft_stats['AvgPointsPerGame'] = (ft_stats['TotalPoints'] / 
                                    ft_stats['GamesPlayed']).round(1)
    
    # Filter players with at least 5 games and at least 5 total free throws made
    ft_stats = ft_stats[
        (ft_stats['GamesPlayed'] >= 5) & 
        (ft_stats['TotalFreeThrowsMade'] >= 5)
    ]
    
    return ft_stats.sort_values('TotalFreeThrowsMade', ascending=False).head(top_n).reset_index(drop=True)

def get_starting_five_vs_bench_stats(data, division=None, team=None):
    """
    Compare starting five players vs bench players statistics.
    
    Parameters:
    data (DataFrame): The game data
    division (str): Optional division filter
    team (str): Optional team filter
    
    Returns:
    dict: Statistics comparing starters vs bench, including:
        - starters_avg: Average points per game for starters
        - bench_avg: Average points per game for bench players
        - difference: Difference between starter and bench averages
        - starters: DataFrame with top starting players
        - bench: DataFrame with top bench players
        - starters_total_players: Total unique starter players
        - starters_total_games: Total game appearances by starters
        - starters_avg_points: Average points per game for starters
        - starters_total_points: Total points scored by starters
        - starters_avg_fouls: Average fouls per game for starters
        - starters_total_shots: Total shots made by starters
        - starters_avg_shots_per_game: Average shots per game for starters
        - (corresponding bench_* fields for bench players)
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return {}
    
    # Filter by team if specified
    if team:
        player_stats = player_stats[player_stats['Team'] == team]
    
    # Separate starters and bench players
    starters = player_stats[player_stats['StartingFive'] == True]
    bench = player_stats[player_stats['StartingFive'] == False]
    
    if starters.empty and bench.empty:
        return {}
    
    # Calculate aggregate statistics for each group
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
    
    # Calculate top performers for each group
    def get_top_performers(group, top_n=20):
        if group.empty:
            return pd.DataFrame()
        
        # Group by player and calculate aggregate statistics
        player_aggregated = group.groupby(['PlayerName', 'Team']).agg({
            'TotalPoints': ['sum', 'mean'],
            'GameId': 'count'
        }).reset_index()
        
        # Flatten column names
        player_aggregated.columns = ['PlayerName', 'Team', 'TotalPoints', 'AvgPointsPerGame', 'GamesPlayed']
        
        # Sort by total points and get top performers
        player_aggregated = player_aggregated.sort_values('TotalPoints', ascending=False).head(top_n)
        
        return player_aggregated
    
    # Get top performers
    top_starters = get_top_performers(starters, 20)
    top_bench = get_top_performers(bench, 20)
    
    # Calculate summary averages for comparison
    starters_avg = starter_stats.get('starters_avg_points', 0)
    bench_avg = bench_stats.get('bench_avg_points', 0)
    difference = round(starters_avg - bench_avg, 1) if starters_avg is not None and bench_avg is not None else 0
    
    # Build result dictionary with all required keys
    result = {
        **starter_stats,
        **bench_stats,
        'starters_avg': starters_avg,
        'bench_avg': bench_avg,
        'difference': difference,
    }
    
    # Add DataFrames only if they have data
    if not top_starters.empty:
        result['starters'] = top_starters
    
    if not top_bench.empty:
        result['bench'] = top_bench
    
    return result

def get_double_digit_scorers(data, min_points=10, division=None, team=None):
    """
    Get players with double-digit scoring games.
    
    Parameters:
    data (DataFrame): The game data
    min_points (int): Minimum points for double-digit game
    division (str): Optional division filter
    team (str): Optional team filter
    
    Returns:
    DataFrame: Players with double-digit scoring statistics
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Filter by team if specified
    if team:
        player_stats = player_stats[player_stats['Team'] == team]
    
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
    all_player_games = player_stats.groupby(['PlayerName', 'Team']).size().reset_index(name='TotalGames')
    double_digit_stats = double_digit_stats.merge(all_player_games, on=['PlayerName', 'Team'], how='left')
    
    # Calculate percentage of double-digit games
    double_digit_stats['DoubleDigitPercentage'] = (
        (double_digit_stats['DoubleDigitGames'] / double_digit_stats['TotalGames']) * 100
    ).round(1)
    
    # Round averages
    double_digit_stats['AvgInDoubleDigitGames'] = double_digit_stats['AvgInDoubleDigitGames'].round(1)
    
    return double_digit_stats.sort_values('DoubleDigitGames', ascending=False).head(20).reset_index(drop=True)

def get_consistent_scorers(data, min_games=5, division=None, team=None):
    """
    Get players who consistently score well across multiple games.
    
    Parameters:
    data (DataFrame): The game data
    min_games (int): Minimum games to be considered
    division (str): Optional division filter
    team (str): Optional team filter
    
    Returns:
    DataFrame: Most consistent scorers
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Filter by team if specified
    if team:
        player_stats = player_stats[player_stats['Team'] == team]
    
    # Group by player and calculate consistency metrics
    player_groups = player_stats.groupby(['PlayerName', 'Team'])
    
    consistency_stats = []
    for (player, team_name), group in player_groups:
        if len(group) >= min_games:
            points = group['TotalPoints']
            consistency_stats.append({
                'PlayerName': player,
                'Team': team_name,
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

def get_top_three_pointers(data, top_n=10, division=None, team=None):
    """
    Get top N three-point shooters.
    
    Parameters:
    data (DataFrame): The game data  
    top_n (int): Number of top three-point shooters to return
    division (str): Optional division filter
    team (str): Optional team filter
    
    Returns:
    DataFrame: Top three-point shooters with their statistics
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Filter by team if specified
    if team:
        player_stats = player_stats[player_stats['Team'] == team]
    
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

def get_top_foulers(data, top_n=10, division=None, team=None):
    """
    Get players with the most fouls.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of top foulers to return
    division (str): Optional division filter
    team (str): Optional team filter
    
    Returns:
    DataFrame: Top foulers with their statistics including:
        - TotalFouls: Sum of all fouls
        - WeightedTotalFouls: Weighted sum (P/P1/P2/P3=1, T1/U1/U2/U3=2, GD=5)
        - FoulDetails: String describing foul type breakdown
        - Individual foul type columns (PFouls, P1Fouls, etc.)
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return pd.DataFrame()
    
    # Filter by team if specified
    if team:
        player_stats = player_stats[player_stats['Team'] == team]
    
    # Group by player and calculate foul totals
    foul_stats = player_stats.groupby(['PlayerName', 'Team']).agg({
        'TotalFouls': 'sum',
        'PFouls': 'sum',
        'P1Fouls': 'sum',
        'P2Fouls': 'sum',
        'P3Fouls': 'sum',
        'T1Fouls': 'sum',
        'U1Fouls': 'sum',
        'U2Fouls': 'sum',
        'U3Fouls': 'sum',
        'GDFouls': 'sum',
        'GameId': 'count',  # Games played
        'TotalPoints': 'sum'
    }).reset_index()
    
    foul_stats.rename(columns={'GameId': 'GamesPlayed'}, inplace=True)
    foul_stats['AvgFoulsPerGame'] = (foul_stats['TotalFouls'] / foul_stats['GamesPlayed']).round(1)
    
    # Calculate weighted total fouls
    # P, P1, P2, P3 = weight 1
    # T1, U1, U2, U3 = weight 2
    # GD = weight 5
    foul_stats['WeightedTotalFouls'] = (
        foul_stats['PFouls'] * 1 +
        foul_stats['P1Fouls'] * 1 +
        foul_stats['P2Fouls'] * 1 +
        foul_stats['P3Fouls'] * 1 +
        foul_stats['T1Fouls'] * 2 +
        foul_stats['U1Fouls'] * 2 +
        foul_stats['U2Fouls'] * 2 +
        foul_stats['U3Fouls'] * 2 +
        foul_stats['GDFouls'] * 5
    )
    
    # Create foul details string
    def create_foul_details(row):
        """
        Create visual foul details with colored blocks sorted by severity.
        
        Args:
            row (pandas.Series): A row from the foul statistics DataFrame containing
                                foul counts for each type (PFouls, P1Fouls, etc.)
        
        Returns:
            str: HTML string representing foul details with colored visual blocks
                 sorted by severity (most severe first)
        
        Foul severity order (most severe first):
        - GD (Game Disqualification): #8B0000 (dark red)
        - U3, U2, U1 (Unsportsmanlike): #DC143C, #FF6347, #FF8C69 (red shades)
        - T1 (Technical): #FF8C00 (dark orange)
        - P3, P2, P1, P (Personal): #FFD700, #FFA500, #FFB84D, #FFE4B5 (gold/orange shades)
        
        Display format:
        - For counts >= 10: Use bigger blocks (◼) for every 10 fouls and small blocks (■) for remainder
        - For counts < 10: Use small blocks (■) only
        """
        # Define fouls in order of severity (most severe first)
        foul_types = [
            ('GD', row['GDFouls'], '#8B0000', 'Game Disqualification'),
            ('U3', row['U3Fouls'], '#DC143C', 'Unsportsmanlike 3'),
            ('U2', row['U2Fouls'], '#FF6347', 'Unsportsmanlike 2'),
            ('U1', row['U1Fouls'], '#FF8C69', 'Unsportsmanlike 1'),
            ('T1', row['T1Fouls'], '#FF8C00', 'Technical'),
            ('P3', row['P3Fouls'], '#FFD700', 'Personal 3'),
            ('P2', row['P2Fouls'], '#FFA500', 'Personal 2'),
            ('P1', row['P1Fouls'], '#FFB84D', 'Personal 1'),
            ('P', row['PFouls'], '#FFE4B5', 'Personal'),
        ]
        
        details = []
        for foul_code, count, color, title in foul_types:
            if count > 0:
                count = int(count)
                
                # When count >= 10, combine every 10 fouls into one bigger block
                if count >= 10:
                    big_blocks = count // 10  # Number of big blocks (each represents 10 fouls)
                    small_blocks = count % 10  # Remaining fouls as small blocks
                    
                    # Limit display to reasonable amount
                    # Note: The actual total count is always shown in the (count) text, so users
                    # can see the full number even when the visual display is truncated
                    if big_blocks > MAX_FOUL_BLOCKS_DISPLAY:
                        # When truncating, calculate total remaining fouls (not displayed visually)
                        # Example: 215 fouls = 21 big blocks + 5 small blocks
                        #   Display: 20 big blocks + "...+15" + "(215)"
                        #   The "...+15" represents 1 truncated big block (10 fouls) + 5 small blocks
                        remaining_fouls = (big_blocks - MAX_FOUL_BLOCKS_DISPLAY) * 10 + small_blocks
                        blocks = '◼' * MAX_FOUL_BLOCKS_DISPLAY + f'...+{remaining_fouls}'
                    else:
                        blocks = '◼' * big_blocks + '■' * small_blocks
                else:
                    # For counts < 10, just use small blocks
                    blocks = '■' * count
                
                # Escape HTML to prevent XSS (color is a hardcoded constant, no need to escape)
                escaped_title = html.escape(title)
                escaped_foul_code = html.escape(foul_code)
                escaped_blocks = html.escape(blocks)
                
                # Create HTML for this foul type
                foul_html = (
                    f'<div class="foul-card" title="{escaped_title}">'
                    f'<span class="foul-label">{escaped_foul_code}:</span>'
                    f'<span class="foul-blocks" style="color: {color};">{escaped_blocks}</span> '
                    f'<span class="foul-count">({count})</span>'
                    f'</div>'
                )
                details.append(foul_html)
        
        return ''.join(details) if details else '<span class="no-fouls">No fouls</span>'
    
    foul_stats['FoulDetails'] = foul_stats.apply(create_foul_details, axis=1)
    
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

def get_highest_scoring_games(data, top_n=10, division=None):
    """
    Get games with highest total scores.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of games to return
    division (str): Optional division filter
    
    Returns:
    DataFrame: Games with highest scores
    """
    # Create a copy to avoid modifying the original data
    data_copy = data.copy()
    
    # Filter by division if specified
    if division:
        data_copy = data_copy[data_copy['GameDivisionDisplay'] == division]
    
    data_copy['TotalScore'] = data_copy['FinalHomeScore'] + data_copy['FinalAwayScore']
    highest_games = data_copy.nlargest(top_n, 'TotalScore')
    return highest_games[['GameId', 'HomeTeamName', 'AwayTeamName', 'FinalHomeScore', 'FinalAwayScore', 'TotalScore', 'GameDivisionDisplay']]

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

def get_referee_detail_stats(data, referee_name):
    """
    Get detailed statistics for a specific referee including:
    - List of games arbitrated
    - Foul type breakdown
    - Game-by-game statistics
    
    Parameters:
    data (DataFrame): The game data
    referee_name (str): The referee name to get details for
    
    Returns:
    dict: Dictionary containing referee statistics and game list
    """
    import ast
    
    if data.empty:
        return None
    
    referee_games = []
    foul_types = defaultdict(int)
    total_fouls = 0
    
    # Iterate through all games to find games this referee officiated
    for _, game in data.iterrows():
        try:
            # Parse referee data
            if isinstance(game['Referres'], str):
                refs_data = ast.literal_eval(game['Referres'])
            else:
                refs_data = game['Referres']
        except:
            continue
        
        if not isinstance(refs_data, list):
            continue
        
        # Check if this referee was in this game
        referee_in_game = False
        for ref in refs_data:
            if isinstance(ref, dict) and ref.get('Referee Name') == referee_name:
                referee_in_game = True
                break
        
        if not referee_in_game:
            continue
        
        # This referee was in this game, extract details
        game_fouls = 0
        game_foul_types = defaultdict(int)
        
        # Parse game events to count fouls and foul types
        try:
            if isinstance(game['GameEvents'], str):
                events_data = ast.literal_eval(game['GameEvents'])
            else:
                events_data = game['GameEvents']
            
            # Count foul events by type
            for event in events_data:
                if isinstance(event, dict) and 'EventAction' in event:
                    action = event['EventAction']
                    
                    # Check for foul added events (not deleted)
                    if 'Foul Added' in action:
                        game_fouls += 1
                        total_fouls += 1
                        
                        # Extract foul type - check more specific patterns first
                        # This ensures 'P2 Foul Added' and 'P1 Foul Added' are matched
                        # before the more general 'P Foul Added'
                        if 'P3 Foul Added' in action:
                            game_foul_types['P3'] += 1
                            foul_types['P3'] += 1
                        elif 'P2 Foul Added' in action:
                            game_foul_types['P2'] += 1
                            foul_types['P2'] += 1
                        elif 'P1 Foul Added' in action:
                            game_foul_types['P1'] += 1
                            foul_types['P1'] += 1
                        elif 'P Foul Added' in action:
                            game_foul_types['P'] += 1
                            foul_types['P'] += 1
                        elif 'U2 Foul Added' in action:
                            game_foul_types['U2'] += 1
                            foul_types['U2'] += 1
                        elif 'U1 Foul Added' in action:
                            game_foul_types['U1'] += 1
                            foul_types['U1'] += 1
                        elif 'T1 Foul Added' in action:
                            game_foul_types['T1'] += 1
                            foul_types['T1'] += 1
                        elif 'C1 Foul Added' in action:
                            game_foul_types['C1'] += 1
                            foul_types['C1'] += 1
                        elif 'B1 Foul Added' in action:
                            game_foul_types['B1'] += 1
                            foul_types['B1'] += 1
                        elif 'D2 Foul Added' in action:
                            game_foul_types['D2'] += 1
                            foul_types['D2'] += 1
                        else:
                            # Catch any unexpected foul types not yet categorized
                            # If this happens, the foul type should be investigated and potentially
                            # added as a new category above
                            game_foul_types['Other'] += 1
                            foul_types['Other'] += 1
        except:
            pass
        
        # Add game to referee's game list
        game_info = {
            'game_id': game['GameId'],
            'date_time': game['DateTime'],
            'division': game['GameDivisionDisplay'],
            'home_team': game['HomeTeamName'],
            'away_team': game['AwayTeamName'],
            'final_score': game['GameFinalScore'],
            'home_score': game['FinalHomeScore'],
            'away_score': game['FinalAwayScore'],
            'winner': game['GameWinner'],
            'location': game['GameLocation'],
            'fouls_called': game_fouls,
            'foul_types': dict(game_foul_types)
        }
        referee_games.append(game_info)
    
    if not referee_games:
        return None
    
    # Sort games by date (most recent first)
    referee_games.sort(key=lambda x: x['date_time'], reverse=True)
    
    # Calculate summary statistics
    total_games = len(referee_games)
    avg_fouls_per_game = total_fouls / total_games if total_games > 0 else 0
    
    return {
        'referee_name': referee_name,
        'total_games': total_games,
        'total_fouls': total_fouls,
        'avg_fouls_per_game': round(avg_fouls_per_game, 1),
        'foul_types': dict(foul_types),
        'games': referee_games
    }

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
        
        # Sort events chronologically for accurate analysis
        sorted_events = sorted(events_data, key=lambda x: x.get('EventDateTime', '') if isinstance(x, dict) else '')
        
        # Analyze score progression
        tie_count = 0
        lead_changes = 0
        max_home_lead = 0
        max_away_lead = 0
        current_advantage = 0
        previous_leader = None
        
        for event in sorted_events:
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

def get_most_tie_scores(data, top_n=10, division=None):
    """
    Get games with the most tie scores.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of games to return
    division (str): Optional division filter
    
    Returns:
    DataFrame: Games with most tie scores
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    game_analysis = analyze_game_events(data)
    
    if game_analysis.empty:
        return pd.DataFrame()
    
    return game_analysis.nlargest(top_n, 'TieScores')

def get_most_lead_changes(data, top_n=10, division=None):
    """
    Get games with the most lead changes.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of games to return
    division (str): Optional division filter
    
    Returns:
    DataFrame: Games with most lead changes
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    game_analysis = analyze_game_events(data)
    
    if game_analysis.empty:
        return pd.DataFrame()
    
    return game_analysis.nlargest(top_n, 'LeadChanges')

def get_biggest_leads(data, top_n=10, division=None):
    """
    Get games with the biggest leads.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of games to return
    division (str): Optional division filter
    
    Returns:
    DataFrame: Games with biggest leads
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    game_analysis = analyze_game_events(data)
    
    if game_analysis.empty:
        return pd.DataFrame()
    
    return game_analysis.nlargest(top_n, 'BiggestLead')

def get_biggest_wins(data, top_n=10, division=None):
    """
    Get games with the biggest win margins.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of games to return
    division (str): Optional division filter
    
    Returns:
    DataFrame: Games with biggest win margins
    """
    # Filter by division if specified
    if division:
        data = data[data['GameDivisionDisplay'] == division]
    
    game_analysis = analyze_game_events(data)
    
    if game_analysis.empty:
        return pd.DataFrame()
    
    return game_analysis.nlargest(top_n, 'WinMargin')

# Only load data when functions are called, not at import time
def create_csv_from_json_data(output_dir, csv_filepath):
    """
    Generate CSV file from JSON data in the specified directory.
    
    Args:
        output_dir (str): Directory containing JSON files
        csv_filepath (str): Path for the output CSV file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Loading JSON files from {output_dir}...")
        all_data = load_data_from_directories(output_dir)
        
        if not all_data:
            print("No JSON data found")
            return False
        
        # Create DataFrame
        data = pd.DataFrame(all_data)
        print(f"Loaded {len(data)} game records")
        
        # Flatten the DataFrame
        print("Flattening nested data...")
        flatten_df(data)
        
        # Save to CSV
        print(f"Saving to {csv_filepath}...")
        data.to_csv(csv_filepath, index=False)
        
        print(f"Successfully created {csv_filepath} with {len(data)} records")
        return True
        
    except Exception as e:
        print(f"Error creating CSV: {e}")
        return False

def load_game_data():
    """
    Load game data prioritizing new data over repository backup.
    For live website, use only new data downloaded. Repository data used only as backup.
    """
    global _data_source_info
    
    root_dir = os.path.join(os.getcwd(), FULL_GAME_STATS_OUTPUT_DIR)
    
    # PRIORITY 1: Try to load from new JSON data directory first (live data)
    if os.path.exists(root_dir):
        all_data = load_data_from_directories(root_dir) 
        if all_data:  # If we have new JSON data, use it
            data = pd.DataFrame(all_data)
            flatten_df(data)
            
            # Update data source info
            last_update = extract_last_update_from_data(data)
            _data_source_info = {
                'source': 'new_data',
                'last_update': last_update,
                'source_description': f'New data from {FULL_GAME_STATS_OUTPUT_DIR} directory'
            }
            
            # Optionally save to CSV for backup
            if FORCE_TO_CREATE_CSV:
                try:
                    data.to_csv(CSV_FILEPATH, index=False)
                    # Create player database CSV if enabled
                    if AUTO_CREATE_PLAYER_DATABASE:
                        create_players_database(data)
                except:
                    pass  # Don't fail if we can't save backup
            
            print(f"✅ Using new data: {len(data)} games loaded from JSON files")
            return data
    
    # PRIORITY 2: Fall back to repository CSV backup only if no new data available
    if os.path.exists(CSV_FILEPATH):
        try:
            data = pd.read_csv(CSV_FILEPATH)
            if not data.empty:
                # Update data source info
                csv_mod_time = os.path.getmtime(CSV_FILEPATH)
                import datetime
                csv_date = datetime.datetime.fromtimestamp(csv_mod_time).strftime("%Y-%m-%d %H:%M:%S")
                
                last_update = extract_last_update_from_data(data)
                _data_source_info = {
                    'source': 'backup_csv',
                    'last_update': last_update or csv_date,
                    'source_description': f'Repository backup CSV (file modified: {csv_date})'
                }
                
                print(f"⚠️  Using backup data: {len(data)} games loaded from repository CSV")
                
                # Create player database from backup CSV if enabled
                if FORCE_TO_CREATE_CSV and AUTO_CREATE_PLAYER_DATABASE:
                    try:
                        create_players_database(data)
                    except:
                        pass  # Don't fail if we can't create player database
                
                return data
            else:
                print(f"Warning: {CSV_FILEPATH} exists but is empty")
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            print(f"Warning: Error reading {CSV_FILEPATH}: {e}")
        except Exception as e:
            print(f"Warning: Unexpected error reading {CSV_FILEPATH}: {e}")
    
    # PRIORITY 3: No data available
    _data_source_info = {
        'source': 'none',
        'last_update': None,
        'source_description': 'No data available'
    }
    
    print("❌ No data available: Neither new data nor backup CSV found")
    return pd.DataFrame()

# =============================================================================
# DEEPER GAME ANALYSIS FUNCTIONS
# =============================================================================

def get_player_game_impact_analysis(data, top_n=20):
    """
    Analyze which players have the most impact on games beyond just scoring.
    Considers win rate when playing, efficiency, and contribution to team success.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of top impact players to return
    
    Returns:
    DataFrame: Players ranked by overall game impact
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        # Return empty DataFrame with expected column structure
        return pd.DataFrame(columns=[
            'PlayerName', 'Team', 'GamesPlayed', 'WinRate', 'AvgPoints', 
            'AvgFouls', 'Efficiency', 'PointDifferential', 'StartingRate', 
            'ImpactScore', 'TotalPoints', 'Wins', 'Losses'
        ])
    
    # Create game outcome mapping
    game_outcomes = {}
    for _, game in data.iterrows():
        game_id = game['GameId']
        home_team = game['HomeTeamName']
        away_team = game['AwayTeamName']
        home_score = game['FinalHomeScore']
        away_score = game['FinalAwayScore']
        
        game_outcomes[game_id] = {
            'winner': home_team if home_score > away_score else away_team,
            'loser': away_team if home_score > away_score else home_team,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score
        }
    
    # Calculate impact metrics for each player
    player_impact = []
    
    for (player_name, team), group in player_stats.groupby(['PlayerName', 'Team']):
        if len(group) < 2:  # Skip players with too few games
            continue
            
        games_played = len(group)
        total_points = group['TotalPoints'].sum()
        total_fouls = group['TotalFouls'].sum()
        avg_points = total_points / games_played
        avg_fouls = total_fouls / games_played
        
        # Calculate win rate when this player plays
        wins = 0
        team_total_scores = []
        opponent_total_scores = []
        
        for _, player_game in group.iterrows():
            game_id = player_game['GameId']
            if game_id in game_outcomes:
                outcome = game_outcomes[game_id]
                if outcome['winner'] == team:
                    wins += 1
                
                # Track team performance when this player plays
                if team == outcome['home_team']:
                    team_total_scores.append(outcome['home_score'])
                    opponent_total_scores.append(outcome['away_score'])
                else:
                    team_total_scores.append(outcome['away_score'])
                    opponent_total_scores.append(outcome['home_score'])
        
        win_rate = (wins / games_played) * 100 if games_played > 0 else 0
        
        # Calculate efficiency metrics
        total_shots = group['1PMadeShots'].sum() + group['2PMadeShots'].sum() + group['3PMadeShots'].sum()
        efficiency = total_points / max(total_shots, 1)  # Points per shot
        
        # Calculate team performance when player plays
        avg_team_score = sum(team_total_scores) / len(team_total_scores) if team_total_scores else 0
        avg_opponent_score = sum(opponent_total_scores) / len(opponent_total_scores) if opponent_total_scores else 0
        point_differential = avg_team_score - avg_opponent_score
        
        # Calculate starting five rate
        starting_games = group['StartingFive'].sum()
        starting_rate = (starting_games / games_played) * 100
        
        # Calculate overall impact score (weighted combination of metrics)
        impact_score = (
            (avg_points * 0.3) +  # Scoring contribution
            (win_rate * 0.25) +   # Team success when playing
            (efficiency * 10 * 0.2) +  # Shooting efficiency
            (point_differential * 0.15) +  # Team performance differential
            (starting_rate * 0.1) -  # Starting importance
            (avg_fouls * 2)  # Penalty for fouling
        )
        
        player_impact.append({
            'PlayerName': player_name,
            'Team': team,
            'GamesPlayed': games_played,
            'WinRate': round(win_rate, 1),
            'AvgPoints': round(avg_points, 1),
            'AvgFouls': round(avg_fouls, 1),
            'Efficiency': round(efficiency, 2),
            'PointDifferential': round(point_differential, 1),
            'StartingRate': round(starting_rate, 1),
            'ImpactScore': round(impact_score, 1),
            'TotalPoints': total_points,
            'Wins': wins,
            'Losses': games_played - wins
        })
    
    impact_df = pd.DataFrame(player_impact)
    return impact_df.sort_values('ImpactScore', ascending=False).head(top_n).reset_index(drop=True)


def get_player_foul_impact_analysis(data, top_n=20):
    """
    Analyze which players have the most impact on their team's foul rate per game.
    
    Parameters:
    data (DataFrame): The game data  
    top_n (int): Number of players to analyze
    
    Returns:
    DataFrame: Players and their impact on team foul patterns
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        # Return empty DataFrame with expected column structure
        return pd.DataFrame(columns=[
            'PlayerName', 'Team', 'GamesPlayed', 'TotalFouls', 'PersonalAvgFouls',
            'TeamFoulsWithPlayer', 'TeamFoulsWithoutPlayer', 'FoulDifference', 
            'FoulImpactPercentage', 'GamesWithPlayer', 'GamesWithoutPlayer', 'AbsImpact'
        ])
    
    # Calculate team foul rates for each game
    team_game_fouls = {}
    for _, game in player_stats.iterrows():
        key = (game['Team'], game['GameId'])
        if key not in team_game_fouls:
            team_game_fouls[key] = {
                'team': game['Team'],
                'game_id': game['GameId'],
                'total_fouls': 0,
                'player_count': 0
            }
        team_game_fouls[key]['total_fouls'] += game['TotalFouls']
        team_game_fouls[key]['player_count'] += 1
    
    # Convert to DataFrame for easier analysis
    game_fouls_df = pd.DataFrame(list(team_game_fouls.values()))
    game_fouls_df['avg_fouls_per_player'] = game_fouls_df['total_fouls'] / game_fouls_df['player_count']
    
    # Calculate overall team averages
    team_averages = game_fouls_df.groupby('team').agg({
        'total_fouls': 'mean',
        'avg_fouls_per_player': 'mean'
    }).round(2)
    
    # Analyze individual player impact
    foul_impact_analysis = []
    
    for (player_name, team), group in player_stats.groupby(['PlayerName', 'Team']):
        if len(group) < 3:  # Skip players with too few games
            continue
        
        player_games = set(group['GameId'])
        team_games = game_fouls_df[game_fouls_df['team'] == team]
        
        # Games with this player
        with_player = team_games[team_games['game_id'].isin(player_games)]
        # Games without this player  
        without_player = team_games[~team_games['game_id'].isin(player_games)]
        
        if len(with_player) == 0 or len(without_player) == 0:
            continue
            
        avg_fouls_with = with_player['total_fouls'].mean()
        avg_fouls_without = without_player['total_fouls'].mean()
        foul_difference = avg_fouls_with - avg_fouls_without
        
        # Player's personal foul stats
        personal_fouls = group['TotalFouls'].sum()
        games_played = len(group)
        personal_avg_fouls = personal_fouls / games_played
        
        # Calculate foul impact score
        # Positive score means player increases team fouls, negative means decreases
        impact_percentage = ((foul_difference / max(avg_fouls_without, 1)) * 100) if avg_fouls_without > 0 else 0
        
        foul_impact_analysis.append({
            'PlayerName': player_name,
            'Team': team,
            'GamesPlayed': games_played,
            'TotalFouls': personal_fouls,
            'PersonalAvgFouls': round(personal_avg_fouls, 1),
            'TeamFoulsWithPlayer': round(avg_fouls_with, 1),
            'TeamFoulsWithoutPlayer': round(avg_fouls_without, 1),
            'FoulDifference': round(foul_difference, 1),
            'FoulImpactPercentage': round(impact_percentage, 1),
            'GamesWithPlayer': len(with_player),
            'GamesWithoutPlayer': len(without_player)
        })
    
    foul_df = pd.DataFrame(foul_impact_analysis)
    # Sort by absolute impact (both positive and negative are interesting)
    foul_df['AbsImpact'] = abs(foul_df['FoulImpactPercentage'])
    return foul_df.sort_values('AbsImpact', ascending=False).head(top_n).reset_index(drop=True)


def get_best_player_combinations(data, min_games=3):
    """
    Analyze the best starting five combinations and player synergies.
    
    Parameters:
    data (DataFrame): The game data
    min_games (int): Minimum games together to be considered
    
    Returns:
    dict: Analysis of best player combinations
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return {}
    
    # Create game outcome mapping
    game_outcomes = {}
    for _, game in data.iterrows():
        game_id = game['GameId']
        home_team = game['HomeTeamName']
        away_team = game['AwayTeamName']
        home_score = game['FinalHomeScore']
        away_score = game['FinalAwayScore']
        
        game_outcomes[game_id] = {
            'winner': home_team if home_score > away_score else away_team,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score
        }
    
    # Analyze starting five combinations
    starting_five_combinations = {}
    
    # Group by team and game to get starting fives
    for (team, game_id), group in player_stats.groupby(['Team', 'GameId']):
        starters = group[group['StartingFive'] == True]['PlayerName'].tolist()
        if len(starters) == 5:  # Only analyze complete starting fives
            starters_key = tuple(sorted(starters))
            
            if starters_key not in starting_five_combinations:
                starting_five_combinations[starters_key] = {
                    'players': starters,
                    'team': team,
                    'games': [],
                    'wins': 0,
                    'total_points': 0,
                    'total_fouls': 0
                }
            
            # Record game result
            starting_five_combinations[starters_key]['games'].append(game_id)
            if game_id in game_outcomes and game_outcomes[game_id]['winner'] == team:
                starting_five_combinations[starters_key]['wins'] += 1
            
            # Add team performance metrics
            team_points = group['TotalPoints'].sum()
            team_fouls = group['TotalFouls'].sum()
            starting_five_combinations[starters_key]['total_points'] += team_points
            starting_five_combinations[starters_key]['total_fouls'] += team_fouls
    
    # Analyze best combinations
    best_combinations = []
    for combo_key, combo_data in starting_five_combinations.items():
        games_played = len(combo_data['games'])
        if games_played >= min_games:
            win_rate = (combo_data['wins'] / games_played) * 100
            avg_points = combo_data['total_points'] / games_played
            avg_fouls = combo_data['total_fouls'] / games_played
            
            best_combinations.append({
                'Players': ', '.join(combo_data['players']),
                'Team': combo_data['team'],
                'GamesPlayed': games_played,
                'Wins': combo_data['wins'],
                'Losses': games_played - combo_data['wins'],
                'WinRate': round(win_rate, 1),
                'AvgPointsPerGame': round(avg_points, 1),
                'AvgFoulsPerGame': round(avg_fouls, 1),
                'EfficiencyScore': round(win_rate + (avg_points / 10) - (avg_fouls / 2), 1)
            })
    
    best_combinations_df = pd.DataFrame(best_combinations)
    if not best_combinations_df.empty:
        best_combinations_df = best_combinations_df.sort_values('EfficiencyScore', ascending=False)
    
    # Analyze individual player synergies (simplified version)
    player_synergies = []
    for team in player_stats['Team'].unique():
        team_data = player_stats[player_stats['Team'] == team]
        team_players = list(team_data['PlayerName'].unique())
        
        # For each pair of players on the same team
        for i, player1 in enumerate(team_players):
            for player2 in team_players[i+1:]:
                # Find games they played together
                p1_games = set(team_data[team_data['PlayerName'] == player1]['GameId'])
                p2_games = set(team_data[team_data['PlayerName'] == player2]['GameId'])
                together_games = p1_games.intersection(p2_games)
                
                if len(together_games) >= min_games:
                    # Calculate performance when playing together
                    together_wins = 0
                    for game_id in together_games:
                        if game_id in game_outcomes and game_outcomes[game_id]['winner'] == team:
                            together_wins += 1
                    
                    win_rate = (together_wins / len(together_games)) * 100
                    
                    player_synergies.append({
                        'Player1': player1,
                        'Player2': player2,
                        'Team': team,
                        'GamesTogether': len(together_games),
                        'WinsTogether': together_wins,
                        'WinRate': round(win_rate, 1)
                    })
    
    synergies_df = pd.DataFrame(player_synergies)
    if not synergies_df.empty:
        synergies_df = synergies_df.sort_values('WinRate', ascending=False).head(20)
    
    return {
        'best_starting_fives': best_combinations_df,
        'player_synergies': synergies_df
    }


def get_referee_game_impact_analysis(data):
    """
    Analyze which referees have the biggest impact on game outcomes and patterns.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    dict: Comprehensive referee impact analysis
    """
    referee_impact = []
    
    # Process each game to extract referee influence
    for _, game in data.iterrows():
        game_id = game['GameId']
        home_team = game['HomeTeamName']
        away_team = game['AwayTeamName']
        home_score = game['FinalHomeScore']
        away_score = game['FinalAwayScore']
        
        # Parse referee data
        try:
            if isinstance(game['Referres'], str):
                import ast
                referees_data = ast.literal_eval(game['Referres'])
            else:
                referees_data = game['Referres']
        except:
            continue
            
        if not isinstance(referees_data, list):
            continue
        
        # Parse game events to count fouls
        total_fouls = 0
        try:
            if isinstance(game['GameEvents'], str):
                import ast
                events = ast.literal_eval(game['GameEvents'])
                for event in events:
                    if isinstance(event, dict) and 'EventAction' in event:
                        if 'Foul' in event['EventAction']:
                            total_fouls += 1
        except:
            pass
        
        # Calculate game characteristics
        total_score = home_score + away_score
        score_difference = abs(home_score - away_score)
        high_scoring = total_score > 100  # Threshold for high-scoring game
        close_game = score_difference <= 5
        home_win = home_score > away_score
        
        # Record impact for each referee in this game
        for ref in referees_data:
            if isinstance(ref, dict) and 'Referee Name' in ref:
                referee_name = ref['Referee Name']
                
                referee_impact.append({
                    'RefereeName': referee_name,
                    'GameId': game_id,
                    'HomeTeam': home_team,
                    'AwayTeam': away_team,
                    'TotalScore': total_score,
                    'ScoreDifference': score_difference,
                    'TotalFouls': total_fouls,
                    'HighScoring': high_scoring,
                    'CloseGame': close_game,
                    'HomeWin': home_win
                })
    
    if not referee_impact:
        return {}
    
    ref_df = pd.DataFrame(referee_impact)
    
    # Aggregate referee statistics
    ref_summary = ref_df.groupby('RefereeName').agg({
        'GameId': 'count',
        'TotalScore': ['mean', 'std'],
        'ScoreDifference': ['mean', 'std'],
        'TotalFouls': ['mean', 'std'],
        'HighScoring': 'sum',
        'CloseGame': 'sum',
        'HomeWin': 'sum'
    }).round(2)
    
    # Flatten column names
    ref_summary.columns = ['_'.join(col).strip() if col[1] else col[0] for col in ref_summary.columns]
    ref_summary = ref_summary.reset_index()
    
    # Calculate derived metrics
    ref_summary['GamesRefereed'] = ref_summary['GameId_count']
    ref_summary['AvgTotalScore'] = ref_summary['TotalScore_mean']
    ref_summary['AvgScoreDifference'] = ref_summary['ScoreDifference_mean']
    ref_summary['AvgFouls'] = ref_summary['TotalFouls_mean']
    ref_summary['HighScoringRate'] = ((ref_summary['HighScoring_sum'] / ref_summary['GamesRefereed']) * 100).round(1)
    ref_summary['CloseGameRate'] = ((ref_summary['CloseGame_sum'] / ref_summary['GamesRefereed']) * 100).round(1)
    ref_summary['HomeWinRate'] = ((ref_summary['HomeWin_sum'] / ref_summary['GamesRefereed']) * 100).round(1)
    
    # Calculate impact scores
    ref_summary['FoulImpact'] = ref_summary['AvgFouls'] - ref_summary['AvgFouls'].mean()
    ref_summary['ScoringImpact'] = ref_summary['AvgTotalScore'] - ref_summary['AvgTotalScore'].mean()
    ref_summary['CompetitivenessImpact'] = ref_summary['CloseGameRate'] - ref_summary['CloseGameRate'].mean()
    
    # Filter referees with sufficient games
    qualified_refs = ref_summary[ref_summary['GamesRefereed'] >= 2]
    
    return {
        'referee_impact_summary': qualified_refs[['RefereeName', 'GamesRefereed', 'AvgFouls', 'AvgTotalScore', 
                                                 'AvgScoreDifference', 'HighScoringRate', 'CloseGameRate', 
                                                 'HomeWinRate', 'FoulImpact', 'ScoringImpact', 'CompetitivenessImpact']].sort_values('GamesRefereed', ascending=False),
        'most_foul_prone_refs': qualified_refs.nlargest(10, 'AvgFouls')[['RefereeName', 'GamesRefereed', 'AvgFouls']],
        'least_foul_prone_refs': qualified_refs.nsmallest(10, 'AvgFouls')[['RefereeName', 'GamesRefereed', 'AvgFouls']],
        'high_scoring_refs': qualified_refs.nlargest(10, 'AvgTotalScore')[['RefereeName', 'GamesRefereed', 'AvgTotalScore']],
        'most_competitive_refs': qualified_refs.nlargest(10, 'CloseGameRate')[['RefereeName', 'GamesRefereed', 'CloseGameRate']]
    }

def _parse_points_from_action(action):
    """
    Parse points value from a GameEvents action string.
    
    Handles both point additions and deletions, returning positive values for 
    additions and negative values for deletions.
    
    Parameters:
    action (str): The EventAction string (e.g., '2P Points Added', '3P Points Deleted')
    
    Returns:
    int: Points value (positive for additions, negative for deletions, 0 if not a point event)
    
    Examples:
    - '2P Points Added' -> 2
    - '3P Points Deleted' -> -3
    - 'Timeout' -> 0
    """
    if '1P Points Added' in action:
        return 1
    elif '2P Points Added' in action:
        return 2
    elif '3P Points Added' in action:
        return 3
    elif '1P Points Deleted' in action:
        return -1
    elif '2P Points Deleted' in action:
        return -2
    elif '3P Points Deleted' in action:
        return -3
    return 0

def calculate_referee_performance_index(data):
    """
    Calculate a comprehensive Referee Performance Index (RPI) based on multiple metrics:
    - Fairness: balance in fouls called for home vs away teams
    - Consistency: variance in fouls called per game
    - Game Control: ratio of technical/unsportsmanlike fouls
    - Experience: number of games officiated
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    DataFrame: Referee performance rankings with detailed metrics
    """
    import ast
    import numpy as np
    
    if data.empty:
        return pd.DataFrame()
    
    referee_data = []
    
    # Process each game to collect referee-specific metrics
    for _, game in data.iterrows():
        try:
            # Parse referee data
            if isinstance(game['Referres'], str):
                refs_data = ast.literal_eval(game['Referres'])
            else:
                refs_data = game['Referres']
        except:
            continue
            
        if not isinstance(refs_data, list):
            continue
        
        # Parse game events
        home_fouls = 0
        away_fouls = 0
        technical_fouls = 0  # T1, U1, U2, C1, B1, D2
        total_fouls = 0
        
        try:
            if isinstance(game['GameEvents'], str):
                events_data = ast.literal_eval(game['GameEvents'])
            else:
                events_data = game['GameEvents']
            
            home_team = game['HomeTeamName']
            away_team = game['AwayTeamName']
            
            for event in events_data:
                if isinstance(event, dict) and 'EventAction' in event:
                    action = event['EventAction']
                    
                    if 'Foul Added' in action:
                        total_fouls += 1
                        
                        # Determine if it's a technical/unsportsmanlike foul
                        if any(foul_type in action for foul_type in ['T1', 'U1', 'U2', 'C1', 'B1', 'D2']):
                            technical_fouls += 1
                        
                        # Determine which team committed the foul
                        event_team = event.get('EventTeam', '')
                        if event_team == home_team:
                            home_fouls += 1
                        elif event_team == away_team:
                            away_fouls += 1
        except:
            pass
        
        # Calculate game metrics
        total_score = game['FinalHomeScore'] + game['FinalAwayScore']
        score_difference = abs(game['FinalHomeScore'] - game['FinalAwayScore'])
        foul_differential = abs(home_fouls - away_fouls)
        technical_foul_rate = (technical_fouls / total_fouls * 100) if total_fouls > 0 else 0
        
        # Record metrics for each referee in this game
        for ref in refs_data:
            if isinstance(ref, dict) and 'Referee Name' in ref:
                referee_data.append({
                    'RefereeName': ref['Referee Name'],
                    'GameId': game['GameId'],
                    'TotalFouls': total_fouls,
                    'HomeFouls': home_fouls,
                    'AwayFouls': away_fouls,
                    'FoulDifferential': foul_differential,
                    'TechnicalFouls': technical_fouls,
                    'TechnicalFoulRate': technical_foul_rate,
                    'TotalScore': total_score,
                    'ScoreDifference': score_difference,
                    'CloseGame': score_difference <= 10
                })
    
    if not referee_data:
        return pd.DataFrame()
    
    ref_df = pd.DataFrame(referee_data)
    
    # Aggregate referee statistics
    ref_summary = ref_df.groupby('RefereeName').agg({
        'GameId': 'count',
        'TotalFouls': ['mean', 'std'],
        'FoulDifferential': ['mean', 'std'],
        'TechnicalFoulRate': 'mean',
        'TotalScore': 'mean',
        'ScoreDifference': 'mean',
        'CloseGame': 'sum'
    }).round(2)
    
    # Flatten column names
    ref_summary.columns = ['_'.join(map(str, col)).strip() if isinstance(col, tuple) else str(col) for col in ref_summary.columns]
    ref_summary = ref_summary.reset_index()
    
    # Rename and calculate derived metrics
    ref_summary['GamesRefereed'] = ref_summary['GameId_count']
    ref_summary['AvgFoulsPerGame'] = ref_summary['TotalFouls_mean']
    ref_summary['FoulVariance'] = ref_summary['TotalFouls_std'].fillna(0)
    ref_summary['AvgFoulDifferential'] = ref_summary['FoulDifferential_mean']
    ref_summary['FoulDifferentialVariance'] = ref_summary['FoulDifferential_std'].fillna(0)
    ref_summary['AvgTechnicalFoulRate'] = ref_summary['TechnicalFoulRate_mean']
    ref_summary['AvgTotalScore'] = ref_summary['TotalScore_mean']
    ref_summary['AvgScoreDifference'] = ref_summary['ScoreDifference_mean']
    ref_summary['CloseGamesCount'] = ref_summary['CloseGame_sum']
    
    # Filter referees with at least 3 games for meaningful statistics
    qualified_refs = ref_summary[ref_summary['GamesRefereed'] >= 3].copy()
    
    if qualified_refs.empty:
        return pd.DataFrame()
    
    # Calculate normalized scores (0-100 scale, higher is better)
    
    # 1. Fairness Score (lower foul differential is better)
    max_diff = qualified_refs['AvgFoulDifferential'].max()
    if max_diff > 0:
        qualified_refs['FairnessScore'] = ((max_diff - qualified_refs['AvgFoulDifferential']) / max_diff * 100).round(1)
    else:
        qualified_refs['FairnessScore'] = 100.0
    
    # 2. Consistency Score (lower variance is better)
    max_variance = qualified_refs['FoulVariance'].max()
    if max_variance > 0:
        qualified_refs['ConsistencyScore'] = ((max_variance - qualified_refs['FoulVariance']) / max_variance * 100).round(1)
    else:
        qualified_refs['ConsistencyScore'] = 100.0
    
    # 3. Game Control Score (lower technical foul rate is better, but not zero)
    # Normalize technical foul rate - ideal is around 5-10%
    qualified_refs['GameControlScore'] = qualified_refs['AvgTechnicalFoulRate'].apply(
        lambda x: max(0, 100 - abs(x - 7.5) * 5)  # Penalty increases as we deviate from 7.5%
    ).round(1)
    
    # 4. Experience Score (more games is better, with diminishing returns)
    max_games = qualified_refs['GamesRefereed'].max()
    qualified_refs['ExperienceScore'] = (np.log1p(qualified_refs['GamesRefereed']) / np.log1p(max_games) * 100).round(1)
    
    # Calculate Composite RPI (weighted average)
    # Weights: Fairness 30%, Consistency 30%, Game Control 25%, Experience 15%
    qualified_refs['RPI'] = (
        qualified_refs['FairnessScore'] * 0.30 +
        qualified_refs['ConsistencyScore'] * 0.30 +
        qualified_refs['GameControlScore'] * 0.25 +
        qualified_refs['ExperienceScore'] * 0.15
    ).round(1)
    
    # Add ranking
    qualified_refs = qualified_refs.sort_values('RPI', ascending=False)
    qualified_refs['Rank'] = range(1, len(qualified_refs) + 1)
    
    # Select and order columns for output
    output_columns = [
        'Rank', 'RefereeName', 'GamesRefereed', 'RPI',
        'FairnessScore', 'ConsistencyScore', 'GameControlScore', 'ExperienceScore',
        'AvgFoulsPerGame', 'FoulVariance', 'AvgFoulDifferential', 'FoulDifferentialVariance',
        'AvgTechnicalFoulRate', 'AvgTotalScore', 'AvgScoreDifference', 'CloseGamesCount'
    ]
    
    return qualified_refs[output_columns].reset_index(drop=True)

def get_top_scorer_by_game(data):
    """
    Get the top scorer for each game.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    DataFrame: Game data with top scorer information added
    """
    if data.empty:
        return pd.DataFrame()
    
    fixtures = []
    
    for _, game in data.iterrows():
        game_id = game['GameId']
        home_team = normalize_team_name_for_display(game['HomeTeamName'])
        away_team = normalize_team_name_for_display(game['AwayTeamName'])
        home_score = game['FinalHomeScore']
        away_score = game['FinalAwayScore']
        date_time = game['DateTime']
        referees = game['Referres']
        division = game['GameDivisionDisplay']
        location = game['GameLocation']
        
        # Extract top scorer from game events
        top_scorer_name = None
        top_scorer_points = 0
        top_scorer_team = None
        
        try:
            if isinstance(game['GameEvents'], str):
                import ast
                events_data = ast.literal_eval(game['GameEvents'])
                
                # Extract player stats from scoring events
                player_stats = {}
                for event in events_data:
                    if isinstance(event, dict) and 'EventActor' in event and 'EventAction' in event:
                        action = event['EventAction']
                        player_name = event['EventActor']
                        team = event.get('EventTeam', '')
                        
                        # Parse points from action (handles both additions and deletions)
                        points = _parse_points_from_action(action)
                        
                        if points != 0 and player_name:
                            if player_name not in player_stats:
                                player_stats[player_name] = {'points': 0, 'team': team}
                            
                            player_stats[player_name]['points'] += points
                            player_stats[player_name]['team'] = team
                
                # Find top scorer
                if player_stats:
                    top_player = max(player_stats.items(), key=lambda x: x[1]['points'])
                    top_scorer_name = top_player[0]
                    top_scorer_points = top_player[1]['points']
                    top_scorer_team = top_player[1]['team']
                    
        except Exception as e:
            # If there's an error parsing events, continue without top scorer
            pass
        
        # Parse referees
        referee_names = []
        try:
            if isinstance(referees, str):
                import ast
                ref_data = ast.literal_eval(referees)
            else:
                ref_data = referees
            
            if isinstance(ref_data, list):
                referee_names = [ref.get('Referee Name', '') for ref in ref_data if isinstance(ref, dict)]
        except:
            referee_names = []
        
        # Calculate hotness for finished games
        hotness_score = 0
        hotness_icon = "❄️"
        if pd.notna(home_score) and pd.notna(away_score):
            try:
                if isinstance(game['GameEvents'], str):
                    events_data = ast.literal_eval(game['GameEvents'])
                    teams_data = ast.literal_eval(game['Teams']) if isinstance(game['Teams'], str) else game['Teams']
                    score_evolution = _calculate_score_evolution(events_data, home_team, away_team, teams_data)
                    game_stats = _calculate_game_statistics(score_evolution)
                    hotness_score = calculate_hotness_score(game_stats['lead_changes'], game_stats['tied_scores'], game_stats.get('close_game_ratio'))
                    hotness_icon = get_hotness_icon(hotness_score)
            except:
                pass
        
        # Convert scores to int to avoid float display issues
        home_score_int = int(home_score) if pd.notna(home_score) else None
        away_score_int = int(away_score) if pd.notna(away_score) else None
        top_scorer_points_int = int(top_scorer_points)
        
        fixtures.append({
            'GameId': game_id,
            'HomeTeam': home_team,
            'AwayTeam': away_team,
            'HomeTeamName': home_team,  # Add for consistency with future games
            'AwayTeamName': away_team,  # Add for consistency with future games
            'HomeScore': home_score_int,
            'AwayScore': away_score_int,
            'DateTime': date_time,
            'Division': division,
            'GameDivisionDisplay': division,  # Add for consistency with future games
            'Location': parse_location_name(location),  # Use the same parsing function
            'TopScorerName': top_scorer_name if top_scorer_name else 'N/A',
            'TopScorerPoints': top_scorer_points_int,
            'TopScorerTeam': top_scorer_team if top_scorer_team else 'N/A',
            'Referees': referee_names,
            'IsFinished': pd.notna(home_score) and pd.notna(away_score),
            'HotnessScore': hotness_score,
            'HotnessIcon': hotness_icon
        })
    
    df = pd.DataFrame(fixtures)
    
    # Convert score columns to nullable integer type to avoid float display
    if not df.empty:
        for col in ['HomeScore', 'AwayScore', 'TopScorerPoints']:
            if col in df.columns:
                df[col] = df[col].astype('Int64')
    
    return df


def load_future_games_from_gamesdb(gamesdb_path='data/gamesDB.json'):
    """
    Load future games from gamesDB.json file.
    
    Parameters:
    gamesdb_path (str): Path to gamesDB.json file
    
    Returns:
    list: List of future game dictionaries
    """
    if not os.path.exists(gamesdb_path):
        return []
    
    try:
        with open(gamesdb_path, 'r', encoding='utf-8-sig') as f:
            games = json.load(f)
        
        # Filter for future games (not started yet)
        future_games = [g for g in games if g.get('GameStatus') == 'NotStarted']
        return future_games
    except Exception as e:
        print(f"Error loading future games from {gamesdb_path}: {e}")
        return []


def normalize_team_name_for_display(team_name):
    """
    Normalize team name for consistent display across finished and future games.
    Handles common abbreviations like AB, BC, US that should be uppercase.
    Also normalizes accents to prevent duplicates (e.g., Gréngewald -> Grengewald).
    
    Parameters:
    team_name (str): The team name to normalize
    
    Returns:
    str: Normalized team name
    """
    if not team_name:
        return team_name
    
    # Remove accents/diacritics for consistency
    import unicodedata
    team_name = ''.join(
        c for c in unicodedata.normalize('NFD', team_name)
        if unicodedata.category(c) != 'Mn'
    )
    
    # List of abbreviations that should be all uppercase
    uppercase_abbreviations = ['AB', 'BC', 'US', 'AS']
    
    # Split the name into words
    words = team_name.split()
    normalized_words = []
    
    for word in words:
        # Check if this word (uppercase version) is in our abbreviations list
        if word.upper() in uppercase_abbreviations:
            normalized_words.append(word.upper())
        else:
            # Keep the original capitalization for other words
            normalized_words.append(word)
    
    return ' '.join(normalized_words)


def parse_team_names_from_url(game_url):
    """
    Extract home and away team names from the game URL.
    URL pattern: https://www.luxembourg.basketball/match/{id}/{date}/{home-team}/{away-team}/{division}
    
    Parameters:
    game_url (str): The game URL
    
    Returns:
    tuple: (home_team, away_team) or (None, None) if parsing fails
    """
    try:
        # Split URL by '/'
        parts = game_url.split('/')
        if len(parts) >= 7:
            # Get home and away team slugs
            home_slug = parts[-3]
            away_slug = parts[-2]
            
            # Convert slugs to readable names (replace hyphens with spaces, title case)
            home_team = ' '.join(word.title() for word in home_slug.split('-'))
            away_team = ' '.join(word.title() for word in away_slug.split('-'))
            
            # Normalize team names to handle abbreviations
            home_team = normalize_team_name_for_display(home_team)
            away_team = normalize_team_name_for_display(away_team)
            
            return home_team, away_team
    except Exception as e:
        print(f"Error parsing team names from URL {game_url}: {e}")
    
    return None, None


def convert_division_name(division_name):
    """
    Convert division name from gamesDB.json format to CSV format.
    
    This ensures future games use the same division naming convention as finished games.
    
    Examples:
    - "m-division-1" -> "M-Division 1:"
    - "m-enovos-leaguetour-qualificatif" -> "M-ENOVOS LEAGUE:Tour qualificatif"
    - "m-nationale-2tour-qualificatif" -> "M-Nationale 2:Tour qualificatif"
    
    Parameters:
    division_name (str): Division name from gamesDB.json
    
    Returns:
    str: Standardized division name matching CSV format
    """
    if not division_name:
        return division_name
    
    # Handle different patterns
    if division_name.startswith('m-division-'):
        # Simple division: m-division-1 -> M-Division 1:
        parts = division_name.split('-')
        if len(parts) >= 3:
            division_num = parts[2]
            return f"M-Division {division_num}:"
    
    elif 'enovos-league' in division_name.lower():
        # ENOVOS LEAGUE: m-enovos-leaguetour-qualificatif -> M-ENOVOS LEAGUE:Tour qualificatif
        if 'tour' in division_name.lower():
            try:
                # Split on 'tour' and handle the suffix
                idx = division_name.lower().index('tour')
                suffix = division_name[idx:].replace('-', ' ')
                # Capitalize 'Tour'
                suffix = 'T' + suffix[1:]
                return f"M-ENOVOS LEAGUE:{suffix}"
            except ValueError:
                # If 'tour' not found (shouldn't happen due to outer check), use fallback
                pass
    
    elif 'nationale' in division_name.lower():
        # Nationale: m-nationale-2tour-qualificatif -> M-Nationale 2:Tour qualificatif
        # Extract number and tour part
        temp = division_name.replace('m-nationale-', '')
        # Find where 'tour' starts
        if 'tour' in temp.lower():
            try:
                idx = temp.lower().index('tour')
                num = temp[:idx]
                suffix = temp[idx:].replace('-', ' ')
                # Capitalize 'Tour'
                suffix = 'T' + suffix[1:]
                return f"M-Nationale {num}:{suffix}"
            except ValueError:
                # If 'tour' not found (shouldn't happen due to outer check), use fallback
                pass
    
    # Fallback: use title case with spaces
    return division_name.replace('-', ' ').title()


def convert_future_game_to_dataframe_format(game):
    """
    Convert a future game from gamesDB.json format to DataFrame row format.
    
    Parameters:
    game (dict): Future game from gamesDB.json
    
    Returns:
    dict: Game data in DataFrame format
    """
    from datetime import datetime
    
    home_team, away_team = parse_team_names_from_url(game.get('GameUrl', ''))
    
    # Parse the date from ScheduledGameDate and convert to ISO format
    game_date = None
    if 'ScheduledGameDate' in game and isinstance(game['ScheduledGameDate'], dict):
        date_str = game['ScheduledGameDate'].get('DateTime')
        if date_str:
            try:
                # Parse the date string like "Saturday, November 8, 2025 12:00:00 AM"
                dt = datetime.strptime(date_str, GAMESDB_DATE_FORMAT)
                # Convert to ISO format to match finished games: "YYYY-MM-DD HH:MM:SS"
                game_date = dt.strftime(ISO_DATE_FORMAT)
            except ValueError as e:
                # If parsing fails, keep the original date string
                game_date = date_str
    
    # Convert division name to match CSV format
    division_display = convert_division_name(game.get('GameDivisionName', ''))
    
    return {
        'GameId': game.get('GameId'),
        'GameLocation': None,  # Not available for future games
        'GameDivisionDisplay': division_display,
        'Division': division_display,  # Add for consistency with finished games
        'GameTeamsShort': f"{home_team} vs {away_team}" if home_team and away_team else None,
        'GameFinalScore': None,
        'GameWinner': None,
        'GameLoser': None,
        'HomeTeam': home_team,  # Add for consistency with finished games
        'AwayTeam': away_team,  # Add for consistency with finished games
        'HomeTeamName': home_team,
        'AwayTeamName': away_team,
        'HomeTeamLeaguePoints': None,
        'AwayTeamLeaguePoints': None,
        'FinalHomeScore': None,
        'FinalAwayScore': None,
        'Referres': None,
        'DateTime': game_date,
        'Teams': None,
        'GameEvents': None,
        'IsFinished': False,
        'GameStatus': game.get('GameStatus', 'NotStarted'),
        'GameUrl': game.get('GameUrl'),
        'IsFutureGame': True
    }


def get_all_fixtures_data(data, division_filter=None):
    """
    Get all fixtures data with enhanced information for display.
    Includes both finished games from CSV and future games from gamesDB.json.
    
    Parameters:
    data (DataFrame): The game data
    division_filter (str): Optional filter by division
    
    Returns:
    DataFrame: Enhanced fixtures data (finished + future games)
    """
    # Get finished games with enhanced info
    filtered_data = data.copy()
    if division_filter is not None:
        filtered_data = filtered_data[filtered_data['GameDivisionDisplay'] == division_filter]
    
    finished_games = get_top_scorer_by_game(filtered_data)
    
    # Load and add future games
    future_games = load_future_games_from_gamesdb()
    if future_games:
        future_games_list = [convert_future_game_to_dataframe_format(g) for g in future_games]
        future_games_df = pd.DataFrame(future_games_list)
        
        # Apply division filter to future games if provided
        if division_filter is not None and not future_games_df.empty:
            future_games_df = future_games_df[future_games_df['GameDivisionDisplay'] == division_filter]
        
        # Combine finished and future games
        if not future_games_df.empty:
            all_games = pd.concat([finished_games, future_games_df], ignore_index=True)
            return all_games
    
    return finished_games


def get_fixtures_matrix_data(data, division_filter=None):
    """
    Get fixtures data organized as a matrix (team vs team).
    Includes both finished games and future games from gamesDB.json.
    
    Parameters:
    data (DataFrame): The game data
    division_filter (str): Optional filter by division
    
    Returns:
    dict: Matrix data with teams as rows/columns and games as cell contents
    """
    if data.empty:
        return {'teams': [], 'matrix': {}, 'divisions': []}
    
    # Apply division filter if provided
    filtered_data = data.copy()
    if division_filter:
        filtered_data = filtered_data[filtered_data['GameDivisionDisplay'] == division_filter]
    
    # Load and add future games
    future_games = load_future_games_from_gamesdb()
    if future_games:
        future_games_list = [convert_future_game_to_dataframe_format(g) for g in future_games]
        future_games_df = pd.DataFrame(future_games_list)
        
        # Apply division filter to future games if provided
        if division_filter and not future_games_df.empty:
            future_games_df = future_games_df[future_games_df['GameDivisionDisplay'] == division_filter]
        
        # Combine finished and future games
        if not future_games_df.empty:
            filtered_data = pd.concat([filtered_data, future_games_df], ignore_index=True)
    
    # Get unique teams with normalization
    home_teams = set(normalize_team_name_for_display(name) for name in filtered_data['HomeTeamName'].dropna())
    away_teams = set(normalize_team_name_for_display(name) for name in filtered_data['AwayTeamName'].dropna())
    all_teams = sorted(home_teams.union(away_teams))
    
    # Get unique divisions for the filter dropdown (from both finished and future games)
    all_divisions_finished = set(data['GameDivisionDisplay'].dropna().unique())
    if future_games:
        future_divisions = set(convert_division_name(g.get('GameDivisionName', '')) for g in future_games)
        all_divisions = sorted(all_divisions_finished.union(future_divisions))
    else:
        all_divisions = sorted(all_divisions_finished)
    
    # Initialize matrix
    matrix = {}
    for home_team in all_teams:
        matrix[home_team] = {}
        for away_team in all_teams:
            matrix[home_team][away_team] = []
    
    # Populate matrix with games
    for _, game in filtered_data.iterrows():
        raw_home = game['HomeTeamName']
        raw_away = game['AwayTeamName']
        
        if pd.notna(raw_home) and pd.notna(raw_away):
            home_team = normalize_team_name_for_display(raw_home)
            away_team = normalize_team_name_for_display(raw_away)
            # Parse location to get just the name
            location_name = parse_location_name(game['GameLocation'])
            
            # Calculate hotness for finished games
            hotness_score = 0
            hotness_icon = "❄️"
            is_finished = pd.notna(game.get('FinalHomeScore')) and pd.notna(game.get('FinalAwayScore'))
            
            if is_finished:
                try:
                    import ast
                    events = ast.literal_eval(game['GameEvents']) if isinstance(game['GameEvents'], str) else game['GameEvents']
                    teams = ast.literal_eval(game['Teams']) if isinstance(game['Teams'], str) else game['Teams']
                    score_evolution = _calculate_score_evolution(events, game['HomeTeamName'], game['AwayTeamName'], teams)
                    game_stats = _calculate_game_statistics(score_evolution)
                    hotness_score = calculate_hotness_score(game_stats['lead_changes'], game_stats['tied_scores'], game_stats.get('close_game_ratio'))
                    hotness_icon = get_hotness_icon(hotness_score)
                except:
                    pass
            
            # Get enhanced game info
            # Convert scores to int to avoid float display issues
            home_score_val = game.get('FinalHomeScore')
            away_score_val = game.get('FinalAwayScore')
            home_score_int = int(home_score_val) if pd.notna(home_score_val) else None
            away_score_int = int(away_score_val) if pd.notna(away_score_val) else None
            
            game_info = {
                'game_id': game['GameId'],
                'date': game['DateTime'][:16] if pd.notna(game['DateTime']) else 'TBD',
                'home_score': home_score_int,
                'away_score': away_score_int,
                'location': location_name,
                'division': game['GameDivisionDisplay'],
                'is_finished': is_finished,
                'referees': parse_referees(game.get('Referres')) if is_finished else [],
                'top_scorer': get_game_top_scorer(game) if is_finished else {'name': None, 'points': 0, 'team': None},
                'hotness_score': hotness_score,
                'hotness_icon': hotness_icon,
                'is_future': game.get('IsFutureGame', False)
            }
            
            matrix[home_team][away_team].append(game_info)
    
    return {
        'teams': all_teams,
        'matrix': matrix,
        'divisions': all_divisions,
        'current_division': division_filter or (all_divisions[0] if all_divisions else None)
    }


def get_closest_games_by_team(data, division_filter=None):
    """
    Identify the closest upcoming game for each team.
    
    Parameters:
    data (DataFrame): The game data
    division_filter (str): Optional filter by division
    
    Returns:
    dict: Dictionary mapping team names to their closest game_id
    """
    from datetime import datetime
    
    # Get all fixtures including future games
    all_fixtures = get_all_fixtures_data(data, division_filter)
    
    # Check if IsFutureGame column exists
    if 'IsFutureGame' not in all_fixtures.columns or all_fixtures.empty:
        return {}
    
    # Filter for future games only
    future_games = all_fixtures[
        (all_fixtures['IsFutureGame']) & 
        (all_fixtures['DateTime'].notna())
    ].copy()
    
    if future_games.empty:
        return {}
    
    # Convert DateTime to datetime objects for comparison
    future_games['DateTimeParsed'] = pd.to_datetime(future_games['DateTime'], errors='coerce')
    future_games = future_games[future_games['DateTimeParsed'].notna()]
    
    # Get current time
    now = datetime.now()
    
    # Find closest game for each team
    closest_games = {}
    
    for team in pd.concat([future_games['HomeTeamName'], future_games['AwayTeamName']]).unique():
        if pd.isna(team):
            continue
        
        # Get all future games for this team
        team_games = future_games[
            (future_games['HomeTeamName'] == team) | 
            (future_games['AwayTeamName'] == team)
        ].copy()
        
        if not team_games.empty:
            # Find the game with the earliest date in the future
            future_team_games = team_games[team_games['DateTimeParsed'] >= now]
            if not future_team_games.empty:
                closest_game = future_team_games.loc[future_team_games['DateTimeParsed'].idxmin()]
                closest_games[team] = closest_game['GameId']
    
    return closest_games


def parse_location_name(location_data):
    """
    Parse location data to extract just the name.
    
    Parameters:
    location_data: The location data (could be string, dict, or JSON string)
    
    Returns:
    str: The location name or 'TBD'
    """
    if pd.isna(location_data):
        return 'TBD'
    
    try:
        if isinstance(location_data, str):
            # Try to parse as JSON if it looks like JSON
            if location_data.startswith('{') and location_data.endswith('}'):
                import ast
                location_dict = ast.literal_eval(location_data)
                return location_dict.get('Name', 'TBD')
            else:
                return location_data
        elif isinstance(location_data, dict):
            return location_data.get('Name', 'TBD')
        else:
            return str(location_data)
    except:
        return 'TBD'


def parse_referees(referees_data):
    """
    Parse referee data to extract names.
    
    Parameters:
    referees_data: The referee data
    
    Returns:
    list: List of referee names
    """
    if pd.isna(referees_data):
        return []
    
    try:
        if isinstance(referees_data, str):
            import ast
            ref_data = ast.literal_eval(referees_data)
        else:
            ref_data = referees_data
        
        if isinstance(ref_data, list):
            return [ref.get('Referee Name', '') for ref in ref_data if isinstance(ref, dict)]
        else:
            return []
    except:
        return []


def get_game_top_scorer(game):
    """
    Get the top scorer for a specific game.
    
    Parameters:
    game: Game data row
    
    Returns:
    dict: Top scorer information
    """
    try:
        if isinstance(game['GameEvents'], str):
            import ast
            events_data = ast.literal_eval(game['GameEvents'])
            
            # Extract player stats from scoring events
            player_stats = {}
            for event in events_data:
                if isinstance(event, dict) and 'EventActor' in event and 'EventAction' in event:
                    action = event['EventAction']
                    player_name = event['EventActor']
                    team = event.get('EventTeam', '')
                    
                    # Parse points from action (handles both additions and deletions)
                    points = _parse_points_from_action(action)
                    
                    if points != 0 and player_name:
                        if player_name not in player_stats:
                            player_stats[player_name] = {'points': 0, 'team': team}
                        
                        player_stats[player_name]['points'] += points
                        player_stats[player_name]['team'] = team
            
            # Find top scorer
            if player_stats:
                top_player = max(player_stats.items(), key=lambda x: x[1]['points'])
                return {
                    'name': top_player[0],
                    'points': top_player[1]['points'],
                    'team': top_player[1]['team']
                }
    except:
        pass
    
    return {'name': None, 'points': 0, 'team': None}


def validate_season_archive(zip_filepath):
    """
    Validate that a zip file contains expected season data structure.
    
    Parameters:
    zip_filepath (str): Path to the zip file
    
    Returns:
    dict: Validation result with success status and details
    """
    result = {
        'valid': False,
        'season_id': None,
        'files_found': [],
        'errors': []
    }
    
    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zip_file:
            file_list = zip_file.namelist()
            result['files_found'] = file_list
            
            # Check for required files/directories
            has_csv = any(f.endswith('.csv') for f in file_list)
            has_game_data = any('game-schedule-raw' in f or 'full-game-stats-raw' in f for f in file_list)
            has_json_db = any(f.endswith('DB.json') for f in file_list)
            
            if has_csv or has_game_data or has_json_db:
                result['valid'] = True
                
                # Try to extract season ID from filename
                filename = os.path.basename(zip_filepath)
                if 'raw-data-' in filename:
                    parts = filename.replace('raw-data-', '').replace('.zip', '').split('-')
                    if len(parts) >= 2:
                        # Assume format: raw-data-YYYY-YYYY-TIMESTAMP.zip
                        if parts[0].isdigit() and parts[1].isdigit():
                            result['season_id'] = f"{parts[0]}-{parts[1]}"
                        # Or format: raw-data-TIMESTAMP.zip (no season)
                        elif len(parts) == 1 and parts[0].isdigit():
                            result['season_id'] = 'unknown'
            else:
                result['errors'].append("Archive does not contain expected data files")
                
    except zipfile.BadZipFile:
        result['errors'].append("Invalid zip file")
    except Exception as e:
        result['errors'].append(f"Error reading zip file: {str(e)}")
    
    return result


def import_season_archive(zip_filepath, target_season_dir=None):
    """
    Import data from a season archive zip file.
    
    Parameters:
    zip_filepath (str): Path to the season archive zip file
    target_season_dir (str): Directory to extract to (optional)
    
    Returns:
    dict: Import result with success status and details
    """
    result = {
        'success': False,
        'imported_files': [],
        'season_id': None,
        'errors': []
    }
    
    # First validate the archive
    validation = validate_season_archive(zip_filepath)
    if not validation['valid']:
        result['errors'] = validation['errors']
        return result
    
    result['season_id'] = validation['season_id']
    
    try:
        # Create target directory if not specified
        if target_season_dir is None:
            season_id = validation['season_id'] or 'imported'
            target_season_dir = f"archive-{season_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        os.makedirs(target_season_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_filepath, 'r') as zip_file:
            # Extract all files to target directory
            zip_file.extractall(target_season_dir)
            result['imported_files'] = zip_file.namelist()
            result['success'] = True
            result['target_directory'] = target_season_dir
            
    except Exception as e:
        result['errors'].append(f"Error extracting archive: {str(e)}")
    
    return result


def list_available_archives(archive_dir='.'):
    """
    List available season archive files in a directory.
    
    Parameters:
    archive_dir (str): Directory to search for archives
    
    Returns:
    list: List of archive information dictionaries
    """
    archives = []
    
    try:
        for filename in os.listdir(archive_dir):
            if filename.startswith('raw-data-') and filename.endswith('.zip'):
                filepath = os.path.join(archive_dir, filename)
                validation = validate_season_archive(filepath)
                
                archive_info = {
                    'filename': filename,
                    'filepath': filepath,
                    'valid': validation['valid'],
                    'season_id': validation['season_id'],
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                }
                
                archives.append(archive_info)
                
    except OSError:
        pass
    
    # Sort by modification time (newest first)
    archives.sort(key=lambda x: x['modified'], reverse=True)
    return archives


def get_website_config():
    """
    Get website configuration including title and description.
    
    Returns:
    dict: Website configuration
    """
    config = load_config()
    website_config = config.get('website', {})
    season_info = get_season_info()
    
    # Add season information to website config
    return {
        'title': website_config.get('title', 'FLBB Basketball Statistics'),
        'description': website_config.get('description', 'Basketball statistics for Luxembourg Basketball Federation'),
        'season_display': season_info['season_display'],
        'season_full_name': season_info['full_name'],
        'features': website_config.get('features', {})
    }

def get_all_players_list(data):
    """
    Get a list of all unique players with their teams for autocomplete/search.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    list: List of dictionaries with player names and teams
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return []
    
    # Group by player name and team to get unique combinations
    unique_players = player_stats.groupby(['PlayerName', 'Team']).size().reset_index(name='Games')
    
    # Sort by player name
    unique_players = unique_players.sort_values('PlayerName')
    
    # Convert to list of dictionaries
    players_list = unique_players.to_dict('records')
    
    return players_list

def get_all_referees_list(data):
    """
    Get a list of all unique referees for autocomplete/search.
    
    This function extracts referee names from game data and returns them
    sorted alphabetically for use in search autocomplete functionality.
    
    Parameters:
    data (DataFrame): The game data containing referee information
    
    Returns:
    list: List of unique referee names sorted alphabetically, or empty list if no data
    
    Note:
    Depends on extract_referee_stats() which parses referee data from the 
    'Referres' column in the game data DataFrame.
    """
    ref_stats = extract_referee_stats(data)
    
    if ref_stats.empty:
        return []
    
    # Get unique referee names and sort
    unique_referees = sorted(ref_stats['RefereeName'].unique())
    
    return unique_referees

def get_all_games_list(data):
    """
    Get a list of all games with key information for autocomplete/search.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    list: List of dictionaries with game details for search
    """
    if data.empty:
        return []
    
    # Select relevant columns and create game list
    games_list = []
    
    for idx, row in data.iterrows():
        game_info = {
            'GameId': row.get('GameId', ''),
            'HomeTeam': row.get('HomeTeamName', ''),
            'AwayTeam': row.get('AwayTeamName', ''),
            'FinalScore': f"{row.get('FinalHomeScore', 0)}-{row.get('FinalAwayScore', 0)}",
            'Division': row.get('GameDivisionDisplay', ''),
            'Date': row.get('DateTime', ''),
            'Location': row.get('GameLocation', '')
        }
        games_list.append(game_info)
    
    # Sort by date (most recent first) if date is available
    if games_list and 'Date' in games_list[0] and games_list[0]['Date']:
        games_list = sorted(games_list, key=lambda x: x.get('Date', ''), reverse=True)
    
    return games_list

def get_player_detail_stats(data, player_name):
    """
    Get comprehensive statistics for a specific player.
    
    Parameters:
    data (DataFrame): The game data
    player_name (str): The name of the player
    
    Returns:
    dict: Comprehensive player statistics including:
        - basic_stats: Overall statistics
        - game_by_game: Detailed game-by-game performance
        - quarter_analysis: Statistics distributed over quarters
        - foul_breakdown: Detailed foul statistics by type
        - starting_five_stats: Starting vs bench statistics
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return None
    
    # Filter for the specific player
    player_games = player_stats[player_stats['PlayerName'] == player_name].copy()
    
    if player_games.empty:
        return None
    
    # Get most used player number
    player_number_mode = player_games['PlayerNumber'].mode()
    if not player_number_mode.empty:
        player_number = player_number_mode[0]
    elif len(player_games) > 0:
        player_number = player_games['PlayerNumber'].iloc[0]
    else:
        player_number = 0
    
    # Convert to int, handling NaN values
    try:
        if pd.isna(player_number):
            player_number = 0
        else:
            player_number = int(player_number)
    except (ValueError, TypeError):
        player_number = 0
    
    # Basic aggregated statistics
    basic_stats = {
        'player_name': player_name,
        'team': player_games['Team'].mode()[0] if not player_games['Team'].mode().empty else player_games['Team'].iloc[0],
        'player_number': player_number,
        'games_played': len(player_games),
        'total_points': int(player_games['TotalPoints'].sum()),
        'avg_points_per_game': round(player_games['TotalPoints'].mean(), 1),
        'max_points_game': int(player_games['TotalPoints'].max()),
        'min_points_game': int(player_games['TotalPoints'].min()),
        'total_1p_made': int(player_games['1PMadeShots'].sum()),
        'total_2p_made': int(player_games['2PMadeShots'].sum()),
        'total_3p_made': int(player_games['3PMadeShots'].sum()),
        'total_field_goals': int(player_games['1PMadeShots'].sum() + player_games['2PMadeShots'].sum() + player_games['3PMadeShots'].sum()),
        'total_fouls': int(player_games['TotalFouls'].sum()),
        'avg_fouls_per_game': round(player_games['TotalFouls'].mean(), 1),
        'p_fouls': int(player_games['PFouls'].sum()),
        'p1_fouls': int(player_games['P1Fouls'].sum()),
        'p2_fouls': int(player_games['P2Fouls'].sum()),
        'p3_fouls': int(player_games['P3Fouls'].sum()),
        't1_fouls': int(player_games['T1Fouls'].sum()),
        'u1_fouls': int(player_games['U1Fouls'].sum()),
        'u2_fouls': int(player_games['U2Fouls'].sum()),
        'u3_fouls': int(player_games['U3Fouls'].sum()),
        'gd_fouls': int(player_games['GDFouls'].sum()),
        'starting_five_games': int(player_games['StartingFive'].sum()),
        'bench_games': int((~player_games['StartingFive']).sum()),
    }
    
    # Calculate shooting percentages
    if basic_stats['starting_five_games'] > 0:
        starting_games = player_games[player_games['StartingFive']]
        if not starting_games.empty:
            basic_stats['avg_points_as_starter'] = round(starting_games['TotalPoints'].mean(), 1)
        else:
            basic_stats['avg_points_as_starter'] = 0
    else:
        basic_stats['avg_points_as_starter'] = 0
        
    if basic_stats['bench_games'] > 0:
        bench_games = player_games[~player_games['StartingFive']]
        if not bench_games.empty:
            basic_stats['avg_points_from_bench'] = round(bench_games['TotalPoints'].mean(), 1)
        else:
            basic_stats['avg_points_from_bench'] = 0
    else:
        basic_stats['avg_points_from_bench'] = 0
    
    # Game-by-game breakdown (sorted by date, most recent first)
    game_by_game = player_games.sort_values('GameDate', ascending=False).to_dict('records')
    
    # Add hotness score to each game
    for game_record in game_by_game:
        game_id = game_record['GameId']
        game_row = data[data['GameId'] == game_id]
        if not game_row.empty:
            game = game_row.iloc[0]
            # Calculate hotness score for this game
            try:
                import ast
                events = ast.literal_eval(game['GameEvents']) if isinstance(game['GameEvents'], str) else game['GameEvents']
                teams = ast.literal_eval(game['Teams']) if isinstance(game['Teams'], str) else game['Teams']
                score_evolution = _calculate_score_evolution(events, game['HomeTeamName'], game['AwayTeamName'], teams)
                game_stats = _calculate_game_statistics(score_evolution)
                hotness_score = calculate_hotness_score(game_stats['lead_changes'], game_stats['tied_scores'], game_stats.get('close_game_ratio'))
                hotness_icon = get_hotness_icon(hotness_score)
                game_record['HotnessScore'] = hotness_score
                game_record['HotnessIcon'] = hotness_icon
            except (ValueError, KeyError, TypeError, AttributeError) as e:
                # If hotness calculation fails, default to cold game
                game_record['HotnessScore'] = 0
                game_record['HotnessIcon'] = "❄️"
    
    # Get quarter-by-quarter analysis from game events
    quarter_analysis = _analyze_player_quarters(data, player_name)
    
    return {
        'basic_stats': basic_stats,
        'game_by_game': game_by_game,
        'quarter_analysis': quarter_analysis
    }

def _analyze_player_quarters(data, player_name):
    """
    Analyze player performance by quarter from game events.
    
    Parameters:
    data (DataFrame): The game data
    player_name (str): The name of the player
    
    Returns:
    dict: Quarter-by-quarter statistics
    """
    import ast
    
    quarter_stats = {
        1: {'points': 0, 'fouls': 0, 'events': 0},
        2: {'points': 0, 'fouls': 0, 'events': 0},
        3: {'points': 0, 'fouls': 0, 'events': 0},
        4: {'points': 0, 'fouls': 0, 'events': 0},
    }
    
    for _, game in data.iterrows():
        try:
            # Parse game events
            if isinstance(game['GameEvents'], str):
                events = ast.literal_eval(game['GameEvents'])
            else:
                events = game['GameEvents']
            
            if not isinstance(events, list):
                continue
            
            # Process each event for this player
            for event in events:
                if not isinstance(event, dict):
                    continue
                
                event_actor = event.get('EventActor', '')
                if event_actor != player_name:
                    continue
                
                quarter = event.get('EventQuarter', 0)
                if quarter not in quarter_stats:
                    continue
                
                quarter_stats[quarter]['events'] += 1
                
                # Check event action
                event_action = event.get('EventAction', '')
                if 'Points Added' in event_action:
                    # Extract points from action (1P, 2P, 3P)
                    if '1P' in event_action:
                        quarter_stats[quarter]['points'] += 1
                    elif '2P' in event_action:
                        quarter_stats[quarter]['points'] += 2
                    elif '3P' in event_action:
                        quarter_stats[quarter]['points'] += 3
                
                if 'Foul' in event_action:
                    quarter_stats[quarter]['fouls'] += 1
        
        except Exception as e:
            # Skip games with parsing errors
            continue
    
    return quarter_stats


def _extract_team_player_stats(team_games, team_name):
    """
    Extract comprehensive player statistics for a team from their games.
    
    Parameters:
    team_games (DataFrame): Games filtered for the team
    team_name (str): Name of the team
    
    Returns:
    dict: Dictionary containing:
        - all_players: List of all players with comprehensive stats
        - quarter_by_quarter: Quarter-by-quarter breakdown for each player
        - performance_evolution: Last 5 games performance for each player
    """
    import ast
    from collections import defaultdict
    
    # Initialize data structures
    player_totals = defaultdict(lambda: {
        'name': '',
        'number': 0,
        'games_played': 0,
        'total_points': 0,
        'total_fouls': 0,
        'total_2p': 0,
        'total_3p': 0,
        'total_1p': 0,
        'starting_five_count': 0,
        'quarters': defaultdict(lambda: {'points': 0, 'fouls': 0, 'games': 0}),
        'last_5_games': []
    })
    
    # Process each game
    for _, game in team_games.iterrows():
        try:
            # Parse the Teams data
            teams_data = ast.literal_eval(game['Teams']) if isinstance(game['Teams'], str) else game['Teams']
            
            # Find the team's data (home or away)
            team_data = None
            is_home = game['HomeTeamName'] == team_name
            
            for team in teams_data:
                if (is_home and team.get('Team Role') == 'Home') or \
                   (not is_home and team.get('Team Role') == 'Away'):
                    team_data = team
                    break
            
            if not team_data or 'Players' not in team_data:
                continue
            
            # Parse game events for quarter-by-quarter data
            game_events = ast.literal_eval(game['GameEvents']) if isinstance(game['GameEvents'], str) else game['GameEvents']
            
            # Process each player
            for player in team_data['Players']:
                player_name = player.get('Player Name', '')
                player_number = player.get('Player Number', 0)
                
                if not player_name:
                    continue
                
                # Use player name as key
                key = player_name
                
                # Update basic stats
                player_totals[key]['name'] = player_name
                player_totals[key]['number'] = player_number
                player_totals[key]['games_played'] += 1
                player_totals[key]['total_points'] += player.get('Total Points', 0)
                player_totals[key]['total_fouls'] += player.get('Total Fouls', 0)
                player_totals[key]['total_2p'] += player.get('2P Made Shots', 0)
                player_totals[key]['total_3p'] += player.get('3P Made Shots', 0)
                player_totals[key]['total_1p'] += player.get('1P Made Shots', 0)
                
                if player.get('Starting Five') == 'true':
                    player_totals[key]['starting_five_count'] += 1
                
                # Calculate quarter-by-quarter stats from game events
                quarter_stats = defaultdict(lambda: {'points': 0, 'fouls': 0})
                
                for event in game_events:
                    if event.get('EventActor') == player_name and event.get('EventTeam') == team_data.get('Team Name Short'):
                        quarter = event.get('EventQuarter')
                        action = event.get('EventAction', '')
                        
                        # Count points
                        if 'Points Added' in action:
                            if '1P' in action:
                                quarter_stats[quarter]['points'] += 1
                            elif '2P' in action:
                                quarter_stats[quarter]['points'] += 2
                            elif '3P' in action:
                                quarter_stats[quarter]['points'] += 3
                        
                        # Count fouls
                        if 'Foul Added' in action:
                            quarter_stats[quarter]['fouls'] += 1
                
                # Update quarter totals
                for quarter in [1, 2, 3, 4]:
                    if quarter in quarter_stats:
                        player_totals[key]['quarters'][quarter]['points'] += quarter_stats[quarter]['points']
                        player_totals[key]['quarters'][quarter]['fouls'] += quarter_stats[quarter]['fouls']
                        player_totals[key]['quarters'][quarter]['games'] += 1
                
                # Add to last 5 games data
                game_data = {
                    'game_id': game['GameId'],
                    'date': game['DateTime'][:10] if game['DateTime'] else 'N/A',
                    'opponent': game['AwayTeamName'] if is_home else game['HomeTeamName'],
                    'points': player.get('Total Points', 0),
                    'fouls': player.get('Total Fouls', 0),
                    'quarters': dict(quarter_stats)
                }
                player_totals[key]['last_5_games'].append(game_data)
                
        except (ValueError, KeyError, TypeError) as e:
            # Skip games with parsing errors (malformed JSON, missing keys, type issues)
            continue
    
    # Convert to final format
    all_players = []
    for player_key, stats in player_totals.items():
        # Keep only last 5 games
        stats['last_5_games'] = sorted(stats['last_5_games'], 
                                       key=lambda x: x['date'], 
                                       reverse=True)[:5]
        
        # Calculate averages
        games = stats['games_played']
        player_dict = {
            'name': stats['name'],
            'number': stats['number'],
            'games_played': games,
            'total_points': stats['total_points'],
            'total_fouls': stats['total_fouls'],
            'avg_points': round(stats['total_points'] / games, 1) if games > 0 else 0,
            'avg_fouls': round(stats['total_fouls'] / games, 1) if games > 0 else 0,
            'total_2p': stats['total_2p'],
            'total_3p': stats['total_3p'],
            'total_1p': stats['total_1p'],
            'starting_percentage': round(stats['starting_five_count'] / games * 100, 1) if games > 0 else 0,
            'quarters': dict(stats['quarters']),
            'last_5_games': stats['last_5_games']
        }
        all_players.append(player_dict)
    
    # Sort by total points descending
    all_players.sort(key=lambda x: x['total_points'], reverse=True)
    
    # Create quarter-by-quarter summary
    quarter_by_quarter = []
    for player in all_players:
        quarters_data = []
        for q in [1, 2, 3, 4]:
            quarter_info = player['quarters'].get(q, {'points': 0, 'fouls': 0, 'games': 0})
            games = quarter_info.get('games', 0)
            quarters_data.append({
                'quarter': q,
                'total_points': quarter_info.get('points', 0),
                'total_fouls': quarter_info.get('fouls', 0),
                'avg_points': round(quarter_info.get('points', 0) / games, 1) if games > 0 else 0,
                'avg_fouls': round(quarter_info.get('fouls', 0) / games, 1) if games > 0 else 0
            })
        
        quarter_by_quarter.append({
            'name': player['name'],
            'number': player['number'],
            'quarters': quarters_data
        })
    
    return {
        'all_players': all_players,
        'quarter_by_quarter': quarter_by_quarter,
        'has_data': len(all_players) > 0
    }


def get_team_detail_stats(data, team_name):
    """
    Get comprehensive statistics for a specific team.
    
    Parameters:
    data (DataFrame): The game data
    team_name (str): The name of the team
    
    Returns:
    dict: Comprehensive team statistics including:
        - basic_stats: Overall team statistics
        - game_by_game: Detailed game-by-game performance
        - performance_evolution: Time series of scores and allowed points
    """
    if data.empty:
        return None
    
    # Filter games for this team
    team_games = data[
        (data['HomeTeamName'] == team_name) | 
        (data['AwayTeamName'] == team_name)
    ].copy()
    
    if team_games.empty:
        return None
    
    # Sort by date
    team_games = team_games.sort_values('DateTime')
    
    # Process each game
    team_games['IsHome'] = team_games['HomeTeamName'] == team_name
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
    
    # Calculate basic statistics
    wins = len(team_games[team_games['Result'] == 'W'])
    losses = len(team_games[team_games['Result'] == 'L'])
    total_games = len(team_games)
    
    basic_stats = {
        'team_name': team_name,
        'total_games': total_games,
        'wins': wins,
        'losses': losses,
        'win_percentage': round((wins / total_games * 100), 1) if total_games > 0 else 0,
        'avg_points_scored': round(team_games['TeamScore'].mean(), 1),
        'avg_points_allowed': round(team_games['OpponentScore'].mean(), 1),
        'point_differential': round(team_games['Margin'].mean(), 1),
        'highest_score': int(team_games['TeamScore'].max()),
        'lowest_score': int(team_games['TeamScore'].min()),
        'biggest_win': int(team_games['Margin'].max()),
        'worst_loss': int(team_games['Margin'].min()),
        'home_games': int(team_games['IsHome'].sum()),
        'away_games': int((~team_games['IsHome']).sum()),
    }
    
    # Home/away split
    home_games = team_games[team_games['IsHome']]
    away_games = team_games[~team_games['IsHome']]
    
    if not home_games.empty:
        home_wins = len(home_games[home_games['Result'] == 'W'])
        basic_stats['home_win_percentage'] = round((home_wins / len(home_games) * 100), 1)
        basic_stats['avg_home_scored'] = round(home_games['TeamScore'].mean(), 1)
    else:
        basic_stats['home_win_percentage'] = 0
        basic_stats['avg_home_scored'] = 0
    
    if not away_games.empty:
        away_wins = len(away_games[away_games['Result'] == 'W'])
        basic_stats['away_win_percentage'] = round((away_wins / len(away_games) * 100), 1)
        basic_stats['avg_away_scored'] = round(away_games['TeamScore'].mean(), 1)
    else:
        basic_stats['away_win_percentage'] = 0
        basic_stats['avg_away_scored'] = 0
    
    # Performance evolution data (for charts)
    performance_evolution = []
    cumulative_scored = 0
    cumulative_allowed = 0
    
    for idx, (_, row) in enumerate(team_games.iterrows(), 1):
        cumulative_scored += int(row['TeamScore'])
        cumulative_allowed += int(row['OpponentScore'])
        performance_evolution.append({
            'game_number': idx,
            'date': row['DateTime'][:10] if row['DateTime'] else 'N/A',
            'scored': int(row['TeamScore']),
            'allowed': int(row['OpponentScore']),
            'margin': int(row['Margin']),
            'cumulative_scored': cumulative_scored,
            'cumulative_allowed': cumulative_allowed,
        })
    
    # Game by game data with hotness calculation
    game_by_game = []
    for _, row in team_games.iterrows():
        game_dict = row.to_dict()
        
        # Calculate hotness for finished games
        hotness_score = 0
        hotness_icon = "❄️"
        if pd.notna(row['TeamScore']) and pd.notna(row['OpponentScore']):
            try:
                import ast
                events = ast.literal_eval(row['GameEvents']) if isinstance(row['GameEvents'], str) else row['GameEvents']
                teams = ast.literal_eval(row['Teams']) if isinstance(row['Teams'], str) else row['Teams']
                score_evolution = _calculate_score_evolution(events, row['HomeTeamName'], row['AwayTeamName'], teams)
                game_stats = _calculate_game_statistics(score_evolution)
                hotness_score = calculate_hotness_score(game_stats['lead_changes'], game_stats['tied_scores'], game_stats.get('close_game_ratio'))
                hotness_icon = get_hotness_icon(hotness_score)
            except:
                pass
        
        game_dict['HotnessScore'] = hotness_score
        game_dict['HotnessIcon'] = hotness_icon
        game_by_game.append(game_dict)
    
    # Extract player statistics for this team
    player_stats = _extract_team_player_stats(team_games, team_name)
    
    return {
        'basic_stats': basic_stats,
        'game_by_game': game_by_game,
        'performance_evolution': performance_evolution,
        'player_stats': player_stats
    }


def get_game_details(data, game_id):
    """
    Get comprehensive details for a specific game.
    
    Parameters:
    data (DataFrame): The game data
    game_id (str or int): The game ID to retrieve details for
    
    Returns:
    dict: Dictionary containing all game details including:
        - basic_info: Game metadata (location, date, division, etc.)
        - teams: Team information and player statistics
        - events: Timeline of game events
        - score_evolution: Score progression throughout the game
        - referees: Referee information
    """
    import ast
    
    # Convert game_id to string for comparison
    game_id = str(game_id)
    
    # Find the game
    game_row = data[data['GameId'].astype(str) == game_id]
    
    if game_row.empty:
        return None
    
    game = game_row.iloc[0]
    
    # Parse complex fields
    try:
        teams = ast.literal_eval(game['Teams']) if isinstance(game['Teams'], str) else game['Teams']
    except:
        teams = []
    
    try:
        events = ast.literal_eval(game['GameEvents']) if isinstance(game['GameEvents'], str) else game['GameEvents']
    except:
        events = []
    
    try:
        referees = ast.literal_eval(game['Referres']) if isinstance(game['Referres'], str) else game['Referres']
    except:
        referees = []
    
    try:
        location = ast.literal_eval(game['GameLocation']) if isinstance(game['GameLocation'], str) else game['GameLocation']
    except:
        location = {}
    
    # Build basic info
    basic_info = {
        'game_id': game_id,
        'location': location,
        'division': game['GameDivisionDisplay'],
        'date_time': game['DateTime'],
        'home_team': game['HomeTeamName'],
        'away_team': game['AwayTeamName'],
        'final_score': game['GameFinalScore'],
        'home_score': game['FinalHomeScore'],
        'away_score': game['FinalAwayScore'],
        'winner': game['GameWinner'],
        'loser': game['GameLoser'],
        'home_league_points': game.get('HomeTeamLeaguePoints', 0),
        'away_league_points': game.get('AwayTeamLeaguePoints', 0)
    }
    
    # Calculate score evolution from events
    score_evolution = _calculate_score_evolution(events, game['HomeTeamName'], game['AwayTeamName'], teams)
    
    # Calculate advanced game statistics
    game_stats = _calculate_game_statistics(score_evolution)
    
    # Calculate hotness score
    hotness_score = calculate_hotness_score(game_stats['lead_changes'], game_stats['tied_scores'], game_stats.get('close_game_ratio'))
    hotness_icon = get_hotness_icon(hotness_score)
    game_stats['hotness_score'] = hotness_score
    game_stats['hotness_icon'] = hotness_icon
    
    # Calculate timeout and coach information from events
    team_timeouts = {}
    team_coaches = {}
    for event in events:
        if event.get('EventAction', '').lower() == 'timeout':
            team_name = event.get('EventTeam', '')
            if team_name:
                team_timeouts[team_name] = team_timeouts.get(team_name, 0) + 1
                # Try to get coach name from the event actor
                actor = event.get('EventActor', '')
                if actor and actor != '* Coach *' and team_name not in team_coaches:
                    team_coaches[team_name] = actor
    
    # Process teams and players
    teams_data = []
    for team in teams:
        team_name = team.get('Team Name', '')
        team_name_short = team.get('Team Name Short', '')
        
        # Calculate totals for player statistics
        players = team.get('Players', [])
        total_points = sum(int(p.get('Total Points', 0)) for p in players)
        total_1p = sum(int(p.get('1P Made Shots', 0)) for p in players)
        total_2p = sum(int(p.get('2P Made Shots', 0)) for p in players)
        total_3p = sum(int(p.get('3P Made Shots', 0)) for p in players)
        total_fouls = sum(int(p.get('Total Fouls', 0)) for p in players)
        
        # Match timeouts and coach by either full name or short name
        timeouts = team_timeouts.get(team_name, 0) or team_timeouts.get(team_name_short, 0)
        coach = team_coaches.get(team_name, team_coaches.get(team_name_short, 'N/A'))
        
        team_info = {
            'name': team_name,
            'name_short': team_name_short,
            'role': team.get('Team Role', ''),
            'result': team.get('Result Outcome', ''),
            'league_points': team.get('League Points', 0),
            'total_won_points': team.get('Total Won Points', 0),
            'total_lost_points': team.get('Total Lost Points', 0),
            'players': players,
            'coach': coach,
            'timeouts_used': timeouts,
            'totals': {
                'points': total_points,
                '1p': total_1p,
                '2p': total_2p,
                '3p': total_3p,
                'fouls': total_fouls
            }
        }
        teams_data.append(team_info)
    
    # Sort events by time (most recent first for display, but we'll reverse for chronological)
    sorted_events = sorted(events, key=lambda x: x.get('EventDateTime', ''), reverse=False)
    
    return {
        'basic_info': basic_info,
        'teams': teams_data,
        'events': sorted_events,
        'score_evolution': score_evolution,
        'game_stats': game_stats,
        'referees': referees
    }


def _calculate_score_evolution(events, home_team, away_team, teams=None):
    """
    Calculate score evolution throughout the game from events.
    
    Parameters:
    events (list): List of game events
    home_team (str): Home team name
    away_team (str): Away team name
    teams (list): List of team objects with Team Name and Team Name Short
    
    Returns:
    list: List of score points with quarters, scores, foul counts, timeouts, and elapsed time
    """
    from datetime import datetime
    
    score_points = []
    home_fouls = 0
    away_fouls = 0
    last_home_score = 0
    last_away_score = 0
    last_quarter = 1
    
    # Extract team short names for matching event teams
    home_team_short = home_team
    away_team_short = away_team
    
    if teams:
        for team in teams:
            if team.get('Team Name') == home_team:
                home_team_short = team.get('Team Name Short', home_team)
            elif team.get('Team Name') == away_team:
                away_team_short = team.get('Team Name Short', away_team)
    
    # Sort events chronologically
    sorted_events = sorted(events, key=lambda x: x.get('EventDateTime', ''))
    
    # Find the first event time to calculate elapsed time
    first_event_time = None
    for event in sorted_events:
        if event.get('EventDateTime'):
            try:
                first_event_time = datetime.fromisoformat(event.get('EventDateTime', '').replace('Z', '+00:00'))
                break
            except:
                pass
    
    for event in sorted_events:
        # Track fouls
        event_action = event.get('EventAction', '').lower()
        event_team = event.get('EventTeam', '')
        
        # Helper function to check if event belongs to a team
        def is_team_event(team_full, team_short):
            return event_team == team_full or event_team == team_short
        
        # Check if this is a foul event (but not a foul deletion)
        is_foul_added = any(keyword in event_action for keyword in ['foul added', 'faute'])
        is_foul_deleted = 'foul deleted' in event_action
        
        if is_foul_added and not is_foul_deleted:
            if is_team_event(home_team, home_team_short):
                home_fouls += 1
            elif is_team_event(away_team, away_team_short):
                away_fouls += 1
        elif is_foul_deleted:
            # Handle foul deletions by decrementing
            if is_team_event(home_team, home_team_short) and home_fouls > 0:
                home_fouls -= 1
            elif is_team_event(away_team, away_team_short) and away_fouls > 0:
                away_fouls -= 1
        
        # Calculate elapsed time in seconds from first event
        elapsed_seconds = 0
        if first_event_time and event.get('EventDateTime'):
            try:
                event_time = datetime.fromisoformat(event.get('EventDateTime', '').replace('Z', '+00:00'))
                elapsed_seconds = (event_time - first_event_time).total_seconds()
            except (ValueError, TypeError, AttributeError):
                pass
        
        # Check for timeout event
        is_timeout = 'timeout' in event_action
        
        # Track score changes
        if event.get('EventScore'):
            score_str = event.get('EventScore', '')
            quarter = event.get('EventQuarter', 0)
            
            # Parse score "X : Y"
            if ':' in score_str:
                try:
                    parts = score_str.split(':')
                    home_score = int(parts[0].strip())
                    away_score = int(parts[1].strip())
                    last_home_score = home_score
                    last_away_score = away_score
                    last_quarter = quarter
                    
                    score_points.append({
                        'quarter': quarter,
                        'home_score': home_score,
                        'away_score': away_score,
                        'home_fouls': home_fouls,
                        'away_fouls': away_fouls,
                        'time': event.get('EventDateTime', ''),
                        'elapsed_seconds': elapsed_seconds,
                        'event': event.get('EventAction', ''),
                        'is_timeout': False
                    })
                except:
                    pass
        elif is_timeout:
            # Add timeout marker with last known score
            score_points.append({
                'quarter': event.get('EventQuarter', last_quarter),
                'home_score': last_home_score,
                'away_score': last_away_score,
                'home_fouls': home_fouls,
                'away_fouls': away_fouls,
                'time': event.get('EventDateTime', ''),
                'elapsed_seconds': elapsed_seconds,
                'event': event.get('EventAction', ''),
                'is_timeout': True,
                'timeout_team': event_team
            })
    
    return score_points


def _calculate_game_statistics(score_evolution):
    """
    Calculate advanced game statistics from score evolution.
    
    Parameters:
    score_evolution (list): List of score points throughout the game
    
    Returns:
    dict: Dictionary containing:
        - tied_scores: Number of times the score was tied
        - lead_changes: Number of times the lead changed
        - home_highest_lead: Highest lead for home team (or None if never led)
        - away_highest_lead: Highest lead for away team (or None if never led)
        - close_game_ratio: Ratio of game time where score difference <= 5 points
        - total_game_time: Total game duration in seconds
    """
    if not score_evolution:
        return {
            'tied_scores': 0,
            'lead_changes': 0,
            'home_highest_lead': None,
            'away_highest_lead': None,
            'close_game_ratio': 0.0,
            'total_game_time': 0
        }
    
    tied_scores = 0
    lead_changes = 0
    home_highest_lead = 0
    away_highest_lead = 0
    previous_leader = None  # 'home' or 'away' (ties are skipped)
    
    # For close game ratio calculation
    close_game_time = 0.0
    previous_elapsed_seconds = 0
    previous_margin = None
    
    for i, point in enumerate(score_evolution):
        home_score = point['home_score']
        away_score = point['away_score']
        margin = abs(home_score - away_score)
        elapsed_seconds = point.get('elapsed_seconds', 0)
        
        # Calculate time-weighted closeness (score difference <= 5 points)
        # We use previous_margin because between events, the score was at the previous state
        if i > 0 and previous_margin is not None:
            time_delta = elapsed_seconds - previous_elapsed_seconds
            if time_delta > 0 and previous_margin <= 5:
                close_game_time += time_delta
        
        previous_elapsed_seconds = elapsed_seconds
        previous_margin = margin
        
        # Count tied scores
        if home_score == away_score:
            tied_scores += 1
            current_leader = 'tied'
        else:
            # Determine current leader
            if home_score > away_score:
                current_leader = 'home'
                lead = home_score - away_score
                home_highest_lead = max(home_highest_lead, lead)
            else:
                current_leader = 'away'
                lead = away_score - home_score
                away_highest_lead = max(away_highest_lead, lead)
            
            # Count lead changes (only when lead switches between teams, not including ties)
            if previous_leader is not None and current_leader != previous_leader:
                lead_changes += 1
            
            # Update previous_leader only for non-tied states
            previous_leader = current_leader
    
    # Calculate close game ratio
    total_game_time = previous_elapsed_seconds if previous_elapsed_seconds > 0 else 0
    close_game_ratio = close_game_time / total_game_time if total_game_time > 0 else 0.0
    
    # Return None for highest lead if team never led
    return {
        'tied_scores': tied_scores,
        'lead_changes': lead_changes,
        'home_highest_lead': home_highest_lead if home_highest_lead > 0 else None,
        'away_highest_lead': away_highest_lead if away_highest_lead > 0 else None,
        'close_game_ratio': close_game_ratio,
        'total_game_time': total_game_time
    }


def calculate_hotness_score(lead_changes, ties, close_game_ratio=None):
    """
    Calculate game hotness score using improved formula that combines game closeness and volatility.
    
    New Formula:
    - Closeness Factor: Percentage of game time where score difference <= 5 points
    - Volatility Factor: Normalized score from lead changes and ties
    - Combined: 0.7 * Closeness + 0.3 * Volatility, normalized to 0-100
    
    If close_game_ratio is not provided, falls back to old formula for backwards compatibility.
    
    Parameters:
    lead_changes (int): Number of lead changes in the game
    ties (int): Number of times the score was tied
    close_game_ratio (float, optional): Ratio of game time where score difference <= 5 (0.0 to 1.0)
    
    Returns:
    int: Hotness score between 0 and 100
    """
    # Backwards compatibility: if close_game_ratio is not provided, use old formula
    if close_game_ratio is None:
        return min(100, (lead_changes * 3 + ties * 2))
    
    # New improved formula
    # Step 1: Closeness factor (already 0-1 ratio)
    closeness_factor = close_game_ratio
    
    # Step 2: Volatility factor - normalize lead changes and ties
    # Typical competitive games have 5-15 lead changes and 3-10 ties
    # We'll normalize using reasonable upper bounds: 20 lead changes, 15 ties
    volatility_raw = (lead_changes * 3 + ties * 2)
    volatility_factor = min(1.0, volatility_raw / 75.0)  # 75 = (20*3 + 15*2) for normalization
    
    # Step 3: Combine with weights (70% closeness, 30% volatility)
    closeness_weight = 0.7
    volatility_weight = 0.3
    
    combined_score = (closeness_weight * closeness_factor + volatility_weight * volatility_factor)
    
    # Step 4: Scale to 0-100
    hotness_score = int(combined_score * 100)
    
    return min(100, max(0, hotness_score))


def get_hotness_icon(hotness_score):
    """
    Get the emoji icon(s) representing the game hotness.
    
    Ranges:
    0-20: ❄️ (Cold - snowflake)
    21-50: 🌡️ (Warm - thermometer)
    51-80: 🔥 (Hot - single flame)
    81-100: 🔥🔥 (Thriller - double flame)
    
    Parameters:
    hotness_score (int): The hotness score (0-100)
    
    Returns:
    str: Emoji icon(s) representing the hotness level
    """
    if hotness_score <= 20:
        return "❄️"
    elif hotness_score <= 50:
        return "🌡️"
    elif hotness_score <= 80:
        return "🔥"
    else:
        return "🔥🔥"


def get_player_hover_stats(data, player_name):
    """
    Get basic statistics for a player to display in hover tooltip.
    
    Parameters:
    data (DataFrame): The game data
    player_name (str): The name of the player
    
    Returns:
    dict: Dictionary containing:
        - games_played: Number of games
        - avg_score: Average points per game
        - fouls_per_game: Average fouls per game
        - best_score: Highest score in one game
        - team: Team name
        - player_number: Player's number
        - last_three_scores: List of scores from last 3 games
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return None
    
    # Filter for the specific player
    player_games = player_stats[player_stats['PlayerName'] == player_name].copy()
    
    if player_games.empty:
        return None
    
    # Sort by game date to get most recent games
    player_games = player_games.sort_values('GameDate')
    
    # Get team name (most recent team if player changed teams)
    team = player_games.iloc[-1]['Team']
    
    # Get player number (most recent number)
    player_number = player_games.iloc[-1]['PlayerNumber']
    
    # Get last 3 game scores
    last_three_scores = player_games.tail(3)['TotalPoints'].tolist()
    
    return {
        'games_played': int(len(player_games)),
        'avg_score': float(round(player_games['TotalPoints'].mean(), 1)),
        'fouls_per_game': float(round(player_games['TotalFouls'].mean(), 1)),
        'best_score': int(player_games['TotalPoints'].max()),
        'team': str(team),
        'player_number': int(player_number) if pd.notna(player_number) else None,
        'last_three_scores': [int(score) for score in last_three_scores]
    }


def get_team_hover_stats(data, team_name):
    """
    Get basic statistics for a team to display in hover tooltip.
    
    Parameters:
    data (DataFrame): The game data
    team_name (str): The name of the team
    
    Returns:
    dict: Dictionary containing:
        - wins: Number of wins
        - losses: Number of losses
        - last_five: List of results for last 5 games (W/L)
        - position: Current position in division standings
        - total_teams: Total number of teams in division
        - division: Division name
        - top_scorers: List of top 5 scorers ranked by total points (descending) with total_points and avg_points
    """
    if data.empty:
        return None
    
    # Filter games for this team
    team_games = data[
        (data['HomeTeamName'] == team_name) | 
        (data['AwayTeamName'] == team_name)
    ].copy()
    
    if team_games.empty:
        return None
    
    # Get division name from first game
    division = team_games.iloc[0]['GameDivisionDisplay']
    
    # Sort by date
    team_games = team_games.sort_values('DateTime')
    
    # Process each game
    team_games['IsHome'] = team_games['HomeTeamName'] == team_name
    team_games['TeamScore'] = team_games.apply(
        lambda row: row['FinalHomeScore'] if row['IsHome'] else row['FinalAwayScore'], 
        axis=1
    )
    team_games['OpponentScore'] = team_games.apply(
        lambda row: row['FinalAwayScore'] if row['IsHome'] else row['FinalHomeScore'], 
        axis=1
    )
    team_games['Result'] = team_games.apply(
        lambda row: 'W' if row['TeamScore'] > row['OpponentScore'] else 'L', 
        axis=1
    )
    
    # Calculate wins and losses
    wins = len(team_games[team_games['Result'] == 'W'])
    losses = len(team_games[team_games['Result'] == 'L'])
    
    # Get last 5 games
    last_five = team_games.tail(5)['Result'].tolist()
    
    # Calculate position in division standings
    position = None
    total_teams = None
    if division:
        standings = calculate_standings_by_division(data, division)
        if not standings.empty:
            total_teams = len(standings)
            team_row = standings[standings['Team Name'] == team_name]
            if not team_row.empty:
                # Get position (index starts at 1 in standings)
                position = team_row.index[0]
    
    # Get top 5 scorers for this team
    top_scorers = []
    player_stats = extract_all_player_stats(data)
    if not player_stats.empty:
        team_players = player_stats[player_stats['Team'] == team_name].copy()
        if not team_players.empty:
            # Group by player name and calculate total points and average points
            player_totals = team_players.groupby('PlayerName').agg({
                'TotalPoints': ['sum', 'mean'],
                'GameId': 'count'
            })
            # Flatten MultiIndex columns for better readability
            player_totals.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in player_totals.columns.values]
            player_totals = player_totals.rename(columns={
                'TotalPoints_sum': 'TotalPoints',
                'TotalPoints_mean': 'AvgPoints',
                'GameId_count': 'GamesPlayed'
            })
            
            # Sort by total points descending and get top 5
            player_totals = player_totals.sort_values('TotalPoints', ascending=False).head(5)
            
            for player_name, row in player_totals.iterrows():
                top_scorers.append({
                    'name': player_name,
                    'total_points': int(row['TotalPoints']),
                    'avg_points': round(row['AvgPoints'], 1)
                })
    
    return {
        'wins': int(wins) if wins is not None else 0,
        'losses': int(losses) if losses is not None else 0,
        'last_five': last_five,
        'position': int(position) if position is not None else None,
        'total_teams': int(total_teams) if total_teams is not None else None,
        'division': str(division) if division is not None else None,
        'top_scorers': top_scorers
    }


def get_referee_hover_stats(data, referee_name):
    """
    Get basic statistics for a referee to display in hover tooltip.
    
    Parameters:
    data (DataFrame): The game data
    referee_name (str): The name of the referee
    
    Returns:
    dict: Dictionary containing:
        - games: Number of games
        - fouls_per_game: Average fouls per game
    """
    import ast
    
    if data.empty:
        return None
    
    # Find games where this referee officiated
    referee_games = []
    for idx, row in data.iterrows():
        try:
            referees = ast.literal_eval(row['Referres']) if isinstance(row['Referres'], str) else row['Referres']
            # Check for both 'RefereeName' and 'Referee Name' keys
            if referees and any(
                ref.get('RefereeName') == referee_name or ref.get('Referee Name') == referee_name 
                for ref in referees
            ):
                referee_games.append(row)
        except:
            continue
    
    if not referee_games:
        return None
    
    # Extract total fouls for each game
    total_fouls = []
    for game_row in referee_games:
        try:
            teams = ast.literal_eval(game_row['Teams']) if isinstance(game_row['Teams'], str) else game_row['Teams']
            game_fouls = 0
            if isinstance(teams, list):
                for team in teams:
                    if isinstance(team, dict) and 'Players' in team:
                        players = team['Players']
                        if isinstance(players, list):
                            for player in players:
                                if isinstance(player, dict):
                                    # Try both key formats
                                    fouls = player.get('Total Fouls', player.get('TotalFouls', 0))
                                    game_fouls += fouls
            # Append fouls count including zero (legitimate no fouls game)
            total_fouls.append(game_fouls)
        except Exception as e:
            # Continue to next game if there's an error
            continue
    
    avg_fouls = round(sum(total_fouls) / len(total_fouls), 1) if total_fouls else 0
    
    return {
        'games': int(len(referee_games)),
        'fouls_per_game': float(avg_fouls)
    }


def get_game_hover_stats(data, game_id):
    """
    Get basic statistics for a game to display in hover tooltip.
    Supports both finished games and future games from gamesDB.json.
    
    Parameters:
    data (DataFrame): The game data
    game_id (str or int): The game ID
    
    Returns:
    dict: Dictionary containing:
        - result: Final score string or team names for future games
        - referees: List of referee names (empty for future games)
        - date_time: Game date and time
        - lead_changes: Number of lead changes (0 for future games)
        - ties: Number of times score was tied (0 for future games)
        - is_future: Boolean indicating if this is a future game
    """
    import ast
    
    # Convert game_id to string for comparison
    game_id = str(game_id)
    
    # First, try to find the game in finished games
    game_row = data[data['GameId'].astype(str) == game_id]
    
    if not game_row.empty:
        # Found in finished games - process normally
        game = game_row.iloc[0]
        
        # Parse referees
        try:
            referees = ast.literal_eval(game['Referres']) if isinstance(game['Referres'], str) else game['Referres']
            # Check for both key formats
            referee_names = [
                ref.get('RefereeName') or ref.get('Referee Name', 'Unknown') 
                for ref in referees
            ] if referees else []
        except:
            referee_names = []
        
        # Parse events for lead changes and ties
        try:
            events = ast.literal_eval(game['GameEvents']) if isinstance(game['GameEvents'], str) else game['GameEvents']
            teams = ast.literal_eval(game['Teams']) if isinstance(game['Teams'], str) else game['Teams']
            score_evolution = _calculate_score_evolution(events, game['HomeTeamName'], game['AwayTeamName'], teams)
            game_stats = _calculate_game_statistics(score_evolution)
            lead_changes = game_stats.get('lead_changes', 0)
            ties = game_stats.get('tied_scores', 0)
            close_game_ratio = game_stats.get('close_game_ratio')
            hotness_score = calculate_hotness_score(lead_changes, ties, close_game_ratio)
            hotness_icon = get_hotness_icon(hotness_score)
        except:
            lead_changes = 0
            ties = 0
            hotness_score = 0
            hotness_icon = "❄️"
        
        return {
            'result': f"{game['HomeTeamName']} {int(game['FinalHomeScore'])} - {int(game['FinalAwayScore'])} {game['AwayTeamName']}",
            'referees': referee_names,
            'date_time': game.get('DateTime', 'N/A'),
            'lead_changes': lead_changes,
            'ties': ties,
            'hotness_score': hotness_score,
            'hotness_icon': hotness_icon,
            'is_future': False
        }
    
    # Not found in finished games - check future games
    future_games = load_future_games_from_gamesdb()
    if future_games:
        for game in future_games:
            if str(game.get('GameId')) == game_id:
                # Found in future games
                from datetime import datetime
                
                home_team, away_team = parse_team_names_from_url(game.get('GameUrl', ''))
                
                # Parse the date from ScheduledGameDate and convert to ISO format
                game_date = 'TBD'
                if 'ScheduledGameDate' in game and isinstance(game['ScheduledGameDate'], dict):
                    date_str = game['ScheduledGameDate'].get('DateTime', 'TBD')
                    if date_str != 'TBD':
                        try:
                            # Parse and convert to ISO format to match finished games
                            dt = datetime.strptime(date_str, GAMESDB_DATE_FORMAT)
                            game_date = dt.strftime(ISO_DATE_FORMAT)
                        except ValueError:
                            # If parsing fails, keep the original
                            game_date = date_str
                
                # Get division name
                division = convert_division_name(game.get('GameDivisionName', ''))
                
                return {
                    'result': f"{home_team} vs {away_team}",
                    'referees': [],
                    'date_time': game_date,
                    'lead_changes': 0,
                    'ties': 0,
                    'hotness_score': 0,
                    'hotness_icon': "📅",
                    'is_future': True,
                    'division': division
                }
    
    # Game not found in either finished or future games
    return None
