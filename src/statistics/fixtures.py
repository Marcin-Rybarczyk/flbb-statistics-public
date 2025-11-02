"""
Fixtures Module

This module contains functions for handling fixtures data, including
fixture listings, matrix displays, and game-specific information.

Note: These functions are temporarily imported from utils.py and will be
refactored into this module in a future update.
"""


def get_all_fixtures_data(data):
    """Import and call from utils.py"""
    from ..utils import get_all_fixtures_data as _func
    return _func(data)


def get_fixtures_matrix_data(data, division_filter=None):
    """Import and call from utils.py"""
    from ..utils import get_fixtures_matrix_data as _func
    return _func(data, division_filter)


def parse_location_name(location_data):
    """Import and call from utils.py"""
    from ..utils import parse_location_name as _func
    return _func(location_data)


def parse_referees(referees_data):
    """Import and call from utils.py"""
    from ..utils import parse_referees as _func
    return _func(referees_data)


def get_game_top_scorer(game):
    """Import and call from utils.py"""
    from ..utils import get_game_top_scorer as _func
    return _func(game)


def get_top_scorer_by_game(data):
    """Import and call from utils.py"""
    from ..utils import get_top_scorer_by_game as _func
    return _func(data)


__all__ = [
    'get_all_fixtures_data',
    'get_fixtures_matrix_data',
    'parse_location_name',
    'parse_referees',
    'get_game_top_scorer',
    'get_top_scorer_by_game'
]
