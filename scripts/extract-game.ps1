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
    $playerMapFilePath = "$ROOT/$($configData.files.playerMap)"
    $eventActionPatternsFilepath = "$ROOT/$($configData.files.eventActionPatterns)"
    $FULL_GAME_STATS_RAW_DIRECTORY = "$ROOT/$($configData.directories.fullGameStatsRaw)"
    $FULL_GAME_STATS_OUTPUT_DIRECTORY = "$ROOT/$($configData.directories.fullGameStatsOutput)"
    $GAMES_DB_FILEPATH = "$ROOT/$($configData.files.gamesDb)"
    $GAME_SCHEDULE_DB_FILEPATH = "$ROOT/$($configData.files.gameScheduleDb)"
} else {
    # Default values if config is not available
    $playerMapFilePath = "$ROOT/player-map.json"
    $eventActionPatternsFilepath = "$ROOT/event-action-patterns.json"
    $FULL_GAME_STATS_RAW_DIRECTORY = "$ROOT/full-game-stats-raw"
    $FULL_GAME_STATS_OUTPUT_DIRECTORY = "$ROOT/full-game-stats-output"
    $GAMES_DB_FILEPATH = "$ROOT/gamesDB.json"
    $GAME_SCHEDULE_DB_FILEPATH = "$ROOT/gameScheduleDB.json"
}

$GAME_NOT_STARTED_SCORE = "0 : 0"

$EVENT_ACTOR_SYSTEM = "* System *"
$EVENT_ACTOR_COACH = "* Coach *"

