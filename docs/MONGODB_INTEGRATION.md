# MongoDB Integration Guide

This guide explains how to use MongoDB storage for extracted JSON game data in the FLBB Statistics application.

## Overview

The MongoDB integration allows you to store extracted basketball game data in MongoDB, providing:
- **Flexible queries** - Query games by division, season, team, etc.
- **Scalability** - Handle large amounts of historical data
- **Cloud support** - Use MongoDB Atlas for cloud storage
- **Optional feature** - Completely optional, CSV workflow still works

## Features

- **Store game data** - Store extracted JSON game data in MongoDB collections
- **Use as data source** - Flask app can load data directly from MongoDB (NEW!)
- **Flexible configuration** - Choose between CSV, MongoDB, or auto mode
- **Migration tools** - Export existing CSV data to MongoDB
- **Local & Cloud** - Support for both local MongoDB and MongoDB Atlas (cloud)
- **Batch operations** - Efficient data storage and retrieval
- **Query capabilities** - Query games by ID, division, season, etc.
- **Automatic indexing** - Better performance for queries
- **Backward compatible** - Existing CSV workflow still works

## Prerequisites

### Install MongoDB

**Option 1: Local MongoDB**

Install MongoDB Community Edition on your system:
- **Ubuntu/Debian**: 
  ```bash
  sudo apt-get install mongodb
  sudo systemctl start mongodb
  ```
- **macOS**: 
  ```bash
  brew tap mongodb/brew
  brew install mongodb-community
  brew services start mongodb-community
  ```
