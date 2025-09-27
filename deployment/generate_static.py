#!/usr/bin/env python3
"""
Generate static HTML files for GitHub Pages deployment
This script generates static versions of the Flask pages that can be hosted on GitHub Pages
"""

import os
import json
from flask import Flask, render_template
import sys

# Add the root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import load_game_data, calculate_standings_by_division, get_highest_scoring_games

def generate_static_site():
    """Generate static HTML files for GitHub Pages"""
    
    # Load configuration
    config_path = 'config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {
            "website": {
                "title": "FLBB Basketball Statistics",
                "description": "Comprehensive basketball statistics for Luxembourg Basketball Federation"
            }
        }
    
    # Create output directory
    output_dir = 'static_site'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'static'), exist_ok=True)
    
    # Create a Flask app for template rendering
    app = Flask(__name__)
    
    # Load data
    data = load_game_data()
    
    if data.empty:
        print("No data available, creating placeholder site")
        divisions = []
    else:
        # Clean the data
        if 'Unnamed: 0' in data.columns:
            data = data.drop('Unnamed: 0', axis=1)
        divisions = data['GameDivisionDisplay'].unique()
    
    with app.app_context():
        # Generate index page (general overview)
        html_content = render_template('index.html', 
                                     divisions=divisions, 
                                     standings=None, 
                                     highest_games=None,
                                     selected_division=None)
        
        with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generate statistics page
        if not data.empty:
            highest_games = get_highest_scoring_games(data, 10)
        else:
            highest_games = None
            
        html_content = render_template('statistics.html',
                                     highest_games=highest_games,
                                     divisions=divisions,
                                     error=None if not data.empty else "No data available")
        
        with open(os.path.join(output_dir, 'statistics.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generate individual division pages
        for division in divisions:
            if not data.empty:
                standings = calculate_standings_by_division(data, division)
                division_data = data[data['GameDivisionDisplay'] == division]
                division_highest_games = get_highest_scoring_games(division_data, 5)
            else:
                standings = None
                division_highest_games = None
            
            html_content = render_template('index.html',
                                         divisions=divisions,
                                         standings=standings,
                                         highest_games=division_highest_games,
                                         selected_division=division)
            
            # Create safe filename
            safe_filename = division.replace(':', '-').replace(' ', '-').lower() + '.html'
            with open(os.path.join(output_dir, safe_filename), 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        # Generate navigation page with links to all divisions
        nav_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{config['website']['title']}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 10px 0; }}
        a {{ text-decoration: none; color: #007bff; padding: 10px 15px; display: block; border: 1px solid #ddd; border-radius: 4px; background-color: #f8f9fa; }}
        a:hover {{ background-color: #e9ecef; }}
        .nav-section {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{config['website']['title']}</h1>
        <p>{config['website']['description']}</p>
        
        <div class="nav-section">
            <h2>General Statistics</h2>
            <ul>
                <li><a href="statistics.html">Overall Statistics & Top Games</a></li>
            </ul>
        </div>
        
        <div class="nav-section">
            <h2>Division Standings</h2>
            <ul>"""
        
        for division in divisions:
            safe_filename = division.replace(':', '-').replace(' ', '-').lower() + '.html'
            nav_html += f'<li><a href="{safe_filename}">{division}</a></li>'
        
        nav_html += """
            </ul>
        </div>
        
        <div class="nav-section">
            <h2>About</h2>
            <p>This site provides comprehensive basketball statistics for the Luxembourg Basketball Federation (FLBB).</p>
            <p>Data is automatically updated daily from the official FLBB website.</p>
        </div>
    </div>
</body>
</html>"""
        
        # Write main navigation page as index.html
        with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(nav_html)
    
    print(f"Static site generated in {output_dir}/")
    print(f"Generated pages for {len(divisions)} divisions")

if __name__ == '__main__':
    generate_static_site()