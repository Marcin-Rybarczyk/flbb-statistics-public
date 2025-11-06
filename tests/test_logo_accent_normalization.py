#!/usr/bin/env python3
"""
Test logo normalization for teams with accented characters.

This test ensures that team names with accented characters (é, ä, etc.)
are correctly normalized for logo file lookups. The normalization should
convert accented characters to their base form (é -> e, ä -> a) rather
than removing them entirely.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.logo_utils import normalize_team_name, get_team_logo_path


# Test data: (original_name, expected_normalized, should_have_logo)
LOGO_NORMALIZATION_TEST_CASES = [
    ("Gréngewald Hueschtert B", "grengewald-hueschtert-b", True),
    ("Gréngewald Hueschtert C", "grengewald-hueschtert-c", True),
    ("BBC Käldall", "bbc-kaldall", True),
    ("Rebound Préizerdaul", "rebound-preizerdaul", True),
    ("Rebound Préizerdaul B", "rebound-preizerdaul-b", True),
    ("Résidence Walferdange", "residence-walferdange", True),
    ("Résidence Walferdange B", "residence-walferdange-b", True),
    # Control case: team without accents
    ("Racing Luxembourg", "racing-luxembourg", True),
]


def test_normalize_team_name():
    """Test that normalize_team_name converts accents to base characters"""
    print("\n" + "="*70)
    print("Testing normalize_team_name with accented characters")
    print("="*70)
    
    all_passed = True
    for original, expected, _ in LOGO_NORMALIZATION_TEST_CASES:
        result = normalize_team_name(original)
        passed = result == expected
        status = "✅" if passed else "❌"
        print(f"{status} '{original}'")
        print(f"   Result:   '{result}'")
        if not passed:
            print(f"   Expected: '{expected}'")
            all_passed = False
    
    return all_passed


def test_logo_file_lookup():
    """Test that teams with accents can find their logo files"""
    print("\n" + "="*70)
    print("Testing logo file lookup for accented team names")
    print("="*70)
    
    all_passed = True
    for original, _, should_have_logo in LOGO_NORMALIZATION_TEST_CASES:
        logo_path = get_team_logo_path(original)
        has_logo = logo_path is not None
        
        if should_have_logo:
            if has_logo:
                # Verify file exists
                file_exists = os.path.exists(logo_path)
                if file_exists:
                    print(f"✅ '{original}' -> {logo_path}")
                else:
                    print(f"❌ '{original}' -> {logo_path} (FILE NOT FOUND)")
                    all_passed = False
            else:
                print(f"❌ '{original}' -> NO LOGO PATH RETURNED")
                all_passed = False
        else:
            if not has_logo:
                print(f"✅ '{original}' -> No logo (expected)")
            else:
                print(f"⚠️  '{original}' -> {logo_path} (unexpected logo found)")
    
    return all_passed


def test_accent_to_base_conversion():
    """Test specific accent-to-base character conversions"""
    print("\n" + "="*70)
    print("Testing specific accent conversions")
    print("="*70)
    
    test_cases = [
        ("é", "e", "e-acute"),
        ("è", "e", "e-grave"),
        ("ê", "e", "e-circumflex"),
        ("ë", "e", "e-diaeresis"),
        ("ä", "a", "a-umlaut"),
        ("ö", "o", "o-umlaut"),
        ("ü", "u", "u-umlaut"),
        ("à", "a", "a-grave"),
        ("â", "a", "a-circumflex"),
    ]
    
    all_passed = True
    for accented, expected_base, description in test_cases:
        # Create a test string with the accented character
        test_input = f"Test{accented}Team"
        expected = f"test{expected_base}team"
        result = normalize_team_name(test_input)
        
        passed = result == expected
        status = "✅" if passed else "❌"
        print(f"{status} {description}: '{test_input}' -> '{result}'")
        if not passed:
            print(f"   Expected: '{expected}'")
            all_passed = False
    
    return all_passed


def main():
    """Run all logo normalization tests"""
    print("\n" + "="*70)
    print("LOGO ACCENT NORMALIZATION TEST SUITE")
    print("="*70)
    print("\nTesting that accented characters in team names are correctly")
    print("normalized for logo file lookups (é -> e, ä -> a, etc.)")
    
    test_results = []
    
    # Run all tests
    test_results.append(("Normalize Team Name", test_normalize_team_name()))
    test_results.append(("Logo File Lookup", test_logo_file_lookup()))
    test_results.append(("Accent Conversions", test_accent_to_base_conversion()))
    
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
        print("\nLogo normalization is working correctly for accented team names.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("\nPlease review the failures above.")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
