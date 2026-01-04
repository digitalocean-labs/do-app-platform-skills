# Initial Environment Setup

Complete guide for setting up DigitalOcean projects, GitHub environments, secrets, and app specs.

---

## Environment Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENVIRONMENT ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. GITHUB REPOSITORY                                                    │
│     ├── Code (.do/app.yaml, application code)                           │
│     ├── Environments (staging, production)                               │
│     │   ├── Secrets (DATABASE_URL, API_KEYS)                            │
│     │   └── Variables (API_URL, LOG_LEVEL)                              │
│     └── Workflows (.github/workflows/deploy.yml)                        │
│                                                                          │
│  2. DIGITALOCEAN PROJECTS (Environment Containers)                       │
│     ├── project: myapp-staging    [Environment: Staging]                │
│     │   └── App: myapp-staging                                          │
│     └── project: myapp-production [Environment: Production]             │
│         └── App: myapp-production                                       │
│                                                                          │
│  3. WORKFLOW FLOW                                                        │
│     push to main → GitHub Action → reads GitHub Environment secrets     │
│                  → app_action deploy → creates/updates App in Project   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

**No secret sprawl**: Instead of `DATABASE_URL_DEV`, `DATABASE_URL_STAGING`, `DATABASE_URL_PROD`, you have ONE `DATABASE_URL` per GitHub environment. The workflow selects which environment to use.

**AI assistant never sees secrets**: Secrets flow directly from generation → GitHub Secrets → App Platform. The assistant generates commands but never handles credential values.

**Environment isolation**: Each DO Project has an explicit environment tag (Development, Staging, Production), making it easy to filter and manage apps.

---

## Prerequisites

### Required Tools

```bash
# Verify doctl is authenticated
doctl account get

# Verify gh CLI is authenticated with repo access
gh auth status
gh secret list --repo owner/repo  # Test access

# Verify git is available
git --version
```

### Python/Node Setup (for scripts)

```bash
# Python with uv (preferred)
uv --version

# Node with nvm
nvm --version
```

---

## Step 1: Create DigitalOcean Projects with Environments

```bash
# Create staging project
doctl projects create --name "myapp-staging" \
  --purpose "Staging environment for myapp" \
  --environment "Staging"

# Create production project
doctl projects create --name "myapp-production" \
  --purpose "Production environment for myapp" \
  --environment "Production"

# Note the project IDs
doctl projects list --format ID,Name,Environment
```

---

## Step 2: Create GitHub Environments

```bash
# Create staging environment
gh api \
  --method PUT \
  repos/:owner/:repo/environments/staging

# Create production environment with protection rules
gh api \
  --method PUT \
  repos/:owner/:repo/environments/production \
  -F prevent_self_review=true \
  -F reviewers[0][type]=User \
  -F reviewers[0][id]=$(gh api user --jq '.id')

# List environments to verify
gh api repos/:owner/:repo/environments --jq '.environments[].name'
```

---

## Step 3: Set Secrets and Variables per Environment

**CRITICAL**: This pattern keeps the AI assistant from ever seeing secret values.

```bash
# === STAGING ENVIRONMENT ===

# Set DigitalOcean token (user provides value)
gh secret set DIGITALOCEAN_ACCESS_TOKEN --env staging --body "YOUR_DO_TOKEN"

# Set project ID (from Step 1)
gh variable set DO_PROJECT_ID --env staging --body "PROJECT_ID_FROM_STEP_1"

# Set app name
gh variable set APP_NAME --env staging --body "myapp-staging"

# If using databases (postgres skill handles these):
gh secret set DATABASE_URL --env staging --body "postgresql://..."

# === PRODUCTION ENVIRONMENT ===

gh secret set DIGITALOCEAN_ACCESS_TOKEN --env production --body "YOUR_DO_TOKEN"
gh variable set DO_PROJECT_ID --env production --body "PROJECT_ID_FROM_STEP_1"
gh variable set APP_NAME --env production --body "myapp-production"
gh secret set DATABASE_URL --env production --body "postgresql://..."
```

**AI Assistant Pattern** (never sees the actual values):

```bash
# Generate the commands, let user fill in values
echo "Run these commands to set up staging secrets:"
echo ""
echo "gh secret set DIGITALOCEAN_ACCESS_TOKEN --env staging"
echo "# (You'll be prompted to enter the value securely)"
echo ""
echo "gh secret set DATABASE_URL --env staging"
```

---

## Step 4: Create App Spec

Ensure `.do/app.yaml` exists in the repo. Use **designer skill** or **migration skill** to create it.

```yaml
# .do/app.yaml
name: myapp  # Will be overridden by workflow variable
region: nyc

services:
  - name: web
    github:
      repo: owner/myapp
      branch: main
      deploy_on_push: false  # IMPORTANT: Let GitHub Actions control deploys
    run_command: npm start
    http_port: 8080
    instance_size_slug: apps-s-1vcpu-0.5gb
    instance_count: 1
    envs:
      - key: NODE_ENV
        scope: RUN_TIME
        value: ${NODE_ENV}
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${DATABASE_URL}
```

---

## Step 5: Generate Deployment Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to App Platform

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'staging' }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Deploy to App Platform
        uses: digitalocean/app_action/deploy@v2
        env:
          # Environment variables for app spec substitution
          NODE_ENV: ${{ github.event.inputs.environment || 'staging' }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
          project_id: ${{ vars.DO_PROJECT_ID }}
          # app_name override if you want environment-specific names
          # app_name: ${{ vars.APP_NAME }}
```

---

## Production Setup Checklist

- [ ] Create DO Projects with environment tags
- [ ] Create GitHub environments (staging, production)
- [ ] Set `DIGITALOCEAN_ACCESS_TOKEN` secret per environment
- [ ] Set `DO_PROJECT_ID` variable per environment
- [ ] Set application secrets (DATABASE_URL, etc.) per environment
- [ ] Create `.do/app.yaml` with `deploy_on_push: false`
- [ ] Create `.github/workflows/deploy.yml`
- [ ] Add environment protection rules for production
- [ ] Test staging deployment
- [ ] Test production deployment with approval

---

## Environment Protection Rules

### Add Required Reviewers to Production

```bash
# Add required reviewers to production environment
gh api \
  --method PUT \
  repos/:owner/:repo/environments/production \
  -F prevent_self_review=true \
  -F reviewers[0][type]=User \
  -F reviewers[0][id]=$(gh api user --jq '.id')
```

---

## Troubleshooting Setup

| Issue | Symptom | Fix |
|-------|---------|-----|
| App spec not found | `Error: spec file not found` | Ensure `.do/app.yaml` exists |
| Invalid token | `401 Unauthorized` | Check `DIGITALOCEAN_ACCESS_TOKEN` secret |
| Project not found | `project_id is invalid` | Verify `DO_PROJECT_ID` variable |
| Env vars not set | Values show `${...}` literally | Check bindable variable names match |

### Debug Steps

```bash
# 1. Validate spec locally
doctl apps spec validate .do/app.yaml

# 2. Check GitHub secrets are set
gh secret list --env staging

# 3. Check GitHub variables
gh variable list --env staging

# 4. Test deployment manually
doctl apps create --spec .do/app.yaml --project-id $PROJECT_ID

# 5. Check logs
doctl apps logs $APP_ID --type build
doctl apps logs $APP_ID --type deploy
doctl apps logs $APP_ID --type run
```
