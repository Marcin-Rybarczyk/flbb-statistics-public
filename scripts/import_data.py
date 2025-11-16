#!/usr/bin/env python3
"""
Import Website Data Script

This script imports data from a ZIP archive created by export_data.py.
The archive contains data from a specific season that can be restored.

Usage:
    python scripts/import_data.py ARCHIVE_FILE [options]
    
Arguments:
    ARCHIVE_FILE           Path to the ZIP archive to import
    
Options:
    --target, -t DIR       Target directory for extraction (default: auto-generated)
    --validate-only        Only validate the archive without importing
    --force                Overwrite existing files without confirmation
    --restore              Restore to current data directory (replaces current data)
    --help, -h             Show this help message

Examples:
    # Validate an archive
    python scripts/import_data.py archive.zip --validate-only
    
    # Import to a new directory
    python scripts/import_data.py archive.zip
    
    # Import to specific directory
    python scripts/import_data.py archive.zip -t season-2023-2024
    
    # Restore to current data directory (BE CAREFUL!)
    python scripts/import_data.py archive.zip --restore --force
"""

import os
import sys
import zipfile
import argparse
import shutil
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import validate_season_archive

def get_file_size_mb(filepath):
    """Get file size in MB."""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0

def validate_archive(archive_path):
    """
    Validate archive contents.
    
    Parameters:
        archive_path (str): Path to ZIP archive
    
    Returns:
        dict: Validation result with details
    """
    print("=" * 70)
    print("Archive Validation")
    print("=" * 70)
    print(f"\nArchive: {archive_path}")
    print(f"Size: {get_file_size_mb(archive_path):.2f} MB")
    print()
    
    # Use existing validation function
    result = validate_season_archive(archive_path)
    
    if result['valid']:
        print("✅ Archive is VALID")
        if result['season_id']:
            print(f"   Season ID: {result['season_id']}")
        print(f"   Files found: {len(result['files_found'])}")
        
        # Show some key files
        key_files = [f for f in result['files_found'] if f.endswith('.csv') or f.endswith('.json')]
        if key_files:
            print(f"\n📄 Key files in archive:")
            for f in key_files[:10]:  # Show first 10
                print(f"   - {f}")
            if len(key_files) > 10:
                print(f"   ... and {len(key_files) - 10} more")
    else:
        print("❌ Archive is INVALID")
        for error in result['errors']:
            print(f"   Error: {error}")
    
    print("=" * 70)
    return result

