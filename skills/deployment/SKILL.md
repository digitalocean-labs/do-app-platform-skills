---
name: app-platform-deployment
description: Ship applications to DigitalOcean App Platform via GitHub Actions with proper environment management, secrets handling, and the app_action v2 workflow
version: 1.0.0
author: Bikram Gupta
triggers:
  - "deploy"
  - "ship"
  - "release"
  - "GitHub Actions"
  - "CI/CD"
  - "push to production"
  - "deploy to app platform"
  - "set up deployment"
  - "environments"
  - "staging"
  - "production"
dependencies:
  required:
    - doctl (authenticated)
    - gh (GitHub CLI, authenticated)
    - git
  optional:
    - python 3.10+ (for scripts)
  skills:
    - designer (produces app spec)
    - migration (produces app spec)
    - postgres (database configuration)
    - troubleshooting (when deployments fail)
    # Future data service skills:
    # - mysql
    # - mongodb
    # - spaces
    # - opensearch
    # - kafka
    # - valkey
    # - gradient-ai
artifacts:
  produced:
    - .github/workflows/deploy.yml
    - .github/workflows/preview.yml (optional)
    - .do/app.yaml
  consumed:
    - .do/app.yaml (from designer or migration skill)
---

# App Platform Deployment Skill

## Philosophy

**This skill focuses on PUSH mode deployment** — where the AI assistant drives deployment via CLI commands and GitHub Actions. This is distinct from PULL mode (using the DigitalOcean console UI to create apps from GitHub repos).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT MODES                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PULL MODE (Console-driven) — NOT covered by this skill                 │
│  ─────────────────────────────────────────────────────────────────────  │
│  • Go to DigitalOcean Console                                           │
│  • Click "Create App" → Point to GitHub repo                            │
│  • App Platform generates app spec for you                              │
│  • Good for: Quick starts, manual deployments                           │
│                                                                          │
│  PUSH MODE (CLI/Actions-driven) — THIS SKILL                            │
│  ─────────────────────────────────────────────────────────────────────  │
│  • Define app spec in your repo (.do/app.yaml)                          │
│  • Use GitHub Actions + app_action to deploy                            │
│  • AI assistant orchestrates the entire workflow                        │
│  • Good for: CI/CD, automation, GitOps, multi-environment               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The Bigger Picture

Successful deployment to App Platform requires understanding how environments flow from GitHub to DigitalOcean:

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

## Core Concept: Command Types

While not the primary focus, understanding when to use which command is important:

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `doctl apps create --spec` | Create new app | First deployment only |
| `doctl apps update --spec` | Update app spec | Config changes (env vars, resources, routes) |
| `doctl apps create-deployment` | Trigger rebuild | Code changes without spec changes |
| **app_action v2** | **Both spec + rebuild** | **Recommended: Handles everything** |

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT DECISION                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Using GitHub Actions? (RECOMMENDED)                                     │
│      │                                                                   │
│      └── YES → Use digitalocean/app_action/deploy@v2                    │
│                • Handles both spec updates AND code deployments         │
│                • Manages app creation if doesn't exist                  │
│                • Supports PR previews                                   │
│                                                                          │
│  Using doctl directly? (Manual/Scripting)                               │
│      │                                                                   │
│      ├── Spec changed? → doctl apps update --spec                       │
│      │                                                                   │
│      └── Code only? → doctl apps create-deployment                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Workflow 1: Initial Environment Setup

**User says**: "Help me set up deployment for my app" / "I want to deploy to staging and production"

This is the foundational workflow. Get this right, and everything else follows.

### Step 1: Create DigitalOcean Projects with Environments

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

### Step 2: Create GitHub Environments

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

### Step 3: Set Secrets and Variables per Environment

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

### Step 4: Create App Spec

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

### Step 5: Generate Deployment Workflow

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

## Workflow 2: Production Deployment with Approval

**User says**: "Production deployments should require approval"

### Enhanced Workflow with Manual Approval

```yaml
name: Deploy to Production

on:
  workflow_dispatch:
    inputs:
      confirm_production:
        description: 'Type "production" to confirm deployment'
        required: true
        type: string

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Validate confirmation
        if: ${{ github.event.inputs.confirm_production != 'production' }}
        run: |
          echo "::error::You must type 'production' to confirm deployment"
          exit 1

  deploy:
    needs: validate
    runs-on: ubuntu-latest
    environment: production  # This triggers GitHub's environment protection rules
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Deploy to App Platform
        uses: digitalocean/app_action/deploy@v2
        env:
          NODE_ENV: production
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
          project_id: ${{ vars.DO_PROJECT_ID }}
```

