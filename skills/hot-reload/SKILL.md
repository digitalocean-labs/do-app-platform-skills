---
name: hot-reload
description: Enable rapid cloud development on DigitalOcean App Platform with 15-30 second iteration cycles instead of 5-7 minute build/deploy cycles
version: 1.0.0
author: Bikram Gupta
source_of_truth: https://github.com/bikramkgupta/do-app-hot-reload-template
triggers:
  - "hot reload"
  - "fast iteration"
  - "cloud dev"
  - "test in app platform"
  - "no rebuild"
  - "quick deploy"
  - "dev environment"
  - "15 second deploy"
---

# Hot Reload Skill

> **Source of Truth:** This skill references the [do-app-hot-reload-template](https://github.com/bikramkgupta/do-app-hot-reload-template) repository. When generating files, **always fetch the latest versions from GitHub** rather than using embedded examples. The repository contains production-tested templates that may be updated with bug fixes and improvements.

## Overview

Enable developers to iterate on code in the cloud (App Platform) without waiting for full rebuild and redeploy cycles. This creates a near-instant feedback loop while running on actual App Platform infrastructure.

**The Problem:**
```
Traditional: Code change → Git push → Build (3-5 min) → Deploy (1-2 min) → Test
             Total: 5-7 minutes per iteration
```

**With Hot Reload:**
```
Hot Reload: Code change → Git push → Sync (15s) → App restarts → Test
            Total: 15-30 seconds per iteration
```

## When to Use This Skill

Use hot-reload when:
- Debugging issues that only reproduce in cloud environment
- Testing with real managed databases (Postgres, Redis, MongoDB)
- Validating networking/VPC configurations
- Integration testing with other App Platform components
- Rapid prototyping that needs cloud resources
- AI-assisted debugging with shell access

Do NOT use for:
- Local development (use **devcontainers** skill instead)
- Production deployments (use **deployment** skill instead)
- Initial app spec creation (use **designer** skill instead)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         App Platform Container                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  GitHub Sync     │    │  Your App        │    │  Health Server   │       │
│  │  (background)    │    │  (port 8080)     │    │  (port 9090)     │       │
│  │                  │    │                  │    │                  │       │
│  │  Polls every     │───▶│  Hot-reload      │    │  Always running  │       │
│  │  15 seconds      │    │  dev server      │    │  Keeps container │       │
│  │                  │    │                  │    │  alive if app    │       │
│  │  Triggers        │    │  npm run dev     │    │  crashes         │       │
│  │  dev_startup.sh  │    │  uvicorn --reload│    │                  │       │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘       │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  /workspaces/app  (synced from GitHub)                                │   │
│  │  ├── dev_startup.sh      # Your startup script                       │   │
│  │  ├── package.json        # Dependencies (auto-detected changes)      │   │
│  │  └── src/                # Your application code                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Port | Purpose |
|-----------|------|---------|
| Your App | 8080 | Your application (public HTTP) |
| Health Server | 9090 | Keeps container alive even if app crashes |
| GitHub Sync | N/A | Background process polling every 15s |

### Pre-built Images

| Image | Repository | Use Case |
|-------|------------|----------|
| Node.js | `hot-reload-node` | Next.js, React, Express, Node APIs |
| Bun | `hot-reload-bun` | Bun apps, fast bundling |
| Python | `hot-reload-python` | FastAPI, Django, Flask |
| Go | `hot-reload-go` | Go APIs with air hot reload |
| Ruby | `hot-reload-ruby` | Rails, Sinatra, Hanami |
| Full Stack | `hot-reload-full` | Multi-language projects |

---

## Quick Start (5 Minutes)

### Prerequisites

- Existing GitHub repository with your application code
- `DIGITALOCEAN_ACCESS_TOKEN` in GitHub Secrets
- `APP_GITHUB_TOKEN` in GitHub Secrets (for private repos only)

### Step 1: Copy Required Files

Copy these files from the hot-reload template to your repository:

```
your-repo/
├── .github/
│   └── workflows/
│       └── deploy-app.yml    # Deployment workflow
├── .do/
│   └── app.yaml              # App Platform spec
└── dev_startup.sh            # Your startup script
```

### Step 2: Create dev_startup.sh

Choose a template based on your framework. **Fetch the latest version from the source repository:**

| Framework | Template Location |
|-----------|-------------------|
| Next.js / Node.js | `examples/dev_startup_nextjs.sh` |
| Python / FastAPI | `examples/dev_startup_python.sh` |
| Go | `examples/dev_startup_go.sh` |
| Ruby / Rails | `examples/dev_startup_rails.sh` |

**Agent Instructions:**
1. Fetch the appropriate template from: `https://github.com/bikramkgupta/do-app-hot-reload-template/tree/main/examples/`
2. Copy it to the user's repository root as `dev_startup.sh`
3. Customize if needed (e.g., change the dev server command)

**What the startup scripts do:**
- Detect dependency file changes (package.json, requirements.txt, go.mod)
- Auto-reinstall when dependencies change
- Start dev server bound to `0.0.0.0:8080`
- Monitor for `.env_updated` trigger (fast env var updates)
- Restart server if it crashes
- Handle graceful shutdown

**Minimal custom example** (if user needs something different):

```bash
#!/bin/bash
set -e

# Install dependencies
npm install

# Start dev server - MUST bind to 0.0.0.0:8080
exec npm run dev -- --hostname 0.0.0.0 --port 8080
```

> **Source of Truth:** Always fetch the latest templates from the [examples/ directory](https://github.com/bikramkgupta/do-app-hot-reload-template/tree/main/examples) in the source repository. The templates there include production-tested features like dependency change detection, graceful restarts, and env var update handling.

### Step 3: Configure .do/app.yaml

**Fetch the latest template from the source repository:**
- Main template: `.do/app.yaml`
- Framework-specific examples: `app-specs/` directory

**Agent Instructions:**
1. Fetch the base template from: `https://github.com/bikramkgupta/do-app-hot-reload-template/blob/main/.do/app.yaml`
2. Or fetch a framework-specific example from: `https://github.com/bikramkgupta/do-app-hot-reload-template/tree/main/app-specs/`
3. Copy to the user's repository as `.do/app.yaml`
4. Customize: app name, region, image repository, and environment variables

**Key configurations to set:**

| Field | Description |
|-------|-------------|
| `name` | Your app name (e.g., `my-dev-app`) |
| `region` | Deployment region (nyc, sfo, ams, sgp, lon, fra, blr, syd, tor) |
| `repository` | Image to use: `hot-reload-node`, `hot-reload-python`, `hot-reload-go`, `hot-reload-ruby`, `hot-reload-bun`, or `hot-reload-full` |
| `instance_size_slug` | Recommended: `apps-s-1vcpu-2gb` for dev |

**Critical configuration (do not change):**

```yaml
# Health check MUST be on port 9090 (not 8080)
internal_ports:
  - 9090
health_check:
  http_path: /dev_health
  port: 9090  # Keeps container alive if app crashes
  initial_delay_seconds: 10
  period_seconds: 10
```

**Adding your app secrets:**

```yaml
envs:
  # Reference secrets stored in GitHub Secrets
  - key: DATABASE_URL
    value: "${DATABASE_URL}"
    scope: RUN_TIME
    type: SECRET
  - key: API_KEY
    value: "${API_KEY}"
    scope: RUN_TIME
    type: SECRET
```

> **Source of Truth:** Always fetch the latest app spec templates from the [.do/](https://github.com/bikramkgupta/do-app-hot-reload-template/tree/main/.do) and [app-specs/](https://github.com/bikramkgupta/do-app-hot-reload-template/tree/main/app-specs) directories. These contain tested configurations with all required environment variables and health check settings.

### Step 4: Add GitHub Secrets

Navigate to your repo → Settings → Secrets and variables → Actions:

| Secret | Required | Description |
|--------|----------|-------------|
| `DIGITALOCEAN_ACCESS_TOKEN` | Yes | Your DO API token |
| `APP_GITHUB_TOKEN` | Private repos | GitHub PAT with repo scope |
| `DATABASE_URL` | If needed | Your database connection string |
| Other app secrets | As needed | API keys, auth secrets, etc. |

### Step 5: Deploy

```bash
# Deploy
gh workflow run deploy-app.yml -f action=deploy

# Watch progress
gh run watch

# Get app URL
doctl apps list --format Name,LiveURL
```

---

## Workflows

### Workflow 1: Initial Setup for Existing Repository

User says: "I want to set up hot reload for my Next.js app"

**Agent Actions:**

1. Identify the framework from package.json or project structure
2. Select appropriate image: `hot-reload-node`
3. Generate dev_startup.sh using the framework template
4. Generate .do/app.yaml with correct configuration
5. Generate .github/workflows/deploy-app.yml
6. Instruct user to add GitHub Secrets
7. Provide deploy command

**Generated Files:**
- `dev_startup.sh` - Framework-specific startup script
- `.do/app.yaml` - App Platform specification
- `.github/workflows/deploy-app.yml` - Deployment workflow

### Workflow 2: Convert Existing App Platform App to Hot Reload

User says: "My App Platform deploys take 7 minutes, I want faster iteration"

**Agent Actions:**

1. Read existing app spec (if available)
2. Identify services and their configurations
3. Replace build-based deployment with pre-built image
4. Preserve environment variables and secrets
5. Add health check configuration for port 9090
6. Generate dev_startup.sh based on existing run command
7. Provide migration steps

**Key Changes:**
```yaml
# BEFORE: Build-based
services:
  - name: api
    github:
      repo: user/repo
      branch: main
      deploy_on_push: true
    build_command: npm run build
    run_command: npm start

# AFTER: Hot-reload
services:
  - name: dev-workspace
    image:
      registry_type: GHCR
      registry: bikramkgupta
      repository: hot-reload-node
      tag: latest
    envs:
      - key: GITHUB_REPO_URL
        value: "${GITHUB_REPO_URL}"
      - key: DEV_START_COMMAND
        value: "bash dev_startup.sh"
```

### Workflow 3: Debug Crashed Application

User says: "My app crashed but I need to debug it in the cloud"

**Agent Actions:**

1. Confirm health check is on port 9090 (container stays alive)
2. Connect and debug:

   **For AI Assistants** — Use the SDK:
   ```python
   from do_app_sandbox import Sandbox

   dev = Sandbox.get_from_id(app_id="your-app-id", component="dev-workspace")
   result = dev.exec("ps aux")  # Check processes
   print(result.stdout)
   ```

   **For Humans**:
   ```bash
   doctl apps console <APP_ID> dev-workspace
   ```
3. Guide through debugging steps

**Key Insight:** Because health check runs on port 9090 (separate from app on 8080), the container stays alive even when the app crashes. This enables shell access for debugging.

### Workflow 4: Update Environment Variables Quickly

User says: "I need to update my API key without redeploying"

**Agent Actions:**

1. Update GitHub Secret with new value
2. Run fast env-vars update:
   ```bash
   gh workflow run deploy-app.yml -f action=env-vars
   ```
3. Wait ~10 seconds for dev server restart

**How It Works:**
1. Workflow writes new .env file to container
2. Creates `.env_updated` trigger file
3. dev_startup.sh detects trigger and restarts dev server
4. No container restart needed

### Workflow 5: Subfolder/Monorepo Setup

User says: "My app is in the `application/` subfolder of a monorepo"

**Agent Actions:**

1. Configure APP_DIR in app spec:
   ```yaml
   envs:
     - key: APP_DIR
       value: "/workspaces/app/application"
       scope: RUN_TIME
   ```
2. Or use path in DEV_START_COMMAND:
   ```yaml
   envs:
     - key: DEV_START_COMMAND
       value: "bash application/dev_startup.sh"
       scope: RUN_TIME
   ```
3. Ensure dev_startup.sh uses APP_DIR variable

---

## Environment Variables Reference

### Required Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_REPO_URL` | Auto-filled by workflow (or set manually) |
| `DEV_START_COMMAND` | Startup command (default: `bash dev_startup.sh`) |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | - | GitHub PAT for private repos |
| `GITHUB_BRANCH` | default | Branch to sync |
| `GITHUB_SYNC_INTERVAL` | 15 | Sync frequency in seconds |
| `APP_DIR` | - | Working directory for startup (for subfolder apps) |
| `PRE_DEPLOY_COMMAND` | - | Hook before app starts (strict mode) |
| `POST_DEPLOY_COMMAND` | - | Hook after app starts (lenient mode) |
| `PRE_DEPLOY_TIMEOUT` | 300 | Timeout for PRE_DEPLOY in seconds |
| `POST_DEPLOY_TIMEOUT` | 300 | Timeout for POST_DEPLOY in seconds |

### Deploy Jobs (PRE/POST_DEPLOY)

Deploy jobs run when a **new commit** is detected (not every sync):

- **PRE_DEPLOY_COMMAND**: Runs before app starts. Failure stops container startup.
- **POST_DEPLOY_COMMAND**: Runs after app starts. Failure is logged but doesn't stop container.

Example use cases:
```yaml
# Database migrations
- key: PRE_DEPLOY_COMMAND
  value: "npm run db:migrate"
  scope: RUN_TIME

# Cache warming
- key: POST_DEPLOY_COMMAND
  value: "npm run cache:warm"
  scope: RUN_TIME
```

---

## Deployment Commands

### Deploy

```bash
# Deploy with default app spec
gh workflow run deploy-app.yml -f action=deploy

# Deploy with custom app spec
gh workflow run deploy-app.yml -f action=deploy -f app_spec_path=.do/staging.yaml
```

### Delete

```bash
gh workflow run deploy-app.yml -f action=delete
```

### Fast Environment Variable Update

```bash
# Update all env vars (~10 seconds, no container restart)
gh workflow run deploy-app.yml -f action=env-vars

# Update specific vars only
gh workflow run deploy-app.yml -f action=env-vars -f include_only_env_vars="DATABASE_URL,API_KEY"
```

### Manual Commands

**doctl commands:**

```bash
# Update app spec (triggers deploy if changed)
doctl apps update <APP_ID> --spec .do/app.yaml

# Force restart (re-runs dev_startup.sh)
doctl apps create-deployment <APP_ID>

# View logs
doctl apps logs <APP_ID>
```

**Shell access — For AI Assistants** (use SDK):

```python
from do_app_sandbox import Sandbox

dev = Sandbox.get_from_id(app_id="your-app-id", component="dev-workspace")
result = dev.exec("ls -la /workspaces/app")
print(result.stdout)
```

**Shell access — For Humans**:

```bash
doctl apps console <APP_ID> dev-workspace
```

---

## Decision Matrix: When to Redeploy

| Change Type | Action Required | Command |
|------------|-----------------|---------|
| App code (src/, components/) | **Wait** | None (auto-syncs in 15s) |
| Dependencies (package.json) | **Wait** | None (auto-reinstalls) |
| dev_startup.sh | **Restart** | `doctl apps create-deployment <APP_ID>` |
| .do/app.yaml | **Update Spec** | `doctl apps update <APP_ID> --spec .do/app.yaml` |
| Environment variables | **Fast Update** | `gh workflow run deploy-app.yml -f action=env-vars` |
| PRE/POST_DEPLOY commands | **Restart** | `doctl apps create-deployment <APP_ID>` |

---

## Troubleshooting

### Container Exits When App Fails

**Problem:** Container restarts when app crashes, losing debug access.

**Solution:** Ensure health check is on port 9090:
```yaml
internal_ports:
  - 9090
health_check:
  http_path: /dev_health
  port: 9090  # NOT 8080
```

### npm install Fails and Container Exits

**Problem:** Using PRE_DEPLOY_COMMAND for npm install causes container exit on failure.

**Solution:** Move npm install to dev_startup.sh (not PRE_DEPLOY_COMMAND). This allows graceful failure handling and shell access for debugging.

### Sync Not Working

**Problem:** Code changes not appearing in container.

**Diagnosis:**
```bash
# Check logs for sync messages
doctl apps logs <APP_ID> | grep -i sync
```

**For AI Assistants** — Check manually via SDK:
```python
from do_app_sandbox import Sandbox

dev = Sandbox.get_from_id(app_id="your-app-id", component="dev-workspace")
result = dev.exec("cd /workspaces/app && git log --oneline -5")
print(result.stdout)
```

**For Humans**:
```bash
doctl apps console <APP_ID> dev-workspace
cd /workspaces/app
git log --oneline -5
```

**Common Causes:**
- `GITHUB_REPO_URL` not set correctly
- `GITHUB_TOKEN` missing for private repo
- `GITHUB_BRANCH` pointing to wrong branch

### App Not Starting on Port 8080

**Problem:** App starts but isn't accessible.

**Solution:** Ensure your dev server binds to `0.0.0.0:8080`:
```bash
# Node.js
npm run dev -- --hostname 0.0.0.0 --port 8080

# Python
uvicorn main:app --host 0.0.0.0 --port 8080

# Go
go run main.go --addr 0.0.0.0:8080
```

### Welcome Page Shows Instead of App

**Problem:** Seeing the hot-reload welcome page instead of your app.

**Causes:**
1. `GITHUB_REPO_URL` points to the template repo, not your repo
2. `dev_startup.sh` not found in your repo
3. `DEV_START_COMMAND` not configured

---

## Cost Considerations

| Resource | Cost | Notes |
|----------|------|-------|
| apps-s-1vcpu-0.5gb | ~$5/month | Minimal, may be slow |
| apps-s-1vcpu-1gb | ~$10/month | Good for simple apps |
| **apps-s-1vcpu-2gb** | ~$20/month | **Recommended for dev** |
| apps-s-2vcpu-4gb | ~$40/month | For larger apps |

**Tips:**
- Use hot-reload for dev/staging only
- Delete dev environments when not in use
- Use `gh workflow run deploy-app.yml -f action=delete` to clean up

---

## Multi-Component Applications

For apps with multiple services (API + frontend, etc.):

```yaml
name: my-fullstack-dev
region: syd

services:
  - name: api
    image:
      registry_type: GHCR
      registry: bikramkgupta
      repository: hot-reload-python
      tag: latest
    envs:
      - key: DEV_START_COMMAND
        value: "bash api/dev_startup.sh"
      # ... other envs

  - name: frontend
    image:
      registry_type: GHCR
      registry: bikramkgupta
      repository: hot-reload-node
      tag: latest
    envs:
      - key: DEV_START_COMMAND
        value: "bash frontend/dev_startup.sh"
      # ... other envs
```

> **Real-world example:** See the [bun-node-comparison-harness dev branch](https://github.com/bikramkgupta/bun-node-comparison-harness/tree/dev) for a working multi-component hot-reload setup with Bun + Node + load tester.

---

## Integration with Other Skills

| Skill | Integration |
|-------|-------------|
| **devcontainers** | Use for local dev, hot-reload for cloud testing |
| **designer** | Generate app spec, then convert to hot-reload |
| **deployment** | Switch to standard deploy for production |
| **troubleshooting** | Use do-app-sandbox for remote debugging |
| **postgres** | Attach managed database in app spec |

---

## Artifact Contracts

| Artifact | Filename | Description |
|----------|----------|-------------|
| App Spec | `.do/app.yaml` | App Platform specification for hot-reload |
| Startup Script | `dev_startup.sh` | Framework-specific startup script |
| Deploy Workflow | `.github/workflows/deploy-app.yml` | GitHub Actions workflow |

---

## Opinionated Defaults

| Decision | Default | Rationale |
|----------|---------|-----------|
| Instance Size | apps-s-1vcpu-2gb | Balance of cost and performance for dev |
| Sync Interval | 15 seconds | Fast enough for iteration, not overwhelming |
| Health Port | 9090 | Separate from app to keep container alive |
| Region | syd | Override as needed |
| Image Registry | GHCR (bikramkgupta) | Pre-built, tested images |

---

## References

- Hot Reload Template: https://github.com/bikramkgupta/do-app-hot-reload-template
- Remote Debugging: https://github.com/bikramkgupta/do-app-sandbox
- App Platform Docs: https://docs.digitalocean.com/products/app-platform/
- Instance Pricing: https://docs.digitalocean.com/products/app-platform/details/pricing/

