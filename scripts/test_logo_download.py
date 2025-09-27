#!/usr/bin/env python3
"""
Test utility for FLBB logo downloading functionality

This script helps test and debug the logo download process by allowing
testing of specific teams or URL patterns without modifying the main script.
"""

import os
import sys
import requests
import time
from urllib.parse import urljoin, quote

# Add the scripts directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from download_team_logos import (
    BASE_URL, normalize_team_name, search_team_logo_on_flbb,
    extract_logo_from_page, score_logo_url, is_valid_logo_url
)

def test_single_team(team_name, verbose=True):
    """Test logo downloading for a single team"""
    print(f"Testing logo download for: {team_name}")
    print("=" * 50)
    
    # Create session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        logo_url = search_team_logo_on_flbb(team_name, session, verbose=verbose)
        if logo_url:
            print(f"\n✓ SUCCESS: Found logo at {logo_url}")
            return True
        else:
            print(f"\n✗ FAILED: No logo found for {team_name}")
            return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False

def test_url_pattern(url):
    """Test a specific URL to see if it contains a logo"""
    print(f"Testing URL pattern: {url}")
    print("=" * 50)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        response = session.get(url, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)} characters")
        print(f"Content Type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            # Try to extract logos from the page
            logo_url = extract_logo_from_page(response.text, "test_team", verbose=True)
            if logo_url:
                print(f"\n✓ Found logo: {logo_url}")
                return True
            else:
                print(f"\n✗ No logos found on page")
                
                # Show some sample content to help debug
                content_preview = response.text[:1000]
                print(f"\nPage content preview (first 1000 chars):")
                print("-" * 40)
                print(content_preview)
                print("...")
                return False
        else:
            print(f"\n✗ URL not accessible (status {response.status_code})")
            return False
            
    except Exception as e:
        print(f"\n✗ Error accessing URL: {e}")
        return False

def list_potential_urls(team_name):
    """Generate and display potential URLs for a team"""
    print(f"Potential URLs for team: {team_name}")
    print("=" * 50)
    
    normalized_name = normalize_team_name(team_name)
    
    urls = [
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
        
        # Search URLs
        f"{BASE_URL}/search?q={quote(team_name)}",
        f"{BASE_URL}/recherche?q={quote(team_name)}",
        
        # Asset patterns
        f"{BASE_URL}/assets/logos/{normalized_name}.png",
        f"{BASE_URL}/assets/logos/{normalized_name}.jpg",
        f"{BASE_URL}/logos/{normalized_name}.png",
        f"{BASE_URL}/logos/{normalized_name}.jpg",
    ]
    
    for i, url in enumerate(urls, 1):
        print(f"{i:2}. {url}")
    
    return urls

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test FLBB logo downloading functionality',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_logo_download.py --team "Racing C"                # Test specific team
  python3 test_logo_download.py --url "https://example.com"      # Test specific URL
  python3 test_logo_download.py --list-urls "Amicale B"          # List potential URLs
  python3 test_logo_download.py --team "Racing C" --quiet        # Less verbose output
        """
    )
    
    parser.add_argument('--team', '-t', type=str,
                        help='Test logo download for specific team name')
    parser.add_argument('--url', '-u', type=str,
                        help='Test specific URL for logo extraction')
    parser.add_argument('--list-urls', '-l', type=str,
                        help='List potential URLs for a team name')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Less verbose output')
    
    args = parser.parse_args()
    
    if not any([args.team, args.url, args.list_urls]):
        parser.print_help()
        print("\nError: Must specify --team, --url, or --list-urls")
        sys.exit(1)
    
    verbose = not args.quiet
    
    try:
        if args.team:
            success = test_single_team(args.team, verbose=verbose)
            sys.exit(0 if success else 1)
        
        elif args.url:
            success = test_url_pattern(args.url)
            sys.exit(0 if success else 1)
        
        elif args.list_urls:
            list_potential_urls(args.list_urls)
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()