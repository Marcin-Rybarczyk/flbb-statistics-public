"""
Base Module - Configuration and Data Loading

This module contains core functionality for loading configuration,
managing data sources, and loading game data.
"""

import os
import pandas as pd
import json
from datetime import datetime


# Constants
FULL_GAME_STATS_OUTPUT_DIR = "full-game-stats-output"
CSV_FILEPATH = "data/full-game-stats.csv"
FORCE_TO_CREATE_CSV = True

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
    list: A list of data dictionaries from all files.
    """
    all_data = []
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(subdir, file)
            data = load_json_data_with_bom_handling(file_path)
            if data:
                all_data.append(data)
    print(f"Total files loaded: {len(all_data)}")
    return all_data


def flatten_df(df):
    """
    Flatten nested 'Teams' and 'Players' data in the DataFrame.
    
    Parameters:
    df (DataFrame): The input DataFrame with nested data
    
    Returns:
    None: Modifies the DataFrame in place
    """
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
                csv_date = datetime.fromtimestamp(csv_mod_time).strftime("%Y-%m-%d %H:%M:%S")
                
                last_update = extract_last_update_from_data(data)
                _data_source_info = {
                    'source': 'backup_csv',
                    'last_update': last_update or csv_date,
                    'source_description': f'Repository backup CSV (file modified: {csv_date})'
                }
                
                print(f"⚠️  Using backup data: {len(data)} games loaded from repository CSV")
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
