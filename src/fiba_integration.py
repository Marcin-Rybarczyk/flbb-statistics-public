"""
FIBA Integration Module

This module provides functions to integrate FIBA API data with the existing
FLBB player database, enriching player profiles with extended international data.

Author: FLBB Statistics Team
Date: 2025-11-12
"""

import os
import sys
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add parent directory to path to import fiba_api_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fiba_api_client import FIBAAPIClient, create_fiba_client


class FIBAPlayerEnrichment:
    """
    Class to handle enrichment of FLBB player data with FIBA information.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize FIBA Player Enrichment.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.fiba_client = create_fiba_client(config)
        self.enrichment_cache = {}
        
        # Load FIBA configuration
        self.enabled = self.config.get('fiba', {}).get('enabled', True)
        self.luxembourg_config = self.config.get('fiba', {}).get('luxembourg', {})
        self.country_code = self.luxembourg_config.get('country_code', 'LUX')
        self.enrich_enabled = self.luxembourg_config.get('enrich_player_data', True)
    
    def enrich_player(self, player_name: str, flbb_data: Dict) -> Dict:
        """
        Enrich a single player's data with FIBA information.
        
        Args:
            player_name: Player's full name
            flbb_data: Dictionary containing FLBB player data
            
        Returns:
            Enriched player data dictionary
        """
        if not self.enabled or not self.enrich_enabled:
            return flbb_data
        
        # Check cache first
        if player_name in self.enrichment_cache:
            cached_data = self.enrichment_cache[player_name]
            # Merge cached FIBA data with current FLBB data
            enriched = flbb_data.copy()
            enriched.update(cached_data)
            return enriched
        
        # Get enriched data from FIBA API
        enriched_data = self.fiba_client.enrich_player_data(player_name, flbb_data)
        
        # Cache FIBA-specific fields
        if enriched_data.get('has_fiba_data'):
            fiba_fields = {
                'fiba_id': enriched_data.get('fiba_id'),
                'fiba_profile_url': enriched_data.get('fiba_profile_url'),
                'birth_date': enriched_data.get('birth_date'),
                'height_cm': enriched_data.get('height_cm'),
                'weight_kg': enriched_data.get('weight_kg'),
                'position': enriched_data.get('position'),
                'nationality': enriched_data.get('nationality'),
                'international_caps': enriched_data.get('international_caps'),
                'fiba_career_stats': enriched_data.get('fiba_career_stats'),
                'has_fiba_data': True
            }
            self.enrichment_cache[player_name] = fiba_fields
        
        return enriched_data
    
    def enrich_players_dataframe(self, df: pd.DataFrame, player_name_column: str = 'PlayerName') -> pd.DataFrame:
        """
        Enrich a pandas DataFrame of players with FIBA data.
        
        Args:
            df: DataFrame containing player data
            player_name_column: Name of the column containing player names
            
        Returns:
            Enriched DataFrame with additional FIBA columns
        """
        if not self.enabled or not self.enrich_enabled:
            return df
        
        # Create copy to avoid modifying original
        enriched_df = df.copy()
        
        # Add FIBA data columns
        fiba_columns = [
            'fiba_id', 'fiba_profile_url', 'birth_date', 'height_cm', 
            'weight_kg', 'position', 'nationality', 'international_caps', 'has_fiba_data'
        ]
        
        for col in fiba_columns:
            enriched_df[col] = None
        
        # Enrich each player
        for idx, row in enriched_df.iterrows():
            player_name = row[player_name_column]
            if pd.notna(player_name):
                # Get enriched data
                flbb_data = row.to_dict()
                enriched = self.enrich_player(player_name, flbb_data)
                
                # Update DataFrame row with FIBA data
                for col in fiba_columns:
                    if col in enriched:
                        enriched_df.at[idx, col] = enriched[col]
        
        return enriched_df
    
    def get_luxembourg_national_team_players(self) -> List[Dict]:
        """
        Get all Luxembourg national team players from FIBA.
        
        Returns:
            List of player dictionaries
        """
        if not self.enabled:
            return []
        
        return self.fiba_client.get_luxembourg_players()
    
    def get_luxembourg_international_games(self, season: Optional[str] = None) -> List[Dict]:
        """
        Get Luxembourg national team games from FIBA.
        
        Args:
            season: Optional season filter (e.g., '2025-2026')
            
        Returns:
            List of game dictionaries
        """
        if not self.enabled:
            return []
        
        return self.fiba_client.get_national_team_games(
            country_code=self.country_code,
            season=season
        )
    
    def search_player_in_fiba(self, player_name: str) -> List[Dict]:
        """
        Search for a player in FIBA database.
        
        Args:
            player_name: Player's name to search
            
        Returns:
            List of matching players
        """
        if not self.enabled:
            return []
        
        return self.fiba_client.search_players(player_name, country_code=self.country_code)
    
    def get_player_extended_profile(self, player_name: str) -> Optional[Dict]:
        """
        Get comprehensive player profile combining FLBB and FIBA data.
        
        Args:
            player_name: Player's full name
            
        Returns:
            Dictionary with extended player profile
        """
        # Search in FIBA
        fiba_matches = self.search_player_in_fiba(player_name)
        
        if not fiba_matches:
            return None
        
        # Get detailed info for first match
        fiba_player = fiba_matches[0]
        player_id = fiba_player.get('id')
        
        if player_id:
            detailed_info = self.fiba_client.get_player_info(player_id)
            return detailed_info
        
        return fiba_player
    
    def export_enriched_player_database(
        self, 
        input_csv: str, 
        output_csv: str,
        player_name_column: str = 'PlayerName'
    ) -> bool:
        """
        Export enriched player database to CSV.
        
        Args:
            input_csv: Path to input CSV file with FLBB data
            output_csv: Path to output CSV file for enriched data
            player_name_column: Name of the column containing player names
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load FLBB player data
            df = pd.read_csv(input_csv, encoding='utf-8-sig')
            
            # Enrich with FIBA data
            enriched_df = self.enrich_players_dataframe(df, player_name_column)
            
            # Save to output CSV
            enriched_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
            
            print(f"Enriched player database exported to: {output_csv}")
            print(f"Total players: {len(enriched_df)}")
            print(f"Players with FIBA data: {enriched_df['has_fiba_data'].sum()}")
            
            return True
        except Exception as e:
            print(f"Error exporting enriched player database: {e}")
            return False
    
    def get_enrichment_statistics(self) -> Dict:
        """
        Get statistics about player data enrichment.
        
        Returns:
            Dictionary with enrichment statistics
        """
        total_cached = len(self.enrichment_cache)
        with_fiba_data = sum(1 for data in self.enrichment_cache.values() if data.get('has_fiba_data'))
        
        return {
            'total_players_cached': total_cached,
            'players_with_fiba_data': with_fiba_data,
            'enrichment_rate': f"{(with_fiba_data/total_cached*100):.1f}%" if total_cached > 0 else "0%",
            'cache_size': len(self.enrichment_cache),
            'fiba_enabled': self.enabled,
            'enrich_enabled': self.enrich_enabled
        }


