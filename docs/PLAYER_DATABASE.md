# Player Database CSV Feature

## Overview
This feature automatically generates a comprehensive player database CSV file (`data/players-database.csv`) whenever game data is loaded from JSON files. The database aggregates player statistics across all games, making it easy to query and analyze individual player performance.

## When is the Player Database Created?

The player database is automatically created in the following scenarios:

1. **When loading new JSON data**: If JSON files are found in the `full-game-stats-output/` directory, the player database is created after processing the game data.

2. **When loading from backup CSV**: If loading from the backup `full-game-stats.csv` file and `FORCE_TO_CREATE_CSV` is enabled, the player database is regenerated.

## File Location

- **Path**: `data/players-database.csv`
- **Encoding**: UTF-8
- **Format**: Standard CSV with header row

## Database Structure

The player database contains **20 columns** with comprehensive player statistics:

### Identification Columns
1. **PlayerName**: Full name of the player
2. **Team**: Team name (a player may appear multiple times if they played for different teams)
3. **PlayerNumber**: Most common jersey number used by the player

### Game Participation
4. **GamesPlayed**: Total number of games the player participated in
5. **GamesStarted**: Number of games where the player was in the starting five
6. **StartingPercentage**: Percentage of games started (0-100%)

### Scoring Statistics
7. **TotalPoints**: Total points scored across all games
8. **AvgPointsPerGame**: Average points per game (rounded to 2 decimals)
9. **1PMadeShots**: Total 1-point shots made (free throws)
10. **2PMadeShots**: Total 2-point field goals made
11. **3PMadeShots**: Total 3-point field goals made
12. **TotalFieldGoalsMade**: Sum of all made shots (1P + 2P + 3P)

### Efficiency Metrics
13. **AvgShotsPerGame**: Average shots made per game
14. **PointsPerShot**: Points scored per shot made (efficiency metric, 0.0 for players with no shots)

### Foul Statistics
15. **TotalFouls**: Total fouls committed
16. **AvgFoulsPerGame**: Average fouls per game
17. **PFouls**: Personal fouls
18. **P1Fouls**: P1 type fouls
19. **P2Fouls**: P2 type fouls
20. **P3Fouls**: P3 type fouls

## Data Aggregation

- **Grouping**: Players are grouped by `PlayerName` and `Team`
- **Sorting**: Records are sorted by `TotalPoints` in descending order (highest scorers first)
- **PlayerNumber**: Uses the most common jersey number if a player used multiple numbers

## Example Usage

### Python
```python
import pandas as pd

# Load the player database
players = pd.read_csv('data/players-database.csv')

# Find top 10 scorers
top_scorers = players.head(10)

# Find players from a specific team
team_players = players[players['Team'] == 'Sparta Bertrange']

# Find most efficient shooters (min 50 shots)
efficient = players[players['TotalFieldGoalsMade'] >= 50].nlargest(10, 'PointsPerShot')

# Players with most games
most_active = players.nlargest(10, 'GamesPlayed')
```

### Command Line
```bash
# View top 10 players
head -11 data/players-database.csv | column -t -s,

# Count total players
wc -l data/players-database.csv

# Search for a specific player
grep "WILLIAMS" data/players-database.csv
```

## Function Reference

### `create_players_database(data, output_filepath=None)`

Creates a comprehensive player database CSV from game data.

**Parameters:**
- `data` (DataFrame): The game data loaded from JSON files
- `output_filepath` (str, optional): Custom output path. Defaults to `PLAYERS_DATABASE_CSV_FILEPATH`

**Returns:**
- DataFrame: The aggregated player statistics

**Example:**
```python
from src.utils import load_game_data, create_players_database

# Load game data
data = load_game_data()

# Create player database
players_db = create_players_database(data)

# Or save to custom location
players_db = create_players_database(data, 'custom/path/players.csv')
```

## Sample Output

Here's what the data looks like:

```csv
PlayerName,Team,PlayerNumber,GamesPlayed,GamesStarted,StartingPercentage,TotalPoints,AvgPointsPerGame,1PMadeShots,2PMadeShots,3PMadeShots,TotalFieldGoalsMade,AvgShotsPerGame,PointsPerShot,TotalFouls,AvgFoulsPerGame,PFouls,P1Fouls,P2Fouls,P3Fouls
WILLIAMS Jarvis Terrill,Sparta Bertrange,14,7,7,100.0,199,28.43,54,68,3,125,17.86,1.59,10,1.43,4,0,6,0
JONAITIS Robertas,Kordall Steelers,15,7,7,100.0,192,27.43,46,61,8,115,16.43,1.67,19,2.71,6,3,7,1
```

## Testing

A comprehensive test suite is available in `tests/test_player_database.py` with 5 tests:

1. **Player Database Creation**: Verifies the database can be created from game data
2. **Structure Validation**: Checks all expected columns are present with correct data types
3. **Data Integrity**: Validates logical consistency (no nulls, valid percentages, correct calculations)
4. **Statistics Calculation**: Tests and displays database statistics
5. **Raw vs Aggregated Comparison**: Ensures aggregation matches raw data totals

Run tests with:
```bash
python3 tests/test_player_database.py
```

## Performance

- **Test Dataset**: 150 games with 2,566 player-game records
- **Output**: 772 unique player records (67% reduction through aggregation)
- **Generation Time**: < 2 seconds for 150 games
- **File Size**: ~67 KB for 772 players

## Notes

- Players who played for multiple teams will have separate records for each team
- The `PointsPerShot` metric is set to 0.0 for players with no field goals made (more accurate than undefined)
- All calculated fields (averages, percentages) are rounded to 2 decimal places for readability
- The database is automatically regenerated when new game data is available

## Integration with Existing Code

The player database feature integrates seamlessly with the existing codebase:

- No breaking changes to existing functions
- Automatically called when `load_game_data()` processes new data
- Uses existing `extract_all_player_stats()` function for data extraction
- Follows the same pattern as `full-game-stats.csv` generation

## Future Enhancements

Potential improvements for future versions:

- Add season/year filtering for multi-season databases
- Include advanced metrics (PER, true shooting %, assist/turnover ratio)
- Support for incremental updates (append new players without full regeneration)
- Export to additional formats (JSON, Excel, SQLite)
- Player comparison and ranking features