### Set Up Environment Protection Rules

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

## Workflow 3: PR Preview Environments

**User says**: "I want preview environments for pull requests"

### Preview Deployment Workflow

```yaml
name: PR Preview

on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Deploy Preview
        id: deploy
        uses: digitalocean/app_action/deploy@v2
        env:
          NODE_ENV: preview
          DATABASE_URL: ${{ secrets.PREVIEW_DATABASE_URL }}
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
          deploy_pr_preview: "true"  # Creates unique app per PR
      
      - name: Comment with preview URL
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `🚀 Preview deployed at: ${{ fromJson(steps.deploy.outputs.app).live_url }}`
            })
      
      - name: Comment on failure
        if: failure()
        uses: actions/github-script@v7
        env:
          BUILD_LOGS: ${{ steps.deploy.outputs.build_logs }}
          DEPLOY_LOGS: ${{ steps.deploy.outputs.deploy_logs }}
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `❌ Preview deployment failed. [View logs](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})`
            })
```

### Preview Cleanup Workflow

```yaml
name: Cleanup PR Preview

on:
  pull_request:
    types: [closed]

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - name: Delete preview app
        uses: digitalocean/app_action/delete@v2
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
          from_pr_preview: "true"
          ignore_not_found: "true"
```

---

## Workflow 4: Multi-Environment with Single Workflow

**User says**: "I want one workflow that can deploy to any environment"

### Unified Deployment Workflow

```yaml
name: Deploy

on:
  push:
    branches:
      - main      # Auto-deploy to staging
      - release/* # Auto-deploy to production
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - development
          - staging
          - production

permissions:
  contents: read

jobs:
  determine-environment:
    runs-on: ubuntu-latest
    outputs:
      environment: ${{ steps.set-env.outputs.environment }}
    steps:
      - name: Determine environment
        id: set-env
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            echo "environment=${{ github.event.inputs.environment }}" >> $GITHUB_OUTPUT
          elif [[ "${{ github.ref }}" == refs/heads/release/* ]]; then
            echo "environment=production" >> $GITHUB_OUTPUT
          else
            echo "environment=staging" >> $GITHUB_OUTPUT
          fi

  deploy:
    needs: determine-environment
    runs-on: ubuntu-latest
    environment: ${{ needs.determine-environment.outputs.environment }}
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Deploy
        uses: digitalocean/app_action/deploy@v2
        env:
          NODE_ENV: ${{ needs.determine-environment.outputs.environment }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
          project_id: ${{ vars.DO_PROJECT_ID }}
```

---

## Workflow 5: Debug Component for Complex Deployments

**User says**: "My app has 10 integrations and keeps failing. Can we test infrastructure first?"

For complex applications with multiple database connections and third-party integrations, deploying a debug component first can save hours of iteration.

### The Problem

```
Traditional approach for complex apps:
Push code → Wait 5-7 min → Fails → Check logs → Guess → Repeat

With debug component:
Deploy debug worker (~45s) → Verify ALL connections → 
If works → Proceed with full app
If fails → Fix infrastructure, not code
```

### Debug Component Pattern

Add this worker to your app spec temporarily:

```yaml
# Add to .do/app.yaml temporarily
workers:
  - name: debug
    image:
      registry_type: DOCKER_HUB
      registry: library
      repository: alpine
      tag: latest
    run_command: sleep infinity
    instance_size_slug: apps-s-1vcpu-0.5gb
    envs:
      # Mirror ALL environment variables from your main service
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: REDIS_URL
        scope: RUN_TIME
        value: ${redis.REDIS_URL}
      - key: KAFKA_BROKERS
        scope: RUN_TIME
        value: ${kafka.KAFKA_BROKERS}
      # Add any other integrations...
```

### Pre-Built Debug Image (Recommended)

For frequent debugging, use a pre-built image with all client tools:

```dockerfile
# Dockerfile.debug - push to GHCR or DOCR
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    # Database clients
    postgresql-client \
    mysql-client \
    redis-tools \
    # Network tools
    curl \
    wget \
    netcat-openbsd \
    dnsutils \
    # Development
    python3 \
    python3-pip \
    # AWS CLI for Spaces
    awscli \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for testing
RUN pip3 install --break-system-packages \
    psycopg2-binary \
    pymysql \
    redis \
    kafka-python \
    opensearch-py \
    boto3

CMD ["sleep", "infinity"]
```

### Verification Checklist

After deploying debug component, connect and verify:

