#!/usr/bin/env python3
"""
Team Logo Downloader for FLBB Statistics

This script downloads team logos from the Luxembourg Basketball Federation (FLBB) website
and stores them in the logos directory for use in the web application.

Enhanced Features:
- Supports FLBB theme directory pattern: /layout/themes/flbb/images/Logos/{CODE}.jpg
- Intelligent team code generation for better logo matching
- Multiple URL pattern strategies for comprehensive coverage
- Force re-download option for updating existing logos
- Verbose debugging mode with detailed URL attempt logging

URL Patterns Supported:
1. FLBB Theme Directory (from issue request):
   - /layout/themes/flbb/images/Logos/{TEAM_CODE}.jpg
   - /layout/themes/flbb/images/logos/{TEAM_CODE}.png
   
2. Standard Asset Directories:
   - /assets/logos/{normalized_name}.png
   - /images/logos/{normalized_name}.jpg
   - /logos/{normalized_name}.png

3. Team Page Extraction:
   - /equipe/{normalized_name}
   - /club/{normalized_name}
   - /teams/{normalized_name}

Team Code Generation:
- First letters of significant words (ignoring A, B, C, D levels)
- Full abbreviations including team levels
- First word + team level combinations
- First 3 letters of primary word
- Common basketball team abbreviations (RAC, AMI, BBC, etc.)

Usage Examples:
    python3 download_team_logos.py                    # Normal mode
    python3 download_team_logos.py --verbose          # Show detailed URL attempts
    python3 download_team_logos.py --force            # Re-download existing logos
    python3 download_team_logos.py --verbose --force  # Verbose + force mode
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

# Extended configuration for enhanced functionality
TIMEOUT_SECONDS = 15
MAX_IMAGE_SIZE_MB = 10  # Maximum logo file size in MB
MIN_IMAGE_SIZE_KB = 1   # Minimum logo file size in KB

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

def generate_team_codes(team_name):
    """Generate possible team codes/abbreviations for logo URLs"""
    codes = []
    
    # Clean team name for processing
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', team_name)
    words = clean_name.split()
    
    # Strategy 1: First letter of each significant word
    main_words = [w for w in words if w.upper() not in ['A', 'B', 'C', 'D', 'THE']]
    if main_words:
        codes.append(''.join([w[0].upper() for w in main_words]))
    
    # Strategy 2: All first letters including team level (A, B, C, D)
    codes.append(''.join([w[0].upper() for w in words]))
    
    # Strategy 3: Full first word + level
    if len(words) >= 2:
        codes.append(words[0].upper() + words[-1].upper())
    
    # Strategy 4: First 3 letters of first word
    if words:
        codes.append(words[0][:3].upper())
    
    # Strategy 5: Common basketball abbreviations
    team_mappings = {
        'RACING': ['RAC', 'RACING'],
        'AMICALE': ['AMI', 'AMIC'],
        'BBC': ['BBC'],
        'BASKETBALL': ['BAS', 'BB'],
        'CONTERN': ['CON'],
        'GRENGEWALD': ['GRE', 'GREN'],
        'HOSTERT': ['HOS'],
        'MAMER': ['MAM'],
        'SCHIEREN': ['SCH'],
        'SPARTA': ['SPA'],
        'MESS': ['MES']
    }
    
    for word in words:
        word_upper = word.upper()
        if word_upper in team_mappings:
            codes.extend(team_mappings[word_upper])
    
    # Remove duplicates while preserving order
    unique_codes = []
    for code in codes:
        if code and code not in unique_codes:
            unique_codes.append(code)
    
    return unique_codes

def search_team_logo_on_flbb(team_name, session, verbose=False):
    """
    Search for team logo on FLBB website using multiple comprehensive strategies
    Returns the logo URL if found, None otherwise
    """
    normalized_name = normalize_team_name(team_name)
    
    if verbose:
        print(f"  Searching for logo for '{team_name}' (normalized: '{normalized_name}')")
    
    # Strategy 1: Try direct team page URL patterns
    # Based on common basketball website structures
    possible_urls = [
        # Direct team pages
        f"{BASE_URL}/equipe/{normalized_name}",
        f"{BASE_URL}/club/{normalized_name}", 
        f"{BASE_URL}/teams/{normalized_name}",
        f"{BASE_URL}/team/{normalized_name}",
        
        # Alternative URL structures
        f"{BASE_URL}/clubs/{normalized_name}",
        f"{BASE_URL}/equipes/{normalized_name}",
        
        # With potential ID patterns
        f"{BASE_URL}/equipe/{normalized_name}.html",
        f"{BASE_URL}/club/{normalized_name}.html",
        
        # Category-based patterns
        f"{BASE_URL}/c/equipe/{normalized_name}",
        f"{BASE_URL}/c/club/{normalized_name}",
    ]
    
    for url in possible_urls:
        try:
            time.sleep(REQUEST_DELAY)
            if verbose:
                print(f"    Trying: {url}")
            response = session.get(url, timeout=15, allow_redirects=True)
            if response.status_code == 200:
                logo_url = extract_logo_from_page(response.text, team_name, verbose)
                if logo_url:
                    if verbose:
                        print(f"    ✓ Found logo at: {logo_url}")
                    return logo_url
            elif verbose:
                print(f"    Status: {response.status_code}")
        except Exception as e:
            if verbose:
                print(f"    Error: {e}")
            continue
    
    # Strategy 2: Search through category and listing pages
    search_urls = [
        f"{BASE_URL}/c/categorie/all",
        f"{BASE_URL}/categories",
        f"{BASE_URL}/equipes",
        f"{BASE_URL}/clubs",
        f"{BASE_URL}/teams",
        f"{BASE_URL}/search?q={quote(team_name)}",
        f"{BASE_URL}/recherche?q={quote(team_name)}",
        f"{BASE_URL}/?s={quote(team_name)}",
    ]
    
    for url in search_urls:
        try:
            time.sleep(REQUEST_DELAY)
            if verbose:
                print(f"    Searching in: {url}")
            response = session.get(url, timeout=15)
            if response.status_code == 200:
                logo_url = extract_logo_from_search_page(response.text, team_name, verbose)
                if logo_url:
                    if verbose:
                        print(f"    ✓ Found logo in search: {logo_url}")
                    return logo_url
        except Exception as e:
            if verbose:
                print(f"    Search error: {e}")
            continue
    
    # Strategy 3: Try to find logos in common asset directories
    asset_patterns = []
    
    # Generate possible team codes
    team_codes = generate_team_codes(team_name)
    if verbose:
        print(f"    Generated team codes: {team_codes}")
    
    # Add patterns with team codes for FLBB-specific theme directory (from issue requirement)
    for code in team_codes:
        asset_patterns.extend([
            f"{BASE_URL}/layout/themes/flbb/images/Logos/{code}.jpg",
            f"{BASE_URL}/layout/themes/flbb/images/Logos/{code}.png",
            f"{BASE_URL}/layout/themes/flbb/images/logos/{code}.jpg",
            f"{BASE_URL}/layout/themes/flbb/images/logos/{code}.png",
        ])
    
    # Add patterns with normalized name for FLBB theme directory
    asset_patterns.extend([
        f"{BASE_URL}/layout/themes/flbb/images/Logos/{normalized_name.upper()}.jpg",
        f"{BASE_URL}/layout/themes/flbb/images/Logos/{normalized_name.upper()}.png",
        f"{BASE_URL}/layout/themes/flbb/images/logos/{normalized_name}.jpg",
        f"{BASE_URL}/layout/themes/flbb/images/logos/{normalized_name}.png",
    ])
    
    # Standard asset directories with normalized name
    asset_patterns.extend([
        f"{BASE_URL}/assets/logos/{normalized_name}.png",
        f"{BASE_URL}/assets/logos/{normalized_name}.jpg",
        f"{BASE_URL}/assets/images/logos/{normalized_name}.png",
        f"{BASE_URL}/assets/images/logos/{normalized_name}.jpg",
        f"{BASE_URL}/images/logos/{normalized_name}.png",
        f"{BASE_URL}/images/logos/{normalized_name}.jpg",
        f"{BASE_URL}/logo/{normalized_name}.png",
        f"{BASE_URL}/logo/{normalized_name}.jpg",
        f"{BASE_URL}/logos/{normalized_name}.png",
        f"{BASE_URL}/logos/{normalized_name}.jpg",
    ])
    
    for logo_url in asset_patterns:
        try:
            time.sleep(REQUEST_DELAY / 2)  # Faster for direct asset checks
            if verbose:
                print(f"    Checking asset: {logo_url}")
            response = session.head(logo_url, timeout=10)  # HEAD request to check if exists
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'image' in content_type:
                    if verbose:
                        print(f"    ✓ Found direct asset: {logo_url}")
                    return logo_url
        except Exception as e:
            if verbose:
                print(f"    Asset check error: {e}")
            continue
    
    return None

def extract_logo_from_page(html_content, team_name, verbose=False):
    """Extract logo URL from team page HTML with comprehensive pattern matching"""
    if verbose:
        print(f"    Analyzing HTML content for '{team_name}' (length: {len(html_content)} chars)")
    
    # More comprehensive logo patterns
    patterns = [
        # Standard logo class patterns
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*logo[^"\']*["\']',
        r'<img[^>]+class=["\'][^"\']*logo[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
        
        # Team-specific patterns with team name
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\'][^"\']*' + re.escape(team_name.lower()) + r'[^"\']*["\']',
        r'<img[^>]+alt=["\'][^"\']*' + re.escape(team_name.lower()) + r'[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
        
        # General logo patterns (more permissive)
        r'<img[^>]+src=["\']([^"\']+logo[^"\']*)["\']',
        r'<img[^>]+src=["\']([^"\']*logo[^"\']+)["\']',
        
        # Common CSS classes for team logos
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*team-logo[^"\']*["\']',
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*club-logo[^"\']*["\']',
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*equipe-logo[^"\']*["\']',
        
        # Data attributes
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*data-[^=]*=["\'][^"\']*logo[^"\']*["\']',
        
        # Background image patterns in CSS
        r'background-image:\s*url\(["\']?([^"\'()]+)["\']?\)',
        
        # Team name in file path
        r'<img[^>]+src=["\']([^"\']*' + re.escape(normalize_team_name(team_name)) + r'[^"\']*\.(png|jpg|jpeg|gif|svg))["\']',
    ]
    
    found_images = []
    
    for i, pattern in enumerate(patterns):
        try:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # Handle tuple results from groups
                img_url = match if isinstance(match, str) else match[0]
                
                if img_url and is_valid_logo_url(img_url):
                    full_url = urljoin(BASE_URL, img_url)
                    found_images.append((full_url, f"pattern_{i+1}"))
                    if verbose:
                        print(f"    Found potential logo with pattern {i+1}: {full_url}")
        except Exception as e:
            if verbose:
                print(f"    Pattern {i+1} error: {e}")
            continue
    
    # Score and rank found images
    if found_images:
        scored_images = []
        for img_url, source in found_images:
            score = score_logo_url(img_url, team_name)
            scored_images.append((score, img_url, source))
            if verbose:
                print(f"    Scored {score}: {img_url} (from {source})")
        
        # Return the highest-scored logo
        scored_images.sort(reverse=True, key=lambda x: x[0])
        best_score, best_url, best_source = scored_images[0]
        if verbose:
            print(f"    Best match (score {best_score}): {best_url} from {best_source}")
        return best_url
    
    return None

def is_valid_logo_url(url):
    """Check if URL looks like a valid logo image"""
    if not url:
        return False
    
    # Must be an image file
    if not any(ext in url.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']):
        return False
    
    # Exclude common non-logo images
    exclude_patterns = [
        'banner', 'header', 'footer', 'background', 'bg', 
        'icon', 'button', 'arrow', 'social', 'facebook', 'twitter',
        'instagram', 'youtube', 'linkedin', 'sponsor', 'partner'
    ]
    
    url_lower = url.lower()
    for pattern in exclude_patterns:
        if pattern in url_lower:
            return False
    
    return True

def score_logo_url(url, team_name):
    """Score a logo URL based on how likely it is to be the team's official logo"""
    score = 0
    url_lower = url.lower()
    team_normalized = normalize_team_name(team_name).lower()
    
    # Higher score for URLs containing team name
    if team_normalized in url_lower:
        score += 50
    
    # Score based on file path indicators
    if 'logo' in url_lower:
        score += 30
    if 'equipe' in url_lower or 'team' in url_lower or 'club' in url_lower:
        score += 20
    
    # Prefer certain file formats
    if url_lower.endswith('.png'):
        score += 15
    elif url_lower.endswith('.svg'):
        score += 10
    elif url_lower.endswith(('.jpg', '.jpeg')):
        score += 5
    
    # Prefer logos directory
    if '/logo' in url_lower or '/logos' in url_lower:
        score += 25
    
    # Prefer reasonable file sizes (avoid tiny icons or huge banners)
    # This is heuristic based on filename patterns
    if any(size in url_lower for size in ['thumb', 'small', 'mini']):
        score -= 10
    if any(size in url_lower for size in ['large', 'banner', 'hero']):
        score -= 5
    
    return score

