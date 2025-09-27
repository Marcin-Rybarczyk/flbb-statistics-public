# Team Logo Management System

This document explains how to manage team logos in the FLBB Statistics application.

## Overview

The application now includes a comprehensive team logo management system that provides logos for all teams in the Luxembourg Basketball Federation dataset. The system includes:

- **Automated logo download** from FLBB website
- **Fallback logo generation** when downloads fail
- **Utility functions** for logo management
- **Full team coverage** (10/10 teams)

## Files Structure

```
logos/                          # Logo storage directory
├── RAC.jpg                     # Original Racing logo
├── amicale-b.png              # Generated team logos (200x200px)
├── bbc-nitia-b.png
├── bc-mess-b.png
├── contern-c.png
├── grengewald-hostert-c.png
├── mamer-b.png
├── racing-c.png               # Converted from RAC.jpg
├── racing-d.png               # Converted from RAC.jpg
├── schieren-b.png
└── sparta-c.png

scripts/                       # Logo management scripts
├── download_team_logos.py     # Enhanced logo download from FLBB website  
├── test_logo_download.py      # Testing and debugging utility for logo downloads
├── create_team_logos.py       # Generate fallback logos locally
└── logo_utils.py              # Utility functions for logo management
```

## Scripts Usage

### 1. Download Team Logos (`download_team_logos.py`) - Enhanced

Attempts to download official team logos from the FLBB website using comprehensive search strategies.

```bash
python3 scripts/download_team_logos.py                    # Normal mode
python3 scripts/download_team_logos.py --verbose          # Detailed debug output
python3 scripts/download_team_logos.py --force            # Re-download existing logos
python3 scripts/download_team_logos.py --verbose --force  # Verbose + force mode
```

**Enhanced Features:**
- **Multiple URL Strategies**: Tests 10+ URL patterns per team (direct team pages, search pages, asset directories)
- **Advanced HTML Parsing**: Uses 8+ regex patterns to extract logos from web pages
- **Intelligent Logo Scoring**: Ranks found logos by relevance and quality indicators
- **Smart Search**: Searches category pages, team listings, and search results
- **Direct Asset Discovery**: Checks common logo directory paths
- **Enhanced Validation**: Validates image content, file sizes, and formats
- **Verbose Debug Mode**: Detailed logging for troubleshooting failed downloads
- **Force Re-download**: Option to re-download all logos even if they exist
- **Comprehensive Error Handling**: Graceful handling of network errors, timeouts, and invalid content
- **Respectful Request Patterns**: Configurable delays and proper HTTP headers

### 2. Create Team Logos (`create_team_logos.py`)

Generates professional-looking fallback logos when official logos are not available.

```bash
python3 scripts/create_team_logos.py
```

**Features:**
- Creates 200x200px PNG logos
- Uses team-specific color schemes
- Generates team abbreviations (e.g., "AB" for Amicale B)
- Includes full team name below abbreviation
- Converts existing JPG logos to standard PNG format
- Cleans up placeholder files

### 3. Test Logo Download (`test_logo_download.py`) - New

Testing and debugging utility for the logo download functionality.

```bash
# Test logo download for specific team
python3 scripts/test_logo_download.py --team "Racing C"

# Test logo extraction from specific URL  
python3 scripts/test_logo_download.py --url "https://example.com/team-page"

# List all potential URLs that would be tested for a team
python3 scripts/test_logo_download.py --list-urls "Amicale B"

# Run tests with less verbose output
python3 scripts/test_logo_download.py --team "Racing C" --quiet
```

**Testing Features:**
- **Single Team Testing**: Test logo discovery for specific team names
- **URL Pattern Analysis**: Test logo extraction from specific web pages
- **URL Generation**: Generate and display all potential URLs for a team
- **Debug Information**: Detailed analysis of HTML content and extraction patterns
- **Network Troubleshooting**: Helps diagnose connectivity and parsing issues

### 4. Logo Utilities (`logo_utils.py`)

Provides utility functions for working with team logos in the application.

```bash
# List all available logos
python3 scripts/logo_utils.py list

# Test logo coverage against team data
python3 scripts/logo_utils.py test

# Check logo for specific team
python3 scripts/logo_utils.py check "Racing C"
```

## Team Color Schemes

Each team has a unique color scheme used in generated logos:

| Team | Background Color | Text Color | Theme |
|------|------------------|------------|-------|
| Amicale B | Navy Blue | White | Professional |
| BBC Nitia B | Orange | White | Energetic |
| BC Mess B | Dark Red | White | Bold |
| Contern C | Green | White | Natural |
| Grengewald Hostert C | Midnight Blue | White | Elegant |
| Mamer B | Purple | White | Royal |
| Racing C | Crimson | White | Dynamic |
| Racing D | Fire Brick | White | Strong |
| Schieren B | Teal | White | Modern |
| Sparta C | Indigo | White | Classical |

