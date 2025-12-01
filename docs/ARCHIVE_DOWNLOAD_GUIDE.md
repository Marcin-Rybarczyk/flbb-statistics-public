# Archive Data Download Guide

This guide explains how to download and export basketball statistics data for multiple years from the Luxembourg Basketball Federation archives.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Scripts Available](#scripts-available)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Data Organization](#data-organization)
- [Troubleshooting](#troubleshooting)

## Overview

The FLBB Statistics application can download and archive data from multiple seasons. This is useful for:
- Building a historical database of basketball statistics
- Analyzing trends across multiple years
- Creating comprehensive season comparisons
- Archiving data from past years

Two scripts are available:
1. **PowerShell Script** (`download-archive-years.ps1`) - For Windows and PowerShell Core
2. **Python Script** (`download_multiple_years.py`) - Cross-platform solution

Both scripts perform the same operations:
1. Iterate through specified years/seasons
2. Download game data for each season
3. Process and export data to ZIP archives
4. Organize data in season-specific directories

## Quick Start

### Using PowerShell (Recommended for Windows)

```powershell
# Download last 3 years (default)
.\scripts\download-archive-years.ps1

# Download last 5 years
.\scripts\download-archive-years.ps1 -Years 5
```

### Using Python (Cross-platform)

```bash
# Download last 3 years (default)
python scripts/download_multiple_years.py

# Download last 5 years
python scripts/download_multiple_years.py --years 5
```

## Scripts Available

### PowerShell: `download-archive-years.ps1`

**Location**: `scripts/download-archive-years.ps1`

**Requirements**:
- PowerShell 5.1+ or PowerShell Core 7+
- HtmlAgilityPack.dll (included in `scripts/Net40/`)

**Features**:
- Native PowerShell implementation
- Better Windows integration
- Color-coded output
- Interactive confirmations

### Python: `download_multiple_years.py`

**Location**: `scripts/download_multiple_years.py`

**Requirements**:
- Python 3.7+
- PowerShell (pwsh or powershell) for running download scripts
- Required Python packages (from `requirements.txt`)

**Features**:
- Cross-platform compatibility
- Easier integration with other Python scripts
- Consistent with existing Python tooling

## Usage Examples

### Download Last N Years

**PowerShell**:
```powershell
# Last 3 years (default)
.\scripts\download-archive-years.ps1

# Last 5 years
.\scripts\download-archive-years.ps1 -Years 5

# Last 10 years
.\scripts\download-archive-years.ps1 -Years 10
```

**Python**:
```bash
# Last 3 years (default)
python scripts/download_multiple_years.py

# Last 5 years
python scripts/download_multiple_years.py --years 5

# Last 10 years
python scripts/download_multiple_years.py --years 10
```

### Download Specific Year Range

**PowerShell**:
```powershell
# Download seasons from 2020 to 2023
.\scripts\download-archive-years.ps1 -StartYear 2020 -EndYear 2023

# This will download:
# - 2020-2021
# - 2021-2022
# - 2022-2023
# - 2023-2024
```

**Python**:
```bash
# Download seasons from 2020 to 2023
python scripts/download_multiple_years.py --start-year 2020 --end-year 2023
```

### Download Specific Seasons

**PowerShell**:
```powershell
# Download specific season IDs
.\scripts\download-archive-years.ps1 -SeasonIds "2022-2023,2023-2024,2024-2025"
```

**Python**:
```bash
# Download specific season IDs
python scripts/download_multiple_years.py --seasons "2022-2023,2023-2024,2024-2025"
```

### Export Only (No Download)

If you already have data downloaded and just want to create archives:

**PowerShell**:
```powershell
.\scripts\download-archive-years.ps1 -ExportOnly -SeasonIds "2023-2024"
```

**Python**:
```bash
python scripts/download_multiple_years.py --export-only --seasons "2023-2024"
```

### Keep Data in Main Directory

By default, data is moved to season-specific directories after export. To keep data in the main `data/` directory:

**PowerShell**:
```powershell
.\scripts\download-archive-years.ps1 -KeepData -Years 3
```

**Python**:
```bash
python scripts/download_multiple_years.py --keep-data --years 3
```

## Configuration

### Season ID Format

Season IDs follow the format: `YYYY-YYYY`
- `2023-2024` - Season starting in 2023 and ending in 2024
- `2024-2025` - Season starting in 2024 and ending in 2025

### Configuration File

Both scripts use `scripts/config.json` for configuration. The scripts will:
1. Backup the current config
2. Update it for each season being processed
3. Restore the original config when done

**Important**: The original configuration is always restored, even if the script is interrupted.

### Divisions Included

To change which divisions are downloaded, edit `scripts/config.json`:

```json
{
  "processing": {
    "divisionsIncluded": [
      "Division 1 Hommes",
      "Division 2 Hommes",
      "Division 3 Hommes",
      "Division 4 Hommes",
      "Enovos League Hommes",
      "Nationale 2 Hommes",
      "Nationale 3 Hommes"
    ]
  }
}
```

## Data Organization

### Directory Structure

After running the scripts, data is organized as follows:

```
flbb-statistics/
├── archives/                           # ZIP archives for each season
│   ├── raw-data-2022-2023-20241115120000.zip
│   ├── raw-data-2023-2024-20241115130000.zip
│   └── raw-data-2024-2025-20241115140000.zip
├── season-data/                        # Extracted season data
│   ├── 2022-2023/
│   │   ├── data/
│   │   │   ├── full-game-stats.csv
│   │   │   ├── gamesDB.json
│   │   │   ├── gameScheduleDB.json
│   │   │   ├── players-database.csv
│   │   │   ├── game-schedule-raw/
│   │   │   ├── full-game-stats-raw/
│   │   │   └── full-game-stats-output/
│   ├── 2023-2024/
│   │   └── data/
│   └── 2024-2025/
│       └── data/
└── data/                              # Current season data
    ├── full-game-stats.csv
    ├── gamesDB.json
    └── ...
```

### Archive Contents

Each ZIP archive contains:
- `data/full-game-stats.csv` - Main statistics CSV
- `data/gamesDB.json` - Game database
- `data/gameScheduleDB.json` - Schedule information
- `data/players-database.csv` - Player database
- `data/game-schedule-raw/` - Raw HTML schedules (if `--include-raw`)
- `data/full-game-stats-raw/` - Raw HTML game stats (if `--include-raw`)
- `data/full-game-stats-output/` - Processed JSON files (if `--include-raw`)

### Using Archived Data

To use data from a specific season:

1. **Option 1**: Import using the import script
   ```bash
   python scripts/import_data.py archives/raw-data-2023-2024-*.zip --restore --force
   ```

2. **Option 2**: Copy from season directory
   ```bash
   cp -r season-data/2023-2024/data/* data/
   ```

3. **Option 3**: Update Flask app to read from season directory
   ```python
   # In app.py or utils.py
   DATA_DIR = Path("season-data/2023-2024/data")
   ```

## Troubleshooting

### PowerShell Script Not Found

**Problem**: `download-controller.ps1: The system cannot find the file specified`

**Solution**: Ensure you're running from the repository root:
```powershell
cd path/to/flbb-statistics-public
.\scripts\download-archive-years.ps1
```

### PowerShell Not Found (Python Script)

**Problem**: `PowerShell not found. Please install PowerShell Core (pwsh)`

**Solution**: Install PowerShell Core:
- **Windows**: Already installed or use Windows Package Manager
  ```powershell
  winget install Microsoft.PowerShell
  ```
- **Linux/Mac**: Follow instructions at https://github.com/PowerShell/PowerShell

### Python Dependencies Missing

**Problem**: `ModuleNotFoundError: No module named 'pandas'`

**Solution**: Install required packages:
```bash
pip install -r requirements.txt
```

### Download Fails for Old Seasons

**Problem**: Some old seasons have no data or incomplete data

**Solution**: This is expected if:
- The season data was never published online
- The data was removed from the website
- The URL structure changed for older seasons

The script will continue processing other seasons even if one fails.

### Archive Already Exists

**Problem**: Archive file already exists

**Solution**: Archives use timestamps in filenames to avoid conflicts. Each run creates a new archive:
- `raw-data-2023-2024-20241115120000.zip`
- `raw-data-2023-2024-20241115130000.zip` (different timestamp)

### Disk Space Issues

**Problem**: Not enough disk space

**Solution**:
1. Use `--export-only` to skip re-downloading
2. Don't use `--include-raw` to create smaller archives
3. Clean up old archives after verification
4. Process fewer years at once

### Configuration Not Restored

**Problem**: Config.json wasn't restored after interruption

**Solution**: Manually restore from backup:
```bash
# PowerShell
Copy-Item scripts\config.json.backup scripts\config.json

# Linux/Mac
cp scripts/config.json.backup scripts/config.json
```

### Network/Connection Issues

**Problem**: Downloads fail due to network errors

**Solution**:
1. Check internet connection
2. Verify FLBB website is accessible: https://www.luxembourg.basketball
3. Try running for fewer seasons at once
4. Use `--skip-download` to retry export only

## Advanced Usage

### Batch Processing with Custom Parameters

Create a batch script to download specific seasons with custom settings:

**PowerShell**:
```powershell
# download-seasons.ps1
$seasons = @("2020-2021", "2021-2022", "2022-2023")

foreach ($season in $seasons) {
    Write-Host "Processing $season..."
    .\scripts\download-archive-years.ps1 -SeasonIds $season -KeepData
    
    # Custom processing here
    # ...
}
```

**Bash**:
```bash
#!/bin/bash
# download-seasons.sh
seasons=("2020-2021" "2021-2022" "2022-2023")

for season in "${seasons[@]}"; do
    echo "Processing $season..."
    python scripts/download_multiple_years.py --seasons "$season" --keep-data
    
    # Custom processing here
    # ...
done
```

### Scheduled Downloads

Set up a scheduled task to download data automatically:

**Windows Task Scheduler**:
1. Create new task
2. Trigger: Daily at 2 AM
3. Action: `pwsh.exe`
4. Arguments: `-File C:\path\to\flbb-statistics-public\scripts\download-archive-years.ps1 -ExportOnly`

**Linux/Mac cron**:
```cron
# Daily at 2 AM
0 2 * * * cd /path/to/flbb-statistics-public && python scripts/download_multiple_years.py --export-only
```

### Integration with Other Scripts

Use within other automation workflows:

```python
# automation.py
import subprocess
import sys

def download_historical_data():
    """Download last 3 years of data."""
    result = subprocess.run([
        sys.executable,
        'scripts/download_multiple_years.py',
        '--years', '3',
        '--export-only'
    ])
    return result.returncode == 0

if __name__ == '__main__':
    if download_historical_data():
        print("Historical data downloaded successfully")
        # Continue with other processing...
    else:
        print("Failed to download historical data")
        sys.exit(1)
```

## See Also

- [Data Export and Import Guide](DATA_EXPORT_IMPORT.md) - Manual export/import procedures
- [CSV Generation Workflow](CSV_GENERATION_WORKFLOW.md) - How data is processed
- [Google Drive Integration](GOOGLE_DRIVE_README.md) - Automated cloud backups
- [GitHub Actions Usage](GITHUB_ACTIONS_USAGE.md) - Automated workflows

## Best Practices

1. **Start Small**: Test with 1-2 seasons before processing many years
2. **Verify Archives**: Use `import_data.py --validate-only` to verify archives
3. **Backup First**: Keep backups of current data before bulk operations
4. **Monitor Progress**: Watch output for errors or warnings
5. **Clean Up**: Remove old archives after verification to save space
6. **Document**: Keep notes on which seasons were downloaded and when
7. **Test Imports**: Verify archived data can be imported successfully
8. **Network**: Run during off-peak hours if processing many years
