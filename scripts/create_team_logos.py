#!/usr/bin/env python3
"""
Team Logo Creator for FLBB Statistics

This script creates default logos for all teams when actual logos cannot be downloaded.
It creates simple, professional-looking logos using team names and colors.
"""

import os
import sys
import pandas as pd
import re
from pathlib import Path
import textwrap

# Try to import PIL, will handle ImportError in main function if needed
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Configuration
LOGOS_DIR = "logos"
CSV_FILE = "data/full-game-stats.csv"
LOGO_SIZE = (200, 200)  # Width x Height in pixels
BACKGROUND_COLOR = (255, 255, 255)  # White background
DEFAULT_TEXT_COLOR = (0, 0, 0)  # Black text

# Team color mapping (common basketball team colors)
TEAM_COLORS = {
    "amicale-b": {"bg": (0, 51, 102), "text": (255, 255, 255)},       # Navy blue
    "bbc-nitia-b": {"bg": (255, 140, 0), "text": (255, 255, 255)},    # Orange
    "bc-mess-b": {"bg": (139, 0, 0), "text": (255, 255, 255)},        # Dark red
    "contern-c": {"bg": (0, 100, 0), "text": (255, 255, 255)},        # Green
    "grengewald-hostert-c": {"bg": (25, 25, 112), "text": (255, 255, 255)}, # Midnight blue
    "mamer-b": {"bg": (128, 0, 128), "text": (255, 255, 255)},        # Purple
    "racing-c": {"bg": (220, 20, 60), "text": (255, 255, 255)},       # Crimson
    "racing-d": {"bg": (178, 34, 34), "text": (255, 255, 255)},       # Fire brick
    "schieren-b": {"bg": (0, 128, 128), "text": (255, 255, 255)},     # Teal
    "sparta-c": {"bg": (75, 0, 130), "text": (255, 255, 255)},        # Indigo
}

def create_logos_directory():
    """Create logos directory if it doesn't exist"""
    Path(LOGOS_DIR).mkdir(exist_ok=True)
    print(f"Created/verified logos directory: {LOGOS_DIR}")

def get_unique_teams():
    """Extract unique team names from the CSV data"""
    try:
        df = pd.read_csv(CSV_FILE)
        home_teams = set(df['HomeTeamName'].dropna().unique())
        away_teams = set(df['AwayTeamName'].dropna().unique())
        all_teams = sorted(home_teams.union(away_teams))
        return all_teams
    except Exception as e:
        print(f"Error reading team data: {e}")
        return []

def normalize_team_name(team_name):
    """Normalize team name for file naming"""
    # Remove special characters and convert to lowercase
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', team_name)
    normalized = normalized.lower().replace(' ', '-')
    return normalized

