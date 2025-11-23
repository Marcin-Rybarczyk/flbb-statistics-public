#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Download and export FLBB basketball data for multiple years from archives.

.DESCRIPTION
    This script downloads game data for specified years from the Luxembourg Basketball Federation.
    It can process multiple seasons and export each year's data to separate archives.
    
    The script:
    1. Iterates through specified years (default: last 3 years)
    2. For each year, updates config.json with the season ID
    3. Runs the download-controller.ps1 script to download data
    4. Exports the data to a season-specific archive
    5. Moves archived data to season-specific directories

.PARAMETER Years
    Number of past years to download (default: 3)
    Example: -Years 5 will download data for the last 5 years

.PARAMETER StartYear
    Starting year for the range (e.g., 2020)
    If specified with EndYear, downloads data for that specific range

.PARAMETER EndYear
    Ending year for the range (e.g., 2023)
    If specified with StartYear, downloads data for that specific range

.PARAMETER SeasonIds
    Comma-separated list of specific season IDs to download
    Example: -SeasonIds "2022-2023,2023-2024,2024-2025"

.PARAMETER ExportOnly
    Only export existing data without downloading new data

.PARAMETER SkipDownload
    Skip the download phase, only process existing data

.PARAMETER KeepData
    Keep downloaded data in data/ directory after export (don't move to archives)

.EXAMPLE
    .\download-archive-years.ps1
    Downloads data for the last 3 years

.EXAMPLE
    .\download-archive-years.ps1 -Years 5
    Downloads data for the last 5 years

.EXAMPLE
    .\download-archive-years.ps1 -StartYear 2020 -EndYear 2023
    Downloads data for seasons 2020-2021, 2021-2022, 2022-2023, 2023-2024

.EXAMPLE
    .\download-archive-years.ps1 -SeasonIds "2022-2023,2023-2024"
    Downloads data for specific season IDs

.EXAMPLE
    .\download-archive-years.ps1 -ExportOnly
    Only exports existing data without downloading
#>

param(
    [int]$Years = 3,
    [int]$StartYear = 0,
    [int]$EndYear = 0,
    [string]$SeasonIds = "",
    [switch]$ExportOnly,
    [switch]$SkipDownload,
    [switch]$KeepData
)

$ROOT = $PSScriptRoot
$PARENT_ROOT = Split-Path -Path $ROOT -Parent
$DATA_ROOT = "$PARENT_ROOT/data"
$CONFIG_FILE = "$ROOT/config.json"
$BACKUP_CONFIG_FILE = "$ROOT/config.json.backup"
$ARCHIVES_DIR = "$PARENT_ROOT/archives"
$DOWNLOAD_SCRIPT = "$ROOT/download-controller.ps1"
$EXPORT_SCRIPT = "$PARENT_ROOT/scripts/export_data.py"

# Color output functions
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""
}

function Get-SeasonIdsToProcess {
    <#
    .SYNOPSIS
        Determine which season IDs to process based on parameters
    #>
    
    $seasonList = @()
    
    # If specific season IDs provided, use those
    if ($SeasonIds) {
        $seasonList = $SeasonIds -split ','
        Write-Info "Using specified season IDs: $($seasonList -join ', ')"
        return $seasonList
    }
    
    # If year range specified, generate season IDs
    if ($StartYear -gt 0 -and $EndYear -gt 0) {
        if ($EndYear -lt $StartYear) {
            Write-Error-Custom "End year must be greater than or equal to start year"
            exit 1
        }
        
        for ($year = $StartYear; $year -le $EndYear; $year++) {
            $nextYear = $year + 1
            $seasonList += "$year-$nextYear"
        }
        
        Write-Info "Generated season IDs from $StartYear to $EndYear : $($seasonList -join ', ')"
        return $seasonList
    }
    
    # Default: generate last N years
    $currentYear = (Get-Date).Year
    $currentMonth = (Get-Date).Month
    
    # If we're in the first half of the year, consider we're still in previous season
    if ($currentMonth -lt 7) {
        $currentYear--
    }
    
    for ($i = 0; $i -lt $Years; $i++) {
        $year = $currentYear - $i
        $nextYear = $year + 1
        $seasonList += "$year-$nextYear"
    }
    
    Write-Info "Generated last $Years season IDs: $($seasonList -join ', ')"
    return $seasonList
}