function Update-SpecialCharacters {
    # From https://stackoverflow.com/questions/7836670/how-remove-accents-in-powershell
    param ([String]$sourceStringToClean = [String]::Empty)
    $normalizedString = $sourceStringToClean.Normalize( [Text.NormalizationForm]::FormD )
    $stringBuilder = new-object Text.StringBuilder
    $normalizedString.ToCharArray() | ForEach-Object { 
        if ( [Globalization.CharUnicodeInfo]::GetUnicodeCategory($_) -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            [void]$stringBuilder.Append($_)
        }

        
    }
    # From https://lazywinadmin.com/2015/05/powershell-remove-diacritics-accents.html
    [Text.Encoding]::ASCII.GetString([Text.Encoding]::GetEncoding("Cyrillic").GetBytes($stringBuilder.ToString()))
}
function Get-NormalizedPlayerName($appConfig, $playerName) {
    #$playerName= "TEGHO François"
    $playerName = Update-SpecialCharacters -sourceStringToClean ($playerName.Trim() -replace '\s{2,}', ' ')
    $normalizedPlayerName = $playerName
    foreach ($player in $appConfig.PlayerMap) {
        if ($playerName -in $player.PlayerNames) {
            Write-Debug "Player $playerName found in player map and replaced by $($player.NormalizedPlayerName)"
            $normalizedPlayerName = $player.NormalizedPlayerName
        }
    }
    return $normalizedPlayerName
}
function Get-EventDetails($eventDetailsRaw, $gameDescription, $appConfig) {
    $eventDetailsRaw = $eventDetailsRaw -replace '\s{2,}', ' '

    foreach ($patternCategory in $appConfig.EventActionPatterns.PSObject.Properties) {
        foreach ($languagePattern in $patternCategory.Value.PSObject.Properties) {
            if ($eventDetailsRaw -match $languagePattern.Value) {
                switch ($patternCategory.Name) {
                    "STARTING_LINEUP_ADDED" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Starting line-up added"
                            "EventActor"  = $matches[1]
                            "EventTeam"   = $matches[2]
                        }
                    }
                    "POINTS_ADDED" {
                        return @{
                            "Raw"                  = $eventDetailsRaw
                            "EventAction"          = "$($matches[1])P Points Added"
                            "EventActor"           = $matches[2]
                            "EventTeam"            = $matches[3]
                            "EventAdvantageChange" = if ($gameDescription['HomeTeamShortName'] -eq $matches[3]) { [int]$matches[1] } else { - [int]$matches[1] }
                        }
                    }
                    "FOUL_ADDED" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "$($matches[1]) Foul Added"
                            "EventActor"  = $matches[2]
                            "EventTeam"   = $matches[3]
                        }
                    }
                    "FOUL_DELETED" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "$($matches[1]) Foul Deleted"
                            "EventActor"  = $matches[2]
                            "EventTeam"   = $matches[3]
                        }
                    }
                    "POINTS_DELETED" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "$($matches[1])P Points Deleted"
                            "EventActor"  = $matches[2]
                            "EventTeam"   = $matches[3]
                        }
                    }
                    "LAST_POINTS_FOR_DIFFERENT_PLAYER" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Last points for different player"
                            "EventActor"  = $matches[1]
                            "EventTeam"   = $matches[2]
                        }
                    }
                    "PLAYER_IN_IN_QUARTER" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Player in"
                            "EventActor"  = $matches[2]
                            "EventTeam"   = $matches[3]
                        }
                    }
                    "PLAYER_IN_IN_QUARTER_DELETED"{
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Player in deleted"
                            "EventActor"  = $matches[2]
                            "EventTeam"   = $matches[3]
                        }
                    }
                    "PLAYER_ADDED_"{
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Player added"
                            "EventActor"  = $matches[1]
                            "EventTeam"   = $matches[2]    
                        }
                    }
                    "CHANGE_OF_LICENSE_NUMBER" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Change of licence number"
                            "EventActor"  = $EVENT_ACTOR_SYSTEM
                        }
                    }
                    "TIMEOUT_ADDED" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Timeout"
                            "EventTeam"   = $matches[1]
                            "EventActor"  = $EVENT_ACTOR_COACH
                        }
                    }
                    "TIMEOUT_DELETED" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Timeout Deleted"
                            "EventTeam"   = $matches[2]
                            "EventActor"  = $EVENT_ACTOR_COACH
                        }
                    }
                    "TIMEOUT_LOST" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Timeout Lost"
                            "EventTeam"   = $matches[2]
                            "EventActor"  = $EVENT_ACTOR_COACH
                        }
                    }
                    "DELETED_FROM_STARTING_LINEUP" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Deleted from starting line-up"
                            "EventActor"  = $matches[1]
                            "EventTeam"   = $matches[2]
                        }
                    }
                    "SIGNAL_END_OF_GAME" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Signal end of game"
                            "EventActor"  = $EVENT_ACTOR_SYSTEM
                        }
                    }
                    "OTHER" {
                        return @{
                            "Raw"         = $eventDetailsRaw
                            "EventAction" = "Other"
                        }
                    }
                    
                    default { continue }
                }
                break # Breaks the inner foreach loop
            }
        }
        if ($matches.Count -gt 0) { break } # Breaks the outer foreach loop if a match was found
    }
    Write-Warning "Event details not found: \"$eventDetailsRaw\""
    return @{
        "Raw"         = $eventDetailsRaw
        "EventAction" = "Unknown"
        "EventActor"  = "Unknown"
        "EventTeam"   = "Unknown"
    }
}

