# MongoDB Helper Module for PowerShell
#
# This module provides functions to interact with MongoDB for game data storage
# and deduplication. It uses the Python bridge script to communicate with MongoDB.
#
# Features:
# - Check if a game exists with status 'finished' before processing
# - Insert/update game documents after parsing
# - Query games by various criteria
# - Support for deduplication based on game_id and status
#
# Configuration:
# Set environment variables or use parameters:
# - MONGODB_ENABLED: Enable MongoDB operations (true/false)
# - MONGODB_URI: Connection string (default: mongodb://localhost:27017/)
# - MONGODB_DATABASE: Database name (default: flbb-statistics)

$MONGODB_BRIDGE_SCRIPT = "$PSScriptRoot/mongodb_powershell_bridge.py"

# Get MongoDB configuration from environment or use defaults
function Get-MongoDBConfig {
    $config = @{
        Enabled = $env:MONGODB_ENABLED -eq "true"
        Uri = if ($env:MONGODB_URI) { $env:MONGODB_URI } else { "mongodb://localhost:27017/" }
        Database = if ($env:MONGODB_DATABASE) { $env:MONGODB_DATABASE } else { "flbb-statistics" }
        Collection = "games"
    }
    return $config
}

# Test if MongoDB is enabled and available
function Test-MongoDBEnabled {
    [CmdletBinding()]
    param()
    
    $config = Get-MongoDBConfig
    
    if (-not $config.Enabled) {
        Write-Debug "MongoDB is not enabled (set MONGODB_ENABLED=true to enable)"
        return $false
    }
    
    # Check if Python is available
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "MongoDB enabled but Python is not available"
            return $false
        }
    }
    catch {
        Write-Warning "MongoDB enabled but Python is not available"
        return $false
    }
    
    # Check if bridge script exists
    if (-not (Test-Path $MONGODB_BRIDGE_SCRIPT)) {
        Write-Warning "MongoDB bridge script not found: $MONGODB_BRIDGE_SCRIPT"
        return $false
    }
    
    return $true
}

# Test MongoDB connection
function Test-MongoDBConnection {
    [CmdletBinding()]
    param(
        [string]$Uri,
        [string]$Database,
        [string]$Collection = "games"
    )
    
    if (-not (Test-MongoDBEnabled)) {
        return $false
    }
    
    $config = Get-MongoDBConfig
    if (-not $Uri) { $Uri = $config.Uri }
    if (-not $Database) { $Database = $config.Database }
    
    try {
        $result = python $MONGODB_BRIDGE_SCRIPT test-connection --uri $Uri --database $Database --collection $Collection 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ MongoDB connection successful" -ForegroundColor Green
            $result | ForEach-Object { Write-Host $_ }
            return $true
        }
        else {
            Write-Warning "MongoDB connection failed"
            $result | ForEach-Object { Write-Warning $_ }
            return $false
        }
    }
    catch {
        Write-Warning "Error testing MongoDB connection: $($_.Exception.Message)"
        return $false
    }
}

# Check if a game exists in MongoDB with a specific status
function Test-GameInMongoDB {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$GameId,
        
        [string]$Status = "finished",
        
        [string]$Uri,
        [string]$Database,
        [string]$Collection = "games"
    )
    
    if (-not (Test-MongoDBEnabled)) {
        Write-Debug "MongoDB not enabled, skipping game check for $GameId"
        return $false
    }
    
    $config = Get-MongoDBConfig
    if (-not $Uri) { $Uri = $config.Uri }
    if (-not $Database) { $Database = $config.Database }
    
    try {
        $arguments = @(
            $MONGODB_BRIDGE_SCRIPT,
            "check-game",
            "--game-id", $GameId,
            "--uri", $Uri,
            "--database", $Database,
            "--collection", $Collection
        )
        
        if ($Status) {
            $arguments += "--status", $Status
        }
        
        $output = python @arguments 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Debug "Game $GameId exists in MongoDB with status '$Status'"
            return $true
        }
        elseif ($LASTEXITCODE -eq 1) {
            Write-Debug "Game $GameId does not exist or has different status"
            return $false
        }
        else {
            Write-Warning "Error checking game in MongoDB: $output"
            return $false
        }
    }
    catch {
        Write-Warning "Error checking game in MongoDB: $($_.Exception.Message)"
        return $false
    }
}

