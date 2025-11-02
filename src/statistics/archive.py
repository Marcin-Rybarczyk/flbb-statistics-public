"""
Archive Module

This module contains functions for managing season archives, including
validation, import, and listing of available archives.

Note: These functions are temporarily imported from utils.py and will be
refactored into this module in a future update.
"""


def validate_season_archive(zip_filepath):
    """Import and call from utils.py"""
    from ..utils import validate_season_archive as _func
    return _func(zip_filepath)


def import_season_archive(zip_filepath, target_season_dir=None):
    """Import and call from utils.py"""
    from ..utils import import_season_archive as _func
    return _func(zip_filepath, target_season_dir)


def list_available_archives(archive_dir='.'):
    """Import and call from utils.py"""
    from ..utils import list_available_archives as _func
    return _func(archive_dir)


__all__ = [
    'validate_season_archive',
    'import_season_archive',
    'list_available_archives'
]