```bash
# Connect to debug container
doctl apps console $APP_ID debug

# Inside container:

# 1. Verify all environment variables populated
env | grep -E 'DATABASE|REDIS|KAFKA|URL' | sort

# 2. Test database connectivity
psql "$DATABASE_URL" -c "SELECT 1;"

# 3. Test Redis connectivity
redis-cli -u "$REDIS_URL" PING

# 4. Test network to third-party services
curl -I https://api.third-party.com/health

# 5. Test Spaces/S3 connectivity
aws s3 ls s3://$SPACES_BUCKET --endpoint=$SPACES_ENDPOINT
```

### Cleanup

**IMPORTANT**: Delete the debug component after verification.

```bash
# Remove debug worker from spec
# Or delete via: doctl apps update $APP_ID --spec (without debug worker)
```

### When to Use This Pattern

✅ **Use debug component when:**
- App has 3+ external integrations
- Deployment keeps failing with connection errors
- Setting up new managed databases for the first time
- Migrating from one database cluster to another

❌ **Skip this when:**
- Simple app with 1-2 services
- Issue is clearly application code (syntax errors, etc.)
- Already verified infrastructure works

---

## Workflow Optimization

### Disable Detailed Logging

For production workflows, disable extensive log capture to save resources:

```yaml
- name: Deploy to App Platform
  uses: digitalocean/app_action/deploy@v2
  with:
    token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
    # Disable detailed log capture
    print_build_logs: "false"
    print_deploy_logs: "false"
```

Users can view logs directly via `doctl apps logs` or the App Platform console.

### Caching doctl (Optional)

If installing doctl repeatedly is slow:

```yaml
- name: Setup doctl
  uses: digitalocean/action-doctl@v2
  with:
    token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
    # Version pinning for reproducibility
    version: 1.100.0
```

---

## Local Deployment (Fallback)

For quick local deployments without GitHub Actions:

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

# Load environment
source .env.local

# Validate spec
doctl apps spec validate .do/app.yaml

# Create or update app
if [ -z "$APP_ID" ]; then
    echo "Creating new app..."
    doctl apps create --spec .do/app.yaml --project-id $PROJECT_ID --wait
else
    echo "Updating existing app..."
    doctl apps update $APP_ID --spec .do/app.yaml --wait
fi

echo "Deployment complete!"
```

---

## Rollback

### Quick Rollback via Console/CLI

```bash
# List recent deployments
doctl apps list-deployments $APP_ID --format ID,Phase,CreatedAt

# App Platform doesn't have native rollback, but you can:
# 1. Revert code in git and push (triggers new deployment)
# 2. Restore previous app spec from git history
# 3. Use doctl apps update with previous spec

# Get current spec
doctl apps spec get $APP_ID > current-spec.yaml

# Restore from git and redeploy
git checkout HEAD~1 -- .do/app.yaml
doctl apps update $APP_ID --spec .do/app.yaml --wait
```

### Rollback Workflow

```yaml
name: Rollback

on:
  workflow_dispatch:
    inputs:
      commit_sha:
        description: 'Commit SHA to rollback to'
        required: true
        type: string

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Checkout specific commit
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.commit_sha }}
      
      - name: Deploy rollback
        uses: digitalocean/app_action/deploy@v2
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
          project_id: ${{ vars.DO_PROJECT_ID }}
```

---

## doctl Command Reference

### App Management

```bash
# Create app
doctl apps create --spec .do/app.yaml --project-id $PROJECT_ID --wait

# Update app spec
doctl apps update $APP_ID --spec .do/app.yaml --wait

# Trigger deployment (code only, no spec change)
doctl apps create-deployment $APP_ID --wait

# Force rebuild (ignores cache)
doctl apps create-deployment $APP_ID --force-rebuild --wait

# Get app info
doctl apps get $APP_ID
doctl apps get $APP_ID -o json | jq '.[]'

# Get app spec
doctl apps spec get $APP_ID > app-spec.yaml

# Validate spec locally
doctl apps spec validate .do/app.yaml

# Delete app
doctl apps delete $APP_ID --force
```

### Deployment History

```bash
# List deployments
doctl apps list-deployments $APP_ID

# Get deployment details
doctl apps get-deployment $APP_ID $DEPLOYMENT_ID

# Get logs
doctl apps logs $APP_ID --type run
doctl apps logs $APP_ID $COMPONENT --type build
doctl apps logs $APP_ID --type run --follow
```

### Project Management

```bash
# List projects
doctl projects list --format ID,Name,Environment

# Create project with environment
doctl projects create --name "myapp-staging" \
  --purpose "Staging" \
  --environment "Staging"

