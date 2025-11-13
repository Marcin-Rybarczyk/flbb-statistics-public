# MongoDB Data Source Migration Guide

## Quick Start

This guide helps you switch from CSV to MongoDB as the data source for the FLBB Statistics Flask application.

## TL;DR - Quick Setup

```bash
# 1. Enable MongoDB
export MONGODB_ENABLED=true
export MONGODB_URI=mongodb://localhost:27017/
export MONGODB_DATABASE=flbb-statistics

# 2. Export existing CSV data to MongoDB
python scripts/export_csv_to_mongodb.py

# 3. Configure Flask to use MongoDB (auto mode with fallback)
export DATA_SOURCE=auto

# 4. Run Flask app
python tests/test_local_flask.py
```

## What's New?

The Flask application can now load game data from three sources:

1. **CSV files** (original behavior)
2. **MongoDB database** (new!)
3. **Auto mode** (try MongoDB, fallback to CSV)

## Configuration Options

### DATA_SOURCE Environment Variable

Control where the Flask app loads data from:

```bash
# Auto mode (default) - Try MongoDB first, fallback to CSV
export DATA_SOURCE=auto

# MongoDB only - Fail if MongoDB unavailable
export DATA_SOURCE=mongodb

# CSV only - Traditional behavior
export DATA_SOURCE=csv
```

### Configuration File

Alternatively, edit `scripts/config.json`:

```json
{
  "dataSourcePreference": {
    "preference": "auto"
  }
}
```

## Setup MongoDB

### Option 1: Local MongoDB

```bash
# Install (Ubuntu/Debian)
sudo apt-get install mongodb
sudo systemctl start mongodb

# Configure
export MONGODB_ENABLED=true
export MONGODB_URI=mongodb://localhost:27017/
export MONGODB_DATABASE=flbb-statistics
```

### Option 2: MongoDB Atlas (Cloud - Recommended)

1. Create free account: https://www.mongodb.com/cloud/atlas
2. Create free M0 cluster (512MB)
3. Create database user and whitelist IP
4. Get connection string
5. Configure:

```bash
export MONGODB_ENABLED=true
export MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/
export MONGODB_DATABASE=flbb-statistics
```

## Migration Steps

### Step 1: Export CSV Data to MongoDB

```bash
# Export from CSV file
python scripts/export_csv_to_mongodb.py --source csv

# Or export from JSON files
python scripts/export_csv_to_mongodb.py --source json

# Or both
python scripts/export_csv_to_mongodb.py
```

Expected output:
```
Loading data from data/full-game-stats.csv...
Loaded 210 records from CSV
Connecting to MongoDB...
✅ Connected to MongoDB database: flbb-statistics
Storing 210 games to MongoDB collection 'games'...

============================================================
Export completed!
============================================================
✅ Inserted: 210
🔄 Updated: 0
❌ Failed: 0
📊 Total: 210
============================================================
```

### Step 2: Test MongoDB Connection

```bash
# Run MongoDB data source tests
python tests/test_mongodb_data_source.py

# Expected: 5/5 tests pass
```

### Step 3: Configure Flask App

```bash
# Auto mode (recommended)
export DATA_SOURCE=auto

# Or MongoDB only
export DATA_SOURCE=mongodb
```

### Step 4: Run Flask Application

```bash
# Test the app
python tests/test_local_flask.py --test-only

# Run the app
python tests/test_local_flask.py
```

You should see in the logs:
```
Data source preference: auto
Loading game data from MongoDB...
✅ Loaded 210 games from MongoDB
```

## Rollback to CSV

If you need to rollback:

```bash
# Option 1: Set data source to CSV
export DATA_SOURCE=csv

# Option 2: Disable MongoDB
export MONGODB_ENABLED=false

# The app will automatically use CSV files
```

## Production Deployment

### Environment Variables for Production

Set these on your hosting platform (Render, Railway, etc.):

```bash
# MongoDB configuration
MONGODB_ENABLED=true
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DATABASE=flbb-statistics

# Data source (auto for safety)
DATA_SOURCE=auto
```

### Why Use "auto" Mode in Production?

- **Reliability**: Falls back to CSV if MongoDB is unavailable
- **Flexibility**: Can switch between sources without code changes
- **Safety**: Ensures app keeps running even if MongoDB has issues

## Data Update Strategy

### Regular Updates

When you process new game data:

```bash
# Update both CSV and MongoDB (recommended)
python scripts/post_process.py

# Or MongoDB only
python scripts/post_process.py --mongodb-only
```

### GitHub Actions

The existing GitHub Actions workflows will continue to work. Add MongoDB export to your workflow:

```yaml
- name: Export to MongoDB
  env:
    MONGODB_ENABLED: true
    MONGODB_URI: ${{ secrets.MONGODB_URI }}
    MONGODB_DATABASE: flbb-statistics
  run: |
    python scripts/export_csv_to_mongodb.py
```

## Benefits of MongoDB

1. **Flexible Queries**: Query by division, season, team, etc.
2. **Scalability**: Handle large amounts of historical data
3. **Cloud Storage**: Use MongoDB Atlas for cloud-based storage
4. **Better Performance**: Indexed queries are faster than CSV scanning
5. **Modern Architecture**: Industry-standard database solution

## Limitations

1. **Additional Setup**: Requires MongoDB installation or Atlas account
2. **Storage Limits**: Free Atlas tier has 512MB limit
3. **Network Dependency**: Cloud MongoDB requires internet connection
4. **Learning Curve**: Team needs to learn MongoDB basics

## Troubleshooting

### "pymongo not installed"

```bash
pip install pymongo
# or
pip install -r requirements.txt
```

### "MongoDB not enabled"

```bash
export MONGODB_ENABLED=true
```

### "Failed to connect to MongoDB"

Check if MongoDB is running:
```bash
# Local MongoDB
sudo systemctl status mongodb

# Or test connection
mongosh  # or mongo (older versions)
```

For Atlas, verify:
- Connection string is correct
- Database user credentials are correct
- IP address is whitelisted

### "No data in MongoDB"

Export your data first:
```bash
python scripts/export_csv_to_mongodb.py
```

## Testing

### Test Data Source Configuration

```bash
# Test configuration reading
python -c "from src.utils import get_data_source_preference; print(get_data_source_preference())"
```

### Test MongoDB Connection

```bash
# Run MongoDB tests
python tests/test_mongodb.py

# Run data source tests
python tests/test_mongodb_data_source.py
```

### Test Flask App

```bash
# Full test suite
python tests/test_local_flask.py --test-only
```

## Files Changed

- `.env.example` - Added DATA_SOURCE configuration
- `scripts/config.json` - Added dataSourcePreference section
- `src/utils.py` - Enhanced load_game_data() with MongoDB support
- `scripts/export_csv_to_mongodb.py` - New migration script
- `tests/test_mongodb_data_source.py` - New test suite
- `docs/MONGODB_INTEGRATION.md` - Updated documentation

## Support

For issues or questions:

1. Check `docs/MONGODB_INTEGRATION.md` for detailed documentation
2. Run tests: `python tests/test_mongodb_data_source.py`
3. Check logs for error messages
4. Create a GitHub issue with details

## Next Steps

1. ✅ Setup MongoDB (local or Atlas)
2. ✅ Export existing data to MongoDB
3. ✅ Test the connection
4. ✅ Configure DATA_SOURCE
5. ✅ Run Flask app
6. ✅ Deploy to production

---

**Note**: This migration is completely optional. The CSV-based workflow continues to work exactly as before. MongoDB is an alternative data source for those who want database capabilities.
