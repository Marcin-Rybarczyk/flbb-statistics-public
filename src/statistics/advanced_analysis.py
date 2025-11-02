"""
Advanced Analysis Module

This module contains advanced statistical analysis functions including
player impact analysis, foul analysis, player combinations, and referee impact.

Note: These functions are temporarily imported from utils.py and will be
refactored into this module in a future update.
"""

# Temporary import - to be refactored later
import sys
import os

# Add parent directory to path if not already there
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def get_player_game_impact_analysis(data, top_n=20):
    """Import and call from utils.py"""
    from ..utils import get_player_game_impact_analysis as _func
    return _func(data, top_n)


def get_player_foul_impact_analysis(data, top_n=20):
    """Import and call from utils.py"""
    from ..utils import get_player_foul_impact_analysis as _func
    return _func(data, top_n)


def get_best_player_combinations(data, min_games=3):
    """Import and call from utils.py"""
    from ..utils import get_best_player_combinations as _func
    return _func(data, min_games)


def get_referee_game_impact_analysis(data):
    """Import and call from utils.py"""
    from ..utils import get_referee_game_impact_analysis as _func
    return _func(data)


__all__ = [
    'get_player_game_impact_analysis',
    'get_player_foul_impact_analysis',
    'get_best_player_combinations',
    'get_referee_game_impact_analysis'
]