def extract_logo_from_search_page(html_content, team_name, verbose=False):
    """Extract logo URL from search results or category pages with improved matching"""
    if verbose:
        print(f"    Analyzing search page for '{team_name}' (length: {len(html_content)} chars)")
    
    team_normalized = normalize_team_name(team_name).lower()
    team_words = team_name.lower().split()
    
    # Look for team cards, listings, or directory entries
    patterns = [
        # Team card or listing patterns with logo
        r'<div[^>]*class=["\'][^"\']*team[^"\']*["\'][^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'][^>]*>.*?' + re.escape(team_name) + r'.*?</div>',
        r'<div[^>]*class=["\'][^"\']*club[^"\']*["\'][^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'][^>]*>.*?' + re.escape(team_name) + r'.*?</div>',
        r'<div[^>]*class=["\'][^"\']*equipe[^"\']*["\'][^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'][^>]*>.*?' + re.escape(team_name) + r'.*?</div>',
        
        # List item patterns
        r'<li[^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'][^>]*>.*?' + re.escape(team_name) + r'.*?</li>',
        
        # Table row patterns  
        r'<tr[^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'][^>]*>.*?' + re.escape(team_name) + r'.*?</tr>',
        
        # Article or section patterns
        r'<article[^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'][^>]*>.*?' + re.escape(team_name) + r'.*?</article>',
        r'<section[^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'][^>]*>.*?' + re.escape(team_name) + r'.*?</section>',
    ]
    
    found_logos = []
    
    # Try pattern matching
    for i, pattern in enumerate(patterns):
        try:
            matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if is_valid_logo_url(match):
                    full_url = urljoin(BASE_URL, match)
                    found_logos.append((full_url, f"search_pattern_{i+1}"))
                    if verbose:
                        print(f"    Found via search pattern {i+1}: {full_url}")
        except Exception as e:
            if verbose:
                print(f"    Search pattern {i+1} error: {e}")
            continue
    
    # Alternative approach: find all images near team name mentions
    team_mentions = []
    for word in team_words:
        pattern = r'(' + re.escape(word) + r')'
        matches = [(m.start(), m.end()) for m in re.finditer(pattern, html_content, re.IGNORECASE)]
        team_mentions.extend(matches)
    
    if team_mentions and verbose:
        print(f"    Found {len(team_mentions)} team name mentions")
    
    # Look for images within reasonable distance of team name mentions
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
    img_matches = [(m.start(), m.end(), m.group(1)) for m in re.finditer(img_pattern, html_content, re.IGNORECASE)]
    
    for mention_start, mention_end in team_mentions:
        for img_start, img_end, img_src in img_matches:
            distance = min(abs(img_start - mention_end), abs(mention_start - img_end))
            if distance < 1000 and is_valid_logo_url(img_src):  # Within 1000 characters
                full_url = urljoin(BASE_URL, img_src)
                found_logos.append((full_url, f"proximity_match_dist_{distance}"))
                if verbose:
                    print(f"    Found via proximity (distance {distance}): {full_url}")
    
    # Score and return best match
    if found_logos:
        scored_logos = []
        for logo_url, source in found_logos:
            score = score_logo_url(logo_url, team_name)
            scored_logos.append((score, logo_url, source))
            if verbose:
                print(f"    Scored {score}: {logo_url} (from {source})")
        
        # Remove duplicates and sort by score
        seen_urls = set()
        unique_logos = []
        for score, url, source in scored_logos:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_logos.append((score, url, source))
        
        unique_logos.sort(reverse=True, key=lambda x: x[0])
        
        if unique_logos:
            best_score, best_url, best_source = unique_logos[0]
            if verbose:
                print(f"    Best search match (score {best_score}): {best_url} from {best_source}")
            return best_url
    
    return None

