#!/usr/bin/env python3
"""
Test script for age and sex group handling functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils import extract_age_sex_group_from_division, get_team_name_with_group_suffix

def test_extract_age_sex_group():
    """Test extraction of age/sex groups from division names."""
    print("=" * 60)
    print("Testing extract_age_sex_group_from_division()")
    print("=" * 60)
    
    test_cases = [
        # Current real divisions
        ("M-Division 1:", {'sex': 'M', 'age_group': 'Adult', 'raw_group': 'M'}),
        ("M-ENOVOS LEAGUE:Tour qualificatif", {'sex': 'M', 'age_group': 'Adult', 'raw_group': 'M'}),
        ("M-Nationale 2:Tour qualificatif", {'sex': 'M', 'age_group': 'Adult', 'raw_group': 'M'}),
        
        # Potential future divisions - Women
        ("W-Division 1", {'sex': 'W', 'age_group': 'Adult', 'raw_group': 'W'}),
        ("Damen-Division 1", {'sex': 'W', 'age_group': 'Adult', 'raw_group': 'W'}),
        ("Women Division 1", {'sex': 'W', 'age_group': 'Adult', 'raw_group': 'W'}),
        
        # Potential future divisions - Youth
        ("U18-Division 1", {'sex': None, 'age_group': 'U18', 'raw_group': 'U18'}),
        ("U16-Division 1", {'sex': None, 'age_group': 'U16', 'raw_group': 'U16'}),
        ("M-U18-Division 1", {'sex': 'M', 'age_group': 'U18', 'raw_group': 'U18'}),
        ("W-U16-Division 1", {'sex': 'W', 'age_group': 'U16', 'raw_group': 'U16'}),
        
        # Other age categories
        ("Cadets Division", {'sex': None, 'age_group': 'Cadets', 'raw_group': 'Cadets'}),
        ("Minimes Division", {'sex': None, 'age_group': 'Minimes', 'raw_group': 'Minimes'}),
        ("Juniors Division", {'sex': None, 'age_group': 'Juniors', 'raw_group': 'Juniors'}),
        
        # Edge cases
        (None, {'sex': None, 'age_group': 'Adult', 'raw_group': None}),
        ("", {'sex': None, 'age_group': 'Adult', 'raw_group': None}),
    ]
    
    passed = 0
    failed = 0
    
    for division, expected in test_cases:
        result = extract_age_sex_group_from_division(division)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status:8} | Division: {str(division):40} | Result: {result}")
        if result != expected:
            print(f"         | Expected: {expected}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_get_team_name_with_suffix():
    """Test adding suffixes to team names based on division."""
    print("\n" + "=" * 60)
    print("Testing get_team_name_with_group_suffix()")
    print("=" * 60)
    
    test_cases = [
        # Current divisions - should have no suffix by default
        ("Racing Luxembourg B", "M-Division 1:", False, "Racing Luxembourg B"),
        ("AB Contern", "M-ENOVOS LEAGUE:Tour qualificatif", False, "AB Contern"),
        
        # Current divisions - with include_default=True should add (Men)
        ("Racing Luxembourg B", "M-Division 1:", True, "Racing Luxembourg B (Men)"),
        
        # Women's divisions - should add (Women)
        ("Racing Luxembourg B", "W-Division 1", False, "Racing Luxembourg B (Women)"),
        ("AB Contern", "Damen-Division 1", False, "AB Contern (Women)"),
        
        # Youth divisions - should add age group
        ("CFBB", "U18-Division 1", False, "CFBB (U18)"),
        ("Racing Luxembourg", "U16-Division 1", False, "Racing Luxembourg (U16)"),
        ("BC Mess", "M-U18-Division 1", False, "BC Mess (U18)"),
        
        # Other age categories
        ("Amicale Steesel", "Cadets Division", False, "Amicale Steesel (Cadets)"),
        ("Basket Esch", "Minimes Division", False, "Basket Esch (Minimes)"),
        
        # Edge cases
        (None, "M-Division 1:", False, None),
        ("", "M-Division 1:", False, ""),
        ("Team A", None, False, "Team A"),
    ]
    
    passed = 0
    failed = 0
    
    for team_name, division, include_default, expected in test_cases:
        result = get_team_name_with_group_suffix(team_name, division, include_default)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status:8} | Team: {str(team_name):25} | Division: {str(division):30} | Result: {result}")
        if result != expected:
            print(f"         | Expected: {expected}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_with_real_data():
    """Test with real data from CSV."""
    print("\n" + "=" * 60)
    print("Testing with Real Data")
    print("=" * 60)
    
    try:
        import pandas as pd
        df = pd.read_csv('data/full-game-stats.csv', encoding='utf-8-sig')
        
        # Get unique combinations of teams and divisions
        home_combos = df[['HomeTeamName', 'GameDivisionDisplay']].drop_duplicates().head(10)
        
        print("\nSample team names with group suffixes (include_default=False):")
        print("-" * 60)
        for _, row in home_combos.iterrows():
            team = row['HomeTeamName']
            division = row['GameDivisionDisplay']
            with_suffix = get_team_name_with_group_suffix(team, division, include_default=False)
            print(f"  {team:30} → {with_suffix}")
        
        print("\nSample team names with group suffixes (include_default=True):")
        print("-" * 60)
        for _, row in home_combos.iterrows():
            team = row['HomeTeamName']
            division = row['GameDivisionDisplay']
            with_suffix = get_team_name_with_group_suffix(team, division, include_default=True)
            print(f"  {team:30} → {with_suffix}")
        
        return True
    except Exception as e:
        print(f"Error testing with real data: {e}")
        return False


if __name__ == "__main__":
    print("\n🏀 Age and Sex Group Handling Tests\n")
    
    test1 = test_extract_age_sex_group()
    test2 = test_get_team_name_with_suffix()
    test3 = test_with_real_data()
    
    print("\n" + "=" * 60)
    print("Overall Test Results")
    print("=" * 60)
    
    all_passed = test1 and test2 and test3
    
    if all_passed:
        print("✓ All tests PASSED")
        sys.exit(0)
    else:
        print("✗ Some tests FAILED")
        sys.exit(1)
