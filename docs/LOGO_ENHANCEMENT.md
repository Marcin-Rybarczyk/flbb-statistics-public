# Logo Download Enhancement

This document describes the enhancement made to the logo download system to support the FLBB theme directory URL pattern.

## Issue Addressed

The issue requested adding support for downloading logos from:
```
https://www.luxembourg.basketball/layout/themes/flbb/images/Logos/BAS.jpg
```

## Enhancement Implementation

### 1. Added FLBB Theme Directory Support

The script now tries the specific URL pattern mentioned in the issue:
- `/layout/themes/flbb/images/Logos/{TEAM_CODE}.jpg`
- `/layout/themes/flbb/images/Logos/{TEAM_CODE}.png`
- `/layout/themes/flbb/images/logos/{TEAM_CODE}.jpg`
- `/layout/themes/flbb/images/logos/{TEAM_CODE}.png`

### 2. Enhanced Team Code Generation

Created `generate_team_codes()` function that generates multiple possible team codes:

**Example for "Racing C":**
- R (first significant letter)
- RC (first letter + team level)
- RACINGC (full name + level)
- RAC (from mapping)
- RACING (from mapping)

**Example for "BBC Nitia B":**
- BN (first letters of significant words)
- BNB (all first letters)
- BBCB (first word + level)
- BBC (from mapping)

### 3. Multiple Code Strategies

1. **First letters of significant words** (ignoring A, B, C, D team levels)
2. **All first letters** including team levels
3. **First word + level combinations**
4. **First 3 letters** of primary word
5. **Common basketball abbreviations** (manually mapped)

### 4. Backward Compatibility

- All existing URL patterns are maintained
- Existing functionality is unchanged
- Script arguments (`--verbose`, `--force`) work as before
- Existing logos are preserved unless `--force` is used

## Usage

```bash
# Normal usage - skips existing logos
python3 scripts/download_team_logos.py

# Verbose mode - shows all generated codes and URL attempts
python3 scripts/download_team_logos.py --verbose

# Force re-download - removes existing logos first
python3 scripts/download_team_logos.py --force

# Test enhanced patterns
python3 scripts/test_enhanced_logo_patterns.py
```

## URL Patterns Attempted (Example for "Racing C")

The enhanced script now tries these URLs in order:

### FLBB Theme Directory (NEW):
1. `https://www.luxembourg.basketball/layout/themes/flbb/images/Logos/R.jpg`
2. `https://www.luxembourg.basketball/layout/themes/flbb/images/Logos/RC.jpg`  
3. `https://www.luxembourg.basketball/layout/themes/flbb/images/Logos/RAC.jpg`
4. `https://www.luxembourg.basketball/layout/themes/flbb/images/Logos/RACING.jpg`

### Standard Patterns (EXISTING):
5. `https://www.luxembourg.basketball/assets/logos/racing-c.png`
6. `https://www.luxembourg.basketball/logos/racing-c.jpg`
7. Team page extraction patterns...

## Files Modified

1. **scripts/download_team_logos.py** - Main enhancement
   - Added `generate_team_codes()` function
   - Enhanced asset patterns to include FLBB theme directory
   - Improved documentation

2. **scripts/test_enhanced_logo_patterns.py** - New test script
   - Demonstrates enhanced functionality
   - Shows generated codes for all teams
   - Validates URL pattern generation

## Technical Details

- Team codes are generated in order of likelihood
- Multiple codes per team increase success rate
- HEAD requests used for efficient URL checking
- Comprehensive error handling maintained
- Request delays preserved for respectful scraping

## Integration

The enhanced logo downloader integrates seamlessly with:
- Flask web application (`src/app.py`)
- Logo utility functions (`scripts/logo_utils.py`) 
- Existing logo management workflow
- GitHub Actions automation