function Get-ForfeitGameEvents($gameDescription, $eventDate, $appConfig) {
    $gameEvents = @()
    $gameEvent = @{ 
        "EventDateTime" = $eventDate
        "EventAction"   = "Forfeit"
        "EventActor"    = $EVENT_ACTOR_SYSTEM
           
    }
    $gameEvents += $gameEvent
    return $gameEvents
}
function Get-GameEvents($htmlDoc, $eventDate, $gameDescription, $appConfig) {
    $gameEventNodes = $htmlDoc.DocumentNode.SelectNodes("//div[@class='row digiaction-item']")
    if ($null -eq $gameEventNodes) {
        $forfeitEventGames = Get-ForfeitGameEvents -gameDescription $gameDescription -eventDate $eventDate -appConfig $appConfig
        return @($forfeitEventGames)
    }
    $gameEvents = @()
    $gameEventNodes | ForEach-Object {
        $eventDateTime = $eventDate + " " + $_.SelectSingleNode(".//div[@class='col-2']").InnerText.Trim()
        $eventDetailsRaw = $_.SelectSingleNode(".//div[@class='col-10']//div").InnerText.Trim()
        $eventDetails =  Get-EventDetails -eventDetailsRaw $eventDetailsRaw -gameDescription $gameDescription -appConfig $appConfig
#        $eventDetails = Get-EventDetailsModified -eventDetailsRaw $eventDetailsRaw -gameDescription $gameDescription -appConfig $appConfig
        $eventQuarter = $_.SelectSingleNode(".//div[@class='col-7']//div[@class='col-3']").InnerText.Trim()
        $eventScore = $_.SelectSingleNode(".//div[@class='col-7']//div[@class='col-6']").InnerText.Trim()
        $eventAdvantage = $_.SelectNodes(".//div[@class='col-7']//div[@class='col-3']")[1].InnerText.Trim()
        $gameEvent = @{ 
            "EventDateTime"   = $eventDateTime 
            "EventDetailsRaw" = $eventDetails["Raw"]
            "EventAction"     = $eventDetails["EventAction"]
            "EventActor"      = $eventDetails["EventActor"]
            "EventTeam"       = $eventDetails["EventTeam"]
            "EventQuarter"    = if ("" -ne $eventQuarter) { [int]$eventQuarter } else { $null }
            "EventScore"      = $eventScore
            "EventAdvantage"  = if ("" -ne $eventAdvantage) { [int]$eventAdvantage } else { $null }
        }
        $gameEvents += $gameEvent
    }
    $sortedGameEvents = $gameEvents | Sort-Object -Property EventDateTime
    return $sortedGameEvents
}
function Get-Referres($htmlDoc) {
    $referresSectionNode = $htmlDoc.DocumentNode.SelectSingleNode("//div[@id='arbitres']")
    if ($null -eq $referresSectionNode) {
        return $null
    } 
    $referres = @()
    $referresNodes = $referresSectionNode.SelectNodes(".//div[@class='col-md-2 mb-4']")
    $referresNodes | ForEach-Object {
        $referreNode = $_.SelectSingleNode(".//div[@class='col-md-12 text-left']")
        $referre = @{ "Referee Name" = $referreNode.InnerText.Trim() }
        $referres += $referre
    }
    return $referres
}
function Get-ShortTeamName($teamName) {
    $shortTeamName = $teamName.Substring(0, 3).ToUpper() + $teamName.Substring($teamName.Length - 1, 1).ToUpper()
    return $shortTeamName
}
function Get-ForfeitTeams($gameDescription) {
    $teams = @()
    #forfeit game
    $teamHome = @{
        "Team Role"       = "Home"
        "Team Name"       = $gameDescription["HomeTeamName"]
        "Team Name Short" = Get-ShortTeamName -teamName $gameDescription["HomeTeamName"]
        "Players"         = @()
    }
    $teamHome["Total Won Points"] = [int]$gameDescription["FinalHomeScore"]
    $teamHome["Total Lost Points"] = [int]$gameDescription["FinalAwayScore"]
    $teamHome["League Points"] = $gameDescription["HomeTeamLeaguePoints"]
  
    switch ($teamHome["League Points"]) {
        0 { $teamHome["Result Outcome"] = "F" }
        1 { $teamHome["Result Outcome"] = "L" }
        2 { $teamHome["Result Outcome"] = "W" }
        Default {}
    }
    $teamAway = @{
        "Team Role"       = "Away"
        "Team Name"       = $gameDescription["AwayTeamName"]
        "Team Name Short" = Get-ShortTeamName -teamName $gameDescription["AwayTeamName"]
        "Players"         = @()
    }
    $teamAway["Total Won Points"] = [int]$gameDescription["FinalAwayScore"]
    $teamAway["Total Lost Points"] = [int]$gameDescription["FinalHomeScore"]
    $teamAway["League Points"] = $gameDescription["AwayTeamLeaguePoints"]
  
    switch ($teamAway["League Points"]) {
        0 { $teamAway["Result Outcome"] = "F" }
        1 { $teamAway["Result Outcome"] = "L" }
        2 { $teamAway["Result Outcome"] = "W" }
        Default {}
    }

    $teams += $teamHome
    $teams += $teamAway

    return $teams
}
function Get-Teams($htmlDoc, $appConfig, $gameDescription) {
    $teamsNodes = $htmlDoc.DocumentNode.SelectSingleNode("//div[@id='digiteams']").ChildNodes
    if ($null -eq $teamsNodes) {
        $teams = Get-ForfeitTeams -gameDescription $gameDescription 
        return $teams
    }
    $teams = @()
    $teamRole = "Home"
    $teamsNodes | ForEach-Object {
        $node = $_
        if ($node.Attributes["class"].Value -eq "row") {
            $teamName = $node.SelectSingleNode(".//h3").InnerText.Trim()
            $team = @{
                "Team Role"       = $teamRole
                "Team Name"       = $teamName
                "Team Name Short" = Get-ShortTeamName -teamName $teamName
                "Players"         = @()
            }
            $teamRole = "Away"
            return
        }
        if ($node.Attributes["class"].Value -eq "row digiequipe-item") {
            $summaryNodeText = $node.SelectSingleNode(".//strong").InnerHtml.Trim()
            $isSummary = $summaryNodeText -eq "Total"
            if ($isSummary) {
                $totalFoulsAttemptGiven = 0
                $team["Players"] | ForEach-Object { $totalFoulsAttemptGiven += $_["P1 Fouls"] + 2 * $_["P2 Fouls"] + 3 * $_["P3 Fouls"] + $_["U1 Fouls"] + 2 * $_["U2 Fouls"] + $_["T1 Fouls"] }
                $team["Total 1P Attempt Given"] = $totalFoulsAttemptGiven
                $teams += $team
            }
            else {
                $playerNameRaw = $node.SelectSingleNode(".//a[@class='cardcontainer']").InnerText.Trim()
                $playerName = Get-NormalizedPlayerName -playerName $playerNameRaw -appConfig $appConfig
                $playerNumber = $node.SelectSingleNode(".//div[@class='col-3']//div[@class='col-3']").InnerText.Trim()
                $playerStartingFive = if ($playerNumber.IndexOf('*') -ge 0) { "true" } else { "false" }
                $playerStatsNode = $node.SelectNodes(".//div[@class='col-9']//div[@class='col-3']//span")
                $playerTotalPoints = $playerStatsNode[0].InnerText.Trim()
                $player1PMadeShots = $playerStatsNode[1].InnerText.Trim()
                $player2PMadeShots = $playerStatsNode[2].InnerText.Trim()
                $player3PMadeShots = $playerStatsNode[3].InnerText.Trim()
                $playerFouls = $node.SelectNodes(".//div[@class='col-6']//span").InnerText.Trim() -replace '\s{2,}', ' '
                $player = @{ 
                    "Player Name"   = $playerName
                    "Player Number" = [int]($playerNumber -replace "\*", "").Trim()
                    'Starting Five' = $playerStartingFive
                    'Total Points'  = [int]$playerTotalPoints
                    '1P Made Shots' = [int]$player1PMadeShots 
                    '2P Made Shots' = [int]$player2PMadeShots
                    '3P Made Shots' = [int]$player3PMadeShots
                    'Total Fouls'   = [int]$playerFouls.Substring(0, 1)
                    'Fouls Raw'     = $playerFouls
                    'P Fouls'       = (($playerFouls | Select-String -Pattern "P " -AllMatches).Matches).Count
                    'P1 Fouls'      = (($playerFouls | Select-String -Pattern "P1" -AllMatches).Matches).Count
                    'P2 Fouls'      = (($playerFouls | Select-String -Pattern "P2" -AllMatches).Matches).Count
                    'P3 Fouls'      = (($playerFouls | Select-String -Pattern "P3" -AllMatches).Matches).Count
                    'U1 Fouls'      = (($playerFouls | Select-String -Pattern "U1" -AllMatches).Matches).Count
                    'U2 Fouls'      = (($playerFouls | Select-String -Pattern "U2" -AllMatches).Matches).Count
                    'U3 Fouls'      = (($playerFouls | Select-String -Pattern "U3" -AllMatches).Matches).Count
                    'T1 Fouls'      = (($playerFouls | Select-String -Pattern "T1" -AllMatches).Matches).Count
                    'GD Fouls'      = (($playerFouls | Select-String -Pattern "GD" -AllMatches).Matches).Count
                }
                $team["Players"] += $player
            }
        }
    }
    $teams[0]["Total 1P Shots Attempted"] = [int]$teams[1]["Total 1P Attempt Given"]
    $teams[1]["Total 1P Shots Attempted"] = [int]$teams[0]["Total 1P Attempt Given"]
    $teams[0]["Total Won Points"] = [int]$gameDescription["FinalHomeScore"]
    $teams[0]["Total Lost Points"] = [int]$gameDescription["FinalAwayScore"]
    $teams[1]["Total Won Points"] = [int]$gameDescription["FinalAwayScore"]
    $teams[1]["Total Lost Points"] = [int]$gameDescription["FinalHomeScore"]
    $teams[0]["League Points"] = $gameDescription["HomeTeamLeaguePoints"]
    $teams[1]["League Points"] = $gameDescription["AwayTeamLeaguePoints"]
    if ($teams[0]["Team Name"] -eq $gameDescription["WinnerTeam"]) { 
        $teams[0]["Result Outcome"] = "W"
        $teams[1]["Result Outcome"] = "L" 
    } 
    else {
        $teams[0]["Result Outcome"] = "L"
        $teams[1]["Result Outcome"] = "W" 
    }
    return $teams
}
function Get-MatchDatetime($htmlDoc) {
    $dateTimeNode = $htmlDoc.DocumentNode.SelectSingleNode("//div[@id='refrgame']/div[1]/div/div[2]")
    $dateTimeString = $dateTimeNode.InnerText.Trim()
    $dateTimeFormat = "dd/MM/yyyy - HH\hmm"
    $dateTime = [DateTime]::ParseExact($dateTimeString, $dateTimeFormat, $null)
    $standardDateTime = $dateTime.ToString("yyyy-MM-dd HH:mm:ss")
    return $standardDateTime
}
function Get-GameLocation($htmlDoc) {
    $gameLocationNode = $htmlDoc.DocumentNode.SelectSingleNode("//*[@id='refrgame']/div[1]/div/div[3]/a")
    if ($null -eq $gameLocationNode) {
        return $null
    }
    $location = $gameLocationNode.InnerText.Trim()
    $coordinates = $gameLocationNode.GetAttributeValue('href', '')
    
    $gameLocation = @{
        "Name"        = $location 
        "Google Link" = $coordinates
    }
    return $gameLocation
}
function Get-CalculateLeaguePoints($firstTeamScore, $secondTeamScore) {
    if ($firstTeamScore -gt $secondTeamScore) {
        return 2
    }
    if ($firstTeamScore -eq 0 -and $secondTeamScore -eq 20) {
        return 0
    }
    return 1
}
function Get-GameDescription($htmlDoc) {
    $scores = $htmlDoc.DocumentNode.SelectNodes("//div[@id='refrgame']/div[2]/div[contains(@class, 'match-score')]/div")
    $homeScore = $scores[0].InnerText.Trim()
    $awayScore = $scores[1].InnerText.Trim()
    $gameDivision = $htmlDoc.DocumentNode.SelectSingleNode("//div[@id='refrgame']/div[1]/div/div[1]").InnerText.Trim()
    $homeTeamName = $htmlDoc.DocumentNode.SelectSingleNode("//div[@id='refrgame']/div[2]/div[@class='col-4 my-auto']/a").InnerText.Trim()
    # $homeScore = $htmlDoc.DocumentNode.SelectSingleNode("//div[@id='refrgame']/div[2]/div[2]/div").InnerText.Trim()
    # $awayScore = $htmlDoc.DocumentNode.SelectSingleNode("//div[@id='refrgame']/div[2]/div[3]/div").InnerText.Trim()
    $awayTeamName = $htmlDoc.DocumentNode.SelectSingleNode("//div[@id='refrgame']/div[2]/div[@class='col-4 my-auto text-right']/a").InnerText.Trim()
    
    $gameDescription = @{
        "Division"             = $gameDivision
        "TeamsShort"           = "$homeTeamName - $awayTeamName"
        "HomeTeamName"         = $homeTeamName
        "AwayTeamName"         = $awayTeamName
        "FinalScore"           = "$homeScore : $awayScore"
        "FinalHomeScore"       = "$homeScore"
        "FinalAwayScore"       = "$awayScore"
        "WinnerTeam"           = if ([int]$homeScore -gt [int]$awayScore) { $homeTeamName } else { $awayTeamName }
        "LoserTeam"            = if ([int]$homeScore -lt [int]$awayScore) { $homeTeamName } else { $awayTeamName }
        "HomeTeamLeaguePoints" = Get-CalculateLeaguePoints -firstTeamScore ([int]$homeScore) -secondTeamScore ([int]$awayScore)
        "AwayTeamLeaguePoints" = Get-CalculateLeaguePoints -firstTeamScore ([int]$awayScore) -secondTeamScore ([int]$homeScore)
    }
    return $gameDescription
}
function New-FullGameStatsJson($content, $gameId, $appConfig) {
    $teams = @()
     
    $htmlDoc = New-Object HtmlAgilityPack.HtmlDocument
    $htmlDoc.LoadHtml($content)
    
    $gameDescritpion = Get-GameDescription -htmlDoc $htmlDoc
    if ($gameDescritpion['FinalScore'] -eq $GAME_NOT_STARTED_SCORE) {
        Write-Warning "Game $gameId is not started yet."
        return $null
    }
    $referres = Get-Referres -htmlDoc $htmlDoc
    $teams = Get-Teams -htmlDoc $htmlDoc -appConfig $appConfig -gameDescription $gameDescritpion
    $dateTime = Get-MatchDatetime -htmlDoc $htmlDoc 
    $gameLocation = Get-GameLocation -htmlDoc $htmlDoc
    # $gameContext = @{
    #     "HomeTeamName"      = $teams[0]["Team Name"]
    #     "HomeTeamShortName" = $teams[0]["Team Name Short"]
    #     "AwayTeamName"      = $teams[1]["Team Name"]
    #     "AwayTeamShortName" = $teams[1]["Team Name Short"]
    # }
    $events = @(Get-GameEvents -htmlDoc $htmlDoc -eventDate ($dateTime.Substring(0, 10)) -gameDescription $gameDescritpion -appConfig $appConfig)
    #    $events = @(Get-GameEventsParallel -htmlDoc $htmlDoc -eventDate ($dateTime.Substring(0, 10)) -gameDescription $gameDescritpion -appConfig $appConfig)
  
    $game = [ordered]@{
        "GameId"               = $gameId
        "GameLocation"         = $gameLocation
        "GameDivisionDisplay"  = $gameDescritpion['Division']
        "GameTeamsShort"       = $gameDescritpion['TeamsShort']
        "GameFinalScore"       = $gameDescritpion['FinalScore']
        "GameWinner"           = $gameDescritpion['WinnerTeam']
        "GameLoser"            = $gameDescritpion['LoserTeam']
        "HomeTeamName"         = $gameDescritpion['HomeTeamName']
        "AwayTeamName"         = $gameDescritpion['AwayTeamName']
        "HomeTeamLeaguePoints" = [int]$gameDescritpion['HomeTeamLeaguePoints']
        "AwayTeamLeaguePoints" = [int]$gameDescritpion['AwayTeamLeaguePoints']
        "FinalHomeScore"       = [int]$gameDescritpion['FinalHomeScore']
        "FinalAwayScore"       = [int]$gameDescritpion['FinalAwayScore']
        "Referres"             = $referres
        "DateTime"             = $dateTime
        "Teams"                = $teams
        "GameEvents"           = $events
    }
   
    if ($null -eq $game["GameId"]) {
        Write-Warning "Game $($game["GameId"]) is not registered in Digibou."
    }
    $json = $game  | ConvertTo-Json -Depth 10
    return $json
}

