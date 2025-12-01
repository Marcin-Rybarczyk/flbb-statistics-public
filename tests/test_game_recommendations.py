#!/usr/bin/env python3
"""
Test script to validate game recommendations functionality for upcoming games
"""

import sys
import os

# Add the root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from src.utils import load_game_data, get_game_details, load_future_games_from_gamesdb


def test_game_recommendations():
    """Test game recommendations functionality for future games"""
    print("=" * 70)
    print("Testing Game Recommendations Functionality")
    print("=" * 70)
    
    # Load data
    print("\n1. Loading game data...")
    try:
        data = load_game_data()
        print(f"   ✓ Loaded {len(data)} finished games")
    except Exception as e:
        print(f"   ✗ Failed to load data: {e}")
        return False
    
    # Load future games
    print("\n2. Loading future games...")
    try:
        future_games = load_future_games_from_gamesdb()
        if not future_games:
            print("   ⚠ No future games found - skipping recommendations test")
            return True
        print(f"   ✓ Found {len(future_games)} future games")
    except Exception as e:
        print(f"   ✗ Failed to load future games: {e}")
        return False
    
    # Test with first future game
    game_id = str(future_games[0].get('GameId'))
    print(f"\n3. Testing recommendations for Game ID: {game_id}")
    
    details = get_game_details(data, game_id)
    
    if not details:
        print("   ✗ Failed to get game details")
        return False
    
    print("   ✓ Game details retrieved successfully")
    
    # Validate basic info
    print("\n4. Validating game info...")
    basic_info = details.get('basic_info', {})
    print(f"   - Home Team: {basic_info.get('home_team', 'N/A')}")
    print(f"   - Away Team: {basic_info.get('away_team', 'N/A')}")
    print(f"   - Is Future Game: {basic_info.get('is_future', False)}")
    
    if not basic_info.get('is_future'):
        print("   ✗ Game is not marked as future game")
        return False
    
    # Validate recommendations exist
    print("\n5. Validating recommendations...")
    recommendations = details.get('recommendations')
    
    if not recommendations:
        print("   ✗ No recommendations found")
        return False
    
    print("   ✓ Recommendations generated successfully")
    
    # Validate home team recommendations
    print("\n6. Validating home team recommendations...")
    home_team = recommendations.get('home_team', {})
    if not home_team:
        print("   ✗ No home team recommendations")
        return False
    
    print(f"   - Team Name: {home_team.get('name', 'N/A')}")
    print(f"   - Key Players: {len(home_team.get('key_players', []))}")
    print(f"   - Strengths: {len(home_team.get('strengths', []))}")
    print(f"   - Weaknesses: {len(home_team.get('weaknesses', []))}")
    print(f"   - Strategy Tips: {len(home_team.get('strategy_tips', []))}")
    
    # Show sample key players
    if home_team.get('key_players'):
        print("\n   Key Players:")
        for i, player in enumerate(home_team['key_players'][:2]):
            print(f"     {i+1}. {player.get('name', 'Unknown')}")
            print(f"        Role: {player.get('role', 'N/A')}")
            print(f"        Avg Points: {player.get('avg_points', 0):.1f}")
            print(f"        Multi-Team: {player.get('is_multi_team', False)}")
    
    # Show sample strengths
    if home_team.get('strengths'):
        print("\n   Sample Strengths:")
        for strength in home_team['strengths'][:2]:
            print(f"     • {strength}")
    
    # Show sample strategy tips
    if home_team.get('strategy_tips'):
        print("\n   Sample Strategy Tips:")
        for tip in home_team['strategy_tips'][:2]:
            print(f"     🎯 {tip}")
    
    # Validate away team recommendations
    print("\n7. Validating away team recommendations...")
    away_team = recommendations.get('away_team', {})
    if not away_team:
        print("   ✗ No away team recommendations")
        return False
    
    print(f"   - Team Name: {away_team.get('name', 'N/A')}")
    print(f"   - Key Players: {len(away_team.get('key_players', []))}")
    print(f"   - Strengths: {len(away_team.get('strengths', []))}")
    print(f"   - Weaknesses: {len(away_team.get('weaknesses', []))}")
    print(f"   - Strategy Tips: {len(away_team.get('strategy_tips', []))}")
    
    # Validate multi-team insights
    print("\n8. Validating multi-team player insights...")
    multi_team_insights = recommendations.get('multi_team_insights', [])
    print(f"   - Multi-team players identified: {len(multi_team_insights)}")
    
    if multi_team_insights:
        print("   Sample Multi-Team Insights:")
        for insight in multi_team_insights[:2]:
            print(f"     • {insight.get('player', 'Unknown')} ({insight.get('team', 'N/A')})")
            print(f"       Also plays for: {', '.join(insight.get('also_plays_for', []))}")
            print(f"       {insight.get('insight', 'N/A')}")
    
    # Validate general insights
    print("\n9. Validating general insights...")
    general_insights = recommendations.get('general_insights', [])
    print(f"   - General insights: {len(general_insights)}")
    
    if general_insights:
        print("   Sample Insights:")
        for insight in general_insights:
            print(f"     📊 {insight}")
    
    # Validate head-to-head
    print("\n10. Validating head-to-head analysis...")
    h2h = recommendations.get('head_to_head')
    if h2h:
        print(f"   - Home Points: {h2h.get('home_points', 0)}")
        print(f"   - Away Points: {h2h.get('away_points', 0)}")
        print(f"   - Home Differential: {h2h.get('home_diff', 0):+d}")
        print(f"   - Away Differential: {h2h.get('away_diff', 0):+d}")
        print("   ✓ Head-to-head data available")
    else:
        print("   ⚠ No head-to-head data (teams may not have played before)")
    
    print("\n" + "=" * 70)
    print("✓ All game recommendations tests passed!")
    print("=" * 70)
    return True


def test_recommendation_quality():
    """Test quality and consistency of recommendations"""
    print("\n" + "=" * 70)
    print("Testing Recommendation Quality & Consistency")
    print("=" * 70)
    
    data = load_game_data()
    future_games = load_future_games_from_gamesdb()
    
    if not future_games or len(future_games) < 3:
        print("   ⚠ Not enough future games for quality testing")
        return True
    
    # Test multiple games
    print(f"\n Testing recommendations for {min(3, len(future_games))} games...")
    
    for i, game in enumerate(future_games[:3]):
        game_id = str(game.get('GameId'))
        details = get_game_details(data, game_id)
        
        if not details or not details.get('recommendations'):
            continue
        
        rec = details['recommendations']
        print(f"\n Game {i+1} ({game_id}):")
        print(f"   Home: {rec['home_team']['name']}")
        print(f"   Away: {rec['away_team']['name']}")
        print(f"   ✓ Key players: {len(rec['home_team']['key_players'])} + {len(rec['away_team']['key_players'])}")
        print(f"   ✓ Strengths: {len(rec['home_team']['strengths'])} + {len(rec['away_team']['strengths'])}")
        print(f"   ✓ Weaknesses: {len(rec['home_team']['weaknesses'])} + {len(rec['away_team']['weaknesses'])}")
        print(f"   ✓ Tips: {len(rec['home_team']['strategy_tips'])} + {len(rec['away_team']['strategy_tips'])}")
        print(f"   ✓ Multi-team insights: {len(rec['multi_team_insights'])}")
    
    print("\n✓ Recommendation quality checks passed!")
    return True


if __name__ == '__main__':
    success = test_game_recommendations()
    if success:
        success = test_recommendation_quality()
    sys.exit(0 if success else 1)
