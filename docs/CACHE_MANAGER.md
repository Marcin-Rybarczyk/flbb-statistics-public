# Cache Manager for FLBB Statistics

## Overview

The cache manager provides an efficient way to avoid re-downloading raw HTML and JSON files for completed basketball games from the FLBB website. Finished games don't change, so their data can be safely cached on Google Drive.

## How It Works

### Cache Workflow

1. **Cache Download (Start of Workflow)**
   - Downloads the latest cache archive from Google Drive
   - Extracts cached HTML and JSON files to appropriate directories
   - Only finished games are cached (status = "Finished")

2. **Data Processing**
   - Downloads only games that aren't already cached
   - Processes new/updated game data
   - Generates statistics and CSV files

3. **Cache Upload (End of Workflow)**
   - Creates a new cache archive with all finished games
   - Uploads to Google Drive for next workflow run
   - Updates cache metadata for tracking

### Benefits

- **Reduces server load**: Avoids redundant downloads from FLBB website
- **Faster execution**: Only downloads new/updated games
- **Reliable**: Automatic fallback if cache is unavailable
- **Private storage**: Cache stored in private Google Drive folder

## Files

### Python Module
- **src/cache_manager.py**: Main cache management logic
  - `CacheManager` class for cache operations
  - ZIP archive creation and extraction
  - Google Drive upload/download integration
  - Cache metadata tracking

### PowerShell Helper
- **scripts/cache_helper.ps1**: PowerShell wrapper functions
  - `Invoke-DownloadCache`: Download cache from Google Drive
  - `Invoke-UploadCache`: Upload cache to Google Drive
  - `Get-CachedGameIds`: Get list of cached game IDs
  - `Test-GameIsCached`: Check if specific game is cached
  - `Show-CacheStatus`: Display cache statistics

### Integration
- **scripts/download-controller.ps1**: Main script with cache integration
  - Calls cache download at start
  - Calls cache upload at end
  - Skips downloading cached files

## Usage

### Command Line (Python)

```bash
# List finished games and cache status
python3 src/cache_manager.py list-finished --data-root data --scripts-root scripts

# Create cache archive
python3 src/cache_manager.py create --data-root data --scripts-root scripts

# Upload cache to Google Drive
python3 src/cache_manager.py upload --data-root data --scripts-root scripts

# Download cache from Google Drive
python3 src/cache_manager.py download --data-root data --scripts-root scripts
```

### PowerShell

```powershell
# Import cache helper functions
. .\scripts\cache_helper.ps1

# Download cache
Invoke-DownloadCache

# Upload cache
Invoke-UploadCache

# Show cache status
Show-CacheStatus

# Check if specific game is cached
Test-GameIsCached -GameId "1101011" -DivisionName "m-enovos-leaguetour-qualificatif"
```

### GitHub Actions

The cache is automatically managed in the `update-csv-data.yml` workflow:

```yaml
- name: 📥 Download raw files and update JSON databases
  run: |
    cd scripts
    pwsh -File download-controller.ps1
  env:
    GOOGLE_DRIVE_CREDENTIALS: ${{ secrets.GOOGLE_DRIVE_CREDENTIALS }}
    GOOGLE_DRIVE_FOLDER_ID: ${{ secrets.GOOGLE_DRIVE_FOLDER_ID }}
```

## Configuration

### Required Secrets

Set these secrets in your GitHub repository:

- `GOOGLE_DRIVE_CREDENTIALS`: Service account JSON credentials
- `GOOGLE_DRIVE_FOLDER_ID`: Google Drive folder ID for cache storage

### Cache Metadata

Cache metadata is stored in `data/cache_metadata.json`:

```json
{
  "last_updated": "2025-11-14T03:30:01.342Z",
  "cached_games": {},
  "drive_file_id": "abc123..."
}
```

This file is automatically managed and should be in `.gitignore`.

## Cache Structure

The cache archive (ZIP file) contains:

```
cache-{season-id}-{timestamp}.zip
├── full-game-stats-raw/
│   ├── division-1-hommes/
│   │   ├── full-game-stats-1101011.html
│   │   └── ...
│   └── ...
├── full-game-stats-output/
│   ├── division-1-hommes/
│   │   ├── full-game-stats-1101011.json
│   │   └── ...
│   └── ...
└── cache_info.json (metadata)
```

## Error Handling

The cache manager includes robust error handling:

- **Cache download fails**: Workflow continues, downloads all games normally
- **Cache upload fails**: Warning logged, but workflow completes successfully
- **Missing credentials**: Falls back to non-cached operation
- **Invalid cache archive**: Skipped, fresh download performed

## Maintenance

### Clearing Cache

To force a fresh download of all games:

1. Delete cache archive from Google Drive
2. Delete local `data/cache_metadata.json`
3. Run the workflow

### Manual Cache Creation

```bash
# Create cache archive locally (for testing)
python3 src/cache_manager.py create --data-root data --scripts-root scripts --output cache-test.zip
```

## Performance Impact

Estimated improvements with caching:

- **First run**: Same as before (no cache available)
- **Subsequent runs**: 
  - Download time: ~90% reduction (only new games)
  - Workflow duration: ~70% faster
  - Server requests: ~90% fewer

Example: With 230 finished games and 10 new games per week:
- Without cache: 240 downloads
- With cache: 10 downloads (96% reduction)

## Troubleshooting

### Cache Not Downloading

Check that:
1. Google Drive credentials are configured
2. Folder ID is correct
3. Service account has access to folder

### Cache Upload Fails

Common issues:
- Service account lacks write permissions
- Folder ID is incorrect
- Network timeout (large archive)

### Games Still Being Re-downloaded

Verify:
1. Games have status "Finished" in `gamesDB.json`
2. Cache was successfully downloaded
3. File paths match expected structure

## Technical Details

### Cache Key

Games are cached based on:
- Game ID (unique identifier)
- Game status ("Finished" only)
- Division name

### File Paths

Cache manager uses paths from `scripts/config.json`:

```json
{
  "directories": {
    "gameScheduleRaw": "game-schedule-raw",
    "fullGameStatsRaw": "full-game-stats-raw",
    "fullGameStatsOutput": "full-game-stats-output"
  }
}
```

### Google Drive Integration

Uses the existing `google_drive_helper.py` module:
- Service account authentication
- File upload/download
- Folder listing
- Automatic retry on failure
