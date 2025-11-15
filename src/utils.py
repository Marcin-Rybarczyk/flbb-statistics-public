import os
import pandas as pd
import json
from collections import defaultdict
import zipfile
import tempfile
from datetime import datetime
import html
import unicodedata


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
SCRIPTS_CONFIG_FILEPATH = "scripts/config.json"


def parse_dotnet_json_date(date_value):
    """
    Parse .NET JSON date format or dictionary format to ISO datetime string.
    
    Supports three formats:
    1. .NET JSON date: /Date(milliseconds)/ 
    2. Dictionary with DateTime key: {'DateTime': 'Saturday, November 8, 2025 12:00:00 AM'}
    3. ISO 8601 format: 2025-11-15T20:00:00
    
    Parameters:
    date_value: Either a string in .NET JSON format, ISO 8601 format, or a dictionary
    
    Returns:
    str: Date in ISO format (YYYY-MM-DD HH:MM:SS) or None if parsing fails
    """
    if not date_value:
        return None
        
    # Handle .NET JSON date format: /Date(milliseconds)/
    if isinstance(date_value, str) and date_value.startswith('/Date(') and date_value.endswith(')/'):
        try:
            # Extract milliseconds from /Date(1763235000000)/
            ms_str = date_value[6:-2]  # Remove '/Date(' and ')/'
            milliseconds = int(ms_str)
            # Convert milliseconds to datetime (Unix epoch is 1970-01-01)
            dt = datetime.fromtimestamp(milliseconds / 1000.0)
            # Convert to ISO format: "YYYY-MM-DD HH:MM:SS"
            return dt.strftime(ISO_DATE_FORMAT)
        except (ValueError, AttributeError, OverflowError):
            return None
    
    # Handle ISO 8601 format: 2025-11-15T20:00:00
    elif isinstance(date_value, str) and 'T' in date_value:
        try:
            # Try to parse ISO 8601 format with or without timezone
            # Common formats: "2025-11-15T20:00:00" or "2025-11-15T20:00:00Z"
            if date_value.endswith('Z'):
                dt = datetime.strptime(date_value, '%Y-%m-%dT%H:%M:%SZ')
            elif '+' in date_value or date_value.count('-') > 2:
                # Handle timezone offsets like "2025-11-15T20:00:00+01:00"
                # For simplicity, just parse the date/time part and ignore timezone
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            else:
                # Simple ISO format without timezone: "2025-11-15T20:00:00"
                dt = datetime.strptime(date_value, '%Y-%m-%dT%H:%M:%S')
            return dt.strftime(ISO_DATE_FORMAT)
        except (ValueError, AttributeError):
            return None
    
    # Handle dictionary format with DateTime key (legacy support)
    elif isinstance(date_value, dict):
        date_str = date_value.get('DateTime')
        if date_str:
            try:
                # Parse the date string like "Saturday, November 8, 2025 12:00:00 AM"
                dt = datetime.strptime(date_str, GAMESDB_DATE_FORMAT)
                return dt.strftime(ISO_DATE_FORMAT)
            except ValueError:
                return date_str  # Return original if parsing fails
    
    return None

# Data source configuration constants
DATA_SOURCE_CSV = 'csv'
DATA_SOURCE_MONGODB = 'mongodb'
DATA_SOURCE_AUTO = 'auto'
VALID_DATA_SOURCES = [DATA_SOURCE_CSV, DATA_SOURCE_MONGODB, DATA_SOURCE_AUTO]

