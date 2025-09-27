# FLBB Statistics

A comprehensive Flask-based web application for analyzing and visualizing basketball statistics from the Luxembourg Basketball Federation (FLBB). The application automatically scrapes game data, processes it into meaningful insights, and presents interactive visualizations through a modern web interface.

## 🏀 Overview

This project provides in-depth analysis and visualization of basketball statistics from the Luxembourg Basketball Federation. It automatically scrapes game data, processes it into meaningful insights, and presents interactive visualizations through a modern web interface.

**Live Demo**: [Visit the deployed application](https://flbb-statistics-public.onrender.com)

## 📁 Project Structure

```
flbb-statistics/
├── 📂 src/                          # Main application source code
│   ├── app.py                       # Flask web application
│   ├── utils.py                     # Data processing and statistics utilities  
│   ├── wsgi.py                      # Production WSGI configuration
│   └── google_drive_helper.py       # Google Drive integration
├── 📂 scripts/                      # Data collection and processing scripts
│   ├── download-controller.ps1      # Main data collection script (PowerShell)
│   ├── extract-game.ps1             # Data extraction and JSON conversion (PowerShell)
│   ├── post_process.py              # Post-processing automation (Python)
│   └── check_version_api.py         # API version checking utility
├── 📂 deployment/                   # Deployment tools and configuration
│   ├── deploy_flask.py              # Multi-platform deployment assistant
│   ├── generate_static.py           # Static site generator for GitHub Pages
│   ├── generate_racing_c_static.py  # Racing C team specific static generator
│   ├── requirements.txt             # Python dependencies
│   ├── render_deploy.txt            # Render.com deployment notes
│   └── railway_deploy.txt           # Railway.app deployment notes
├── 📂 data/                         # Data files and configuration
│   ├── full-game-stats.csv          # Main statistics data source
│   ├── config.json                  # Application configuration
│   ├── player-map.json              # Player mapping data
│   ├── event-action-patterns.json   # Game event patterns
│   └── Net40/                       # .NET dependencies for PowerShell scripts
├── 📂 docs/                         # Comprehensive documentation
│   ├── README.md                    # This file
│   ├── README_DEPLOYMENT.md         # Complete deployment instructions
│   ├── GOOGLE_DRIVE_SECRETS_SETUP.md # Google Drive API setup guide
│   ├── GITHUB_ACTIONS_USAGE.md      # Automation workflows documentation
│   ├── CSV_GENERATION_WORKFLOW.md   # Data processing pipeline guide
│   └── IMPLEMENTATION_SUMMARY.md    # Technical implementation details
├── 📂 tests/                        # Testing and validation
│   ├── test_local_flask.py          # Local development and testing script
│   ├── test_google_drive.py         # Google Drive integration tests
│   └── test-multiple-downloads.ps1  # PowerShell testing script
├── 📂 templates/                    # HTML templates for web interface
│   ├── base.html                    # Base template layout
│   ├── index.html                   # Home page template
│   ├── statistics.html              # Main statistics overview
│   ├── team_stats.html              # Team analysis page
│   ├── player_stats.html            # Player statistics page
│   ├── deeper_analysis.html         # Advanced analytics page
│   ├── fixtures.html                # Fixtures and schedule page
│   └── admin.html                   # Administrative interface
├── 📂 static_site/                  # Generated static files for GitHub Pages
├── 📂 logos/                        # Team logos and branding assets
├── 📂 .github/workflows/            # GitHub Actions automation
│   ├── google-drive-upload.yml      # Automated Google Drive uploads
│   ├── google-drive-list.yml        # Drive file listing workflow
│   ├── upload-to-gdrive.yml         # Legacy upload workflow
│   └── deploy-website.yml           # Website deployment automation
├── wsgi.py                          # Root-level WSGI entry point for deployment
├── requirements.txt                 # Python dependencies (copy for easy access)
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
- **[Render.com](docs/README_DEPLOYMENT.md#render-com)** - Recommended for full Flask deployment
- **[Railway.app](docs/README_DEPLOYMENT.md#railway-app)** - Modern platform with generous free tier
- **[GitHub Pages](docs/README_DEPLOYMENT.md#github-pages)** - Static version hosting

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:
- **[Deployment Guide](docs/README_DEPLOYMENT.md)** - Complete deployment instructions
- **[Google Drive Setup](docs/GOOGLE_DRIVE_SECRETS_SETUP.md)** - API configuration guide
- **[GitHub Actions Usage](docs/GITHUB_ACTIONS_USAGE.md)** - Automation workflows
- **[CSV Generation Workflow](docs/CSV_GENERATION_WORKFLOW.md)** - Data processing pipeline

## 🚦 Usage

### Web Interface
The Flask application provides several analytical views:
- **Home Page** - Division standings with filtering options
- **Team Stats** - Detailed team performance metrics
- **Player Analysis** - Individual player statistics and rankings
- **Game Insights** - Notable games and statistical highlights

### Data Processing
The application automatically processes basketball data through:
1. **Data Collection** - PowerShell scripts scrape FLBB website
2. **Data Processing** - Raw HTML converted to structured JSON
3. **CSV Generation** - Statistics calculated and exported  
4. **Visualization** - Flask app presents interactive charts and tables

## 🔧 Configuration

### Environment Variables (Production)
- `SECRET_KEY` - Flask secret key for sessions
- `FLASK_ENV` - Set to `production` for production deployments
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
- Game results and schedules
- Player statistics and performance metrics
- Division standings and team information  
- Referee assignments and foul statistics

## 🛡️ Security

- Service account credentials are securely handled through GitHub Secrets
- No sensitive data is committed to the repository
- Automated cleanup of temporary credential files
- Production deployments use environment-based configuration

## 🎯 Roadmap

- [ ] Enhanced mobile responsive design
- [ ] Advanced player comparison tools
- [ ] Historical trend analysis
- [ ] Real-time game tracking
- [ ] API endpoints for data access
- [ ] Enhanced visualizations and charts

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