- **Windows**: Download from [MongoDB Downloads](https://www.mongodb.com/try/download/community)

**Option 2: MongoDB Atlas (Cloud)**

1. Sign up for free at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free cluster (M0 - 512 MB storage)
3. Get your connection string from the Atlas dashboard

### Install Python Package

```bash
pip install pymongo
```

Or install all dependencies including pymongo:
```bash
pip install -r requirements.txt
```

## Configuration

### Method 1: Environment Variables (Recommended)

Create a `.env` file or set environment variables:

```bash
# Enable MongoDB storage
MONGODB_ENABLED=true

# Local MongoDB
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=flbb-statistics

# Or MongoDB Atlas (cloud)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=flbb-statistics
```

### Method 2: Configuration File

Edit `scripts/config.json`:

```json
{
  "mongodb": {
    "enabled": true,
    "connectionString": "mongodb://localhost:27017/",
    "database": "flbb-statistics",
    "collections": {
      "games": "games",
      "players": "players",
      "teams": "teams"
    }
  }
}
```

### Data Source Configuration

**NEW in v2.0:** The Flask application can now load game data directly from MongoDB instead of CSV files.

Configure the data source via environment variable or configuration file:

**Environment Variable (Recommended):**
```bash
# Use MongoDB as the primary data source (with CSV fallback)
DATA_SOURCE=auto

# Use only MongoDB (no CSV fallback)
DATA_SOURCE=mongodb

# Use only CSV files
DATA_SOURCE=csv
```

**Configuration File (`scripts/config.json`):**
```json
{
  "dataSourcePreference": {
    "preference": "auto"
  }
}
```

**Data Source Options:**
- `auto` (default): Try MongoDB first, fall back to CSV if unavailable
- `mongodb`: Use only MongoDB (Flask will fail if MongoDB is not available)
- `csv`: Use only CSV files (traditional behavior)

**Example Usage:**
```bash
# Run Flask app with MongoDB as data source
export MONGODB_ENABLED=true
export MONGODB_URI=mongodb://localhost:27017/
export MONGODB_DATABASE=flbb-statistics
export DATA_SOURCE=mongodb
python src/app.py

# Or use auto mode (recommended for production)
export DATA_SOURCE=auto
python src/app.py
```

## Usage

### Exporting CSV Data to MongoDB

Use the export script to migrate existing CSV data to MongoDB:

```bash
# Export from CSV file
python scripts/export_csv_to_mongodb.py --source csv

# Export from JSON files
python scripts/export_csv_to_mongodb.py --source json

# Export from both (default)
python scripts/export_csv_to_mongodb.py

# Force export even if MongoDB not enabled
python scripts/export_csv_to_mongodb.py --force

# Custom MongoDB connection
python scripts/export_csv_to_mongodb.py \
  --uri mongodb://localhost:27017/ \
  --database my-stats
```

### Automatic Storage During Post-Processing

When you run the post-processing script, it will automatically store data to MongoDB if enabled:

```bash
# Run full post-processing (CSV + MongoDB + Archive + Upload)
python scripts/post_process.py

# Skip MongoDB storage
python scripts/post_process.py --skip-mongodb

# Store only to MongoDB (skip CSV and archive)
python scripts/post_process.py --mongodb-only
```

### Manual Storage from Python

```python
from src.mongodb_helper import store_json_data_to_mongodb
import json

# Load your game data
with open('data/gamesDB.json', 'r') as f:
    games_data = json.load(f)

# Store to MongoDB
store_json_data_to_mongodb(
    games_data,
    connection_string='mongodb://localhost:27017/',
    database_name='flbb-statistics',
    collection_name='games'
)
```

### Query Data from MongoDB

```python
from src.mongodb_helper import MongoDBHelper

# Connect to MongoDB
mongo = MongoDBHelper('mongodb://localhost:27017/', 'flbb-statistics')
mongo.connect()

# Get a specific game
game = mongo.get_game_by_id('1101011')
print(f"Game: {game['HomeTeamName']} vs {game['AwayTeamName']}")

# Get all games for a division
division_games = mongo.get_games_by_division('m-enovos-leaguetour-qualificatif')
print(f"Found {len(division_games)} games")

# Get total game count
count = mongo.get_games_count()
print(f"Total games: {count}")

# Close connection
mongo.disconnect()
```

## Testing

Run the MongoDB integration tests:

```bash
# Test with default settings (local MongoDB)
python tests/test_mongodb.py

# Test with custom connection
python tests/test_mongodb.py --connection-string mongodb://localhost:27017/ --database test-db

# Keep test data (don't clean up)
python tests/test_mongodb.py --skip-cleanup
```

The tests will:
1. Check if pymongo is installed
2. Test MongoDB connection
3. Test single game storage
4. Test batch storage
5. Test querying data
6. Clean up test data

## MongoDB Collections

### games Collection

Stores individual game records with the following structure:

```json
{
  "GameId": "1101011",
  "GameDivisionName": "m-enovos-leaguetour-qualificatif",
  "HomeTeamName": "Amicale Steesel",
  "AwayTeamName": "Kordall Steelers",
  "FinalHomeScore": 85,
  "FinalAwayScore": 78,
  "SeasonId": "2025-2026",
  "GameStatus": "Finished",
  "GameUrl": "https://...",
  "ScheduledGameDate": {...},
  "_stored_at": "2025-11-06T15:30:00Z"
}
```

**Indexes:**
- `GameId` (unique) - Fast lookup by game ID
- `GameDivisionName` - Query games by division
- `SeasonId` - Query games by season

## Migration Guide: CSV to MongoDB

This guide helps you migrate from CSV-based data storage to MongoDB.

### Step 1: Install and Configure MongoDB

Choose one option:

**Option A: Local MongoDB**
```bash
# Install MongoDB (Ubuntu/Debian)
sudo apt-get install mongodb
sudo systemctl start mongodb
```

**Option B: MongoDB Atlas (Cloud)**
1. Create free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create free M0 cluster
3. Get connection string

### Step 2: Configure Environment

```bash
# Enable MongoDB
export MONGODB_ENABLED=true

# Set connection (local or Atlas)
export MONGODB_URI=mongodb://localhost:27017/
# OR for Atlas:
# export MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/

# Set database name
export MONGODB_DATABASE=flbb-statistics
```

### Step 3: Export Existing Data

```bash
# Export CSV data to MongoDB
python scripts/export_csv_to_mongodb.py --source csv

# Or export JSON files
python scripts/export_csv_to_mongodb.py --source json

# Or both
python scripts/export_csv_to_mongodb.py
```

### Step 4: Configure Data Source

```bash
# Use auto mode (tries MongoDB, falls back to CSV)
export DATA_SOURCE=auto

# Or MongoDB only
export DATA_SOURCE=mongodb
```

### Step 5: Test the Application

```bash
# Run Flask app
python src/app.py

# Or run tests
python tests/test_mongodb_data_source.py
```

### Step 6: Verify Data Loading

Check the Flask app startup logs. You should see:
```
Data source preference: auto
Loading game data from MongoDB...
✅ Loaded 210 games from MongoDB
```

### Rollback to CSV

If you need to rollback to CSV:

```bash
# Set data source to CSV only
export DATA_SOURCE=csv

# Or disable MongoDB
export MONGODB_ENABLED=false
```

The application will automatically use CSV files.

### Production Deployment

For production with MongoDB:

1. **Use MongoDB Atlas** (recommended) - Free tier available
2. **Set environment variables** on your hosting platform:
   ```bash
   MONGODB_ENABLED=true
   MONGODB_URI=mongodb+srv://...
   MONGODB_DATABASE=flbb-statistics
   DATA_SOURCE=auto  # For safety, allows CSV fallback
   ```
3. **Monitor MongoDB storage** - Free tier has 512MB limit
4. **Schedule data exports** - Export fresh data regularly using GitHub Actions
5. **Keep CSV backups** - Even when using MongoDB, CSV backups are useful

### Data Sync Strategy

**Recommended approach:**

1. **Development**: Use `DATA_SOURCE=auto` with local MongoDB
2. **Production**: Use `DATA_SOURCE=auto` with MongoDB Atlas
3. **Backup**: Keep CSV files as backup (automatically created when loading from MongoDB)
4. **Updates**: Use `post_process.py` to update both CSV and MongoDB

**Update workflow:**
```bash
# Process new data (updates both CSV and MongoDB)
python scripts/post_process.py

# Or MongoDB only
python scripts/post_process.py --mongodb-only
```

## Troubleshooting

### pymongo not installed

**Error:** `ImportError: No module named 'pymongo'`

**Solution:**
```bash
pip install pymongo
```

### MongoDB connection refused

**Error:** `[Errno 111] Connection refused`

**Solution:** Make sure MongoDB is running:
```bash
# Check if MongoDB is running
sudo systemctl status mongodb

# Start MongoDB
sudo systemctl start mongodb
```

### Authentication failed

**Error:** `Authentication failed`

**Solution:** Check your MongoDB connection string includes correct username and password:
```bash
MONGODB_URI=mongodb://username:password@host:port/
```

For MongoDB Atlas, get the connection string from your cluster's "Connect" button.

### Storage disabled

**Message:** `MongoDB storage is disabled in configuration`

**Solution:** Enable MongoDB in your configuration:
- Set `MONGODB_ENABLED=true` in environment variables, OR
- Set `"enabled": true` in `scripts/config.json` under `"mongodb"` section

## Best Practices

1. **Use MongoDB Atlas for production** - Free tier provides reliable cloud storage
2. **Enable indexing** - Indexes are automatically created for better query performance
3. **Backup your data** - MongoDB Atlas provides automatic backups
4. **Monitor storage** - Keep an eye on storage usage, especially on free tiers
5. **Use environment variables** - Keep credentials secure with environment variables

## MongoDB Atlas Setup

1. **Create Account**: Sign up at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. **Create Cluster**: Create a free M0 cluster (512 MB)
3. **Create Database User**: 
   - Go to "Database Access"
   - Add new database user with password
4. **Whitelist IP**: 
   - Go to "Network Access"
   - Add IP address (use `0.0.0.0/0` for access from anywhere)
5. **Get Connection String**: 
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password

Example connection string:
```
mongodb+srv://flbb-user:mypassword@cluster0.mongodb.net/
```

## Performance Considerations

- **Batch operations** - Use `store_games_batch()` for multiple games
- **Indexes** - Automatically created on GameId, GameDivisionName, and SeasonId
- **Connection pooling** - MongoDBHelper manages connections efficiently
- **Query optimization** - Use specific queries instead of getting all games

## API Reference

### MongoDBHelper Class

```python
# Initialize
mongo = MongoDBHelper(connection_string, database_name)

# Connect/Disconnect
mongo.connect()
mongo.disconnect()
mongo.is_connected()

# Store data
mongo.store_game_data(game_data, collection_name='games')
mongo.store_games_batch(games_list, collection_name='games')

# Query data
mongo.get_game_by_id(game_id, collection_name='games')
mongo.get_games_by_division(division_name, collection_name='games')
mongo.get_all_games(collection_name='games', limit=100)
mongo.get_games_count(collection_name='games')

# Maintenance
mongo.delete_all_games(collection_name='games')
mongo.create_indexes(collection_name='games')
```

### Convenience Functions

```python
# Store data (simpler interface)
store_json_data_to_mongodb(
    json_data,
    connection_string=None,  # Uses env var if not provided
    database_name=None,      # Uses env var if not provided
    collection_name='games'
)

# Load data (simpler interface)
load_json_data_from_mongodb(
    connection_string=None,
    database_name=None,
    collection_name='games',
    limit=None
)

# Check if enabled
is_mongodb_enabled()  # Returns True if enabled in config
is_mongodb_available()  # Returns True if pymongo is installed
```

## Security Notes

- Never commit MongoDB credentials to Git
- Use environment variables for connection strings
- Restrict IP access in MongoDB Atlas
- Use strong passwords for database users
- Enable authentication for local MongoDB instances

## Support

For issues or questions:
1. Check [MongoDB Documentation](https://docs.mongodb.com/)
2. Review test output from `tests/test_mongodb.py`
3. Check application logs for error messages
4. Open an issue on GitHub with error details