def import_data(archive_path, target_dir=None, force=False, restore=False):
    """
    Import data from archive.
    
    Parameters:
        archive_path (str): Path to ZIP archive
        target_dir (str): Target directory for extraction (optional)
        force (bool): Overwrite existing files without confirmation
        restore (bool): Restore to current data directory
    
    Returns:
        tuple: (success: bool, target_path: str, message: str)
    """
    print("=" * 70)
    print("FLBB Statistics Data Import")
    print("=" * 70)
    
    # First validate the archive
    validation = validate_season_archive(archive_path)
    if not validation['valid']:
        error_msg = "Archive validation failed: " + "; ".join(validation['errors'])
        print(f"\n❌ ERROR: {error_msg}")
        print("=" * 70)
        return False, None, error_msg
    
    season_id = validation['season_id'] or 'unknown'
    print(f"\n✓ Archive validated successfully")
    print(f"  Season ID: {season_id}")
    print(f"  Files: {len(validation['files_found'])}")
    print()
    
    # Determine target directory
    if restore:
        # Restore to current data directory
        target_path = Path("data")
        print(f"⚠️  RESTORE MODE: Will replace files in {target_path}/")
        
        if not force:
            # Ask for confirmation
            response = input("\nThis will OVERWRITE existing data. Are you sure? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Import cancelled by user")
                return False, None, "Import cancelled by user"
        
        # Backup current data before restore
        backup_dir = Path(f"data-backup-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        print(f"\n📦 Creating backup: {backup_dir}/")
        
        if target_path.exists():
            try:
                shutil.copytree(target_path, backup_dir)
                print(f"   ✓ Backup created successfully")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not create backup: {e}")
    
    elif target_dir:
        # Use specified directory
        target_path = Path(target_dir)
    else:
        # Auto-generate directory name
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        target_path = Path(f"archive-{season_id}-{timestamp}")
    
    # Check if target exists
    if target_path.exists() and not restore:
        if not force:
            response = input(f"\n⚠️  Target directory {target_path} exists. Overwrite? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Import cancelled by user")
                return False, None, "Import cancelled by user"
        
        print(f"Removing existing directory: {target_path}")
        shutil.rmtree(target_path)
    
    # Create target directory
    target_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📂 Extracting to: {target_path.absolute()}")
    print("-" * 70)
    
    # Extract the archive
    try:
        files_extracted = 0
        with zipfile.ZipFile(archive_path, 'r') as zipf:
            # Get list of files to extract
            file_list = zipf.namelist()
            
            for file_name in file_list:
                # Extract file
                if restore:
                    # In restore mode, extract to repository root to maintain structure
                    zipf.extract(file_name, ".")
                else:
                    # In normal mode, extract to target directory
                    zipf.extract(file_name, target_path)
                
                files_extracted += 1
                if files_extracted <= 20:  # Show first 20
                    print(f"  Extracted: {file_name}")
            
            if files_extracted > 20:
                print(f"  ... and {files_extracted - 20} more files")
        
        print("-" * 70)
        print(f"✅ SUCCESS: Data imported successfully!")
        print(f"\n📊 Summary:")
        print(f"   Files extracted: {files_extracted}")
        print(f"   Target directory: {target_path.absolute()}")
        
        if restore:
            print(f"\n✓ Data has been restored to: data/")
            print(f"  Backup saved to: {backup_dir}/ (if created)")
        else:
            print(f"\n💡 To use this data:")
            print(f"   1. Copy files from {target_path}/ to data/")
            print(f"   2. Or update your config to point to this directory")
            print(f"   3. Restart the application")
        
        print("=" * 70)
        
        return True, str(target_path), f"Successfully imported {files_extracted} files"
        
    except Exception as e:
        error_msg = f"Error extracting archive: {e}"
        print(f"\n❌ ERROR: {error_msg}")
        print("=" * 70)
        return False, None, error_msg

def list_archives():
    """List available archives in the archives directory."""
    print("=" * 70)
    print("Available Archives")
    print("=" * 70)
    
    archives_dir = Path("archives")
    if not archives_dir.exists():
        print("\nNo archives directory found")
        print("=" * 70)
        return
    
    archives = sorted(archives_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not archives:
        print("\nNo archive files found in archives/")
        print("=" * 70)
        return
    
    print(f"\nFound {len(archives)} archive(s):\n")
    
    for archive in archives:
        size_mb = get_file_size_mb(archive)
        mod_time = datetime.fromtimestamp(archive.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Quick validation
        validation = validate_season_archive(str(archive))
        status = "✓ Valid" if validation['valid'] else "✗ Invalid"
        season = validation.get('season_id', 'Unknown')
        
        print(f"  {archive.name}")
        print(f"    Season: {season}")
        print(f"    Size: {size_mb:.2f} MB")
        print(f"    Modified: {mod_time}")
        print(f"    Status: {status}")
        print()
    
    print("=" * 70)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Import FLBB Statistics data from ZIP archive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available archives
  python scripts/import_data.py --list
  
  # Validate an archive
  python scripts/import_data.py archive.zip --validate-only
  
  # Import to new directory
  python scripts/import_data.py archive.zip
  
  # Import to specific directory
  python scripts/import_data.py archive.zip -t season-2023-2024
  
  # Restore to current data directory (CAUTION!)
  python scripts/import_data.py archive.zip --restore --force

⚠️  WARNING: --restore mode will replace your current data!
        """
    )
    
    parser.add_argument(
        'archive',
        nargs='?',
        help='Path to ZIP archive to import'
    )
    
    parser.add_argument(
        '--target', '-t',
        help='Target directory for extraction (default: auto-generated)',
        default=None
    )
    
    parser.add_argument(
        '--validate-only',
        help='Only validate the archive without importing',
        action='store_true'
    )
    
    parser.add_argument(
        '--force',
        help='Overwrite existing files without confirmation',
        action='store_true'
    )
    
    parser.add_argument(
        '--restore',
        help='Restore to current data directory (replaces current data)',
        action='store_true'
    )
    
    parser.add_argument(
        '--list',
        help='List available archives in archives/ directory',
        action='store_true'
    )
    
    args = parser.parse_args()
    
    # Handle list command
    if args.list:
        list_archives()
        sys.exit(0)
    
    # Require archive path for other operations
    if not args.archive:
        parser.print_help()
        print("\n❌ ERROR: Archive file path is required (or use --list)")
        sys.exit(1)
    
    # Check if archive exists
    if not os.path.exists(args.archive):
        print(f"❌ ERROR: Archive file not found: {args.archive}")
        sys.exit(1)
    
    # Validate only mode
    if args.validate_only:
        result = validate_archive(args.archive)
        sys.exit(0 if result['valid'] else 1)
    
    # Import the archive
    success, target_path, message = import_data(
        archive_path=args.archive,
        target_dir=args.target,
        force=args.force,
        restore=args.restore
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
