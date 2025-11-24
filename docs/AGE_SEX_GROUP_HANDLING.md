# Age and Sex Group Handling

This document describes the age and sex group handling functionality added to the FLBB Statistics application.

## Overview

The age and sex group handling feature provides utilities to parse division names and automatically add appropriate suffixes to team names based on the division's age and sex group category. This helps distinguish teams when they compete in multiple divisions (Men's, Women's, Youth, etc.).

## Motivation

Most teams in the Luxembourg Basketball Federation have teams competing in different age and sex groups:
- **Men's divisions**: M-Division 1, M-ENOVOS LEAGUE, etc.
- **Women's divisions**: W-Division 1, Damen-Division, etc. (future)
- **Youth divisions**: U18, U16, U14, Cadets, Minimes, etc. (future)

Without clear indicators, it can be confusing to distinguish between "Racing Luxembourg" in the Men's division versus "Racing Luxembourg" in the U18 division.

## Design Principles

1. **Main group remains unchanged**: The default group (Adult Men) keeps team names without additional suffix
2. **Non-invasive**: Original team names in the database remain unchanged
3. **Extensible**: Easy to add support for new age/sex categories
4. **Backward compatible**: Works with existing data without breaking changes

## Functions

### `extract_age_sex_group_from_division(division_name)`

Extracts age and sex group information from a division name.

**Parameters:**
- `division_name` (str): The division name to analyze (e.g., "M-Division 1", "W-Nationale 1", "U18-Division")

**Returns:**
- `dict`: Dictionary with:
  - `sex` (str): 'M' for Men, 'W' for Women, or None
  - `age_group` (str): 'Adult', 'U18', 'U16', 'Cadets', etc.
  - `raw_group` (str): The original indicator extracted

**Examples:**
```python
from src.utils import extract_age_sex_group_from_division

# Men's division
result = extract_age_sex_group_from_division("M-Division 1:")
# Returns: {'sex': 'M', 'age_group': 'Adult', 'raw_group': 'M'}

# Women's division
result = extract_age_sex_group_from_division("W-Division 1")
# Returns: {'sex': 'W', 'age_group': 'Adult', 'raw_group': 'W'}

# Youth division
result = extract_age_sex_group_from_division("U18-Division 1")
# Returns: {'sex': None, 'age_group': 'U18', 'raw_group': 'U18'}
```

### `get_team_name_with_group_suffix(team_name, division_name, include_default=False)`

Adds age/sex group suffix to team name based on division.

**Parameters:**
- `team_name` (str): The base team name
- `division_name` (str): The division name to extract group from
- `include_default` (bool): If True, also add suffix for default group (Adult Men)

**Returns:**
- `str`: Team name with appropriate group suffix

**Examples:**
```python
from src.utils import get_team_name_with_group_suffix

# Men's division (default) - no suffix
result = get_team_name_with_group_suffix("Racing Luxembourg", "M-Division 1:", False)
# Returns: "Racing Luxembourg"

# Women's division - adds (Women)
result = get_team_name_with_group_suffix("Racing Luxembourg", "W-Division 1", False)
# Returns: "Racing Luxembourg (Women)"

# Youth division (unspecified sex) - adds age group only
result = get_team_name_with_group_suffix("Racing Luxembourg", "U18-Division 1", False)
# Returns: "Racing Luxembourg (U18)"

# Youth Boys division - adds age group and sex
result = get_team_name_with_group_suffix("Racing Luxembourg", "M-U18-Division 1", False)
# Returns: "Racing Luxembourg (U18 Boys)"

# Youth Girls division - adds age group and sex
result = get_team_name_with_group_suffix("Racing Luxembourg", "W-U16-Division 1", False)
# Returns: "Racing Luxembourg (U16 Girls)"

# Men's division with include_default=True
result = get_team_name_with_group_suffix("Racing Luxembourg", "M-Division 1:", True)
# Returns: "Racing Luxembourg (Men)"
```

## Supported Division Patterns

### Sex Groups
- **Men**: `M-`, `MEN`, `MESSIEURS`
- **Women**: `W-`, `WOMEN`, `DAMEN`, `DAMES`

### Age Groups
- **Youth by age**: `U18`, `U16`, `U14`, `U12`, etc.
- **Named categories**: `CADETS`, `MINIMES`, `JUNIORS`, `SENIORS`, `ESPOIRS`

### Combined Sex and Age Groups
When both sex and age indicators are present (e.g., "M-U18-Division", "W-U16-Division"), the suffix combines both:
- **Boys/Men Youth**: Shows age with "Boys" (e.g., "(U18 Boys)", "(U16 Boys)")
- **Girls/Women Youth**: Shows age with "Girls" (e.g., "(U18 Girls)", "(U16 Girls)")
- **Unspecified sex Youth**: Shows age only (e.g., "(U18)", "(U16)")

## Usage in Templates

The functions are available in all Jinja2 templates via the global context:

```jinja2
{# Display team name with group suffix #}
<h3>{{ get_team_name_with_group_suffix(team_name, division, false) }}</h3>

{# Extract group info for custom display #}
{% set group_info = extract_age_sex_group_from_division(division) %}
{% if group_info.age_group != 'Adult' %}
  <span class="age-badge">{{ group_info.age_group }}</span>
{% endif %}
```

## Usage in Python Code

```python
from src.utils import extract_age_sex_group_from_division, get_team_name_with_group_suffix

# Process team names in backend
def format_team_display(team_name, division):
    return get_team_name_with_group_suffix(team_name, division, include_default=False)

# Check if a division is for youth
def is_youth_division(division_name):
    group_info = extract_age_sex_group_from_division(division_name)
    return group_info['age_group'] != 'Adult'
```

## Current Data

As of the current season, all divisions in the database are Men's divisions (M-Division 1, M-ENOVOS LEAGUE, etc.). The feature is designed to be ready for when Women's and Youth divisions are added to the system.

## Testing

Comprehensive tests are available in `tests/test_age_sex_groups.py`:

```bash
# Run the age/sex group tests
python3 tests/test_age_sex_groups.py

# Tests cover:
# - All current division patterns (Men's)
# - Future division patterns (Women's, Youth)
# - Edge cases (None, empty strings)
# - Real data from CSV
```

## Migration Path

When new divisions are added:

1. **No code changes needed**: The functions automatically detect the group from division names
2. **Opt-in display**: Use `get_team_name_with_group_suffix()` where you want to show suffixes
3. **Gradual adoption**: Can be enabled incrementally in different parts of the app

## Future Enhancements

Potential future improvements:
- User preference to always show/hide group suffixes
- Abbreviation options (e.g., "(W)" instead of "(Women)")
- Language-specific suffixes (English/French/German)
- Configuration file for custom group mappings

## See Also

- Implementation: `src/utils.py` (lines ~3118-3230)
- Tests: `tests/test_age_sex_groups.py`
- Flask Integration: `src/app.py` (lines 14-17, 285-289)
