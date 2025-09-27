$ROOT = $PSScriptRoot

Add-Type -Path "$ROOT\Net40\HtmlAgilityPack.dll"

# Load configuration from config.json
$CONFIG_FILEPATH = "$ROOT/config.json"
if (Test-Path $CONFIG_FILEPATH) {
    Write-Host "Loading configuration from config.json"
    $configData = Get-Content -Path $CONFIG_FILEPATH | ConvertFrom-Json
} else {
    Write-Warning "config.json not found, using default configuration"
    $configData = $null
}

# Set variables from config or defaults
if ($configData) {
    $PLAYER_MAP_FILEPATH = "$ROOT/$($configData.files.playerMap)"
    $EVENT_ACTION_PATTERNS_FILEPATH = "$ROOT/$($configData.files.eventActionPatterns)"
    $GAMES_DB_FILEPATH = "$ROOT/$($configData.files.gamesDb)"
    $GAME_SCHEDULE_DB_FILEPATH = "$ROOT/$($configData.files.gameScheduleDb)"
    $GAME_SCHEDULE_RAW_DIRECTORY = "$ROOT/$($configData.directories.gameScheduleRaw)"
    $FULL_GAME_STATS_RAW_DIRECTORY = "$ROOT/$($configData.directories.fullGameStatsRaw)"
    $NUMBER_OF_PARALLEL_DOWNLOADS = $configData.processing.parallelDownloads
    $SEASON_ID = $configData.seasonId
    $FLBB_ALL_COMPTETION_URL = $configData.dataSource.allCompetitionsUrl
    $DIVISIONS_INCLUDED = $configData.processing.divisionsIncluded
} else {
    # Default values if config is not available
    $PLAYER_MAP_FILEPATH = "$ROOT/player-map.json"
    $EVENT_ACTION_PATTERNS_FILEPATH = "$ROOT/event-action-patterns.json"
    $GAMES_DB_FILEPATH = "$ROOT/gamesDB.json"
    $GAME_SCHEDULE_DB_FILEPATH = "$ROOT/gameScheduleDB.json"
    $GAME_SCHEDULE_RAW_DIRECTORY = "$ROOT/game-schedule-raw"
    $FULL_GAME_STATS_RAW_DIRECTORY = "$ROOT/full-game-stats-raw"
    $NUMBER_OF_PARALLEL_DOWNLOADS = 10
    $SEASON_ID = "2024-2025"
    $FLBB_ALL_COMPTETION_URL = "https://www.luxembourg.basketball/c/categorie/all"
    $DIVISIONS_INCLUDED = @("division 1 hommes", "division 2 hommes", "division 3 hommes", "division 4 hommes")
}

$PATTERN_SCHEDULE_URL = "https://www.luxembourg.basketball/c/calendrier-resultat/(\d+)/(.+)"
$PATTERN_GAME_URL = "https://www.luxembourg.basketball/match/(\d+)/(\d{4}-\d{2}-\d{2})/(.+)/(.+)"

$GAME_STATUS_FINISHED = "Finished"
$GAME_STATUS_NOT_STARTED = "NotStarted"
$GAME_STATUS_IN_PROGRESS = "InProgress"

$CATEGORIES_EXCLUDED = @("U12 Garcons", "U12 Filles")
$DIVISIONS_EXCLUDED = @()

function Get-AppConfig() {
    $appConfig = @{
        "PlayerMap"                  = Get-Content -Path $PLAYER_MAP_FILEPATH | ConvertFrom-Json
        "EventActionPatterns"        = Get-Content -Path $EVENT_ACTION_PATTERNS_FILEPATH | ConvertFrom-Json
        "GameScheduleRawDirectory"   = $GAME_SCHEDULE_RAW_DIRECTORY
        "FullGameStatsRawDirectory"  = $FULL_GAME_STATS_RAW_DIRECTORY
        "NumberOfParallelDownloads"  = $NUMBER_OF_PARALLEL_DOWNLOADS
        "SeasonId"                   = $SEASON_ID
        "GamesDbFilepath"            = $GAMES_DB_FILEPATH
        "GameScheduleDbFilepath"     = $GAME_SCHEDULE_DB_FILEPATH
        "FlbbAllCompetitionUrl"      = $FLBB_ALL_COMPTETION_URL
        "ForceDownloadGameSchedule"  = if ($configData) { $configData.processing.forceDownloadGameSchedule } else { $true }
        "ForceDownloadFullGameStats" = if ($configData) { $configData.processing.forceDownloadFullGameStats } else { $true }
        "DivisionsIncluded"          = $DIVISIONS_INCLUDED
        "ConfigData"                 = $configData
    }
    return $appConfig
}

