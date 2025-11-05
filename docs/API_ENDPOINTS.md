# API Endpoints Documentation

This document describes the API endpoints available in the FLBB Statistics application.

## 📋 Overview

The application provides several API endpoints for retrieving statistical data in JSON format. These endpoints are primarily used for hover tooltips but can also be accessed directly for integration with other tools.

## 🔗 Base URL

**Local Development:**
```
http://localhost:5000/api
```

**Production:**
```
https://your-domain.com/api
```

## 📊 Available Endpoints

### 1. Player Hover Stats

Get quick statistics for a specific player to display in hover tooltips.

**Endpoint:**
```
GET /api/hover/player/<player_name>
```

**Parameters:**
- `player_name` (path parameter) - URL-encoded player name

**Example Request:**
```
GET /api/hover/player/John%20Smith
```

**Response Format:**
```json
{
  "success": true,
  "player_name": "John Smith",
  "stats": {
    "total_games": 15,
    "total_points": 247,
    "average_points": 16.47,
    "highest_score": 28,
    "total_fouls": 23,
    "teams": ["Team A", "Team B"]
  }
}
```

**Response Fields:**
- `success` - Boolean indicating if request was successful
- `player_name` - Player's full name
- `stats.total_games` - Total games played
- `stats.total_points` - Total points scored
- `stats.average_points` - Points per game average
- `stats.highest_score` - Highest single-game score
- `stats.total_fouls` - Total fouls committed
- `stats.teams` - List of teams player has played for

**Error Response:**
```json
{
  "success": false,
  "error": "Player not found"
}
```

### 2. Team Hover Stats

Get quick statistics for a specific team.

**Endpoint:**
```
GET /api/hover/team/<team_name>
```

**Parameters:**
- `team_name` (path parameter) - URL-encoded team name

**Example Request:**
```
GET /api/hover/team/Racing%20Luxembourg
```

**Response Format:**
```json
{
  "success": true,
  "team_name": "Racing Luxembourg",
  "stats": {
    "total_games": 20,
    "wins": 15,
    "losses": 5,
    "win_percentage": 75.0,
    "points_scored": 1543,
    "points_allowed": 1324,
    "point_differential": 219,
    "average_points_scored": 77.15,
    "average_points_allowed": 66.2,
    "division": "Division 1 Hommes",
    "position": 2,
    "streak": "W3"
  }
}
```

**Response Fields:**
- `success` - Boolean indicating success
- `team_name` - Team's full name
- `stats.total_games` - Total games played
- `stats.wins` - Number of wins
- `stats.losses` - Number of losses
- `stats.win_percentage` - Win percentage (0-100)
- `stats.points_scored` - Total points scored
- `stats.points_allowed` - Total points allowed
- `stats.point_differential` - Net point difference
- `stats.average_points_scored` - Average points per game
- `stats.average_points_allowed` - Average points allowed per game
- `stats.division` - Team's division
- `stats.position` - Current position in standings
- `stats.streak` - Current win/loss streak (e.g., "W3" = 3 wins)

### 3. Referee Hover Stats

Get quick statistics for a specific referee.

**Endpoint:**
```
GET /api/hover/referee/<referee_name>
```

**Parameters:**
- `referee_name` (path parameter) - URL-encoded referee name

**Example Request:**
```
GET /api/hover/referee/Jane%20Doe
```

**Response Format:**
```json
{
  "success": true,
  "referee_name": "Jane Doe",
  "stats": {
    "total_games": 45,
    "total_fouls": 892,
    "average_fouls_per_game": 19.82,
    "divisions": ["Division 1 Hommes", "Division 2 Hommes"],
    "performance_index": 8.5
  }
}
```

**Response Fields:**
- `success` - Boolean indicating success
- `referee_name` - Referee's full name
- `stats.total_games` - Total games officiated
- `stats.total_fouls` - Total fouls called
- `stats.average_fouls_per_game` - Average fouls per game
- `stats.divisions` - List of divisions worked
- `stats.performance_index` - Performance rating (1-10)

### 4. Game Hover Stats

Get quick statistics for a specific game.