# Insert or update a game in MongoDB
function Set-GameInMongoDB {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$GameId,
        
        [Parameter(Mandatory=$true)]
        [string]$JsonFilePath,
        
        [string]$Status = "finished",
        
        [bool]$CsvGenerated = $false,
        
        [string]$Uri,
        [string]$Database,
        [string]$Collection = "games"
    )
    
    if (-not (Test-MongoDBEnabled)) {
        Write-Debug "MongoDB not enabled, skipping game storage for $GameId"
        return $false
    }
    
    # Verify JSON file exists
    if (-not (Test-Path $JsonFilePath)) {
        Write-Warning "JSON file not found: $JsonFilePath"
        return $false
    }
    
    $config = Get-MongoDBConfig
    if (-not $Uri) { $Uri = $config.Uri }
    if (-not $Database) { $Database = $config.Database }
    
    try {
        $arguments = @(
            $MONGODB_BRIDGE_SCRIPT,
            "upsert-game",
            "--game-id", $GameId,
            "--json-file", $JsonFilePath,
            "--status", $Status,
            "--uri", $Uri,
            "--database", $Database,
            "--collection", $Collection
        )
        
        if ($CsvGenerated) {
            $arguments += "--csv-generated", "true"
        }
        else {
            $arguments += "--csv-generated", "false"
        }
        
        $output = python @arguments 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Game $GameId stored in MongoDB" -ForegroundColor Green
            return $true
        }
        else {
            Write-Warning "Failed to store game $GameId in MongoDB"
            $output | ForEach-Object { Write-Warning $_ }
            return $false
        }
    }
    catch {
        Write-Warning "Error storing game in MongoDB: $($_.Exception.Message)"
        return $false
    }
}

# Query games from MongoDB
function Get-GamesFromMongoDB {
    [CmdletBinding()]
    param(
        [string]$Status,
        [string]$Division,
        [string]$Season,
        [string]$Uri,
        [string]$Database,
        [string]$Collection = "games"
    )
    
    if (-not (Test-MongoDBEnabled)) {
        Write-Debug "MongoDB not enabled, cannot query games"
        return @()
    }
    
    $config = Get-MongoDBConfig
    if (-not $Uri) { $Uri = $config.Uri }
    if (-not $Database) { $Database = $config.Database }
    
    try {
        $arguments = @(
            $MONGODB_BRIDGE_SCRIPT,
            "query-games",
            "--uri", $Uri,
            "--database", $Database,
            "--collection", $Collection
        )
        
        if ($Status) { $arguments += "--status", $Status }
        if ($Division) { $arguments += "--division", $Division }
        if ($Season) { $arguments += "--season", $Season }
        
        $output = python @arguments 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            # Parse JSON output
            $games = $output | ConvertFrom-Json
            return $games
        }
        else {
            Write-Warning "Failed to query games from MongoDB"
            $output | ForEach-Object { Write-Warning $_ }
            return @()
        }
    }
    catch {
        Write-Warning "Error querying games from MongoDB: $($_.Exception.Message)"
        return @()
    }
}

# Get count of games in MongoDB
function Get-MongoDBGameCount {
    [CmdletBinding()]
    param(
        [string]$Uri,
        [string]$Database,
        [string]$Collection = "games"
    )
    
    if (-not (Test-MongoDBEnabled)) {
        Write-Debug "MongoDB not enabled, cannot get count"
        return 0
    }
    
    $config = Get-MongoDBConfig
    if (-not $Uri) { $Uri = $config.Uri }
    if (-not $Database) { $Database = $config.Database }
    
    try {
        $output = python $MONGODB_BRIDGE_SCRIPT count-games --uri $Uri --database $Database --collection $Collection 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            # Parse count from output like "COUNT: 123"
            $countLine = $output | Where-Object { $_ -match "^COUNT: (\d+)" }
            if ($countLine -match "COUNT: (\d+)") {
                return [int]$Matches[1]
            }
        }
        
        Write-Warning "Failed to get game count from MongoDB"
        return 0
    }
    catch {
        Write-Warning "Error getting game count from MongoDB: $($_.Exception.Message)"
        return 0
    }
}

# Export functions
Export-ModuleMember -Function @(
    'Get-MongoDBConfig',
    'Test-MongoDBEnabled',
    'Test-MongoDBConnection',
    'Test-GameInMongoDB',
    'Set-GameInMongoDB',
    'Get-GamesFromMongoDB',
    'Get-MongoDBGameCount'
)
