#!/usr/bin/env python3
"""
Script to demonstrate the improved hotness index by comparing old vs new formula
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from src.utils import load_game_data, calculate_hotness_score, _calculate_game_statistics, _calculate_score_evolution, get_hotness_icon
import ast


def analyze_hotness_improvements():
    """Analyze and display hotness improvements across all games"""
    print("=" * 80)
    print("HOTNESS INDEX IMPROVEMENT ANALYSIS")
    print("=" * 80)
    print("\nComparing OLD formula (lead changes + ties only)")
    print("vs NEW formula (70% closeness + 30% volatility)\n")
    
    # Load data
    data = load_game_data()
    
    improvements = []
    
    for idx, row in data.iterrows():
        if pd.notna(row.get('GameEvents')):
            try:
                events = ast.literal_eval(row['GameEvents']) if isinstance(row['GameEvents'], str) else row['GameEvents']
                teams = ast.literal_eval(row['Teams']) if isinstance(row['Teams'], str) else row['Teams']
                
                score_evolution = _calculate_score_evolution(events, row['HomeTeamName'], row['AwayTeamName'], teams)
                game_stats = _calculate_game_statistics(score_evolution)
                
                hotness_old = calculate_hotness_score(game_stats['lead_changes'], game_stats['tied_scores'])
                hotness_new = calculate_hotness_score(game_stats['lead_changes'], game_stats['tied_scores'], game_stats['close_game_ratio'])
                
                improvement = hotness_new - hotness_old
                
                improvements.append({
                    'game_id': row['GameId'],
                    'home_team': row['HomeTeamName'],
                    'away_team': row['AwayTeamName'],
                    'score': f"{int(row['FinalHomeScore'])}-{int(row['FinalAwayScore'])}",
                    'lead_changes': game_stats['lead_changes'],
                    'ties': game_stats['tied_scores'],
                    'close_ratio': game_stats['close_game_ratio'],
                    'hotness_old': hotness_old,
                    'hotness_new': hotness_new,
                    'improvement': improvement,
                    'icon_old': get_hotness_icon(hotness_old),
                    'icon_new': get_hotness_icon(hotness_new)
                })
            except:
                continue
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(improvements)
    
    print(f"✅ Analyzed {len(df)} games\n")
    
    # Statistics
    print("OVERALL STATISTICS:")
    print("-" * 80)
    print(f"Average hotness OLD: {df['hotness_old'].mean():.1f}/100")
    print(f"Average hotness NEW: {df['hotness_new'].mean():.1f}/100")
    print(f"Average improvement: {df['improvement'].mean():.1f} points")
    print(f"Games improved: {(df['improvement'] > 0).sum()} ({(df['improvement'] > 0).sum()/len(df)*100:.1f}%)")
    print(f"Games unchanged: {(df['improvement'] == 0).sum()} ({(df['improvement'] == 0).sum()/len(df)*100:.1f}%)")
    print(f"Games decreased: {(df['improvement'] < 0).sum()} ({(df['improvement'] < 0).sum()/len(df)*100:.1f}%)")
    
    # Top improvements (close games that were underrated)
    print("\n" + "=" * 80)
    print("TOP 10 IMPROVEMENTS (Close games that were underrated by old formula)")
    print("=" * 80)
    print(f"{'Game':<45} {'Score':<10} {'Close%':<8} {'Old':<12} {'New':<12} {'Δ':<6}")
    print("-" * 80)
    
    top_improvements = df.nlargest(10, 'improvement')
    for _, game in top_improvements.iterrows():
        match_name = f"{game['home_team'][:20]} vs {game['away_team'][:20]}"
        print(f"{match_name:<45} {game['score']:<10} {game['close_ratio']:.1%}    "
              f"{game['icon_old']:<3} {game['hotness_old']:>3}   "
              f"{game['icon_new']:<3} {game['hotness_new']:>3}   "
              f"+{game['improvement']:>3}")
    
    # Games with high closeness but low volatility (the original problem case)
    print("\n" + "=" * 80)
    print("GAMES WITH HIGH CLOSENESS BUT LOW VOLATILITY")
    print("(The original problem: stayed close but few lead changes)")
    print("=" * 80)
    
    close_but_stable = df[(df['close_ratio'] > 0.6) & (df['lead_changes'] <= 5)]
    if len(close_but_stable) > 0:
        print(f"{'Game':<45} {'Score':<10} {'LC':<4} {'Ties':<5} {'Close%':<8} {'Old':<12} {'New':<12}")
        print("-" * 80)
        for _, game in close_but_stable.head(10).iterrows():
            match_name = f"{game['home_team'][:20]} vs {game['away_team'][:20]}"
            print(f"{match_name:<45} {game['score']:<10} {game['lead_changes']:<4} "
                  f"{game['ties']:<5} {game['close_ratio']:.1%}    "
                  f"{game['icon_old']:<3} {game['hotness_old']:>3}   "
                  f"{game['icon_new']:<3} {game['hotness_new']:>3}")
    else:
        print("No games found matching this criteria")
    
    # Blowouts (should stay low)
    print("\n" + "=" * 80)
    print("BLOWOUT GAMES (Should correctly have low hotness)")
    print("=" * 80)
    
    blowouts = df[df['close_ratio'] < 0.2]
    if len(blowouts) > 0:
        print(f"{'Game':<45} {'Score':<10} {'Close%':<8} {'Old':<12} {'New':<12}")
        print("-" * 80)
        for _, game in blowouts.head(10).iterrows():
            match_name = f"{game['home_team'][:20]} vs {game['away_team'][:20]}"
            print(f"{match_name:<45} {game['score']:<10} {game['close_ratio']:.1%}    "
                  f"{game['icon_old']:<3} {game['hotness_old']:>3}   "
                  f"{game['icon_new']:<3} {game['hotness_new']:>3}")
    else:
        print("No games found matching this criteria")
    
    print("\n" + "=" * 80)
    print("✅ Analysis Complete!")
    print("=" * 80)


if __name__ == '__main__':
    analyze_hotness_improvements()