function New-FullGameStatsJsonWithMeasurement($content, $gameId, $appConfig) {
    $teams = @()
     
    $htmlDoc = New-Object HtmlAgilityPack.HtmlDocument
    $htmlDoc.LoadHtml($content)
    
    # Measure Get-GameDescription execution time
    $gameDescriptionTime = Measure-Command {
        $gameDescription = Get-GameDescription -htmlDoc $htmlDoc
    }
    Write-Host "Get-GameDescription Execution Time: $($gameDescriptionTime.TotalMilliseconds) milliseconds"

    if ($gameDescription['FinalScore'] -eq $GAME_NOT_STARTED_SCORE) {
        Write-Warning "Game $gameId is not started yet."
        return $null
    }

    # Measure Get-Referres execution time
    $referresTime = Measure-Command {
        $referres = Get-Referres -htmlDoc $htmlDoc
    }
    Write-Host "Get-Referres Execution Time: $($referresTime.TotalMilliseconds) milliseconds"

    # Measure Get-Teams execution time
    $teamsTime = Measure-Command {
        $teams = Get-Teams -htmlDoc $htmlDoc -appConfig $appConfig -gameDescription $gameDescription
    }
    Write-Host "Get-Teams Execution Time: $($teamsTime.TotalMilliseconds) milliseconds"

    # Measure Get-MatchDatetime execution time
    $dateTimeTime = Measure-Command {
        $dateTime = Get-MatchDatetime -htmlDoc $htmlDoc 
    }
    Write-Host "Get-MatchDatetime Execution Time: $($dateTimeTime.TotalMilliseconds) milliseconds"

    # Measure Get-GameLocation execution time
    $gameLocationTime = Measure-Command {
        $gameLocation = Get-GameLocation -htmlDoc $htmlDoc
    }
    Write-Host "Get-GameLocation Execution Time: $($gameLocationTime.TotalMilliseconds) milliseconds"

    # Measure Get-GameEvents execution time
    $eventsTime = Measure-Command {
        $events = @(Get-GameEvents -htmlDoc $htmlDoc -eventDate ($dateTime.Substring(0, 10)) -gameDescription $gameDescription -appConfig $appConfig)
    }
    Write-Host "Get-GameEvents Execution Time: $($eventsTime.TotalMilliseconds) milliseconds"
  
    # $game = @{
    #     "GameId"               = $gameId
    #     "GameLocation"         = $gameLocation
    #     "GameDivisionDisplay"  = $gameDescritpion['Division']
    #     "GameTeamsShort"       = $gameDescritpion['TeamsShort']
    #     "GameFinalScore"       = $gameDescritpion['FinalScore']
    #     "GameWinner"           = $gameDescritpion['WinnerTeam']
    #     "GameLoser"            = $gameDescritpion['LoserTeam']
    #     "HomeTeamName"         = $gameDescritpion['HomeTeamName']
    #     "AwayTeamName"         = $gameDescritpion['AwayTeamName']
    #     "HomeTeamLeaguePoints" = [int]$gameDescritpion['HomeTeamLeaguePoints']
    #     "AwayTeamLeaguePoints" = [int]$gameDescritpion['AwayTeamLeaguePoints']
    #     "FinalHomeScore"       = [int]$gameDescritpion['FinalHomeScore']
    #     "FinalAwayScore"       = [int]$gameDescritpion['FinalAwayScore']
    #     "Referres"             = $referres
    #     "DateTime"             = $dateTime
    #     "Teams"                = $teams
    #     "GameEvents"           = $events
    # }

    # if ($null -eq $game["GameId"]) {
    #     Write-Warning "Game $($game["GameId"]) is not registered in Digibou."
    # }

    $jsonTime = Measure-Command {
        $json = $game | ConvertTo-Json -Depth 10
    }
    Write-Host "ConvertTo-Json Execution Time: $($jsonTime.TotalMilliseconds) milliseconds"

    return $json
}

