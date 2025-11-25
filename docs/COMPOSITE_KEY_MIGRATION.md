# MongoDB Composite Key Migration Guide

## Overview

This document describes the migration from a single-field primary key (GameId) to a composite primary key (GameId + SeasonId) in the MongoDB games collection.

## Background

### Problem Statement

The original MongoDB implementation used `GameId` as the sole unique identifier for game records. However, this was incorrect because:

1. **GameId is not globally unique**: The same GameId can be reused across different seasons
2. **Risk of data corruption**: Games from different seasons could overwrite each other
3. **Inaccurate data retrieval**: Queries without SeasonId could return the wrong game

### Solution

Implement a composite primary key using both `GameId` and `SeasonId` to uniquely identify each game.

## Changes Made

### 1. MongoDB Schema (mongodb_schema.json)

**Changed:**
- Schema version updated from 1.0 to 2.0
- `GameId` field: Changed from `unique: true` to `unique: false`
- `SeasonId` field: Changed from `required: false` to `required: true`
- Primary index: Changed from `GameId (unique)` to `GameId + SeasonId (composite unique)`

**New Indexes:**
```javascript
// Primary key - composite unique index
db.games.createIndex({ "GameId": 1, "SeasonId": 1 }, { unique: true })

// Supporting indexes
db.games.createIndex({ "GameId": 1 })  // Non-unique, for queries without season
db.games.createIndex({ "SeasonId": 1 })
db.games.createIndex({ "status": 1 })
db.games.createIndex({ "GameDivisionDisplay": 1 })
```

### 2. Python MongoDB Helper (src/mongodb_helper.py)

**Updated Methods:**

#### `store_game_data()`
- Now uses composite key `{'GameId': game_id, 'SeasonId': season_id}` for upsert operations
- Falls back to GameId-only with a warning if SeasonId is not provided
- Ensures data integrity by preventing overwrites across seasons

#### `get_game_by_id()`
- Added optional `season_id` parameter
- When `season_id` is provided, performs precise lookup using composite key
- When `season_id` is None, searches by GameId only (with warning)

#### `get_game_by_composite_key()`
- New method for explicit composite key lookups
- Requires both `game_id` and `season_id` parameters

#### `create_indexes()`
- Creates composite unique index on `(GameId, SeasonId)`
- Creates non-unique index on `GameId` for queries without season
- Creates compound index on `(GameId, SeasonId, status)` for efficient status checks

### 3. PowerShell MongoDB Helper (scripts/mongodb_helper.ps1)

**Updated Functions:**

#### `Test-GameInMongoDB`
```powershell
# New signature
Test-GameInMongoDB -GameId "12345" -SeasonId "2025-2026" -Status "finished"

# Parameters:
# - GameId (required): Game identifier
# - SeasonId (optional): Season identifier for composite key lookup
# - Status (optional): Status to check
```

#### `Set-GameInMongoDB`
```powershell
# New signature
Set-GameInMongoDB -GameId "12345" -SeasonId "2025-2026" -JsonFilePath "game.json" -Status "finished"

# Parameters:
# - GameId (required): Game identifier
# - SeasonId (optional): Season identifier for composite key
# - JsonFilePath (required): Path to JSON file with game data
# - Status (optional): Game status
# - CsvGenerated (optional): Whether CSV was generated
```

### 4. Python Bridge Script (scripts/mongodb_powershell_bridge.py)

**Updated Commands:**

#### `check-game`
```bash
# New usage
python scripts/mongodb_powershell_bridge.py check-game \
  --game-id 12345 \
  --season-id "2025-2026" \
  --status finished

# Parameters:
# - --game-id (required): Game identifier
# - --season-id (optional): Season identifier for composite key lookup
# - --status (optional): Status to check
```

#### `upsert-game`
```bash
# New usage
python scripts/mongodb_powershell_bridge.py upsert-game \
  --game-id 12345 \
  --season-id "2025-2026" \
  --json-file game.json \
  --status finished

# Parameters:
# - --game-id (required): Game identifier
# - --season-id (optional): Season identifier for composite key
# - --json-file or --json-data (required): Game data
# - --status (optional): Game status
# - --csv-generated (optional): Whether CSV was generated
```