def download_logo(logo_url, team_name, session):
    """Download logo from URL and save to logos directory with enhanced validation"""
    try:
        time.sleep(REQUEST_DELAY)
        response = session.get(logo_url, timeout=TIMEOUT_SECONDS, stream=True)
        response.raise_for_status()
        
        # Check content length
        content_length = response.headers.get('content-length')
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > MAX_IMAGE_SIZE_MB:
                print(f"  ✗ Logo too large ({size_mb:.1f}MB > {MAX_IMAGE_SIZE_MB}MB)")
                return None
        
        # Read content
        content = response.content
        content_size_kb = len(content) / 1024
        
        if content_size_kb < MIN_IMAGE_SIZE_KB:
            print(f"  ✗ Logo too small ({content_size_kb:.1f}KB < {MIN_IMAGE_SIZE_KB}KB)")
            return None
        
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
        
        # Validate image content (basic check)
        if not is_valid_image_content(content, ext):
            print(f"  ✗ Invalid image content detected")
            return None
        
        # Save logo
        with open(filepath, 'wb') as f:
            f.write(content)
        
        print(f"  ✓ Downloaded: {filename} ({content_size_kb:.1f}KB)")
        return filepath
        
    except Exception as e:
        print(f"  ✗ Failed to download logo: {e}")
        return None

