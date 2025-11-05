# FLBB Statistics Documentation

A comprehensive data analytics and visualization platform for Luxembourg Basketball Federation (FLBB) statistics.

![Basketball Statistics Dashboard](https://img.shields.io/badge/Flask-Web%20App-blue?logo=flask) ![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python) ![Data Analysis](https://img.shields.io/badge/Data-Analytics-orange) ![Deployment](https://img.shields.io/badge/Deploy-Ready-success)

## 🏀 Overview

This Flask-based web application provides in-depth analysis and visualization of basketball statistics from the Luxembourg Basketball Federation. It automatically scrapes game data, processes it into meaningful insights, and presents interactive visualizations through a modern web interface.

**Live Demo**: [Visit the deployed application](https://marcin-rybarczyk.github.io/flbb-statistics-public)

## 🚀 Features

### 📊 Statistical Analysis
- **Division Standings** - Interactive league tables with team performance metrics
- **Player Statistics** - Top scorers, shooting efficiency, and performance analysis
- **Team Performance** - Win/loss records, scoring trends, and comparative analysis
- **Game Insights** - Highest scoring games, biggest wins, and lead changes
- **Referee Analysis** - Foul statistics, performance index, and game impact analysis
- **Detail Pages** - Individual pages for teams, players, referees, and games

### 🎨 User Experience Features
- **6 Custom Themes** - default, ocean, sunset, forest, minimal, cherry
- **User Preferences** - Save preferred division, team, and theme
- **Interactive Tooltips** - Quick stats via hover API endpoints
- **Team Logos** - 90+ professional team logos
- **Responsive Design** - Optimized for all devices

### 🤖 Automated Data Pipeline
- **Daily Data Collection** - Automated scraping from FLBB website via PowerShell
- **Automatic Processing** - HTML to JSON to CSV conversion
- **CSV Generation** - Comprehensive statistics generation
- **Google Drive Integration** - Automated backups
- **GitHub Actions Workflows** - 5+ workflows for CI/CD

### 🌐 Multi-Platform Deployment
- **Local Development** - Full-featured development environment
- **Render.com** - Recommended cloud hosting platform
- **Railway.app** - Modern deployment with generous free tier
- **GitHub Pages** - Static version for basic hosting
- **MyDevil.net** - Polish hosting with Python support

## 🛠️ Quick Start

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Marcin-Rybarczyk/flbb-statistics-public.git
   cd flbb-statistics-public
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run tests:**
   ```bash
   python3 tests/test_local_flask.py --test-only
   ```

4. **Start the application:**
   ```bash
   # Development server
   python3 tests/test_local_flask.py
   
   # Production-like testing
   python3 tests/test_local_flask.py --production
   ```

5. **Access the web interface:**
   Open your browser to `http://localhost:5000`

## 📁 Project Structure

```
flbb-statistics/
├── 📂 src/                          # Main application source code
│   ├── app.py                       # Flask web application (21+ routes)
│   ├── utils.py                     # Data processing (48+ functions)
│   ├── wsgi.py                      # Production WSGI configuration
│   ├── version.py                   # Version tracking
│   └── google_drive_helper.py       # Google Drive integration
├── 📂 scripts/                      # Data collection scripts
│   ├── download-controller.ps1      # Data collection (PowerShell)
│   ├── extract-game.ps1             # Data extraction (PowerShell)
│   ├── post_process.py              # Post-processing automation
│   ├── create_team_logos.py         # Logo creation utility
│   ├── download_team_logos.py       # Logo download automation
│   └── config.json                  # Main configuration
├── 📂 deployment/                   # Deployment tools
│   ├── deploy_flask.py              # Multi-platform deployment
│   ├── generate_static.py           # Static site generator
│   └── generate_racing_c_static.py  # Team-specific generator
├── 📂 data/                         # Data files
│   ├── full-game-stats.csv          # Main statistics data
│   ├── gamesDB.json                 # Game database
│   └── players-database.csv         # Player database
├── 📂 docs/                         # Documentation
│   ├── README.md                    # This file
│   ├── README_DEPLOYMENT.md         # Deployment guide
│   ├── MYDEVIL_STATISTICS.md        # MyDevil statistics setup
│   ├── GOOGLE_DRIVE_SECRETS_SETUP.md
│   ├── GITHUB_ACTIONS_USAGE.md
│   ├── CSV_GENERATION_WORKFLOW.md
│   ├── TEAM_LOGOS.md
│   ├── PLAYER_DATABASE.md
│   └── LOGO_ENHANCEMENT.md
├── 📂 tests/                        # Testing utilities
│   ├── test_local_flask.py          # Main test script
│   ├── test_google_drive.py
│   ├── test_player_database.py
│   └── test_hotness.py
├── 📂 templates/                    # HTML templates (17 files)
│   ├── base.html                    # Base layout (62KB)
│   ├── team_detail.html             # Team details (32KB)
│   ├── player_stats.html            # Player stats (47KB)
│   └── ... (14 more templates)
├── 📂 logos/                        # Team logos (90+ logos)
└── 📂 .github/workflows/            # GitHub Actions (5 workflows)
```

## 🚦 Usage

### Web Interface
The Flask application provides comprehensive analytical views:

#### Main Pages
- **Home Page (/)** - Division standings with season overview
- **Statistics (/statistics)** - Comprehensive statistics overview
- **Team Stats (/team-stats)** - Team performance comparison
- **Team Detail (/team-detail)** - Individual team analysis with roster and fixtures
- **Player Stats (/player-stats)** - Player rankings and performance
- **Player Detail (/player-detail)** - Individual player profiles
- **Referee Stats (/referee-stats)** - Referee statistics overview
- **Referee Detail (/referee-detail)** - Individual referee profiles
- **Referee Performance Index (/referee-performance-index)** - Performance metrics
- **Deeper Analysis (/deeper-analysis)** - Advanced game insights
- **Fixtures (/fixtures)** - Complete fixture schedule with predictions
- **Game Detail (/game-detail/<game_id>)** - Individual game analysis
- **Preferences (/preferences)** - User customization (themes, favorites)
- **Admin (/admin)** - Season data management

#### API Endpoints
- `/api/hover/player/<player_name>` - Player hover statistics
- `/api/hover/team/<team_name>` - Team hover statistics
- `/api/hover/referee/<referee_name>` - Referee hover statistics
- `/api/hover/game/<game_id>` - Game hover statistics

### Data Processing
The application automatically processes basketball data through:
1. **Data Collection** - PowerShell scripts scrape FLBB website
2. **Data Processing** - Raw HTML converted to structured JSON
3. **CSV Generation** - Statistics calculated and exported
4. **Visualization** - Flask app presents interactive charts and tables

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
- **[Render.com](README_DEPLOYMENT.md#render-com)** - Recommended for full Flask deployment
- **[Railway.app](README_DEPLOYMENT.md#railway-app)** - Modern platform with generous free tier
- **[GitHub Pages](README_DEPLOYMENT.md#github-pages)** - Static version hosting
- **[MyDevil.net](README_DEPLOYMENT.md#mydevil-net)** - Polish hosting with Python support
  - **[Enable WWW Statistics](MYDEVIL_STATISTICS.md)** - Visitor statistics tracking setup

## 📖 Documentation

Comprehensive documentation is available in this directory:

### Core Documentation
- **[Deployment Guide](README_DEPLOYMENT.md)** - Complete deployment instructions for all platforms
- **[MyDevil Statistics Setup](MYDEVIL_STATISTICS.md)** - Enable visitor statistics for MyDevil.net hosting
- **[User Features Guide](USER_FEATURES.md)** - Themes, preferences, and personalization

### Technical Documentation
- **[API Endpoints](API_ENDPOINTS.md)** - REST API documentation for hover stats
- **[Version Tracking](VERSION_TRACKING.md)** - Version management system
- **[CSV Generation Workflow](CSV_GENERATION_WORKFLOW.md)** - Data processing pipeline
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Technical implementation details

### Integration & Setup
- **[Google Drive Setup](GOOGLE_DRIVE_SECRETS_SETUP.md)** - API configuration guide
- **[GitHub Actions Usage](GITHUB_ACTIONS_USAGE.md)** - Automation workflows

### Asset Management
- **[Team Logos Guide](TEAM_LOGOS.md)** - Team logo management
- **[Player Database](PLAYER_DATABASE.md)** - Player data structure
- **[Logo Enhancement](LOGO_ENHANCEMENT.md)** - Logo enhancement techniques

### Team-Specific
- **[Racing C Documentation](RACING_C_README.md)** - Team-specific documentation

## 🔧 Configuration

### Environment Variables (Production)
- `SECRET_KEY` - Flask secret key for sessions (auto-generated in dev)
- `FLASK_ENV` - Set to `production` for production deployments
- `DEBUG` - Set to `False` for production
- `GOOGLE_DRIVE_CREDENTIALS` - Google API service account JSON
- `GOOGLE_DRIVE_FOLDER_ID` - Target folder for file uploads

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
- **Player Statistics** - Individual player performance metrics
- **Division Standings** - Team rankings and records
- **Referee Assignments** - Referee assignments and foul statistics
- **Game Schedules** - Upcoming fixtures and schedules

The data processing pipeline:
1. **Scraping** - PowerShell scripts download HTML from FLBB website
2. **Extraction** - Game data extracted and stored as JSON
3. **Processing** - Python utilities calculate statistics and generate CSV
4. **Storage** - Data stored locally and backed up to Google Drive
5. **Visualization** - Flask application renders interactive interface

## 🛡️ Security

- Service account credentials are securely handled through GitHub Secrets
- No sensitive data is committed to the repository
- Automated cleanup of temporary credential files
- Production deployments use environment-based configuration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

### Completed Features ✅
- [x] Team, player, referee, and game detail pages
- [x] User preferences with 6 custom themes
- [x] Admin interface for season management
- [x] API endpoints for hover statistics
- [x] Starting five predictions
- [x] Game hotness rating system
- [x] Automated Google Drive backups
- [x] Multi-platform deployment support
- [x] Version tracking system
- [x] Referee performance index

### Planned Enhancements 🚧
- [ ] Advanced player comparison tools
- [ ] Historical trend analysis across seasons
- [ ] Real-time game tracking
- [ ] RESTful API for external access
- [ ] Enhanced data visualizations
- [ ] Mobile app (iOS/Android)
- [ ] Email notifications
- [ ] Fantasy basketball integration

## 📞 Support

For questions, issues, or contributions:
1. Check the [documentation](./) for detailed guides
2. Review existing [GitHub Issues](../../issues) 
3. Create a new issue with detailed information
4. Refer to deployment guides for hosting questions

---

**Ready to explore Luxembourg basketball statistics?** 🏀  
Get started with `python3 tests/test_local_flask.py` and visit `http://localhost:5000`!