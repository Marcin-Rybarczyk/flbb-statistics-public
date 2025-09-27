#!/usr/bin/env python3
"""
Generate static HTML files for Racing C team GitHub Pages deployment
This script generates static versions focused specifically on Racing C team data
"""

import os
import json
from flask import Flask, render_template
from utils import load_game_data, calculate_standings_by_division, get_highest_scoring_games

def filter_racing_c_data(data):
    """Filter data to include only games involving Racing C team"""
    if data.empty:
        return data
    
    racing_c_games = data[
        (data['HomeTeamName'] == 'Racing C') | 
        (data['AwayTeamName'] == 'Racing C')
    ].copy()
    
    return racing_c_games

def get_racing_c_stats(data):
    """Calculate Racing C specific statistics"""
    if data.empty:
        return {}
    
    racing_c_games = filter_racing_c_data(data)
    
    if racing_c_games.empty:
        return {}
    
    stats = {
        'total_games': len(racing_c_games),
        'wins': 0,
        'losses': 0,
        'points_scored': 0,
        'points_allowed': 0,
        'home_games': 0,
        'away_games': 0
    }
    
    for _, game in racing_c_games.iterrows():
        is_home = game['HomeTeamName'] == 'Racing C'
        
        if is_home:
            stats['home_games'] += 1
            racing_c_score = game['FinalHomeScore']
            opponent_score = game['FinalAwayScore']
        else:
            stats['away_games'] += 1
            racing_c_score = game['FinalAwayScore']
            opponent_score = game['FinalHomeScore']
        
        stats['points_scored'] += racing_c_score
        stats['points_allowed'] += opponent_score
        
        if racing_c_score > opponent_score:
            stats['wins'] += 1
        else:
            stats['losses'] += 1
    
    # Calculate averages
    if stats['total_games'] > 0:
        stats['avg_scored'] = round(stats['points_scored'] / stats['total_games'], 1)
        stats['avg_allowed'] = round(stats['points_allowed'] / stats['total_games'], 1)
        stats['win_percentage'] = round((stats['wins'] / stats['total_games']) * 100, 1)
    
    return stats

def generate_racing_c_static_site():
    """Generate static HTML files for Racing C team GitHub Pages"""
    
    # Load configuration
    config_path = 'config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {
            "website": {
                "title": "Racing C Basketball Statistics",
                "description": "Basketball statistics for Racing C team"
            }
        }
    
    # Customize config for Racing C
    config['website']['title'] = "Racing C Basketball Statistics"
    config['website']['description'] = "Official statistics and game results for Racing C basketball team"
    
    # Create output directory
    output_dir = 'racing-c-site'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'static'), exist_ok=True)
    
    # Create a Flask app for template rendering
    app = Flask(__name__)
    
    # Load data
    data = load_game_data()
    
    if data.empty:
        print("No data available, creating placeholder site")
        racing_c_games = data
        racing_c_stats = {}
        divisions = []
    else:
        # Filter for Racing C games only
        racing_c_games = filter_racing_c_data(data)
        racing_c_stats = get_racing_c_stats(data)
        
        # Clean the data
        if 'Unnamed: 0' in racing_c_games.columns:
            racing_c_games = racing_c_games.drop('Unnamed: 0', axis=1)
        divisions = racing_c_games['GameDivisionDisplay'].unique() if not racing_c_games.empty else []
    
    with app.app_context():
        # Generate Racing C main page
        if not racing_c_games.empty:
            # Get Racing C's division standings (but focus on Racing C)
            racing_division = racing_c_games['GameDivisionDisplay'].iloc[0]
            full_division_data = data[data['GameDivisionDisplay'] == racing_division]
            standings = calculate_standings_by_division(full_division_data, racing_division)
            
            # Get highest scoring Racing C games
            highest_games = get_highest_scoring_games(racing_c_games, 5)
        else:
            standings = None
            highest_games = None
            racing_division = None
        
        # Generate main Racing C page using index template
        html_content = render_template('index.html',
                                     divisions=divisions,
                                     standings=standings,
                                     highest_games=highest_games,
                                     selected_division=racing_division if racing_division else None)
        
        with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generate Racing C statistics page
        html_content = render_template('statistics.html',
                                     highest_games=highest_games,
                                     divisions=divisions,
                                     error=None if not racing_c_games.empty else "No Racing C data available")
        
        with open(os.path.join(output_dir, 'statistics.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generate Racing C navigation page
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
        .stats-highlight {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 15px 0; }}
        .stat-item {{ background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 24px; font-weight: bold; margin-bottom: 5px; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{config['website']['title']}</h1>
        <p>{config['website']['description']}</p>
        """
        
        # Add Racing C stats if available
        if racing_c_stats and racing_c_stats.get('total_games', 0) > 0:
            nav_html += f"""
        <div class="stats-highlight">
            <h2>Racing C Season Overview</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-number">{racing_c_stats['total_games']}</div>
                    <div class="stat-label">Games Played</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{racing_c_stats['wins']}-{racing_c_stats['losses']}</div>
                    <div class="stat-label">Win-Loss</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{racing_c_stats['win_percentage']}%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{racing_c_stats['avg_scored']}</div>
                    <div class="stat-label">Avg Points</div>
                </div>
            </div>
        </div>"""
        
        nav_html += """
        <div class="nav-section">
            <h2>Racing C Statistics</h2>
            <ul>
                <li><a href="statistics.html">Game Results & Top Performances</a></li>
            </ul>
        </div>
        """
        
        # Add division link if Racing C plays in a division
        if divisions and len(divisions) > 0:
            nav_html += """
        <div class="nav-section">
            <h2>Division Information</h2>
            <ul>"""
            
            for division in divisions:
                safe_filename = division.replace(':', '-').replace(' ', '-').lower() + '.html'
                nav_html += f'<li><a href="{safe_filename}">{division} Standings</a></li>'
            
            nav_html += """
            </ul>
        </div>"""
        
        nav_html += """
        <div class="nav-section">
            <h2>About Racing C</h2>
            <p>This site provides comprehensive basketball statistics specifically for Racing C team.</p>
            <p>Data includes game results, performance metrics, and division standings.</p>
        </div>
    </div>
</body>
</html>"""
        
        # Write Racing C navigation page as index.html
        with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(nav_html)
        
        # Generate division page if Racing C is in a division
        if not racing_c_games.empty and racing_division:
            full_division_data = data[data['GameDivisionDisplay'] == racing_division]
            standings = calculate_standings_by_division(full_division_data, racing_division)
            division_highest_games = get_highest_scoring_games(racing_c_games, 3)
            
            html_content = render_template('index.html',
                                         divisions=[racing_division],
                                         standings=standings,
                                         highest_games=division_highest_games,
                                         selected_division=racing_division)
            
            safe_filename = racing_division.replace(':', '-').replace(' ', '-').lower() + '.html'
            with open(os.path.join(output_dir, safe_filename), 'w', encoding='utf-8') as f:
                f.write(html_content)
    
    print(f"Racing C static site generated in {output_dir}/")
    print(f"Generated pages for Racing C team")
    if racing_c_stats:
        print(f"Racing C stats: {racing_c_stats['total_games']} games, {racing_c_stats['wins']}-{racing_c_stats['losses']} record, {racing_c_stats['win_percentage']}% win rate")

if __name__ == '__main__':
    generate_racing_c_static_site()