**Endpoint:**
```
GET /api/hover/game/<game_id>
```

**Parameters:**
- `game_id` (path parameter) - Unique game identifier

**Example Request:**
```
GET /api/hover/game/12345
```

**Response Format:**
```json
{
  "success": true,
  "game_id": "12345",
  "stats": {
    "date": "2025-11-05",
    "home_team": "Team A",
    "away_team": "Team B",
    "home_score": 85,
    "away_score": 78,
    "division": "Division 1 Hommes",
    "lead_changes": 12,
    "tie_scores": 8,
    "biggest_lead": 15,
    "hotness_score": 7.8,
    "top_scorer": {
      "name": "John Smith",
      "points": 28
    }
  }
}
```

**Response Fields:**
- `success` - Boolean indicating success
- `game_id` - Unique game identifier
- `stats.date` - Game date (YYYY-MM-DD)
- `stats.home_team` - Home team name
- `stats.away_team` - Away team name
- `stats.home_score` - Final home team score
- `stats.away_score` - Final away team score
- `stats.division` - Game division
- `stats.lead_changes` - Number of lead changes
- `stats.tie_scores` - Number of tie scores
- `stats.biggest_lead` - Largest lead by any team
- `stats.hotness_score` - Game excitement rating (1-10)
- `stats.top_scorer` - Top scorer information

## 🔐 Authentication

Currently, all API endpoints are **publicly accessible** and do not require authentication.

⚠️ **Security Consideration:** Public API endpoints without authentication can be subject to abuse. For production deployments, consider implementing:

### Recommended Security Measures

**For Production Environments:**

1. **Rate Limiting**
   - Limit requests per IP address (e.g., 100 requests per minute)
   - Implement exponential backoff for repeated requests
   - Use tools like Flask-Limiter or nginx rate limiting

   ```python
   from flask_limiter import Limiter
   from flask_limiter.util import get_remote_address
   
   limiter = Limiter(
       app,
       key_func=get_remote_address,
       default_limits=["100 per minute"]
   )
   
   @app.route('/api/hover/player/<player_name>')
   @limiter.limit("50 per minute")
   def api_player_hover(player_name):
       # endpoint code
   ```

2. **API Key Authentication**
   - Require API keys for external access
   - Implement key rotation and expiration
   - Track usage per API key

3. **CORS Configuration**
   - Restrict origins that can access the API
   - Configure allowed methods and headers
   - Use Flask-CORS for proper CORS handling

4. **Request Validation**
   - Validate all input parameters
   - Sanitize user input to prevent injection attacks
   - Implement request size limits

5. **Monitoring and Logging**
   - Log all API requests with timestamps and IPs
   - Monitor for unusual patterns or abuse
   - Set up alerts for suspicious activity

### Future Authentication Plans

For future versions, these authentication methods may be added:
- **API Key Authentication** - Simple key-based access control
- **OAuth2 Integration** - Industry-standard authentication
- **JWT Tokens** - Stateless authentication for scalability
- **IP Whitelisting** - Restrict access to known IPs

## 📝 Request Guidelines

### URL Encoding

Always URL-encode parameters containing special characters:

**Correct:**
```
/api/hover/player/Jean-Paul%20Muller
```

**Incorrect:**
```
/api/hover/player/Jean-Paul Muller
```

### Case Sensitivity

Names are case-sensitive. Use exact names as they appear in the database:
- "Racing Luxembourg" ✅
- "racing luxembourg" ❌
- "RACING LUXEMBOURG" ❌

### Character Encoding

All responses use UTF-8 encoding to support international characters:
- French: é, è, à, ç
- German: ä, ö, ü, ß
- Luxembourg: Special team names

## 🚀 Usage Examples

### JavaScript (Fetch API)

```javascript
// Fetch player stats
async function getPlayerStats(playerName) {
  const encodedName = encodeURIComponent(playerName);
  const response = await fetch(`/api/hover/player/${encodedName}`);
  const data = await response.json();
  
  if (data.success) {
    console.log(`${data.player_name}: ${data.stats.average_points} PPG`);
  } else {
    console.error(data.error);
  }
}

// Fetch team stats
async function getTeamStats(teamName) {
  const encodedName = encodeURIComponent(teamName);
  const response = await fetch(`/api/hover/team/${encodedName}`);
  const data = await response.json();
  
  if (data.success) {
    console.log(`${data.team_name}: ${data.stats.wins}-${data.stats.losses}`);
  }
}
```

