# FLBB Statistics

A comprehensive data analytics and visualization platform for Luxembourg Basketball Federation (FLBB) statistics.

![Basketball Statistics Dashboard](https://img.shields.io/badge/Flask-Web%20App-blue?logo=flask) ![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python) ![Data Analysis](https://img.shields.io/badge/Data-Analytics-orange) ![Deployment](https://img.shields.io/badge/Deploy-Ready-success)

## 🏀 Overview

This Flask-based web application provides in-depth analysis and visualization of basketball statistics from the Luxembourg Basketball Federation. It automatically scrapes game data, processes it into meaningful insights, and presents interactive visualizations through a modern web interface.

## 🚀 Features

### 📊 Statistical Analysis
- **Division Standings** - Interactive league tables with team performance metrics
- **Player Statistics** - Top scorers, shooting efficiency, and performance analysis  
- **Team Performance** - Win/loss records, scoring trends, and comparative analysis
- **Game Insights** - Highest scoring games, biggest wins, and lead changes
- **Referee Analysis** - Foul statistics and game impact analysis

### 🤖 Automated Data Pipeline
- Daily automated data collection from FLBB website
- Automatic processing of HTML game data into structured formats
- CSV generation and Google Drive integration
- GitHub Actions workflows for continuous updates

### 🌐 Multi-Platform Deployment
- **Local Development** - Full-featured development environment
- **Render.com** - Recommended cloud hosting platform
- **Railway.app** - Modern deployment with generous free tier
- **GitHub Pages** - Static version for basic hosting

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
   python3 test_local_flask.py --test-only
   ```

4. **Start the application:**
   ```bash
   # Development server
   python3 test_local_flask.py
   
   # Production-like testing
   python3 test_local_flask.py --production
   ```

5. **Access the web interface:**
   Open your browser to `http://localhost:5000`

## 📁 Project Structure

```
flbb-statistics/
├── app.py                    # Main Flask application
├── utils.py                  # Data processing and statistics
├── wsgi.py                   # Production WSGI entry point
├── requirements.txt          # Python dependencies
├── full-game-stats.csv      # Main statistics data source
├── templates/               # HTML templates for web interface
├── static_site/             # Generated static files
├── .github/workflows/       # GitHub Actions automation
├── doc/                     # Comprehensive documentation
├── deploy_flask.py          # Multi-platform deployment assistant  
├── google_drive_helper.py   # Google Drive integration
├── download-controller.ps1  # Data collection script
├── extract-game.ps1         # Data processing script
└── test_local_flask.py      # Local testing and development
```

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

## 🌐 Deployment Options

### Quick Deployment
Use the built-in deployment assistant:
```bash
python3 deploy_flask.py              # Interactive guided deployment
python3 deploy_flask.py render      # Deploy to Render.com
python3 deploy_flask.py railway     # Deploy to Railway.app
python3 deploy_flask.py github      # Generate static site for GitHub Pages
```

### Platform-Specific Instructions
- **[Render.com](doc/README_DEPLOYMENT.md#render-com)** - Recommended for full Flask deployment
- **[Railway.app](doc/README_DEPLOYMENT.md#railway-app)** - Modern platform with generous free tier
- **[GitHub Pages](doc/README_DEPLOYMENT.md#github-pages)** - Static version hosting

## 📖 Documentation

Comprehensive documentation is available in the `doc/` directory:
- **[Deployment Guide](README_DEPLOYMENT.md)** - Complete deployment instructions
- **[Google Drive Setup](doc/GOOGLE_DRIVE_SECRETS_SETUP.md)** - API configuration guide
- **[GitHub Actions Usage](doc/GITHUB_ACTIONS_USAGE.md)** - Automation workflows
- **[CSV Generation Workflow](doc/CSV_GENERATION_WORKFLOW.md)** - Data processing pipeline

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
3. Test your changes locally with `python3 test_local_flask.py --test-only`
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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] Enhanced mobile responsive design
- [ ] Advanced player comparison tools
- [ ] Historical trend analysis
- [ ] Real-time game tracking
- [ ] API endpoints for data access
- [ ] Enhanced visualizations and charts

## 📞 Support

For questions, issues, or contributions:
1. Check the [documentation](doc/) for detailed guides
2. Review existing [GitHub Issues](../../issues) 
3. Create a new issue with detailed information
4. Refer to deployment guides for hosting questions

---

**Ready to explore Luxembourg basketball statistics?** 🏀  
Get started with `python3 test_local_flask.py` and visit `http://localhost:5000`!