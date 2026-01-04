#!/usr/bin/env python3
"""
Migration Checklist Generator

Generates a comprehensive migration checklist (MIGRATION.md) based on
repository analysis and migration mapping.

Usage:
    python generate_checklist.py /path/to/repo --name myapp
    python generate_checklist.py /path/to/repo --name myapp --output MIGRATION.md
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from analyze_architecture import ArchitectureAnalyzer
from detect_platform import PlatformDetector
from generate_app_spec import AppSpecGenerator


def generate_checklist(repo_path: str, app_name: str, 
                       repo_url: Optional[str] = None,
                       test_branch: str = 'migrate/test',
                       prod_branch: str = 'migrate/prod') -> str:
    """Generate comprehensive migration checklist."""
    
    # Run analysis
    platform_detector = PlatformDetector(repo_path)
    platform_info = platform_detector.detect()
    
    analyzer = ArchitectureAnalyzer(repo_path)
    architecture = analyzer.analyze()
    
    # Generate specs for both environments
    test_generator = AppSpecGenerator(repo_path, app_name, 'test')
    prod_generator = AppSpecGenerator(repo_path, app_name, 'production')
    
    test_report = test_generator.get_migration_report()
    prod_report = prod_generator.get_migration_report()
    
    # Build checklist
    checklist = []
    checklist.append(f"# Migration Report: {app_name}")
    checklist.append(f"\n**Source Platform:** {platform_info['primary_description']}")
    checklist.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    checklist.append(f"**Repository:** {repo_url or 'Local'}")
    
    # Summary section
    checklist.append("\n## Summary\n")
    checklist.append("| Metric | Value |")
    checklist.append("|--------|-------|")
    checklist.append(f"| Source Platform | {platform_info['primary_description']} |")
    checklist.append(f"| Config Files | {', '.join(platform_info['config_files']) or 'None detected'} |")
    checklist.append(f"| Architecture Type | {architecture['architecture_type']} |")
    checklist.append(f"| Runtime | {architecture['runtime']} |")
    checklist.append(f"| Components Detected | {len(architecture['components'])} |")
    checklist.append(f"| Successfully Mapped | {len(architecture['components']) - len(test_generator.unmapped_items)} |")
    checklist.append(f"| Requires Decision | {len(test_generator.unmapped_items)} |")
    checklist.append(f"| Test Branch | `{test_branch}` |")
    checklist.append(f"| Production Branch | `{prod_branch}` |")
    
    # Component mapping section
    checklist.append("\n## Component Mapping\n")
    checklist.append("### ✅ Successfully Mapped\n")
    checklist.append("| Source | Target | Type | Notes |")
    checklist.append("|--------|--------|------|-------|")
    
    for comp in architecture['components']:
        source = f"{comp['name']}"
        if comp.get('command'):
            source += f" (`{comp['command'][:30]}...`)" if len(comp.get('command', '')) > 30 else f" (`{comp['command']}`)"
        
        target_type = {
            'service': 'services',
            'worker': 'workers',
            'job': 'jobs',
            'static_site': 'static_sites'
        }.get(comp['type'], comp['type'])
        
        notes = []
        if comp.get('port'):
            notes.append(f"port {comp['port']}")
        if comp.get('source_dir') and comp['source_dir'] != '/':
            notes.append(f"dir: {comp['source_dir']}")
        
        checklist.append(f"| {source} | {target_type}.{comp['name']} | {comp['type']} | {', '.join(notes) or '-'} |")
    
    # Dependencies mapping
    deps = architecture['dependencies']
    if deps['databases'] or deps['caches']:
        checklist.append("\n### Database & Cache Mapping\n")
        checklist.append("| Source | Target | Notes |")
        checklist.append("|--------|--------|-------|")
        
        for db in deps['databases']:
            target = 'databases.db' if db['type'] == 'postgres' else f"databases.{db['type']}"
            engine = {'postgres': 'PG', 'mysql': 'MYSQL', 'mongodb': 'MONGODB'}.get(db['type'], db['type'].upper())
            checklist.append(f"| {db['source']} | {target} ({engine}) | {db.get('note', '-')} |")
        
        for cache in deps['caches']:
            note = cache.get('note', 'Redis EOL → using Valkey')
            checklist.append(f"| {cache['source']} | databases.cache (VALKEY) | {note} |")
    
    # Unmapped items section
    if test_generator.unmapped_items:
        checklist.append("\n### ⚠️ Requires Your Decision\n")
        
        for item in test_generator.unmapped_items:
            checklist.append(f"\n**{item['name']}**")
            checklist.append(f"- Source: {item['source']}")
            checklist.append(f"- Issue: {item['reason']}")
            checklist.append("- Options:")
            for opt in item.get('options', []):
                checklist.append(f"  - [ ] {opt}")
    
    # Environment variables section
    checklist.append("\n## Environment Variables\n")
    checklist.append("| Variable | Source | Action |")
    checklist.append("|----------|--------|--------|")
    
    # Standard bindings
    if deps['databases']:
        for db in deps['databases']:
            if db['type'] == 'postgres':
                checklist.append("| `DATABASE_URL` | database binding | Auto-bound: `${db.DATABASE_URL}` |")
            elif db['type'] == 'mysql':
                checklist.append("| `MYSQL_URL` | database binding | Auto-bound: `${mysqldb.DATABASE_URL}` |")
    
    if deps['caches']:
        checklist.append("| `VALKEY_URL` | cache binding | Auto-bound: `${cache.DATABASE_URL}` |")
        checklist.append("| `REDIS_URL` | cache binding | Alias for Valkey compatibility |")
    
    # Secrets
    checklist.append("| `SECRET_KEY` | application secret | Set in GitHub Secrets |")
    checklist.append("| `PORT` | app port | Auto-set by App Platform |")
    
    # Code changes section
    checklist.append("\n## Code Changes Required\n")
    
    code_changes = []
    
    # Platform-specific changes
    if platform_info['primary_platform'] == 'heroku':
        code_changes.append("- [ ] Remove Heroku-specific `DATABASE_URL` postgres:// → postgresql:// fix (if present)")
        code_changes.append("- [ ] Update any `REDIS_URL` references to `VALKEY_URL`")
    
    if any(c['type'] == 'redis' for c in deps.get('caches', [])):
        code_changes.append("- [ ] Update Redis client configuration for Valkey compatibility")
    
    if deps.get('storage'):
        code_changes.append("- [ ] Update S3/storage configuration for Spaces compatibility")
        code_changes.append("  - Endpoint: `https://<region>.digitaloceanspaces.com`")
        code_changes.append("  - Use `SPACES_KEY`, `SPACES_SECRET`, `SPACES_BUCKET` env vars")
    
    if not code_changes:
        code_changes.append("- [ ] No platform-specific code changes detected")
    
    for change in code_changes:
        checklist.append(change)
    
    # Files created section
    checklist.append("\n## Files Created\n")
    checklist.append("```")
    checklist.append(".do/")
    checklist.append("├── app.yaml              # App Platform spec")
    checklist.append("├── deploy.template.yaml  # Deploy-to-DO button")
    checklist.append("├── test.app.yaml         # Testing environment spec")
    checklist.append("└── prod.app.yaml         # Production environment spec")
    checklist.append("MIGRATION.md              # This file")
    checklist.append(".env.example              # Environment variable template")
    checklist.append("```")
    
    # Pre-migration checklist
    checklist.append("\n## Pre-Migration Checklist\n")
    checklist.append("### Before You Begin\n")
    checklist.append("- [ ] Review all component mappings above")
    checklist.append("- [ ] Decide on unmapped items (if any)")
    checklist.append("- [ ] Ensure `doctl` is authenticated: `doctl account get`")
    checklist.append("- [ ] Ensure `gh` is authenticated: `gh auth status`")
    checklist.append("- [ ] Note current environment variable values from source platform")
    
    # Setup checklist
    checklist.append("\n### App Platform Setup\n")
    
    # Production database creation
    if any(db.get('type') == 'postgres' for db in deps.get('databases', [])):
        checklist.append("#### Database Setup (Production)\n")
        checklist.append("```bash")
        checklist.append(f"# Create managed PostgreSQL cluster")
        checklist.append(f"doctl databases create {app_name}-db \\")
        checklist.append("  --engine pg \\")
        checklist.append("  --region nyc \\")
        checklist.append("  --size db-s-1vcpu-1gb \\")
        checklist.append("  --num-nodes 1")
        checklist.append("")
        checklist.append("# Get connection string")
        checklist.append(f"doctl databases connection {app_name}-db --format URI")
        checklist.append("```")
    
    if any(c.get('type') in ['redis', 'valkey'] for c in deps.get('caches', [])):
        checklist.append("\n#### Cache Setup (Production)\n")
        checklist.append("```bash")
        checklist.append(f"# Create Valkey cluster")
        checklist.append(f"doctl databases create {app_name}-cache \\")
        checklist.append("  --engine valkey \\")
        checklist.append("  --region nyc \\")
        checklist.append("  --size db-s-1vcpu-1gb")
        checklist.append("```")
    
    # GitHub setup
    checklist.append("\n#### GitHub Environment Setup\n")
    checklist.append("```bash")
    checklist.append("# Create staging environment")
    checklist.append("gh api --method PUT repos/:owner/:repo/environments/staging")
    checklist.append("")
    checklist.append("# Create production environment with protection")
    checklist.append("gh api --method PUT repos/:owner/:repo/environments/production \\")
    checklist.append("  -F prevent_self_review=true")
    checklist.append("")
    checklist.append("# Set secrets (you'll be prompted for values)")
    checklist.append("gh secret set DIGITALOCEAN_ACCESS_TOKEN --env staging")
    checklist.append("gh secret set SECRET_KEY --env staging")
    checklist.append("")
    checklist.append("# Repeat for production")
    checklist.append("gh secret set DIGITALOCEAN_ACCESS_TOKEN --env production")
    checklist.append("gh secret set SECRET_KEY --env production")
    checklist.append("```")
    
    # Deployment checklist
    checklist.append("\n### Deployment\n")
    checklist.append("```bash")
    checklist.append("# Validate app spec")
    checklist.append("doctl apps spec validate .do/app.yaml")
    checklist.append("")
    checklist.append("# Deploy testing environment")
    checklist.append(f"git checkout {test_branch}")
    checklist.append("doctl apps create --spec .do/app.yaml")
    checklist.append("")
    checklist.append("# After testing, deploy production")
    checklist.append(f"git checkout {prod_branch}")
    checklist.append("doctl apps create --spec .do/app.yaml")
    checklist.append("```")
    
    # Data migration section
    if deps.get('databases'):
        checklist.append("\n## Data Migration\n")
        
        if any(db['type'] == 'postgres' for db in deps['databases']):
            checklist.append("### PostgreSQL\n")
            
            if platform_info['primary_platform'] == 'heroku':
                checklist.append("```bash")
                checklist.append("# 1. Create backup from Heroku")
                checklist.append("heroku pg:backups:capture --app <heroku-app-name>")
                checklist.append("heroku pg:backups:download --app <heroku-app-name>")
                checklist.append("")
                checklist.append("# 2. Restore to DigitalOcean")
                checklist.append("pg_restore -d \"<DO_DATABASE_URL>\" latest.dump")
                checklist.append("```")
            else:
                checklist.append("```bash")
                checklist.append("# 1. Export from source database")
                checklist.append("pg_dump \"<SOURCE_DATABASE_URL>\" > backup.sql")
                checklist.append("")
                checklist.append("# 2. Import to DigitalOcean")
                checklist.append("psql \"<DO_DATABASE_URL>\" < backup.sql")
                checklist.append("```")
    
    # DNS cutover section
    checklist.append("\n## DNS Cutover\n")
    checklist.append("```bash")
    checklist.append("# 1. Lower TTL 24-48 hours before migration")
    checklist.append("# Set TTL to 300 (5 minutes) in your DNS provider")
    checklist.append("")
    checklist.append("# 2. Get App Platform URL")
    checklist.append("doctl apps list --format ID,DefaultIngress")
    checklist.append("")
    checklist.append("# 3. Update DNS records to point to App Platform")
    checklist.append("# CNAME: your-domain.com → <app-name>.ondigitalocean.app")
    checklist.append("")
    checklist.append("# 4. (Optional) Add custom domain in App Platform")
    checklist.append("doctl apps update <app-id> --spec .do/app.yaml")
    checklist.append("# (after adding domain to spec)")
    checklist.append("")
    checklist.append("# 5. After cutover, increase TTL back to normal (3600+)")
    checklist.append("```")
    
    # Post-migration checklist
    checklist.append("\n## Post-Migration Checklist\n")
    checklist.append("- [ ] Verify all components are running: `doctl apps list-deployments <app-id>`")
    checklist.append("- [ ] Check application logs: `doctl apps logs <app-id> --type run`")
    checklist.append("- [ ] Test critical user journeys")
    checklist.append("- [ ] Verify background jobs/workers are processing")
    checklist.append("- [ ] Monitor error rates in App Platform Insights")
    checklist.append("- [ ] Update documentation with new deployment process")
    checklist.append("- [ ] Decommission old infrastructure after verification period")
    
    # Rollback section
    checklist.append("\n## Rollback Plan\n")
    checklist.append("If issues occur after cutover:\n")
    checklist.append("1. Point DNS back to original platform")
    checklist.append("2. Original infrastructure should remain running during verification period")
    checklist.append("3. Debug issues using `doctl apps logs` and App Platform console")
    checklist.append("4. Fix and re-attempt migration")
    
    # Warnings section
    if test_generator.warnings or prod_generator.warnings:
        checklist.append("\n## ⚠️ Warnings\n")
        all_warnings = list(set(test_generator.warnings + prod_generator.warnings))
        for warning in all_warnings:
            checklist.append(f"- {warning}")
    
    # Next steps section
    checklist.append("\n## Next Steps\n")
    checklist.append("After reviewing this migration report:\n")
    checklist.append(f"1. **Review branches**: `git diff main..{test_branch}`")
    checklist.append("2. **Use deployment skill**: Set up GitHub Actions CI/CD")
    checklist.append("3. **Use devcontainers skill**: Set up local development environment")
    checklist.append("4. **Use troubleshooting skill**: If deployment issues occur")
    
    return '\n'.join(checklist)


def main():
    parser = argparse.ArgumentParser(
        description='Generate migration checklist for App Platform'
    )
    parser.add_argument('repo_path', help='Path to the repository')
    parser.add_argument('--name', required=True, help='Application name')
    parser.add_argument('--repo-url', help='Git repository URL')
    parser.add_argument('--test-branch', default='migrate/test', help='Test branch name')
    parser.add_argument('--prod-branch', default='migrate/prod', help='Production branch name')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    try:
        checklist = generate_checklist(
            args.repo_path,
            args.name,
            repo_url=args.repo_url,
            test_branch=args.test_branch,
            prod_branch=args.prod_branch
        )
        
        if args.output:
            Path(args.output).write_text(checklist)
            print(f"Written to: {args.output}")
        else:
            print(checklist)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
