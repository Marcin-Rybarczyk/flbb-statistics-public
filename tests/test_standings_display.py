#!/usr/bin/env python3
"""
Test script to verify standings display with H2H columns.
Generates a simple HTML preview of the standings table.
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import load_game_data, calculate_standings_by_division
import pandas as pd

def generate_standings_html(standings, division_name):
    """Generate HTML table for standings"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Standings Test - {division_name}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                padding: 20px;
                background: #f5f5f5;
            }}
            h1 {{
                color: #333;
            }}
            .info {{
                background: #e3f2fd;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
                border-left: 4px solid #2196f3;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 20px 0;
            }}
            th {{
                background: #2196f3;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }}
            td {{
                padding: 10px 12px;
                border-bottom: 1px solid #e0e0e0;
            }}
            tr:hover {{
                background: #f5f5f5;
            }}
            .tied {{
                background: #fff3e0 !important;
            }}
            .h2h-col {{
                background: #e8f5e9;
                font-weight: 600;
            }}
            .rank {{
                font-weight: 700;
                color: #2196f3;
            }}
            .positive {{
                color: #4caf50;
            }}
            .negative {{
                color: #f44336;
            }}
        </style>
    </head>
    <body>
        <h1>🏆 Standings for {division_name}</h1>
        
        <div class="info">
            <strong>✓ Head-to-Head Tiebreaker Implemented</strong><br>
            When teams have equal league points, the standings are determined by:<br>
            1. H2H Points (points earned in games between tied teams)<br>
            2. H2H Diff (score difference in games between tied teams)<br>
            3. Overall Points Diff (total score difference)<br>
            <br>
            Rows with yellow background indicate teams tied on league points.
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Team Name</th>
                    <th>Games</th>
                    <th>W</th>
                    <th>L</th>
                    <th>F</th>
                    <th>A</th>
                    <th>Pts Diff</th>
                    <th>League Pts</th>
                    <th class="h2h-col">H2H Pts</th>
                    <th class="h2h-col">H2H Diff</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Group teams by league points to highlight ties
    points_groups = standings.groupby('Points')['Team Name'].apply(list).to_dict()
    tied_teams = set()
    for teams in points_groups.values():
        if len(teams) >= 2:
            tied_teams.update(teams)
    
    # Generate table rows
    for idx, row in standings.iterrows():
        team_name = row['Team Name']
        is_tied = team_name in tied_teams
        row_class = 'tied' if is_tied else ''
        
        # Format score differences with color
        pts_diff = row['Points Diff']
        pts_diff_class = 'positive' if pts_diff > 0 else ('negative' if pts_diff < 0 else '')
        pts_diff_str = f"+{pts_diff}" if pts_diff > 0 else str(pts_diff)
        
        h2h_diff = row['H2H Diff']
        h2h_diff_class = 'positive' if h2h_diff > 0 else ('negative' if h2h_diff < 0 else '')
        h2h_diff_str = f"+{h2h_diff}" if h2h_diff > 0 else str(h2h_diff)
        
        html += f"""
                <tr class="{row_class}">
                    <td class="rank">{idx}</td>
                    <td><strong>{team_name}</strong></td>
                    <td>{row['Games']}</td>
                    <td>{row['W']}</td>
                    <td>{row['L']}</td>
                    <td>{row['F']}</td>
                    <td>{row['A']}</td>
                    <td class="{pts_diff_class}">{pts_diff_str}</td>
                    <td><strong>{row['Points']}</strong></td>
                    <td class="h2h-col">{int(row['H2H Points'])}</td>
                    <td class="h2h-col {h2h_diff_class}">{h2h_diff_str}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <div class="info">
            <strong>Note:</strong> Teams highlighted in yellow have the same league points. 
            Their ranking is determined by head-to-head records (green columns).
        </div>
    </body>
    </html>
    """
    
    return html


def main():
    """Generate and save standings HTML"""
    print("Loading game data...")
    data = load_game_data()
    
    if data.empty:
        print("❌ No data available")
        return 1
    
    print(f"✓ Loaded {len(data)} games")
    
    # Get divisions
    divisions = sorted(data['GameDivisionDisplay'].unique())
    print(f"✓ Found {len(divisions)} divisions")
    
    # Generate HTML for first division
    test_division = divisions[0]
    print(f"\nGenerating standings for: {test_division}")
    
    standings = calculate_standings_by_division(data, test_division)
    
    # Verify H2H columns exist
    if 'H2H Points' not in standings.columns or 'H2H Diff' not in standings.columns:
        print("❌ H2H columns not found in standings!")
        return 1
    
    print("✓ H2H columns present")
    
    # Find tied teams
    points_groups = standings.groupby('Points')['Team Name'].apply(list).to_dict()
    tied_groups = [(pts, teams) for pts, teams in points_groups.items() if len(teams) >= 2]
    
    if tied_groups:
        print(f"\n✓ Found {len(tied_groups)} groups of tied teams:")
        for pts, teams in tied_groups:
            print(f"  {pts} points: {', '.join(teams)}")
    else:
        print("\nℹ️  No tied teams in this division")
    
    # Generate HTML
    html = generate_standings_html(standings, test_division)
    
    # Save to file using tempfile for cross-platform compatibility
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html)
        output_file = f.name
    
    print(f"\n✓ HTML preview saved to: {output_file}")
    print(f"\nTop 5 teams:")
    print(standings[['Team Name', 'Points', 'H2H Points', 'H2H Diff', 'Points Diff']].head(5))
    
    return 0


if __name__ == '__main__':
    exit(main())
