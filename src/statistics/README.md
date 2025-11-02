# FLBB Statistics Module

A modular statistics calculation package for the FLBB Basketball Statistics website. This module organizes statistics calculations into logical components for better maintainability and code organization.

## Structure

The statistics module is organized into focused sub-modules based on the type of statistics:

### Core Modules

#### `base.py`
Configuration and data loading functionality. This is the foundation module that all other modules depend on.

**Functions:**
- `get_data_source_info()` - Get information about current data source
- `load_config()` - Load configuration from JSON
- `get_season_info()` - Get season information
- `get_season_archive_filename()` - Generate archive filename
- `get_website_config()` - Get website configuration
- `load_game_data()` - Load game data (main data loading function)
- `extract_last_update_from_data()` - Extract last update timestamp
- Helper functions for JSON loading and data flattening

**Key Features:**
- Prioritizes new data from JSON files over repository CSV backup
- UTF-8 BOM handling for international characters
- Caching for configuration data
- Automatic CSV backup generation

---

#### `player_stats.py`
Individual player performance statistics including scoring, shooting efficiency, and fouls.

**Functions:**
- `extract_all_player_stats(data)` - Extract all player stats from nested Teams data
- `get_top_scorers(data, top_n=20)` - Top N scorers across all games
- `get_highest_single_game_score(data, top_n=10)` - Highest single game performances
- `get_player_shooting_efficiency(data, top_n=20)` - Shooting efficiency metrics
- `get_starting_five_vs_bench_stats(data)` - Compare starters vs bench players
- `get_double_digit_scorers(data, min_points=10)` - Players with double-digit games
- `get_consistent_scorers(data, min_games=5)` - Most consistent scorers
- `get_top_three_pointers(data, top_n=10)` - Top three-point shooters
- `get_top_foulers(data, top_n=10)` - Players with most fouls
- `get_top_players_by_score(data, top_n=50)` - Top players by average score

**Key Features:**
- Comprehensive player performance metrics
- Game-by-game and aggregated statistics
- Efficiency calculations (points per shot, consistency scores)
- Support for filtering by minimum games played

---

#### `team_stats.py`
Team performance statistics including standings, win/loss records, and scoring.

**Functions:**
- `calculate_standings(df)` - Calculate standings from game data
- `calculate_standings_by_division(data, division_name)` - Division-specific standings
- `get_team_performance_stats(data)` - Comprehensive team performance
- `get_highest_scoring_games(data, top_n=10)` - Games with highest total scores

**Key Features:**
- Win/loss records with points system
- Points differential calculations
- Home and away game statistics
- Division-based filtering

---

#### `referee_stats.py`
Referee performance statistics including games officiated and fouls called.

**Functions:**
- `extract_referee_stats(data)` - Extract referee stats from game data
- `get_referee_statistics(data)` - Comprehensive referee statistics
- `get_referee_fouls_per_game(data)` - Referees sorted by fouls per game
- `get_referees_least_fouls_per_game(data)` - Referees with least fouls per game

**Key Features:**
- Games officiated tracking
- Fouls called analysis
- Minimum game thresholds for meaningful statistics

---

#### `game_analysis.py`
Game event analysis including ties, lead changes, and win margins.

**Functions:**
- `analyze_game_events(data)` - Analyze game events for ties, leads, etc.
- `get_most_tie_scores(data, top_n=10)` - Games with most tie scores
- `get_most_lead_changes(data, top_n=10)` - Games with most lead changes
- `get_biggest_leads(data, top_n=10)` - Games with biggest leads
- `get_biggest_wins(data, top_n=10)` - Games with biggest win margins

**Key Features:**
- Real-time game event tracking
- Lead change detection
- Maximum lead calculations
- Win margin analysis

---

### Delegated Modules

These modules currently wrap functions from `utils.py` for backward compatibility. They will be fully refactored in future updates.

#### `advanced_analysis.py`
Advanced statistical analysis including player impact and combinations.

**Functions:**
- `get_player_game_impact_analysis(data, top_n=20)` - Player impact on game outcomes
- `get_player_foul_impact_analysis(data, top_n=20)` - Foul impact analysis
- `get_best_player_combinations(data, min_games=3)` - Best player pairings
- `get_referee_game_impact_analysis(data)` - Referee impact on games

---

