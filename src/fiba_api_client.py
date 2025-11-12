"""
FIBA API Client for Luxembourg Basketball Games

This module provides access to FIBA (International Basketball Federation) APIs
to retrieve extended player data and game information for Luxembourg basketball.

FIBA API Documentation:
- LiveStats API: https://fibalivestats.dcd.shared.geniussports.com
- SportResult Cache: https://livecache.sportresult.com/node/db/FIBASTATS
- FIBA Official: https://www.fiba.basketball

Author: FLBB Statistics Team
Date: 2025-11-12
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import os


class FIBAAPIClient:
    """
    Client for accessing FIBA APIs to retrieve basketball data.
    
    Supports multiple FIBA data sources:
    - FIBA LiveStats (Genius Sports) - Live and historical game data
    - FIBA SportResult Cache - Structured competition and player data
    - FIBA Official Website - General competition information
    """
    
    # Base URLs for different FIBA API endpoints
    FIBA_LIVESTATS_BASE_URL = "https://fibalivestats.dcd.shared.geniussports.com"
    FIBA_SPORTRESULT_BASE_URL = "https://livecache.sportresult.com/node/db/FIBASTATS"
    FIBA_OFFICIAL_BASE_URL = "https://www.fiba.basketball"
    
    # FIBA Europe zone code (Luxembourg is in Europe)
    FIBA_EUROPE_ZONE = "E"
    
    # Luxembourg country code in FIBA system
    LUXEMBOURG_COUNTRY_CODE = "LUX"
    LUXEMBOURG_FIBA_CODE = "LUX"
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30, cache_enabled: bool = True):
        """
        Initialize FIBA API Client.
        
        Args:
            api_key: Optional API key for authenticated endpoints
            timeout: Request timeout in seconds (default: 30)
            cache_enabled: Enable local caching of API responses (default: True)
        """
        self.api_key = api_key
        self.timeout = timeout
        self.cache_enabled = cache_enabled
        self.session = requests.Session()
        
        # Set up headers
        self.session.headers.update({
            'User-Agent': 'FLBB-Statistics/1.0 (Luxembourg Basketball Federation)',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Add API key if provided
        if self.api_key:
            self.session.headers['Authorization'] = f'Bearer {self.api_key}'
        
        # Cache directory
        self.cache_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'fiba_cache')
        if self.cache_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def _make_request(self, url: str, params: Optional[Dict] = None, use_cache: bool = True) -> Dict:
        """
        Make HTTP request to FIBA API with caching support.
        
        Args:
            url: Full URL to request
            params: Optional query parameters
            use_cache: Whether to use cached response if available
            
        Returns:
            Dict containing API response
            
        Raises:
            requests.RequestException: If request fails
        """
        # Generate cache key
        cache_key = self._generate_cache_key(url, params)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # Check cache if enabled
        if use_cache and self.cache_enabled and os.path.exists(cache_file):
            # Check if cache is less than 24 hours old
            cache_age = time.time() - os.path.getmtime(cache_file)
            if cache_age < 86400:  # 24 hours
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # Make request
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            # Cache response
            if self.cache_enabled:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            return data
        except requests.RequestException as e:
            print(f"Error making request to {url}: {e}")
            raise
    
    def _generate_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Generate unique cache key for URL and parameters."""
        import hashlib
        key_string = url
        if params:
            key_string += json.dumps(params, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_competitions(self, zone: Optional[str] = None, season: Optional[str] = None) -> List[Dict]:
        """
        Get list of FIBA competitions.
        
        Args:
            zone: Optional zone filter (e.g., 'E' for Europe)
            season: Optional season filter (e.g., '2025-2026')
            
        Returns:
            List of competition dictionaries
        """
        url = f"{self.FIBA_OFFICIAL_BASE_URL}/api/get-competitions"
        params = {}
        
        if zone:
            params['zone'] = zone
        if season:
            params['season'] = season
        
        try:
            data = self._make_request(url, params)
            return data.get('competitions', [])
        except Exception as e:
            print(f"Error fetching competitions: {e}")
            return []
    
    def get_luxembourg_competitions(self, season: Optional[str] = None) -> List[Dict]:
        """
        Get competitions involving Luxembourg teams.
        
        Args:
            season: Optional season filter (e.g., '2025-2026')
            
        Returns:
            List of competition dictionaries involving Luxembourg
        """
        # Get all European competitions
        competitions = self.get_competitions(zone=self.FIBA_EUROPE_ZONE, season=season)
        
        # Filter for Luxembourg involvement
        lux_competitions = []
        for comp in competitions:
            # Check if Luxembourg teams are participating
            if self._competition_has_luxembourg(comp):
                lux_competitions.append(comp)
        
        return lux_competitions
    
    def _competition_has_luxembourg(self, competition: Dict) -> bool:
        """Check if a competition involves Luxembourg teams."""
        # Check teams list
        teams = competition.get('teams', [])
        for team in teams:
            if team.get('country_code') == self.LUXEMBOURG_COUNTRY_CODE:
                return True
        
        # Check participants
        participants = competition.get('participants', [])
        for participant in participants:
            if participant.get('country_code') == self.LUXEMBOURG_COUNTRY_CODE:
                return True
        
        return False
    
    def get_player_info(self, player_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific player from FIBA.
        
        Args:
            player_id: FIBA player ID
            
        Returns:
            Dictionary containing player information, or None if not found
        """
        url = f"{self.FIBA_LIVESTATS_BASE_URL}/api/player/{player_id}"
        
        try:
            data = self._make_request(url)
            return data
        except Exception as e:
            print(f"Error fetching player info for {player_id}: {e}")
            return None
    
    def search_players(self, name: str, country_code: Optional[str] = None) -> List[Dict]:
        """
        Search for players by name.
        
        Args:
            name: Player name to search for
            country_code: Optional country code filter (e.g., 'LUX')
            
        Returns:
            List of matching player dictionaries
        """
        url = f"{self.FIBA_OFFICIAL_BASE_URL}/api/search-players"
        params = {
            'name': name
        }
        
        if country_code:
            params['country'] = country_code
        
        try:
            data = self._make_request(url, params)
            return data.get('players', [])
        except Exception as e:
            print(f"Error searching for players: {e}")
            return []
    
    def get_luxembourg_players(self) -> List[Dict]:
        """
        Get all Luxembourg national team players from FIBA database.
        
        Returns:
            List of Luxembourg player dictionaries
        """
        url = f"{self.FIBA_OFFICIAL_BASE_URL}/api/players/country/{self.LUXEMBOURG_COUNTRY_CODE}"
        
        try:
            data = self._make_request(url)
            return data.get('players', [])
        except Exception as e:
            print(f"Error fetching Luxembourg players: {e}")
            return []
    
    def get_game_stats(self, game_id: str) -> Optional[Dict]:
        """
        Get detailed statistics for a specific game.
        
        Args:
            game_id: FIBA game ID
            
        Returns:
            Dictionary containing game statistics, or None if not found
        """
        url = f"{self.FIBA_LIVESTATS_BASE_URL}/api/game/{game_id}/stats"
        
        try:
            data = self._make_request(url)
            return data
        except Exception as e:
            print(f"Error fetching game stats for {game_id}: {e}")
            return None
    
    def get_player_game_stats(self, game_id: str, player_id: str) -> Optional[Dict]:
        """
        Get player statistics for a specific game.
        
        Args:
            game_id: FIBA game ID
            player_id: FIBA player ID
            
        Returns:
            Dictionary containing player's game statistics, or None if not found
        """
        game_stats = self.get_game_stats(game_id)
        
        if not game_stats:
            return None
        
        # Search for player in game stats
        for team in game_stats.get('teams', []):
            for player in team.get('players', []):
                if player.get('id') == player_id:
                    return player
        
        return None
    
    def get_team_roster(self, team_id: str, competition_id: Optional[str] = None) -> List[Dict]:
        """
        Get team roster from FIBA.
        
        Args:
            team_id: FIBA team ID
            competition_id: Optional competition ID for specific roster
            
        Returns:
            List of player dictionaries
        """
        url = f"{self.FIBA_OFFICIAL_BASE_URL}/api/team/{team_id}/roster"
        params = {}
        
        if competition_id:
            params['competition'] = competition_id
        
        try:
            data = self._make_request(url, params)
            return data.get('players', [])
        except Exception as e:
            print(f"Error fetching team roster: {e}")
            return []
    
    def enrich_player_data(self, player_name: str, flbb_data: Dict) -> Dict:
        """
        Enrich FLBB player data with FIBA information.
        
        Args:
            player_name: Player's name
            flbb_data: Existing player data from FLBB
            
        Returns:
            Enriched player data dictionary combining FLBB and FIBA data
        """
        enriched_data = flbb_data.copy()
        
        # Search for player in FIBA database
        fiba_players = self.search_players(player_name, country_code=self.LUXEMBOURG_COUNTRY_CODE)
        
        if fiba_players:
            # Use first match (most likely the same player)
            fiba_player = fiba_players[0]
            
            # Add FIBA-specific data
            enriched_data['fiba_id'] = fiba_player.get('id')
            enriched_data['fiba_profile_url'] = fiba_player.get('profile_url')
            enriched_data['birth_date'] = fiba_player.get('birth_date')
            enriched_data['height_cm'] = fiba_player.get('height_cm')
            enriched_data['weight_kg'] = fiba_player.get('weight_kg')
            enriched_data['position'] = fiba_player.get('position')
            enriched_data['nationality'] = fiba_player.get('nationality')
            enriched_data['international_caps'] = fiba_player.get('caps', 0)
            enriched_data['fiba_career_stats'] = fiba_player.get('career_stats', {})
            
            # Add flag that data has been enriched
            enriched_data['has_fiba_data'] = True
        else:
            enriched_data['has_fiba_data'] = False
        
        return enriched_data
    
    def get_national_team_games(self, country_code: str = None, season: Optional[str] = None) -> List[Dict]:
        """
        Get national team games for a country.
        
        Args:
            country_code: Country code (defaults to Luxembourg)
            season: Optional season filter
            
        Returns:
            List of game dictionaries
        """
        if country_code is None:
            country_code = self.LUXEMBOURG_COUNTRY_CODE
        
        url = f"{self.FIBA_OFFICIAL_BASE_URL}/api/games/national-team/{country_code}"
        params = {}
        
        if season:
            params['season'] = season
        
        try:
            data = self._make_request(url, params)
            return data.get('games', [])
        except Exception as e:
            print(f"Error fetching national team games: {e}")
            return []
    
    def clear_cache(self):
        """Clear all cached API responses."""
        if self.cache_enabled and os.path.exists(self.cache_dir):
            import shutil
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            print("FIBA API cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.cache_enabled or not os.path.exists(self.cache_dir):
            return {
                'enabled': False,
                'total_files': 0,
                'total_size_mb': 0
            }
        
        total_files = 0
        total_size = 0
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                total_files += 1
                filepath = os.path.join(self.cache_dir, filename)
                total_size += os.path.getsize(filepath)
        
        return {
            'enabled': True,
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': self.cache_dir
        }


def create_fiba_client(config: Optional[Dict] = None) -> FIBAAPIClient:
    """
    Factory function to create FIBA API client with configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured FIBAAPIClient instance
    """
    api_key = None
    timeout = 30
    cache_enabled = True
    
    if config:
        api_key = config.get('fiba', {}).get('api_key')
        timeout = config.get('fiba', {}).get('timeout', 30)
        cache_enabled = config.get('fiba', {}).get('cache_enabled', True)
    
    # Also check environment variables
    if not api_key:
        api_key = os.environ.get('FIBA_API_KEY')
    
    return FIBAAPIClient(api_key=api_key, timeout=timeout, cache_enabled=cache_enabled)


# Example usage and testing
if __name__ == "__main__":
    print("FIBA API Client for Luxembourg Basketball")
    print("=" * 80)
    
    # Create client
    client = FIBAAPIClient()
    
    print("\nClient Information:")
    print(f"- LiveStats URL: {client.FIBA_LIVESTATS_BASE_URL}")
    print(f"- SportResult URL: {client.FIBA_SPORTRESULT_BASE_URL}")
    print(f"- Official URL: {client.FIBA_OFFICIAL_BASE_URL}")
    print(f"- Luxembourg Code: {client.LUXEMBOURG_COUNTRY_CODE}")
    print(f"- Cache Enabled: {client.cache_enabled}")
    
    # Get cache stats
    cache_stats = client.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"- Enabled: {cache_stats['enabled']}")
    print(f"- Total Files: {cache_stats['total_files']}")
    print(f"- Total Size: {cache_stats['total_size_mb']} MB")
    
    print("\nFIBA API Client ready!")
    print("\nAvailable methods:")
    print("- get_competitions(zone, season)")
    print("- get_luxembourg_competitions(season)")
    print("- get_player_info(player_id)")
    print("- search_players(name, country_code)")
    print("- get_luxembourg_players()")
    print("- get_game_stats(game_id)")
    print("- get_team_roster(team_id, competition_id)")
    print("- enrich_player_data(player_name, flbb_data)")
    print("- get_national_team_games(country_code, season)")
    
    print("\n" + "=" * 80)
    print("Note: Actual API calls require internet access to FIBA endpoints")
    print("Some endpoints may require authentication with API key")
