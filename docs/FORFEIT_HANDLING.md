# Forfeit Game Handling

## Overview
This document explains how the FLBB Statistics system handles forfeit games.

## Detection
Forfeit games are detected by parsing the game location field. When a team forfeits, the FLBB website includes "FORFAIT <team name>" in the location text.

### Example
```
Hall Omnisp. Alain Marchetti - FORFAIT BBC East Side Pirates B
```

## Processing

### 1. Location Parsing (`Get-GameLocation`)
The location field is parsed using regex pattern:
```powershell
if ($location -match "FORFAIT\s+(.+)$")
```

This extracts:
- `IsForfeit`: Boolean flag (true/false)
- `ForfeitTeam`: Name of the team that forfeited

### 2. Score Adjustment (`Get-GameDescription`)
When a forfeit is detected:
1. Match the forfeit team to either home or away team
2. Set score based on which team forfeited:
   - Away team forfeits → Score: 20:0 (home wins)
   - Home team forfeits → Score: 0:20 (away wins)

### 3. Team Matching
Uses bidirectional regex matching to handle team name variations:
```powershell
$awayTeamName -match [regex]::Escape($forfeitTeam) -or 
$forfeitTeam -match [regex]::Escape($awayTeamName)
```

This handles cases where:
- Forfeit text uses abbreviations
- Team names have slight variations
- Extra characters or spacing differences exist

## League Points
The existing league points calculation automatically handles forfeit scores:
- Winner: 2 points
- Forfeit team: 0 points
- Regular loser: 1 point

This is implemented in `Get-CalculateLeaguePoints`:
```powershell
if ($firstTeamScore -eq 0 -and $secondTeamScore -eq 20) {
    return 0  # Forfeit team gets 0 points
}
```

## Output Format

### JSON Structure
```json
{
  "GameId": "1701053",
  "GameLocation": {
    "Name": "Hall Omnisp. Alain Marchetti - FORFAIT BBC East Side Pirates B",
    "Google Link": "https://maps.app.goo.gl/...",
    "IsForfeit": true,
    "ForfeitTeam": "BBC East Side Pirates B"
  },
  "GameFinalScore": "20 : 0",
  "HomeTeamLeaguePoints": 2,
  "AwayTeamLeaguePoints": 0,
  "FinalHomeScore": 20,
  "FinalAwayScore": 0
}
```

### CSV Output
In the CSV file, forfeit games appear with:
- GameFinalScore: "20 : 0" or "0 : 20"
- Correct league points for each team
- GameLocation: Original text with FORFAIT marker

## Logging
When processing a forfeit game, the system outputs:
```
Forfeit detected: <team name> (<home/away> team) forfeited. Score adjusted to <score>
```

If team matching fails, a warning is logged:
```
WARNING: Forfeit team '<team>' could not be matched to home team '<home>' or away team '<away>'
```

## Integration with Existing Features

### Game Events
Forfeit games use the existing `Get-ForfeitGameEvents` function which creates a single system event marking the forfeit.

### Team Statistics
The existing `Get-ForfeitTeams` function handles teams with empty player rosters, which is typical for forfeit games.

### Database
Forfeit games are included in statistics with:
- Adjusted scores (20:0 or 0:20)
- Correct league points
- Original location text preserved

## Backward Compatibility
The implementation is fully backward compatible:
- Existing GameLocation fields (Name, Google Link) remain unchanged
- New fields (IsForfeit, ForfeitTeam) are additions only
- Python code accessing `GameLocation['Name']` continues to work
- No changes to database schema or CSV format structure

## Testing
To test forfeit detection:
1. Create HTML with forfeit marker in location
2. Run extract-game.ps1 on the HTML
3. Verify JSON output has correct score and league points
4. Check CSV export has correct values

## Future Considerations
- Add forfeit statistics to analytics
- Track forfeit frequency by team/division
- Support alternative forfeit score conventions if league rules change
