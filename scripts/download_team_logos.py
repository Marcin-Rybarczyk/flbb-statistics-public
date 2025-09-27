#!/usr/bin/env python3
"""
Team Logo Downloader for FLBB Statistics

This script downloads team logos from the Luxembourg Basketball Federation (FLBB) website
and stores them in the logos directory for use in the web application.
"""

import os
import sys
import requests
import pandas as pd
from urllib.parse import urljoin, quote
import time
import re
from pathlib import Path

# Configuration
LOGOS_DIR = "logos"
CSV_FILE = "data/full-game-stats.csv"
BASE_URL = "https://www.luxembourg.basketball"
REQUEST_DELAY = 1.0  # Delay between requests to be respectful
MAX_RETRIES = 3

def create_logos_directory():
    """Create logos directory if it doesn't exist"""
    Path(LOGOS_DIR).mkdir(exist_ok=True)
    print(f"Created/verified logos directory: {LOGOS_DIR}")

def get_unique_teams():
    """Extract unique team names from the CSV data"""
    try:
        df = pd.read_csv(CSV_FILE)
        home_teams = set(df['HomeTeamName'].dropna().unique())
        away_teams = set(df['AwayTeamName'].dropna().unique())
        all_teams = sorted(home_teams.union(away_teams))
        return all_teams
    except Exception as e:
        print(f"Error reading team data: {e}")
        return []

def normalize_team_name(team_name):
    """Normalize team name for file naming and URL construction"""
    # Remove special characters and convert to lowercase
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', team_name)
    normalized = normalized.lower().replace(' ', '-')
    return normalized

def search_team_logo_on_flbb(team_name, session):
    """
    Search for team logo on FLBB website using different strategies
    Returns the logo URL if found, None otherwise
    """
    normalized_name = normalize_team_name(team_name)
    
    # Strategy 1: Try direct team page URL patterns
    possible_urls = [
        f"{BASE_URL}/equipe/{normalized_name}",
        f"{BASE_URL}/club/{normalized_name}", 
        f"{BASE_URL}/teams/{normalized_name}",
    ]
    
    for url in possible_urls:
        try:
            time.sleep(REQUEST_DELAY)
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                logo_url = extract_logo_from_page(response.text, team_name)
                if logo_url:
                    return logo_url
        except Exception as e:
            print(f"  Failed to check {url}: {e}")
            continue
    
    # Strategy 2: Search for team in general pages
    search_urls = [
        f"{BASE_URL}/c/categorie/all",
        f"{BASE_URL}/search?q={quote(team_name)}",
    ]
    
    for url in search_urls:
        try:
            time.sleep(REQUEST_DELAY)
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                logo_url = extract_logo_from_search_page(response.text, team_name)
                if logo_url:
                    return logo_url
        except Exception as e:
            print(f"  Failed to search at {url}: {e}")
            continue
    
    return None

def extract_logo_from_page(html_content, team_name):
    """Extract logo URL from team page HTML"""
    # Look for common logo patterns
    patterns = [
        r'<img[^>]+src="([^"]+)"[^>]*class="[^"]*logo[^"]*"',
        r'<img[^>]+class="[^"]*logo[^"]*"[^>]+src="([^"]+)"',
        r'<img[^>]+src="([^"]+logo[^"]+)"',
        r'<img[^>]+src="([^"]+)"[^>]*alt="[^"]*' + re.escape(team_name) + '[^"]*"',
        r'<img[^>]+alt="[^"]*' + re.escape(team_name) + '[^"]*"[^>]+src="([^"]+)"',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            if match and any(ext in match.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']):
                return urljoin(BASE_URL, match)
    
    return None

def extract_logo_from_search_page(html_content, team_name):
    """Extract logo URL from search results or category pages"""
    # This would be more complex - looking for team cards or listings
    # For now, return None as this needs specific knowledge of FLBB site structure
    return None

def download_logo(logo_url, team_name, session):
    """Download logo from URL and save to logos directory"""
    try:
        time.sleep(REQUEST_DELAY)
        response = session.get(logo_url, timeout=15)
        response.raise_for_status()
        
        # Determine file extension from content-type or URL
        content_type = response.headers.get('content-type', '').lower()
        if 'png' in content_type:
            ext = '.png'
        elif 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'gif' in content_type:
            ext = '.gif'
        elif 'svg' in content_type:
            ext = '.svg'
        else:
            # Try to get extension from URL
            ext = '.jpg'  # Default
            if logo_url.lower().endswith('.png'):
                ext = '.png'
            elif logo_url.lower().endswith(('.jpg', '.jpeg')):
                ext = '.jpg'
            elif logo_url.lower().endswith('.gif'):
                ext = '.gif'
            elif logo_url.lower().endswith('.svg'):
                ext = '.svg'
        
        # Create filename
        safe_name = normalize_team_name(team_name)
        filename = f"{safe_name}{ext}"
        filepath = os.path.join(LOGOS_DIR, filename)
        
        # Save logo
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"  ✓ Downloaded: {filename}")
        return filepath
        
    except Exception as e:
        print(f"  ✗ Failed to download logo: {e}")
        return None

def create_default_logo(team_name):
    """Create a simple text-based logo as fallback"""
    try:
        # For now, just create a placeholder file
        safe_name = normalize_team_name(team_name)
        filename = f"{safe_name}_placeholder.txt"
        filepath = os.path.join(LOGOS_DIR, filename)
        
        with open(filepath, 'w') as f:
            f.write(f"Logo placeholder for: {team_name}\n")
            f.write(f"Team: {team_name}\n")
            f.write(f"Normalized: {safe_name}\n")
        
        print(f"  → Created placeholder: {filename}")
        return filepath
    except Exception as e:
        print(f"  ✗ Failed to create placeholder: {e}")
        return None

def download_all_team_logos():
    """Main function to download logos for all teams"""
    print("FLBB Team Logo Downloader")
    print("=" * 40)
    
    # Setup
    create_logos_directory()
    teams = get_unique_teams()
    
    if not teams:
        print("No teams found in data!")
        return False
    
    print(f"Found {len(teams)} unique teams:")
    for i, team in enumerate(teams, 1):
        print(f"  {i:2}. {team}")
    
    print("\nStarting logo download process...")
    
    # Create session for efficient requests
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    successful_downloads = 0
    failed_downloads = 0
    
    # Process each team
    for i, team_name in enumerate(teams, 1):
        print(f"\n[{i}/{len(teams)}] Processing: {team_name}")
        
        # Check if logo already exists
        safe_name = normalize_team_name(team_name)
        existing_files = [f for f in os.listdir(LOGOS_DIR) 
                         if f.startswith(safe_name) and 
                         any(f.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg'])]
        
        if existing_files:
            print(f"  → Logo already exists: {existing_files[0]}")
            successful_downloads += 1
            continue
        
        # Search for team logo
        logo_url = search_team_logo_on_flbb(team_name, session)
        
        if logo_url:
            print(f"  Found logo URL: {logo_url}")
            downloaded_file = download_logo(logo_url, team_name, session)
            if downloaded_file:
                successful_downloads += 1
            else:
                failed_downloads += 1
                create_default_logo(team_name)
        else:
            print(f"  ✗ No logo found for {team_name}")
            failed_downloads += 1
            create_default_logo(team_name)
    
    # Summary
    print(f"\n" + "=" * 40)
    print(f"Download Summary:")
    print(f"  Successful: {successful_downloads}")
    print(f"  Failed: {failed_downloads}")
    print(f"  Total teams: {len(teams)}")
    
    return successful_downloads > 0

if __name__ == "__main__":
    try:
        success = download_all_team_logos()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)