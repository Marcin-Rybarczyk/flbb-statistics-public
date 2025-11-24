# MongoDB Integration Setup Guide for PowerShell Scripts

This guide explains how to integrate MongoDB with the PowerShell data collection and processing scripts for the FLBB Statistics application.

## Overview

The MongoDB integration provides:
- **Deduplication** - Skip downloading and processing games that are already finished
- **Single Collection** - All game data stored in one `games` collection
- **Status Tracking** - Track processing status (pending, finished)
- **Parallel Processing** - Enable parallel CSV export after JSON stored in MongoDB
- **Flexible Configuration** - Easy deployment with connection string placeholders

## Table of Contents

1. [MongoDB Collection Schema](#mongodb-collection-schema)
2. [Deduplication Logic](#deduplication-logic)
3. [Integration Workflow](#integration-workflow)
4. [Configuration](#configuration)
5. [PowerShell Usage Examples](#powershell-usage-examples)
6. [Python Bridge Usage](#python-bridge-usage)
7. [Parallel CSV/JSON Generation](#parallel-csvjson-generation)
8. [Troubleshooting](#troubleshooting)

## MongoDB Collection Schema

### Collection: `games`

All game data is stored in a single collection called `games`. Each document represents one game with the following structure:

```json
{
  "_id": ObjectId("..."),
  "GameId": "12345",
  "status": "finished",
  "csv_generated": true,
  "json_data": {
    "GameId": "12345",
    "GameLocation": { ... },
    "GameDivisionDisplay": "Division 1 Hommes",
    "GameTeamsShort": "Team A - Team B",
    "GameFinalScore": "85 : 78",
    "HomeTeamName": "Team A",
    "AwayTeamName": "Team B",
    "FinalHomeScore": 85,
    "FinalAwayScore": 78,
    "DateTime": "2025-11-24 20:00:00",
    "Teams": [ ... ],
    "GameEvents": [ ... ],
    "Referees": [ ... ]
  },
  "SeasonId": "2025-2026",
  "GameDivisionDisplay": "Division 1 Hommes",
  "HomeTeamName": "Team A",
  "AwayTeamName": "Team B",
  "_stored_at": "2025-11-24T21:00:00Z",
  "_last_updated": "2025-11-24T21:30:00Z",
  "_processed_by": "PowerShell Script"
}
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `GameId` | String | Unique game identifier (primary key) |
| `status` | String | Processing status: `pending`, `finished` |
| `csv_generated` | Boolean | Whether CSV has been generated |
| `json_data` | Object | Full game statistics and metadata |
| `SeasonId` | String | Season identifier (e.g., "2025-2026") |
| `GameDivisionDisplay` | String | Division name for quick filtering |
| `HomeTeamName` | String | Home team name |
| `AwayTeamName` | String | Away team name |
| `_stored_at` | DateTime | When document was first created |
| `_last_updated` | DateTime | When document was last modified |
| `_processed_by` | String | Processing source identifier |

### Indexes

For optimal performance, create the following indexes:

```javascript
// MongoDB shell or Compass
db.games.createIndex({ "GameId": 1 }, { unique: true })
db.games.createIndex({ "status": 1 })
db.games.createIndex({ "GameDivisionDisplay": 1 })
db.games.createIndex({ "SeasonId": 1 })
db.games.createIndex({ "GameId": 1, "status": 1 })
```

These indexes are automatically created by the Python helper when storing data.

## Deduplication Logic

The deduplication system prevents re-downloading and re-processing games that are already complete:

### Workflow

1. **Before Downloading HTML**
   - Query MongoDB: `db.games.findOne({ GameId: "12345", status: "finished" })`
   - If found → **Skip download and processing**
   - If not found → **Proceed with download**

2. **After Parsing HTML to JSON**
   - Parse HTML and create JSON game data
   - Insert/update document in MongoDB
   - Set `status: "finished"`
   - Set `csv_generated: true/false`
   - Store full JSON in `json_data` field

3. **CSV Generation**
   - Can happen in parallel after MongoDB storage
   - Query MongoDB for all games: `db.games.find({})`
   - Generate CSV from stored JSON data
   - Update `csv_generated: true` for all processed games

### Status States

| Status | Description |
|--------|-------------|
| `pending` | Game downloaded but not fully processed |
| `finished` | Game fully processed and stored in MongoDB |

### Deduplication Benefits

- ✅ **Faster Downloads** - Skip games already processed
- ✅ **Bandwidth Savings** - Don't re-download same data
- ✅ **Processing Time** - Skip re-parsing finished games
- ✅ **Reliable State** - Clear status tracking
- ✅ **Resume Support** - Can resume interrupted downloads

## Integration Workflow

### Overall Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Download Controller (download-controller.ps1)           │
├─────────────────────────────────────────────────────────────┤
│  For each game:                                             │
│    ├─ Check MongoDB: Is game finished?                      │
│    │   ├─ YES → Skip download                              │
│    │   └─ NO → Download HTML                               │
│    └─ Save HTML to disk                                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Extract Game (extract-game.ps1)                         │
├─────────────────────────────────────────────────────────────┤
│  For each HTML file:                                        │
│    ├─ Parse HTML → JSON                                     │
│    ├─ Save JSON to disk                                     │
│    └─ Store in MongoDB:                                     │
│        ├─ json_data: Full game data                        │
│        ├─ status: "finished"                               │
│        └─ csv_generated: false                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CSV Generation (parallel or sequential)                 │
├─────────────────────────────────────────────────────────────┤
│  ├─ Query MongoDB for all finished games                    │
│  ├─ Generate CSV from json_data                            │
│  └─ Update csv_generated: true                             │
└─────────────────────────────────────────────────────────────┘
```

### Integration Points

The PowerShell scripts integrate MongoDB at these points:

1. **download-controller.ps1**
   ```powershell
   # Import MongoDB helper
   . "$ROOT\mongodb_helper.ps1"
   
   # Before downloading each game
   if (Test-GameInMongoDB -GameId $game.GameId -Status "finished") {
       Write-Host "Game $($game.GameId) already finished, skipping"
       continue
   }
   ```

2. **extract-game.ps1**
   ```powershell
   # After creating JSON
   Set-GameInMongoDB -GameId $game.GameId -JsonFilePath $outputFilepath -Status "finished"
   ```

## Configuration

### Environment Variables

Set these environment variables to enable MongoDB integration:

```bash
# Enable MongoDB
export MONGODB_ENABLED=true

# Local MongoDB
export MONGODB_URI=mongodb://localhost:27017/
export MONGODB_DATABASE=flbb-statistics

# MongoDB Atlas (Cloud)
export MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
export MONGODB_DATABASE=flbb-statistics
```

### PowerShell Configuration

On Windows, set environment variables:

```powershell
# PowerShell
$env:MONGODB_ENABLED = "true"
$env:MONGODB_URI = "mongodb://localhost:27017/"
$env:MONGODB_DATABASE = "flbb-statistics"
```

Or in config.json (future enhancement):

```json
{
  "mongodb": {
    "enabled": true,
    "uri": "mongodb://localhost:27017/",
    "database": "flbb-statistics",
    "collection": "games"
  }
}
```

### Connection String Examples

#### Local MongoDB
```
mongodb://localhost:27017/
```

#### MongoDB with Authentication
```
mongodb://username:password@localhost:27017/
```

#### MongoDB Atlas (Cloud)
```
mongodb+srv://username:password@cluster-name.mongodb.net/
```

#### Multiple Hosts (Replica Set)
```
mongodb://host1:27017,host2:27017,host3:27017/?replicaSet=myReplicaSet
```

## PowerShell Usage Examples

### Import the MongoDB Helper

```powershell
# Import the MongoDB helper module
. "$PSScriptRoot\mongodb_helper.ps1"
```

### Test MongoDB Connection

```powershell
# Test if MongoDB is enabled and connection works
if (Test-MongoDBConnection) {
    Write-Host "MongoDB is ready to use"
} else {
    Write-Warning "MongoDB is not available, using fallback mode"
}
```

### Check if Game Exists

```powershell
# Check if a game exists with status 'finished'
$gameExists = Test-GameInMongoDB -GameId "12345" -Status "finished"

if ($gameExists) {
    Write-Host "Game already processed, skipping"
} else {
    Write-Host "Processing game..."
    # Download and process game
}
```

### Store Game in MongoDB

```powershell
# After creating JSON file
$jsonPath = "data/full-game-stats-output/division1/full-game-stats-12345.json"
$success = Set-GameInMongoDB -GameId "12345" -JsonFilePath $jsonPath -Status "finished" -CsvGenerated $false

if ($success) {
    Write-Host "Game stored successfully"
}
```

### Query Games

```powershell
# Get all finished games
$finishedGames = Get-GamesFromMongoDB -Status "finished"
Write-Host "Found $($finishedGames.Count) finished games"

# Get games for specific division
$div1Games = Get-GamesFromMongoDB -Division "Division 1 Hommes" -Status "finished"

# Get games for specific season
$seasonGames = Get-GamesFromMongoDB -Season "2025-2026"
```

### Get Game Count

```powershell
# Get total number of games in MongoDB
$count = Get-MongoDBGameCount
Write-Host "Total games in MongoDB: $count"
```

## Python Bridge Usage

The Python bridge script can also be used directly from command line:

### Test Connection

```bash
python scripts/mongodb_powershell_bridge.py test-connection
```

### Check if Game Exists

```bash
python scripts/mongodb_powershell_bridge.py check-game --game-id 12345 --status finished
# Exit code 0: Game exists with status
# Exit code 1: Game doesn't exist or different status
# Exit code 2: Error occurred
```

### Insert/Update Game

```bash
python scripts/mongodb_powershell_bridge.py upsert-game \
  --game-id 12345 \
  --json-file data/full-game-stats-output/game.json \
  --status finished \
  --csv-generated true
```

### Query Games

```bash
# Query all finished games (outputs JSON)
python scripts/mongodb_powershell_bridge.py query-games --status finished

# Query by division
python scripts/mongodb_powershell_bridge.py query-games --division "Division 1 Hommes"

# Query by season
python scripts/mongodb_powershell_bridge.py query-games --season "2025-2026"
```

### Count Games

```bash
python scripts/mongodb_powershell_bridge.py count-games
```

## Parallel CSV/JSON Generation

MongoDB enables parallel processing by decoupling JSON storage from CSV generation:

### Sequential Mode (Traditional)

```powershell
# Traditional sequential processing
foreach ($game in $games) {
    # 1. Download HTML
    Download-GameHTML -GameId $game.GameId
    
    # 2. Parse to JSON
    $json = Parse-GameHTML -GameId $game.GameId
    
    # 3. Generate CSV row (blocking)
    Add-GameToCSV -GameData $json
}
```

### Parallel Mode (MongoDB-Enabled)

```powershell
# MongoDB-enabled parallel processing

# Phase 1: Download and store JSON in MongoDB (parallel)
$games | ForEach-Object -Parallel {
    $game = $_
    
    # Check if already finished
    if (-not (Test-GameInMongoDB -GameId $game.GameId -Status "finished")) {
        # Download HTML
        Download-GameHTML -GameId $game.GameId
        
        # Parse to JSON
        $json = Parse-GameHTML -GameId $game.GameId
        
        # Store in MongoDB (non-blocking for CSV)
        Set-GameInMongoDB -GameId $game.GameId -JsonFilePath $json -Status "finished"
    }
} -ThrottleLimit 10

# Phase 2: Generate CSV from MongoDB (can run in parallel with Phase 1)
$allGames = Get-GamesFromMongoDB -Status "finished"
Generate-CSV -Games $allGames
```

### Benefits of Parallel Processing

- ✅ **Faster Overall** - JSON storage and CSV generation don't block each other
- ✅ **Independent Pipelines** - CSV can be regenerated without re-parsing HTML
- ✅ **Scalability** - Can process thousands of games efficiently
- ✅ **Flexibility** - Different CSV formats without re-processing

## Troubleshooting

### MongoDB Not Enabled

**Symptom**: Scripts don't use MongoDB
**Solution**: Set environment variable
```powershell
$env:MONGODB_ENABLED = "true"
```

### Python Not Found

**Symptom**: Error about Python not being available
**Solution**: Install Python 3.x and ensure it's in PATH
```bash
python --version  # Should show Python 3.x
```

### pymongo Not Installed

**Symptom**: Error about pymongo module
**Solution**: Install pymongo
```bash
pip install pymongo
```

### Connection Failed

**Symptom**: Cannot connect to MongoDB
**Solution**: 
1. Check if MongoDB is running: `mongod --version`
2. Verify connection string is correct
3. Check firewall/network settings
4. For Atlas: Check IP whitelist and credentials

### Games Not Being Skipped

**Symptom**: Games are re-downloaded even though they're finished
**Solution**:
1. Verify MongoDB is enabled: `Test-MongoDBEnabled`
2. Check game status in MongoDB: 
   ```javascript
   db.games.findOne({ GameId: "12345" })
   ```
3. Ensure status is exactly "finished" (lowercase)

### Performance Issues

**Symptom**: Queries are slow
**Solution**: Create indexes
```bash
python scripts/mongodb_powershell_bridge.py test-connection
# Indexes are created automatically
```

Or manually in MongoDB:
```javascript
db.games.createIndex({ "GameId": 1 }, { unique: true })
db.games.createIndex({ "status": 1 })
```

## Sample MongoDB Operations

### MongoDB Shell Examples

```javascript
// Connect to database
use flbb-statistics

// Count all games
db.games.countDocuments()

// Find a specific game
db.games.findOne({ GameId: "12345" })

// Find all finished games
db.games.find({ status: "finished" }).count()

// Find games by division
db.games.find({ GameDivisionDisplay: "Division 1 Hommes" })

// Update game status
db.games.updateOne(
  { GameId: "12345" },
  { $set: { status: "finished", csv_generated: true } }
)

// Delete all games (careful!)
db.games.deleteMany({})

// Get games without CSV
db.games.find({ csv_generated: false })

// Aggregate games by division
db.games.aggregate([
  { $group: { _id: "$GameDivisionDisplay", count: { $sum: 1 } } }
])
```

### Python Examples

```python
from src.mongodb_helper import MongoDBHelper

# Connect
mongo = MongoDBHelper()
mongo.connect()

# Get a game
game = mongo.get_game_by_id("12345")

# Get all finished games
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['flbb-statistics']
games = list(db.games.find({"status": "finished"}))

# Close
mongo.disconnect()
```

## Summary

The MongoDB integration provides:

✅ **Single Collection** - All games in `games` collection  
✅ **Deduplication** - Skip finished games automatically  
✅ **Status Tracking** - `pending` vs `finished` states  
✅ **Parallel Processing** - JSON storage and CSV generation decoupled  
✅ **Easy Configuration** - Connection string via environment variables  
✅ **PowerShell Integration** - Native PowerShell functions  
✅ **Python Bridge** - CLI interface for complex operations  
✅ **No Breaking Changes** - Existing CSV workflow still works  

For more information, see:
- [MongoDB Integration Documentation](../docs/MONGODB_INTEGRATION.md)
- [Python MongoDB Helper](../src/mongodb_helper.py)
- [PowerShell MongoDB Helper](mongodb_helper.ps1)
- [Python Bridge Script](mongodb_powershell_bridge.py)
