#!/usr/bin/env python3
"""
Collect GitHub repository analytics and store them for historical tracking.

This script collects:
- Traffic (views, unique visitors)
- Clones (count, unique cloners)
- Popular content (most viewed files)
- Referring sites
- Top paths

Data is stored in CSV format in analytics/ directory.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from github import Github, Auth
import pandas as pd

# Configuration
REPO_OWNER = os.environ.get('REPO_OWNER')
REPO_NAME = os.environ.get('REPO_NAME')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
ANALYTICS_DIR = Path('analytics')

def setup_analytics_directory():
    """Create analytics directory structure."""
    ANALYTICS_DIR.mkdir(exist_ok=True)
    (ANALYTICS_DIR / 'traffic').mkdir(exist_ok=True)
    (ANALYTICS_DIR / 'clones').mkdir(exist_ok=True)
    (ANALYTICS_DIR / 'content').mkdir(exist_ok=True)
    (ANALYTICS_DIR / 'referrers').mkdir(exist_ok=True)

def collect_traffic_data(repo):
    """Collect traffic (views) data."""
    print("Collecting traffic data...")
    try:
        views_data = repo.get_views_traffic(per="day")
    except Exception as e:
        print(f"⚠️  Warning: Cannot access traffic data: {e}")
        print("   This requires a Personal Access Token with 'repo' scope.")
        print("   See analytics/README.md for setup instructions.")
        return []
    
    data = []
    # views_data is a View object with a 'views' attribute containing the list
    for view in views_data.get('views', []) if isinstance(views_data, dict) else (views_data.views if hasattr(views_data, 'views') else []):
        data.append({
            'date': view.timestamp.strftime('%Y-%m-%d'),
            'count': view.count,
            'uniques': view.uniques,
            'collected_at': datetime.now(timezone.utc).isoformat()
        })
    
    if data:
        df = pd.DataFrame(data)
        file_path = ANALYTICS_DIR / 'traffic' / 'views.csv'
        
        # Append to existing data if file exists
        if file_path.exists():
            existing_df = pd.read_csv(file_path)
            df = pd.concat([existing_df, df]).drop_duplicates(subset=['date'], keep='last')
        
        df.to_csv(file_path, index=False)
        print(f"✓ Saved {len(data)} traffic records")
        return data
    return []

def collect_clones_data(repo):
    """Collect clones data."""
    print("Collecting clones data...")
    try:
        clones_data = repo.get_clones_traffic(per="day")
    except Exception as e:
        print(f"⚠️  Warning: Cannot access clones data: {e}")
        return []
    
    data = []
    # clones_data is a Clones object with a 'clones' attribute containing the list
    for clone in clones_data.get('clones', []) if isinstance(clones_data, dict) else (clones_data.clones if hasattr(clones_data, 'clones') else []):
        data.append({
            'date': clone.timestamp.strftime('%Y-%m-%d'),
            'count': clone.count,
            'uniques': clone.uniques,
            'collected_at': datetime.now(timezone.utc).isoformat()
        })
    
    if data:
        df = pd.DataFrame(data)
        file_path = ANALYTICS_DIR / 'clones' / 'clones.csv'
        
        # Append to existing data if file exists
        if file_path.exists():
            existing_df = pd.read_csv(file_path)
            df = pd.concat([existing_df, df]).drop_duplicates(subset=['date'], keep='last')
        
        df.to_csv(file_path, index=False)
        print(f"✓ Saved {len(data)} clone records")
        return data
    return []

def collect_popular_content(repo):
    """Collect popular content (most viewed paths)."""
    print("Collecting popular content...")
    paths = repo.get_top_paths()
    
    if paths:
        data = []
        for path in paths:
            data.append({
                'path': path.path,
                'title': path.title,
                'count': path.count,
                'uniques': path.uniques,
                'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
            })
        
        df = pd.DataFrame(data)
        file_path = ANALYTICS_DIR / 'content' / f'popular_{datetime.now(timezone.utc).strftime("%Y%m")}.csv'
        
        # Append to monthly file
        if file_path.exists():
            existing_df = pd.read_csv(file_path)
            df = pd.concat([existing_df, df])
        
        df.to_csv(file_path, index=False)
        print(f"✓ Saved {len(data)} popular content records")
        return data
    return []

def collect_referrers(repo):
    """Collect referring sites."""
    print("Collecting referrers...")
    referrers = repo.get_top_referrers()
    
    if referrers:
        data = []
        for referrer in referrers:
            data.append({
                'referrer': referrer.referrer,
                'count': referrer.count,
                'uniques': referrer.uniques,
                'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
            })
        
        df = pd.DataFrame(data)
        file_path = ANALYTICS_DIR / 'referrers' / f'referrers_{datetime.now(timezone.utc).strftime("%Y%m")}.csv'
        
        # Append to monthly file
        if file_path.exists():
            existing_df = pd.read_csv(file_path)
            df = pd.concat([existing_df, df])
        
        df.to_csv(file_path, index=False)
        print(f"✓ Saved {len(data)} referrer records")
        return data
    return []

def generate_summary_report(traffic_data, clones_data, popular_data, referrers_data):
    """Generate a summary report."""
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'summary': {
            'total_views': sum(d['count'] for d in traffic_data) if traffic_data else 0,
            'unique_visitors': sum(d['uniques'] for d in traffic_data) if traffic_data else 0,
            'total_clones': sum(d['count'] for d in clones_data) if clones_data else 0,
            'unique_cloners': sum(d['uniques'] for d in clones_data) if clones_data else 0,
            'popular_paths_count': len(popular_data),
            'referrers_count': len(referrers_data)
        },
        'top_content': popular_data[:10] if popular_data else [],
        'top_referrers': referrers_data[:10] if referrers_data else []
    }
    
    # Save JSON report
    report_path = ANALYTICS_DIR / 'latest_summary.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*60}")
    print("📊 ANALYTICS SUMMARY")
    print(f"{'='*60}")
    print(f"Total Views: {report['summary']['total_views']}")
    print(f"Unique Visitors: {report['summary']['unique_visitors']}")
    print(f"Total Clones: {report['summary']['total_clones']}")
    print(f"Unique Cloners: {report['summary']['unique_cloners']}")
    print(f"{'='*60}\n")
    
    return report

def main():
    """Main execution function."""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    if not REPO_OWNER or not REPO_NAME:
        raise ValueError("REPO_OWNER and REPO_NAME environment variables are required")
    
    print(f"Collecting analytics for {REPO_OWNER}/{REPO_NAME}...")
    
    # Setup
    setup_analytics_directory()
    
    # Connect to GitHub using Auth.Token
    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    
    try:
        repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
    except Exception as e:
        print(f"❌ Error accessing repository: {e}")
        raise
    
    # Collect all data
    traffic_data = collect_traffic_data(repo)
    clones_data = collect_clones_data(repo)
    popular_data = collect_popular_content(repo)
    referrers_data = collect_referrers(repo)
    
    # Generate summary
    generate_summary_report(traffic_data, clones_data, popular_data, referrers_data)
    
    print("\n✅ Analytics collection complete!")

if __name__ == '__main__':
    main()
