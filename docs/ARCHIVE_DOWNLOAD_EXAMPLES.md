# Multi-Year Archive Download - Examples and Walkthrough

This document provides step-by-step examples for downloading and exporting basketball statistics data for multiple years.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Basic Usage Examples](#basic-usage-examples)
- [Advanced Scenarios](#advanced-scenarios)
- [Workflow Examples](#workflow-examples)
- [Integration Examples](#integration-examples)
- [Troubleshooting Examples](#troubleshooting-examples)

## Prerequisites

Before starting, ensure you have:

1. **PowerShell** (for PowerShell script):
   - Windows: PowerShell 5.1+ (built-in) or PowerShell Core 7+
   - Linux/Mac: PowerShell Core 7+

2. **Python 3.7+** (for Python script):
   ```bash
   python --version  # Should show 3.7 or higher
   ```

3. **Required Python packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Internet connection** to download data from FLBB website

## Basic Usage Examples

### Example 1: Download Last 3 Years (Default)

This is the simplest use case - download data for the last 3 basketball seasons.

**Using PowerShell:**
```powershell
# Navigate to repository
cd C:\path\to\flbb-statistics-public

# Run the script
.\scripts\download-archive-years.ps1

# When prompted, type 'yes' to confirm
# Output will show:
# - Season IDs being processed (e.g., 2024-2025, 2023-2024, 2022-2023)
# - Download progress for each season
# - Archive creation progress
# - Final summary
```

**Using Python:**
```bash
# Navigate to repository
cd /path/to/flbb-statistics-public

# Run the script
python scripts/download_multiple_years.py

# When prompted, type 'yes' to confirm
```

**What happens:**
1. Script backs up `scripts/config.json`
2. For each season (e.g., 2024-2025, 2023-2024, 2022-2023):
   - Updates config.json with season ID
   - Runs download-controller.ps1
   - Exports data to ZIP archive
   - Moves data to `season-data/{SEASON_ID}/`
3. Restores original config.json
4. Shows summary of results

**Expected output structure:**
```
flbb-statistics-public/
├── archives/
│   ├── raw-data-2022-2023-20241115120000.zip
│   ├── raw-data-2023-2024-20241115130000.zip
│   └── raw-data-2024-2025-20241115140000.zip
└── season-data/
    ├── 2022-2023/
    ├── 2023-2024/
    └── 2024-2025/
```

### Example 2: Download Last 5 Years

Download data for more years to build a larger historical database.

**Using PowerShell:**
```powershell
.\scripts\download-archive-years.ps1 -Years 5
```

**Using Python:**
```bash
python scripts/download_multiple_years.py --years 5
```

**Result:** Downloads and archives 5 seasons (e.g., 2024-2025 through 2020-2021)

### Example 3: Download Specific Year Range

Download data for a specific range of years, useful for filling gaps or archiving a specific period.

**Using PowerShell:**
```powershell
# Download seasons from 2019-2020 through 2022-2023
.\scripts\download-archive-years.ps1 -StartYear 2019 -EndYear 2022
```

**Using Python:**
```bash
# Same range
python scripts/download_multiple_years.py --start-year 2019 --end-year 2022
```

**Seasons downloaded:**
- 2019-2020
- 2020-2021
- 2021-2022
- 2022-2023

## Advanced Scenarios

### Example 4: Download Specific Seasons Only

When you need data for specific seasons (not consecutive years).

**Using PowerShell:**
```powershell
.\scripts\download-archive-years.ps1 -SeasonIds "2020-2021,2022-2023,2024-2025"
```

**Using Python:**
```bash
python scripts/download_multiple_years.py --seasons "2020-2021,2022-2023,2024-2025"
```

**Use case:** You already have 2021-2022 and 2023-2024, so you only download the missing seasons.

### Example 5: Export Only (Re-export Existing Data)

Create new archives from already downloaded data without re-downloading.

**Using PowerShell:**
```powershell
.\scripts\download-archive-years.ps1 -ExportOnly -SeasonIds "2023-2024"
```

**Using Python:**
```bash
python scripts/download_multiple_years.py --export-only --seasons "2023-2024"
```

**Use cases:**
- Archive was corrupted and needs to be recreated
- Want to create archive with different compression settings
- Data was downloaded manually and needs archiving

### Example 6: Keep Data in Main Directory

By default, data is moved to `season-data/`. Use this option to keep it in the main `data/` directory.

**Using PowerShell:**
```powershell
.\scripts\download-archive-years.ps1 -Years 3 -KeepData
```

**Using Python:**
```bash
python scripts/download_multiple_years.py --years 3 --keep-data
```

**Use case:** You want to immediately use the downloaded data in the Flask app.

## Workflow Examples

### Workflow 1: Complete Historical Archive

Build a complete archive of all available historical data.

```powershell
# Step 1: Download the last 10 years
.\scripts\download-archive-years.ps1 -Years 10

# Step 2: Verify archives were created
Get-ChildItem archives\raw-data-*.zip | Sort-Object LastWriteTime

# Step 3: Validate one archive
python scripts\import_data.py archives\raw-data-2023-2024-*.zip --validate-only

# Step 4: List all archives with details
python scripts\import_data.py --list
```

### Workflow 2: Incremental Archive Updates

Regularly update your archive with new seasons.

```bash
# Run monthly to archive the current season
python scripts/download_multiple_years.py --seasons "2024-2025" --export-only

# Or set up a scheduled task (Linux/Mac cron example)
# Add to crontab: 0 0 1 * * cd /path/to/repo && python scripts/download_multiple_years.py --seasons "2024-2025" --export-only
```

### Workflow 3: Build Comparative Analysis Database

Download specific seasons for year-over-year comparison.

```powershell
# Download same periods from different years
$seasons = @("2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025")

foreach ($season in $seasons) {
    Write-Host "Processing season: $season"
    .\scripts\download-archive-years.ps1 -SeasonIds $season -KeepData
    
    # Run custom analysis here
    # python analyze_season.py --season $season
    
    # Archive the results
    .\scripts\download-archive-years.ps1 -SeasonIds $season -ExportOnly
}
```

### Workflow 4: Disaster Recovery Archive

Create comprehensive backups including all raw data.

```bash
# Download with all raw HTML and JSON files
python scripts/download_multiple_years.py --years 5

# Verify all archives
for archive in archives/raw-data-*.zip; do
    echo "Validating $archive..."
    python scripts/import_data.py "$archive" --validate-only
done

# Upload to cloud storage (example with rclone)
# rclone sync archives/ mycloud:flbb-backups/archives/
```

## Integration Examples

### Integration 1: Import Archived Season

After downloading archives, import a specific season for analysis.

```bash
# Download archives
python scripts/download_multiple_years.py --years 3

# List available archives
python scripts/import_data.py --list

# Import 2022-2023 season to working directory
python scripts/import_data.py archives/raw-data-2022-2023-*.zip --restore --force

# Now the Flask app will use 2022-2023 data
python src/app.py
```

### Integration 2: Compare Multiple Seasons

Extract each season to separate directories for comparison.

```bash
# Download 3 seasons
python scripts/download_multiple_years.py --years 3

# Import each to separate directory
python scripts/import_data.py archives/raw-data-2022-2023-*.zip -t analysis/2022-2023
python scripts/import_data.py archives/raw-data-2023-2024-*.zip -t analysis/2023-2024
python scripts/import_data.py archives/raw-data-2024-2025-*.zip -t analysis/2024-2025

# Run comparison analysis
# python compare_seasons.py analysis/
```

### Integration 3: MongoDB Import from Archives

Download archives, then import to MongoDB.

```bash
# Download multiple years
python scripts/download_multiple_years.py --start-year 2020 --end-year 2024

# For each season, import to MongoDB
for season_dir in season-data/*/; do
    season=$(basename "$season_dir")
    echo "Importing $season to MongoDB..."
    
    # Copy data to main directory temporarily
    cp -r "$season_dir/data/"* data/
    
    # Import to MongoDB
    python scripts/export_csv_to_mongodb.py
    
    # Clean up
    rm -f data/full-game-stats.csv data/gamesDB.json
done
```

### Integration 4: Automated GitHub Actions

Create a GitHub Actions workflow to automatically archive data.

```yaml
# .github/workflows/archive-season.yml
name: Archive Current Season

on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly on the 1st
  workflow_dispatch:

jobs:
  archive:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Download and archive current season
        run: |
          SEASON=$(date +%Y)-$(($(date +%Y) + 1))
          python scripts/download_multiple_years.py --seasons "$SEASON"
      
      - name: Upload archive to releases
        uses: actions/upload-artifact@v2
        with:
          name: season-archives
          path: archives/*.zip
```

## Troubleshooting Examples

### Problem 1: PowerShell Execution Policy Error

**Error:**
```
download-archive-years.ps1 cannot be loaded because running scripts is disabled on this system.
```

**Solution:**
```powershell
# Check current policy
Get-ExecutionPolicy

# Set to allow scripts (user level)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run the script again
.\scripts\download-archive-years.ps1
```

### Problem 2: Python Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'pandas'
```

**Solution:**
```bash
# Install all requirements
pip install -r requirements.txt

# Or install specific package
pip install pandas

# Verify installation
python -c "import pandas; print('pandas version:', pandas.__version__)"
```

### Problem 3: Download Fails for Old Seasons

**Error:**
```
⚠ Download failed for season 2015-2016
```

**Solution:**
This is expected for very old seasons that may not have data online.

```bash
# Continue with available seasons
python scripts/download_multiple_years.py --start-year 2018 --end-year 2024

# Or skip failed seasons manually
python scripts/download_multiple_years.py --seasons "2018-2019,2019-2020,2020-2021"
```

### Problem 4: Disk Space Issues

**Error:**
```
OSError: [Errno 28] No space left on device
```

**Solution:**
```bash
# Check disk space
df -h

# Clean up old archives
rm archives/raw-data-*-old.zip

# Download fewer years at once
python scripts/download_multiple_years.py --years 2

# Or don't include raw data
# Modify export_data.py to skip --include-raw
```

### Problem 5: Configuration Not Restored

**Problem:** Script was interrupted and config.json wasn't restored.

**Solution:**
```bash
# Check if backup exists
ls scripts/config.json.backup

# Manually restore
cp scripts/config.json.backup scripts/config.json

# Or reset to current season
# Edit scripts/config.json and set:
# "seasonId": "2024-2025"
```

## Tips and Best Practices

1. **Start Small:** Test with 1-2 seasons before downloading many years
   ```bash
   python scripts/download_multiple_years.py --seasons "2023-2024"
   ```

2. **Validate Archives:** Always validate before relying on them
   ```bash
   python scripts/import_data.py archives/raw-data-*.zip --validate-only
   ```

3. **Backup First:** Keep a backup of current data
   ```bash
   cp -r data/ data-backup-$(date +%Y%m%d)/
   ```

4. **Monitor Progress:** Watch the output for errors
   ```bash
   python scripts/download_multiple_years.py --years 3 | tee download-log.txt
   ```

5. **Clean Up:** Remove old archives after verification
   ```bash
   # Keep only the most recent archive for each season
   python scripts/cleanup_old_archives.py
   ```

6. **Document:** Keep a log of what you've downloaded
   ```bash
   echo "$(date): Downloaded seasons 2020-2024" >> archive-log.txt
   ```

## See Also

- [ARCHIVE_DOWNLOAD_GUIDE.md](ARCHIVE_DOWNLOAD_GUIDE.md) - Complete reference guide
- [DATA_EXPORT_IMPORT.md](DATA_EXPORT_IMPORT.md) - Export and import procedures
- [README_ARCHIVE_DOWNLOAD.md](README_ARCHIVE_DOWNLOAD.md) - Quick reference

## Questions?

For common questions and answers, see the main documentation or open an issue on GitHub.
