#!/usr/bin/env python3
"""
Test that PNG logos are prioritized over JPG when both exist.

This test verifies the fix for the issue where PNG files (with uppercase .PNG extension)
were not being detected, causing the system to use JPG files even when PNG versions
were available.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.logo_utils import get_team_logo_path


def test_png_priority():
    """Test that PNG files are prioritized over JPG files"""
    print("\n" + "="*70)
    print("Testing PNG prioritization over JPG")
    print("="*70)
    
    # Teams known to have both PNG and JPG versions
    teams_with_both = [
        "Racing Luxembourg",
        "Racing Luxembourg B",
        "Racing Luxembourg C",
        "Racing Luxembourg D",
        "AB Contern",
        "AB Contern B",
        "AB Contern C",
        "Amicale Steesel",
        "Basket Esch",
    ]
    
    all_passed = True
    for team_name in teams_with_both:
        logo_path = get_team_logo_path(team_name)
        
        if logo_path is None:
            print(f"❌ '{team_name}' -> NO LOGO FOUND")
            all_passed = False
            continue
        
        # Check if PNG is being used
        is_png = logo_path.endswith('.PNG') or logo_path.endswith('.png')
        is_jpg = logo_path.endswith('.jpg') or logo_path.endswith('.JPG')
        
        if is_png:
            print(f"✅ '{team_name}' -> {logo_path}")
        elif is_jpg:
            print(f"❌ '{team_name}' -> {logo_path} (SHOULD BE PNG!)")
            all_passed = False
        else:
            print(f"⚠️  '{team_name}' -> {logo_path} (unexpected format)")
    
    return all_passed


def test_jpg_fallback():
    """Test that JPG is still used when PNG is not available"""
    print("\n" + "="*70)
    print("Testing JPG fallback for teams without PNG")
    print("="*70)
    
    # Teams known to only have JPG versions
    teams_jpg_only = [
        "BBC Dikrich",
        "BBC East Side Pirates",
        "BBC Kaldall",
        "Etzella Ettelbruck",
    ]
    
    all_passed = True
    for team_name in teams_jpg_only:
        logo_path = get_team_logo_path(team_name)
        
        if logo_path is None:
            print(f"❌ '{team_name}' -> NO LOGO FOUND")
            all_passed = False
            continue
        
        # Should be JPG
        is_jpg = logo_path.endswith('.jpg') or logo_path.endswith('.JPG')
        
        if is_jpg:
            print(f"✅ '{team_name}' -> {logo_path}")
        else:
            print(f"⚠️  '{team_name}' -> {logo_path} (expected JPG)")
    
    return all_passed


def test_case_insensitivity():
    """Test that both .png and .PNG extensions are checked"""
    print("\n" + "="*70)
    print("Testing case-insensitive PNG detection")
    print("="*70)
    
    # The actual files have .PNG (uppercase)
    team = "Racing Luxembourg"
    logo_path = get_team_logo_path(team)
    
    if logo_path and (logo_path.endswith('.PNG') or logo_path.endswith('.png')):
        print(f"✅ '{team}' -> {logo_path}")
        print("   Extension case sensitivity is handled correctly")
        return True
    else:
        print(f"❌ '{team}' -> {logo_path}")
        print("   Failed to detect PNG file (case sensitivity issue)")
        return False


def main():
    """Run all PNG priority tests"""
    print("\n" + "="*70)
    print("PNG PRIORITIZATION TEST SUITE")
    print("="*70)
    print("\nTesting that PNG logos are prioritized over JPG when both exist,")
    print("and that the check is case-insensitive (.png and .PNG)")
    
    test_results = []
    
    # Run all tests
    test_results.append(("PNG Priority", test_png_priority()))
    test_results.append(("JPG Fallback", test_jpg_fallback()))
    test_results.append(("Case Insensitivity", test_case_insensitivity()))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nPNG prioritization is working correctly.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("\nPlease review the failures above.")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