function Get-HtmlContent($url) {
    # Define the URL

    # Use Invoke-WebRequest to get the HTML content
    $response = Invoke-WebRequest -Uri $url

    # Check if the request was successful (status code 200)
    if ($response.StatusCode -eq 200) {
        # Display the HTML content
        $htmlContent = $response.Content
        return $htmlContent
    }
    else {
        Write-Error "Failed to retrieve HTML content. Status code: $($response.StatusCode)"
    }
}

$downloadRawHtml = {
    param($url, $filepath)
    # Define the URL
    # Use Invoke-WebRequest to get the HTML content
    $response = Invoke-WebRequest -Uri $url

    # Check if the request was successful (status code 200)
    if ($response.StatusCode -eq 200) {
        # Display the HTML content
        $htmlContent = $response.Content
        Set-Content -Path $filepath -Value $htmlContent
        Write-Host "File from $url saved to $filepath"
    }
    else {
        Write-Error "Failed to retrieve HTML content. Status code: $($response.StatusCode)"
    }
}
function Get-GameSchedules($appConfig) {
    if (-not (Test-Path $appConfig.GameScheduleDbFilepath) -or $appConfig.ForceDownloadGameSchedule) {
        $localAllCompetitionFilepath = "$GAME_SCHEDULE_RAW_DIRECTORY/all.html"
        if (-not(Test-Path $GAME_SCHEDULE_RAW_DIRECTORY)) {
            New-Item -ItemType Directory -Path $GAME_SCHEDULE_RAW_DIRECTORY
        }
        if (-not (Test-Path $localAllCompetitionFilepath)) {
            Write-Host "Downloading list of categories from $($appConfig.FlbbAllCompetitionUrl)"
            $htmlContent = Get-HtmlContent $appConfig.FlbbAllCompetitionUrl
            $htmlContent | Out-File -FilePath $localAllCompetitionFilepath
            Write-Host "List of categories saved to $localAllCompetitionFilepath"
        }

        $htmlDoc = New-Object HtmlAgilityPack.HtmlDocument
        $htmlDoc.Load($localAllCompetitionFilepath)
        $categoryUrlNodes = $htmlDoc.DocumentNode.SelectNodes(".//div[@id='wrapper']//a")

        $gameSchedules = @()

        $categoryUrlNodes | ForEach-Object {
            $categoryUrl = $_.GetAttributeValue('href', '')
            $categoryNameRaw = $categoryUrl.Split("/")[-1]
            $categoryName = $categoryNameRaw -replace ("-", " ")
            $categoryName = (Get-Culture).TextInfo.ToTitleCase($categoryName)

            $gameSchedule = @{
                "SeasonId"          = $appConfig.SeasonId
                "CategoryUrl"       = $categoryUrl
                "ExcludedFromStats" = if ($categoryNameRaw -in $CATEGORIES_EXCLUDED) { $true } else { $false }
                "CategoryName"      = $categoryName
                "CategoryNameRaw"   = $categoryNameRaw
            }
        
            # add if statement to exclude categories
            Write-Host "Category found: name=$($gameSchedule.CategoryName), url=$($gameSchedule.CategoryUrl)"
            if ($appConfig.DivisionsIncluded -contains $gameSchedule.CategoryName) {
                $gameSchedules += $gameSchedule
            }
            else {
                Write-Host "Category excluded: name=$($gameSchedule.CategoryName), url=$($gameSchedule.CategoryUrl)"
            }
        }
        $gameSchedules | ConvertTo-Json -Depth 10 | Out-File -FilePath $appConfig.GameScheduleDbFilepath -Encoding UTF8
    }
    else {
        $gameSchedules = Get-Content -Path $appConfig.GameScheduleDbFilepath -Raw | ConvertFrom-Json
    }
    Write-Host "Found $($gameSchedules.Count) categories"
    return $gameSchedules
}
function Get-FilepathBy( $appConfig, $url) {
    if ($url -match $PATTERN_SCHEDULE_URL) {
        $categoryName = $Matches[2]
        $filepath = "$($appConfig.GameScheduleRawDirectory)/$categoryName.html"
        return $filepath
    }
    if ($url -match $PATTERN_GAME_URL) {
        $matchNumber = $Matches[1]
        $divisionName = $Matches[4]
        $filepath = "$($appConfig.FullGameStatsRawDirectory)/$divisionName/full-game-stats-$matchNumber.html"
        return $filepath
    }
}
function ChunkBy($items, [int]$size) {
    $list = new-object System.Collections.ArrayList
    $tmpList = new-object System.Collections.ArrayList
    foreach ($item in $items) {
        $tmpList.Add($item) | out-null
        if ($tmpList.Count -ge $size) {
            $list.Add($tmpList.ToArray()) | out-null
            $tmpList.Clear()
        }
    }
    if ($tmpList.Count -gt 0) {
        $list.Add($tmpList.ToArray()) | out-null
    }
    return $list.ToArray()
}

