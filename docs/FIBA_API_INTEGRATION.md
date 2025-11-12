# FIBA API Integration Documentation

This document provides comprehensive information about the FIBA API integration in the FLBB Statistics application.

## Overview

The FIBA API integration enables access to extended player data and international game statistics from the International Basketball Federation (FIBA). This enriches the existing FLBB (Luxembourg Basketball Federation) data with international player profiles, career statistics, and national team game information.

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [API Endpoints](#api-endpoints)
7. [Player Data Enrichment](#player-data-enrichment)
8. [Caching System](#caching-system)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)

## Features

### Core Capabilities

- **Player Information Retrieval**: Access detailed player profiles from FIBA database
- **Competition Data**: Retrieve information about FIBA competitions including Luxembourg teams
- **Game Statistics**: Access game-level statistics for international matches
- **Player Enrichment**: Automatically enhance FLBB player data with FIBA information
- **National Team Data**: Get Luxembourg national team rosters and game results
- **Caching System**: Local caching to minimize API calls and improve performance

### Extended Player Data

When a player is enriched with FIBA data, the following additional information becomes available:

- **FIBA Player ID**: Unique identifier in FIBA system
- **Profile URL**: Link to official FIBA player profile
- **Birth Date**: Player's date of birth
- **Height**: Height in centimeters
- **Weight**: Weight in kilograms
- **Position**: Official playing position
- **Nationality**: Player's nationality
- **International Caps**: Number of national team appearances
- **FIBA Career Statistics**: Career totals from FIBA competitions

## Architecture

### Components

The FIBA integration consists of three main components:

1. **`fiba_api_client.py`** - Core API client for making requests to FIBA endpoints
2. **`fiba_integration.py`** - Integration layer for enriching FLBB data with FIBA information
3. **Configuration** - Settings in `scripts/config.json` to control integration behavior

### FIBA API Endpoints

The integration uses multiple FIBA data sources:

1. **FIBA LiveStats API** (Genius Sports)
   - Base URL: `https://fibalivestats.dcd.shared.geniussports.com`
   - Provides live and historical game data
   - Player statistics and game-by-game breakdowns

2. **FIBA SportResult Cache**
   - Base URL: `https://livecache.sportresult.com/node/db/FIBASTATS`
   - Structured JSON data for competitions and players
   - Efficient access to historical data

3. **FIBA Official Website**
   - Base URL: `https://www.fiba.basketball`
   - General competition information
   - Player search and profile access

## Installation

### Prerequisites

The FIBA integration requires the following Python packages:

```bash
pip install requests>=2.32.3
pip install pandas>=2.3.2
```

These are included in the project's `requirements.txt` file.

### Installation Steps

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. The FIBA integration modules are located in the `src/` directory:
   - `src/fiba_api_client.py`
   - `src/fiba_integration.py`

3. Configuration is automatically loaded from `scripts/config.json`

## Configuration

### Configuration File

The FIBA integration is configured in `scripts/config.json`:

```json
{
  "fiba": {
    "enabled": true,
    "api_key": "",
    "timeout": 30,
    "cache_enabled": true,
    "endpoints": {
      "livestats": "https://fibalivestats.dcd.shared.geniussports.com",
      "sportresult": "https://livecache.sportresult.com/node/db/FIBASTATS",
      "official": "https://www.fiba.basketball"
    },
    "luxembourg": {
      "country_code": "LUX",
      "fiba_zone": "E",
      "enrich_player_data": true
    }
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable FIBA integration |
| `api_key` | string | `""` | FIBA API key (if required) |
| `timeout` | integer | `30` | Request timeout in seconds |
| `cache_enabled` | boolean | `true` | Enable local caching of API responses |
| `luxembourg.country_code` | string | `"LUX"` | Luxembourg's FIBA country code |
| `luxembourg.fiba_zone` | string | `"E"` | FIBA zone (E = Europe) |
| `luxembourg.enrich_player_data` | boolean | `true` | Auto-enrich player data |

### Environment Variables

You can also configure the FIBA API key via environment variable:

```bash
export FIBA_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage

#### 1. Import and Initialize

```python
from src.fiba_api_client import FIBAAPIClient
from src.fiba_integration import FIBAPlayerEnrichment

# Create API client
client = FIBAAPIClient()

# Or use factory function with config
from src.fiba_api_client import create_fiba_client
client = create_fiba_client(config)
```

#### 2. Search for Players

```python
# Search for Luxembourg players
players = client.search_players("Felix", country_code="LUX")

# Get all Luxembourg national team players
lux_players = client.get_luxembourg_players()
```

#### 3. Get Player Information

```python
# Get detailed player info by ID
player_info = client.get_player_info("player_fiba_id")
```

#### 4. Get Competition Data

```python
# Get all European competitions
competitions = client.get_competitions(zone="E")

# Get Luxembourg-specific competitions
lux_competitions = client.get_luxembourg_competitions(season="2025-2026")
```

#### 5. Get Game Statistics

```python
# Get stats for a specific game
game_stats = client.get_game_stats("game_id")

# Get player stats for a specific game
player_game_stats = client.get_player_game_stats("game_id", "player_id")
```

### Player Data Enrichment

#### Command-Line Interface

Enrich the player database using the CLI:

```bash
# Enrich player database with default settings
python src/fiba_integration.py --input data/players-database.csv --output data/players-database-enriched.csv

# Show enrichment statistics
python src/fiba_integration.py --stats
```

#### Programmatic Usage

```python
from src.fiba_integration import FIBAPlayerEnrichment, load_config_for_fiba
import pandas as pd

# Load configuration
config = load_config_for_fiba()

# Create enrichment instance
enrichment = FIBAPlayerEnrichment(config)

# Enrich a single player
player_data = {
    'PlayerName': 'KLOMAN Felix Whitcomb',
    'Team': 'AS Soleuvre',
    'TotalPoints': 244,
    'GamesPlayed': 8
}

enriched_data = enrichment.enrich_player('KLOMAN Felix Whitcomb', player_data)

# Enrich entire DataFrame
df = pd.read_csv('data/players-database.csv', encoding='utf-8-sig')
enriched_df = enrichment.enrich_players_dataframe(df, player_name_column='PlayerName')

# Save enriched data
enriched_df.to_csv('data/players-database-enriched.csv', index=False, encoding='utf-8-sig')
```

#### Get Extended Player Profile

```python
# Get comprehensive player profile
profile = enrichment.get_player_extended_profile('KLOMAN Felix Whitcomb')

if profile:
    print(f"Player ID: {profile.get('id')}")
    print(f"Height: {profile.get('height_cm')} cm")
    print(f"Position: {profile.get('position')}")
    print(f"International Caps: {profile.get('caps', 0)}")
```

## API Endpoints

### Player Endpoints

| Method | Description | Parameters |
|--------|-------------|------------|
| `get_player_info(player_id)` | Get detailed player information | `player_id`: FIBA player ID |
| `search_players(name, country_code)` | Search for players by name | `name`: Player name<br>`country_code`: Optional country filter |
| `get_luxembourg_players()` | Get all Luxembourg players | None |

### Competition Endpoints

| Method | Description | Parameters |
|--------|-------------|------------|
| `get_competitions(zone, season)` | Get list of competitions | `zone`: Optional zone filter (e.g., 'E')<br>`season`: Optional season filter |
| `get_luxembourg_competitions(season)` | Get Luxembourg competitions | `season`: Optional season filter |

### Game Endpoints

| Method | Description | Parameters |
|--------|-------------|------------|
| `get_game_stats(game_id)` | Get game statistics | `game_id`: FIBA game ID |
| `get_player_game_stats(game_id, player_id)` | Get player stats for game | `game_id`: FIBA game ID<br>`player_id`: FIBA player ID |
| `get_national_team_games(country_code, season)` | Get national team games | `country_code`: Country code<br>`season`: Optional season filter |

### Team Endpoints

| Method | Description | Parameters |
|--------|-------------|------------|
| `get_team_roster(team_id, competition_id)` | Get team roster | `team_id`: FIBA team ID<br>`competition_id`: Optional competition filter |

### Enrichment Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `enrich_player_data(player_name, flbb_data)` | Enrich FLBB data with FIBA info | `player_name`: Player's name<br>`flbb_data`: Existing FLBB data dict |

## Player Data Enrichment

### Enrichment Process

1. **Search**: Player name is searched in FIBA database by name and country code
2. **Match**: Best matching player is identified
3. **Retrieve**: Additional FIBA data is retrieved for the matched player
4. **Merge**: FIBA data is merged with existing FLBB data
5. **Cache**: Result is cached for future use

### Enriched Data Fields

When a player is successfully enriched, the following fields are added:

```python
{
    'fiba_id': 'unique_fiba_identifier',
    'fiba_profile_url': 'https://www.fiba.basketball/player/...',
    'birth_date': '1995-03-15',
    'height_cm': 198,
    'weight_kg': 95,
    'position': 'Forward',
    'nationality': 'Luxembourg',
    'international_caps': 25,
    'fiba_career_stats': {
        'games': 45,
        'points': 567,
        'rebounds': 234,
        # ... additional stats
    },
    'has_fiba_data': True
}
```

### Handling Players Without FIBA Data

If a player is not found in FIBA database:

```python
{
    # Original FLBB data remains unchanged
    'has_fiba_data': False
}
```

## Caching System

### Cache Overview

The FIBA API client includes a built-in caching system to:
- Reduce API calls and improve performance
- Work offline with previously fetched data
- Respect API rate limits

### Cache Configuration

```python
client = FIBAAPIClient(cache_enabled=True)
```

### Cache Location

Cache files are stored in:
```
data/fiba_cache/
```

Each API response is cached as a JSON file with a unique hash-based filename.

### Cache Duration

- Default cache lifetime: 24 hours
- After 24 hours, data is refreshed from API on next request

### Cache Management

```python
# Get cache statistics
cache_stats = client.get_cache_stats()
print(f"Total cached files: {cache_stats['total_files']}")
print(f"Cache size: {cache_stats['total_size_mb']} MB")

# Clear entire cache
client.clear_cache()
```

## Examples

### Example 1: Enrich Player Database

```python
from src.fiba_integration import FIBAPlayerEnrichment, load_config_for_fiba
import pandas as pd

# Load configuration
config = load_config_for_fiba()

# Create enrichment instance
enrichment = FIBAPlayerEnrichment(config)

# Load player database
df = pd.read_csv('data/players-database.csv', encoding='utf-8-sig')

# Enrich all players
enriched_df = enrichment.enrich_players_dataframe(df)

# Filter players with FIBA data
with_fiba = enriched_df[enriched_df['has_fiba_data'] == True]

print(f"Total players: {len(df)}")
print(f"Players with FIBA data: {len(with_fiba)}")

# Save enriched database
enriched_df.to_csv('data/players-database-enriched.csv', index=False, encoding='utf-8-sig')
```

### Example 2: Get Luxembourg National Team Games

```python
from src.fiba_api_client import FIBAAPIClient

client = FIBAAPIClient()

# Get Luxembourg national team games for current season
games = client.get_national_team_games(country_code='LUX', season='2025-2026')

for game in games:
    print(f"{game['date']}: {game['home_team']} vs {game['away_team']}")
    print(f"Score: {game['home_score']}-{game['away_score']}")
    print()
```

### Example 3: Search and Display Player Info

```python
from src.fiba_api_client import FIBAAPIClient

client = FIBAAPIClient()

# Search for a player
players = client.search_players("Felix", country_code="LUX")

for player in players:
    print(f"Name: {player.get('name')}")
    print(f"Position: {player.get('position')}")
    print(f"Height: {player.get('height_cm')} cm")
    print(f"International Caps: {player.get('caps', 0)}")
    print(f"Profile: {player.get('profile_url')}")
    print("-" * 40)
```

### Example 4: CLI Usage

```bash
# Show help
python src/fiba_integration.py --help

# Enrich player database
python src/fiba_integration.py \
    --input data/players-database.csv \
    --output data/players-database-enriched.csv \
    --player-column PlayerName

# Show enrichment statistics
python src/fiba_integration.py --stats
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'requests'`

**Solution**: Install required dependencies
```bash
pip install -r requirements.txt
```

#### 2. API Connection Errors

**Problem**: `Failed to resolve 'www.fiba.basketball'`

**Solution**: 
- Check internet connection
- Verify FIBA endpoints are accessible
- Check firewall settings
- Use cached data if available

#### 3. No FIBA Data Found

**Problem**: Players show `has_fiba_data: False`

**Solution**:
- Player may not be in FIBA database (only national team or international players)
- Name spelling may differ between FLBB and FIBA databases
- Try manual search to verify player exists in FIBA

#### 4. Configuration Not Loading

**Problem**: FIBA integration not working

**Solution**:
- Verify `scripts/config.json` contains FIBA section
- Check `fiba.enabled` is set to `true`
- Verify configuration file syntax is valid JSON

### Testing

Run the integration tests:

```bash
python tests/test_fiba_integration.py
```

This will verify:
- Module imports work correctly
- FIBA client can be initialized
- Configuration is loaded properly
- Player database structure is compatible
- Cache system functions correctly

### Debug Mode

Enable verbose output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from src.fiba_api_client import FIBAAPIClient
client = FIBAAPIClient()
```

## Limitations

### Current Limitations

1. **Domestic Games**: FIBA APIs primarily cover international competitions, not domestic league games
2. **Player Coverage**: Only players who have participated in FIBA competitions have profiles
3. **API Access**: Some endpoints may require authentication or have rate limits
4. **Data Accuracy**: Player name matching between FLBB and FIBA may not be perfect
5. **Real-time Data**: FIBA data may not be updated in real-time

### Scope

The FIBA integration is designed to:
- ✅ Enrich player profiles with international data
- ✅ Access Luxembourg national team information
- ✅ Retrieve data from FIBA Europe competitions
- ❌ Replace FLBB domestic league data
- ❌ Provide real-time live scoring
- ❌ Access all historical game data

## Future Enhancements

Planned improvements:

1. **Automated Player Matching**: Improved algorithm for matching FLBB and FIBA player names
2. **Batch Processing**: Optimize enrichment for large player databases
3. **Live Updates**: Real-time updates during national team games
4. **Additional Stats**: More detailed career statistics and achievements
5. **Multi-language Support**: Support for player names in different languages
6. **Web Interface**: Integration with Flask application for displaying FIBA data

## Support

For issues, questions, or contributions:

1. Check this documentation
2. Run the test suite: `python tests/test_fiba_integration.py`
3. Review the code comments in `src/fiba_api_client.py` and `src/fiba_integration.py`
4. Create an issue on GitHub with detailed information

## License

This FIBA integration is part of the FLBB Statistics project and follows the same MIT License.

---

**Note**: This integration uses publicly available FIBA data. For official FIBA API access or commercial use, please contact FIBA directly.