def create_text_logo(team_name, output_path):
    """Create a simple text-based logo for a team"""
    try:
        # Create image
        img = Image.new('RGB', LOGO_SIZE, BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)
        
        # Get team colors
        normalized_name = normalize_team_name(team_name)
        colors = TEAM_COLORS.get(normalized_name, {
            "bg": (70, 130, 180),  # Steel blue default
            "text": (255, 255, 255)
        })
        
        # Fill background
        img = Image.new('RGB', LOGO_SIZE, colors["bg"])
        draw = ImageDraw.Draw(img)
        
        # Prepare text
        # Try to use a system font, fall back to default if not available
        font_size = 24
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Create team abbreviation (first letters of each word)
        words = team_name.split()
        if len(words) >= 2:
            abbrev = ''.join(word[0].upper() for word in words if word)
        else:
            abbrev = team_name[:3].upper()
        
        # Calculate text size and position
        text_bbox = draw.textbbox((0, 0), abbrev, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Center the text
        x = (LOGO_SIZE[0] - text_width) // 2
        y = (LOGO_SIZE[1] - text_height) // 2 - 20  # Slightly above center for abbreviation
        
        # Draw abbreviation
        draw.text((x, y), abbrev, font=font, fill=colors["text"])
        
        # Draw full team name below (smaller font)
        small_font_size = 12
        try:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", small_font_size)
        except:
            try:
                small_font = ImageFont.truetype("arial.ttf", small_font_size)
            except:
                small_font = ImageFont.load_default()
        
        # Wrap team name if it's too long
        max_chars_per_line = 20
        wrapped_name = textwrap.fill(team_name, max_chars_per_line)
        name_lines = wrapped_name.split('\n')
        
        # Draw each line of the team name
        line_height = 15
        start_y = y + text_height + 10
        for i, line in enumerate(name_lines):
            line_bbox = draw.textbbox((0, 0), line, font=small_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (LOGO_SIZE[0] - line_width) // 2
            line_y = start_y + (i * line_height)
            draw.text((line_x, line_y), line, font=small_font, fill=colors["text"])
        
        # Add a border
        border_color = tuple(max(0, c - 50) for c in colors["bg"])  # Darker version of bg
        draw.rectangle([(0, 0), (LOGO_SIZE[0]-1, LOGO_SIZE[1]-1)], outline=border_color, width=3)
        
        # Save image
        img.save(output_path, 'PNG', quality=95)
        return True
        
    except Exception as e:
        print(f"  ✗ Error creating logo: {e}")
        return False

def copy_existing_logo(src_path, dest_path):
    """Copy an existing logo file"""
    try:
        import shutil
        shutil.copy2(src_path, dest_path)
        return True
    except Exception as e:
        print(f"  ✗ Error copying logo: {e}")
        return False

def create_all_team_logos():
    """Main function to create logos for all teams"""
    print("FLBB Team Logo Creator")
    print("=" * 40)
    
    # Check if PIL is available
    if not PIL_AVAILABLE:
        print("PIL (Pillow) not available. Installing...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
            # Try to import again after installation
            global Image, ImageDraw, ImageFont
            from PIL import Image, ImageDraw, ImageFont
            print("✓ Pillow installed successfully")
        except Exception as e:
            print(f"✗ Failed to install Pillow: {e}")
            return False
    
    # Setup
    create_logos_directory()
    teams = get_unique_teams()
    
    if not teams:
        print("No teams found in data!")
        return False
    
    print(f"Found {len(teams)} unique teams:")
    for i, team in enumerate(teams, 1):
        print(f"  {i:2}. {team}")
    
    print("\nCreating team logos...")
    
    successful_creations = 0
    
    # Process each team
    for i, team_name in enumerate(teams, 1):
        print(f"\n[{i}/{len(teams)}] Processing: {team_name}")
        
        normalized_name = normalize_team_name(team_name)
        logo_path = os.path.join(LOGOS_DIR, f"{normalized_name}.png")
        
        # Check if logo already exists (various formats)
        existing_logo = None
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
            existing_path = os.path.join(LOGOS_DIR, f"{normalized_name}{ext}")
            if os.path.exists(existing_path):
                existing_logo = existing_path
                break
        
        # Special case for Racing teams - check if RAC.jpg should be used
        if not existing_logo and 'racing' in normalized_name:
            rac_path = os.path.join(LOGOS_DIR, "RAC.jpg")
            if os.path.exists(rac_path):
                existing_logo = rac_path
        
        if existing_logo:
            if existing_logo.endswith('.png') and existing_logo == logo_path:
                print(f"  → Logo already exists: {os.path.basename(existing_logo)}")
                successful_creations += 1
            else:
                # Copy/convert existing logo to standard format
                print(f"  → Found existing logo: {os.path.basename(existing_logo)}")
                if existing_logo.endswith(('.jpg', '.jpeg')):
                    # Convert JPG to PNG for consistency
                    try:
                        img = Image.open(existing_logo)
                        img = img.convert('RGB')
                        img.thumbnail(LOGO_SIZE, Image.Resampling.LANCZOS)
                        img.save(logo_path, 'PNG')
                        print(f"  ✓ Converted to PNG: {os.path.basename(logo_path)}")
                        successful_creations += 1
                    except Exception as e:
                        print(f"  ✗ Failed to convert: {e}")
                        # Fall back to creating text logo
                        if create_text_logo(team_name, logo_path):
                            print(f"  ✓ Created text logo: {os.path.basename(logo_path)}")
                            successful_creations += 1
                else:
                    print(f"  → Using existing logo: {os.path.basename(existing_logo)}")
                    successful_creations += 1
        else:
            # Create new text-based logo
            if create_text_logo(team_name, logo_path):
                print(f"  ✓ Created logo: {os.path.basename(logo_path)}")
                successful_creations += 1
    
    # Clean up placeholder files
    print("\nCleaning up placeholder files...")
    placeholder_files = [f for f in os.listdir(LOGOS_DIR) if f.endswith('_placeholder.txt')]
    for placeholder in placeholder_files:
        placeholder_path = os.path.join(LOGOS_DIR, placeholder)
        try:
            os.remove(placeholder_path)
            print(f"  ✓ Removed: {placeholder}")
        except Exception as e:
            print(f"  ✗ Failed to remove {placeholder}: {e}")
    
    # Summary
    print(f"\n" + "=" * 40)
    print(f"Logo Creation Summary:")
    print(f"  Successful: {successful_creations}")
    print(f"  Total teams: {len(teams)}")
    
    # List final logo files
    print(f"\nLogo files created:")
    logo_files = sorted([f for f in os.listdir(LOGOS_DIR) 
                        if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))])
    for logo_file in logo_files:
        print(f"  - {logo_file}")
    
    return successful_creations == len(teams)

if __name__ == "__main__":
    try:
        success = create_all_team_logos()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nLogo creation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)