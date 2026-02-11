# Heroku Migration Workflows

Step-by-step procedures for each migration mode. Read [heroku-overview.md](heroku-overview.md) first to determine which mode applies.

## Table of Contents

1. [Mode 1: Q&A — Concept Mapping](#mode-1-qa--concept-mapping)
2. [Mode 2: Guided — Step-by-Step Assistance](#mode-2-guided--step-by-step-assistance)
3. [Mode 3: Auto-Migrate — Full Automation](#mode-3-auto-migrate--full-automation)
4. [Pipeline Migration Workflow](#pipeline-migration-workflow)
5. [Data Migration Workflow](#data-migration-workflow)

---

## Mode 1: Q&A — Concept Mapping

**When**: User asks conceptual questions about Heroku → App Platform equivalence.

### Procedure

1. Identify the Heroku concept being asked about
2. Look up mapping in [heroku-mapping.md](heroku-mapping.md) or [heroku-addons.md](heroku-addons.md)
3. Provide the App Platform equivalent with:
   - What maps directly
   - What's different (and how)
   - What doesn't exist (and workaround)
4. Include app spec snippet if it helps clarify

### Example Patterns

**"How do Heroku config vars work on App Platform?"**
→ Reference [heroku-mapping.md #environment-variables](heroku-mapping.md#environment-variables)
→ Explain: Config vars → `envs` in app spec. Secrets → `type: SECRET` (GitHub Secrets). Database URLs → bindable variables.

**"What happens to my Heroku Postgres?"**
→ Reference [heroku-addons.md #data-services](heroku-addons.md#data-services)
→ Explain: Maps to DO Managed PostgreSQL. Connection via bindable `${db.DATABASE_URL}`. Plan mapping available.

**"Can I keep my CI/CD pipeline?"**
→ Reference [heroku-concepts.md #pipelines](heroku-concepts.md#pipelines-and-heroku-flow)
→ Explain: Heroku Pipelines → GitHub Actions. Promotion → deploy workflows. Review Apps → preview environments.

---

## Mode 2: Guided — Step-by-Step Assistance

**When**: User wants to migrate but wants to understand and control each step. Typically: "Help me migrate" or "Walk me through this."

### Procedure

#### Step 1: Analyze

```
AI examines the repository:
├── Read Procfile → identify process types
├── Read app.json → identify add-ons, env vars, buildpacks
├── Read heroku.yml → identify Docker configuration (if present)
├── Check for Dockerfile → determine build method
├── Scan code for Heroku-specific patterns
└── Identify runtime (package.json, requirements.txt, etc.)
```

#### Step 2: Present Analysis

Present findings in this format:

```
I've analyzed your Heroku app. Here's what I found:

COMPONENTS:
  <process-type> → <app-platform-type>.<name> (<details>)

DATABASES / SERVICES:
  <heroku-addon> → <do-service> (<plan notes>)

ENVIRONMENT VARIABLES:
  <var-name>: <migration-action>

CODE CHANGES NEEDED:
  1. <specific change with file and reason>

THINGS THAT DON'T MAP:
  <feature>: <options>

Would you like me to explain any of these mappings in more detail?
```

#### Step 3: Generate Migration Plan

On user approval, provide step-by-step instructions:

```
Here's your migration plan. Execute each step and let me know when done:

1. CREATE BRANCH
   git checkout -b migrate/app-platform

2. CODE CHANGES
   File: config/database.py
   Change: Remove postgres:// URL fix on line 23
   Reason: App Platform bindable variables use postgresql:// format

3. CREATE APP SPEC
   I'll generate .do/app.yaml — review it below:
   [show generated app spec]

4. SET SECRETS
   In your GitHub repo → Settings → Secrets:
   - SECRET_KEY: <your value from `heroku config:get SECRET_KEY`>
   - SENDGRID_API_KEY: <your value>

5. CREATE DATABASE
   doctl databases create myapp-db --engine pg --version 16 --region nyc --size db-s-1vcpu-1gb

6. VALIDATE
   doctl apps spec validate .do/app.yaml

7. DEPLOY
   doctl apps create --spec .do/app.yaml

Ready to start with step 1?
```

#### Step 4: Support Each Step

As user executes steps, answer questions and troubleshoot issues.

---

## Mode 3: Auto-Migrate — Full Automation

**When**: User provides repo and wants the AI to do the work. Typically: "Migrate this to App Platform" or "Convert my Heroku app."

### Procedure

#### Phase 1: Discovery

```bash
# Clone and analyze
git clone <repo-url> /tmp/migration-work
cd /tmp/migration-work

# Run detection script
python <skill-path>/scripts/detect_platform.py /tmp/migration-work --json

# Run architecture analysis
python <skill-path>/scripts/analyze_architecture.py /tmp/migration-work --json
```

Parse results. Read Heroku config files directly:
- `Procfile` → process types and commands
- `app.json` → add-ons, env declarations, buildpacks, formation
- `heroku.yml` → Docker config, setup, release phase

#### Phase 2: Mapping (Present Proposal)

**ALWAYS present the mapping proposal to the user before making changes.**

Format:

```
HEROKU MIGRATION PROPOSAL

Source: Heroku (detected from Procfile + app.json)
Build: <buildpack|docker>

COMPONENT MAPPING:
  <process> → <component-type>.<name>

DATABASE MAPPING:
  <addon> → <do-service>

ENV VAR MAPPING:
  <var>: <action>

CODE CHANGES:
  <N> files need modification

ITEMS NEEDING YOUR INPUT:
  <items requiring user decision>

Proceed with this plan?
```

#### Phase 3: Refactoring (On Approval)

```bash
# Create migration branch
git checkout -b migrate/test
```

Apply code changes:
1. **Environment variables**: Update references per mapping
2. **Redis → Valkey**: Update connection variable names if needed
3. **S3 → Spaces**: Update endpoints and credential env vars if applicable
4. **Remove Heroku-specific code**: DATABASE_URL fixes, Heroku-specific middleware
5. **Port binding**: Ensure web process binds to correct port

Generate files:
1. `.do/app.yaml` — using `generate_app_spec.py` or manual composition
2. `.do/deploy.template.yaml` — Deploy-to-DO button
3. `MIGRATION.md` — using `generate_checklist.py`
4. `.env.example` — template with all required env vars

```bash
# Validate app spec
doctl apps spec validate .do/app.yaml
```

#### Phase 4: Commit and Present

```bash
git add .do/app.yaml .do/deploy.template.yaml MIGRATION.md .env.example
git add <modified-files>
git commit -m "Migrate from Heroku to DigitalOcean App Platform

- Generated .do/app.yaml with <N> components
- Mapped <N> Heroku add-ons to DO managed services
- Updated environment variable references
- Created migration checklist"

git push origin migrate/test
```

Present results:

```
Migration branch created: migrate/test

Files created:
├── .do/app.yaml
├── .do/deploy.template.yaml
├── MIGRATION.md
└── .env.example

Code changes:
├── <file>: <change description>
└── <file>: <change description>

MANUAL STEPS REQUIRED:
1. Set GitHub Secrets: <list>
2. Create managed database: <command>
3. Review: git diff main..migrate/test
4. Deploy: Use deployment skill

Data migration: See MIGRATION.md for database migration steps
```

#### Phase 5: Handoff

Suggest next skills:
- **deployment** skill → set up GitHub Actions CI/CD
- **postgres** skill → if complex DB setup needed
- **devcontainers** skill → if local dev environment needed

---

## Pipeline Migration Workflow

For Heroku shops using the full Heroku Flow (pipelines, review apps, CI).

### Step 1: Map Pipeline Stages

```
Heroku Pipeline              GitHub Actions + App Platform
─────────────────            ─────────────────────────────
Review Apps (per PR)    →    Preview environments (deploy_on_push on PR branch)
Staging (auto-deploy)   →    GitHub Actions: deploy to staging app on push to main
Production (promotion)  →    GitHub Actions: deploy to production app (manual trigger or approval)
```

### Step 2: Generate GitHub Actions Workflow

Suggest the **deployment** skill to create `.github/workflows/deploy.yml` with:

```yaml
# Simplified structure — deployment skill generates the full version
name: Deploy
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test    # or pytest, etc.

  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: digitalocean/app_action@v2
        with:
          app_name: myapp-staging
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      # Requires manual approval in GitHub environment settings
    steps:
      - uses: digitalocean/app_action@v2
        with:
          app_name: myapp-production
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
```

### Step 3: Review App Equivalent

App Platform preview environments are created automatically for PRs when `deploy_on_push: true` is configured. Unlike Heroku Review Apps:

- No separate `app.json` needed (uses same app spec)
- Preview URL generated per PR
- Destroyed when PR is closed
- Database: Uses dev database (not per-PR databases like Heroku Review Apps)

---

## Data Migration Workflow

### PostgreSQL: Heroku → DO Managed

```bash
# 1. Create backup on Heroku
heroku pg:backups:capture --app myapp

# 2. Download backup
heroku pg:backups:download --app myapp

# 3. Create DO Managed Database (if not already)
doctl databases create myapp-db --engine pg --version 16 --region nyc --size db-s-1vcpu-1gb

# 4. Get connection details
doctl databases connection myapp-db-id --format Host,Port,User,Password,Database

# 5. Restore to DO Managed Database
pg_restore --verbose --clean --no-acl --no-owner \
  -h <do-host> -U <do-user> -d <do-database> \
  latest.dump

# 6. Verify
psql -h <do-host> -U <do-user> -d <do-database> -c "SELECT count(*) FROM <main-table>;"
```

### Redis: Heroku → DO Managed Valkey

Redis data is typically ephemeral (cache). If persistence is needed:

```bash
# Option A: Let cache rebuild naturally (recommended for caches)
# No data migration needed

# Option B: Export/import if data is critical
# 1. DUMP keys from Heroku Redis
heroku redis:cli --app myapp --confirm myapp
> BGSAVE
> exit

# 2. No direct import — application should warm cache on startup
```

### Verification Checklist

```
[ ] Database row counts match source
[ ] Application connects to new database
[ ] Background jobs process correctly
[ ] Cron jobs execute on schedule
[ ] External service integrations work (email, storage, etc.)
[ ] Health check endpoint responds
[ ] Custom domain resolves (if configured)
[ ] SSL certificate provisioned
```