function Invoke-CreateGameStatsJson($appConfig, $game, $forceToProcess = $false) {
    $outputDirectory = "$($appConfig.FullGameStatsOutputDirectory)/$($game.gameDivisionName)"
    $rawHtmlDirectory = "$($appConfig.FullGameStatsRawDirectory)/$($game.gameDivisionName)"

    $filepath = "$rawHtmlDirectory/full-game-stats-$($game.gameId).html"
    $outputFilepath = "$outputDirectory/full-game-stats-$($game.gameId).json"

    if (-not (Test-Path $filepath)) {
        Write-Warning "Game $($game.gameId) not found ($filepath)"
        return
    }
    if ((Test-Path $outputFilepath) -and (-not ($forceToProcess))) {
        Write-Debug "Game $($game.gameId) already processed"
        return
    }
    if (-not (Test-Path $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory
    }
    $content = Get-Content -Path $filepath
    
    $json = New-FullGameStatsJson -content $content -gameId $($game.gameId) -appConfig $appConfig
    #  $json = New-FullGameStatsJsonWithMeasurement -content $content -gameId $($game.gameId) -appConfig $appConfig
    Set-Content -Path $outputFilepath -Value $json -Encoding utf8 -NoNewline
    Write-Host "Game $($game.gameId) processed"
}
function Main ($appConfig) {
    #    $games = $appConfig.GamesDb | Where-Object { $_.gameDivisionName -eq "division1-hommes" -and $_.GameStatus -eq "Finished" }
    $games = $appConfig.GamesDb | Where-Object { $_.GameStatus -eq "Finished" }
    Write-Host "Processing $($games.Count) games"
    Write-Host "Games $($games.Count) found"
    $processedGames = 1

    foreach ($game in $games) {
        Invoke-CreateGameStatsJson -appConfig $appConfig -game $game
        if ($processedGames % 50 -eq 0) {
            Write-Host "Processed $([System.Math]::Round($processedGames/$gameS.Count *100,0))% of games"
        }
        $processedGames++
    }
}
function Get-AppConfig() {
    #  $map = Get-Content -Path $playerMapFilePath | ConvertFrom-Json
    $appConfig = @{
        "PlayerMap"                    = Get-Content -Path $playerMapFilePath | ConvertFrom-Json
        "EventActionPatterns"          = Get-Content -Path $eventActionPatternsFilepath | ConvertFrom-Json
        "GamesDb"                      = Get-Content -Path $GAMES_DB_FILEPATH | ConvertFrom-Json
        "GameScheduleDb"               = Get-Content -Path $GAME_SCHEDULE_DB_FILEPATH | ConvertFrom-Json
        "FullGameStatsOutputDirectory" = $FULL_GAME_STATS_OUTPUT_DIRECTORY
        "FullGameStatsRawDirectory"    = $FULL_GAME_STATS_RAW_DIRECTORY
    }
    return $appConfig
}
$appConfig = Get-AppConfig

#Main -appConfig $appConfig

$mainTime = Measure-Command {
    Main -appConfig $appConfig
}
Write-Host "Main Execution Time: $($mainTime.TotalSeconds) seconds"
