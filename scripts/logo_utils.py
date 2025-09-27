#!/usr/bin/env python3
"""
Team Logo Utility Functions

This module provides utility functions for working with team logos in the FLBB Statistics application.
"""

import os
import re
from pathlib import Path

LOGOS_DIR = "logos"

def normalize_team_name(team_name):
    """Normalize team name for file naming (same as used in logo creation)"""
    if not team_name:
        return ""
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', str(team_name))
    normalized = normalized.lower().replace(' ', '-')
    return normalized

def get_team_logo_path(team_name, relative_path=True):
    """
    Get the logo file path for a given team name.
    
    Args:
        team_name (str): The team name (e.g., "Racing C", "Amicale B")
        relative_path (bool): If True, return relative path, else absolute
        
    Returns:
        str: Path to the logo file, or None if not found
    """
    if not team_name:
        return None
        
    normalized_name = normalize_team_name(team_name)
    
    # Check for PNG files (our standard format)
    png_path = os.path.join(LOGOS_DIR, f"{normalized_name}.png")
    if os.path.exists(png_path):
        return png_path if not relative_path else f"{LOGOS_DIR}/{normalized_name}.png"
    
    # Check for other formats
    for ext in ['.jpg', '.jpeg', '.gif', '.svg']:
        logo_path = os.path.join(LOGOS_DIR, f"{normalized_name}{ext}")
        if os.path.exists(logo_path):
            return logo_path if not relative_path else f"{LOGOS_DIR}/{normalized_name}{ext}"
    
    # Special case for Racing teams - check RAC.jpg
    if 'racing' in normalized_name.lower():
        rac_path = os.path.join(LOGOS_DIR, "RAC.jpg")
        if os.path.exists(rac_path):
            return rac_path if not relative_path else f"{LOGOS_DIR}/RAC.jpg"
    
    return None

def get_all_team_logos():
    """
    Get a mapping of all available team logos.
    
    Returns:
        dict: Dictionary mapping team names to logo paths
    """
    logo_mapping = {}
    
    if not os.path.exists(LOGOS_DIR):
        return logo_mapping
    
    # Get all logo files
    logo_files = [f for f in os.listdir(LOGOS_DIR) 
                 if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]
    
    for logo_file in logo_files:
        # Extract team name from filename
        name_part = os.path.splitext(logo_file)[0]
        
        # Convert back to display format
        if name_part == "RAC":
            # Special case for RAC.jpg - could represent Racing C or Racing D
            display_names = ["Racing C", "Racing D"]
            for display_name in display_names:
                logo_mapping[display_name] = f"{LOGOS_DIR}/{logo_file}"
        else:
            # Convert normalized name back to display format
            display_name = name_part.replace('-', ' ').title()
            logo_mapping[display_name] = f"{LOGOS_DIR}/{logo_file}"
    
    return logo_mapping

def list_available_logos():
    """Print all available team logos"""
    print("Available Team Logos:")
    print("=" * 30)
    
    logo_mapping = get_all_team_logos()
    if not logo_mapping:
        print("No logos found!")
        return
    
    for team_name, logo_path in sorted(logo_mapping.items()):
        print(f"  {team_name:<25} -> {logo_path}")
    
    print(f"\nTotal logos: {len(set(logo_mapping.values()))}")
    print(f"Team mappings: {len(logo_mapping)}")

def test_team_logo_mapping(csv_file="data/full-game-stats.csv"):
    """Test logo mapping against actual team names in data"""
    try:
        import pandas as pd
        df = pd.read_csv(csv_file)
        home_teams = set(df['HomeTeamName'].dropna().unique())
        away_teams = set(df['AwayTeamName'].dropna().unique())
        all_teams = sorted(home_teams.union(away_teams))
        
        print("Team Logo Mapping Test:")
        print("=" * 40)
        
        found_logos = 0
        missing_logos = []
        
        for team_name in all_teams:
            logo_path = get_team_logo_path(team_name)
            if logo_path:
                print(f"  ✓ {team_name:<25} -> {logo_path}")
                found_logos += 1
            else:
                print(f"  ✗ {team_name:<25} -> NO LOGO FOUND")
                missing_logos.append(team_name)
        
        print(f"\nSummary:")
        print(f"  Teams with logos: {found_logos}/{len(all_teams)}")
        print(f"  Coverage: {found_logos/len(all_teams)*100:.1f}%")
        
        if missing_logos:
            print(f"  Missing logos for: {', '.join(missing_logos)}")
        else:
            print(f"  ✓ All teams have logos!")
            
    except Exception as e:
        print(f"Error testing logo mapping: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_available_logos()
        elif sys.argv[1] == "test":
            test_team_logo_mapping()
        elif sys.argv[1] == "check":
            # Check specific team
            if len(sys.argv) > 2:
                team_name = " ".join(sys.argv[2:])
                logo_path = get_team_logo_path(team_name)
                if logo_path:
                    print(f"Logo for '{team_name}': {logo_path}")
                else:
                    print(f"No logo found for '{team_name}'")
            else:
                print("Usage: python logo_utils.py check <team name>")
        else:
            print("Usage: python logo_utils.py [list|test|check <team name>]")
    else:
        # Default: run test
        test_team_logo_mapping()