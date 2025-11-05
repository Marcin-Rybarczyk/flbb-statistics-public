# Version Tracking System

This document describes the version tracking and management system used in the FLBB Statistics application.

## 📋 Overview

The application uses a Git-integrated version tracking system that automatically manages version information and displays it throughout the application. The system is implemented in `src/version.py` and provides version details to all templates via Flask's context processor.

## 🔢 Version Information

### Version Components

The version system tracks four key pieces of information:

1. **Version Number** (`__version__`)
   - Format: Semantic versioning (e.g., "1.0.0")
   - Manually updated for releases
   - Follows MAJOR.MINOR.PATCH convention

2. **Release Date** (`__release_date__`)
   - Format: ISO date (YYYY-MM-DD)
   - Date of the version release
   - Manually set for each version

3. **Build Number** (`__build_number__`)
   - Sequential build identifier
   - Incremented for each build
   - Used for tracking deployments

4. **Last Modified Date**
   - Automatically extracted from Git commit history
   - Shows the date of the last Git commit
   - Falls back to release date if Git is unavailable

## 🛠️ Implementation

### File Structure

```python
# src/version.py

__version__ = "1.0.0"
__release_date__ = "2025-11-02"
__build_number__ = "1"

def get_last_modification_date():
    """
    Get the last modification date from Git commit history.
    Falls back to release date if Git is not available.
    """
    # Git integration code
    
def get_version_info():
    """
    Returns a dictionary with version information including last modification date
    """
    # Returns version dictionary
```

### Version Dictionary

The `get_version_info()` function returns:

```python
{
    'version': '1.0.0',
    'release_date': '2025-11-02',
    'build_number': '1',
    'last_modified': '2025-11-05',  # From Git
    'version_string': 'v1.0.0 (Last modified: 2025-11-05)'
}
```

## 🌐 Template Integration

### Context Processor

Version information is automatically available in all templates via Flask's context processor:

```python
# src/app.py

@app.context_processor
def inject_season_info():
    """Make season information available to all templates"""
    version_info = get_version_info()
    return {
        'version_info': version_info,
        # ... other context variables
    }
```

### Using in Templates

Access version information in any template:

```html
<!-- Display version in footer -->
<footer>
    <p>Version {{ version_info.version }}</p>
    <p>{{ version_info.version_string }}</p>
</footer>

<!-- Show build information -->
<div class="build-info">
    Build #{{ version_info.build_number }}
    Released: {{ version_info.release_date }}
</div>
```

## 📝 Version Update Process

### For Releases

1. **Update version.py:**
   ```python
   __version__ = "1.1.0"           # Increment version
   __release_date__ = "2025-11-15"  # Set release date
   __build_number__ = "2"           # Increment build
   ```

2. **Commit changes:**
   ```bash
   git add src/version.py
   git commit -m "Bump version to 1.1.0"
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push origin v1.1.0
   ```

3. **Deploy:**
   - The last modified date will automatically update from Git
   - No need to manually update `last_modified`

### Semantic Versioning Guidelines

Follow semantic versioning (semver) principles:

- **MAJOR** (1.x.x) - Breaking changes, incompatible API changes
- **MINOR** (x.1.x) - New features, backwards-compatible
- **PATCH** (x.x.1) - Bug fixes, backwards-compatible

**Examples:**
- `1.0.0` → `1.0.1` - Bug fix
- `1.0.1` → `1.1.0` - New feature (preferences page)
- `1.1.0` → `2.0.0` - Breaking change (complete redesign)

## 🔄 Git Integration

### Automatic Last Modified Date

The system automatically retrieves the last commit date from Git:

```python
def get_last_modification_date():
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cd', '--date=format:%Y-%m-%d'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return __release_date__  # Fallback
```

### Fallback Mechanism

If Git is unavailable (e.g., in certain deployment environments):
- System uses `__release_date__` as fallback
- No errors or crashes
- Graceful degradation

## 🚀 Deployment Considerations

### Production Environments

**With Git:**
- Last modified date updates automatically
- Shows actual last commit date
- Ideal for development and staging

**Without Git (e.g., static deploys):**
- Uses release date as fallback
- Still shows version information
- No degradation in functionality

### Environment-Specific Behavior

**Local Development:**
```
Version: 1.0.0
Last modified: 2025-11-05  (from Git)
Build: 1
```

**GitHub Pages (no Git):**
```
Version: 1.0.0
Last modified: 2025-11-02  (from release_date)
Build: 1
```

## 📊 Version Display Examples

### Footer Display
```html
<footer class="site-footer">
    <div class="container">
        <p>FLBB Statistics {{ version_info.version_string }}</p>
        <p>Build #{{ version_info.build_number }}</p>
    </div>
</footer>
```

### Admin Page Display
```html
<div class="version-info">
    <h3>System Information</h3>
    <table>
        <tr>
            <td>Version:</td>
            <td>{{ version_info.version }}</td>
        </tr>
        <tr>
            <td>Release Date:</td>
            <td>{{ version_info.release_date }}</td>
        </tr>
        <tr>
            <td>Build Number:</td>
            <td>{{ version_info.build_number }}</td>
        </tr>
        <tr>
            <td>Last Modified:</td>
            <td>{{ version_info.last_modified }}</td>
        </tr>
    </table>
</div>
```

## 🔒 Security Considerations

### Information Disclosure

Version information is publicly visible:
- **Safe to expose:** Version numbers, dates, build numbers
- **Not exposed:** Server paths, internal configurations, secrets
- **Best practice:** Generic version info helps users report bugs

### Version in API Responses

Consider adding version to API responses for debugging:

```python
@app.route('/api/version')
def api_version():
    return jsonify(get_version_info())
```

## 🧪 Testing

### Test Version Retrieval

```python
# tests/test_version.py

from src.version import get_version_info

def test_version_info():
    info = get_version_info()
    assert 'version' in info
    assert 'release_date' in info
    assert 'build_number' in info
    assert 'last_modified' in info
    assert 'version_string' in info

def test_version_format():
    info = get_version_info()
    # Check semantic version format
    assert len(info['version'].split('.')) == 3
```

## 💡 Best Practices

### Version Management

1. **Update version.py before releases**
   - Increment version number appropriately
   - Update release date to deployment date
   - Increment build number

2. **Tag releases in Git**
   ```bash
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin v1.0.0
   ```

3. **Document changes**
   - Keep a CHANGELOG.md file
   - List features, fixes, and breaking changes
   - Reference version numbers

4. **Consistent versioning**
   - Follow semantic versioning strictly
   - Communicate breaking changes clearly
   - Plan major versions carefully

### Display Recommendations

**Footer (all pages):**
- Short version string
- Unobtrusive placement

**Admin page:**
- Full version details
- All components visible

**About page (if exists):**
- Version history
- Release notes link

## 📚 Related Documentation

- [Main README](../README.md) - Project overview
- [Deployment Guide](README_DEPLOYMENT.md) - Deployment instructions
- [GitHub Actions Usage](GITHUB_ACTIONS_USAGE.md) - CI/CD workflows

---

**Version tracking helps maintain and debug the application effectively!** 🔢
