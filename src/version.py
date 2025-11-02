"""
Version information for FLBB Statistics website
"""
import subprocess
import os
from datetime import datetime

__version__ = "1.0.0"
__release_date__ = "2025-11-02"
__build_number__ = "1"

def get_last_modification_date():
    """
    Get the last modification date from Git commit history.
    Falls back to current date if Git is not available.
    """
    try:
        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_dir = os.path.dirname(current_dir)
        
        # Get last commit date
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cd', '--date=format:%Y-%m-%d'],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    
    # Fallback to release date if Git command fails
    return __release_date__

def get_version_info():
    """
    Returns a dictionary with version information including last modification date
    """
    last_modified = get_last_modification_date()
    return {
        'version': __version__,
        'release_date': __release_date__,
        'build_number': __build_number__,
        'last_modified': last_modified,
        'version_string': f"v{__version__} (Last modified: {last_modified})"
    }
