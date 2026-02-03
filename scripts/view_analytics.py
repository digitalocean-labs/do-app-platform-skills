#!/usr/bin/env python3
"""
View collected analytics data with visualizations and reports.

Usage:
    python scripts/view_analytics.py [--period 30] [--output report.html]
"""

import argparse
import json
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

ANALYTICS_DIR = Path('analytics')

def load_traffic_data():
    """Load historical traffic data."""
    file_path = ANALYTICS_DIR / 'traffic' / 'views.csv'
    if file_path.exists():
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        return df
    return pd.DataFrame()

def load_clones_data():
    """Load historical clones data."""
    file_path = ANALYTICS_DIR / 'clones' / 'clones.csv'
    if file_path.exists():
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        return df
    return pd.DataFrame()

def load_latest_summary():
    """Load the latest summary report."""
    file_path = ANALYTICS_DIR / 'latest_summary.json'
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def generate_report(days=30):
    """Generate a text report for the specified period."""
    traffic_df = load_traffic_data()
    clones_df = load_clones_data()
    summary = load_latest_summary()
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    print(f"\n{'='*70}")
    print(f"📊 GITHUB ANALYTICS REPORT - Last {days} Days")
    print(f"{'='*70}\n")
    
    if not traffic_df.empty:
        recent_traffic = traffic_df[traffic_df['date'] >= cutoff_date]
        if not recent_traffic.empty:
            print("📈 TRAFFIC SUMMARY")
            print(f"   Total Views: {recent_traffic['count'].sum():,}")
            print(f"   Unique Visitors: {recent_traffic['uniques'].sum():,}")
            print(f"   Avg Daily Views: {recent_traffic['count'].mean():.1f}")
            print(f"   Peak Day: {recent_traffic.loc[recent_traffic['count'].idxmax(), 'date'].strftime('%Y-%m-%d')} "
                  f"({recent_traffic['count'].max()} views)")
            print()
    
    if not clones_df.empty:
        recent_clones = clones_df[clones_df['date'] >= cutoff_date]
        if not recent_clones.empty:
            print("📥 CLONES SUMMARY")
            print(f"   Total Clones: {recent_clones['count'].sum():,}")
            print(f"   Unique Cloners: {recent_clones['uniques'].sum():,}")
            print(f"   Avg Daily Clones: {recent_clones['count'].mean():.1f}")
            print()
    
    if summary and summary.get('top_content'):
        print("🔥 MOST POPULAR CONTENT")
        for i, item in enumerate(summary['top_content'][:10], 1):
            print(f"   {i}. {item['path']:<50} {item['count']:>6} views ({item['uniques']} unique)")
        print()
    
    if summary and summary.get('top_referrers'):
        print("🔗 TOP REFERRERS")
        for i, item in enumerate(summary['top_referrers'][:10], 1):
            print(f"   {i}. {item['referrer']:<50} {item['count']:>6} visits")
        print()
    
    # Trend analysis
    if not traffic_df.empty and len(traffic_df) > days:
        recent = traffic_df[traffic_df['date'] >= cutoff_date]['count'].sum()
        previous = traffic_df[(traffic_df['date'] >= cutoff_date - timedelta(days=days)) & 
                             (traffic_df['date'] < cutoff_date)]['count'].sum()
        
        if previous > 0:
            change = ((recent - previous) / previous) * 100
            trend = "📈" if change > 0 else "📉"
            print(f"📊 TREND ANALYSIS")
            print(f"   {trend} Traffic change vs previous period: {change:+.1f}%")
            print()
    
    print(f"{'='*70}\n")
    
    # Show skills breakdown if available
    show_skills_breakdown()

def show_skills_breakdown():
    """Show breakdown by skill directory."""
    content_files = list((ANALYTICS_DIR / 'content').glob('*.csv'))
    
    if not content_files:
        return
    
    # Load all content data
    all_content = []
    for file in content_files:
        df = pd.read_csv(file)
        all_content.append(df)
    
    if not all_content:
        return
    
    content_df = pd.concat(all_content, ignore_index=True)
    
    # Extract skill from path
    content_df['skill'] = content_df['path'].apply(lambda x: 
        x.split('/')[1] if x.startswith('skills/') and len(x.split('/')) > 1 else 'other'
    )
    
    # Aggregate by skill
    skill_stats = content_df.groupby('skill').agg({
        'count': 'sum',
        'uniques': 'sum'
    }).sort_values('count', ascending=False)
    
    if not skill_stats.empty:
        print("🎯 USAGE BY SKILL")
        for skill, row in skill_stats.head(10).iterrows():
            print(f"   {skill:<30} {row['count']:>6} views ({row['uniques']} unique)")
        print()

def main():
    parser = argparse.ArgumentParser(description='View GitHub analytics data')
    parser.add_argument('--period', type=int, default=30, 
                       help='Number of days to include in report (default: 30)')
    parser.add_argument('--output', type=str, 
                       help='Optional: Save report to HTML file')
    
    args = parser.parse_args()
    
    if not ANALYTICS_DIR.exists():
        print("❌ No analytics data found. Run collect_analytics.py first.")
        return
    
    generate_report(days=args.period)
    
    if args.output:
        print(f"💾 HTML reports not yet implemented. Stay tuned!")

if __name__ == '__main__':
    main()