### 5. Documentation Migration

All MongoDB documentation files moved from root to `docs/` folder:
- `MONGODB_IMPLEMENTATION.md` → `docs/MONGODB_IMPLEMENTATION.md`
- `MONGODB_QUICKREF.md` → `docs/MONGODB_QUICKREF.md`
- `MONGODB_SETUP.md` → `docs/MONGODB_SETUP.md`

All documentation updated to reflect:
- Composite key as primary identifier
- SeasonId as required field
- Updated examples using both GameId and SeasonId

## Migration Path

### For Existing Deployments

If you have existing MongoDB data with the old schema:

#### Option 1: Drop and Recreate (Recommended for development)
```javascript
// Drop the old unique index
db.games.dropIndex("GameId_1")

// Create the new composite unique index
db.games.createIndex({ "GameId": 1, "SeasonId": 1 }, { unique: true })

// Create supporting indexes
db.games.createIndex({ "GameId": 1 })
db.games.createIndex({ "SeasonId": 1 })
```

#### Option 2: Ensure Data Integrity (Production)
```javascript
// Step 1: Verify all documents have SeasonId
db.games.find({ SeasonId: { $exists: false } }).count()

// Step 2: If any documents lack SeasonId, you must add it manually
// (This depends on your data - you may need to determine the season from other fields)

// Step 3: Drop the old unique index
db.games.dropIndex("GameId_1")

// Step 4: Create the new composite unique index
db.games.createIndex({ "GameId": 1, "SeasonId": 1 }, { unique: true })

// Step 5: Verify no duplicates exist
db.games.aggregate([
  { $group: { _id: { GameId: "$GameId", SeasonId: "$SeasonId" }, count: { $sum: 1 } } },
  { $match: { count: { $gt: 1 } } }
])
```

### For New Deployments

No migration needed - the helper scripts will automatically create the correct indexes on first use.

## Backward Compatibility

### What Still Works
- Queries by GameId alone (with warning)
- Queries by SeasonId alone
- Queries by status, division, etc.

### What Changed
- GameId is no longer globally unique
- SeasonId is now required for all new game insertions
- Upsert operations use composite key (GameId + SeasonId)

### Breaking Changes
- Any code that assumed GameId uniqueness across seasons must be updated
- Scripts that don't provide SeasonId will receive warnings

## Testing

All tests pass with the new composite key implementation:
- MongoDB PowerShell integration tests: 7/7 passed
- Composite key logic verification: All checks passed

## Benefits

### Data Integrity
✅ No risk of games from different seasons overwriting each other  
✅ Accurate game identification across all seasons  
✅ Proper support for historical data

### Query Performance
✅ Composite unique index ensures fast lookups  
✅ Supporting indexes for flexible querying  
✅ Efficient status checks with compound index

### Future-Proof
✅ Supports multi-season data storage  
✅ Enables cross-season analytics  
✅ Aligns with actual data structure

## Examples

### Before (Incorrect)
```powershell
# Could return wrong game if same GameId exists in multiple seasons
Test-GameInMongoDB -GameId "12345" -Status "finished"
```

### After (Correct)
```powershell
# Precisely identifies game using composite key
Test-GameInMongoDB -GameId "12345" -SeasonId "2025-2026" -Status "finished"
```

### MongoDB Queries

#### Find a specific game
```javascript
// Precise lookup with composite key
db.games.findOne({ GameId: "12345", SeasonId: "2025-2026" })
```

#### Update a specific game
```javascript
// Update using composite key
db.games.updateOne(
  { GameId: "12345", SeasonId: "2025-2026" },
  { $set: { status: "finished", csv_generated: true } }
)
```

#### Query all games from a season
```javascript
db.games.find({ SeasonId: "2025-2026", status: "finished" })
```

## Conclusion

The migration to a composite primary key (GameId + SeasonId) ensures data integrity and aligns the MongoDB schema with the actual data structure. All documentation, code, and examples have been updated to reflect this change.

**Key Takeaway:** Always use both GameId and SeasonId when working with game records to ensure accurate and reliable data operations.
