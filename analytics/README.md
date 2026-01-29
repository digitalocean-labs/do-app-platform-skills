# GitHub Analytics

This directory contains historical GitHub traffic and usage data for the do-app-platform-skills repository.

## Data Collection

Analytics data is automatically collected daily via the `.github/workflows/collect-analytics.yml` GitHub Action.

### What's Collected

- **Traffic** (`traffic/views.csv`) - Daily page views and unique visitors
- **Clones** (`clones/clones.csv`) - Daily repository clones and unique cloners  
- **Popular Content** (`content/popular_YYYYMM.csv`) - Most viewed files and paths
- **Referrers** (`referrers/referrers_YYYYMM.csv`) - Top referring sites

### Data Retention

- GitHub API only provides 14 days of historical data
- This automation captures and stores data daily to build long-term history
- Data is stored indefinitely unless manually cleaned up

## Viewing Analytics

### Quick Summary

View the latest summary:
```bash
cat analytics/latest_summary.json | jq
```

### Detailed Report

Generate a comprehensive report:
```bash
python scripts/view_analytics.py --period 30
```

Options:
- `--period N` - Report on last N days (default: 30)
- `--output file.html` - Save as HTML report (coming soon)

### Skills Usage

See which skills are most viewed:
```bash
python scripts/view_analytics.py --period 90
```

The report includes a "Usage by Skill" section showing traffic breakdown.

## Manual Collection

To manually trigger analytics collection:

1. Go to Actions tab in GitHub
2. Select "Collect GitHub Analytics" workflow
3. Click "Run workflow"

Or via GitHub CLI:
```bash
gh workflow run collect-analytics.yml
```

## Data Structure

### Traffic Data (`traffic/views.csv`)
```csv
date,count,uniques,collected_at
2026-01-29,245,89,2026-01-30T00:00:00Z
```

### Clones Data (`clones/clones.csv`)
```csv
date,count,uniques,collected_at
2026-01-29,42,23,2026-01-30T00:00:00Z
```

### Popular Content (`content/popular_202601.csv`)
```csv
path,title,count,uniques,date
skills/postgres/SKILL.md,PostgreSQL Skill,156,45,2026-01-29
```

### Referrers (`referrers/referrers_202601.csv`)
```csv
referrer,count,uniques,date
github.com,234,89,2026-01-29
google.com,87,34,2026-01-29
```

## Privacy & Security

- All data is aggregated and anonymized by GitHub
- No personally identifiable information is collected
- Data is stored in the public repository (if repo is public)
- For private repos, analytics data remains private

## Troubleshooting

### No data being collected

Check the GitHub Action logs:
```bash
gh run list --workflow=collect-analytics.yml
gh run view <run-id> --log
```

### Missing dependencies

Install required packages:
```bash
pip install PyGithub pandas
```

### Permission errors

Ensure the GitHub Action has `contents: write` permission in the workflow file.

## Future Enhancements

- [ ] HTML dashboard with charts
- [ ] Integration with external analytics platforms
- [ ] Alerts for traffic spikes/drops
- [ ] Skill comparison charts
- [ ] Download reports as PDF