#### `fixtures.py`
Fixtures and game schedule management.

**Functions:**
- `get_all_fixtures_data(data)` - Get all fixtures
- `get_fixtures_matrix_data(data, division_filter=None)` - Matrix view of fixtures
- `parse_location_name(location_data)` - Parse location data
- `parse_referees(referees_data)` - Parse referee data
- `get_game_top_scorer(game)` - Get top scorer for a game
- `get_top_scorer_by_game(data)` - Top scorer for each game

---

#### `archive.py`
Season archive management for data backup and import.

**Functions:**
- `validate_season_archive(zip_filepath)` - Validate archive file
- `import_season_archive(zip_filepath, target_season_dir=None)` - Import archive
- `list_available_archives(archive_dir='.')` - List available archives

---

## Usage

### In Flask Application

```python
from src.statistics import (
    # Base functions
    load_game_data, get_season_info,
    # Player statistics
    get_top_scorers, get_player_shooting_efficiency,
    # Team statistics
    calculate_standings_by_division, get_team_performance_stats,
    # And other functions as needed...
)

# Load data
data = load_game_data()

# Get statistics
top_scorers = get_top_scorers(data, 20)
standings = calculate_standings_by_division(data, "M-Division 1:")
```

### Data Flow

1. **Data Loading**: `load_game_data()` from `base.py`
   - Tries JSON files first (live data)
   - Falls back to CSV backup
   - Returns pandas DataFrame

2. **Statistics Calculation**: Import specific functions
   - All functions accept DataFrame as input
   - Return processed DataFrames or dicts
   - Handle empty data gracefully

3. **Web Display**: Pass to Flask templates
   - Statistics returned as DataFrames for easy templating
   - Jinja2 templates iterate over results

---

## Data Structure

### Input Data (DataFrame)
The main data structure is a pandas DataFrame with columns:
- `GameId` - Unique game identifier
- `HomeTeamName`, `AwayTeamName` - Team names
- `FinalHomeScore`, `FinalAwayScore` - Final scores
- `GameDivisionDisplay` - Division name
- `DateTime` - Game date/time
- `Teams` - Nested team/player data (for player stats)
- `GameEvents` - Nested event data (for game analysis)
- `Referres` - Referee data

### Output Data
Most functions return pandas DataFrames with relevant statistics:
- Column names are descriptive (e.g., `TotalPoints`, `AvgPointsPerGame`)
- Sorted by relevant metric (usually descending)
- Limited to top N results where applicable

---

## Testing

Run tests using the test script:

```bash
# Run all tests
python3 tests/test_local_flask.py --test-only

# Start development server
python3 tests/test_local_flask.py

# Start production-like server
python3 tests/test_local_flask.py --production
```

---

## Future Enhancements

### Planned Refactoring
- Move advanced analysis functions from utils.py to `advanced_analysis.py`
- Move fixtures functions from utils.py to `fixtures.py`
- Move archive functions from utils.py to `archive.py`

### Potential New Modules
- `comparisons.py` - Team vs team, player vs player comparisons
- `trends.py` - Temporal analysis and trends
- `predictions.py` - Predictive analytics (if ML is added)
- `visualizations.py` - Data visualization helpers

---

## Contributing

When adding new statistics:

1. **Choose the right module** based on statistic type
2. **Follow naming conventions**: `get_<statistic_name>(data, ...)`
3. **Handle empty data**: Check `if data.empty` and return appropriate default
4. **Add docstrings**: Include parameters, return type, and description
5. **Update `__init__.py`**: Add function to exports
6. **Write tests**: Ensure function works with sample data
7. **Update documentation**: Add function to this README

---

## Module Dependencies

```
base.py (no dependencies)
├── player_stats.py
├── team_stats.py
├── referee_stats.py
├── game_analysis.py
├── advanced_analysis.py (→ utils.py temporarily)
├── fixtures.py (→ utils.py temporarily)
└── archive.py (→ utils.py temporarily)
```

---

## Notes

- All statistics functions accept a pandas DataFrame as the first parameter
- Functions return DataFrames, dicts, or scalars depending on the statistic
- Empty data is handled gracefully (returns empty DataFrame or appropriate default)
- UTF-8 encoding with BOM handling for international player/team names
- Configuration is cached to avoid repeated file reads

---

## License

Same as parent project.