## Logo Integration

### In Python Code

```python
from scripts.logo_utils import get_team_logo_path

# Get logo path for a team
team_name = "Racing C"
logo_path = get_team_logo_path(team_name)
if logo_path:
    print(f"Logo: {logo_path}")
```

### In Flask Templates

```html
<!-- Example: Display team logo -->
{% if team_name %}
    {% set logo_path = get_team_logo_path(team_name) %}
    {% if logo_path %}
        <img src="{{ url_for('static', filename=logo_path) }}" 
             alt="{{ team_name }} logo" 
             class="team-logo">
    {% endif %}
{% endif %}
```

### CSS for Logo Display

```css
.team-logo {
    width: 50px;
    height: 50px;
    object-fit: contain;
    border-radius: 4px;
}

.team-logo-large {
    width: 100px;
    height: 100px;
    object-fit: contain;
}
```

## Maintenance

### Adding New Teams

When new teams appear in the dataset:

1. Run the logo download script to try fetching official logos:
   ```bash
   python3 scripts/download_team_logos.py
   ```

2. If download fails, generate fallback logos:
   ```bash
   python3 scripts/create_team_logos.py
   ```

3. Verify coverage:
   ```bash
   python3 scripts/logo_utils.py test
   ```

### Updating Existing Logos

1. Replace the logo file in the `logos/` directory
2. Ensure the filename follows the pattern: `{normalized-team-name}.png`
3. Test the change:
   ```bash
   python3 scripts/logo_utils.py check "Team Name"
   ```

### Logo File Naming Convention

- Team names are normalized: lowercase, spaces replaced with hyphens, special characters removed
- Examples:
  - "Racing C" → `racing-c.png`
  - "Grengewald Hostert C" → `grengewald-hostert-c.png`
  - "BBC Nitia B" → `bbc-nitia-b.png`

## Enhanced Logo Discovery Process

The enhanced `download_team_logos.py` script uses a sophisticated multi-strategy approach:

### Discovery Strategies

1. **Direct Team Page Search**
   - Tests 10+ URL patterns per team (e.g., `/equipe/`, `/club/`, `/teams/`)
   - Follows redirects to find correct team pages
   - Analyzes HTML content with 8+ logo extraction patterns

2. **Search and Category Pages**
   - Searches team listings and category pages
   - Uses search functionality (`/search?q=`, `/recherche?q=`)
   - Extracts logos from team cards and listings

3. **Direct Asset Discovery**
   - Checks common logo directory paths (`/logos/`, `/assets/logos/`)
   - Tests multiple image formats (PNG, JPG, GIF, SVG)
   - Uses HTTP HEAD requests for efficient asset checking

### Logo Scoring System

Found logos are scored based on:
- **Team name match** in URL (+50 points)
- **"logo" keyword** in path (+30 points)
- **Team/club keywords** in path (+20 points)
- **Preferred formats** (PNG +15, SVG +10, JPG +5)
- **Logo directory** location (+25 points)
- **File size heuristics** (avoid thumbnails and banners)

### Validation and Quality Control

- **Content Type Validation**: Checks HTTP headers for image content
- **File Size Limits**: 1KB minimum, 10MB maximum
- **Magic Byte Verification**: Validates actual image file formats
- **Error Recovery**: Graceful handling of network issues and timeouts

## Troubleshooting

### Common Issues

1. **Missing PIL/Pillow dependency**
   ```bash
   pip install pillow
   ```

2. **Logo not found for team**
   - Check if team name is in the CSV data
   - Verify filename matches normalized team name
   - Run logo creation script to generate missing logos

3. **Network issues with download script**
   - Check internet connection
   - Verify FLBB website is accessible  
   - Use `--verbose` flag for detailed debugging
   - Test specific teams with `test_logo_download.py`
   - Use fallback logo creation script

### Testing Coverage

Always verify logo coverage after making changes:

```bash
python3 scripts/logo_utils.py test
```

Expected output should show 100% coverage:
```
Teams with logos: 10/10
Coverage: 100.0%
✓ All teams have logos!
```

## Technical Implementation

### Logo Generation Process

1. **Team Name Normalization**: Convert team names to filename-safe format
2. **Color Assignment**: Use predefined color schemes for visual consistency
3. **Logo Creation**: Generate PNG images with team abbreviations and full names
4. **Format Standardization**: All logos are 200x200px PNG format
5. **Quality Control**: Verify all teams have corresponding logos

### File Management

- All logos stored in `logos/` directory
- Consistent PNG format (except original RAC.jpg)
- Proper file permissions for web serving
- Cleanup of temporary/placeholder files

This system ensures every team in the FLBB dataset has a professional logo for use in the web application.