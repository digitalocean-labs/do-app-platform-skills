# GitHub Actions Workflow Templates

Complete collection of GitHub Actions workflows for DigitalOcean App Platform deployments.

---

## Minimum Viable Deployment

The simplest possible workflow:

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

---

## Basic Environment Deployment

Deploy to staging or production with manual environment selection:

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

## Production Deployment with Approval

Enhanced workflow requiring explicit confirmation for production:

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

---

## PR Preview Environments

### Preview Deployment Workflow

Creates unique preview apps for each pull request:

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

Automatically deletes preview apps when PRs are closed:

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

## Multi-Environment with Single Workflow

One workflow that auto-deploys based on branch or manual trigger:

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

## Rollback Workflow

Deploy a specific commit SHA for rollback:

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

## Local Deployment Script (Fallback)

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

## Workflow Selection Guide

| Scenario | Workflow |
|----------|----------|
| Simple single-environment | Minimum Viable Deployment |
| Staging + production | Basic Environment Deployment |
| Production needs approval | Production with Approval |
| Test PRs before merge | PR Preview Environments |
| Multiple environments, one workflow | Multi-Environment Single Workflow |
| Need to revert quickly | Rollback Workflow |

---

## app_action Reference

### Available Actions

| Action | Purpose |
|--------|---------|
| `digitalocean/app_action/deploy@v2` | Deploy or update app |
| `digitalocean/app_action/delete@v2` | Delete app |

### Deploy Action Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `token` | Yes | DigitalOcean API token |
| `project_id` | No | Target project ID |
| `app_name` | No | Override app name |
| `deploy_pr_preview` | No | Create unique app per PR |
| `print_build_logs` | No | Output build logs (default: true) |
| `print_deploy_logs` | No | Output deploy logs (default: true) |

### Deploy Action Outputs

| Output | Description |
|--------|-------------|
| `app` | JSON object with app details |
| `build_logs` | Build phase logs |
| `deploy_logs` | Deploy phase logs |

### Delete Action Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `token` | Yes | DigitalOcean API token |
| `app_id` | Conditional | App ID to delete |
| `from_pr_preview` | No | Delete PR preview app |
| `ignore_not_found` | No | Don't fail if app doesn't exist |