function Backup-Config {
    <#
    .SYNOPSIS
        Backup the current config.json file
    #>
    
    if (Test-Path $CONFIG_FILE) {
        Copy-Item $CONFIG_FILE $BACKUP_CONFIG_FILE -Force
        Write-Success "Configuration backed up to $BACKUP_CONFIG_FILE"
        return $true
    } else {
        Write-Error-Custom "Config file not found: $CONFIG_FILE"
        return $false
    }
}

function Restore-Config {
    <#
    .SYNOPSIS
        Restore the backed up config.json file
    #>
    
    if (Test-Path $BACKUP_CONFIG_FILE) {
        Copy-Item $BACKUP_CONFIG_FILE $CONFIG_FILE -Force
        Write-Success "Configuration restored from backup"
        Remove-Item $BACKUP_CONFIG_FILE -Force
        return $true
    } else {
        Write-Warning-Custom "No backup config file found"
        return $false
    }
}

function Update-ConfigForSeason {
    <#
    .SYNOPSIS
        Update config.json with the specified season ID
    #>
    param(
        [string]$SeasonId
    )
    
    try {
        $config = Get-Content $CONFIG_FILE | ConvertFrom-Json
        $config.seasonId = $SeasonId
        
        # Also update event name if it exists
        if ($config.eventName) {
            $config.eventName = "FLBB Basketball Season $SeasonId"
        }
        
        $config | ConvertTo-Json -Depth 10 | Set-Content $CONFIG_FILE -Encoding UTF8
        Write-Success "Updated config.json with season ID: $SeasonId"
        return $true
    } catch {
        Write-Error-Custom "Failed to update config.json: $_"
        return $false
    }
}

function Invoke-DownloadForSeason {
    <#
    .SYNOPSIS
        Run the download script for the current season
    #>
    param(
        [string]$SeasonId
    )
    
    Write-Header "Downloading data for season $SeasonId"
    
    if (-not (Test-Path $DOWNLOAD_SCRIPT)) {
        Write-Error-Custom "Download script not found: $DOWNLOAD_SCRIPT"
        return $false
    }
    
    try {
        # Run the download controller script
        & $DOWNLOAD_SCRIPT
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Download completed for season $SeasonId"
            return $true
        } else {
            Write-Warning-Custom "Download script exited with code $LASTEXITCODE for season $SeasonId"
            return $true  # Continue even if there are warnings
        }
    } catch {
        Write-Error-Custom "Error running download script: $_"
        return $false
    }
}

function Invoke-ExportForSeason {
    <#
    .SYNOPSIS
        Export data to archive for the current season
    #>
    param(
        [string]$SeasonId
    )
    
    Write-Header "Exporting data for season $SeasonId"
    
    # Create archives directory if it doesn't exist
    if (-not (Test-Path $ARCHIVES_DIR)) {
        New-Item -ItemType Directory -Path $ARCHIVES_DIR | Out-Null
        Write-Info "Created archives directory: $ARCHIVES_DIR"
    }
    
    # Generate archive filename
    $timestamp = Get-Date -Format "yyyyMMddHHmmss"
    $archiveFilename = "raw-data-$SeasonId-$timestamp.zip"
    $archivePath = "$ARCHIVES_DIR/$archiveFilename"
    
    try {
        # Check if Python is available
        $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCmd) {
            $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
        }
        
        if (-not $pythonCmd) {
            Write-Warning-Custom "Python not found. Attempting PowerShell export..."
            return Invoke-PowerShellExport -SeasonId $SeasonId -ArchivePath $archivePath
        }
        
        # Run Python export script
        $pythonExe = $pythonCmd.Source
        Write-Info "Using Python: $pythonExe"
        Write-Info "Export script: $EXPORT_SCRIPT"
        
        if (Test-Path $EXPORT_SCRIPT) {
            & $pythonExe $EXPORT_SCRIPT --output $archivePath --include-raw
            
            if ($LASTEXITCODE -eq 0 -and (Test-Path $archivePath)) {
                $archiveSize = (Get-Item $archivePath).Length / 1MB
                Write-Success "Archive created: $archivePath ($([math]::Round($archiveSize, 2)) MB)"
                return $archivePath
            } else {
                Write-Warning-Custom "Python export failed. Attempting PowerShell export..."
                return Invoke-PowerShellExport -SeasonId $SeasonId -ArchivePath $archivePath
            }
        } else {
            Write-Warning-Custom "Export script not found: $EXPORT_SCRIPT"
            return Invoke-PowerShellExport -SeasonId $SeasonId -ArchivePath $archivePath
        }
    } catch {
        Write-Error-Custom "Error during export: $_"
        Write-Info "Attempting PowerShell fallback export..."
        return Invoke-PowerShellExport -SeasonId $SeasonId -ArchivePath $archivePath
    }
}

