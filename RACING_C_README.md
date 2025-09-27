# Racing C Static Website Generator

This document describes how to generate a static website specifically for the Racing C basketball team.

## Overview

The Racing C static website generator creates a focused version of the basketball statistics site that shows only data relevant to the Racing C team. This includes:

- Racing C game results and statistics
- Division standings (highlighting Racing C's position)
- Team-specific performance metrics
- Racing C's highest scoring games

## Usage

### Generate Racing C Static Site

```bash
python3 generate_racing_c_static.py
```

This will create a new directory `racing-c-site/` containing the static HTML files optimized for Racing C team.

### Output Structure

```
racing-c-site/
├── index.html              # Racing C homepage with team overview
├── statistics.html         # Game results and top performances
├── division-2---hommes.html # Division standings page
└── static/                 # Static assets directory
```

### Features

1. **Team Overview**: Shows Racing C's season statistics including:
   - Total games played
   - Win-loss record
   - Win percentage
   - Average points scored

2. **Game Results**: Displays Racing C's games sorted by total points scored

3. **Division Context**: Shows the full Division:2 - Hommes standings with Racing C highlighted

4. **Team-Focused Branding**: Custom title and description focused on Racing C

## Differences from Main Site

The Racing C site differs from the main FLBB statistics site in several ways:

- **Filtered Data**: Only shows games involving Racing C team
- **Team Branding**: Title changed to "Racing C Basketball Statistics"  
- **Focused Content**: Removes general statistics not relevant to Racing C
- **Custom Styling**: Includes a prominent team overview section
- **Simplified Navigation**: Streamlined for Racing C specific content

## Implementation Details

The generator (`generate_racing_c_static.py`) works by:

1. Loading the full game data from `full-game-stats.csv`
2. Filtering to only games where Racing C is home or away team
3. Calculating Racing C specific statistics (wins, losses, averages)
4. Generating HTML pages using existing Flask templates
5. Creating custom navigation with Racing C branding
6. Outputting to the `racing-c-site/` directory

## Deployment

The generated static site can be deployed to:
- GitHub Pages
- Any static web hosting service
- CDN or cloud storage bucket configured for web hosting

The site contains only static HTML, CSS, and JavaScript files with no server-side dependencies.