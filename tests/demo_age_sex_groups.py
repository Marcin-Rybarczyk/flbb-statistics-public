#!/usr/bin/env python3
"""
Demonstration script showing the age and sex group handling feature in action.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import extract_age_sex_group_from_division, get_team_name_with_group_suffix

def demo():
    print("\n" + "=" * 70)
    print(" 🏀 Age and Sex Group Handling Feature - Demonstration")
    print("=" * 70)
    
    # Sample teams
    teams = ["Racing Luxembourg", "AB Contern", "BC Mess", "Gréngewald Hueschtert"]
    
    # Sample divisions
    divisions = [
        ("M-Division 1:", "Current Men's Division"),
        ("M-ENOVOS LEAGUE:Tour qualificatif", "Current Men's Elite League"),
        ("W-Division 1", "Future Women's Division"),
        ("U18-Division 1", "Future Youth U18"),
        ("U16-Division 1", "Future Youth U16"),
        ("Damen-Division 1", "Future Women's Division (German)"),
    ]
    
    print("\n📊 Division Analysis")
    print("-" * 70)
    for division, description in divisions:
        info = extract_age_sex_group_from_division(division)
        print(f"\nDivision: {division}")
        print(f"  Description: {description}")
        print(f"  Detected: Sex={info['sex']}, Age Group={info['age_group']}")
    
    print("\n\n👥 Team Name Display Examples")
    print("-" * 70)
    
    for division, description in divisions:
        print(f"\n{description} ({division}):")
        print("-" * 70)
        for team in teams[:2]:  # Show 2 teams per division
            default_name = get_team_name_with_group_suffix(team, division, False)
            explicit_name = get_team_name_with_group_suffix(team, division, True)
            print(f"  {team:25} → {default_name:35} (include_default=False)")
            if default_name != explicit_name:
                print(f"  {' ':25}   {explicit_name:35} (include_default=True)")
    
    print("\n\n🎯 Key Behavior")
    print("-" * 70)
    print("✓ Men's divisions (default): No suffix added")
    print("✓ Women's divisions: '(Women)' suffix added")
    print("✓ Youth divisions: Age group suffix added (e.g., '(U18)')")
    print("✓ Original data remains unchanged")
    print("✓ Backward compatible with existing system")
    
    print("\n\n💡 Usage in Code")
    print("-" * 70)
    print("Python:")
    print("  from src.utils import get_team_name_with_group_suffix")
    print("  name = get_team_name_with_group_suffix(team, division, False)")
    print("\nJinja Template:")
    print("  {{ get_team_name_with_group_suffix(team_name, division, false) }}")
    
    print("\n" + "=" * 70)
    print(" ✅ Feature is ready for production use!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    demo()