# Global variables to track data source and last update
_data_source_info = {
    'source': 'unknown',  # 'new_data', 'backup_csv', 'mongodb', 'none'
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
    First tries data/config.json, then config.json, then scripts/config.json, then returns defaults.
    
    Returns:
    dict: Configuration dictionary
    """
    global _cached_config
    
    if _cached_config is not None:
        return _cached_config
    
    # Try config files in order: data/config.json, config.json, scripts/config.json
    for config_path in [CONFIG_FILEPATH, DEFAULT_CONFIG_FILEPATH, SCRIPTS_CONFIG_FILEPATH]:
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
    
    # Track game results for last 5 games calculation
    team_games = defaultdict(list)

    # Sort by DateTime to ensure games are processed in chronological order
    df_sorted = df.sort_values('DateTime') if 'DateTime' in df.columns else df

    for _, row in df_sorted.iterrows():
        home_team = row['HomeTeamName']
        away_team = row['AwayTeamName']
        home_score = row['FinalHomeScore']
        away_score = row['FinalAwayScore']
        game_id = row.get('GameId', '')

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
            # Track game result for last 5 games
            team_games[home_team].append({'result': 'W', 'game_id': game_id})
            team_games[away_team].append({'result': 'L', 'game_id': game_id})
        else:  # Away team wins
            standings[home_team]['L'] += 1
            standings[away_team]['W'] += 1
            standings[home_team]['Points'] += 1
            standings[away_team]['Points'] += 2
            # Track game result for last 5 games
            team_games[home_team].append({'result': 'L', 'game_id': game_id})
            team_games[away_team].append({'result': 'W', 'game_id': game_id})

    # Convert to a DataFrame
    standings_df = pd.DataFrame.from_dict(standings, orient='index').reset_index()
    standings_df.rename(columns={'index': 'Team Name'}, inplace=True)
    standings_df['Points Diff'] = standings_df['F'] - standings_df['A']
    
    # Add Last 5 Games column
    last_five_games = []
    for team_name in standings_df['Team Name']:
        games = team_games[team_name][-5:]  # Get last 5 games
        games = list(reversed(games))  # Reverse to show most recent first
        last_five_games.append(games)
    standings_df['Last 5 Games'] = last_five_games

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

def calculate_ft_stats_from_events(game_events):
    """
    Calculate free throw attempts and makes for each player based on game events.
    
    According to the requirements:
    - Any foul with FT (P1, P2, P3 fouls) is counted as number of attempts
    - Number of following 1P scores counts as successful attempts
    - Any other event occurring after 1P score ends the shot attempts
    - FT without defined shooter (all missed) are tracked separately
    
    Parameters:
    game_events: List of game events or string representation of list
    
    Returns:
    dict: Dictionary mapping player names to their FT stats
          {player_name: {'attempts': int, 'makes': int}}
          Special key 'TEAM_MISSED_FTS' for unattributed missed free throws
    """
    ft_stats = {}
    
    try:
        if isinstance(game_events, str):
            import ast
            events = ast.literal_eval(game_events)
        else:
            events = game_events
    except (ValueError, TypeError, SyntaxError):
        return ft_stats
    
    if not isinstance(events, list):
        return ft_stats
    
    i = 0
    while i < len(events):
        event = events[i]
        action = event.get('EventAction', '')
        
        # Check for shooting fouls (P1, P2, P3)
        if action in ['P1 Foul Added', 'P2 Foul Added', 'P3 Foul Added']:
            foul_team = event.get('EventTeam', '')
            
            # Determine number of FT attempts based on foul type
            if action == 'P1 Foul Added':
                expected_attempts = 1
            elif action == 'P2 Foul Added':
                expected_attempts = 2
            elif action == 'P3 Foul Added':
                expected_attempts = 3
            else:
                expected_attempts = 0
            
            # Look ahead for 1P points (opponent team gets FT)
            j = i + 1
            ft_shooter = None
            ft_makes = 0
            
            while j < len(events):
                next_event = events[j]
                next_action = next_event.get('EventAction', '')
                next_team = next_event.get('EventTeam', '')
                next_actor = next_event.get('EventActor', '')
                
                # 1P points by opponent team (the team that didn't commit the foul)
                if next_action == '1P Points Added' and next_team != foul_team:
                    if ft_shooter is None:
                        ft_shooter = next_actor
                    # Count makes only if same shooter
                    if next_actor == ft_shooter:
                        ft_makes += 1
                    j += 1
                # Skip some events that don't end FT sequence
                elif next_action in ['Player in', 'Player in deleted', '1P Points Deleted']:
                    j += 1
                else:
                    # Any other event ends the FT sequence
                    break
            
            # Record FT stats
            if expected_attempts > 0:
                if ft_shooter:
                    # Shooter identified - attribute to player
                    if ft_shooter not in ft_stats:
                        ft_stats[ft_shooter] = {'attempts': 0, 'makes': 0}
                    ft_stats[ft_shooter]['attempts'] += expected_attempts
                    # Cap makes at expected attempts (can't make more than you attempt)
                    ft_stats[ft_shooter]['makes'] += min(ft_makes, expected_attempts)
                elif ft_makes == 0:
                    # No shooter identified and all missed - track as team missed FTs
                    if 'TEAM_MISSED_FTS' not in ft_stats:
                        ft_stats['TEAM_MISSED_FTS'] = {'attempts': 0, 'makes': 0}
                    ft_stats['TEAM_MISSED_FTS']['attempts'] += expected_attempts
        
        i += 1
    
    return ft_stats

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
        
        # Calculate FT stats from game events
        game_ft_stats = calculate_ft_stats_from_events(game.get('GameEvents', []))
        
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
                
                player_name = player.get('Player Name', 'Unknown')
                
                # Get FT stats for this player from game events
                ft_attempts = 0
                ft_makes = 0
                if player_name in game_ft_stats:
                    ft_attempts = game_ft_stats[player_name]['attempts']
                    ft_makes = game_ft_stats[player_name]['makes']
                    
                player_record = {
                    'GameId': game_id,
                    'GameDate': game_date,
                    'GameDivision': game_division,
                    'PlayerName': player_name,
                    'PlayerNumber': player.get('Player Number', 0),
                    'Team': team_name,
                    'OpponentTeam': opponent_team,
                    'TotalPoints': player.get('Total Points', 0),
                    '1PMadeShots': player.get('1P Made Shots', 0),
                    '2PMadeShots': player.get('2P Made Shots', 0),
                    '3PMadeShots': player.get('3P Made Shots', 0),
                    'FTAttempts': ft_attempts,
                    'FTMakes': ft_makes,
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
        'FTAttempts': 'sum',
        'FTMakes': 'sum',
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
    
    # Calculate FT percentage
    players_db['FTPercentage'] = 0.0
    ft_mask = players_db['FTAttempts'] > 0
    players_db.loc[ft_mask, 'FTPercentage'] = (
        (players_db.loc[ft_mask, 'FTMakes'] / players_db.loc[ft_mask, 'FTAttempts']) * 100
    ).round(1)
    
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
        'FTAttempts', 'FTMakes', 'FTPercentage',
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
    Get player free throw statistics including FT percentage.
    
    This function shows comprehensive free throw statistics:
    - Total FT attempts and makes
    - FT percentage
    - Average FT per game
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of top players to return
    division (str): Optional division filter
    team (str): Optional team filter
    
    Returns:
    DataFrame: Players with free throw statistics including FT%
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
        'FTAttempts': 'sum',
        'FTMakes': 'sum',
        '1PMadeShots': 'sum',
        'TotalPoints': 'sum',
        'GameId': 'count'  # Games played
    }).reset_index()
    
    ft_stats.rename(columns={
        'GameId': 'GamesPlayed',
        '1PMadeShots': 'TotalFreeThrowsMade'  # Keep for backward compatibility
    }, inplace=True)
    
    # Calculate FT percentage
    ft_stats['FTPercentage'] = 0.0
    ft_mask = ft_stats['FTAttempts'] > 0
    ft_stats.loc[ft_mask, 'FTPercentage'] = (
        (ft_stats.loc[ft_mask, 'FTMakes'] / ft_stats.loc[ft_mask, 'FTAttempts']) * 100
    ).round(1)
    
    # Calculate average free throws per game
    ft_stats['AvgFreeThrowsPerGame'] = (ft_stats['TotalFreeThrowsMade'] / 
                                         ft_stats['GamesPlayed']).round(2)
    ft_stats['AvgPointsPerGame'] = (ft_stats['TotalPoints'] / 
                                    ft_stats['GamesPlayed']).round(1)
    
    # Filter players with at least 5 games and at least 5 total free throw attempts
    ft_stats = ft_stats[
        (ft_stats['GamesPlayed'] >= 5) & 
        (ft_stats['FTAttempts'] >= 5)
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
        
        # Check if this referee was in this game (normalize for comparison)
        referee_in_game = False
        normalized_referee_name = normalize_name_for_matching(referee_name)
        for ref in refs_data:
            if isinstance(ref, dict):
                ref_name = ref.get('Referee Name', '')
                if normalize_name_for_matching(ref_name) == normalized_referee_name:
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

def get_longest_duration_games(data, top_n=20, division=None):
    """
    Get games with the longest duration based on quarter durations.
    Uses the same calculation method as game detail page for consistency.
    
    Parameters:
    data (DataFrame): The game data
    top_n (int): Number of games to return (default 20)
    division (str): Optional division filter
    
    Returns:
    DataFrame: Games with longest duration, including duration in minutes
    """
    import ast
    
    # Create a copy to avoid modifying the original data
    data_copy = data.copy()
    
    # Filter by division if specified
    if division:
        data_copy = data_copy[data_copy['GameDivisionDisplay'] == division]
    
    if data_copy.empty:
        return pd.DataFrame()
    
    game_durations = []
    
    for _, game in data_copy.iterrows():
        events_str = game['GameEvents']
        teams_str = game.get('Teams', '[]')
        
        if pd.notna(events_str):
            try:
                events = ast.literal_eval(events_str)
                # Handle teams_str which could be a string, None, or pandas NA
                if pd.notna(teams_str) and isinstance(teams_str, str):
                    teams = ast.literal_eval(teams_str)
                else:
                    teams = []
                
                if events and len(events) > 0:
                    # Use the same calculation method as game detail page
                    # Calculate score evolution and then quarter durations
                    score_evolution = _calculate_score_evolution(
                        events, 
                        game['HomeTeamName'], 
                        game['AwayTeamName'],
                        teams
                    )
                    quarter_durations = _calculate_quarter_durations(score_evolution, events)
                    
                    # Get total duration from quarter_durations
                    if quarter_durations and 'total' in quarter_durations:
                        total_duration = quarter_durations['total']
                        duration_seconds = total_duration['duration_seconds']
                        duration_minutes = duration_seconds / 60
                        duration_formatted = total_duration['duration_formatted']
                        
                        game_durations.append({
                            'GameId': game['GameId'],
                            'HomeTeamName': game['HomeTeamName'],
                            'AwayTeamName': game['AwayTeamName'],
                            'FinalHomeScore': game['FinalHomeScore'],
                            'FinalAwayScore': game['FinalAwayScore'],
                            'GameDivisionDisplay': game['GameDivisionDisplay'],
                            'DurationMinutes': duration_minutes,
                            'DurationFormatted': duration_formatted
                        })
            except Exception:
                # Skip games with parsing errors
                continue
    
    if not game_durations:
        return pd.DataFrame()
    
    # Create DataFrame and sort by duration
    duration_df = pd.DataFrame(game_durations)
    longest_games = duration_df.nlargest(top_n, 'DurationMinutes')
    
    return longest_games

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

def get_data_source_preference():
    """
    Get the preferred data source from environment variable or configuration.
    
    Returns:
    str: One of 'csv', 'mongodb', or 'auto' (default)
    """
    # Check environment variable first
    env_source = os.environ.get('DATA_SOURCE', '').lower()
    if env_source in VALID_DATA_SOURCES:
        return env_source
    
    # Check configuration file
    try:
        config = load_config()
        config_source = config.get('dataSource', {}).get('preference', '').lower()
        if config_source in VALID_DATA_SOURCES:
            return config_source
    except:
        pass
    
    # Default to auto
    return DATA_SOURCE_AUTO

def load_game_data_from_mongodb_source():
    """
    Load game data from MongoDB and convert to pandas DataFrame.
    
    Returns:
    pandas.DataFrame: Game data loaded from MongoDB, or empty DataFrame if failed
    """
    global _data_source_info
    
    try:
        # Import MongoDB helper
        from src.mongodb_helper import is_mongodb_available, is_mongodb_enabled, load_json_data_from_mongodb
        
        # Check if MongoDB is available and enabled
        if not is_mongodb_available():
            print("❌ MongoDB not available: pymongo not installed")
            return pd.DataFrame()
        
        if not is_mongodb_enabled():
            print("❌ MongoDB not enabled: set MONGODB_ENABLED=true")
            return pd.DataFrame()
        
        # Load data from MongoDB
        print("Loading game data from MongoDB...")
        games_data = load_json_data_from_mongodb()
        
        if not games_data:
            print("❌ No data found in MongoDB")
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = pd.DataFrame(games_data)
        flatten_df(data)
        
        # Update data source info
        last_update = extract_last_update_from_data(data)
        if not last_update and '_stored_at' in data.columns:
            # Use MongoDB storage timestamp if available
            try:
                max_stored = pd.to_datetime(data['_stored_at'], errors='coerce').max()
                if pd.notna(max_stored):
                    last_update = max_stored.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        _data_source_info = {
            'source': 'mongodb',
            'last_update': last_update,
            'source_description': f'MongoDB database (loaded {len(data)} games)'
        }
        
        print(f"✅ Loaded {len(data)} games from MongoDB")
        
        # Optionally save to CSV for backup
        if FORCE_TO_CREATE_CSV:
            try:
                data.to_csv(CSV_FILEPATH, index=False)
                if AUTO_CREATE_PLAYER_DATABASE:
                    create_players_database(data)
            except:
                pass  # Don't fail if we can't save backup
        
        return data
        
    except ImportError as e:
        print(f"❌ Cannot import MongoDB helper: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Error loading data from MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def load_game_data():
    """
    Load game data based on configured data source preference.
    
    Supports three modes via DATA_SOURCE environment variable or config:
    - 'csv': Load only from CSV files (JSON directory or CSV backup)
    - 'mongodb': Load only from MongoDB database
    - 'auto': Try MongoDB first, then fall back to CSV (default)
    
    Returns:
    pandas.DataFrame: Game data from the configured source
    """
    global _data_source_info
    
    # Get data source preference
    data_source = get_data_source_preference()
    print(f"Data source preference: {data_source}")
    
    # MODE 1: MongoDB only
    if data_source == DATA_SOURCE_MONGODB:
        print("Configured to use MongoDB as data source")
        data = load_game_data_from_mongodb_source()
        if not data.empty:
            return data
        else:
            print("❌ MongoDB data source failed and CSV fallback is disabled")
            _data_source_info = {
                'source': 'none',
                'last_update': None,
                'source_description': 'MongoDB failed and fallback disabled'
            }
            return pd.DataFrame()
    
    # MODE 2: Auto (try MongoDB, fallback to CSV)
    if data_source == DATA_SOURCE_AUTO:
        print("Auto mode: Trying MongoDB first, will fallback to CSV if needed")
        data = load_game_data_from_mongodb_source()
        if not data.empty:
            return data
        else:
            print("MongoDB not available or empty, falling back to CSV sources...")
    
    # MODE 3: CSV only (or fallback from auto mode)
    # Continue with existing CSV loading logic
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
    
    print("❌ No data available: Neither MongoDB nor CSV sources found")
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
        
        # Parse location data
        location_info = parse_location_with_link(location)
        
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
            'Location': location_info['name'],  # Use the cleaned location name
            'LocationGoogleLink': location_info['google_link'],  # Add Google Maps link
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


def normalize_name_for_matching(name):
    """
    Normalize any name (player, team, referee) for matching/comparison purposes.
    Removes accents/diacritics to ensure consistent matching regardless of how
    the name was encoded/decoded in URLs or stored in the database.
    
    Parameters:
    name (str): The name to normalize
    
    Returns:
    str: Normalized name (without accents)
    
    Examples:
    >>> normalize_name_for_matching('KAFER Jérôme Charel')
    'KAFER Jerome Charel'
    >>> normalize_name_for_matching('Gréngewald Hueschtert B')
    'Grengewald Hueschtert B'
    """
    if not name:
        return name
    
    # Remove accents/diacritics for consistency
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', str(name))
        if unicodedata.category(c) != 'Mn'
    )
    return normalized


def normalize_team_name_for_matching(team_name):
    """
    Normalize team name for matching/comparison purposes.
    Removes accents/diacritics to ensure consistent matching regardless of how
    the name was encoded/decoded in URLs.
    
    This function now delegates to normalize_name_for_matching() for consistency.
    
    Parameters:
    team_name (str): The team name to normalize
    
    Returns:
    str: Normalized team name (without accents)
    """
    return normalize_name_for_matching(team_name)


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
    home_team, away_team = parse_team_names_from_url(game.get('GameUrl', ''))
    
    # Parse the date from ScheduledGameDate using the helper function
    game_date = parse_dotnet_json_date(game.get('ScheduledGameDate'))
    
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
            
            # Add time_until columns for future games
            all_games['TimeUntilText'] = ''
            all_games['TimeUntilColorClass'] = ''
            all_games['TimeUntilHours'] = float('inf')
            
            # Calculate hotness for future games based on standings
            # Get standings for the division filter if provided, otherwise None
            standings_df = None
            if division_filter is not None:
                standings_df = calculate_standings_by_division(filtered_data, division_filter)
            
            for idx, row in all_games.iterrows():
                if row.get('IsFutureGame', False):
                    time_until = calculate_time_until_game(row.get('DateTime'))
                    all_games.at[idx, 'TimeUntilText'] = time_until['text']
                    all_games.at[idx, 'TimeUntilColorClass'] = time_until['color_class']
                    all_games.at[idx, 'TimeUntilHours'] = time_until['hours']
                    
                    # Calculate hotness based on league standings
                    home_team = row.get('HomeTeamName')
                    away_team = row.get('AwayTeamName')
                    game_division = row.get('GameDivisionDisplay')
                    
                    # Get standings for this game's division if not already calculated
                    if game_division and (standings_df is None or division_filter != game_division):
                        game_standings = calculate_standings_by_division(filtered_data, game_division)
                    else:
                        game_standings = standings_df
                    
                    if home_team and away_team and game_standings is not None and not game_standings.empty:
                        hotness_score, hotness_icon = calculate_future_game_hotness(
                            home_team, away_team, game_standings
                        )
                        all_games.at[idx, 'HotnessScore'] = hotness_score
                        all_games.at[idx, 'HotnessIcon'] = hotness_icon
                    else:
                        # Default neutral hotness if we can't calculate
                        all_games.at[idx, 'HotnessScore'] = 50
                        all_games.at[idx, 'HotnessIcon'] = '🌡️'
            
            return all_games
    
    return finished_games


def calculate_time_until_game(game_datetime_str):
    """
    Calculate time remaining until a game and return formatted string with color class.
    
    Parameters:
    game_datetime_str (str): The game datetime string
    
    Returns:
    dict: Dictionary with keys:
        - 'text': Formatted time remaining text (e.g., "in 2 days", "in 5 hours")
        - 'color_class': CSS class for color coding based on urgency
        - 'hours': Total hours until game (for sorting)
    """
    from datetime import datetime, timedelta
    
    if not game_datetime_str or game_datetime_str == 'TBD':
        return {'text': '', 'color_class': '', 'hours': float('inf')}
    
    try:
        # Parse the game datetime
        game_dt = pd.to_datetime(game_datetime_str)
        now = datetime.now()
        
        # Calculate time difference
        time_diff = game_dt - now
        
        # If game is in the past, return empty
        if time_diff.total_seconds() < 0:
            return {'text': '', 'color_class': '', 'hours': -1}
        
        total_hours = time_diff.total_seconds() / 3600
        # Round up for partial days to show more accurate day count
        import math
        total_days = math.ceil(total_hours / 24)
        
        # Format the text based on time remaining
        if total_hours < 1:
            minutes = int(time_diff.total_seconds() / 60)
            text = f"in {minutes} min" if minutes > 0 else "starting soon"
            color_class = 'time-very-soon'
        elif total_hours < 24:
            hours = int(total_hours)
            text = f"in {hours}h"
            color_class = 'time-today'
        elif total_hours >= 24 and total_hours < 36:  # Between 1-1.5 days (reasonable "tomorrow" range)
            text = "tomorrow"
            color_class = 'time-tomorrow'
        elif total_days <= 3:
            text = f"in {total_days} days"
            color_class = 'time-few-days'
        elif total_days <= 7:
            text = f"in {total_days} days"
            color_class = 'time-week'
        else:
            text = f"in {total_days} days"
            color_class = 'time-later'
        
        return {
            'text': text,
            'color_class': color_class,
            'hours': total_hours
        }
    except Exception as e:
        return {'text': '', 'color_class': '', 'hours': float('inf')}


def get_fixtures_matrix_data(data, division_filter=None):
    """
    Get fixtures data organized as a matrix (team vs team).
    Includes both finished games and future games from gamesDB.json.
    
    Parameters:
    data (DataFrame): The game data
    division_filter (str): Optional filter by division
    
    Returns:
    dict: Matrix data with the following keys:
        - teams (list): List of teams sorted by points (descending), then alphabetically
        - matrix (dict): Nested dict with teams as keys and lists of games as values
        - divisions (list): List of available divisions
        - current_division (str): Currently selected division
        - team_points (dict): Dictionary mapping team names to their total points
        - team_wins (dict): Dictionary mapping team names to their total wins
        - team_losses (dict): Dictionary mapping team names to their total losses
    """
    if data.empty:
        return {'teams': [], 'matrix': {}, 'divisions': [], 'team_points': {}, 'team_wins': {}, 'team_losses': {}}
    
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
    
    # Get closest games for each team to determine which games are "next" for which team
    closest_games = get_closest_games_by_team(data, division_filter)
    
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
    
    # Initialize matrix and team points
    matrix = {}
    team_points = {}
    team_wins = {}
    team_losses = {}
    for home_team in all_teams:
        matrix[home_team] = {}
        team_points[home_team] = 0
        team_wins[home_team] = 0
        team_losses[home_team] = 0
        for away_team in all_teams:
            matrix[home_team][away_team] = []
    
    # Populate matrix with games and calculate team points
    for _, game in filtered_data.iterrows():
        raw_home = game['HomeTeamName']
        raw_away = game['AwayTeamName']
        
        if pd.notna(raw_home) and pd.notna(raw_away):
            home_team = normalize_team_name_for_display(raw_home)
            away_team = normalize_team_name_for_display(raw_away)
            # Parse location to get name and Google Maps link
            location_info = parse_location_with_link(game['GameLocation'])
            
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
            
            # Determine which team(s) this game is the next game for
            game_id = game['GameId']
            is_next_for_home = closest_games.get(raw_home) == game_id
            is_next_for_away = closest_games.get(raw_away) == game_id
            
            # Calculate time until game for future games
            time_until = {'text': '', 'color_class': '', 'hours': float('inf')}
            if game.get('IsFutureGame', False):
                time_until = calculate_time_until_game(game['DateTime'])
            
            game_info = {
                'game_id': game_id,
                'date': game['DateTime'][:16] if pd.notna(game['DateTime']) else 'TBD',
                'home_score': home_score_int,
                'away_score': away_score_int,
                'home_team_raw': raw_home,
                'away_team_raw': raw_away,
                'location': location_info['name'],
                'location_google_link': location_info['google_link'],
                'division': game['GameDivisionDisplay'],
                'is_finished': is_finished,
                'referees': parse_referees(game.get('Referres')) if is_finished else [],
                'top_scorer': get_game_top_scorer(game) if is_finished else {'name': None, 'points': 0, 'team': None},
                'hotness_score': hotness_score,
                'hotness_icon': hotness_icon,
                'is_future': game.get('IsFutureGame', False),
                'is_next_for_home': is_next_for_home,
                'is_next_for_away': is_next_for_away,
                'time_until': time_until
            }
            
            matrix[home_team][away_team].append(game_info)
            
            # Calculate team points for finished games (2 points for win, 1 point for loss)
            if is_finished and home_score_int is not None and away_score_int is not None:
                if home_score_int > away_score_int:  # Home team wins
                    team_points[home_team] += 2
                    team_points[away_team] += 1
                    team_wins[home_team] += 1
                    team_losses[away_team] += 1
                elif away_score_int > home_score_int:  # Away team wins
                    team_points[home_team] += 1
                    team_points[away_team] += 2
                    team_wins[away_team] += 1
                    team_losses[home_team] += 1
                # Note: Tied games (rare in basketball) are not awarded points
    
    # Sort teams by points (descending), then alphabetically
    sorted_teams = sorted(all_teams, key=lambda t: (-team_points[t], t))
    
    return {
        'teams': sorted_teams,
        'matrix': matrix,
        'divisions': all_divisions,
        'current_division': division_filter or (all_divisions[0] if all_divisions else None),
        'team_points': team_points,
        'team_wins': team_wins,
        'team_losses': team_losses
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
        location_name = None
        if isinstance(location_data, str):
            # Try to parse as JSON if it looks like JSON
            if location_data.startswith('{') and location_data.endswith('}'):
                import ast
                location_dict = ast.literal_eval(location_data)
                location_name = location_dict.get('Name', 'TBD')
            else:
                location_name = location_data
        elif isinstance(location_data, dict):
            location_name = location_data.get('Name', 'TBD')
        else:
            location_name = str(location_data)
        
        # Remove " - FINAL RESULT" suffix if present
        if location_name and location_name != 'TBD':
            location_name = location_name.replace(' - FINAL RESULT', '')
        
        return location_name
    except:
        return 'TBD'


def parse_location_with_link(location_data):
    """
    Parse location data to extract both the name and Google Maps link.
    
    Parameters:
    location_data: The location data (could be string, dict, or JSON string)
    
    Returns:
    dict: Dictionary with 'name' and 'google_link' keys
    """
    result = {
        'name': 'TBD',
        'google_link': None
    }
    
    if pd.isna(location_data):
        return result
    
    try:
        location_dict = None
        if isinstance(location_data, str):
            # Try to parse as JSON if it looks like JSON
            if location_data.startswith('{') and location_data.endswith('}'):
                import ast
                location_dict = ast.literal_eval(location_data)
            else:
                result['name'] = location_data
                return result
        elif isinstance(location_data, dict):
            location_dict = location_data
        
        if location_dict:
            location_name = location_dict.get('Name', 'TBD')
            # Remove " - FINAL RESULT" suffix if present
            if location_name and location_name != 'TBD':
                location_name = location_name.replace(' - FINAL RESULT', '')
            result['name'] = location_name
            
            # Get Google Maps link and clean it up
            google_link = location_dict.get('Google Link', '')
            if google_link and isinstance(google_link, str):
                # Strip whitespace and validate it's a URL
                google_link = google_link.strip()
                if google_link.lower().startswith(('http://', 'https://')):
                    result['google_link'] = google_link
        
        return result
    except:
        return result


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


def export_season_archive(output_path=None, include_raw=False):
    """
    Export current season data to a ZIP archive.
    
    Parameters:
    output_path (str): Path for output ZIP file (optional, auto-generated if not provided)
    include_raw (bool): Include raw HTML data directories (default: False)
    
    Returns:
    dict: Export result with success status and details
    """
    result = {
        'success': False,
        'archive_path': None,
        'files_added': 0,
        'archive_size': 0,
        'errors': []
    }
    
    try:
        # Load configuration
        config = load_config()
        season_id = config.get("seasonId", "unknown")
        
        # Determine output path
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            archives_dir = "archives"
            os.makedirs(archives_dir, exist_ok=True)
            
            if season_id != "unknown":
                output_path = os.path.join(archives_dir, f"raw-data-{season_id}-{timestamp}.zip")
            else:
                output_path = os.path.join(archives_dir, f"raw-data-{timestamp}.zip")
        else:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(output_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
        
        # Files to include
        essential_files = [
            CSV_FILEPATH,
            "data/gamesDB.json",
            "data/gameScheduleDB.json",
            PLAYERS_DATABASE_CSV_FILEPATH,
        ]
        
        # Create the archive
        files_added = 0
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            # Add essential files
            for filepath in essential_files:
                if os.path.exists(filepath):
                    zipf.write(filepath, filepath)
                    files_added += 1
            
            # Add raw data directories if requested
            if include_raw:
                raw_directories = [
                    config.get("directories", {}).get("gameScheduleRaw", "data/game-schedule-raw"),
                    config.get("directories", {}).get("fullGameStatsRaw", "data/full-game-stats-raw"),
                    config.get("directories", {}).get("fullGameStatsOutput", "data/full-game-stats-output"),
                ]
                
                for dir_path in raw_directories:
                    if os.path.exists(dir_path) and os.path.isdir(dir_path):
                        for root, dirs, files in os.walk(dir_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = file_path
                                zipf.write(file_path, arcname)
                                files_added += 1
        
        # Get final archive size
        archive_size = os.path.getsize(output_path)
        
        result['success'] = True
        result['archive_path'] = output_path
        result['files_added'] = files_added
        result['archive_size'] = archive_size
        result['season_id'] = season_id
        
    except Exception as e:
        result['errors'].append(f"Error creating archive: {str(e)}")
    
    return result


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
    
    # Normalize player name for matching
    normalized_player_name = normalize_name_for_matching(player_name)
    
    # Filter for the specific player (normalize database names for comparison)
    player_games = player_stats[
        player_stats['PlayerName'].apply(normalize_name_for_matching) == normalized_player_name
    ].copy()
    
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
        'ft_attempts': int(player_games['FTAttempts'].sum()),
        'ft_makes': int(player_games['FTMakes'].sum()),
        'ft_percentage': round((player_games['FTMakes'].sum() / player_games['FTAttempts'].sum() * 100), 1) if player_games['FTAttempts'].sum() > 0 else 0.0,
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
    
    # Add hotness score and FT percentage to each game
    for game_record in game_by_game:
        game_id = game_record['GameId']
        game_row = data[data['GameId'] == game_id]
        
        # Calculate FT percentage for this game
        if game_record['FTAttempts'] > 0:
            game_record['FTPercentage'] = round((game_record['FTMakes'] / game_record['FTAttempts']) * 100, 1)
        else:
            game_record['FTPercentage'] = 0.0
        
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


def _get_multi_team_players(data):
    """
    Identify players who play for multiple teams.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    dict: Dictionary mapping player names to list of teams they play for
    """
    if data.empty:
        return {}
    
    # Extract all player stats to get player-team relationships
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return {}
    
    # Group by player name and get unique teams
    player_teams = player_stats.groupby('PlayerName')['Team'].apply(lambda x: sorted(set(x))).to_dict()
    
    # Filter to only include players with more than one team
    multi_team_players = {player: teams for player, teams in player_teams.items() if len(teams) > 1}
    
    return multi_team_players


def _extract_team_player_stats(team_games, team_name, multi_team_players=None):
    """
    Extract comprehensive player statistics for a team from their games.
    
    Parameters:
    team_games (DataFrame): Games filtered for the team
    team_name (str): Name of the team
    multi_team_players (dict): Optional dictionary of players who play for multiple teams
    
    Returns:
    dict: Dictionary containing:
        - all_players: List of all players with comprehensive stats
        - quarter_by_quarter: Quarter-by-quarter breakdown for each player
        - performance_evolution: Last 5 games performance for each player
    """
    import ast
    from collections import defaultdict
    
    if multi_team_players is None:
        multi_team_players = {}
    
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
            
            # Normalize team names for comparison
            normalized_team_name = normalize_name_for_matching(team_name)
            normalized_home_team = normalize_name_for_matching(game['HomeTeamName'])
            normalized_away_team = normalize_name_for_matching(game['AwayTeamName'])
            
            # Find the team's data (home or away)
            team_data = None
            is_home = normalized_home_team == normalized_team_name
            
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
        player_name = stats['name']
        
        # Check if player plays for multiple teams
        plays_multiple_teams = player_name in multi_team_players
        other_teams = []
        if plays_multiple_teams:
            # Get list of other teams (excluding current team)
            all_teams = multi_team_players[player_name]
            other_teams = [t for t in all_teams if normalize_name_for_matching(t) != normalize_name_for_matching(team_name)]
        
        player_dict = {
            'name': player_name,
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
            'last_5_games': stats['last_5_games'],
            'plays_multiple_teams': plays_multiple_teams,
            'other_teams': other_teams
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
    
    # Normalize team name for matching
    normalized_team_name = normalize_team_name_for_matching(team_name)
    
    # Filter games for this team (normalize data team names for comparison)
    team_games = data[
        (data['HomeTeamName'].apply(normalize_team_name_for_matching) == normalized_team_name) | 
        (data['AwayTeamName'].apply(normalize_team_name_for_matching) == normalized_team_name)
    ].copy()
    
    if team_games.empty:
        return None
    
    # Sort by date
    team_games = team_games.sort_values('DateTime')
    
    # Process each game
    team_games['IsHome'] = team_games['HomeTeamName'].apply(normalize_team_name_for_matching) == normalized_team_name
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
    
    # Get multi-team players information
    multi_team_players = _get_multi_team_players(data)
    
    # Extract player statistics for this team
    player_stats = _extract_team_player_stats(team_games, team_name, multi_team_players)
    
    # Get next 5 upcoming games for this team
    next_games = get_team_next_games(team_name, limit=5)
    
    return {
        'basic_stats': basic_stats,
        'game_by_game': game_by_game,
        'performance_evolution': performance_evolution,
        'player_stats': player_stats,
        'next_games': next_games
    }


def get_team_next_games(team_name, limit=5, gamesdb_path='data/gamesDB.json'):
    """
    Get the next upcoming games for a specific team.
    
    Parameters:
    team_name (str): The name of the team
    limit (int): Maximum number of games to return (default: 5)
    gamesdb_path (str): Path to gamesDB.json file
    
    Returns:
    list: List of upcoming game dictionaries with formatted information
    """
    from datetime import datetime
    
    # Load future games
    future_games = load_future_games_from_gamesdb(gamesdb_path)
    if not future_games:
        return []
    
    # Normalize the team name for comparison
    normalized_team_name = normalize_team_name_for_display(team_name)
    
    # Filter games for this team and parse dates
    team_future_games = []
    for game in future_games:
        home_team, away_team = parse_team_names_from_url(game.get('GameUrl', ''))
        
        # Check if this team is playing
        if home_team == normalized_team_name or away_team == normalized_team_name:
            # Parse the game date using the helper function
            game_date_iso = parse_dotnet_json_date(game.get('ScheduledGameDate'))
            game_date = None
            game_datetime = None
            if game_date_iso:
                try:
                    # Parse the ISO date back to datetime for further processing
                    game_datetime = datetime.strptime(game_date_iso, ISO_DATE_FORMAT)
                    game_date = game_datetime.strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
            
            # Determine if team is home or away
            is_home = home_team == normalized_team_name
            opponent = away_team if is_home else home_team
            
            # Convert division name
            division_display = convert_division_name(game.get('GameDivisionName', ''))
            
            # Extract time from datetime if available
            game_time = None
            if game_datetime:
                game_time = game_datetime.strftime('%H:%M')
            
            team_future_games.append({
                'game_id': game.get('GameId'),
                'date': game_date,
                'time': game_time,
                'datetime_obj': game_datetime,
                'division': division_display,
                'opponent': opponent,
                'is_home': is_home,
                'location': 'Home' if is_home else 'Away',
                'game_url': game.get('GameUrl')
            })
    
    # Sort by date (earliest first) and limit to requested number
    # Use a large naive datetime for games without dates to sort them to the end
    team_future_games.sort(key=lambda x: x['datetime_obj'] if x['datetime_obj'] else datetime(9999, 12, 31))
    
    # Remove datetime_obj as it's not JSON serializable
    for game in team_future_games[:limit]:
        game.pop('datetime_obj', None)
    
    return team_future_games[:limit]


def get_team_player_stats_for_future_game(team_name, players_db_path='data/players-database.csv'):
    """
    Get player statistics for a team from the players database.
    Used for future games to show historical player performance.
    
    Parameters:
    team_name (str): Team name to get players for
    players_db_path (str): Path to the players database CSV
    
    Returns:
    list: List of player dictionaries with statistics
    """
    if not os.path.exists(players_db_path):
        return []
    
    try:
        # Load players database
        players_df = pd.read_csv(players_db_path, encoding='utf-8-sig')
        
        # Normalize team name for matching
        team_name_normalized = normalize_team_name_for_display(team_name)
        
        # Filter players for this team
        team_players = players_df[players_df['Team'].apply(normalize_team_name_for_display) == team_name_normalized].copy()
        
        if team_players.empty:
            return []
        
        # Sort by StartingPercentage (descending) and TotalPoints (descending)
        team_players = team_players.sort_values(
            by=['StartingPercentage', 'TotalPoints'], 
            ascending=[False, False]
        )
        
        # Convert to list of dictionaries
        players = []
        for _, player in team_players.iterrows():
            player_dict = {
                'Player Name': player['PlayerName'],
                'Player Number': int(player['PlayerNumber']) if pd.notna(player['PlayerNumber']) else 0,
                'Total Points': int(player['TotalPoints']) if pd.notna(player['TotalPoints']) else 0,
                '1P Made Shots': int(player['1PMadeShots']) if pd.notna(player['1PMadeShots']) else 0,
                '2P Made Shots': int(player['2PMadeShots']) if pd.notna(player['2PMadeShots']) else 0,
                '3P Made Shots': int(player['3PMadeShots']) if pd.notna(player['3PMadeShots']) else 0,
                'Total Fouls': int(player['TotalFouls']) if pd.notna(player['TotalFouls']) else 0,
                'Games Played': int(player['GamesPlayed']) if pd.notna(player['GamesPlayed']) else 0,
                'Games Started': int(player['GamesStarted']) if pd.notna(player['GamesStarted']) else 0,
                'Starting Percentage': float(player['StartingPercentage']) if pd.notna(player['StartingPercentage']) else 0.0,
                'Avg Points Per Game': float(player['AvgPointsPerGame']) if pd.notna(player['AvgPointsPerGame']) else 0.0,
                'Starting Five': 'false'  # Will be set by predict_starting_five
            }
            players.append(player_dict)
        
        return players
    except Exception as e:
        # Use logging for better error tracking
        import logging
        logging.warning(f"Error loading player stats for team {team_name}: {e}")
        return []


def predict_starting_five(players):
    """
    Predict the starting five players based on a weighted formula that considers:
    1. Starting Percentage (primary factor - 70% weight)
    2. Games Played (experience factor - 20% weight)
    3. Average Points Per Game (minor factor - 10% weight)
    
    The formula creates a composite score that balances historical starting frequency,
    player experience, and offensive contribution.
    
    Parameters:
    players (list): List of player dictionaries with statistics
    
    Returns:
    list: List of player dictionaries with 'Starting Five' field updated
    """
    if not players:
        return players
    
    # Calculate composite score for each player
    def calculate_player_score(player):
        """
        Calculate a weighted score for predicting starting five.
        
        Formula:
        Score = (Starting% * 0.7) + (Normalized Games Played * 0.2) + (Normalized Avg Points * 0.1)
        
        This prioritizes players who:
        - Have high starting percentages (main indicator)
        - Have played more games (experience and reliability)
        - Contribute points (offensive value)
        """
        starting_pct = player.get('Starting Percentage', 0)
        games_played = player.get('Games Played', 0)
        avg_points = player.get('Avg Points Per Game', 0)
        
        # Starting percentage is already 0-100, we'll normalize it to 0-1
        starting_score = starting_pct / 100.0
        
        # For normalization, we'll use the max values among all players
        # This will be calculated after we know all players' values
        return {
            'starting_pct': starting_pct,
            'games_played': games_played,
            'avg_points': avg_points,
            'starting_score': starting_score
        }
    
    # Calculate scores for all players
    player_scores = []
    max_games = max((p.get('Games Played', 0) for p in players), default=0)
    max_points = max((p.get('Avg Points Per Game', 0) for p in players), default=0)
    
    for player in players:
        scores = calculate_player_score(player)
        
        # Normalize games played (0-1 scale)
        # If max_games is 0, all players have 0 games, so games_score is 0 for all
        games_score = scores['games_played'] / max_games if max_games > 0 else 0
        
        # Normalize average points (0-1 scale)
        # If max_points is 0, all players have 0 points, so points_score is 0 for all
        points_score = scores['avg_points'] / max_points if max_points > 0 else 0
        
        # Calculate weighted composite score
        # 70% starting percentage, 20% games played, 10% points
        composite_score = (
            scores['starting_score'] * 0.7 +
            games_score * 0.2 +
            points_score * 0.1
        )
        
        player_scores.append({
            'player': player,
            'composite_score': composite_score,
            'starting_pct': scores['starting_pct'],
            'games_played': scores['games_played'],
            'avg_points': scores['avg_points']
        })
    
    # Sort by composite score (descending)
    player_scores.sort(key=lambda x: x['composite_score'], reverse=True)
    
    # Mark top 5 as starting five
    for i, item in enumerate(player_scores):
        if i < 5:
            item['player']['Starting Five'] = 'true'
        else:
            item['player']['Starting Five'] = 'false'
    
    return players


def get_future_game_details(game_id, game):
    """
    Get comprehensive details for a future game.
    
    Parameters:
    game_id (str): The game ID
    game (dict): Future game data from gamesDB.json
    
    Returns:
    dict: Dictionary containing future game details with predicted starting lineups
    """
    from datetime import datetime
    
    home_team, away_team = parse_team_names_from_url(game.get('GameUrl', ''))
    
    # Parse the date from ScheduledGameDate using the helper function
    game_date = parse_dotnet_json_date(game.get('ScheduledGameDate'))
    if not game_date:
        game_date = 'TBD'
    
    # Convert division name
    division = convert_division_name(game.get('GameDivisionName', ''))
    
    # Build basic info
    basic_info = {
        'game_id': game_id,
        'location': None,  # Not available for future games
        'division': division,
        'date_time': game_date,
        'home_team': home_team,
        'away_team': away_team,
        'final_score': 'Upcoming',
        'home_score': None,
        'away_score': None,
        'winner': None,
        'loser': None,
        'is_future': True,
        'game_url': game.get('GameUrl'),
        'season_id': game.get('SeasonId')
    }
    
    # Get player statistics for both teams
    home_players = get_team_player_stats_for_future_game(home_team)
    away_players = get_team_player_stats_for_future_game(away_team)
    
    # Predict starting five for each team
    home_players = predict_starting_five(home_players)
    away_players = predict_starting_five(away_players)
    
    # Calculate team totals (historical averages)
    def calculate_team_totals(players):
        if not players:
            return {
                'points': 0,
                '1p': 0,
                '2p': 0,
                '3p': 0,
                'fouls': 0,
                'avg_points': 0
            }
        
        # Calculate total season stats
        total_points = sum(p.get('Total Points', 0) for p in players)
        total_1p = sum(p.get('1P Made Shots', 0) for p in players)
        total_2p = sum(p.get('2P Made Shots', 0) for p in players)
        total_3p = sum(p.get('3P Made Shots', 0) for p in players)
        total_fouls = sum(p.get('Total Fouls', 0) for p in players)
        
        # Calculate average points per game (team)
        # Use the median games_played to avoid outliers affecting the calculation
        games_played_list = [p.get('Games Played', 0) for p in players if p.get('Games Played', 0) > 0]
        games_played = max(games_played_list) if games_played_list else 0
        avg_points = total_points / games_played if games_played > 0 else 0
        
        return {
            'points': total_points,
            '1p': total_1p,
            '2p': total_2p,
            '3p': total_3p,
            'fouls': total_fouls,
            'avg_points': round(avg_points, 1),
            'games_played': games_played
        }
    
    # Build teams data
    teams_data = [
        {
            'name': home_team,
            'name_short': home_team,
            'role': 'Home',
            'result': None,
            'league_points': None,
            'total_won_points': None,
            'total_lost_points': None,
            'players': home_players,
            'coach': 'N/A',
            'timeouts_used': 0,
            'totals': calculate_team_totals(home_players)
        },
        {
            'name': away_team,
            'name_short': away_team,
            'role': 'Away',
            'result': None,
            'league_points': None,
            'total_won_points': None,
            'total_lost_points': None,
            'players': away_players,
            'coach': 'N/A',
            'timeouts_used': 0,
            'totals': calculate_team_totals(away_players)
        }
    ]
    
    return {
        'basic_info': basic_info,
        'teams': teams_data,
        'events': [],
        'score_evolution': [],
        'game_stats': None,
        'referees': []
    }


def get_game_details(data, game_id):
    """
    Get comprehensive details for a specific game.
    Handles both finished games and future games.
    
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
    
    # First check if it's a future game
    future_games = load_future_games_from_gamesdb()
    if future_games:
        for game in future_games:
            if str(game.get('GameId')) == game_id:
                # Found a future game - use the future game details function
                return get_future_game_details(game_id, game)
    
    # Find the game in finished games
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
    
    # Calculate quarter durations
    quarter_durations = _calculate_quarter_durations(score_evolution, events)
    
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
        'quarter_durations': quarter_durations,
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


def _calculate_quarter_durations(score_evolution, events):
    """
    Calculate the duration of each quarter based on game events.
    
    Rules:
    1. Beginning of each quarter starts with any game event in that quarter (foul, score, timeout)
    2. End of quarter is when any event from next quarter occurs
    3. For the last quarter, it ends when "End of game signal" occurs
    
    Parameters:
    score_evolution (list): List of score points throughout the game
    events (list): List of all game events
    
    Returns:
    dict: Dictionary mapping quarter number to duration info:
        {
            1: {'start_seconds': X, 'end_seconds': Y, 'duration_seconds': Z, 'duration_formatted': 'MM:SS'},
            ...
        }
    """
    if not score_evolution:
        return {}
    
    from datetime import datetime
    
    # Sort events chronologically
    sorted_events = sorted(events, key=lambda x: x.get('EventDateTime', ''))
    
    # Find first event time for calculating elapsed time
    first_event_time = None
    for e in sorted_events:
        if e.get('EventDateTime'):
            try:
                first_event_time = datetime.fromisoformat(e.get('EventDateTime', '').replace('Z', '+00:00'))
                break
            except:
                pass
    
    # Group events by quarter and track timing
    quarter_times = {}
    
    # First pass: Get start and end times from score_evolution
    for point in score_evolution:
        quarter = point.get('quarter', 0)
        elapsed = point.get('elapsed_seconds', 0)
        
        if quarter not in quarter_times:
            quarter_times[quarter] = {
                'start_seconds': elapsed,
                'end_seconds': elapsed
            }
        else:
            # Update end time to latest event in this quarter
            quarter_times[quarter]['end_seconds'] = elapsed
    
    # Second pass: Adjust end times based on next quarter's start
    # End of quarter is when next quarter's first event occurs
    sorted_quarters = sorted(quarter_times.keys())
    for i, quarter in enumerate(sorted_quarters):
        if i < len(sorted_quarters) - 1:
            # Not the last quarter - end is when next quarter starts
            next_quarter = sorted_quarters[i + 1]
            quarter_times[quarter]['end_seconds'] = quarter_times[next_quarter]['start_seconds']
    
    # For the last quarter, check if there's an "End of game signal" event
    if sorted_quarters and sorted_events and first_event_time:
        last_quarter = sorted_quarters[-1]
        for event in reversed(sorted_events):  # Check from end (already sorted)
            action = event.get('EventAction', '').lower()
            if 'end of game' in action or 'signal end' in action:
                # Found end of game signal - use its timestamp
                event_time = event.get('EventDateTime', '')
                if event_time:
                    try:
                        end_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                        elapsed_seconds = (end_time - first_event_time).total_seconds()
                        quarter_times[last_quarter]['end_seconds'] = elapsed_seconds
                    except:
                        pass
                break
    
    # Calculate durations and format
    total_duration_seconds = 0
    for quarter in quarter_times:
        start = quarter_times[quarter]['start_seconds']
        end = quarter_times[quarter]['end_seconds']
        duration = end - start
        
        quarter_times[quarter]['duration_seconds'] = duration
        total_duration_seconds += duration
        
        # Format as MM:SS
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        quarter_times[quarter]['duration_formatted'] = f"{minutes}:{seconds:02d}"
    
    # Add total duration to the dictionary
    if quarter_times:
        total_minutes = int(total_duration_seconds // 60)
        total_seconds = int(total_duration_seconds % 60)
        quarter_times['total'] = {
            'duration_seconds': total_duration_seconds,
            'duration_formatted': f"{total_minutes}:{total_seconds:02d}"
        }
    
    return quarter_times


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


def calculate_future_game_hotness(home_team, away_team, standings_df):
    """
    Calculate hotness score for a future game based on league standings.
    
    The hotness is based on:
    1. Team Rankings: Higher when both teams are highly ranked
    2. Ranking Proximity: Higher when teams are close in standings (competitive matchup)
    3. Top-of-table Factor: Extra weight for games involving top 3 teams
    
    Parameters:
    home_team (str): Home team name
    away_team (str): Away team name
    standings_df (DataFrame): Standings table with 'Team Name' column and index as rank
    
    Returns:
    tuple: (hotness_score (int 0-100), hotness_icon (str))
    """
    # Default for cases where we can't calculate
    if standings_df is None or standings_df.empty:
        return 50, "🌡️"  # Neutral/unknown
    
    # Normalize team names for matching
    home_team_normalized = normalize_team_name_for_matching(home_team)
    away_team_normalized = normalize_team_name_for_matching(away_team)
    
    # Find teams in standings
    home_rank = None
    away_rank = None
    total_teams = len(standings_df)
    
    for rank, row in standings_df.iterrows():
        team_name = row['Team Name']
        team_normalized = normalize_team_name_for_matching(team_name)
        
        if team_normalized == home_team_normalized:
            home_rank = rank
        if team_normalized == away_team_normalized:
            away_rank = rank
    
    # If either team is not found in standings, return neutral hotness
    if home_rank is None or away_rank is None:
        return 50, "🌡️"
    
    # Calculate hotness components
    
    # 1. Average Ranking Factor (0-1): Lower average rank = higher hotness
    # Normalize ranks to 0-1 range (1st place = 0, last place = 1)
    home_rank_normalized = (home_rank - 1) / max(total_teams - 1, 1)
    away_rank_normalized = (away_rank - 1) / max(total_teams - 1, 1)
    avg_rank_normalized = (home_rank_normalized + away_rank_normalized) / 2
    ranking_factor = 1 - avg_rank_normalized  # Invert so top teams = high value
    
    # 2. Proximity Factor (0-1): Closer ranks = more competitive = higher hotness
    rank_difference = abs(home_rank - away_rank)
    # Normalize by total teams (difference of half the league = 0.5)
    proximity_normalized = rank_difference / max(total_teams, 1)
    proximity_factor = 1 - min(proximity_normalized, 1)  # Closer = higher value
    
    # 3. Top-of-table Bonus: Extra excitement for top teams playing
    # Only apply significant bonus for top 2 teams, smaller bonus for top 3-4
    top_tier_1 = 2  # Top 2 teams
    top_tier_2 = 4  # Top 4 teams
    
    home_is_top1 = home_rank <= top_tier_1
    away_is_top1 = away_rank <= top_tier_1
    home_is_top2 = home_rank <= top_tier_2
    away_is_top2 = away_rank <= top_tier_2
    
    if home_is_top1 and away_is_top1:
        top_bonus = 0.25  # Both in top 2 = very hot
    elif home_is_top2 and away_is_top2:
        top_bonus = 0.12  # Both in top 4 = warm bonus
    elif home_is_top1 or away_is_top1:
        top_bonus = 0.08  # One in top 2 = small bonus
    else:
        top_bonus = 0.0  # Neither in top tier = no bonus
    
    # Combine factors with weights
    # 50% ranking quality, 35% proximity/competitiveness, 15% base + top bonus
    base_score = (0.50 * ranking_factor + 0.35 * proximity_factor + 0.15)
    
    # Add top bonus and scale to 0-100
    hotness_score = int(min(100, (base_score + top_bonus) * 100))
    
    # Get icon for the score
    hotness_icon = get_hotness_icon(hotness_score)
    
    return hotness_score, hotness_icon


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
        - team: Team name (most recent team if player changed teams)
        - player_number: Player's number
        - last_three_scores: List of scores from last 3 games
        - teams_played_for: List of dictionaries with team breakdown (team name, games count, avg score)
    """
    player_stats = extract_all_player_stats(data)
    
    if player_stats.empty:
        return None
    
    # Normalize player name for matching
    normalized_player_name = normalize_name_for_matching(player_name)
    
    # Filter for the specific player (normalize database names for comparison)
    player_games = player_stats[
        player_stats['PlayerName'].apply(normalize_name_for_matching) == normalized_player_name
    ].copy()
    
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
    
    # Calculate team breakdown - group by team and get stats
    teams_breakdown = []
    for team_name in player_games['Team'].unique():
        team_games = player_games[player_games['Team'] == team_name]
        teams_breakdown.append({
            'team': str(team_name),
            'games': int(len(team_games)),
            'avg_score': float(round(team_games['TotalPoints'].mean(), 1))
        })
    
    # Sort by number of games (descending)
    teams_breakdown.sort(key=lambda x: x['games'], reverse=True)
    
    return {
        'games_played': int(len(player_games)),
        'avg_score': float(round(player_games['TotalPoints'].mean(), 1)),
        'fouls_per_game': float(round(player_games['TotalFouls'].mean(), 1)),
        'best_score': int(player_games['TotalPoints'].max()),
        'team': str(team),
        'player_number': int(player_number) if pd.notna(player_number) else None,
        'last_three_scores': [int(score) for score in last_three_scores],
        'teams_played_for': teams_breakdown
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
        - next_game: Dictionary with next game info (opponent, opponent_position, opponent_total_teams, date, time, is_home, location) or None
    """
    if data.empty:
        return None
    
    # Normalize team name for matching
    normalized_team_name = normalize_team_name_for_matching(team_name)
    
    # Filter games for this team (normalize data team names for comparison)
    team_games = data[
        (data['HomeTeamName'].apply(normalize_team_name_for_matching) == normalized_team_name) | 
        (data['AwayTeamName'].apply(normalize_team_name_for_matching) == normalized_team_name)
    ].copy()
    
    if team_games.empty:
        return None
    
    # Get division name from first game
    division = team_games.iloc[0]['GameDivisionDisplay']
    
    # Sort by date
    team_games = team_games.sort_values('DateTime')
    
    # Process each game
    team_games['IsHome'] = team_games['HomeTeamName'].apply(normalize_team_name_for_matching) == normalized_team_name
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
            # Normalize team names in standings for comparison
            team_row = standings[standings['Team Name'].apply(normalize_team_name_for_matching) == normalized_team_name]
            if not team_row.empty:
                # Get position (index starts at 1 in standings)
                position = team_row.index[0]
    
    # Get top 5 scorers for this team
    top_scorers = []
    player_stats = extract_all_player_stats(data)
    if not player_stats.empty:
        # Normalize team names in player stats for comparison
        team_players = player_stats[player_stats['Team'].apply(normalize_team_name_for_matching) == normalized_team_name].copy()
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
    
    # Get next game information
    next_game_info = None
    try:
        next_games = get_team_next_games(team_name, limit=1)
        if next_games and len(next_games) > 0:
            next_game = next_games[0]
            opponent = next_game.get('opponent')
            
            # Get opponent's position in standings if available
            opponent_position = None
            opponent_total_teams = None
            if opponent and division:
                standings = calculate_standings_by_division(data, division)
                if not standings.empty:
                    # Normalize opponent name for comparison
                    normalized_opponent = normalize_team_name_for_matching(opponent)
                    opponent_row = standings[standings['Team Name'].apply(normalize_team_name_for_matching) == normalized_opponent]
                    if not opponent_row.empty:
                        opponent_position = opponent_row.index[0]
                        opponent_total_teams = len(standings)
            
            next_game_info = {
                'opponent': opponent,
                'opponent_position': int(opponent_position) if opponent_position is not None else None,
                'opponent_total_teams': int(opponent_total_teams) if opponent_total_teams is not None else None,
                'date': next_game.get('date'),
                'time': next_game.get('time'),
                'is_home': next_game.get('is_home'),
                'location': next_game.get('location')
            }
    except Exception as e:
        # If there's any error getting next game info, just skip it
        # This ensures the hover box still displays other information even if next game lookup fails
        # (e.g., if gamesDB.json is missing or opponent team name doesn't match standings)
        pass
    
    return {
        'wins': int(wins) if wins is not None else 0,
        'losses': int(losses) if losses is not None else 0,
        'last_five': last_five,
        'position': int(position) if position is not None else None,
        'total_teams': int(total_teams) if total_teams is not None else None,
        'division': str(division) if division is not None else None,
        'top_scorers': top_scorers,
        'next_game': next_game_info
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
    normalized_referee_name = normalize_name_for_matching(referee_name)
    
    for idx, row in data.iterrows():
        try:
            referees = ast.literal_eval(row['Referres']) if isinstance(row['Referres'], str) else row['Referres']
            # Check for both 'RefereeName' and 'Referee Name' keys (normalize for comparison)
            if referees and any(
                normalize_name_for_matching(ref.get('RefereeName', '')) == normalized_referee_name or 
                normalize_name_for_matching(ref.get('Referee Name', '')) == normalized_referee_name
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


def _get_team_position_and_streak(data, team_name, division):
    """
    Helper function to get team position and last 5 game streak.
    
    Parameters:
    data (DataFrame): The game data
    team_name (str): The name of the team
    division (str): The division name
    
    Returns:
    dict: Dictionary containing:
        - position: Current position in division standings (None if not found)
        - total_teams: Total number of teams in division (None if not found)
        - last_five: List of results for last 5 games (W/L), empty list if no games
    """
    if data.empty or not team_name:
        return {
            'position': None,
            'total_teams': None,
            'last_five': []
        }
    
    # Normalize team name for matching
    normalized_team_name = normalize_team_name_for_matching(team_name)
    
    # Filter games for this team (normalize data team names for comparison)
    team_games = data[
        (data['HomeTeamName'].apply(normalize_team_name_for_matching) == normalized_team_name) | 
        (data['AwayTeamName'].apply(normalize_team_name_for_matching) == normalized_team_name)
    ].copy()
    
    # Get last 5 games streak
    last_five = []
    if not team_games.empty:
        # Sort by date
        team_games = team_games.sort_values('DateTime')
        
        # Process each game
        team_games['IsHome'] = team_games['HomeTeamName'].apply(normalize_team_name_for_matching) == normalized_team_name
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
        
        # Get last 5 games
        last_five = team_games.tail(5)['Result'].tolist()
    
    # Calculate position in division standings
    position = None
    total_teams = None
    if division:
        standings = calculate_standings_by_division(data, division)
        if not standings.empty:
            total_teams = int(len(standings))
            # Normalize team names in standings for comparison
            team_row = standings[standings['Team Name'].apply(normalize_team_name_for_matching) == normalized_team_name]
            if not team_row.empty:
                # Get position (standings index starts at 1)
                position = int(team_row.index[0])
    
    return {
        'position': position,
        'total_teams': total_teams,
        'last_five': last_five
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
                home_team, away_team = parse_team_names_from_url(game.get('GameUrl', ''))
                
                # Parse the date from ScheduledGameDate using the helper function
                game_date = parse_dotnet_json_date(game.get('ScheduledGameDate'))
                if not game_date:
                    game_date = 'TBD'
                
                # Get division name
                division = convert_division_name(game.get('GameDivisionName', ''))
                
                # Get position and streak for both teams
                home_team_info = _get_team_position_and_streak(data, home_team, division)
                away_team_info = _get_team_position_and_streak(data, away_team, division)
                
                # Get referees if available (currently not in gamesDB.json for future games)
                referees = []
                if 'Referees' in game and game['Referees']:
                    try:
                        referee_names = [
                            ref.get('RefereeName') or ref.get('Referee Name', 'TBD') 
                            for ref in game['Referees']
                        ] if isinstance(game['Referees'], list) else []
                        referees = referee_names
                    except:
                        referees = []
                
                return {
                    'result': f"{home_team} vs {away_team}",
                    'referees': referees,
                    'date_time': game_date,
                    'is_future': True,
                    'division': division,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_position': home_team_info['position'],
                    'home_total_teams': home_team_info['total_teams'],
                    'home_last_five': home_team_info['last_five'],
                    'away_position': away_team_info['position'],
                    'away_total_teams': away_team_info['total_teams'],
                    'away_last_five': away_team_info['last_five']
                }
    
    # Game not found in either finished or future games
    return None

def get_division_hover_stats(data, division_name):
    """
    Get basic statistics for a division to display in hover tooltip.
    
    Parameters:
    data (DataFrame): The game data
    division_name (str): The name of the division
    
    Returns:
    dict: Dictionary containing:
        - top_teams: List of top 3 teams with wins, losses, and points
        - top_scorers: List of top 3 scorers with avg score per game
        - division_name: The division name
    """
    if data.empty:
        return None
    
    # Filter games for this division
    division_games = data[data['GameDivisionDisplay'] == division_name].copy()
    
    if division_games.empty:
        return None
    
    # Calculate standings for the division
    standings = calculate_standings_by_division(data, division_name)
    
    # Get top 3 teams from standings
    top_teams = []
    if not standings.empty:
        for idx in range(min(3, len(standings))):
            team_row = standings.iloc[idx]
            top_teams.append({
                'name': team_row['Team Name'],
                'wins': team_row['Wins'],
                'losses': team_row['Losses'],
                'points': team_row.get('League Points', 0)
            })
    
    # Get top 3 scorers based on average score per game
    top_scorers = []
    player_stats = extract_all_player_stats(division_games)
    
    if not player_stats.empty:
        # Group by player name and calculate average points per game
        player_aggregates = player_stats.groupby('PlayerName').agg({
            'TotalPoints': ['sum', 'mean'],
            'GameId': 'count'
        }).reset_index()
        
        # Flatten column names
        player_aggregates.columns = ['PlayerName', 'TotalPoints', 'AvgPoints', 'GamesPlayed']
        
        # Filter players with at least 1 game
        player_aggregates = player_aggregates[player_aggregates['GamesPlayed'] >= 1]
        
        # Sort by average points descending
        player_aggregates = player_aggregates.sort_values('AvgPoints', ascending=False)
        
        # Get top 3 scorers
        for idx in range(min(3, len(player_aggregates))):
            player_row = player_aggregates.iloc[idx]
            top_scorers.append({
                'name': player_row['PlayerName'],
                'avg_score': round(player_row['AvgPoints'], 1),
                'games_played': int(player_row['GamesPlayed'])
            })
    
    return {
        'division_name': division_name,
        'top_teams': top_teams,
        'top_scorers': top_scorers
    }
