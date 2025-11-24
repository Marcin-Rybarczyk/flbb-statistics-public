#!/usr/bin/env python3
"""
Download and Export FLBB Data for Multiple Years

This script downloads basketball statistics data for multiple years from the
Luxembourg Basketball Federation and exports each year to a separate archive.

Usage:
    python scripts/download_multiple_years.py [options]
    
Options:
    --years N              Number of past years to download (default: 3)
    --start-year YEAR      Start year for range (e.g., 2020)
    --end-year YEAR        End year for range (e.g., 2023)
    --seasons "ID1,ID2"    Specific season IDs to process
    --export-only          Only export existing data, skip download
    --skip-download        Skip download phase, only process existing data
    --keep-data            Keep data in main directory after export
    --help, -h             Show this help message

Examples:
    # Download last 3 years
    python scripts/download_multiple_years.py
    
    # Download last 5 years
    python scripts/download_multiple_years.py --years 5
    
    # Download specific year range
    python scripts/download_multiple_years.py --start-year 2020 --end-year 2023
    
    # Download specific seasons
    python scripts/download_multiple_years.py --seasons "2022-2023,2023-2024"
    
    # Export only (don't download)
    python scripts/download_multiple_years.py --export-only
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import create_csv_from_json_data, load_data_from_directories

# Paths
ROOT_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
DATA_DIR = ROOT_DIR / "data"
ARCHIVES_DIR = ROOT_DIR / "archives"
SEASON_DATA_DIR = ROOT_DIR / "season-data"
CONFIG_FILE = SCRIPTS_DIR / "config.json"
BACKUP_CONFIG = SCRIPTS_DIR / "config.json.backup"
DOWNLOAD_SCRIPT = SCRIPTS_DIR / "download-controller.ps1"
EXPORT_SCRIPT = SCRIPTS_DIR / "export_data.py"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    """Print success message in green."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_info(msg):
    """Print info message in cyan."""
    print(f"{Colors.CYAN}ℹ {msg}{Colors.RESET}")

def print_warning(msg):
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_error(msg):
    """Print error message in red."""
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_header(msg):
    """Print header with separator."""
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}{msg}{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}\n")

def get_seasons_to_process(years=3, start_year=None, end_year=None, season_ids=None):
    """
    Determine which seasons to process based on parameters.
    
    Args:
        years: Number of past years to process
        start_year: Starting year for range
        end_year: Ending year for range
        season_ids: Specific season IDs to process
    
    Returns:
        List of season IDs (e.g., ["2022-2023", "2023-2024"])
    """
    seasons = []
    
    # If specific season IDs provided, use those
    if season_ids:
        seasons = [s.strip() for s in season_ids.split(',')]
        print_info(f"Using specified season IDs: {', '.join(seasons)}")
        return seasons
    
    # If year range specified, generate season IDs
    if start_year and end_year:
        if end_year < start_year:
            print_error("End year must be greater than or equal to start year")
            sys.exit(1)
        
        for year in range(start_year, end_year + 1):
            next_year = year + 1
            seasons.append(f"{year}-{next_year}")
        
        print_info(f"Generated season IDs from {start_year} to {end_year}: {', '.join(seasons)}")
        return seasons
    
    # Default: generate last N years
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # If in first half of year, consider we're still in previous season
    if current_month < 7:
        current_year -= 1
    
    for i in range(years):
        year = current_year - i
        next_year = year + 1
        seasons.append(f"{year}-{next_year}")
    
    print_info(f"Generated last {years} season IDs: {', '.join(seasons)}")
    return seasons

def backup_config():
    """Backup current configuration file."""
    try:
        if CONFIG_FILE.exists():
            shutil.copy2(CONFIG_FILE, BACKUP_CONFIG)
            print_success(f"Configuration backed up to {BACKUP_CONFIG}")
            return True
        else:
            print_error(f"Config file not found: {CONFIG_FILE}")
            return False
    except Exception as e:
        print_error(f"Failed to backup config: {e}")
        return False

def restore_config():
    """Restore backed up configuration file."""
    try:
        if BACKUP_CONFIG.exists():
            shutil.copy2(BACKUP_CONFIG, CONFIG_FILE)
            print_success("Configuration restored from backup")
            BACKUP_CONFIG.unlink()
            return True
        else:
            print_warning("No backup config file found")
            return False
    except Exception as e:
        print_error(f"Failed to restore config: {e}")
        return False