def is_valid_image_content(content, ext):
    """Basic validation of image content"""
    if len(content) < 100:  # Too small to be a valid image
        return False
    
    # Check magic bytes for common image formats
    if ext.lower() == '.png':
        return content.startswith(b'\x89PNG\r\n\x1a\n')
    elif ext.lower() in ['.jpg', '.jpeg']:
        return content.startswith(b'\xff\xd8\xff')
    elif ext.lower() == '.gif':
        return content.startswith(b'GIF87a') or content.startswith(b'GIF89a')
    elif ext.lower() == '.svg':
        try:
            content_str = content.decode('utf-8', errors='ignore')
            return '<svg' in content_str.lower() and '</svg>' in content_str.lower()
        except:
            return False
    
    return True  # Unknown format, assume valid

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

def download_all_team_logos(verbose=False):
    """Main function to download logos for all teams"""
    print("FLBB Team Logo Downloader - Enhanced Version")
    print("=" * 50)
    
    # Setup
    create_logos_directory()
    teams = get_unique_teams()
    
    if not teams:
        print("No teams found in data!")
        return False
    
    print(f"Found {len(teams)} unique teams:")
    for i, team in enumerate(teams, 1):
        print(f"  {i:2}. {team}")
    
    print(f"\nStarting logo download process (verbose={'ON' if verbose else 'OFF'})...")
    
    # Create session for efficient requests
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    successful_downloads = 0
    failed_downloads = 0
    skipped_existing = 0
    
    # Process each team
    for i, team_name in enumerate(teams, 1):
        print(f"\n[{i}/{len(teams)}] Processing: {team_name}")
        print("-" * 40)
        
        # Check if logo already exists
        safe_name = normalize_team_name(team_name)
        existing_files = [f for f in os.listdir(LOGOS_DIR) 
                         if f.startswith(safe_name) and 
                         any(f.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg'])]
        
        if existing_files:
            print(f"  → Logo already exists: {existing_files[0]}")
            skipped_existing += 1
            successful_downloads += 1  # Count as successful for summary
            continue
        
        # Search for team logo with enhanced functionality
        try:
            logo_url = search_team_logo_on_flbb(team_name, session, verbose)
            
            if logo_url:
                print(f"  ✓ Found logo URL: {logo_url}")
                downloaded_file = download_logo(logo_url, team_name, session)
                if downloaded_file:
                    successful_downloads += 1
                    print(f"  ✓ Successfully downloaded: {os.path.basename(downloaded_file)}")
                else:
                    failed_downloads += 1
                    print(f"  ✗ Download failed, creating placeholder")
                    create_default_logo(team_name)
            else:
                print(f"  ✗ No logo found for {team_name}")
                failed_downloads += 1
                create_default_logo(team_name)
                
        except Exception as e:
            print(f"  ✗ Error processing {team_name}: {e}")
            failed_downloads += 1
            create_default_logo(team_name)
    
    # Summary
    print(f"\n" + "=" * 50)
    print(f"Download Summary:")
    print(f"  Total teams processed: {len(teams)}")
    print(f"  Already had logos: {skipped_existing}")
    print(f"  Successfully downloaded: {successful_downloads - skipped_existing}")
    print(f"  Failed downloads: {failed_downloads}")
    print(f"  Overall success rate: {(successful_downloads / len(teams) * 100):.1f}%")
    
    if verbose and failed_downloads > 0:
        print(f"\nTroubleshooting tips:")
        print(f"  - Check network connectivity to {BASE_URL}")
        print(f"  - Verify team names match website structure")
        print(f"  - Consider running with --verbose for detailed debug info")
    
    return successful_downloads > 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Download team logos from FLBB website',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 download_team_logos.py                    # Normal mode
  python3 download_team_logos.py --verbose          # Detailed output
  python3 download_team_logos.py --force            # Re-download existing logos
  python3 download_team_logos.py --verbose --force  # Verbose + force mode
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable detailed debug output')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Re-download logos even if they already exist')
    
    args = parser.parse_args()
    
    # Remove existing logos if force mode is enabled
    if args.force:
        print("Force mode enabled - removing existing logos...")
        import glob
        existing_logos = glob.glob(os.path.join(LOGOS_DIR, "*.png")) + \
                        glob.glob(os.path.join(LOGOS_DIR, "*.jpg")) + \
                        glob.glob(os.path.join(LOGOS_DIR, "*.jpeg")) + \
                        glob.glob(os.path.join(LOGOS_DIR, "*.gif")) + \
                        glob.glob(os.path.join(LOGOS_DIR, "*.svg"))
        
        for logo_file in existing_logos:
            try:
                os.remove(logo_file)
                if args.verbose:
                    print(f"  Removed: {os.path.basename(logo_file)}")
            except Exception as e:
                print(f"  Failed to remove {logo_file}: {e}")
        
        print(f"Removed {len(existing_logos)} existing logo files\n")
    
    try:
        success = download_all_team_logos(verbose=args.verbose)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)