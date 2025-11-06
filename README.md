# FLBB Statistics

A comprehensive Flask-based web application for analyzing and visualizing basketball statistics from the Luxembourg Basketball Federation (FLBB). The application automatically scrapes game data, processes it into meaningful insights, and presents interactive visualizations through a modern web interface.

## 🏀 Overview

This project provides in-depth analysis and visualization of basketball statistics from the Luxembourg Basketball Federation. It automatically scrapes game data, processes it into meaningful insights, and presents interactive visualizations through a modern web interface.

**Live Demo**: [Visit the deployed application](http://flbb.ryba.usermd.net)
**Test Environment**: [Visit the deployed application](https://test.flbb-public.ryba.usermd.net)


## ✨ Key Features

### 🎨 User Experience
- **6 Custom Themes** - Choose from default, ocean, sunset, forest, minimal, and cherry themes
- **User Preferences** - Save your preferred division, team, and theme settings
- **Responsive Design** - Optimized for desktop, tablet, and mobile devices
- **Interactive Hover Tooltips** - Quick stats preview via API endpoints
- **Team Logos** - Professional branding with 90+ team logos

### 📊 Analytics & Insights
- **21+ Page Routes** - Comprehensive coverage of teams, players, referees, and games
- **48+ Statistical Functions** - Advanced analytics and data processing
- **Detailed Player Profiles** - Individual performance tracking with quarter analysis
- **Team Detail Pages** - Complete team history, rosters, and upcoming fixtures
- **Referee Performance Index** - Comprehensive referee evaluation metrics
- **Game Hotness Rating** - Excitement factor calculation for every game
- **Starting Five Predictions** - AI-powered lineup predictions for upcoming games

### 🤖 Automation & Integration
- **Automated Data Collection** - Daily scraping from FLBB website via PowerShell
- **Google Drive Integration** - Automatic backup and file management
- **GitHub Actions Workflows** - 5+ automated workflows for deployment and data processing
- **Season Archive System** - Import and manage historical season data
- **Version Tracking** - Automated version management with Git integration

### 🚀 Deployment Ready
- **Multi-Platform Support** - Deploy to Render.com, Railway.app, GitHub Pages, or MyDevil.net
- **Production WSGI** - Ready for production with Gunicorn
- **Environment Configuration** - Flexible configuration via environment variables
- **Static Site Generation** - Create static versions for GitHub Pages deployment

## 📁 Project Structure

```
flbb-statistics/
├── 📂 src/                          # Main application source code
│   ├── app.py                       # Flask web application with 21+ routes
│   ├── utils.py                     # Data processing and statistics utilities (48+ functions)
│   ├── wsgi.py                      # Production WSGI configuration
│   ├── version.py                   # Version tracking and management
│   └── google_drive_helper.py       # Google Drive integration
├── 📂 scripts/                      # Data collection and processing scripts
│   ├── download-controller.ps1      # Main data collection script (PowerShell)
│   ├── extract-game.ps1             # Data extraction and JSON conversion (PowerShell)
│   ├── post_process.py              # Post-processing automation (Python)
│   ├── check_version_api.py         # API version checking utility
│   ├── create_team_logos.py         # Team logo creation utility
│   ├── download_team_logos.py       # Team logo download automation
│   ├── logo_utils.py                # Logo processing utilities
│   ├── config.json                  # Main configuration file
│   ├── player-map.json              # Player mapping data
│   └── event-action-patterns.json   # Game event patterns
├── 📂 deployment/                   # Deployment tools and configuration
│   ├── deploy_flask.py              # Multi-platform deployment assistant
│   ├── generate_static.py           # Static site generator for GitHub Pages
│   ├── generate_racing_c_static.py  # Racing C team specific static generator
│   └── requirements.txt             # Python dependencies for deployment
├── 📂 data/                         # Data files and configuration
│   ├── full-game-stats.csv          # Main statistics data source
│   ├── gamesDB.json                 # Game database with fixtures
│   ├── players-database.csv         # Comprehensive player database
│   └── config.json                  # Application configuration (legacy)
├── 📂 docs/                         # Comprehensive documentation
│   ├── README.md                    # Documentation overview
│   ├── README_DEPLOYMENT.md         # Complete deployment instructions
│   ├── GOOGLE_DRIVE_SECRETS_SETUP.md # Google Drive API setup guide
│   ├── GITHUB_ACTIONS_USAGE.md      # Automation workflows documentation
│   ├── CSV_GENERATION_WORKFLOW.md   # Data processing pipeline guide
│   ├── IMPLEMENTATION_SUMMARY.md    # Technical implementation details
│   ├── TEAM_LOGOS.md                # Team logo management guide
│   ├── PLAYER_DATABASE.md           # Player database documentation
│   ├── LOGO_ENHANCEMENT.md          # Logo enhancement techniques
│   └── RACING_C_README.md           # Racing C team specific documentation
├── 📂 tests/                        # Testing and validation
│   ├── test_local_flask.py          # Local development and testing script
│   ├── test_google_drive.py         # Google Drive integration tests
│   ├── test_player_database.py      # Player database tests
│   ├── test_team_detail_scores.py   # Team detail score validation
│   ├── test_hotness.py              # Game hotness calculation tests
│   └── analyze_hotness.py           # Hotness analysis utilities
├── 📂 templates/                    # HTML templates for web interface
│   ├── base.html                    # Base template layout (62KB)
│   ├── index.html                   # Home page template
│   ├── standings.html               # Standings page
│   ├── statistics.html              # Main statistics overview
│   ├── team_stats.html              # Team statistics page
│   ├── team_detail.html             # Team detail page (32KB)
│   ├── player_stats.html            # Player statistics page (47KB)
│   ├── player_detail.html           # Player detail page (31KB)
│   ├── referee_stats.html           # Referee statistics page
│   ├── referee_detail.html          # Referee detail page
│   ├── referee_performance_index.html # Referee performance index
│   ├── deeper_analysis.html         # Advanced analytics page
│   ├── fixtures.html                # Fixtures and schedule page (27KB)
│   ├── game_detail.html             # Game detail page (29KB)
│   ├── game_details.html            # Game search page
│   ├── preferences.html             # User preferences page
│   └── admin.html                   # Administrative interface (15KB)
├── 📂 static_site/                  # Generated static files for GitHub Pages
├── 📂 logos/                        # Team logos and branding assets (90+ team logos)
├── 📂 .github/                      # GitHub configuration and workflows
│   ├── copilot-instructions.md      # GitHub Copilot instructions
│   └── workflows/                   # GitHub Actions automation
│       ├── google-drive-upload.yml  # Automated Google Drive uploads
│       ├── google-drive-list.yml    # Drive file listing workflow
│       ├── upload-to-gdrive.yml     # Legacy upload workflow
│       ├── deploy-to-prod.yml       # Production deployment
│       └── deploy-to-test.yml       # Test deployment
├── wsgi.py                          # Root-level WSGI entry point for deployment
├── passenger_wsgi.py                # MyDevil.net WSGI configuration
├── prepare_mydevil_setup.py         # MyDevil.net deployment preparation script
├── structure.py                     # Project structure visualization utility
├── requirements.txt                 # Python dependencies (main)
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore configuration
└── _config.yml                      # Jekyll configuration for GitHub Pages
```

## 🚀 Quick Start

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Marcin-Rybarczyk/flbb-statistics-public.git
   cd flbb-statistics-public
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python3 tests/test_local_flask.py
   ```

4. **Access the web interface:**
   - Local: http://localhost:5000
   - Network: http://127.0.0.1:5000

### Testing Only
```bash
python3 tests/test_local_flask.py --test-only
```

## 🌐 Deployment Options

### Quick Deployment
Use the built-in deployment assistant:
```bash
python3 deployment/deploy_flask.py              # Interactive guided deployment
python3 deployment/deploy_flask.py render      # Deploy to Render.com
python3 deployment/deploy_flask.py railway     # Deploy to Railway.app  
python3 deployment/deploy_flask.py github      # Generate static site for GitHub Pages
```

### Platform-Specific Instructions
- **[MyDevil.net](docs/README_DEPLOYMENT.md#mydevil-net)** - Polish hosting with Python support
  - **[Enable WWW Statistics](docs/MYDEVIL_STATISTICS.md)** - Guide for enabling visitor statistics in MyDevil panel

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:

### Core Documentation
- **[Documentation Overview](docs/README.md)** - Complete documentation index
- **[Deployment Guide](docs/README_DEPLOYMENT.md)** - Complete deployment instructions for multiple platforms
- **[MyDevil Statistics Setup](docs/MYDEVIL_STATISTICS.md)** - Enable visitor statistics for MyDevil.net hosting
- **[User Features Guide](docs/USER_FEATURES.md)** - Themes, preferences, and personalization

### Technical Documentation
- **[API Endpoints](docs/API_ENDPOINTS.md)** - REST API documentation for hover stats
- **[Version Tracking](docs/VERSION_TRACKING.md)** - Version management system
- **[CSV Generation Workflow](docs/CSV_GENERATION_WORKFLOW.md)** - Data processing pipeline
- **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)** - Technical implementation details

### Integration & Setup
- **[Google Drive Setup](docs/GOOGLE_DRIVE_SECRETS_SETUP.md)** - API configuration guide
- **[GitHub Actions Usage](docs/GITHUB_ACTIONS_USAGE.md)** - Automation workflows
- **[MongoDB Integration](docs/MONGODB_INTEGRATION.md)** - Store JSON data in MongoDB

### Asset Management
- **[Team Logos Guide](docs/TEAM_LOGOS.md)** - Team logo management and integration
- **[Player Database](docs/PLAYER_DATABASE.md)** - Player data structure and usage
- **[Logo Enhancement](docs/LOGO_ENHANCEMENT.md)** - Logo enhancement techniques

### Team-Specific
- **[Racing C Documentation](docs/RACING_C_README.md)** - Racing C team specific documentation

## 🚦 Usage

### Web Interface
The Flask application provides comprehensive analytical views:

#### Main Pages
- **Home Page (/)** - Division standings with filtering options and season overview
- **Standings (/standings)** - Dedicated standings page with advanced filtering
- **Statistics (/statistics)** - Comprehensive statistics overview page
- **Team Stats (/team-stats)** - Team performance comparison and metrics
- **Team Detail (/team-detail)** - In-depth individual team analysis with:
  - Complete game history and results
  - Player roster with statistics
  - Upcoming fixtures with predictions
  - Team performance trends
- **Player Stats (/player-stats)** - Player rankings and performance analysis
- **Player Detail (/player-detail)** - Individual player profiles with:
  - Game-by-game performance history
  - Season statistics and averages
  - Quarter-by-quarter analysis
  - Team contribution metrics

#### Advanced Analytics
- **Deeper Analysis (/deeper-analysis)** - Advanced game insights including:
  - Biggest wins and leads
  - Most tie scores and lead changes
  - Game "hotness" ratings
  - Player impact analysis
- **Referee Stats (/referee-stats)** - Referee statistics and analysis
- **Referee Detail (/referee-detail)** - Individual referee profiles
- **Referee Performance Index (/referee-performance-index)** - Comprehensive referee performance metrics
- **Fixtures (/fixtures)** - Complete fixture schedule with:
  - Upcoming games matrix
  - Team matchup predictions
  - Historical head-to-head records

#### Game Details
- **Game Detail (/game-detail/<game_id>)** - Individual game analysis with:
  - Play-by-play timeline
  - Score evolution charts
  - Player performance breakdown
  - Game statistics and highlights
- **Game Details Search (/game-details)** - Search and filter games

#### User Features
- **Preferences (/preferences)** - Personalize your experience with:
  - Theme selection (6 themes: default, ocean, sunset, forest, minimal, cherry)
  - Preferred division and team settings
  - Custom dashboard configuration
- **Admin (/admin)** - Administrative tools for:
  - Season data import
  - Archive management
  - System configuration

#### API Endpoints
- **/api/hover/player/<player_name>** - Get player hover statistics
- **/api/hover/team/<team_name>** - Get team hover statistics
- **/api/hover/referee/<referee_name>** - Get referee hover statistics
- **/api/hover/game/<game_id>** - Get game hover statistics

### Data Processing
The application automatically processes basketball data through:
1. **Data Collection** - PowerShell scripts scrape FLBB website
2. **Data Processing** - Raw HTML converted to structured JSON
3. **CSV Generation** - Statistics calculated and exported  
4. **Visualization** - Flask app presents interactive charts and tables

## 🔧 Configuration

### Application Configuration (`scripts/config.json`)
```json
{
  "eventName": "FLBB Basketball Season 2025-2026",
  "seasonId": "2025-2026",
  "dataSource": {
    "baseUrl": "https://www.luxembourg.basketball"
  },
  "processing": {
    "divisionsIncluded": ["Division 1 Hommes", "Division 2 Hommes", ...],
    "parallelDownloads": 10
  },
  "website": {
    "title": "FLBB Basketball Statistics",
    "features": {
      "showStandings": true,
      "showTopPlayers": true,
      "showPlayerStatistics": true
    }
  }
}
```

### Environment Variables (Production)
- `SECRET_KEY` - Flask secret key for sessions (auto-generated in development)
- `FLASK_ENV` - Set to `production` for production deployments
- `DEBUG` - Set to `False` for production
- `GOOGLE_DRIVE_CREDENTIALS` - Google API service account JSON
- `GOOGLE_DRIVE_FOLDER_ID` - Target folder for file uploads

### Version Configuration (`src/version.py`)
The application tracks version information automatically:
- `__version__` - Current version (e.g., "1.0.0")
- `__release_date__` - Release date
- `__build_number__` - Build number
- Automatic Git integration for last modification date

### GitHub Secrets (for automation)
- `GOOGLE_DRIVE_CREDENTIALS` - Service account credentials for API access
- `GOOGLE_DRIVE_FOLDER_ID` - Google Drive folder for automated uploads

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Test your changes locally with `python3 tests/test_local_flask.py --test-only`
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📊 Data Sources

Data is collected from the [Luxembourg Basketball Federation](https://www.luxembourg.basketball/) website:
- **Game Results** - Complete game results with play-by-play data
- **Player Statistics** - Individual player performance metrics across all games
- **Division Standings** - Team rankings and records for all divisions
- **Referee Assignments** - Referee assignments and foul statistics
- **Game Schedules** - Upcoming fixtures and game schedules
- **Team Rosters** - Player rosters and team compositions

The data is processed through a multi-stage pipeline:
1. **Scraping** - PowerShell scripts download HTML data from FLBB website
2. **Extraction** - Game data extracted from HTML and stored as JSON
3. **Processing** - Python utilities calculate statistics and generate CSV
4. **Storage** - Data stored locally and backed up to Google Drive
5. **Visualization** - Flask application renders interactive web interface

## 🛠️ Technologies

### Backend
- **Python 3.11+** - Core application language
- **Flask 3.1+** - Web framework
- **Pandas** - Data processing and analysis
- **Gunicorn** - WSGI HTTP server for production

### Data Collection
- **PowerShell** - Web scraping scripts
- **HTML Parsing** - Data extraction from FLBB website
- **JSON** - Structured data storage

### Frontend
- **Jinja2** - HTML templating
- **CSS** - Custom styling with 6 theme options
- **JavaScript** - Interactive elements and hover tooltips

### Integration & Deployment
- **Google Drive API** - File backup and storage
- **GitHub Actions** - CI/CD automation
- **Git** - Version control and tracking
- **Multiple Hosting Platforms** - Render, Railway, GitHub Pages, MyDevil

### Testing
- **Custom Test Suite** - Flask application testing
- **Validation Scripts** - Data integrity checks
- **Hot-reload Development** - Rapid development workflow

## 🛡️ Security

- **Environment Variables** - Sensitive configuration via environment variables
- **Service Account Credentials** - Securely handled through GitHub Secrets
- **No Hardcoded Secrets** - No sensitive data committed to repository
- **Automated Cleanup** - Temporary credential files automatically removed
- **Production-Ready** - Separate development and production configurations
- **Session Management** - Secure Flask sessions with secret key
- **Input Validation** - Data validation and sanitization

## 🎯 Roadmap

### Completed Features ✅
- [x] Team detail pages with comprehensive analytics
- [x] Player detail pages with game-by-game performance
- [x] Referee performance index and detailed statistics
- [x] Game detail pages with play-by-play timeline
- [x] User preferences and theme customization (6 themes)
- [x] Admin interface for season data management
- [x] API endpoints for hover statistics
- [x] Starting five predictions for upcoming games
- [x] Game hotness rating system
- [x] Automated Google Drive backups
- [x] Multi-platform deployment support
- [x] Version tracking system

### Planned Enhancements 🚧
- [ ] Advanced player comparison tools with side-by-side stats
- [ ] Historical trend analysis across multiple seasons
- [ ] Real-time game tracking during live games
- [ ] RESTful API endpoints for external data access
- [ ] Enhanced data visualizations with interactive charts
- [ ] Mobile app for iOS and Android
- [ ] Email notifications for favorite teams
- [ ] Fantasy basketball league integration
- [ ] Social sharing features
- [ ] Export reports as PDF

## 📞 Support

For questions, issues, or contributions:
1. Check the [documentation](docs/) for detailed guides
2. Review existing [GitHub Issues](../../issues)
3. Create a new issue with detailed information
4. Refer to deployment guides for hosting questions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Ready to explore Luxembourg basketball statistics?** 🏀  
Get started with `python3 tests/test_local_flask.py` and visit `http://localhost:5000`!