def update_config_for_season(season_id):
    """
    Update config.json with the specified season ID.
    
    Args:
        season_id: Season ID (e.g., "2022-2023")
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config['seasonId'] = season_id
        
        # Also update event name if it exists
        if 'eventName' in config:
            config['eventName'] = f"FLBB Basketball Season {season_id}"
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print_success(f"Updated config.json with season ID: {season_id}")
        return True
    except Exception as e:
        print_error(f"Failed to update config.json: {e}")
        return False

def run_download_script(season_id):
    """
    Run the PowerShell download script for the specified season.
    
    Args:
        season_id: Season ID
    
    Returns:
        True if successful, False otherwise
    """
    print_header(f"Downloading data for season {season_id}")
    
    if not DOWNLOAD_SCRIPT.exists():
        print_error(f"Download script not found: {DOWNLOAD_SCRIPT}")
        return False
    
    try:
        # Check if PowerShell is available
        pwsh_cmd = shutil.which('pwsh') or shutil.which('powershell')
        
        if not pwsh_cmd:
            print_error("PowerShell not found. Please install PowerShell Core (pwsh)")
            return False
        
        print_info(f"Using PowerShell: {pwsh_cmd}")
        
        # Run the download script
        result = subprocess.run(
            [pwsh_cmd, str(DOWNLOAD_SCRIPT)],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode == 0:
            print_success(f"Download completed for season {season_id}")
            return True
        else:
            print_warning(f"Download script exited with code {result.returncode}")
            return True  # Continue even with warnings
            
    except Exception as e:
        print_error(f"Error running download script: {e}")
        return False

def export_season_data(season_id, include_raw=True):
    """
    Export season data to archive.
    
    Args:
        season_id: Season ID
        include_raw: Include raw HTML data
    
    Returns:
        Path to created archive or None if failed
    """
    print_header(f"Exporting data for season {season_id}")
    
    # Create archives directory
    ARCHIVES_DIR.mkdir(exist_ok=True)
    
    # Generate archive filename
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    archive_name = f"raw-data-{season_id}-{timestamp}.zip"
    archive_path = ARCHIVES_DIR / archive_name
    
    try:
        # Check if export script exists
        if not EXPORT_SCRIPT.exists():
            print_warning(f"Export script not found: {EXPORT_SCRIPT}")
            return None
        
        # Build command
        cmd = [sys.executable, str(EXPORT_SCRIPT), '--output', str(archive_path)]
        if include_raw:
            cmd.append('--include-raw')
        
        # Run export script
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode == 0 and archive_path.exists():
            archive_size = archive_path.stat().st_size / (1024 * 1024)
            print_success(f"Archive created: {archive_path} ({archive_size:.2f} MB)")
            return str(archive_path)
        else:
            print_error("Export failed")
            return None
            
    except Exception as e:
        print_error(f"Error during export: {e}")
        return None

def move_data_to_season_directory(season_id, keep_data=False):
    """
    Move downloaded data to season-specific directory.
    
    Args:
        season_id: Season ID
        keep_data: If True, keep data in main directory
    
    Returns:
        True if successful, False otherwise
    """
    if keep_data:
        print_info("Keeping data in main data directory (--keep-data flag set)")
        return True
    
    season_dir = SEASON_DATA_DIR / season_id
    
    try:
        # Create season directory
        season_dir.mkdir(parents=True, exist_ok=True)
        
        # Items to move
        items_to_move = [
            DATA_DIR / "full-game-stats.csv",
            DATA_DIR / "gamesDB.json",
            DATA_DIR / "gameScheduleDB.json",
            DATA_DIR / "players-database.csv",
            DATA_DIR / "game-schedule-raw",
            DATA_DIR / "full-game-stats-raw",
            DATA_DIR / "full-game-stats-output"
        ]
        
        for item in items_to_move:
            if item.exists():
                dest = season_dir / item.name
                
                # Remove destination if exists
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                
                # Move item
                shutil.move(str(item), str(dest))
                print_info(f"Moved {item.name} to {season_dir}")
        
        print_success(f"Data moved to season directory: {season_dir}")
        return True
        
    except Exception as e:
        print_warning(f"Error moving data to season directory: {e}")
        return False

def show_summary(results):
    """
    Display summary of operations.
    
    Args:
        results: List of result dictionaries
    """
    print_header("Summary")
    
    total_seasons = len(results)
    successful_downloads = sum(1 for r in results if r.get('download_success'))
    successful_exports = sum(1 for r in results if r.get('export_success'))
    
    print(f"Total seasons processed: {total_seasons}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Successful exports: {successful_exports}")
    print()
    
    print(f"{Colors.CYAN}Details:{Colors.RESET}")
    for result in results:
        status = "✓" if result.get('export_success') else "✗"
        archive_info = f" → {result.get('archive_path', '')}" if result.get('archive_path') else ""
        print(f"  {status} Season {result['season_id']}{archive_info}")
    
    print()
    print(f"{Colors.CYAN}Archives location: {ARCHIVES_DIR}{Colors.RESET}")
    print(f"{Colors.CYAN}Season data location: {SEASON_DATA_DIR}/{Colors.RESET}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download and export FLBB data for multiple years",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download last 3 years
  python scripts/download_multiple_years.py
  
  # Download last 5 years
  python scripts/download_multiple_years.py --years 5
  
  # Download specific year range
  python scripts/download_multiple_years.py --start-year 2020 --end-year 2023
  
  # Download specific seasons
  python scripts/download_multiple_years.py --seasons "2022-2023,2023-2024"
  
  # Export only (don't download)
  python scripts/download_multiple_years.py --export-only
        """
    )
    
    parser.add_argument('--years', type=int, default=3,
                       help='Number of past years to download (default: 3)')
    parser.add_argument('--start-year', type=int,
                       help='Start year for range (e.g., 2020)')
    parser.add_argument('--end-year', type=int,
                       help='End year for range (e.g., 2023)')
    parser.add_argument('--seasons',
                       help='Comma-separated list of season IDs (e.g., "2022-2023,2023-2024")')
    parser.add_argument('--export-only', action='store_true',
                       help='Only export existing data, skip download')
    parser.add_argument('--skip-download', action='store_true',
                       help='Skip download phase, only process existing data')
    parser.add_argument('--keep-data', action='store_true',
                       help='Keep data in main directory after export')
    
    args = parser.parse_args()
    
    # Print header
    print_header("FLBB Archive Data Download and Export Tool")
    
    print("Parameters:")
    print(f"  Years: {args.years}")
    print(f"  Start Year: {args.start_year or 'N/A'}")
    print(f"  End Year: {args.end_year or 'N/A'}")
    print(f"  Seasons: {args.seasons or 'N/A'}")
    print(f"  Export Only: {args.export_only}")
    print(f"  Skip Download: {args.skip_download}")
    print(f"  Keep Data: {args.keep_data}")
    print()
    
    # Get seasons to process
    seasons = get_seasons_to_process(
        years=args.years,
        start_year=args.start_year,
        end_year=args.end_year,
        season_ids=args.seasons
    )
    
    if not seasons:
        print_error("No seasons to process")
        sys.exit(1)
    
    print()
    print(f"{Colors.GREEN}Will process {len(seasons)} season(s):{Colors.RESET}")
    for season in seasons:
        print(f"  - {season}")
    print()
    
    # Confirm with user (unless export-only)
    if not args.export_only:
        response = input("Continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print_info("Operation cancelled by user")
            sys.exit(0)
    
    # Backup configuration
    if not backup_config():
        print_error("Failed to backup configuration. Aborting.")
        sys.exit(1)
    
    # Process each season
    results = []
    
    try:
        for season_id in seasons:
            result = {
                'season_id': season_id,
                'download_success': False,
                'export_success': False,
                'archive_path': None
            }
            
            print_header(f"Processing Season: {season_id}")
            
            # Update configuration
            if not update_config_for_season(season_id):
                print_error(f"Failed to update configuration for {season_id}. Skipping...")
                results.append(result)
                continue
            
            # Download data (unless skipped or export-only)
            if not args.export_only and not args.skip_download:
                download_success = run_download_script(season_id)
                result['download_success'] = download_success
                
                if not download_success:
                    print_warning(f"Download failed for {season_id}. Continuing with export if data exists...")
            else:
                print_info(f"Skipping download for season {season_id}")
                result['download_success'] = True
            
            # Export data
            archive_path = export_season_data(season_id, include_raw=True)
            
            if archive_path:
                result['export_success'] = True
                result['archive_path'] = archive_path
            
            # Move data to season directory
            if result['export_success']:
                move_data_to_season_directory(season_id, args.keep_data)
            
            results.append(result)
            print()
            
    finally:
        # Always restore configuration
        print_header("Cleanup")
        restore_config()
    
    # Show summary
    show_summary(results)
    
    # Determine exit code
    has_failures = any(not r.get('export_success') for r in results)
    if has_failures:
        print_warning("Some seasons failed to process")
        sys.exit(1)
    else:
        print_success("All seasons processed successfully!")
        sys.exit(0)

if __name__ == '__main__':
    main()
