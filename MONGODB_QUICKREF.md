# MongoDB Integration Quick Reference

## Overview
This integration adds MongoDB support to PowerShell data collection scripts for game data storage and deduplication.

## Files Added/Modified

### New Files Created
1. **`scripts/mongodb_helper.ps1`** - PowerShell module with MongoDB functions
2. **`scripts/mongodb_powershell_bridge.py`** - Python CLI bridge for PowerShell
3. **`MONGODB_SETUP.md`** - Complete setup and usage documentation
4. **`mongodb_schema.json`** - MongoDB collection schema definition
5. **`examples/mongodb_integration_example.ps1`** - PowerShell usage examples
6. **`tests/test_mongodb_powershell_integration.py`** - Test suite (7 tests)

### Modified Files
1. **`scripts/download-controller.ps1`** - Added MongoDB deduplication checks
2. **`scripts/extract-game.ps1`** - Added MongoDB storage after parsing

## Quick Start

### 1. Enable MongoDB (Optional)

```powershell
# Set environment variables
$env:MONGODB_ENABLED = "true"
$env:MONGODB_URI = "mongodb://localhost:27017/"
$env:MONGODB_DATABASE = "flbb-statistics"
```

### 2. Install Dependencies

```bash
pip install pymongo
```

### 3. Test Connection

```powershell
# PowerShell
. "scripts\mongodb_helper.ps1"
Test-MongoDBConnection

# Python
python scripts/mongodb_powershell_bridge.py test-connection
```

## PowerShell Functions

### Test-MongoDBEnabled
Check if MongoDB is enabled and available.
```powershell
if (Test-MongoDBEnabled) {
    Write-Host "MongoDB is ready"
}
```

### Test-MongoDBConnection
Test MongoDB connection.
```powershell
Test-MongoDBConnection
```

### Test-GameInMongoDB
Check if a game exists with specific status.
```powershell
$exists = Test-GameInMongoDB -GameId "12345" -Status "finished"
if ($exists) {
    Write-Host "Game already processed"
}
```

### Set-GameInMongoDB
Store or update a game in MongoDB.
```powershell
Set-GameInMongoDB -GameId "12345" -JsonFilePath "path/to/game.json" -Status "finished" -CsvGenerated $false
```

### Get-GamesFromMongoDB
Query games by criteria.
```powershell
# All finished games
$games = Get-GamesFromMongoDB -Status "finished"

# Games by division
$games = Get-GamesFromMongoDB -Division "Division 1 Hommes"

# Games by season
$games = Get-GamesFromMongoDB -Season "2025-2026"
```

### Get-MongoDBGameCount
Get total game count.
```powershell
$count = Get-MongoDBGameCount
Write-Host "Total games: $count"
```

## Python Bridge Commands

### Test Connection
```bash
python scripts/mongodb_powershell_bridge.py test-connection
```

### Check if Game Exists
```bash
python scripts/mongodb_powershell_bridge.py check-game --game-id 12345 --status finished
# Exit code 0 = exists, 1 = not found, 2 = error
```

### Insert/Update Game
```bash
python scripts/mongodb_powershell_bridge.py upsert-game \
  --game-id 12345 \
  --json-file path/to/game.json \
  --status finished \
  --csv-generated false
```

### Query Games
```bash
# All finished games (returns JSON)
python scripts/mongodb_powershell_bridge.py query-games --status finished

# By division
python scripts/mongodb_powershell_bridge.py query-games --division "Division 1 Hommes"

# By season
python scripts/mongodb_powershell_bridge.py query-games --season "2025-2026"
```

### Count Games
```bash
python scripts/mongodb_powershell_bridge.py count-games
```

## Integration Workflow

### Download Phase (download-controller.ps1)
1. Script checks if game exists in MongoDB with status 'finished'
2. If exists → skip download (deduplication)
3. If not exists → download HTML