function Invoke-MultipleDownloadRawHtml($appConfig, $urls, $forceToDownload = $false) {
    $chunks = ChunkBy -items $urls -size $appConfig.NumberOfParallelDownloads
    $downloads = 0
    foreach ($chunk in $chunks) {
        foreach ($url in $chunk) {
            $filepath = Get-FilepathBy -appConfig $appConfig -url $url
            if (-not (Test-Path $filepath) -or $forceToDownload) {
                Write-Debug "Downloading $url"
                $divisionName = $url.Split("/")[-1]
                $fullGameStatsRawDivisionDirectory = "$($appConfig.FullGameStatsRawDirectory)/$divisionName"
                if (-not (Test-Path $fullGameStatsRawDivisionDirectory)) {
                    New-Item -ItemType Directory -Path $fullGameStatsRawDivisionDirectory
                }
                Start-Job -ScriptBlock $downloadRawHtml -ArgumentList $url, $filepath
            }
        }
        while (Get-Job -State "Running") {
            Start-Sleep 1
        }
        # Get-Job | Receive-Job
        Get-Job | Remove-Job
        $downloads += $chunk.Count
        Write-Host "Downloaded $([System.Math]::Round($downloads/$urls.Count *100,0))% ($downloads out of $($urls.Count))"
    }
}
function Get-GamesInDivision($appConfig, $gameSchedule) {
    Write-Host "Requested url: $($gameSchedule.CategoryUrl)"
    # $divisionNameExtracted = $gameSchedule.DivisionUrl.Split("/")[-1]
    # $divisionName = $divisionNameExtracted -replace ("-", " ")
    # $divisionName = (Get-Culture).TextInfo.ToTitleCase($divisionName)
    if (-not (Test-Path "$($appConfig.GameScheduleRawDirectory)")) {
        New-Item -ItemType Directory -Path "$($appConfig.GameScheduleRawDirectory)"
    }
    $localGameScheduleFilepath = "$($appConfig.GameScheduleRawDirectory)/$($gameSchedule.CategoryNameRaw).html"
    if (-not (Test-Path $localGameScheduleFilepath)) {
        Write-Host "Downloading game schedule for $($gameSchedule.CategoryName) from $($gameSchedule.CategoryUrl)"
        $htmlContent = Get-HtmlContent $gameSchedule.CategoryUrl
        $htmlContent | Out-File -FilePath $localGameScheduleFilepath -Encoding UTF8
        Write-Host "Game schedule for $($gameSchedule.CategoryName) saved to $localGameScheduleFilepath"
    }
    $htmlDoc = New-Object HtmlAgilityPack.HtmlDocument
    $htmlDoc.Load($localGameScheduleFilepath)
    
    $matchNodes = $htmlDoc.DocumentNode.SelectNodes(".//div[@class='row match-item calendarmatch']")

    $games = @()
    # $gameUrls = @()
 
    foreach ($matchNode in $matchNodes) {
        $gameUrlNode = $matchNode.SelectNodes('.//a') | Where-Object { $_.GetAttributeValue('href', '') -match $PATTERN_GAME_URL } 
        $gameUrl = $gameUrlNode.GetAttributeValue('href', '')
        if ($gameUrl -match $PATTERN_GAME_URL) {
            $game = @{
                "GameId"            = $Matches[1]
                "GameStatus"        = $GAME_STATUS_NOT_STARTED
                "GameDivisionName"  = $Matches[4]
                "GameUrl"           = $gameUrl
                "SeasonId"          = $appConfig.SeasonId
                "ScheduledGameDate" = Get-Date -Date $Matches[2]
                "ExcludedFromStats" = if ($Matches[4] -in $DIVISIONS_EXCLUDED -or 
                    $gameSchedule.CategoryName -in $CATEGORIES_EXCLUDED) { $true } else { $false }
            }
            $htmlNodes = $matchNode.ChildNodes | Where-Object { $_.NodeType -eq 'Element' }
      
            # find <a> node in $htmlNodes, where href value match PATTERN_GAME_URL and extract game id and division

            if ($htmlNodes.Count -eq 5) {
                # 5 divs indicate that the game is finished
                $game["GameStatus"] = $GAME_STATUS_FINISHED
            }
            $games += $game
        }
    }
    return $games 
}

