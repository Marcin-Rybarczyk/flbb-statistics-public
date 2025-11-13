#!/usr/bin/env python3
"""
Export Website Data Script

This script exports all data used by the FLBB Statistics website into a ZIP archive.
The archive can be imported later to restore data from past seasons.

Usage:
    python scripts/export_data.py [options]
    
Options:
    --output, -o PATH      Output path for the ZIP file (default: auto-generated)
    --season SEASON        Season ID (e.g., "2024-2025") - auto-detected from config
    --config CONFIG        Path to config.json (default: scripts/config.json)
    --include-raw          Include raw HTML data directories
    --help, -h             Show this help message

Examples:
    # Export with default settings
    python scripts/export_data.py
    
    # Export to specific file
    python scripts/export_data.py -o my-archive.zip
    
    # Export with raw HTML data
    python scripts/export_data.py --include-raw
"""

import os
import sys
import json
import zipfile
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_config(config_file):
    """Load configuration from JSON file."""
    if not os.path.exists(config_file):
        print(f"Warning: Config file {config_file} not found")
        return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def get_file_size_mb(filepath):
    """Get file size in MB."""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0

def export_data(output_path=None, config_file="scripts/config.json", include_raw=False):
    """
    Export website data to ZIP archive.
    
    Parameters:
        output_path (str): Path for output ZIP file (optional)
        config_file (str): Path to configuration file
        include_raw (bool): Include raw HTML data directories
    
    Returns:
        tuple: (success: bool, zip_filepath: str, message: str)
    """
    print("=" * 70)
    print("FLBB Statistics Data Export")
    print("=" * 70)
    
    # Load configuration
    config = load_config(config_file)
    season_id = config.get("seasonId", "unknown")
    
    # Determine output path
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        archives_dir = Path("archives")
        archives_dir.mkdir(exist_ok=True)
        
        if season_id != "unknown":
            output_path = archives_dir / f"raw-data-{season_id}-{timestamp}.zip"
        else:
            output_path = archives_dir / f"raw-data-{timestamp}.zip"
    else:
        output_path = Path(output_path)
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\nSeason ID: {season_id}")
    print(f"Output file: {output_path}")
    print(f"Include raw data: {include_raw}")
    print()
    
    # Define data root
    data_root = Path("data")
    
    # Files to include (relative to repository root)
    files_to_include = []
    
    # Essential CSV and JSON files
    essential_files = [
        data_root / "full-game-stats.csv",
        data_root / "gamesDB.json",
        data_root / "gameScheduleDB.json",
        data_root / "players-database.csv",
    ]
    
    for filepath in essential_files:
        if filepath.exists():
            files_to_include.append(filepath)
            print(f"✓ Found: {filepath} ({get_file_size_mb(filepath):.2f} MB)")
        else:
            print(f"⚠ Missing: {filepath}")
    
    # Optional raw data directories
    if include_raw:
        raw_directories = [
            data_root / config.get("directories", {}).get("gameScheduleRaw", "game-schedule-raw"),
            data_root / config.get("directories", {}).get("fullGameStatsRaw", "full-game-stats-raw"),
            data_root / config.get("directories", {}).get("fullGameStatsOutput", "full-game-stats-output"),
        ]
        
        for dir_path in raw_directories:
            if dir_path.exists() and dir_path.is_dir():
                file_count = len(list(dir_path.rglob('*')))
                print(f"✓ Found directory: {dir_path} ({file_count} files)")
    
    # Create the archive
    print(f"\n📦 Creating archive: {output_path}")
    print("-" * 70)
    
    try:
        files_added = 0
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            # Add essential files
            for filepath in files_to_include:
                if filepath.exists():
                    arcname = str(filepath)
                    zipf.write(filepath, arcname)
                    files_added += 1
                    print(f"  Added: {arcname}")
            
            # Add raw data directories if requested
            if include_raw:
                for dir_path in raw_directories:
                    if dir_path.exists() and dir_path.is_dir():
                        for root, dirs, files in os.walk(dir_path):
                            for file in files:
                                file_path = Path(root) / file
                                arcname = str(file_path)
                                zipf.write(file_path, arcname)
                                files_added += 1
                                if files_added <= 20:  # Only show first 20 for brevity
                                    print(f"  Added: {arcname}")
                        
                        if files_added > 20:
                            print(f"  ... and {files_added - 20} more files")
        
        # Get final archive size
        archive_size = get_file_size_mb(output_path)
        
        print("-" * 70)
        print(f"✅ SUCCESS: Archive created successfully!")
        print(f"\n📊 Summary:")
        print(f"   Files archived: {files_added}")
        print(f"   Archive size: {archive_size:.2f} MB")
        print(f"   Archive path: {output_path.absolute()}")
        print(f"\n💡 To import this archive:")
        print(f"   python scripts/import_data.py {output_path}")
        print("=" * 70)
        
        return True, str(output_path), f"Successfully exported {files_added} files ({archive_size:.2f} MB)"
        
    except Exception as e:
        error_msg = f"Error creating archive: {e}"
        print(f"\n❌ ERROR: {error_msg}")
        print("=" * 70)
        return False, None, error_msg

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Export FLBB Statistics website data to ZIP archive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export with default settings
  python scripts/export_data.py
  
  # Export to specific file
  python scripts/export_data.py -o my-backup.zip
  
  # Export including raw HTML data (larger archive)
  python scripts/export_data.py --include-raw
  
  # Use custom config file
  python scripts/export_data.py --config my-config.json
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output path for ZIP file (default: auto-generated in archives/)',
        default=None
    )
    
    parser.add_argument(
        '--season',
        help='Season ID (e.g., "2024-2025") - overrides config',
        default=None
    )
    
    parser.add_argument(
        '--config',
        help='Path to config.json (default: scripts/config.json)',
        default='scripts/config.json'
    )
    
    parser.add_argument(
        '--include-raw',
        help='Include raw HTML data directories (creates larger archive)',
        action='store_true'
    )
    
    args = parser.parse_args()
    
    # Override season in config if provided
    if args.season:
        config = load_config(args.config)
        config['seasonId'] = args.season
        # Save temporarily (won't affect actual config file)
    
    # Run export
    success, archive_path, message = export_data(
        output_path=args.output,
        config_file=args.config,
        include_raw=args.include_raw
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
