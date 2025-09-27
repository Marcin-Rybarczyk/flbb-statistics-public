# Copilot Instructions for FLBB Statistics

This repository contains a Flask web application that analyzes and visualizes basketball statistics from the Luxembourg Basketball Federation (FLBB).

## Project Overview

This is a data analytics and visualization platform that:
- Scrapes basketball game data from Luxembourg Basketball Federation website
- Processes raw HTML into structured JSON data
- Generates comprehensive CSV statistics files  
- Provides a Flask web interface for data visualization
- Automatically uploads data to Google Drive via GitHub Actions
- Supports deployment to multiple hosting platforms (Render, Railway, GitHub Pages)

## Architecture

### Core Components

1. **Data Collection (`download-controller.ps1`)**
   - PowerShell script that scrapes game data from FLBB website
   - Downloads HTML files and creates JSON databases
   - Compresses data into ZIP archives for backup

2. **Data Processing (`extract-game.ps1`, `utils.py`)**
   - Transforms raw HTML into structured JSON records
   - Calculates statistics (standings, player performance, referee stats)
   - Generates the main `full-game-stats.csv` file

3. **Web Application (`app.py`, `templates/`)**
   - Flask-based web interface for data visualization
   - Interactive division standings and team performance stats
   - Player analysis, referee statistics, and game insights

4. **Google Drive Integration (`google_drive_helper.py`)**
   - Automated file uploads to Google Drive
   - GitHub Actions workflows for continuous data updates

5. **Deployment Tools (`deploy_flask.py`, `wsgi.py`)**
   - Multi-platform deployment assistant
   - Production-ready WSGI configuration

## Key Files and Directories

- `app.py` - Main Flask application with all routes and data visualization logic
- `utils.py` - Data processing utilities and statistical calculations  
- `full-game-stats.csv` - Primary data source (generated from JSON files)
- `requirements.txt` - Python dependencies (Flask, pandas, Google API client)
- `templates/` - Jinja2 HTML templates for the web interface
- `static_site/` - Generated static files for GitHub Pages deployment
- `.github/workflows/` - GitHub Actions for automated data processing and uploads
- `doc/` - Comprehensive documentation for setup and usage

## Development Guidelines

### Code Style
- Follow Python PEP 8 conventions
- Use descriptive function and variable names
- Add docstrings for complex functions
- Keep functions focused and modular

### Data Handling
- Primary data source is `full-game-stats.csv` 
- All statistics calculations are in `utils.py`
- Use pandas DataFrames for data manipulation
- Handle missing data gracefully with appropriate defaults

### Flask Application
- Routes are organized by functionality in `app.py`
- Use Jinja2 templates in `templates/` directory
- Static assets should go in `static/` (if created)
- Error handling should provide user-friendly messages

### Testing
- Use `test_local_flask.py` for local testing and validation
- Test data processing with `python3 test_local_flask.py --test-only`
- Production testing available with `--production` flag

## Common Tasks

### Adding New Statistics
1. Implement calculation function in `utils.py`
2. Add route in `app.py` if web interface needed
3. Create corresponding HTML template if applicable
4. Test with existing data using `test_local_flask.py`

### Modifying Data Processing
1. Update functions in `utils.py` 
2. Test changes don't break existing calculations
3. Verify CSV generation still works correctly
4. Run full test suite before deployment

### Deployment Changes
1. Update `deploy_flask.py` for new deployment options
2. Modify `wsgi.py` for production configuration changes
3. Update `requirements.txt` for new dependencies
4. Test locally before pushing changes

### Adding Documentation
- Use existing doc/ structure following established patterns
- Include code examples and clear setup instructions
- Update README files for significant changes

## Environment Setup

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python3 test_local_flask.py --test-only  

# Start development server
python3 app.py
# or 
python3 test_local_flask.py
```

### Production Deployment  
Use the deployment assistant:
```bash
python3 deploy_flask.py          # Interactive mode
python3 deploy_flask.py render   # Render.com
python3 deploy_flask.py railway  # Railway.app  
python3 deploy_flask.py github   # GitHub Pages
```

## Data Flow

1. **Collection**: PowerShell scripts scrape FLBB website → Raw HTML files
2. **Processing**: `extract-game.ps1` → JSON records → CSV via `utils.py`
3. **Automation**: GitHub Actions run data collection daily
4. **Storage**: Files uploaded to Google Drive automatically
5. **Visualization**: Flask app serves data via web interface

## Security Notes

- Google Drive credentials stored as GitHub Secrets
- Service account files cleaned up after each workflow run
- No sensitive data committed to repository
- Production deployments use environment variables

## Testing Strategy

- Local testing with `test_local_flask.py`
- Automated workflows test data processing
- Manual verification of web interface functionality
- Production testing before deployment

When helping with this codebase:
1. Understand the data flow from scraping to visualization
2. Test changes locally before suggesting modifications  
3. Consider impact on both data processing and web interface
4. Follow existing patterns for consistency
5. Prioritize data integrity and user experience