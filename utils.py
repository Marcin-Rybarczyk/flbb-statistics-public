import os
import pandas as pd
import json
from collections import defaultdict


FULL_GAME_STATS_OUTPUT_DIR = "full-game-stats-output"
CSV_FILEPATH = "full-game-stats.csv"
FORCE_TO_CREATE_CSV = True

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
    Load game data from CSV file or generate from JSON files if needed.
    """
    # Check if we should force CSV regeneration from JSON data
    root_dir = os.path.join(os.getcwd(), FULL_GAME_STATS_OUTPUT_DIR)
    
    if FORCE_TO_CREATE_CSV and os.path.exists(root_dir):
        # Force regeneration of CSV from JSON data
        all_data = load_data_from_directories(root_dir) 
        if all_data:  # Only proceed if we have JSON data
            data = pd.DataFrame(all_data)
            flatten_df(data)
            data.to_csv(CSV_FILEPATH, index=False)
            return data
    
    # Try to load existing CSV file
    if os.path.exists(CSV_FILEPATH):
        try:
            data = pd.read_csv(CSV_FILEPATH)
            # Check if the CSV has data
            if not data.empty:
                return data
            else:
                print(f"Warning: {CSV_FILEPATH} exists but is empty")
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            print(f"Warning: Error reading {CSV_FILEPATH}: {e}")
        except Exception as e:
            print(f"Warning: Unexpected error reading {CSV_FILEPATH}: {e}")
    
    # If CSV doesn't exist or failed to load, try to generate from JSON files
    if os.path.exists(root_dir):
        all_data = load_data_from_directories(root_dir) 
        if all_data:  # Only proceed if we have JSON data
            data = pd.DataFrame(all_data)
            flatten_df(data)
            data.to_csv(CSV_FILEPATH, index=False)
            return data
    
    # Return empty DataFrame if no data available
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
        return pd.DataFrame()
    
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
        return pd.DataFrame()
    
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
        home_team = game['HomeTeamName']
        away_team = game['AwayTeamName']
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
                        
                        # Check for scoring actions
                        points = 0
                        if '1P Points Added' in action:
                            points = 1
                        elif '2P Points Added' in action:
                            points = 2
                        elif '3P Points Added' in action:
                            points = 3
                        
                        if points > 0 and player_name:
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
        
        fixtures.append({
            'GameId': game_id,
            'HomeTeam': home_team,
            'AwayTeam': away_team,
            'HomeScore': home_score,
            'AwayScore': away_score,
            'DateTime': date_time,
            'Division': division,
            'Location': parse_location_name(location),  # Use the same parsing function
            'TopScorerName': top_scorer_name if top_scorer_name else 'N/A',
            'TopScorerPoints': top_scorer_points,
            'TopScorerTeam': top_scorer_team if top_scorer_team else 'N/A',
            'Referees': referee_names,
            'IsFinished': pd.notna(home_score) and pd.notna(away_score)
        })
    
    return pd.DataFrame(fixtures)

def get_all_fixtures_data(data):
    """
    Get all fixtures data with enhanced information for display.
    
    Parameters:
    data (DataFrame): The game data
    
    Returns:
    DataFrame: Enhanced fixtures data
    """
    return get_top_scorer_by_game(data)


def get_fixtures_matrix_data(data, division_filter=None):
    """
    Get fixtures data organized as a matrix (team vs team).
    
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
    
    # Get unique teams
    home_teams = set(filtered_data['HomeTeamName'].dropna())
    away_teams = set(filtered_data['AwayTeamName'].dropna())
    all_teams = sorted(home_teams.union(away_teams))
    
    # Get unique divisions for the filter dropdown
    all_divisions = sorted(data['GameDivisionDisplay'].dropna().unique())
    
    # Initialize matrix
    matrix = {}
    for home_team in all_teams:
        matrix[home_team] = {}
        for away_team in all_teams:
            matrix[home_team][away_team] = []
    
    # Populate matrix with games
    for _, game in filtered_data.iterrows():
        home_team = game['HomeTeamName']
        away_team = game['AwayTeamName']
        
        if pd.notna(home_team) and pd.notna(away_team):
            # Parse location to get just the name
            location_name = parse_location_name(game['GameLocation'])
            
            # Get enhanced game info
            game_info = {
                'game_id': game['GameId'],
                'date': game['DateTime'][:16] if pd.notna(game['DateTime']) else 'TBD',
                'home_score': game['FinalHomeScore'] if pd.notna(game['FinalHomeScore']) else None,
                'away_score': game['FinalAwayScore'] if pd.notna(game['FinalAwayScore']) else None,
                'location': location_name,
                'division': game['GameDivisionDisplay'],
                'is_finished': pd.notna(game['FinalHomeScore']) and pd.notna(game['FinalAwayScore']),
                'referees': parse_referees(game['Referres']),
                'top_scorer': get_game_top_scorer(game)
            }
            
            matrix[home_team][away_team].append(game_info)
    
    return {
        'teams': all_teams,
        'matrix': matrix,
        'divisions': all_divisions,
        'current_division': division_filter or (all_divisions[0] if all_divisions else None)
    }


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
                    
                    # Check for scoring actions
                    points = 0
                    if '1P Points Added' in action:
                        points = 1
                    elif '2P Points Added' in action:
                        points = 2
                    elif '3P Points Added' in action:
                        points = 3
                    
                    if points > 0 and player_name:
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