### Extraction Phase (extract-game.ps1)
1. Parse HTML to JSON
2. Save JSON to disk
3. Store in MongoDB with status='finished', csv_generated=false

### CSV Generation Phase (separate or parallel)
1. Query all finished games from MongoDB
2. Generate CSV from JSON data
3. Update csv_generated=true

## MongoDB Collection Schema

**Collection Name:** `games`

**Key Fields:**
- `GameId` (String, unique) - Game identifier
- `status` (String) - "pending" or "finished"
- `csv_generated` (Boolean) - CSV generation flag
- `json_data` (Object) - Full game statistics
- `SeasonId` (String) - Season identifier
- `GameDivisionDisplay` (String) - Division name

**Indexes:**
- GameId (unique)
- status
- GameDivisionDisplay
- SeasonId

See `mongodb_schema.json` for complete schema.

## Deduplication Logic

1. **Before Download:** Check if `GameId` exists with `status: "finished"`
2. **If Found:** Skip download and processing
3. **If Not Found:** Process game normally
4. **After Processing:** Set `status: "finished"` in MongoDB

This prevents re-downloading and re-processing completed games.

## Configuration Options

### Environment Variables
```bash
MONGODB_ENABLED=true          # Enable MongoDB (default: false)
MONGODB_URI=mongodb://...     # Connection string
MONGODB_DATABASE=flbb-stats   # Database name
```

### Connection Strings

**Local MongoDB:**
```
mongodb://localhost:27017/
```

**MongoDB Atlas (Cloud):**
```
mongodb+srv://user:pass@cluster.mongodb.net/
```

**With Authentication:**
```
mongodb://username:password@host:27017/
```

## Parallel Processing Example

```powershell
# Enable parallel processing with MongoDB

# Phase 1: Download and parse (can run in parallel)
$games | ForEach-Object -Parallel {
    $gameId = $_.GameId
    
    # Skip if already finished
    if (-not (Test-GameInMongoDB -GameId $gameId -Status "finished")) {
        Download-and-Parse-Game -GameId $gameId
        Set-GameInMongoDB -GameId $gameId -JsonFilePath $json -Status "finished"
    }
} -ThrottleLimit 10

# Phase 2: Generate CSV (can run independently)
$allGames = Get-GamesFromMongoDB -Status "finished"
Generate-CSV -Games $allGames
```

## Testing

Run the test suite:
```bash
python tests/test_mongodb_powershell_integration.py
```

Tests verify:
- Helper files exist
- PowerShell scripts are readable
- MongoDB imports present
- Python bridge works correctly
- Graceful handling of missing MongoDB
- Documentation completeness

## Troubleshooting

### MongoDB Not Enabled
Set `$env:MONGODB_ENABLED = "true"`

### Python Not Found
Install Python 3.x and add to PATH

### pymongo Not Installed
Run `pip install pymongo`

### Connection Failed
- Check if MongoDB is running
- Verify connection string
- Check firewall settings
- For Atlas: verify IP whitelist

### Games Not Being Skipped
- Verify MongoDB is enabled: `Test-MongoDBEnabled`
- Check game status in MongoDB
- Ensure status is exactly "finished" (lowercase)

## No Breaking Changes

✅ **Completely Optional** - Works only when MONGODB_ENABLED=true
✅ **Graceful Fallback** - Scripts work normally without MongoDB
✅ **Existing CSV Workflow** - Still works as before
✅ **Backward Compatible** - No changes to existing data flow

## Documentation

- **`MONGODB_SETUP.md`** - Complete setup guide with examples
- **`docs/MONGODB_INTEGRATION.md`** - Integration documentation
- **`mongodb_schema.json`** - Schema definition and examples
- **`examples/mongodb_integration_example.ps1`** - Usage examples

## Support

For issues or questions:
1. Check `MONGODB_SETUP.md` for detailed documentation
2. Review `mongodb_schema.json` for schema details
3. Run test suite to verify integration
4. Check troubleshooting section in MONGODB_SETUP.md
