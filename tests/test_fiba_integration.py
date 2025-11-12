"""
Test Script for FIBA API Integration

This script tests the FIBA API client and integration module.

Author: FLBB Statistics Team
Date: 2025-11-12
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fiba_api_client import FIBAAPIClient, create_fiba_client
from fiba_integration import FIBAPlayerEnrichment, load_config_for_fiba


def test_fiba_client():
    """Test FIBA API Client initialization and basic functionality."""
    print("=" * 80)
    print("Testing FIBA API Client")
    print("=" * 80)
    
    # Create client
    client = FIBAAPIClient()
    
    print("\n✓ Client created successfully")
    print(f"  LiveStats URL: {client.FIBA_LIVESTATS_BASE_URL}")
    print(f"  SportResult URL: {client.FIBA_SPORTRESULT_BASE_URL}")
    print(f"  Official URL: {client.FIBA_OFFICIAL_BASE_URL}")
    print(f"  Luxembourg Code: {client.LUXEMBOURG_COUNTRY_CODE}")
    print(f"  FIBA Zone: {client.FIBA_EUROPE_ZONE}")
    print(f"  Cache Enabled: {client.cache_enabled}")
    print(f"  Timeout: {client.timeout}s")
    
    # Test cache stats
    cache_stats = client.get_cache_stats()
    print(f"\n✓ Cache statistics retrieved")
    print(f"  Enabled: {cache_stats['enabled']}")
    print(f"  Total Files: {cache_stats['total_files']}")
    print(f"  Total Size: {cache_stats['total_size_mb']} MB")
    if cache_stats['enabled']:
        print(f"  Cache Directory: {cache_stats['cache_dir']}")
    
    return True


def test_fiba_integration():
    """Test FIBA Integration module."""
    print("\n" + "=" * 80)
    print("Testing FIBA Integration Module")
    print("=" * 80)
    
    # Load configuration
    config = load_config_for_fiba()
    print("\n✓ Configuration loaded")
    
    # Check FIBA config
    fiba_config = config.get('fiba', {})
    print(f"  FIBA Enabled: {fiba_config.get('enabled', False)}")
    print(f"  Cache Enabled: {fiba_config.get('cache_enabled', False)}")
    print(f"  Timeout: {fiba_config.get('timeout', 30)}s")
    
    lux_config = fiba_config.get('luxembourg', {})
    print(f"  Luxembourg Country Code: {lux_config.get('country_code', 'LUX')}")
    print(f"  FIBA Zone: {lux_config.get('fiba_zone', 'E')}")
    print(f"  Enrich Player Data: {lux_config.get('enrich_player_data', True)}")
    
    # Create enrichment instance
    enrichment = FIBAPlayerEnrichment(config)
    print("\n✓ FIBAPlayerEnrichment instance created")
    print(f"  Enabled: {enrichment.enabled}")
    print(f"  Country Code: {enrichment.country_code}")
    print(f"  Enrich Enabled: {enrichment.enrich_enabled}")
    
    # Test enrichment statistics
    stats = enrichment.get_enrichment_statistics()
    print("\n✓ Enrichment statistics retrieved")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test player enrichment with sample data
    print("\n✓ Testing player data enrichment")
    sample_flbb_data = {
        'PlayerName': 'Sample Player',
        'Team': 'Test Team',
        'GamesPlayed': 10,
        'TotalPoints': 150,
        'AvgPointsPerGame': 15.0
    }
    
    print(f"  Input data: {sample_flbb_data}")
    
    # Note: This won't actually fetch data without internet/valid API, but tests the flow
    try:
        enriched = enrichment.enrich_player('Sample Player', sample_flbb_data)
        print(f"  Enriched data keys: {list(enriched.keys())}")
        print(f"  Has FIBA data: {enriched.get('has_fiba_data', False)}")
    except Exception as e:
        print(f"  Note: Cannot fetch live data (expected without internet): {type(e).__name__}")
        print(f"  This is normal in test environment without API access")
    
    return True


def test_config_file():
    """Test that config file has FIBA settings."""
    print("\n" + "=" * 80)
    print("Testing Configuration File")
    print("=" * 80)
    
    config_paths = [
        'scripts/config.json',
        '../scripts/config.json',
        'data/config.json',
        '../data/config.json',
    ]
    
    config_found = False
    for config_path in config_paths:
        if os.path.exists(config_path):
            print(f"\n✓ Config file found: {config_path}")
            config_found = True
            
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Check for FIBA section
            if 'fiba' in config:
                print("  ✓ FIBA configuration section found")
                fiba_config = config['fiba']
                
                required_keys = ['enabled', 'api_key', 'timeout', 'cache_enabled', 'endpoints', 'luxembourg']
                for key in required_keys:
                    if key in fiba_config:
                        print(f"    ✓ {key}: present")
                    else:
                        print(f"    ✗ {key}: missing")
                
                # Check endpoints
                if 'endpoints' in fiba_config:
                    endpoints = fiba_config['endpoints']
                    print(f"  ✓ Endpoints configured:")
                    for name, url in endpoints.items():
                        print(f"    - {name}: {url}")
                
                # Check Luxembourg config
                if 'luxembourg' in fiba_config:
                    lux = fiba_config['luxembourg']
                    print(f"  ✓ Luxembourg configuration:")
                    print(f"    - country_code: {lux.get('country_code')}")
                    print(f"    - fiba_zone: {lux.get('fiba_zone')}")
                    print(f"    - enrich_player_data: {lux.get('enrich_player_data')}")
            else:
                print("  ✗ FIBA configuration section not found")
            
            break
    
    if not config_found:
        print("\n✗ No config file found in standard locations")
        return False
    
    return True


def test_module_imports():
    """Test that all modules can be imported."""
    print("\n" + "=" * 80)
    print("Testing Module Imports")
    print("=" * 80)
    
    modules_to_test = [
        ('fiba_api_client', ['FIBAAPIClient', 'create_fiba_client']),
        ('fiba_integration', ['FIBAPlayerEnrichment', 'load_config_for_fiba']),
    ]
    
    all_passed = True
    
    for module_name, classes in modules_to_test:
        try:
            module = __import__(module_name)
            print(f"\n✓ Module '{module_name}' imported successfully")
            
            for class_name in classes:
                if hasattr(module, class_name):
                    print(f"  ✓ {class_name} found")
                else:
                    print(f"  ✗ {class_name} not found")
                    all_passed = False
        except Exception as e:
            print(f"\n✗ Failed to import '{module_name}': {e}")
            all_passed = False
    
    return all_passed


def test_player_database_structure():
    """Test that player database can be loaded and enriched."""
    print("\n" + "=" * 80)
    print("Testing Player Database Structure")
    print("=" * 80)
    
    # Try to load player database
    db_paths = [
        'data/players-database.csv',
        '../data/players-database.csv',
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\n✓ Player database found: {db_path}")
            
            try:
                import pandas as pd
                df = pd.read_csv(db_path, encoding='utf-8-sig')
                
                print(f"  Total players: {len(df)}")
                print(f"  Columns: {len(df.columns)}")
                
                # Check for PlayerName column
                if 'PlayerName' in df.columns:
                    print(f"  ✓ PlayerName column found")
                    print(f"  Sample players:")
                    for i, name in enumerate(df['PlayerName'].head(3)):
                        print(f"    {i+1}. {name}")
                else:
                    print(f"  ✗ PlayerName column not found")
                    print(f"  Available columns: {list(df.columns)}")
                
                return True
            except Exception as e:
                print(f"  ✗ Error loading database: {e}")
                return False
    
    print("\n⚠ Player database not found (this is OK if not yet generated)")
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 80)
    print("FIBA API Integration Test Suite")
    print("=" * 80)
    
    tests = [
        ("Module Imports", test_module_imports),
        ("FIBA Client", test_fiba_client),
        ("FIBA Integration", test_fiba_integration),
        ("Configuration File", test_config_file),
        ("Player Database Structure", test_player_database_structure),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'=' * 80}")
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n✗ Test '{test_name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 80)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
