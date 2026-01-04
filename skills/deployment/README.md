# Deployment Skill

Ship applications to DigitalOcean App Platform via GitHub Actions with proper environment management, secrets handling, and the `app_action` v2 workflow.

## Quick Start

```bash
# 1. Create DO Project with environment
doctl projects create --name "myapp-staging" --environment "Staging"

# 2. Create GitHub environment
gh api --method PUT repos/:owner/:repo/environments/staging

# 3. Set secrets (you'll be prompted for values)
gh secret set DIGITALOCEAN_ACCESS_TOKEN --env staging
gh secret set DATABASE_URL --env staging

# 4. Set variables
gh variable set DO_PROJECT_ID --env staging --body "your-project-id"

# 5. Create workflow (.github/workflows/deploy.yml) - see SKILL.md

# 6. Push to main → Auto-deploys to staging!
```

## Key Concepts

### Push Mode (This Skill)

AI assistant drives deployment via CLI commands and GitHub Actions:
- App spec lives in repo (`.do/app.yaml`)
- GitHub Actions + `app_action` handle deployment
- Secrets flow: User → GitHub Secrets → App Platform (AI never sees values)

### Environment Architecture

```
GitHub Repository
├── Environments (staging, production)
│   ├── Secrets (DATABASE_URL)
│   └── Variables (DO_PROJECT_ID)
└── Workflows (deploy.yml)
       ↓
DigitalOcean Projects
├── myapp-staging [Environment: Staging]
└── myapp-production [Environment: Production]
```

### Primary Action: `digitalocean/app_action/deploy@v2`

Handles everything in one step:
- Creates app if doesn't exist
- Updates spec if changed
- Triggers deployment
- Supports PR previews

```yaml
- uses: digitalocean/app_action/deploy@v2
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  with:
    token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
    project_id: ${{ vars.DO_PROJECT_ID }}
```

## Workflows

| Workflow | Use Case | Key Feature |
|----------|----------|-------------|
| Basic Deploy | Push to main | Auto-deploy to staging |
| Multi-Environment | staging + production | Environment selection |
| PR Preview | Pull requests | Temporary preview apps |
| Production Approval | Protected deploys | Required reviewers |
| Rollback | Revert bad deploy | Deploy specific commit |

## Debug Component Pattern

For complex apps with multiple integrations, deploy a debug Alpine container first to verify infrastructure (~45 seconds vs 5-7 minutes).

See SKILL.md for full details.

## Dependencies

- **Required**: doctl, gh CLI, git
- **Skills**: designer, migration (produce app spec), postgres (database setup), troubleshooting (when things fail)

## Files Produced

- `.github/workflows/deploy.yml` - Main deployment workflow
- `.github/workflows/preview.yml` - PR preview workflow (optional)

## Documentation

- [SKILL.md](./SKILL.md) - Full skill documentation
- [app_action repo](https://github.com/digitalocean/app_action)
- [App Platform docs](https://docs.digitalocean.com/products/app-platform/)
