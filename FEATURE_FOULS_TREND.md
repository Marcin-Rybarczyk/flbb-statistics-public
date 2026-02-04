# Team Fouls Trend Statistics - Feature Enhancement

## Overview
Enhanced the existing team fouls trend feature to include comprehensive statistical analysis and visual indicators showing whether teams are improving or worsening in their fouling behavior over the season.

## What Was Already Present
- Basic fouls trend visualization (line chart)
- Per-game foul data collection
- Team selection interface
- Export to Excel functionality

## What Was Added

### 1. Statistical Analysis Function (`calculate_fouls_trend_statistics`)
A new function that calculates:
- **Average fouls per game**: Mean of all games
- **Linear regression slope**: Measures the rate of change
- **Trend direction**: Classifies as "improving" (↓), "worsening" (↑), or "stable" (→)
- **Min/Max values**: Range of fouls over the season
- **First half vs Second half comparison**: Shows progression
- **Percentage change**: Quantifies improvement or decline

### 2. Enhanced Data Structure
Modified `get_team_fouls_trend_data()` to return:
```python
{
    'TeamName': {
        'games': [
            {game_number, date, game_id, total_fouls, fouls_by_type}
        ],
        'statistics': {
            'average', 'slope', 'trend_direction', 'trend_indicator',
            'first_half_avg', 'second_half_avg', 'change_percent',
            'min', 'max', 'total_games'
        }
    }
}
```

### 3. Visual Statistics Display
Added interactive statistics cards below the chart showing:
- Color-coded trend indicator (green=improving, red=worsening, gray=stable)
- Key metrics in an easy-to-read card format
- Season progression visualization
- Matches the team colors from the chart

### 4. Enhanced Excel Export
Updated Excel export to include:
- Statistics summary at the top of each team's sheet
- Trend analysis information
- All detailed game-by-game data

## How It Works

### Algorithm for Trend Detection
1. **Linear Regression**: Calculates slope using least squares method
2. **Threshold**: Slopes < 0.1 absolute value are considered "stable"
3. **Direction**: Negative slope = improving (fewer fouls), Positive = worsening

### Mathematical Formula
```
Slope = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)

where:
- n = number of games
- x = game numbers (1, 2, 3, ...)
- y = fouls for each game
```

### Example Calculation
For a team with fouls: [25, 24, 22, 21, 20, 18, 17, 16]
- Average: 20.4 fouls/game
- Slope: -1.321 (improving)
- First half: 23.0, Second half: 17.8
- Change: -22.8% (improvement)

## User Interface

### Location
Team Statistics page → Fouls tab → "📈 Fouls Trend Over Games" section

### Interaction Flow
1. User selects teams from dropdown (up to 5 teams)
2. Clicks "📊 Load Trend Chart"
3. Chart displays with fouls per game
4. Statistics cards appear below showing trend analysis
5. User can export data to Excel with statistics included

### Visual Elements
- **Trend Indicator**: ↑ (worsening), ↓ (improving), → (stable)
- **Color Coding**: Red (worsening), Green (improving), Gray (stable)
- **Statistics Cards**: Grid layout, color-matched to chart lines
- **Progress Bar**: Visual comparison of first vs second half

## Testing

### Unit Tests
Created `test_trend_stats.py` with 5 test cases:
- ✓ Improving trend detection
- ✓ Worsening trend detection
- ✓ Stable trend detection
- ✓ Empty data handling
- ✓ Single value handling

All tests pass successfully.

### Integration
- Function integrates with existing data loading
- Backwards compatible (handles both new and old data formats)
- No breaking changes to existing functionality

## Files Modified

1. **src/utils.py**: Added statistical calculation functions
2. **src/app.py**: Updated Excel export to include statistics
3. **templates/team_stats.html**: Added statistics display and updated JavaScript

## Technical Decisions

### Why Linear Regression?
- Simple and interpretable
- Works well with small sample sizes
- Provides clear trend direction
- Computationally efficient

### Why 0.1 Threshold for Stable?
- Less than 0.1 fouls per game change is negligible
- Accounts for natural variation
- Prevents over-sensitivity to minor fluctuations

### Why First Half vs Second Half?
- Easy to understand
- Shows season-long improvement/decline
- Doesn't require complex time-series analysis

## Future Enhancements (Not Implemented)
- Moving average smoothing
- Confidence intervals
- Trend prediction for future games
- Comparison against league average
- Heat map of foul types over time

## Performance Considerations
- Calculations done on-demand when user requests
- Minimal overhead (linear time complexity)
- No database changes required
- Works with existing CSV data source

## Backwards Compatibility
- JavaScript checks for both old and new data formats
- Excel export handles missing statistics gracefully
- No changes required to existing routes
- Existing functionality preserved
