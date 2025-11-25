# MongoDB Integration Example for PowerShell
#
# This script demonstrates how to use the MongoDB integration
# with the FLBB statistics PowerShell scripts.
#
# Usage:
#   .\examples\mongodb_integration_example.ps1

$ROOT = Split-Path -Path $PSScriptRoot -Parent
$SCRIPTS_ROOT = Join-Path -Path $ROOT -ChildPath "scripts"

# Import MongoDB helper
. "$SCRIPTS_ROOT\mongodb_helper.ps1"

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "MongoDB Integration Example" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""

# Example 1: Check if MongoDB is enabled
Write-Host "Example 1: Check MongoDB Status" -ForegroundColor Yellow
Write-Host "-" * 60
if (Test-MongoDBEnabled) {
    Write-Host "✅ MongoDB is enabled and available" -ForegroundColor Green
} else {
    Write-Host "ℹ️  MongoDB is not enabled or not available" -ForegroundColor Gray
    Write-Host "   To enable MongoDB, set environment variable:" -ForegroundColor Gray
    Write-Host "   `$env:MONGODB_ENABLED = 'true'" -ForegroundColor Cyan
}
Write-Host ""

# Example 2: Test MongoDB connection
Write-Host "Example 2: Test MongoDB Connection" -ForegroundColor Yellow
Write-Host "-" * 60
if (Test-MongoDBEnabled) {
    $connected = Test-MongoDBConnection
    if (-not $connected) {
        Write-Host "⚠️  Could not connect to MongoDB" -ForegroundColor Yellow
        Write-Host "   Make sure MongoDB is running and connection string is correct" -ForegroundColor Gray
    }
} else {
    Write-Host "Skipped - MongoDB not enabled" -ForegroundColor Gray
}
Write-Host ""

# Example 3: Check if a specific game exists
Write-Host "Example 3: Check if Game Exists" -ForegroundColor Yellow
Write-Host "-" * 60
if (Test-MongoDBEnabled) {
    $gameId = "12345"
    $exists = Test-GameInMongoDB -GameId $gameId -Status "finished"
    
    if ($exists) {
        Write-Host "✅ Game $gameId exists with status 'finished'" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  Game $gameId does not exist or has different status" -ForegroundColor Gray
    }
} else {
    Write-Host "Skipped - MongoDB not enabled" -ForegroundColor Gray
}
Write-Host ""

# Example 4: Store a game in MongoDB (simulated)
Write-Host "Example 4: Store Game in MongoDB" -ForegroundColor Yellow
Write-Host "-" * 60
if (Test-MongoDBEnabled) {
    # This would normally be a real JSON file path
    $jsonPath = "data/full-game-stats-output/division1-hommes/full-game-stats-12345.json"
    
    if (Test-Path $jsonPath) {
        Write-Host "Storing game in MongoDB..." -ForegroundColor Gray
        $success = Set-GameInMongoDB -GameId "12345" -JsonFilePath $jsonPath -Status "finished" -CsvGenerated $false
        
        if ($success) {
            Write-Host "✅ Game stored successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Failed to store game" -ForegroundColor Yellow
        }
    } else {
        Write-Host "ℹ️  Sample JSON file not found (this is expected in demo)" -ForegroundColor Gray
        Write-Host "   In real usage, this would be the path to your game JSON file" -ForegroundColor Gray
    }
} else {
    Write-Host "Skipped - MongoDB not enabled" -ForegroundColor Gray
}
Write-Host ""

# Example 5: Query games
Write-Host "Example 5: Query Games from MongoDB" -ForegroundColor Yellow
Write-Host "-" * 60
if (Test-MongoDBEnabled) {
    Write-Host "Querying finished games..." -ForegroundColor Gray
    $games = Get-GamesFromMongoDB -Status "finished"
    
    if ($games.Count -gt 0) {
        Write-Host "✅ Found $($games.Count) finished games" -ForegroundColor Green
        Write-Host "   First game ID: $($games[0].GameId)" -ForegroundColor Gray
    } else {
        Write-Host "ℹ️  No finished games found in MongoDB" -ForegroundColor Gray
    }
} else {
    Write-Host "Skipped - MongoDB not enabled" -ForegroundColor Gray
}
Write-Host ""

# Example 6: Get game count
Write-Host "Example 6: Get Total Game Count" -ForegroundColor Yellow
Write-Host "-" * 60
if (Test-MongoDBEnabled) {
    $count = Get-MongoDBGameCount
    Write-Host "📊 Total games in MongoDB: $count" -ForegroundColor Cyan
} else {
    Write-Host "Skipped - MongoDB not enabled" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""
Write-Host "To enable MongoDB integration:" -ForegroundColor Yellow
Write-Host "1. Install MongoDB locally or use MongoDB Atlas" -ForegroundColor White
Write-Host "2. Install pymongo: pip install pymongo" -ForegroundColor White
Write-Host "3. Set environment variables:" -ForegroundColor White
Write-Host "   `$env:MONGODB_ENABLED = 'true'" -ForegroundColor Cyan
Write-Host "   `$env:MONGODB_URI = 'mongodb://localhost:27017/'" -ForegroundColor Cyan
Write-Host "   `$env:MONGODB_DATABASE = 'flbb-statistics'" -ForegroundColor Cyan
Write-Host ""
Write-Host "For more information, see:" -ForegroundColor Yellow
Write-Host "- MONGODB_SETUP.md - Complete setup guide" -ForegroundColor White
Write-Host "- docs/MONGODB_INTEGRATION.md - Integration documentation" -ForegroundColor White
Write-Host ""
