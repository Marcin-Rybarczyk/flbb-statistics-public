# Flask Application Deployment Guide

This guide provides comprehensive instructions for deploying the FLBB Statistics Flask application locally and to various free hosting platforms.

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git

### Local Testing

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test the application:**
   ```bash
   python3 test_local_flask.py --test-only
   ```

3. **Run locally:**
   ```bash
   # Development server (with debugging)
   python3 test_local_flask.py
   
   # Production-like testing
   python3 test_local_flask.py --production
   ```

   The application will be available at `http://localhost:5000`

## 🌐 Free Hosting Options

### 1. Render.com (Recommended)

**Why Render.com:**
- ✅ 750 free hours per month (enough for continuous running)
- ✅ Automatic SSL certificates
- ✅ Git-based deployments
- ✅ Environment variable management
- ✅ Easy to use interface

**Deployment Steps:**

1. **Prepare your repository:**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Deploy using the assistant:**
   ```bash
   python3 deploy_flask.py render
   ```
   
3. **Manual deployment:**
   - Go to [render.com](https://render.com)
   - Sign up/in with GitHub
   - Create new "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT wsgi:application`
     - **Environment Variables:**
       - `SECRET_KEY`: (generate a secure random string)
       - `FLASK_ENV`: `production`

4. **Deploy!** Render will build and deploy your app automatically.

### 2. Railway.app

**Why Railway.app:**
- ✅ $5/month free credits (generous usage)
- ✅ Modern interface
- ✅ One-click deployments
- ✅ Built-in monitoring

**Deployment Steps:**

1. **Using the deployment assistant:**
   ```bash
   python3 deploy_flask.py railway
   ```

2. **Manual deployment:**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Python and deploys

### 3. GitHub Pages (Static Version)

**Note:** This deploys a static version of your site (no server-side functionality).

**Deployment:**
```bash
python3 deploy_flask.py github
```

This will:
1. Generate static HTML files using `generate_static.py`
2. Create files in the `static_site/` directory
3. Provide instructions for GitHub Pages setup

## 🛠️ Deployment Scripts

### `test_local_flask.py`
Local development and testing script with the following features:

- **Data validation:** Checks if CSV data is available
- **Flask app testing:** Validates routes and functionality
- **Multiple modes:**
  ```bash
  python3 test_local_flask.py --help           # Show help
  python3 test_local_flask.py --test-only      # Run tests only
  python3 test_local_flask.py --port 8080      # Custom port
  python3 test_local_flask.py --production     # Test with gunicorn
  ```

### `deploy_flask.py`
Comprehensive deployment assistant:

- **Requirements validation:** Ensures all files are present
- **Platform-specific guides:** Tailored instructions for each platform
- **Interactive deployment:** Guides you through the process
- **Browser integration:** Opens deployment sites automatically

```bash
python3 deploy_flask.py                    # Interactive mode
python3 deploy_flask.py render            # Render.com guide
python3 deploy_flask.py railway           # Railway.app guide
python3 deploy_flask.py github            # GitHub Pages deploy
python3 deploy_flask.py local             # Local production test
```

## 📁 Project Structure

```
flbb-statistics/
├── app.py                 # Main Flask application
├── wsgi.py                # Production WSGI entry point
├── utils.py               # Data processing utilities
├── requirements.txt       # Python dependencies
├── test_local_flask.py    # Local testing script
├── deploy_flask.py        # Deployment assistant
├── templates/             # HTML templates
├── static_site/           # Generated static files (for GitHub Pages)
├── full-game-stats.csv    # Basketball statistics data
├── render_deploy.txt      # Render.com deployment notes
├── railway_deploy.txt     # Railway.app deployment notes
└── README_DEPLOYMENT.md   # This file
```

## 🔧 Configuration Files

### `requirements.txt`
```
Flask==3.1.2
pandas==2.3.2  
gunicorn==23.0.0
```

### `wsgi.py`
Production-ready WSGI configuration with:
- Environment-based configuration
- HTTPS enforcement option
- Production logging
- Error handling

## 🚨 Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'flask'**
   ```bash
   pip install -r requirements.txt
   ```

2. **No data available error**
   - Ensure `full-game-stats.csv` exists in the project root
   - Check data format with: `python3 test_local_flask.py --test-only`

3. **Port already in use**
   ```bash
   python3 test_local_flask.py --port 8080  # Use different port
   ```

4. **Deployment fails**
   - Run requirements check: `python3 deploy_flask.py local`
   - Check logs in hosting platform dashboard
   - Ensure environment variables are set correctly

### Getting Help

1. **Test locally first:**
   ```bash
   python3 test_local_flask.py --test-only
   ```

2. **Check deployment requirements:**
   ```bash
   python3 deploy_flask.py local
   ```

3. **Review hosting platform documentation:**
   - [Render.com Docs](https://docs.render.com)
   - [Railway.app Docs](https://docs.railway.app)

## 🎯 Next Steps After Deployment

1. **Set up custom domain** (if supported by hosting platform)
2. **Configure environment variables** for production
3. **Set up monitoring** and alerts
4. **Enable automatic deployments** from main branch
5. **Set up data pipeline** for regular data updates

## 📊 Features

The deployed Flask application includes:

- **Interactive division standings** with filtering
- **Team performance statistics** 
- **Highest scoring games** analysis
- **Responsive design** for mobile and desktop
- **Real basketball data** from FLBB (Luxembourg Basketball Federation)

---

**Ready to deploy?** Run `python3 deploy_flask.py` to get started! 🚀