function Invoke-PowerShellExport {
    <#
    .SYNOPSIS
        Fallback export using PowerShell Compress-Archive
    #>
    param(
        [string]$SeasonId,
        [string]$ArchivePath
    )
    
    Write-Info "Creating archive using PowerShell..."
    
    try {
        # Remove existing archive if present
        if (Test-Path $ArchivePath) {
            Remove-Item $ArchivePath -Force
        }
        
        # Collect files to archive
        $filesToArchive = @()
        
        # Add essential data files
        $essentialFiles = @(
            "$DATA_ROOT/full-game-stats.csv",
            "$DATA_ROOT/gamesDB.json",
            "$DATA_ROOT/gameScheduleDB.json",
            "$DATA_ROOT/players-database.csv"
        )
        
        foreach ($file in $essentialFiles) {
            if (Test-Path $file) {
                $filesToArchive += $file
            }
        }
        
        # Add raw data directories
        $rawDirs = @(
            "$DATA_ROOT/game-schedule-raw",
            "$DATA_ROOT/full-game-stats-raw",
            "$DATA_ROOT/full-game-stats-output"
        )
        
        foreach ($dir in $rawDirs) {
            if (Test-Path $dir) {
                $filesToArchive += $dir
            }
        }
        
        if ($filesToArchive.Count -eq 0) {
            Write-Error-Custom "No files found to archive"
            return $null
        }
        
        # Create the archive
        Compress-Archive -Path $filesToArchive -DestinationPath $ArchivePath -CompressionLevel Optimal
        
        if (Test-Path $ArchivePath) {
            $archiveSize = (Get-Item $ArchivePath).Length / 1MB
            Write-Success "Archive created: $ArchivePath ($([math]::Round($archiveSize, 2)) MB)"
            return $ArchivePath
        } else {
            Write-Error-Custom "Failed to create archive"
            return $null
        }
    } catch {
        Write-Error-Custom "PowerShell export failed: $_"
        return $null
    }
}

function Move-DataToSeasonDirectory {
    <#
    .SYNOPSIS
        Move downloaded data to season-specific directory
    #>
    param(
        [string]$SeasonId
    )
    
    if ($KeepData) {
        Write-Info "Keeping data in main data directory (--KeepData flag set)"
        return $true
    }
    
    $seasonDataDir = "$PARENT_ROOT/season-data/$SeasonId"
    
    try {
        # Create season directory if it doesn't exist
        if (-not (Test-Path $seasonDataDir)) {
            New-Item -ItemType Directory -Path $seasonDataDir -Force | Out-Null
        }
        
        # Move data files to season directory
        $itemsToMove = @(
            "$DATA_ROOT/full-game-stats.csv",
            "$DATA_ROOT/gamesDB.json",
            "$DATA_ROOT/gameScheduleDB.json",
            "$DATA_ROOT/players-database.csv",
            "$DATA_ROOT/game-schedule-raw",
            "$DATA_ROOT/full-game-stats-raw",
            "$DATA_ROOT/full-game-stats-output"
        )
        
        foreach ($item in $itemsToMove) {
            if (Test-Path $item) {
                $itemName = Split-Path $item -Leaf
                $destination = "$seasonDataDir/$itemName"
                
                # Remove destination if it exists
                if (Test-Path $destination) {
                    Remove-Item $destination -Recurse -Force
                }
                
                Move-Item $item $destination -Force
                Write-Info "Moved $itemName to $seasonDataDir"
            }
        }
        
        Write-Success "Data moved to season directory: $seasonDataDir"
        return $true
    } catch {
        Write-Warning-Custom "Error moving data to season directory: $_"
        return $false
    }
}

