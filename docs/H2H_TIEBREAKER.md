# Head-to-Head Tiebreaker Implementation

## Overview

When two or more teams have the same number of league points in the standings, the ranking is now determined using head-to-head (H2H) records between those teams.

## How It Works

### Tiebreaker Order

When teams are tied on league points, the following rules apply in order:

1. **H2H Points** - Points earned in direct games between the tied teams
2. **H2H Diff** - Score difference in games between the tied teams
3. **Points Diff** - Overall score difference (existing tiebreaker)

### Calculation Logic

For teams with equal league points:

1. Create a "mini-table" containing only games between the tied teams
2. Calculate league points from those games (2 for win, 1 for loss)
3. Calculate score differences from those games
4. Rank teams by H2H Points, then H2H Diff, then overall Points Diff

### Examples

#### Two-Team Tie
```
Team A vs Team B: 75-70 (A wins)
Team B vs Team A: 73-77 (A wins)

H2H Results:
- Team A: 2 wins × 2 points = 4 H2H Points, +9 H2H Diff
- Team B: 2 losses × 1 point = 2 H2H Points, -9 H2H Diff

Ranking: Team A ranked higher (better H2H record)
```

#### Three-Way Circular Tie
```
Team A vs Team B: 80-70 (A wins)
Team B vs Team C: 75-65 (B wins)
Team C vs Team A: 78-72 (C wins)

H2H Results (everyone 1-1):
- Team A: 3 H2H Points, +4 H2H Diff
- Team B: 3 H2H Points, 0 H2H Diff
- Team C: 3 H2H Points, -4 H2H Diff

Ranking: A, B, C (sorted by H2H score difference)
```

## UI Changes

### Standings Table

Two new columns added:

| Column | Description |
|--------|-------------|
| **H2H Pts** | Points earned in games between teams with same league points |
| **H2H Diff** | Score difference in games between teams with same league points |

These columns:
- Have tooltips explaining their purpose
- Are styled as "important" columns (visible on most screen sizes)
- Show 0 for teams not involved in ties
- Only affect ranking when league points are equal

## Testing

### Test Coverage

1. **Unit Tests** (`tests/test_h2h_standings.py`)
   - Two-team H2H calculation
   - Standings with H2H tiebreaker
   - Three-way circular tie scenarios

2. **Integration Tests** (`tests/test_standings_display.py`)
   - HTML generation with H2H columns
   - Display formatting verification

3. **Real Data Tests**
   - Verified across all 7 divisions
   - 51 teams affected by H2H tiebreaker
   - All tied groups correctly sorted

### Test Results (2024-12-01)

From M-Division 1:
```
16 points (3 teams tied):
  - AB Contern B: H2H Pts=3, H2H Diff=+3
  - Racing Luxembourg B: H2H Pts=3, H2H Diff=+3
  - Racing Luxembourg C: H2H Pts=3, H2H Diff=-6

14 points (3 teams tied):
  - Basket Esch B: H2H Pts=4, H2H Diff=+33
  - Musel Pikes B: H2H Pts=1, H2H Diff=-4
  - Sparta Bertrange B: H2H Pts=1, H2H Diff=-29
```

## Technical Details

### Implementation

**Location**: `src/utils.py`

**Functions**:
- `calculate_head_to_head(df, teams)` - Calculates H2H stats for a group of teams
- `calculate_standings(df)` - Updated to include H2H tiebreaker

**Algorithm**:
1. Calculate all regular standings (W/L, Points, etc.)
2. Group teams by league points
3. For each group of 2+ teams:
   - Filter games to only those between the tied teams
   - Calculate H2H points and score differences
   - Store in new columns
4. Sort by: League Points → H2H Points → H2H Diff → Points Diff

### Performance

- Minimal impact on performance
- H2H calculation only runs for tied teams
- Most divisions have small tie groups (2-4 teams)
- Sorting remains O(n log n)

## Code Quality

- ✓ All tests passing
- ✓ CodeQL security scan: No issues
- ✓ Cross-platform compatible
- ✓ Well-documented with comments
- ✓ Follows existing code patterns

## Future Enhancements

Potential improvements:
1. Add visual indicators in UI for tied teams
2. Show H2H game details in tooltip
3. Support additional tiebreaker rules if needed
4. Add H2H stats to team detail pages
