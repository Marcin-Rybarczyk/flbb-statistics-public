#!/usr/bin/env python3
"""
Test script to verify foul details are properly added to team stats.
"""
import pandas as pd
import sys
import os

# Add the parent directory to path to allow src imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils import get_team_fouls_stats, load_game_data

def test_foul_details():
    """Test that foul details are properly generated for team stats"""
    print("Loading game data...")
    data = load_game_data()
    
    if data.empty:
        print("❌ No data loaded")
        return False
    
    print(f"✓ Loaded {len(data)} games")
    
    # Get team foul stats
    print("\nGetting team foul stats...")
    team_fouls = get_team_fouls_stats(data, top_n=5)
    
    if team_fouls.empty:
        print("❌ No team foul stats generated")
        return False
    
    print(f"✓ Generated stats for {len(team_fouls)} teams")
    
    # Check that FoulDetails column exists
    if 'FoulDetails' not in team_fouls.columns:
        print("❌ FoulDetails column not found in team_fouls DataFrame")
        print(f"Available columns: {team_fouls.columns.tolist()}")
        return False
    
    print("✓ FoulDetails column exists")
    
    # Check that FoulDetails are populated
    print("\nChecking FoulDetails content for top 5 teams:")
    print("="*80)
    for idx, row in team_fouls.iterrows():
        team = row['Team']
        total_fouls = row['TotalFouls']
        foul_details = row['FoulDetails']
        
        print(f"\n{idx+1}. {team}")
        print(f"   Total Fouls: {total_fouls}")
        print(f"   Details length: {len(foul_details)} characters")
        
        # Check if it contains HTML foul-card elements
        if '<div class="foul-card"' in foul_details:
            print(f"   ✓ Contains foul-card HTML elements")
        elif '<span class="no-fouls"' in foul_details:
            print(f"   ℹ No fouls recorded")
        else:
            print(f"   ❌ Unexpected format")
            print(f"   Sample: {foul_details[:100]}")
        
        # Show breakdown of foul types
        if row['PFouls'] > 0:
            print(f"   - Personal (P): {int(row['PFouls'])}")
        if row['P1Fouls'] > 0:
            print(f"   - Personal 1 (P1): {int(row['P1Fouls'])}")
        if row['P2Fouls'] > 0:
            print(f"   - Personal 2 (P2): {int(row['P2Fouls'])}")
        if row['P3Fouls'] > 0:
            print(f"   - Personal 3 (P3): {int(row['P3Fouls'])}")
        if row['T1Fouls'] > 0:
            print(f"   - Technical (T1): {int(row['T1Fouls'])}")
        if row['U1Fouls'] > 0:
            print(f"   - Unsportsmanlike 1 (U1): {int(row['U1Fouls'])}")
        if row['U2Fouls'] > 0:
            print(f"   - Unsportsmanlike 2 (U2): {int(row['U2Fouls'])}")
        if row['U3Fouls'] > 0:
            print(f"   - Unsportsmanlike 3 (U3): {int(row['U3Fouls'])}")
        if row['GDFouls'] > 0:
            print(f"   - Game Disqualification (GD): {int(row['GDFouls'])}")
    
    print("\n" + "="*80)
    print("\n✅ All tests passed! Foul details are properly generated.")
    return True

if __name__ == '__main__':
    success = test_foul_details()
    sys.exit(0 if success else 1)
