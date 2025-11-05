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
   python3 tests/test_local_flask.py --test-only
   ```

3. **Run locally:**
   ```bash
   # Development server (with debugging)
   python3 tests/test_local_flask.py
   
   # Production-like testing
   python3 tests/test_local_flask.py --production
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
python3 deployment/deploy_flask.py github
```

This will:
1. Generate static HTML files using `generate_static.py`
2. Create files in the `static_site/` directory
3. Provide instructions for GitHub Pages setup

### 4. MyDevil.net (Polish Hosting)

**Why MyDevil.net:**
- ✅ Affordable Polish hosting with Python support
- ✅ SSH access for deployment
- ✅ Virtual environment support
- ✅ Custom domain support

**Deployment Steps:**

1. **Prepare your project for MyDevil:**
   ```bash
   python3 prepare_mydevil_setup.py
   ```
   
   **Note:** The `prepare_mydevil_setup.py` script is located in the root directory of the repository.
   
   This script will:
   - Ensure all `__init__.py` files exist in `src/` directory
   - Fix relative imports to use absolute paths (e.g., `from src.utils import ...`)
   - Create/verify `wsgi.py` and `passenger_wsgi.py` entry points
   - Check `requirements.txt` for Flask and gunicorn
   
   For more details about this script, see the [`prepare_mydevil_setup.py`](#prepare_mydevil_setuppy) section below.

2. **SSH into your MyDevil account:**
   ```bash
   ssh yourlogin@server.mydevil.net
   ```

3. **Create a virtual environment:**
   ```bash
   python3.11 -m venv ~/flaskenv
   source ~/flaskenv/bin/activate
   ```

4. **Upload your project:**
   - Use Git: `git clone your-repo-url`
   - Or use SFTP to upload files

5. **Install dependencies:**
   ```bash
   cd ~/your-project-directory
   pip install -r requirements.txt
   ```

6. **Configure webapp in MyDevil panel:**
   - Go to WWW → Add new website
   - Choose Python application
   - Set Python version to 3.11
   - Set WSGI file path: `/home/yourlogin/path/to/passenger_wsgi.py`
   
   Or via SSH:
   ```bash
   devil www add myflaskapp python3.11 ~/path/to/passenger_wsgi.py
   ```

7. **Set environment variables (optional):**
   Create `.env` file or set in panel:
   ```
   FLASK_ENV=production
   DEBUG=False
   SECRET_KEY=your-secret-key-here
   ```

8. **Restart the application:**
   ```bash
   touch ~/domains/myflaskapp.YOURUSERNAME.mydevil.net/tmp/restart.txt
   ```

9. **Access your application:**
   Visit `https://myflaskapp.YOURUSERNAME.mydevil.net`

**Important Files for MyDevil:**
- `passenger_wsgi.py` - Entry point for Passenger WSGI
- `prepare_mydevil_setup.py` - Setup automation script
- `requirements.txt` - Dependencies list
- `.env` (optional) - Environment variables

**Troubleshooting:**
- If you see import errors, make sure all imports use `from src.module import ...` format
- Check error logs: `~/logs/yourapp-error.log`
- Verify Python version: `python --version` (should be 3.11+)
- Restart after changes: `touch tmp/restart.txt`

## 🛠️ Deployment Scripts

### `test_local_flask.py`
Local development and testing script with the following features:

- **Data validation:** Checks if CSV data is available
- **Flask app testing:** Validates routes and functionality
- **Multiple modes:**
  ```bash
  python3 tests/test_local_flask.py --help           # Show help
  python3 tests/test_local_flask.py --test-only      # Run tests only
  python3 tests/test_local_flask.py --port 8080      # Custom port
  python3 tests/test_local_flask.py --production     # Test with gunicorn
  ```

### `deploy_flask.py`
Comprehensive deployment assistant:

- **Requirements validation:** Ensures all files are present
- **Platform-specific guides:** Tailored instructions for each platform
- **Interactive deployment:** Guides you through the process
- **Browser integration:** Opens deployment sites automatically

```bash
python3 deployment/deploy_flask.py                    # Interactive mode
python3 deployment/deploy_flask.py render            # Render.com guide
python3 deployment/deploy_flask.py railway           # Railway.app guide
python3 deployment/deploy_flask.py github            # GitHub Pages deploy
python3 deployment/deploy_flask.py local             # Local production test
```

### `prepare_mydevil_setup.py`
MyDevil.net deployment preparation script (located in project root):

**Purpose:** Prepares the Flask application for deployment on MyDevil.net hosting platform.

**What it does:**
- **Ensures proper project structure:** Creates `__init__.py` files in all directories under `src/`
- **Fixes imports:** Converts relative imports (e.g., `from .utils import X`) to absolute imports (e.g., `from src.utils import X`) for MyDevil compatibility
- **Creates WSGI files:** Sets up `passenger_wsgi.py` for Passenger WSGI server
- **Validates requirements:** Checks for Flask and gunicorn in `requirements.txt` and adds them if missing
- **Provides deployment instructions:** Prints step-by-step SSH and setup commands

**Usage:**
```bash
python3 prepare_mydevil_setup.py
```

**Output Example:**
```
🚀 Preparing Flask app for MyDevil.net deployment...

✅ Added src/__init__.py
✅ Added src/utils/__init__.py
🔧 Fixed relative imports in src/app.py
✅ Created passenger_wsgi.py
✅ requirements.txt already contains Flask & gunicorn

🎉 Done! Your project is ready for MyDevil deployment.

👉 Next steps on MyDevil:
1. SSH into your account: ssh yourlogin@server.mydevil.net
2. Create virtual environment
3. Upload your project
4. Install requirements
5. Add webapp in panel
```

**Important Notes:**
- Run this script before uploading to MyDevil.net
- The script modifies import statements for compatibility
- All changes are safe and reversible
- Passenger WSGI is specific to MyDevil's hosting environment
```

## 📁 Project Structure

```
flbb-statistics/
├── src/
│   ├── app.py                 # Main Flask application
│   ├── wsgi.py                # Production WSGI entry point
│   ├── utils.py               # Data processing utilities
│   ├── version.py             # Version tracking
│   └── google_drive_helper.py # Google Drive integration
├── deployment/
│   ├── deploy_flask.py        # Deployment assistant
│   ├── generate_static.py     # Static site generator
│   └── requirements.txt       # Deployment dependencies
├── tests/
│   └── test_local_flask.py    # Local testing script
├── requirements.txt           # Main Python dependencies
├── passenger_wsgi.py          # MyDevil.net WSGI entry point
├── prepare_mydevil_setup.py   # MyDevil deployment prep
└── ...
```
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
   - Ensure `data/full-game-stats.csv` exists in the project
   - Check data format with: `python3 tests/test_local_flask.py --test-only`

3. **Port already in use**
   ```bash
   python3 tests/test_local_flask.py --port 8080  # Use different port
   ```

4. **Deployment fails**
   - Run requirements check: `python3 deployment/deploy_flask.py local`
   - Check logs in hosting platform dashboard
   - Ensure environment variables are set correctly

### Getting Help

1. **Test locally first:**
   ```bash
   python3 tests/test_local_flask.py --test-only
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