### jQuery

```javascript
// Get player stats with jQuery
$.ajax({
  url: '/api/hover/player/' + encodeURIComponent(playerName),
  method: 'GET',
  success: function(data) {
    if (data.success) {
      $('#player-stats').html(`
        <strong>${data.player_name}</strong><br>
        Games: ${data.stats.total_games}<br>
        Avg: ${data.stats.average_points} PPG
      `);
    }
  }
});
```

### Python (requests)

```python
import requests
from urllib.parse import quote

def get_player_stats(player_name):
    base_url = "http://localhost:5000"
    encoded_name = quote(player_name)
    url = f"{base_url}/api/hover/player/{encoded_name}"
    
    response = requests.get(url)
    data = response.json()
    
    if data['success']:
        print(f"{data['player_name']}: {data['stats']['average_points']} PPG")
    else:
        print(f"Error: {data['error']}")

# Usage
get_player_stats("John Smith")
```

### cURL

```bash
# Get player stats
curl "http://localhost:5000/api/hover/player/John%20Smith"

# Get team stats
curl "http://localhost:5000/api/hover/team/Racing%20Luxembourg"

# Get referee stats
curl "http://localhost:5000/api/hover/referee/Jane%20Doe"

# Get game stats
curl "http://localhost:5000/api/hover/game/12345"
```

## 🎯 Use Cases

### 1. Hover Tooltips (Primary Use)

Display quick stats when users hover over names:

```javascript
$('.player-name').hover(function() {
  const playerName = $(this).text();
  fetch(`/api/hover/player/${encodeURIComponent(playerName)}`)
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        showTooltip(data.stats);
      }
    });
});
```

### 2. External Integration

Integrate with external dashboards or tools:

```python
# Fetch all team stats for external dashboard
teams = ["Team A", "Team B", "Team C"]
stats = []

for team in teams:
    response = requests.get(f"http://api/hover/team/{quote(team)}")
    if response.json()['success']:
        stats.append(response.json())

# Export to CSV, database, etc.
```

### 3. Mobile App Integration

Use endpoints in mobile applications:

```swift
// Swift example
func fetchPlayerStats(playerName: String) {
    let encodedName = playerName.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed)!
    let url = URL(string: "https://api/hover/player/\(encodedName)")!
    
    URLSession.shared.dataTask(with: url) { data, response, error in
        if let data = data {
            let stats = try? JSONDecoder().decode(PlayerStats.self, from: data)
            // Use stats
        }
    }.resume()
}
```

## ⚡ Performance

### Response Times

Typical response times:
- Player stats: 50-100ms
- Team stats: 75-150ms
- Referee stats: 50-100ms
- Game stats: 100-200ms

### Caching

Currently, no caching is implemented. Consider:
- Browser caching for static data
- Server-side caching for frequently accessed endpoints
- CDN caching for production deployments

### Rate Limiting

No rate limiting is currently enforced, but consider implementing:
- Per-IP rate limits
- Per-endpoint rate limits
- Graceful degradation when limits are exceeded

## 🐛 Error Handling

### Common Errors

**404 Not Found:**
```json
{
  "success": false,
  "error": "Player not found"
}
```

**400 Bad Request:**
```json
{
  "success": false,
  "error": "Invalid player name format"
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "error": "An error occurred while processing your request"
}
```

### Best Practices

1. **Always check `success` field** before accessing stats
2. **Handle errors gracefully** with fallback UI
3. **Validate input** before making requests
4. **Implement retry logic** for network failures

## 📚 Related Documentation

- [Main README](../README.md) - Project overview
- [User Features Guide](USER_FEATURES.md) - User-facing features
- [Deployment Guide](README_DEPLOYMENT.md) - Deployment instructions

---

**Use these APIs to build amazing basketball statistics integrations!** 🏀
