# FIBA API Integration - Quick Start Guide

This guide helps you get started with the FIBA API integration that was added to access extended player data for Luxembourg basketball games.

## What Was Added?

The FIBA (International Basketball Federation) API integration enables access to:

- **Extended Player Profiles**: Height, weight, position, birth date from FIBA database
- **National Team Data**: Luxembourg national team rosters and game results
- **International Statistics**: Career stats from FIBA competitions
- **Player Enrichment**: Automatic enhancement of FLBB data with FIBA information

## Quick Start

### 1. Understand the Structure

Three new modules were added:

```
src/
├── fiba_api_client.py      # Core FIBA API client
└── fiba_integration.py     # Player data enrichment

tests/
└── test_fiba_integration.py # Test suite

examples/
└── fiba_api_usage.py       # Usage examples

docs/
└── FIBA_API_INTEGRATION.md # Full documentation
```

### 2. Run the Tests

Verify everything works:

```bash
python tests/test_fiba_integration.py
```

Expected output: `Total: 5/5 tests passed ✓`

### 3. Try the Examples

Run the usage examples:

```bash
python examples/fiba_api_usage.py
```

This demonstrates:
- Creating FIBA API client
- Searching for players
- Enriching player data
- Getting national team information
- Cache management

### 4. Enrich Your Player Database

Use the command-line tool:

```bash
# Enrich player database with FIBA data
python src/fiba_integration.py \
  --input data/players-database.csv \
  --output data/players-database-enriched.csv

# View enrichment statistics
python src/fiba_integration.py --stats
```

### 5. Use in Your Code

```python
from src.fiba_integration import FIBAPlayerEnrichment, load_config_for_fiba

# Load configuration
config = load_config_for_fiba()

# Create enrichment instance
enrichment = FIBAPlayerEnrichment(config)

# Enrich a player
player_data = {'PlayerName': 'John Doe', 'Team': 'ABC', 'TotalPoints': 100}
enriched = enrichment.enrich_player('John Doe', player_data)

# Check if FIBA data was found
if enriched.get('has_fiba_data'):
    print(f"Height: {enriched['height_cm']} cm")
    print(f"Position: {enriched['position']}")
    print(f"International Caps: {enriched['international_caps']}")
```

## Configuration

FIBA settings are in `scripts/config.json`:

```json
{
  "fiba": {
    "enabled": true,
    "api_key": "",
    "timeout": 30,
    "cache_enabled": true,
    "luxembourg": {
      "country_code": "LUX",
      "fiba_zone": "E",
      "enrich_player_data": true
    }
  }
}
```

### Optional: Add API Key

If you have a FIBA API key, add it to the config or set environment variable:

```bash
export FIBA_API_KEY="your-api-key-here"
```

## Understanding the Results

### Players WITH FIBA Data

When a player is found in FIBA database, you'll get:

```python
{
    'PlayerName': 'Sample Player',
    'Team': 'Sample Team',
    # ... existing FLBB data ...
    
    # New FIBA data:
    'fiba_id': 'ABC123',
    'fiba_profile_url': 'https://www.fiba.basketball/player/ABC123',
    'birth_date': '1995-03-15',
    'height_cm': 198,
    'weight_kg': 95,
    'position': 'Forward',
    'nationality': 'Luxembourg',
    'international_caps': 25,
    'fiba_career_stats': { ... },
    'has_fiba_data': True
}
```

### Players WITHOUT FIBA Data

For players not in FIBA database (domestic-only players):

```python
{
    'PlayerName': 'Domestic Player',
    'Team': 'Local Team',
    # ... existing FLBB data unchanged ...
    'has_fiba_data': False
}
```

This is normal - FIBA database contains primarily:
- National team players
- Players in FIBA international competitions
- Players in FIBA Europe events

Most domestic league players won't have FIBA data.

## Caching System

The integration includes a caching system:

- **Location**: `data/fiba_cache/`
- **Duration**: 24 hours per cached response
- **Benefits**: Faster access, fewer API calls, offline capability

View cache status:

```python
from src.fiba_api_client import FIBAAPIClient

client = FIBAAPIClient()
stats = client.get_cache_stats()
print(f"Cache files: {stats['total_files']}")
print(f"Cache size: {stats['total_size_mb']} MB")
```

Clear cache:

```python
client.clear_cache()
```

## Common Use Cases

### Use Case 1: Find Luxembourg National Team Players

```python
from src.fiba_api_client import FIBAAPIClient

client = FIBAAPIClient()
players = client.get_luxembourg_players()

for player in players:
    print(f"{player['name']} - {player['position']}")
```

### Use Case 2: Search for Specific Player

```python
from src.fiba_api_client import FIBAAPIClient

client = FIBAAPIClient()
results = client.search_players("Felix", country_code="LUX")

if results:
    player = results[0]
    print(f"Found: {player['name']}")
    print(f"Position: {player['position']}")
    print(f"Height: {player['height_cm']} cm")
```

### Use Case 3: Get National Team Games

```python
from src.fiba_api_client import FIBAAPIClient

client = FIBAAPIClient()
games = client.get_national_team_games(
    country_code='LUX',
    season='2025-2026'
)

for game in games:
    print(f"{game['date']}: {game['home_team']} vs {game['away_team']}")
```

### Use Case 4: Batch Enrich Players from DataFrame

```python
import pandas as pd
from src.fiba_integration import FIBAPlayerEnrichment, load_config_for_fiba

# Load data
df = pd.read_csv('data/players-database.csv', encoding='utf-8-sig')

# Enrich
config = load_config_for_fiba()
enrichment = FIBAPlayerEnrichment(config)
enriched_df = enrichment.enrich_players_dataframe(df)

# Filter players with FIBA data
with_fiba = enriched_df[enriched_df['has_fiba_data'] == True]
print(f"{len(with_fiba)} players have FIBA data")

# Save
enriched_df.to_csv('output.csv', index=False, encoding='utf-8-sig')
```

## Troubleshooting

### Problem: "No module named 'requests'"

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Problem: Network/DNS errors when accessing FIBA APIs

**Solution**: This is normal if:
- You don't have internet access
- FIBA endpoints are blocked
- Running in restricted environment

The code handles this gracefully by:
- Returning empty results
- Using cached data if available
- Setting `has_fiba_data: False`

### Problem: All players show `has_fiba_data: False`

**Possible reasons**:
1. Players are domestic-only (not in FIBA database) - This is normal
2. No internet access to FIBA APIs
3. Name spelling differs between FLBB and FIBA

**Check**: Try searching manually for a known national team player

### Problem: Import errors

**Solution**: Make sure you're running from the project root:
```bash
cd /path/to/flbb-statistics-public
python examples/fiba_api_usage.py
```

## Need More Help?

1. **Full Documentation**: See `docs/FIBA_API_INTEGRATION.md`
2. **Examples**: Run `python examples/fiba_api_usage.py`
3. **Tests**: Run `python tests/test_fiba_integration.py`
4. **Code**: Review `src/fiba_api_client.py` and `src/fiba_integration.py`

## Next Steps

Now that you have FIBA integration:

1. **Try enriching your player database** to see which players have FIBA data
2. **Explore national team data** for Luxembourg basketball
3. **Integrate with Flask app** to display FIBA data in the web interface
4. **Create reports** combining FLBB domestic and FIBA international stats

## Summary

✅ FIBA API integration is ready to use  
✅ All tests passing (5/5)  
✅ Comprehensive documentation available  
✅ Examples provided for common use cases  
✅ Caching system for performance  
✅ Graceful handling of errors and missing data  

The integration enhances your FLBB statistics with international player data while maintaining backward compatibility with existing code.

---

**Questions?** Check the full documentation at `docs/FIBA_API_INTEGRATION.md`
