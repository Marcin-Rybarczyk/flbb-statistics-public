"""
FIBA API Usage Examples

This script demonstrates various ways to use the FIBA API integration
to access extended player data for Luxembourg basketball games.

Author: FLBB Statistics Team
Date: 2025-11-12
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fiba_api_client import FIBAAPIClient, create_fiba_client
from fiba_integration import FIBAPlayerEnrichment, load_config_for_fiba


def example_1_basic_client():
    """Example 1: Basic FIBA API Client Usage"""
    print("\n" + "=" * 80)
    print("Example 1: Basic FIBA API Client Usage")
    print("=" * 80)
    
    # Create client
    client = FIBAAPIClient()
    
    print("\nClient initialized successfully!")
    print(f"Luxembourg Country Code: {client.LUXEMBOURG_COUNTRY_CODE}")
    print(f"FIBA Zone (Europe): {client.FIBA_EUROPE_ZONE}")
    
    # Show cache information
    cache_stats = client.get_cache_stats()
    print(f"\nCache Status:")
    print(f"  Enabled: {cache_stats['enabled']}")
    print(f"  Location: {cache_stats.get('cache_dir', 'N/A')}")
    print(f"  Files: {cache_stats['total_files']}")
    print(f"  Size: {cache_stats['total_size_mb']} MB")


def example_2_search_players():
    """Example 2: Search for Luxembourg Players"""
    print("\n" + "=" * 80)
    print("Example 2: Search for Luxembourg Players")
    print("=" * 80)
    
    client = FIBAAPIClient()
    
    # Note: This requires internet access and valid FIBA endpoints
    print("\nSearching for Luxembourg players...")
    print("(Note: Requires internet connection to FIBA APIs)")
    
    try:
        # Search for players with common Luxembourg names
        search_names = ["Felix", "Laurent", "Bob"]
        
        for name in search_names:
            print(f"\nSearching for '{name}'...")
            players = client.search_players(name, country_code="LUX")
            
            if players:
                print(f"Found {len(players)} player(s):")
                for player in players[:3]:  # Show first 3 results
                    print(f"  - {player.get('name', 'Unknown')}")
                    print(f"    Position: {player.get('position', 'N/A')}")
                    print(f"    Height: {player.get('height_cm', 'N/A')} cm")
            else:
                print(f"  No players found (or API not accessible)")
    
    except Exception as e:
        print(f"\nNote: Cannot access FIBA API in this environment")
        print(f"Error type: {type(e).__name__}")
        print("This is expected without internet access to FIBA endpoints")


def example_3_player_enrichment():
    """Example 3: Enrich Player Data with FIBA Information"""
    print("\n" + "=" * 80)
    print("Example 3: Enrich Player Data with FIBA Information")
    print("=" * 80)
    
    # Load configuration
    config = load_config_for_fiba()
    
    # Create enrichment instance
    enrichment = FIBAPlayerEnrichment(config)
    
    print(f"\nFIBA Enrichment Settings:")
    print(f"  Enabled: {enrichment.enabled}")
    print(f"  Country: {enrichment.country_code}")
    print(f"  Auto-enrich: {enrichment.enrich_enabled}")
    
    # Sample FLBB player data
    sample_players = [
        {
            'PlayerName': 'KLOMAN Felix Whitcomb',
            'Team': 'AS Soleuvre',
            'TotalPoints': 244,
            'GamesPlayed': 8,
            'AvgPointsPerGame': 30.5
        },
        {
            'PlayerName': 'BARNES Cobie Logan',
            'Team': 'BC Mess',
            'TotalPoints': 244,
            'GamesPlayed': 7,
            'AvgPointsPerGame': 34.86
        }
    ]
    
    print("\nEnriching player data...")
    
    for player_data in sample_players:
        player_name = player_data['PlayerName']
        print(f"\n{player_name}:")
        print(f"  FLBB Stats: {player_data['TotalPoints']} pts in {player_data['GamesPlayed']} games")
        
        # Enrich player data
        enriched = enrichment.enrich_player(player_name, player_data)
        
        # Show enrichment results
        if enriched.get('has_fiba_data'):
            print(f"  ✓ FIBA Data Available:")
            print(f"    - FIBA ID: {enriched.get('fiba_id')}")
            print(f"    - Height: {enriched.get('height_cm')} cm")
            print(f"    - Position: {enriched.get('position')}")
            print(f"    - International Caps: {enriched.get('international_caps', 0)}")
        else:
            print(f"  ⚠ FIBA Data: Not available (player not in FIBA database or API not accessible)")


def example_4_luxembourg_national_team():
    """Example 4: Get Luxembourg National Team Data"""
    print("\n" + "=" * 80)
    print("Example 4: Get Luxembourg National Team Data")
    print("=" * 80)
    
    client = FIBAAPIClient()
    
    print("\nAttempting to retrieve Luxembourg national team data...")
    print("(Note: Requires internet connection to FIBA APIs)")
    
    try:
        # Get Luxembourg national team players
        lux_players = client.get_luxembourg_players()
        
        if lux_players:
            print(f"\nFound {len(lux_players)} Luxembourg national team players:")
            for player in lux_players[:5]:  # Show first 5
                print(f"  - {player.get('name', 'Unknown')}")
                print(f"    Position: {player.get('position', 'N/A')}")
                print(f"    Caps: {player.get('caps', 0)}")
        else:
            print("\nNo data returned (API may not be accessible)")
        
        # Get national team games
        print("\nAttempting to retrieve Luxembourg national team games...")
        games = client.get_national_team_games(season="2025-2026")
        
        if games:
            print(f"\nFound {len(games)} games:")
            for game in games[:3]:  # Show first 3
                print(f"  {game.get('date')}: {game.get('home_team')} vs {game.get('away_team')}")
        else:
            print("\nNo games returned (API may not be accessible)")
    
    except Exception as e:
        print(f"\nNote: Cannot access FIBA API in this environment")
        print(f"Error type: {type(e).__name__}")
        print("This is expected without internet access to FIBA endpoints")


def example_5_enrich_dataframe():
    """Example 5: Enrich Entire Player Database"""
    print("\n" + "=" * 80)
    print("Example 5: Enrich Entire Player Database")
    print("=" * 80)
    
    try:
        import pandas as pd
        
        # Check if player database exists
        db_path = 'data/players-database.csv'
        
        if os.path.exists(db_path):
            print(f"\nLoading player database from: {db_path}")
            
            # Load player database
            df = pd.read_csv(db_path, encoding='utf-8-sig')
            print(f"Loaded {len(df)} players")
            
            # Load configuration
            config = load_config_for_fiba()
            
            # Create enrichment instance
            enrichment = FIBAPlayerEnrichment(config)
            
            # Show sample of players before enrichment
            print("\nSample players:")
            for idx, row in df.head(3).iterrows():
                print(f"  {idx+1}. {row['PlayerName']} - {row['Team']}")
            
            print("\nNote: Full enrichment would process all players.")
            print("This can take time depending on API access and player count.")
            print("\nTo enrich the full database, use:")
            print("  python src/fiba_integration.py --input data/players-database.csv --output data/players-database-enriched.csv")
            
            # Get enrichment statistics
            stats = enrichment.get_enrichment_statistics()
            print(f"\nCurrent enrichment statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print(f"\nPlayer database not found at: {db_path}")
            print("Generate it first or update the path.")
    
    except ImportError:
        print("\nPandas not available. Install requirements:")
        print("  pip install -r requirements.txt")
    except Exception as e:
        print(f"\nError: {e}")


def example_6_cache_management():
    """Example 6: Cache Management"""
    print("\n" + "=" * 80)
    print("Example 6: Cache Management")
    print("=" * 80)
    
    client = FIBAAPIClient()
    
    # Show cache statistics
    cache_stats = client.get_cache_stats()
    
    print("\nCache Information:")
    print(f"  Enabled: {cache_stats['enabled']}")
    
    if cache_stats['enabled']:
        print(f"  Location: {cache_stats.get('cache_dir', 'N/A')}")
        print(f"  Total Files: {cache_stats['total_files']}")
        print(f"  Total Size: {cache_stats['total_size_mb']} MB")
        
        if cache_stats['total_files'] > 0:
            print("\nCache contains previously fetched FIBA data.")
            print("Benefits:")
            print("  - Faster access to previously requested data")
            print("  - Reduced API calls")
            print("  - Works offline for cached data")
            
            # Note: Don't actually clear cache in example
            print("\nTo clear cache:")
            print("  client.clear_cache()")
        else:
            print("\nCache is empty. It will fill as you use the FIBA API.")
    else:
        print("  Cache is disabled in configuration")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("FIBA API Integration - Usage Examples")
    print("=" * 80)
    print("\nThese examples demonstrate how to use the FIBA API integration")
    print("to access extended player data for Luxembourg basketball games.")
    
    examples = [
        ("Basic Client Usage", example_1_basic_client),
        ("Search Players", example_2_search_players),
        ("Player Enrichment", example_3_player_enrichment),
        ("National Team Data", example_4_luxembourg_national_team),
        ("Enrich Database", example_5_enrich_dataframe),
        ("Cache Management", example_6_cache_management),
    ]
    
    # Run all examples
    for title, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ Example failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 80)
    print("Examples Complete")
    print("=" * 80)
    print("\nFor more information, see:")
    print("  - Documentation: docs/FIBA_API_INTEGRATION.md")
    print("  - Source code: src/fiba_api_client.py")
    print("  - Integration: src/fiba_integration.py")
    print("  - Tests: tests/test_fiba_integration.py")
    print("\nTo enrich your player database:")
    print("  python src/fiba_integration.py --input data/players-database.csv --output data/players-database-enriched.csv")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