# Get project ID for an app
APP_ID="your-app-id"
doctl apps get "$APP_ID" -o json | jq -r '.[0].project_id'

# Get environment for an app's project
PROJECT_ID=$(doctl apps get "$APP_ID" -o json | jq -r '.[0].project_id')
doctl projects get "$PROJECT_ID" -o json | jq -r '.[0].environment'
```

---

## GitHub CLI Reference

### Environment Management

```bash
# Create environment
gh api --method PUT repos/:owner/:repo/environments/staging

# Create environment with protection
gh api --method PUT repos/:owner/:repo/environments/production \
  -F prevent_self_review=true \
  -F reviewers[0][type]=User \
  -F reviewers[0][id]=USER_ID

# List environments
gh api repos/:owner/:repo/environments --jq '.environments[].name'

# Delete environment
gh api --method DELETE repos/:owner/:repo/environments/staging
```

### Secrets and Variables

```bash
# Set secret for environment (prompted for value)
gh secret set SECRET_NAME --env staging

# Set secret with value (use cautiously)
gh secret set SECRET_NAME --env staging --body "value"

# Set variable for environment
gh variable set VAR_NAME --env staging --body "value"

# List secrets (names only, not values)
gh secret list --env staging

# List variables
gh variable list --env staging

# Delete secret
gh secret delete SECRET_NAME --env staging
```

---

## Integration with Other Skills

### → designer skill

The designer skill creates the app spec that deployment consumes:

```bash
# Designer creates .do/app.yaml
# Deployment workflow reads and deploys it
```

### → postgres skill (and future data service skills)

The postgres skill handles database creation and credential management. The deployment skill consumes those credentials via GitHub Secrets:

```bash
# Postgres skill creates database, stores credentials in GitHub Secrets:
gh secret set DATABASE_URL --env staging --body "postgresql://..."

# Deployment workflow uses them via GitHub environment:
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

Future skills (mysql, mongodb, spaces, opensearch, kafka, valkey, gradient-ai) will follow the same pattern.

### → troubleshooting skill

When deployments fail, hand off to troubleshooting skill:

```bash
# If deployment fails:
# 1. Check build logs: doctl apps logs $APP_ID --type build
# 2. Check deploy logs: doctl apps logs $APP_ID --type deploy
# 3. Use troubleshooting skill for deeper diagnosis
```

### → dev-containers skill

Ensure local development matches deployment:

```bash
# Dev containers should use same env vars as production
# .devcontainer/ should mirror .do/app.yaml structure
```

---

## Opinionated Defaults

| Decision | Default | Rationale |
|----------|---------|-----------|
| CI Platform | GitHub Actions | Best DO integration via app_action |
| Deploy Action | digitalocean/app_action/deploy@v2 | Handles spec + deploy in one step |
| Secrets | GitHub Secrets per environment | Secure, AI never sees values |
| Environments | Separate per stage | Clean isolation, easy filtering |
| deploy_on_push | false in app spec | Let GitHub Actions control deploys |
| Wait for deploy | Yes (default in app_action) | Know if deployment succeeded |
| App spec location | .do/app.yaml | Conventional, matches DO button |
| Log output | Disabled in workflow | View in console/doctl instead |
| Python env | uv | Fast, reliable |
| Node env | nvm | Version management |

---

## Troubleshooting Deployments

### Common Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| App spec not found | `Error: spec file not found` | Ensure `.do/app.yaml` exists |
| Invalid token | `401 Unauthorized` | Check `DIGITALOCEAN_ACCESS_TOKEN` secret |
| Project not found | `project_id is invalid` | Verify `DO_PROJECT_ID` variable |
| Build fails | `BuildJobFailed` | Check build logs, fix dependencies |
| Deploy fails | `ContainerHealthChecksFailed` | Check health endpoint, PORT usage |
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

---

## Quick Reference

### Minimum Viable Deployment

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: digitalocean/app_action/deploy@v2
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
```

### Full Production Setup Checklist

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

## Documentation Links

- [app_action GitHub Repository](https://github.com/digitalocean/app_action)
- [App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [App Spec Reference](https://docs.digitalocean.com/products/app-platform/reference/app-spec/)
- [Environment Support Blog](https://www.digitalocean.com/blog/environment-support-app-platform)
- [GitHub Actions for App Platform Blog](https://www.digitalocean.com/blog/github-actions-for-app-platform)
- [doctl apps reference](https://docs.digitalocean.com/reference/doctl/reference/apps/)
- [GitHub Environments Docs](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
