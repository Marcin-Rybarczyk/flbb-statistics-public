"""
Version information for FLBB Statistics website
"""

__version__ = "1.0.0"
__release_date__ = "2025-11-02"
__build_number__ = "1"

def get_version_info():
    """
    Returns a dictionary with version information
    """
    return {
        'version': __version__,
        'release_date': __release_date__,
        'build_number': __build_number__,
        'version_string': f"v{__version__}"
    }
