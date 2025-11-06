#!/usr/bin/env python3
"""
Test script to validate game detail page rendering and data structure
"""

import sys
import os

# Add the root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from src.utils import get_game_details

# Constants
MAX_TIMEOUT_DISPLAY = 3  # Maximum number of timeout markers to display in test output


def test_game_details():
    """Test game details functionality"""
    print("=" * 60)
    print("Testing Game Details Functionality")
    print("=" * 60)
    
    # Load data
    print("\n1. Loading game data...")
    try:
        df = pd.read_csv('data/full-game-stats.csv', encoding='utf-8-sig')
        print(f"   ✓ Loaded {len(df)} games")
    except Exception as e:
        print(f"   ✗ Failed to load data: {e}")
        return False
    
    # Test with first game
    game_id = str(df.iloc[0]['GameId'])
    print(f"\n2. Testing with Game ID: {game_id}")
    
    details = get_game_details(df, game_id)
    
    if not details:
        print("   ✗ Failed to get game details")
        return False
    
    print("   ✓ Game details retrieved successfully")
    
    # Test basic info
    print("\n3. Validating basic info...")
    basic_info = details.get('basic_info', {})
    print(f"   - Home Team: {basic_info.get('home_team', 'N/A')}")
    print(f"   - Away Team: {basic_info.get('away_team', 'N/A')}")
    print(f"   - Final Score: {basic_info.get('final_score', 'N/A')}")
    
    # Test referees (Fix #1)
    print("\n4. Validating referees (Fix #1)...")
    referees = details.get('referees', [])
    if referees:
        print(f"   ✓ Found {len(referees)} referee(s)")
        for ref in referees:
            print(f"     - {ref.get('Referee Name', 'Unknown')}")
    else:
        print("   ⚠ No referees found (may be normal for some games)")
    
    # Test teams - verify "W - xx points" is not needed (Fix #2)
    print("\n5. Validating team data (Fix #2)...")
    teams = details.get('teams', [])
    for team in teams:
        print(f"   - Team: {team.get('name', 'N/A')}")
        print(f"     Players: {len(team.get('players', []))}")
        # Note: We removed the "W - xx points" display from template
        print(f"     Total Points: {team.get('total_won_points', 0)}")
    
    # Test coach and timeouts (Fix #3)
    print("\n6. Validating coach and timeout info (Fix #3)...")
    for team in teams:
        coach = team.get('coach', 'N/A')
        timeouts = team.get('timeouts_used', 0)
        print(f"   - Team: {team.get('name', 'N/A')}")
        print(f"     Coach: {coach}")
        print(f"     Timeouts Used: {timeouts}")
        if coach != 'N/A' or timeouts > 0:
            print(f"     ✓ Coach/timeout info available")
    
    # Test score evolution (Fix #4)
    print("\n7. Validating score evolution (Fix #4)...")
    score_evolution = details.get('score_evolution', [])
    
    if not score_evolution:
        print("   ⚠ No score evolution data (may be normal for some games)")
    else:
        print(f"   ✓ Found {len(score_evolution)} data points")
        
        # Check for foul data (Fix #4a)
        points_with_fouls = [p for p in score_evolution if p.get('home_fouls', 0) > 0 or p.get('away_fouls', 0) > 0]
        print(f"   - Points with foul data: {len(points_with_fouls)}/{len(score_evolution)}")
        if points_with_fouls:
            print("     ✓ Foul tracking is working")
        
        # Check for timeout markers (Fix #4b)
        timeout_markers = [p for p in score_evolution if p.get('is_timeout', False)]
        print(f"   - Timeout markers: {len(timeout_markers)}")
        if timeout_markers:
            print("     ✓ Timeout markers are included")
            for tm in timeout_markers[:MAX_TIMEOUT_DISPLAY]:  # Show first few
                mins = int(tm.get('elapsed_seconds', 0) // 60)
                secs = int(tm.get('elapsed_seconds', 0) % 60)
                print(f"       - Q{tm.get('quarter', '?')} at {mins}:{secs:02d} ({tm.get('timeout_team', 'Unknown')})")
        else:
            print("     ⚠ No timeout markers (may be normal if no timeouts)")
        
        # Check quarter data (Fix #4c)
        quarters = set(p.get('quarter', 0) for p in score_evolution)
        print(f"   - Quarters represented: {sorted(quarters)}")
        if len(quarters) > 1:
            print("     ✓ Multiple quarters detected for boundary highlighting")
        
        # Check game start/end (Fix #4d)
        if score_evolution:
            start_time = score_evolution[0].get('elapsed_seconds', 0) / 60
            end_time = score_evolution[-1].get('elapsed_seconds', 0) / 60
            print(f"   - Game time range: {start_time:.1f} to {end_time:.1f} minutes")
            print("     ✓ Chart will use proper time boundaries")
    
    # Test quarter durations (New Feature)
    print("\n8. Validating quarter durations (New Feature)...")
    quarter_durations = details.get('quarter_durations', {})
    if not quarter_durations:
        print("   ✗ No quarter duration data found")
        return False
    
    # Separate numeric quarter keys from 'total' key
    numeric_quarters = sorted([q for q in quarter_durations.keys() if isinstance(q, int)])
    
    print(f"   ✓ Found durations for {len(numeric_quarters)} quarter(s)")
    total_duration = 0
    for quarter in numeric_quarters:
        info = quarter_durations[quarter]
        duration_formatted = info.get('duration_formatted', 'N/A')
        duration_seconds = info.get('duration_seconds', 0)
        print(f"   - Quarter {quarter}: {duration_formatted} ({duration_seconds:.1f} seconds)")
        total_duration += duration_seconds
        
        # Validate duration is reasonable (between 5 and 40 minutes)
        if duration_seconds < 300 or duration_seconds > 2400:
            print(f"     ⚠ Warning: Unusual quarter duration")
    
    total_mins = int(total_duration // 60)
    total_secs = int(total_duration % 60)
    print(f"   - Calculated total game time: {total_mins}:{total_secs:02d}")
    
    # Test the new total duration field
    if 'total' in quarter_durations:
        total_info = quarter_durations['total']
        print(f"   - Total from data structure: {total_info.get('duration_formatted', 'N/A')}")
        print("     ✓ Total duration field added successfully")
    else:
        print("   ✗ Total duration field not found in data structure")
        return False
    
    print("     ✓ Quarter durations calculated successfully")
    
    print("\n" + "=" * 60)
    print("✓ All game details tests passed!")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = test_game_details()
    sys.exit(0 if success else 1)
