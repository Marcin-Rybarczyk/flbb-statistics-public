"""
FLBB Statistics Module

A modular statistics calculation package for the FLBB Basketball Statistics website.
This module organizes statistics calculations into logical components for better
maintainability and code organization.
"""

from .base import (
    get_data_source_info,
    load_config,
    get_season_info,
    get_season_archive_filename,
    get_website_config,
    load_game_data
)

from .player_stats import (
    extract_all_player_stats,
    get_top_scorers,
    get_highest_single_game_score,
    get_player_shooting_efficiency,
    get_starting_five_vs_bench_stats,
    get_double_digit_scorers,
    get_consistent_scorers,
    get_top_three_pointers,
    get_top_foulers,
    get_top_players_by_score
)

from .team_stats import (
    calculate_standings,
    calculate_standings_by_division,
    get_team_performance_stats,
    get_highest_scoring_games
)

from .referee_stats import (
    extract_referee_stats,
    get_referee_statistics,
    get_referee_fouls_per_game,
    get_referees_least_fouls_per_game
)

from .game_analysis import (
    analyze_game_events,
    get_most_tie_scores,
    get_most_lead_changes,
    get_biggest_leads,
    get_biggest_wins
)

from .advanced_analysis import (
    get_player_game_impact_analysis,
    get_player_foul_impact_analysis,
    get_best_player_combinations,
    get_referee_game_impact_analysis
)

from .fixtures import (
    get_all_fixtures_data,
    get_fixtures_matrix_data,
    parse_location_name,
    parse_referees,
    get_game_top_scorer,
    get_top_scorer_by_game
)

from .archive import (
    validate_season_archive,
    import_season_archive,
    list_available_archives
)

__all__ = [
    # Base
    'get_data_source_info',
    'load_config',
    'get_season_info',
    'get_season_archive_filename',
    'get_website_config',
    'load_game_data',
    
    # Player Statistics
    'extract_all_player_stats',
    'get_top_scorers',
    'get_highest_single_game_score',
    'get_player_shooting_efficiency',
    'get_starting_five_vs_bench_stats',
    'get_double_digit_scorers',
    'get_consistent_scorers',
    'get_top_three_pointers',
    'get_top_foulers',
    'get_top_players_by_score',
    
    # Team Statistics
    'calculate_standings',
    'calculate_standings_by_division',
    'get_team_performance_stats',
    'get_highest_scoring_games',
    
    # Referee Statistics
    'extract_referee_stats',
    'get_referee_statistics',
    'get_referee_fouls_per_game',
    'get_referees_least_fouls_per_game',
    
    # Game Analysis
    'analyze_game_events',
    'get_most_tie_scores',
    'get_most_lead_changes',
    'get_biggest_leads',
    'get_biggest_wins',
    
    # Advanced Analysis
    'get_player_game_impact_analysis',
    'get_player_foul_impact_analysis',
    'get_best_player_combinations',
    'get_referee_game_impact_analysis',
    
    # Fixtures
    'get_all_fixtures_data',
    'get_fixtures_matrix_data',
    'parse_location_name',
    'parse_referees',
    'get_game_top_scorer',
    'get_top_scorer_by_game',
    
    # Archive
    'validate_season_archive',
    'import_season_archive',
    'list_available_archives',
]