function Show-Summary {
    <#
    .SYNOPSIS
        Display summary of the operation
    #>
    param(
        [array]$Results
    )
    
    Write-Header "Summary"
    
    $totalSeasons = $Results.Count
    $successfulDownloads = ($Results | Where-Object { $_.DownloadSuccess }).Count
    $successfulExports = ($Results | Where-Object { $_.ExportSuccess }).Count
    
    Write-Host "Total seasons processed: $totalSeasons"
    Write-Host "Successful downloads: $successfulDownloads"
    Write-Host "Successful exports: $successfulExports"
    Write-Host ""
    
    Write-Host "Details:" -ForegroundColor Cyan
    foreach ($result in $Results) {
        $status = if ($result.ExportSuccess) { "✓" } else { "✗" }
        $archiveInfo = if ($result.ArchivePath) { " → $($result.ArchivePath)" } else { "" }
        Write-Host "  $status Season $($result.SeasonId)$archiveInfo"
    }
    
    Write-Host ""
    Write-Host "Archives location: $ARCHIVES_DIR" -ForegroundColor Cyan
    
    if ($KeepData) {
        Write-Host "Data location: $DATA_ROOT (kept in main directory)" -ForegroundColor Cyan
    } else {
        Write-Host "Season data location: $PARENT_ROOT/season-data/" -ForegroundColor Cyan
    }
}

# ============================================================================
# Main Execution
# ============================================================================

Write-Header "FLBB Archive Data Download and Export Tool"

Write-Host "Parameters:"
Write-Host "  Years: $Years"
Write-Host "  StartYear: $StartYear"
Write-Host "  EndYear: $EndYear"
Write-Host "  SeasonIds: $SeasonIds"
Write-Host "  ExportOnly: $ExportOnly"
Write-Host "  SkipDownload: $SkipDownload"
Write-Host "  KeepData: $KeepData"
Write-Host ""

# Get list of seasons to process
$seasonsToProcess = Get-SeasonIdsToProcess

if ($seasonsToProcess.Count -eq 0) {
    Write-Error-Custom "No seasons to process"
    exit 1
}

Write-Host ""
Write-Host "Will process $($seasonsToProcess.Count) season(s):" -ForegroundColor Green
foreach ($season in $seasonsToProcess) {
    Write-Host "  - $season"
}
Write-Host ""

# Confirm with user
if (-not $ExportOnly) {
    $confirmation = Read-Host "Continue? (yes/no)"
    if ($confirmation -notmatch '^(yes|y)$') {
        Write-Info "Operation cancelled by user"
        exit 0
    }
}

# Backup current configuration
if (-not (Backup-Config)) {
    Write-Error-Custom "Failed to backup configuration. Aborting."
    exit 1
}

# Process each season
$results = @()

try {
    foreach ($seasonId in $seasonsToProcess) {
        $result = @{
            SeasonId = $seasonId
            DownloadSuccess = $false
            ExportSuccess = $false
            ArchivePath = $null
        }
        
        Write-Header "Processing Season: $seasonId"
        
        # Update configuration
        if (-not (Update-ConfigForSeason -SeasonId $seasonId)) {
            Write-Error-Custom "Failed to update configuration for $seasonId. Skipping..."
            $results += $result
            continue
        }
        
        # Download data (unless skipped or export-only mode)
        if (-not $ExportOnly -and -not $SkipDownload) {
            $downloadSuccess = Invoke-DownloadForSeason -SeasonId $seasonId
            $result.DownloadSuccess = $downloadSuccess
            
            if (-not $downloadSuccess) {
                Write-Warning-Custom "Download failed for $seasonId. Continuing with export if data exists..."
            }
        } else {
            Write-Info "Skipping download for season $seasonId"
            $result.DownloadSuccess = $true
        }
        
        # Export data
        $archivePath = Invoke-ExportForSeason -SeasonId $seasonId
        
        if ($archivePath) {
            $result.ExportSuccess = $true
            $result.ArchivePath = $archivePath
        }
        
        # Move data to season directory (unless keeping in main directory)
        if ($result.ExportSuccess) {
            Move-DataToSeasonDirectory -SeasonId $seasonId
        }
        
        $results += $result
        
        Write-Host ""
    }
} finally {
    # Always restore configuration
    Write-Header "Cleanup"
    Restore-Config
}

# Show summary
Show-Summary -Results $results

# Determine exit code
$hasFailures = $results | Where-Object { -not $_.ExportSuccess }
if ($hasFailures) {
    Write-Warning-Custom "Some seasons failed to process"
    exit 1
} else {
    Write-Success "All seasons processed successfully!"
    exit 0
}
