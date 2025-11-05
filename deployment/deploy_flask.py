#!/usr/bin/env python3
"""
Flask Application Deployment Assistant

This script helps deploy the FLBB Statistics Flask application to various 
free hosting platforms. It provides guided setup and deployment instructions.

Usage:
    python3 deploy_flask.py [platform]
    
Supported platforms:
    - render (render.com)
    - railway (railway.app)  
    - github (GitHub Pages - static only)
    - local (local production testing)
"""

import argparse
import os
import sys
import subprocess
import webbrowser
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text, color=Colors.GREEN):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.END}")

def print_header(text):
    """Print a formatted header"""
    print_colored(f"\n{Colors.BOLD}{'=' * 60}", Colors.BLUE)
    print_colored(f"{Colors.BOLD}{text.center(60)}", Colors.BLUE)
    print_colored(f"{Colors.BOLD}{'=' * 60}", Colors.BLUE)

def check_requirements():
    """Check if all required files exist"""
    print_header("Checking Requirements")
    
    required_files = [
        'app.py',
        'utils.py', 
        'wsgi.py',
        'requirements.txt',
        'full-game-stats.csv'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print_colored(f"✅ {file} - Found")
        else:
            print_colored(f"❌ {file} - Missing", Colors.RED)
            missing_files.append(file)
    
    if missing_files:
        print_colored(f"\n❌ Missing required files: {', '.join(missing_files)}", Colors.RED)
        return False
    
    # Test Flask app
    try:
        from test_local_flask import test_data_availability, test_flask_import
        if not test_data_availability():
            print_colored("❌ Data validation failed", Colors.RED)
            return False
        if not test_flask_import():
            print_colored("❌ Flask app validation failed", Colors.RED) 
            return False
        print_colored("✅ All requirements satisfied!")
    except Exception as e:
        print_colored(f"❌ Validation error: {e}", Colors.RED)
        return False
    
    return True

def deploy_render():
    """Guide user through Render.com deployment"""
    print_header("Render.com Deployment Guide")
    
    print_colored("🚀 Render.com is recommended for Flask apps with these benefits:")
    print("   • 750 free hours per month (continuous running)")
    print("   • Automatic SSL certificates")
    print("   • Git-based deployments")
    print("   • Environment variable management")
    print("   • Free PostgreSQL database available")
    
    print_colored("\n📋 Deployment Steps:")
    print("1. Create account at https://render.com")
    print("2. Connect your GitHub repository")
    print("3. Create a new Web Service")
    print("4. Configure the service:")
    print("   • Runtime: Python 3")
    print(f"   • Build Command: pip install -r requirements.txt")
    print(f"   • Start Command: gunicorn --bind 0.0.0.0:$PORT wsgi:application")
    print("   • Environment Variables:")
    print("     - SECRET_KEY: (generate a secure random key)")
    print("     - FLASK_ENV: production")
    
    print_colored("\n🔗 Ready to deploy?")
    if input("Open Render.com in browser? (y/n): ").lower().startswith('y'):
        webbrowser.open("https://render.com")
    
    print_colored("\n📝 Configuration files created:")
    print("   • render_deploy.txt - Contains detailed instructions")
    
    print_colored("\n🔒 HTTPS/SSL Information:", Colors.GREEN)
    print("   • Render.com provides automatic HTTPS/SSL certificates")
    print("   • Your app will be available at https://your-app-name.onrender.com")
    print("   • See docs/HTTPS_SETUP.md for custom domain setup")

def deploy_railway():
    """Guide user through Railway.app deployment"""
    print_header("Railway.app Deployment Guide")
    
    print_colored("🚂 Railway.app offers modern deployment with:")
    print("   • $5/month free credits (generous usage)")
    print("   • One-click deployments")
    print("   • Built-in monitoring")
    print("   • Database integrations")
    
    print_colored("\n📋 Deployment Options:")
    print("\n1. Web Interface (Recommended for beginners):")
    print("   • Go to https://railway.app")
    print("   • Sign in with GitHub")
    print("   • Click 'New Project' > 'Deploy from GitHub repo'")
    print("   • Select your repository")
    print("   • Railway will auto-detect Python and deploy")
    
    print("\n2. Railway CLI (For advanced users):")
    print("   • npm install -g @railway/cli")
    print("   • railway login")
    print("   • railway link (in your project directory)")
    print("   • railway up")
    
    print_colored("\n🔗 Ready to deploy?")
    if input("Open Railway.app in browser? (y/n): ").lower().startswith('y'):
        webbrowser.open("https://railway.app")
    
    print_colored("\n🔒 HTTPS/SSL Information:", Colors.GREEN)
    print("   • Railway.app provides automatic HTTPS/SSL certificates")
    print("   • Your app will be available at https://your-app.up.railway.app")
    print("   • See docs/HTTPS_SETUP.md for custom domain setup")

def deploy_github_pages():
    """Deploy static version to GitHub Pages"""
    print_header("GitHub Pages Static Deployment")
    
    print_colored("📄 GitHub Pages deploys a static version of your site:")
    print("   • Free hosting for public repositories")
    print("   • Custom domains supported")
    print("   • Automatic updates via GitHub Actions")
    print("   • Limited to static content (no server-side processing)")
    
    print_colored("\n🔄 Generating static site...")
    try:
        subprocess.run([sys.executable, 'deployment/generate_static.py'], check=True)
        print_colored("✅ Static site generated successfully!")
        
        if os.path.exists('static_site'):
            file_count = len(list(Path('static_site').rglob('*')))
            print(f"   Generated {file_count} files in static_site/ directory")
        
        print_colored("\n📋 Next steps:")
        print("1. Commit and push the generated static_site/ directory")
        print("2. Go to your GitHub repository settings")
        print("3. Enable GitHub Pages from the 'static_site' folder")
        print("4. Your site will be available at: https://[username].github.io/[repo-name]")
        
        print_colored("\n🔒 HTTPS/SSL Information:", Colors.GREEN)
        print("   • GitHub Pages provides automatic HTTPS")
        print("   • Enable 'Enforce HTTPS' in repository settings")
        print("   • See docs/HTTPS_SETUP.md for custom domain setup")
        
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Error generating static site: {e}", Colors.RED)
        return False
    
    return True

def test_local_production():
    """Test Flask app in production mode locally"""
    print_header("Local Production Testing")
    
    print_colored("🧪 Testing production configuration locally...")
    
    # Test with gunicorn
    try:
        print_colored("\n🔧 Testing with gunicorn (production WSGI server):")
        print("   Starting on http://localhost:8000")
        print("   Press Ctrl+C to stop")
        
        cmd = [
            'gunicorn',
            '--bind', '127.0.0.1:8000', 
            '--workers', '1',
            '--timeout', '30',
            '--access-logfile', '-',
            'wsgi:application'
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print_colored("\n🛑 Local production test stopped")
    except FileNotFoundError:
        print_colored("❌ gunicorn not found. Install with: pip install gunicorn", Colors.RED)
    except Exception as e:
        print_colored(f"❌ Error running production test: {e}", Colors.RED)

def main():
    parser = argparse.ArgumentParser(description='Deploy Flask application to various platforms')
    parser.add_argument('platform', nargs='?', 
                        choices=['render', 'railway', 'github', 'local'],
                        help='Deployment platform (render, railway, github, local)')
    
    args = parser.parse_args()
    
    print_colored("🏀 FLBB Statistics - Flask Deployment Assistant", Colors.BOLD)
    print_colored("   📖 For HTTPS/SSL setup, see: docs/HTTPS_SETUP.md", Colors.BLUE)
    
    # Check requirements first (skip for GitHub Pages as it handles missing data gracefully)
    if args.platform != 'github' and not check_requirements():
        print_colored("\n❌ Requirements check failed. Please fix issues before deploying.", Colors.RED)
        return 1
    
    if not args.platform:
        print_header("Available Deployment Options")
        print_colored("1. render - Render.com (Recommended)")
        print_colored("2. railway - Railway.app") 
        print_colored("3. github - GitHub Pages (Static only)")
        print_colored("4. local - Local production testing")
        
        choice = input("\nSelect platform (1-4) or enter name: ").strip()
        platform_map = {'1': 'render', '2': 'railway', '3': 'github', '4': 'local'}
        args.platform = platform_map.get(choice, choice)
        
        # Re-check requirements if not GitHub Pages and not already checked
        if args.platform != 'github' and not check_requirements():
            print_colored("\n❌ Requirements check failed. Please fix issues before deploying.", Colors.RED)
            return 1
    
    # Deploy to selected platform
    if args.platform == 'render':
        deploy_render()
    elif args.platform == 'railway':
        deploy_railway()
    elif args.platform == 'github':
        if not deploy_github_pages():
            return 1
    elif args.platform == 'local':
        test_local_production()
    else:
        print_colored(f"❌ Unknown platform: {args.platform}", Colors.RED)
        print("Available: render, railway, github, local")
        return 1
    
    print_colored(f"\n🎉 Deployment guide for {args.platform} completed!")
    return 0

if __name__ == '__main__':
    sys.exit(main())