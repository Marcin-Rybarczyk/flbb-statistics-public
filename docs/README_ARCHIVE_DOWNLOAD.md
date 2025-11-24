# Archive Download Scripts

This directory contains scripts for downloading and exporting basketball statistics data for multiple years.

## Quick Start

### Download Last 3 Years (PowerShell)
```powershell
.\download-archive-years.ps1
```

### Download Last 3 Years (Python)
```bash
python download_multiple_years.py
```

## Scripts Overview

### `download-archive-years.ps1`
PowerShell script for downloading and exporting data from multiple years.

**Features:**
- Download data for multiple seasons
- Export each season to a ZIP archive
- Organize data in season-specific directories
- Interactive confirmations and progress tracking

**Usage:**
```powershell
# Last 3 years
.\download-archive-years.ps1

# Last 5 years
.\download-archive-years.ps1 -Years 5

# Specific year range
.\download-archive-years.ps1 -StartYear 2020 -EndYear 2023

# Specific seasons
.\download-archive-years.ps1 -SeasonIds "2022-2023,2023-2024"

# Export only (no download)
.\download-archive-years.ps1 -ExportOnly

# Get full help
Get-Help .\download-archive-years.ps1 -Full
```

### `download_multiple_years.py`
Cross-platform Python script for the same functionality.

**Usage:**
```bash
# Last 3 years
python download_multiple_years.py

# Last 5 years
python download_multiple_years.py --years 5

# Specific year range
python download_multiple_years.py --start-year 2020 --end-year 2023

# Specific seasons
python download_multiple_years.py --seasons "2022-2023,2023-2024"

# Export only (no download)
python download_multiple_years.py --export-only

# Get full help
python download_multiple_years.py --help
```

## How It Works

1. **Backup Configuration** - Current `config.json` is backed up
2. **For Each Season:**
   - Update `config.json` with season ID
   - Run `download-controller.ps1` to download data
   - Run `export_data.py` to create archive
   - Move data to `season-data/{SEASON_ID}/`
3. **Restore Configuration** - Original config is restored

## Output

### Archives
ZIP files are created in `archives/`:
```
archives/
├── raw-data-2022-2023-20241115120000.zip
├── raw-data-2023-2024-20241115130000.zip
└── raw-data-2024-2025-20241115140000.zip
```

### Season Data
Extracted data is organized in `season-data/`:
```
season-data/
├── 2022-2023/
│   └── data/
│       ├── full-game-stats.csv
│       ├── gamesDB.json
│       └── ...
├── 2023-2024/
│   └── data/
└── 2024-2025/
    └── data/
```

## Requirements

### PowerShell Script
- PowerShell 5.1+ or PowerShell Core 7+
- HtmlAgilityPack.dll (included in `Net40/`)

### Python Script
- Python 3.7+
- PowerShell (for running download scripts)
- Python packages from `requirements.txt`

## Documentation

For detailed documentation, see:
- [Archive Download Guide](../docs/ARCHIVE_DOWNLOAD_GUIDE.md) - Complete guide with examples
- [Data Export/Import](../docs/DATA_EXPORT_IMPORT.md) - Using exported archives

## Common Parameters

| Parameter | PowerShell | Python | Description |
|-----------|-----------|--------|-------------|
| Number of years | `-Years 3` | `--years 3` | Download last N years |
| Year range | `-StartYear 2020 -EndYear 2023` | `--start-year 2020 --end-year 2023` | Specific range |
| Specific seasons | `-SeasonIds "2022-2023,2023-2024"` | `--seasons "2022-2023,2023-2024"` | Comma-separated list |
| Export only | `-ExportOnly` | `--export-only` | Skip download, only export |
| Skip download | `-SkipDownload` | `--skip-download` | Skip download phase |
| Keep data | `-KeepData` | `--keep-data` | Keep in main data/ directory |

## Troubleshooting

### PowerShell Execution Policy
If you get "cannot be loaded because running scripts is disabled":
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Dependencies
If you get import errors:
```bash
pip install -r ../requirements.txt
```

### PowerShell Not Found (Python)
Install PowerShell Core:
- Windows: `winget install Microsoft.PowerShell`
- Linux/Mac: See https://github.com/PowerShell/PowerShell

## Examples

### Example 1: Build Historical Database
Download data for the last 10 years and keep everything:
```powershell
.\download-archive-years.ps1 -Years 10 -KeepData
```

### Example 2: Archive Specific Seasons
Export archives for specific seasons without re-downloading:
```bash
python download_multiple_years.py --seasons "2020-2021,2021-2022,2022-2023" --export-only
```

### Example 3: Year Range
Download all data from 2018 to 2024:
```powershell
.\download-archive-years.ps1 -StartYear 2018 -EndYear 2024
```

## Testing

Run the test suite to verify everything works:
```bash
python ../tests/test_archive_download.py
```

## See Also

- `download-controller.ps1` - Main download script
- `export_data.py` - Data export script
- `import_data.py` - Data import script
- `config.json` - Configuration file
