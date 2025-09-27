#!/usr/bin/env python3
"""
Test script to demonstrate enhanced logo URL patterns
including the FLBB theme directory pattern requested in the issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from download_team_logos import generate_team_codes, get_unique_teams, BASE_URL, normalize_team_name

def test_url_patterns():
    """Test the enhanced URL patterns for logo downloading"""
    print("Enhanced Logo URL Pattern Testing")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Issue example: {BASE_URL}/layout/themes/flbb/images/Logos/BAS.jpg")
    print()
    
    teams = get_unique_teams()
    print(f"Found {len(teams)} teams in the CSV data")
    print()
    
    for i, team_name in enumerate(teams, 1):
        print(f"[{i}] Team: {team_name}")
        normalized_name = normalize_team_name(team_name)
        team_codes = generate_team_codes(team_name)
        
        print(f"  Normalized name: {normalized_name}")
        print(f"  Generated codes: {team_codes}")
        print("  URL Patterns that will be tested:")
        
        # Show FLBB theme directory patterns (from issue)
        print("    FLBB Theme Directory Patterns:")
        for code in team_codes[:3]:  # Show first 3 codes
            print(f"      {BASE_URL}/layout/themes/flbb/images/Logos/{code}.jpg")
            print(f"      {BASE_URL}/layout/themes/flbb/images/Logos/{code}.png")
        
        # Show some standard patterns
        print("    Standard Pattern Examples:")
        print(f"      {BASE_URL}/logos/{normalized_name}.png")
        print(f"      {BASE_URL}/assets/logos/{normalized_name}.jpg")
        print()

def demonstrate_bas_example():
    """Demonstrate how the BAS example from the issue would work"""
    print("Demonstrating BAS Example from Issue")
    print("=" * 40)
    
    # The issue shows: https://www.luxembourg.basketball/layout/themes/flbb/images/Logos/BAS.jpg
    # Let's see which team might match "BAS"
    
    teams = get_unique_teams()
    print("Checking which teams might generate 'BAS' as a code:")
    
    found_bas = False
    for team in teams:
        codes = generate_team_codes(team)
        if 'BAS' in codes:
            print(f"  ✓ '{team}' generates code 'BAS'")
            found_bas = True
    
    if not found_bas:
        print("  ℹ  No current teams generate 'BAS' code")
        print("  ℹ  'BAS' might be from 'Basketball' or a team not in current data")
    
    print()
    print("Enhanced patterns now support this URL structure:")
    print(f"  {BASE_URL}/layout/themes/flbb/images/Logos/BAS.jpg")
    print(f"  {BASE_URL}/layout/themes/flbb/images/Logos/BAS.png")
    print()

if __name__ == "__main__":
    try:
        demonstrate_bas_example()
        test_url_patterns()
        
        print("Summary of Enhancements:")
        print("=" * 25)
        print("✓ Added support for FLBB theme directory pattern from issue")
        print("✓ Enhanced team code generation for better abbreviations")
        print("✓ Multiple code strategies for comprehensive logo search")
        print("✓ Maintains backward compatibility with existing patterns")
        print("✓ Verbose mode shows generated codes and tried URLs")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)