# Age and Sex Group Handling - Implementation Summary

## What Was Implemented

This PR successfully implements age and sex group handling for teams, allowing the system to automatically detect division types and add appropriate suffixes to team names.

## Problem Solved

**Issue**: Teams can compete in multiple divisions (Men's, Women's, Youth), but all teams shared the same name, making it difficult to distinguish them.

**Solution**: Automatic suffix system that adds context to team names based on their division:
- Men's (default): "Racing Luxembourg" → "Racing Luxembourg" (no change)
- Women's: "Racing Luxembourg" → "Racing Luxembourg (Women)"
- Youth U18: "Racing Luxembourg" → "Racing Luxembourg (U18)"

## Core Functions

### 1. `extract_age_sex_group_from_division(division_name)`
Parses division names to identify the age and sex group.

**Supports:**
- Men: M-, MEN, MESSIEURS
- Women: W-, WOMEN, DAMEN, DAMES
- Youth: U18, U16, U14, U12, etc.
- Categories: CADETS, MINIMES, JUNIORS, SENIORS, ESPOIRS

### 2. `get_team_name_with_group_suffix(team_name, division_name, include_default=False)`
Adds appropriate suffix to team name based on division.

**Behavior:**
- Default group (Adult Men): No suffix
- Women's divisions: "(Women)" suffix
- Youth divisions: "(U18)", "(U16)", etc.
- With `include_default=True`: Also shows "(Men)" for default group

## How to Use

### In Python Code
```python
from src.utils import get_team_name_with_group_suffix

# Example 1: Men's division (no suffix)
name = get_team_name_with_group_suffix("Racing Luxembourg", "M-Division 1:", False)
# Result: "Racing Luxembourg"

# Example 2: Women's division
name = get_team_name_with_group_suffix("Racing Luxembourg", "W-Division 1", False)
# Result: "Racing Luxembourg (Women)"

# Example 3: Youth division
name = get_team_name_with_group_suffix("Racing Luxembourg", "U18-Division", False)
# Result: "Racing Luxembourg (U18)"
```

### In Jinja Templates
```jinja2
{# Display team name with suffix #}
<h3>{{ get_team_name_with_group_suffix(team_name, division, false) }}</h3>

{# Example with real data #}
{% for team in teams %}
  <div class="team-card">
    {{ get_team_name_with_group_suffix(team.name, team.division, false) }}
  </div>
{% endfor %}
```

## Current Impact

### On Existing Data
✅ **No visual changes** - All current divisions are Men's divisions, which display without suffix (default behavior)

### Future Data
✅ **Automatic handling** - When Women's or Youth divisions are added, suffixes will appear automatically

## Files Modified

1. **src/utils.py** - Added 2 new utility functions
2. **src/app.py** - Imported and exposed functions to templates
3. **tests/test_age_sex_groups.py** - Comprehensive test suite (28 tests)
4. **docs/AGE_SEX_GROUP_HANDLING.md** - Complete documentation

## Testing

✅ All 28 unit tests passing  
✅ Flask application tests passing  
✅ Real data validation successful  
✅ Code review completed - all issues addressed  
✅ Security scan completed - 0 vulnerabilities  

## Key Features

- **Non-invasive**: Original data unchanged
- **Backward compatible**: Existing functionality preserved
- **Extensible**: Ready for new division types
- **Well-tested**: Comprehensive test coverage
- **Documented**: Complete usage guide
- **Secure**: Zero security vulnerabilities

## Future Enhancements

Possible future improvements:
- User preference to always show/hide suffixes
- Configurable suffix format (e.g., "(W)" vs "(Women)")
- Multi-language support (EN/FR/DE suffixes)
- Custom group mappings via configuration

## Documentation

Full documentation available in: `docs/AGE_SEX_GROUP_HANDLING.md`

## Migration Path

When new divisions are added (Women's, Youth):
1. ✅ No code changes needed - automatic detection
2. ✅ Use functions in templates where suffixes are desired
3. ✅ Control display via `include_default` parameter

## Questions?

See the full documentation in `docs/AGE_SEX_GROUP_HANDLING.md` for:
- Detailed API reference
- More code examples
- Supported patterns
- Integration guide