def load_config_for_fiba() -> Dict:
    """
    Load configuration for FIBA integration.
    
    Returns:
        Configuration dictionary
    """
    config_paths = [
        'scripts/config.json',
        'data/config.json',
        'config.json'
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config from {config_path}: {e}")
    
    # Return default config
    return {
        'fiba': {
            'enabled': True,
            'api_key': '',
            'timeout': 30,
            'cache_enabled': True,
            'luxembourg': {
                'country_code': 'LUX',
                'fiba_zone': 'E',
                'enrich_player_data': True
            }
        }
    }


def enrich_player_database_cli():
    """
    Command-line interface for enriching player database with FIBA data.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enrich FLBB player database with FIBA data'
    )
    parser.add_argument(
        '--input',
        default='data/players-database.csv',
        help='Input CSV file with FLBB player data'
    )
    parser.add_argument(
        '--output',
        default='data/players-database-enriched.csv',
        help='Output CSV file for enriched player data'
    )
    parser.add_argument(
        '--player-column',
        default='PlayerName',
        help='Name of the column containing player names'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show enrichment statistics'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config_for_fiba()
    
    # Create enrichment instance
    enrichment = FIBAPlayerEnrichment(config)
    
    if args.stats:
        # Show cache statistics
        cache_stats = enrichment.fiba_client.get_cache_stats()
        print("\nFIBA API Cache Statistics:")
        print(f"  Enabled: {cache_stats['enabled']}")
        print(f"  Total Files: {cache_stats['total_files']}")
        print(f"  Total Size: {cache_stats['total_size_mb']} MB")
        
        enrich_stats = enrichment.get_enrichment_statistics()
        print("\nEnrichment Statistics:")
        for key, value in enrich_stats.items():
            print(f"  {key}: {value}")
        return
    
    # Enrich player database
    print(f"\nEnriching player database...")
    print(f"  Input: {args.input}")
    print(f"  Output: {args.output}")
    
    success = enrichment.export_enriched_player_database(
        args.input,
        args.output,
        args.player_column
    )
    
    if success:
        # Show statistics
        enrich_stats = enrichment.get_enrichment_statistics()
        print("\nEnrichment Statistics:")
        for key, value in enrich_stats.items():
            print(f"  {key}: {value}")
    else:
        print("\nEnrichment failed!")
        sys.exit(1)


# Example usage
if __name__ == "__main__":
    # Check if running as CLI
    if len(sys.argv) > 1:
        enrich_player_database_cli()
    else:
        # Example usage
        print("FIBA Player Data Enrichment")
        print("=" * 80)
        
        # Load configuration
        config = load_config_for_fiba()
        
        # Create enrichment instance
        enrichment = FIBAPlayerEnrichment(config)
        
        print("\nFIBA Integration Status:")
        print(f"  Enabled: {enrichment.enabled}")
        print(f"  Country Code: {enrichment.country_code}")
        print(f"  Enrich Enabled: {enrichment.enrich_enabled}")
        
        # Example: Search for a player
        print("\nExample: Searching for Luxembourg players...")
        
        # Show available commands
        print("\n" + "=" * 80)
        print("Command-line usage:")
        print("  python fiba_integration.py --help")
        print("  python fiba_integration.py --input data/players-database.csv --output data/players-database-enriched.csv")
        print("  python fiba_integration.py --stats")
        print("\nProgrammatic usage:")
        print("  from fiba_integration import FIBAPlayerEnrichment")
        print("  enrichment = FIBAPlayerEnrichment(config)")
        print("  enriched_data = enrichment.enrich_player(player_name, flbb_data)")
