# Cache Helper for FLBB Statistics
# This script provides functions to work with the cache manager for raw HTML and JSON files

$SCRIPT_ROOT = $PSScriptRoot
$PARENT_ROOT = Split-Path -Path $SCRIPT_ROOT -Parent
$DATA_ROOT = Join-Path -Path $PARENT_ROOT -ChildPath "data"

function Invoke-DownloadCache {
    <#
    .SYNOPSIS
    Download cache from Google Drive
    
    .DESCRIPTION
    Downloads the cached raw HTML and JSON files from Google Drive to avoid re-downloading
    finished games from the FLBB website.
    
    .PARAMETER FileId
    Optional Google Drive file ID. If not provided, will use the latest cache file.
    #>
    param(
        [string]$FileId
    )
    
    Write-Host "Downloading cache from Google Drive..." -ForegroundColor Cyan
    
    $pythonArgs = @(
        "$PARENT_ROOT/src/cache_manager.py",
        "download",
        "--data-root", $DATA_ROOT,
        "--scripts-root", $SCRIPT_ROOT
    )
    
    if ($FileId) {
        $pythonArgs += "--file-id"
        $pythonArgs += $FileId
    }
    
    try {
        $result = & python3 $pythonArgs 2>&1
        $exitCode = $LASTEXITCODE
        
        Write-Host $result
        
        if ($exitCode -eq 0) {
            Write-Host "✓ Cache download completed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Warning "Cache download failed or no cache available"
            return $false
        }
    }
    catch {
        Write-Warning "Error downloading cache: $_"
        return $false
    }
}

function Invoke-UploadCache {
    <#
    .SYNOPSIS
    Upload cache to Google Drive
    
    .DESCRIPTION
    Creates and uploads a cache archive of raw HTML and JSON files for finished games
    to Google Drive.
    #>
    
    Write-Host "Uploading cache to Google Drive..." -ForegroundColor Cyan
    
    $pythonArgs = @(
        "$PARENT_ROOT/src/cache_manager.py",
        "upload",
        "--data-root", $DATA_ROOT,
        "--scripts-root", $SCRIPT_ROOT
    )
    
    try {
        $result = & python3 $pythonArgs 2>&1
        $exitCode = $LASTEXITCODE
        
        Write-Host $result
        
        if ($exitCode -eq 0) {
            Write-Host "✓ Cache upload completed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Warning "Cache upload failed"
            return $false
        }
    }
    catch {
        Write-Warning "Error uploading cache: $_"
        return $false
    }
}

function Get-CachedGameIds {
    <#
    .SYNOPSIS
    Get list of cached game IDs
    
    .DESCRIPTION
    Returns a list of game IDs that are currently cached locally.
    
    .OUTPUTS
    Array of game ID strings
    #>
    
    $cachedIds = @()
    $rawDirectory = Join-Path -Path $DATA_ROOT -ChildPath "full-game-stats-raw"
    
    if (Test-Path $rawDirectory) {
        Get-ChildItem -Path $rawDirectory -Directory | ForEach-Object {
            $divisionDir = $_.FullName
            Get-ChildItem -Path $divisionDir -Filter "full-game-stats-*.html" | ForEach-Object {
                # Extract game ID from filename: full-game-stats-{ID}.html
                $filename = $_.BaseName
                $gameId = $filename -replace "^full-game-stats-", ""
                $cachedIds += $gameId
            }
        }
    }
    
    return $cachedIds
}

function Test-GameIsCached {
    <#
    .SYNOPSIS
    Check if a specific game is cached
    
    .DESCRIPTION
    Checks if the raw HTML file for a specific game exists in the cache.
    
    .PARAMETER GameId
    The game ID to check
    
    .PARAMETER DivisionName
    The division name for the game
    
    .OUTPUTS
    Boolean indicating if the game is cached
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$GameId,
        
        [Parameter(Mandatory=$true)]
        [string]$DivisionName
    )
    
    $rawDirectory = Join-Path -Path $DATA_ROOT -ChildPath "full-game-stats-raw"
    $divisionPath = Join-Path -Path $rawDirectory -ChildPath $DivisionName
    $htmlFilePath = Join-Path -Path $divisionPath -ChildPath "full-game-stats-$GameId.html"
    
    return Test-Path $htmlFilePath
}

function Show-CacheStatus {
    <#
    .SYNOPSIS
    Display cache status information
    
    .DESCRIPTION
    Shows information about finished games and their cache status.
    #>
    
    Write-Host "`nCache Status:" -ForegroundColor Cyan
    
    $pythonArgs = @(
        "$PARENT_ROOT/src/cache_manager.py",
        "list-finished",
        "--data-root", $DATA_ROOT,
        "--scripts-root", $SCRIPT_ROOT
    )
    
    try {
        $result = & python3 $pythonArgs 2>&1
        Write-Host $result
    }
    catch {
        Write-Warning "Error getting cache status: $_"
    }
}

# Export functions for use in other scripts
Export-ModuleMember -Function @(
    'Invoke-DownloadCache',
    'Invoke-UploadCache',
    'Get-CachedGameIds',
    'Test-GameIsCached',
    'Show-CacheStatus'
)