function Invoke-CreateArchive($appConfig) {
    # Create season-aware filename
    $timestamp = Get-Date -Format 'yyyyMMddHHmmss'
    $seasonId = $appConfig.ConfigData.seasonId
    
    if ($seasonId -and $seasonId -ne "unknown") {
        $zipFilepath = "$ROOT/raw-data-$seasonId-$timestamp.zip"
    } else {
        $zipFilepath = "$ROOT/raw-data-$timestamp.zip"
    }
    
    Write-Host "Creating season archive: $zipFilepath"
    
    if (Test-Path $zipFilepath) {
        Remove-Item -Path $zipFilepath
    }
    Compress-Archive -Path $appConfig.FullGameStatsRawDirectory, $appConfig.GameScheduleRawDirectory -DestinationPath $zipFilepath
    return $zipFilepath
}

function Invoke-GoogleDriveUpload($filepath, $folderId) {
    # PowerShell fallback for Google Drive upload using REST API
    Write-Host "PowerShell Google Drive upload not implemented - use Python script instead"
    Write-Host "File to upload: $filepath"
    Write-Host "Folder ID: $folderId"
    return $null
}

function Test-PythonDependencies() {
    Write-Host "Checking Python environment..."
    
    # Test if Python is available
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Python is not installed or not in PATH"
            return $false
        }
        Write-Host "Found Python: $pythonVersion"
    }
    catch {
        Write-Warning "Python is not installed or not in PATH"
        return $false
    }
    
    # Test if required packages are installed
    try {
        $testResult = python -c "import pandas; import googleapiclient.discovery; print('Dependencies OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Python dependencies are installed correctly"
            return $true
        } else {
            Write-Warning "Python dependencies are missing"
            Write-Host "Error output: $testResult"
            Write-Host ""
            Write-Host "SOLUTION: Install Python dependencies by running:" -ForegroundColor Yellow
            Write-Host "  pip install -r requirements.txt" -ForegroundColor Cyan
            Write-Host ""
            return $false
        }
    }
    catch {
        Write-Warning "Error checking Python dependencies: $($_.Exception.Message)"
        return $false
    }
}

