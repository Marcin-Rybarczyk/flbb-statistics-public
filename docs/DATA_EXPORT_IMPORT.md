# Data Export and Import Guide

This guide explains how to export and import season data for the FLBB Statistics application. This is useful for:
- Creating backups of season data
- Archiving data from past years
- Sharing data between installations
- Restoring historical data

## Table of Contents

- [Quick Start](#quick-start)
- [Export Data](#export-data)
  - [Using the Command-Line Script](#using-the-command-line-script-export)
  - [Using the Admin Interface](#using-the-admin-interface-export)
- [Import Data](#import-data)
  - [Using the Command-Line Script](#using-the-command-line-script-import)
  - [Using the Admin Interface](#using-the-admin-interface-import)
- [Archive Format](#archive-format)
- [Use Cases](#use-cases)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Export Current Data
```bash
# Export with default settings
python scripts/export_data.py

# Export to specific file
python scripts/export_data.py -o my-backup.zip
```

### Import Data
```bash
# List available archives
python scripts/import_data.py --list

# Validate an archive
python scripts/import_data.py archive.zip --validate-only

# Import to a new directory
python scripts/import_data.py archive.zip
```

## Export Data

### Using the Command-Line Script (Export)

The `scripts/export_data.py` script creates a ZIP archive containing all essential data files.

#### Basic Usage

```bash
# Export with default settings
python scripts/export_data.py
```

This creates an archive in the `archives/` directory with a name like:
`raw-data-2025-2026-20241113143000.zip`

#### Export Options

```bash
# Export to a specific file
python scripts/export_data.py -o /path/to/my-archive.zip

# Include raw HTML data (larger archive)
python scripts/export_data.py --include-raw

# Use a custom config file
python scripts/export_data.py --config my-config.json

# Override season ID
python scripts/export_data.py --season 2023-2024
```

#### What Gets Exported

By default, the following files are included:
- `data/full-game-stats.csv` - Main statistics data
- `data/gamesDB.json` - Game database
- `data/gameScheduleDB.json` - Game schedule
- `data/players-database.csv` - Player database

With `--include-raw` flag, additionally includes:
- `data/game-schedule-raw/` - Raw HTML game schedules
- `data/full-game-stats-raw/` - Raw HTML game statistics
- `data/full-game-stats-output/` - Processed JSON files

#### Example Output

```
======================================================================
FLBB Statistics Data Export
======================================================================

Season ID: 2025-2026
Output file: archives/raw-data-2025-2026-20241113143000.zip
Include raw data: False

✓ Found: data/full-game-stats.csv (9.29 MB)
✓ Found: data/gamesDB.json (0.24 MB)
✓ Found: data/gameScheduleDB.json (0.00 MB)
✓ Found: data/players-database.csv (0.10 MB)

📦 Creating archive: archives/raw-data-2025-2026-20241113143000.zip
----------------------------------------------------------------------
  Added: data/full-game-stats.csv
  Added: data/gamesDB.json
  Added: data/gameScheduleDB.json
  Added: data/players-database.csv
----------------------------------------------------------------------
✅ SUCCESS: Archive created successfully!

📊 Summary:
   Files archived: 4
   Archive size: 0.74 MB
   Archive path: archives/raw-data-2025-2026-20241113143000.zip

💡 To import this archive:
   python scripts/import_data.py archives/raw-data-2025-2026-20241113143000.zip
======================================================================
```

### Using the Admin Interface (Export)

1. Navigate to the Admin page: `/admin`
2. Scroll to the "Export Current Data" section
3. Optionally check "Include raw HTML data" for a complete backup
4. Click "📥 Export Data Archive"
5. The ZIP file will download automatically

## Import Data

### Using the Command-Line Script (Import)

The `scripts/import_data.py` script imports data from a previously exported archive.

#### List Available Archives

```bash
python scripts/import_data.py --list
```

This shows all archives in the `archives/` directory with their details.

#### Validate an Archive

```bash
python scripts/import_data.py archive.zip --validate-only
```

This checks if the archive is valid without importing it.

#### Import to a New Directory

```bash
# Import with auto-generated directory name
python scripts/import_data.py archive.zip

# Import to a specific directory
python scripts/import_data.py archive.zip -t season-2023-2024
```

#### Restore to Current Data Directory (⚠️ CAUTION!)

```bash
# This will REPLACE your current data!
python scripts/import_data.py archive.zip --restore --force
```

**WARNING**: The `--restore` mode replaces files in the `data/` directory. A backup is created automatically, but use with caution!

#### Example Output

```
======================================================================
FLBB Statistics Data Import
======================================================================

✓ Archive validated successfully
  Season ID: 2025-2026
  Files: 4

📂 Extracting to: /home/user/archive-2025-2026-20241113143500
----------------------------------------------------------------------
  Extracted: data/full-game-stats.csv
  Extracted: data/gamesDB.json
  Extracted: data/gameScheduleDB.json
  Extracted: data/players-database.csv
----------------------------------------------------------------------
✅ SUCCESS: Data imported successfully!

📊 Summary:
   Files extracted: 4
   Target directory: /home/user/archive-2025-2026-20241113143500

💡 To use this data:
   1. Copy files from archive-2025-2026-20241113143500/ to data/
   2. Or update your config to point to this directory
   3. Restart the application
======================================================================
```

### Using the Admin Interface (Import)

1. Navigate to the Admin page: `/admin`
2. Scroll to the "Import Season Archive" section
3. Click "Choose File" and select your archive
4. Click "📤 Import Archive"
5. Wait for the import to complete
6. The page will refresh automatically

The imported data will be extracted to a new directory (e.g., `archive-2025-2026-20241113143500/`).

## Archive Format

Archives created by the export script follow a specific naming convention:

```
raw-data-{SEASON_ID}-{TIMESTAMP}.zip
```

For example:
- `raw-data-2025-2026-20241113143000.zip`
- `raw-data-2023-2024-20230915120000.zip`

### Archive Contents

A standard archive (without `--include-raw`) contains:
```
archive.zip
├── data/
│   ├── full-game-stats.csv
│   ├── gamesDB.json
│   ├── gameScheduleDB.json
│   └── players-database.csv
```

An archive with raw data (with `--include-raw`) additionally contains:
```
archive.zip
├── data/
│   ├── full-game-stats.csv
│   ├── gamesDB.json
│   ├── gameScheduleDB.json
│   ├── players-database.csv
│   ├── game-schedule-raw/
│   │   └── [HTML files]
│   ├── full-game-stats-raw/
│   │   └── [HTML files]
│   └── full-game-stats-output/
│       └── [JSON files]
```

## Use Cases

### 1. Create a Backup Before Updates

```bash
# Export current data before making changes
python scripts/export_data.py -o backup-before-update.zip
```

### 2. Archive End-of-Season Data

```bash
# Export with raw data for complete archive
python scripts/export_data.py --season 2023-2024 --include-raw
```

### 3. Import Previous Season Data

```bash
# Import to a separate directory
python scripts/import_data.py raw-data-2023-2024.zip -t seasons/2023-2024

# Copy specific files from imported directory to current data
cp seasons/2023-2024/data/full-game-stats.csv data/
```

### 4. Share Data with Another Installation

```bash
# On source machine
python scripts/export_data.py -o transfer.zip

# Transfer file to destination machine
scp transfer.zip user@destination:/path/to/flbb-statistics/

# On destination machine
python scripts/import_data.py transfer.zip --restore --force
```

### 5. Validate an Archive Before Import

```bash
# Check if archive is valid
python scripts/import_data.py archive.zip --validate-only

# If valid, proceed with import
python scripts/import_data.py archive.zip
```

## Troubleshooting

### Archive Validation Fails

**Problem**: Import script reports "Archive is INVALID"

**Solutions**:
1. Check if the ZIP file is corrupted:
   ```bash
   unzip -t archive.zip
   ```
2. Verify the archive was created correctly:
   ```bash
   unzip -l archive.zip
   ```
3. Ensure the archive contains the required files

### Export Script Can't Find Data Files

**Problem**: Export reports missing files

**Solutions**:
1. Check if data files exist:
   ```bash
   ls -la data/
   ```
2. Verify the config file is correct:
   ```bash
   cat scripts/config.json
   ```
3. Run from the repository root directory

### Import Overwrites Existing Files

**Problem**: Accidentally replaced current data with import

**Solutions**:
1. Check for backup directory (created automatically):
   ```bash
   ls -la data-backup-*
   ```
2. Restore from backup:
   ```bash
   cp -r data-backup-TIMESTAMP/* data/
   ```

### Large Archive Size

**Problem**: Archive is too large when using `--include-raw`

**Solutions**:
1. Export without raw data:
   ```bash
   python scripts/export_data.py
   ```
2. Raw data can be re-downloaded if needed
3. Only use `--include-raw` for archival purposes

### Permission Denied

**Problem**: Can't create archive or extract files

**Solutions**:
1. Check directory permissions:
   ```bash
   ls -la archives/
   ```
2. Ensure write permissions:
   ```bash
   chmod u+w archives/
   ```
3. Run with appropriate permissions

## Best Practices

1. **Regular Backups**: Export data regularly, especially before updates
2. **Archive Organization**: Keep archives in a dedicated directory
3. **Naming Convention**: Use descriptive names for manual exports
4. **Validation**: Always validate archives before relying on them
5. **Documentation**: Note what each archive contains and when it was created
6. **Storage**: Store important archives in multiple locations
7. **Testing**: Test import process with a copy of data before production use

## Integration with Other Tools

### Google Drive Upload

After exporting, you can upload to Google Drive:

```bash
# Export data
python scripts/export_data.py

# Upload to Google Drive (if configured)
python scripts/post_process.py --skip-csv
```

### Automated Backups

Add to crontab for daily backups:

```cron
# Daily backup at 2 AM
0 2 * * * cd /path/to/flbb-statistics && python scripts/export_data.py
```

### Version Control

For development, track exported archives in git (if small enough):

```bash
git add archives/raw-data-dev-backup.zip
git commit -m "Add development data backup"
```

## See Also

- [CSV Generation Workflow](CSV_GENERATION_WORKFLOW.md) - How data is processed
- [Google Drive Integration](GOOGLE_DRIVE_README.md) - Automated uploads
- [MongoDB Integration](MONGODB_INTEGRATION.md) - Alternative data storage
- [Admin Interface](API_ENDPOINTS.md#admin-endpoints) - Web-based management