function Main($appConfig) {
    # Check Python dependencies early
    if (-not (Test-PythonDependencies)) {
        Write-Warning "Python dependencies are not properly configured. Post-processing will fall back to PowerShell-only mode."
        Write-Host ""
    }
    if (-not (Test-Path $appConfig.GamesDbFilepath) -or $appConfig.ForceDownloadFullGameStats) {
        $gameSchedules = Get-GameSchedules -appConfig $appConfig

        Invoke-MultipleDownloadRawHtml -appConfig $appConfig -urls $gameSchedules.CategoryUrl -forceToDownload $true

        $allGames = @()
        foreach ($gameSchedule in $gameSchedules) {
            Write-Host "Category URL: $($gameSchedule.CategoryUrl)"
            $games = Get-GamesInDivision -appConfig $appConfig -gameSchedule $gameSchedule
            $allGames += $games
        }

        $allGames | ConvertTo-Json -Depth 10 | Out-File -FilePath $appConfig.GamesDbFilepath -Encoding UTF8
        
    }
    else {
        $allGames = Get-Content -Path $appConfig.GamesDbFilepath -Raw | ConvertFrom-Json
    }
    $games = $allGames | Where-Object { $_.SeasonId -eq $appConfig.SeasonId }
    Write-Host "Found $($games.Count) games for season $($appConfig.SeasonId)"

    $gamesToUpdate = $games | Where-Object { $_.GameStatus -eq $GAME_STATUS_FINISHED } 
    #-or ($_.GameStatus -ne $GAME_STATUS_FINISHED -and $_.ScheduledGameDate -le (Get-Date).AddDays(3) -and $_.ExcludedFromStats -eq $false) }
    Write-Host "Found $($gamesToUpdate.Count) games to update"

    Invoke-MultipleDownloadRawHtml -appConfig $appConfig -urls $gamesToUpdate.GameUrl
    
    # Create archive and upload to Google Drive using Python script
    Write-Host "Running post-processing (CSV generation, archive creation, and Google Drive upload)..."
    
    try {
        $pythonResult = python post_process.py 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Post-processing completed successfully"
            Write-Host $pythonResult
        } else {
            Write-Warning "Post-processing completed with errors (exit code: $LASTEXITCODE)"
            Write-Host $pythonResult
            
            # Check if this is a dependency issue
            if ($pythonResult -match "Missing required Python packages" -or $pythonResult -match "ModuleNotFoundError") {
                Write-Host ""
                Write-Host "SOLUTION: This appears to be a Python dependency issue." -ForegroundColor Yellow
                Write-Host "To fix this, run the following command:" -ForegroundColor Yellow
                Write-Host "  pip install -r requirements.txt" -ForegroundColor Cyan
                Write-Host ""
            }
            
            Write-Host "Falling back to PowerShell archive creation..."
        }
    }
    catch {
        Write-Warning "Error running post-processing script: $($_.Exception.Message)"
        Write-Host "Falling back to PowerShell archive creation..."
        
        $zipFilepath = Invoke-CreateArchive -appConfig $appConfig
        if ($zipFilepath -and (Test-Path $zipFilepath)) {
            Write-Host "Archive created successfully: $zipFilepath"
            
            # Try PowerShell Google Drive upload (placeholder)
            $googleDriveConfig = $appConfig.ConfigData.googleDrive
            if ($googleDriveConfig -and $googleDriveConfig.enabled) {
                $folderId = $googleDriveConfig.folderId
                Invoke-GoogleDriveUpload -filepath $zipFilepath -folderId $folderId
            }
        } else {
            Write-Error "Failed to create archive"
        }
    }
    
}

$appConfig = Get-AppConfig

Main -appConfig $appConfig
#Main3
#$divisionUrls = Get-AllCompetitionUrls -url $FLBB_ALL_COMPTETION_URL
#$divisionUrls = @($FLBB_DIV1_URL, $FLBB_DIV2_URL, $FLBB_DIV3_URL, $FLBB_DIV4_URL)
#$divisionUrls = @($FLBB_DIV2_URL)
#Main2 -appConfig $appConfig -divisionUrls $divisionUrls 
    