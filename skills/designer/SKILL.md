---
name: app-platform-designer
description: Transform natural language application descriptions into production-ready DigitalOcean App Platform specifications
version: 1.0.0
author: Bikram Gupta
triggers:
  - "design my app"
  - "create app spec"
  - "new application"
  - "architect"
  - "structure my service"
  - "app spec"
  - "generate app spec"
  - "app platform architecture"
  - "deploy to do button"
outputs:
  - path: .do/app.yaml
    description: App Platform specification for CLI/API deployment
  - path: .do/deploy.template.yaml
    description: Deploy to DigitalOcean button template (public repos only)
  - path: .env.example
    description: Environment variable template
consumes:
  - Repository structure analysis
  - Natural language requirements
produces_for:
  - deployment skill (consumes app spec)
  - devcontainers skill (reads app spec for local parity)
---

# App Platform Designer Skill

## Overview

Transform natural language descriptions into production-ready App Platform specifications. This skill is the "architect" that decomposes requirements into components, selects appropriate resources, and generates valid app specs with sensible defaults.

**Primary question this skill answers:**
> "I want to build [description]. What should my App Platform architecture look like, and give me the app spec."

**What this skill produces:**
- `.do/app.yaml` — Complete App Platform specification
- `.do/deploy.template.yaml` — Deploy to DO button (public repos only)
- `.env.example` — Environment variable template
- Architecture diagram (Mermaid, for 3+ components)

**When to use this skill:**
- "Design an app with API, worker, and database"
- "Create app spec for my Next.js app"
- "I have a monorepo, help me structure it for App Platform"
- "Add a Deploy to DigitalOcean button to my repo"

**When NOT to use this skill:**
- Migrating from another platform → use **migration** skill
- Deploying an existing spec → use **deployment** skill
- Database schemas and users → use **postgres** skill
- Local development setup → use **devcontainers** skill

---

## Opinionated Defaults

| Decision | Default | Rationale |
|----------|---------|-----------|
| Instance size | `apps-s-1vcpu-1gb` | Good starting point, scales up easily |
| Instance count | 1 | Start minimal, scale based on load |
| Database | Dev database for testing, Managed for production | Cost-effective progression |
| Cache | Valkey (not Redis) | Redis is EOL on DO |
| Build | Dockerfile if present, else buildpack | Dockerfile gives more control |
| Health check | `GET /health` or `GET /healthz` | Industry standard |
| Deploy on push | `true` | GitOps workflow |
| Region | `nyc` | Good default, user can change |
| Source format | `git:` block (not `github:`) | Required for deploy.template.yaml compatibility |

---

## Quick Reference

### Instance Sizes

| Slug | CPU | RAM | Price | Scaling |
|------|-----|-----|-------|---------|
| `apps-s-1vcpu-0.5gb` | 1 shared | 512 MiB | $5/mo | No |
| `apps-s-1vcpu-1gb-fixed` | 1 shared | 1 GiB | $10/mo | No |
| `apps-s-1vcpu-1gb` | 1 shared | 1 GiB | $12/mo | Yes |
| `apps-s-1vcpu-2gb` | 1 shared | 2 GiB | $25/mo | Yes |
| `apps-s-2vcpu-4gb` | 2 shared | 4 GiB | $50/mo | Yes |
| `apps-d-1vcpu-0.5gb` | 1 dedicated | 512 MiB | $29/mo | Yes |
| `apps-d-1vcpu-1gb` | 1 dedicated | 1 GiB | $34/mo | Yes |
| `apps-d-1vcpu-2gb` | 1 dedicated | 2 GiB | $39/mo | Yes |
| `apps-d-1vcpu-4gb` | 1 dedicated | 4 GiB | $49/mo | Yes |
| `apps-d-2vcpu-4gb` | 2 dedicated | 4 GiB | $78/mo | Yes |
| `apps-d-2vcpu-8gb` | 2 dedicated | 8 GiB | $98/mo | Yes |
| `apps-d-4vcpu-8gb` | 4 dedicated | 8 GiB | $156/mo | Yes |
| `apps-d-4vcpu-16gb` | 4 dedicated | 16 GiB | $196/mo | Yes |
| `apps-d-8vcpu-32gb` | 8 dedicated | 32 GiB | $392/mo | Yes |

**Sizing guidance:**
- Start with `apps-s-1vcpu-1gb` for most workloads
- Use dedicated (`apps-d-*`) for consistent performance requirements
- Workers can often use smaller instances than services

### Regions

| Slug | Location |
|------|----------|
| `nyc` | New York |
| `ams` | Amsterdam |
| `sfo` | San Francisco |
| `sgp` | Singapore |
| `lon` | London |
| `fra` | Frankfurt |
| `tor` | Toronto |
| `blr` | Bangalore |
| `syd` | Sydney |
| `atl` | Atlanta |

### Database Engines

| Engine | Slug | Dev DB? | Notes |
|--------|------|---------|-------|
| PostgreSQL | `PG` | ✅ Yes | Recommended. Dev DB: $7/mo, 1GB limit |
| MySQL | `MYSQL` | ❌ No | Must create managed cluster first |
| Valkey | `VALKEY` | ✅ Yes | Use instead of Redis (Redis is EOL) |
| MongoDB | `MONGODB` | ❌ No | Must create managed cluster first |
| Kafka | `KAFKA` | ❌ No | Must create managed cluster first, special setup |
| OpenSearch | `OPENSEARCH` | ❌ No | Must create managed cluster first |

**Dev database:** Set `production: false` (or omit). App Platform creates it automatically.
**Managed database:** Set `production: true` + `cluster_name`. Must create cluster first via `doctl databases create` or console.

**Database decision tree:**
```
What data storage do you need?
├─ Relational data?
│  ├─ PostgreSQL OK? → PG (dev DB available)
│  └─ MySQL required? → MYSQL (managed only)
├─ Caching/sessions/queues? → VALKEY (dev DB available)
├─ Document store? → MONGODB (managed only)
├─ Search? → OPENSEARCH (managed only)
└─ Event streaming? → KAFKA (managed only, special setup)

Dev DB or Managed?
├─ Testing/small app (<1GB data)? → Dev DB (production: false)
└─ Production/scaling/features? → Managed (production: true)
   └─ Create cluster first: doctl databases create ...
```

### Buildpack Slugs (environment_slug)

| Slug | Language/Framework |
|------|-------------------|
| `node-js` | Node.js (default: v22.x) |
| `python` | Python |
| `go` | Go |
| `ruby` | Ruby |
| `php` | PHP |
| `hugo` | Hugo static sites |
| `bun` | Bun runtime |

---

## Core Workflows

### Workflow 1: Natural Language → App Spec

**Trigger:** "I need a web app with [description]"

**Process:**

1. **Gather requirements** (ask if not provided):
   - What does the app do?
   - Language/framework?
   - Database needs?
   - Background processing?
   - Expected traffic level?

2. **Decompose into components:**
   - Identify HTTP-facing services → `services`
   - Identify background processors → `workers`
   - Identify one-time/scheduled tasks → `jobs`
   - Identify static frontends → `static_sites`
   - Identify data stores → `databases`

3. **Generate app spec** with:
   - Appropriate component types
   - Health checks
   - Environment variables with placeholders
   - Internal routing for component communication

4. **Validate spec:**
   ```bash
   doctl apps spec validate .do/app.yaml
   ```

5. **Offer next steps:**
   - "To deploy: use the **deployment** skill"
   - "For local dev: use the **devcontainers** skill"

---

### Workflow 2: Analyze Repository → App Spec

**Trigger:** "Here's my repo, create an app spec"

**Process:**

1. **Analyze repository structure:**
   ```
   Check for:
   ├── Dockerfile → Use dockerfile build
   ├── package.json → Node.js app
   ├── requirements.txt / pyproject.toml → Python app
   ├── go.mod → Go app
   ├── Gemfile → Ruby app
   ├── composer.json → PHP app
   └── Multiple directories with above → Monorepo
   ```

2. **Detect entry points:**
   - `package.json` scripts: `start`, `dev`, `build`
   - Python: `main.py`, `app.py`, `manage.py`
   - Procfile if present

3. **Infer component needs:**
   - Web entry point → Service
   - Worker processes → Workers
   - Celery/Bull/Sidekiq → Workers
   - Scheduled tasks → Jobs

4. **Generate spec matching detected structure**

5. **Validate and present**

---

### Workflow 3: Multi-Environment Setup

**Trigger:** "I need dev, staging, and prod environments"

**Process:**

1. **Generate base spec** (`.do/app.yaml`)

2. **Create environment variations:**
   - `.do/app.dev.yaml` — Smaller instances, dev database
   - `.do/app.staging.yaml` — Production-like, different domain
   - `.do/app.prod.yaml` — Full resources, production domain

3. **Document differences:**

| Aspect | Dev | Staging | Prod |
|--------|-----|---------|------|
| Instance size | `apps-s-1vcpu-0.5gb` | `apps-s-1vcpu-1gb` | `apps-d-1vcpu-2gb` |
| Instance count | 1 | 1 | 2+ |
| Database | Dev DB | Managed (small) | Managed (sized) |
| Domain | `*.ondigitalocean.app` | `staging.example.com` | `example.com` |

---

### Workflow 4: Generate Deploy to DO Button

**Trigger:** "Add Deploy to DigitalOcean button" or "Create deploy.template.yaml"

**Prerequisites:**
- Public GitHub repository (required)
- Working app spec

**Process:**

1. **Verify repo is public** — Deploy to DO only works with public repos

2. **Generate `.do/deploy.template.yaml`:**

   **Critical difference from app.yaml:**
   - Wrap everything under `spec:` key
   - Use `git:` block instead of `github:` block
   - Use `repo_clone_url` with full HTTPS URL

3. **Generate README badge:**

   ```markdown
   [![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/OWNER/REPO/tree/BRANCH)
   ```

4. **Provide button variations:**
   - Blue: `do-btn-blue.svg`
   - Blue Ghost: `do-btn-blue-ghost.svg`
   - White: `do-btn-white.svg`
   - White Ghost: `do-btn-white-ghost.svg`

---

## Component Types

### Services (HTTP Workloads)

**When to use:** Component serves HTTP/HTTPS traffic to users or external systems.

```yaml
services:
  - name: api
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    http_port: 8080
    instance_size_slug: apps-s-1vcpu-1gb
    instance_count: 1
    health_check:
      http_path: /health
      initial_delay_seconds: 10
      period_seconds: 10
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
```

**Key settings:**
- `http_port`: Port your app listens on (default: 8080)
- `health_check`: Required for reliability
- `routes`: Define URL paths (deprecated, use `ingress` instead)

---

### Workers (Background Processors)

**When to use:** Background jobs, queue consumers, internal services that don't need public HTTP.

```yaml
workers:
  - name: queue-processor
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /worker
    instance_size_slug: apps-s-1vcpu-0.5gb
    instance_count: 1
    run_command: python worker.py
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
```

**Key insight:** Workers are cheaper and appropriate for:
- Queue consumers (Celery, Bull, Sidekiq)
- Background job processors
- Internal APIs that only services call
- Scheduled polling tasks

---

### Jobs (One-time/Scheduled Tasks)

**When to use:** Database migrations, scheduled reports, cleanup tasks.

```yaml
jobs:
  - name: migrate
    kind: PRE_DEPLOY
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    run_command: npm run migrate
    instance_size_slug: apps-s-1vcpu-0.5gb
    instance_count: 1
```

**Job kinds:**
- `PRE_DEPLOY`: Runs before deployment (migrations)
- `POST_DEPLOY`: Runs after deployment (cache warming)
- `FAILED_DEPLOY`: Runs if deployment fails (notifications)
- `SCHEDULED`: Runs on cron schedule

**Scheduled job example:**
```yaml
jobs:
  - name: daily-report
    kind: SCHEDULED
    schedule:
      cron: "0 9 * * *"
      time_zone: America/New_York
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    run_command: python generate_report.py
```

---

### Static Sites

**When to use:** Frontend apps, marketing sites, documentation.

```yaml
static_sites:
  - name: frontend
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    build_command: npm run build
    output_dir: dist
    index_document: index.html
    error_document: 404.html
    envs:
      - key: NEXT_PUBLIC_API_URL
        scope: BUILD_TIME
        value: https://api.example.com
```

**Key settings:**
- `output_dir`: Where built assets live (common: `dist`, `build`, `public`, `_static`)
- `catchall_document`: For SPAs, route all paths to index.html

---

### Databases

App Platform supports two types of databases:

#### Dev Databases (PostgreSQL Only)

Dev databases are fully managed by App Platform—they don't appear in your DO Databases console and are private to your app.

```yaml
databases:
  - name: db
    engine: PG
    production: false  # or omit entirely
    version: "16"      # optional: 13, 14, 15, 16
```

- $7/month, 1GB limit
- PostgreSQL only (no MySQL, Valkey, etc.)
- Good for development, testing, small production apps
- Auto-provides `${db.DATABASE_URL}` bindable variable

#### Managed Databases (All Engines)

Managed databases are full DigitalOcean Managed Database clusters. **You must create the cluster first**, then reference it in your app spec.

**Step 1: Create the managed database cluster**
```bash
# Create cluster via CLI
doctl databases create my-app-db \
  --engine pg \
  --region nyc \
  --size db-s-1vcpu-1gb \
  --version 16

# Get cluster ID
CLUSTER_ID=$(doctl databases list --format ID --no-header | head -1)

# Create a database within the cluster
doctl databases db create $CLUSTER_ID myappdb

# Create a user (DO generates and stores the password)
doctl databases user create $CLUSTER_ID myappuser

# Or do all of this via console: Create → Databases
```

**Step 2: Reference it in app spec**
```yaml
databases:
  - name: db                          # Component name (for bindable vars)
    engine: PG
    production: true                  # Signals this is a managed database
    cluster_name: my-app-db           # Must match existing cluster name
    db_name: myappdb                  # Database within cluster (optional)
    db_user: myappuser                # User within cluster (optional)
```

**Key points:**
- Dev databases are created automatically. Managed databases must exist before you reference them.
- Users MUST be created via DigitalOcean interface (console, API, or doctl)—not via raw SQL
- App Platform automatically retrieves credentials for users created via DO interface
- Your app is automatically added as a trusted source for secure connectivity

#### Bindable Environment Variables

Both dev and managed databases expose connection details via bindable variables. **This works automatically for any user created via DigitalOcean's interface** (console, API, or doctl).

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `${db.DATABASE_URL}` | Full connection string | `postgresql://user:pass@host:25060/dbname?sslmode=require` |
| `${db.HOSTNAME}` | Database host | `cluster-do-user-123.db.ondigitalocean.com` |
| `${db.PORT}` | Database port | `25060` |
| `${db.USERNAME}` | Database user | `myappuser` |
| `${db.PASSWORD}` | Database password | (auto-populated) |
| `${db.DATABASE}` | Database name | `myappdb` |
| `${db.CA_CERT}` | CA certificate (for TLS) | (certificate content) |

Where `db` is the component name you specified in the app spec.

**Verified behavior:** When you specify `db_user: myappuser` in your app spec, App Platform automatically retrieves the password for that user from DigitalOcean's internal credential store. You never need to manually copy/paste passwords.

**Usage in app spec:**
```yaml
services:
  - name: api
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      # Or access individual components:
      - key: DB_HOST
        scope: RUN_TIME
        value: ${db.HOSTNAME}
      - key: DB_USER
        scope: RUN_TIME
        value: ${db.USERNAME}
```

**Important:** This only works for users created via DigitalOcean's interface. If you create a user via raw SQL (`CREATE USER...`), App Platform won't have access to the password.

#### Connection Pools (PostgreSQL Only)

For high-traffic apps, use connection pools to reduce database connection overhead.

**Step 1:** Create a connection pool on your managed PostgreSQL cluster (via console or API)

**Step 2:** Reference it in environment variables:
```yaml
envs:
  - key: DATABASE_POOL_URL
    scope: RUN_TIME
    value: ${db.my-pool-name.DATABASE_URL}
```

Where `my-pool-name` is the name of the connection pool you created.

#### Valkey/Redis for Caching

For caching, sessions, or queues, add Valkey (Redis is EOL on DO):

**Dev Valkey:**
```yaml
databases:
  - name: cache
    engine: VALKEY
    production: false
```

**Managed Valkey:**
```bash
# Create first
doctl databases create my-app-cache --engine valkey --region nyc --size db-s-1vcpu-1gb
```

```yaml
databases:
  - name: cache
    engine: VALKEY
    production: true
    cluster_name: my-app-cache
```

**Usage:**
```yaml
envs:
  - key: VALKEY_URL
    scope: RUN_TIME
    value: ${cache.DATABASE_URL}
```

#### Database Decision Summary

| Need | Engine | Dev Available? | Notes |
|------|--------|----------------|-------|
| Relational data | `PG` | Yes | Recommended default |
| MySQL required | `MYSQL` | No | Must use managed |
| Caching/sessions | `VALKEY` | Yes | Use instead of Redis |
| Document store | `MONGODB` | No | Must use managed |
| Search | `OPENSEARCH` | No | Must use managed |
| Event streaming | `KAFKA` | No | Must use managed, special setup |

#### Trusted Sources (Managed Databases)

When you attach a managed database, you should configure trusted sources for security.

**Without VPC:** App Platform can automatically be added as a trusted source using `--rule app:<app-id>`.

**With VPC (Recommended):** You must manually add the app's VPC egress private IP:
```bash
# Find VPC egress IP from inside container: ip addr show | grep "inet 10\."
doctl databases firewalls append <cluster-id> --rule ip_addr:10.x.x.x
```

> **See [networking skill](../networking/SKILL.md)** for complete VPC + trusted sources setup.

**Limitations:**
- **Build time:** Cannot connect with trusted sources enabled (use PRE_DEPLOY job for migrations)
- **Kafka:** Trusted sources NOT supported — must be disabled
- **OpenSearch:** Log forwarding doesn't work with trusted sources enabled

#### Debug Pattern: Alpine Worker for Connectivity Testing

When troubleshooting database connectivity, deploy a minimal Alpine worker to verify environment variables and connections work before debugging your actual application:

```yaml
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
      - key: DB_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: DB_HOST
        scope: RUN_TIME
        value: ${db.HOSTNAME}
      - key: DB_USER
        scope: RUN_TIME
        value: ${db.USERNAME}
```

Deploy, then use the Console tab to verify:
```bash
echo $DB_URL
echo $DB_HOST
echo $DB_USER
```

This deploys in under a minute and confirms your database configuration is correct before you debug application-level issues. Remove the debug worker once verified.

---

## Architecture Patterns

### Pattern 1: Single Service + Database

The simplest production-ready setup.

```yaml
name: my-app
region: nyc
services:
  - name: web
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    http_port: 8080
    instance_size_slug: apps-s-1vcpu-1gb
    instance_count: 1
    health_check:
      http_path: /health
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
databases:
  - name: db
    engine: PG
    production: false
```

---

### Pattern 2: API + Static Frontend

Separate backend API from frontend SPA.

```yaml
name: fullstack-app
region: nyc
services:
  - name: api
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /api
    http_port: 8080
    instance_size_slug: apps-s-1vcpu-1gb
    health_check:
      http_path: /health
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
static_sites:
  - name: frontend
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /frontend
    build_command: npm run build
    output_dir: dist
    envs:
      - key: VITE_API_URL
        scope: BUILD_TIME
        value: ${api.PUBLIC_URL}
databases:
  - name: db
    engine: PG
    production: false
ingress:
  rules:
    - match:
        path:
          prefix: /api
      component:
        name: api
    - match:
        path:
          prefix: /
      component:
        name: frontend
```

---

### Pattern 3: Service + Worker + Database

For apps with background processing.

```yaml
name: async-app
region: nyc
services:
  - name: api
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    http_port: 8080
    instance_size_slug: apps-s-1vcpu-1gb
    health_check:
      http_path: /health
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: VALKEY_URL
        scope: RUN_TIME
        value: ${cache.DATABASE_URL}
workers:
  - name: processor
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    run_command: python worker.py
    instance_size_slug: apps-s-1vcpu-0.5gb
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: VALKEY_URL
        scope: RUN_TIME
        value: ${cache.DATABASE_URL}
databases:
  - name: db
    engine: PG
    production: false
  - name: cache
    engine: VALKEY
    production: false
```

---

### Pattern 4: Monorepo Multi-Service

Multiple services from one repository.

```yaml
name: monorepo-app
region: nyc
services:
  - name: api
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /packages/api
    http_port: 8080
    instance_size_slug: apps-s-1vcpu-1gb
    health_check:
      http_path: /health
  - name: admin
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /packages/admin
    http_port: 3000
    instance_size_slug: apps-s-1vcpu-0.5gb
    health_check:
      http_path: /health
static_sites:
  - name: web
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /packages/web
    build_command: npm run build
    output_dir: dist
ingress:
  rules:
    - match:
        path:
          prefix: /api
      component:
        name: api
    - match:
        path:
          prefix: /admin
      component:
        name: admin
    - match:
        path:
          prefix: /
      component:
        name: web
```

**Key:** Use `source_dir` to point to each package's directory.

---

### Pattern 5: SaaS Multi-Component

Complex SaaS with multiple user-facing services.

```yaml
name: saas-platform
region: nyc
services:
  - name: api
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /services/api
    http_port: 8080
    instance_size_slug: apps-s-1vcpu-2gb
    instance_count: 2
    autoscaling:
      min_instance_count: 2
      max_instance_count: 10
      metrics:
        cpu:
          percent: 70
    health_check:
      http_path: /health
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
workers:
  - name: jobs
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /services/jobs
    run_command: node worker.js
    instance_size_slug: apps-s-1vcpu-1gb
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
jobs:
  - name: migrate
    kind: PRE_DEPLOY
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /services/api
    run_command: npm run migrate
  - name: daily-reports
    kind: SCHEDULED
    schedule:
      cron: "0 6 * * *"
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /services/reports
    run_command: python generate.py
static_sites:
  - name: dashboard
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /apps/dashboard
    build_command: npm run build
    output_dir: dist
  - name: marketing
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /apps/marketing
    build_command: npm run build
    output_dir: out
databases:
  - name: db
    engine: PG
    production: true
    cluster_name: saas-prod-db
domains:
  - domain: api.example.com
    type: PRIMARY
  - domain: app.example.com
    type: ALIAS
  - domain: www.example.com
    type: ALIAS
ingress:
  rules:
    - match:
        path:
          prefix: /api
      component:
        name: api
    - match:
        path:
          prefix: /
      component:
        name: dashboard
alerts:
  - rule: DEPLOYMENT_FAILED
  - rule: DOMAIN_FAILED
```

---

## Environment Variables

### Scopes

| Scope | Available | Use Case |
|-------|-----------|----------|
| `RUN_TIME` | Only at runtime | Secrets, DB URLs |
| `BUILD_TIME` | Only during build | Public API URLs, feature flags |
| `RUN_AND_BUILD_TIME` | Both | NPM tokens, shared config |

### Types

| Type | Behavior |
|------|----------|
| `GENERAL` | Plain text, visible in UI |
| `SECRET` | Encrypted, hidden in UI after first save |

### Placeholder Patterns

| Pattern | Resolves To |
|---------|-------------|
| `${db.DATABASE_URL}` | Database connection string |
| `${db.CA_CERT}` | Database CA certificate |
| `${service-name.PRIVATE_URL}` | Internal URL of another component |
| `${service-name.PUBLIC_URL}` | Public URL of another component |
| `${APP_URL}` | App's default URL |

### Example Environment Block

```yaml
envs:
  # Database (injected from managed database)
  - key: DATABASE_URL
    scope: RUN_TIME
    value: ${db.DATABASE_URL}
  
  # Secret (user provides, encrypted)
  - key: JWT_SECRET
    scope: RUN_TIME
    type: SECRET
    value: PLACEHOLDER_CHANGE_ME
  
  # Build-time config
  - key: NEXT_PUBLIC_API_URL
    scope: BUILD_TIME
    value: https://api.example.com
  
  # Internal service communication
  - key: AUTH_SERVICE_URL
    scope: RUN_TIME
    value: ${auth.PRIVATE_URL}
```

---

## Ingress and Routing

The modern way to configure routing (replaces deprecated `routes`).

> **For advanced networking** (subdomain routing, wildcard domains, CORS, VPC, static IPs), see the [networking skill](../networking/SKILL.md).

### Basic Path Routing

```yaml
ingress:
  rules:
    - match:
        path:
          prefix: /api
      component:
        name: api
    - match:
        path:
          prefix: /
      component:
        name: frontend
```

### Path Rewriting

```yaml
ingress:
  rules:
    - match:
        path:
          prefix: /v1/api
      component:
        name: api
        rewrite: /api  # Strips /v1 before forwarding
```

### Redirects

```yaml
ingress:
  rules:
    - match:
        path:
          prefix: /old-path
      redirect:
        uri: /new-path
        redirect_code: 301
```

### CORS Configuration

```yaml
ingress:
  rules:
    - match:
        path:
          prefix: /api
      component:
        name: api
      cors:
        allow_origins:
          - exact: https://example.com
          - regex: ^https://.*\.example\.com$
        allow_methods:
          - GET
          - POST
          - PUT
          - DELETE
        allow_headers:
          - Content-Type
          - Authorization
        max_age: "1h"
```

---

## Validation

Always validate specs before deployment:

```bash
# Validate app spec
doctl apps spec validate .do/app.yaml

# Validate deploy template
doctl apps spec validate .do/deploy.template.yaml
```

**Common validation errors:**

| Error | Cause | Fix |
|-------|-------|-----|
| `invalid component name` | Uppercase or special chars | Use lowercase, alphanumeric, hyphens |
| `unknown instance size` | Invalid slug | Check Quick Reference section |
| `invalid database reference` | Typo in `${db.X}` | Verify database name matches |
| `routes is deprecated` | Using old routing | Switch to `ingress.rules` |

---

## Deploy to DO Button Deep Dive

### When to Use

- Public GitHub repositories only
- For community awareness and easy onboarding
- Open source projects
- Tutorials and demos

### app.yaml vs deploy.template.yaml

| Aspect | app.yaml | deploy.template.yaml |
|--------|----------|---------------------|
| Wrapper | None | `spec:` key required |
| Git source | `github:` block | `git:` block with `repo_clone_url` |
| Usage | `doctl apps create --spec` | Deploy to DO button |
| Repo visibility | Any | Public only |

### Conversion Example

**app.yaml:**
```yaml
name: my-app
region: nyc
services:
  - name: web
    github:
      repo: owner/repo
      branch: main
      deploy_on_push: true
    http_port: 8080
```

**deploy.template.yaml:**
```yaml
spec:
  name: my-app
  region: nyc
  services:
    - name: web
      git:
        repo_clone_url: https://github.com/owner/repo.git
        branch: main
      http_port: 8080
```

### Button HTML/Markdown

**Markdown (README.md):**
```markdown
[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/OWNER/REPO/tree/BRANCH)
```

**HTML (website):**
```html
<a href="https://cloud.digitalocean.com/apps/new?repo=https://github.com/OWNER/REPO/tree/BRANCH">
  <img src="https://www.deploytodo.com/do-btn-blue.svg" alt="Deploy to DO">
</a>
```

### Environment Variable Prompts

Variables without values prompt user at deploy time:

```yaml
spec:
  name: my-app
  services:
    - name: web
      envs:
        # Will prompt user for value
        - key: API_KEY
          scope: RUN_TIME
          type: SECRET
        # Has default, user can edit
        - key: LOG_LEVEL
          scope: RUN_TIME
          value: "info"
```

---

## Architecture Diagrams

For complex apps (3+ components), generate a Mermaid diagram:

```mermaid
graph TB
    subgraph "App Platform"
        subgraph "Services"
            API[api<br/>:8080]
            Admin[admin<br/>:3000]
        end
        
        subgraph "Workers"
            Jobs[jobs]
        end
        
        subgraph "Static Sites"
            Web[web]
        end
        
        subgraph "Databases"
            DB[(PostgreSQL)]
            Cache[(Valkey)]
        end
    end
    
    User((User)) --> Web
    User --> API
    User --> Admin
    
    API --> DB
    API --> Cache
    Jobs --> DB
    Admin --> API
```

---

## Handoff Protocol

When spec is complete:

1. **State artifacts produced:**
   - "Created `.do/app.yaml` with [N] components"
   - "Created `.do/deploy.template.yaml` for Deploy to DO button" (if applicable)

2. **Validate:**
   ```bash
   doctl apps spec validate .do/app.yaml
   ```

3. **Suggest next steps:**
   - "To deploy: use the **deployment** skill"
   - "For local development: use the **devcontainers** skill"
   - "For database setup: use the **postgres** skill"

---

## Complete Example: Next.js + API + Worker

**User request:** "I'm building a Next.js app with a Python API backend and a job processor, using PostgreSQL and Valkey."

**Generated `.do/app.yaml`:**

```yaml
name: nextjs-python-app
region: nyc

services:
  - name: api
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /api
    dockerfile_path: api/Dockerfile
    http_port: 8000
    instance_size_slug: apps-s-1vcpu-1gb
    instance_count: 1
    health_check:
      http_path: /health
      initial_delay_seconds: 10
      period_seconds: 10
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: VALKEY_URL
        scope: RUN_TIME
        value: ${cache.DATABASE_URL}
      - key: SECRET_KEY
        scope: RUN_TIME
        type: SECRET
        value: CHANGE_ME_IN_CONSOLE

workers:
  - name: jobs
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /worker
    dockerfile_path: worker/Dockerfile
    run_command: python worker.py
    instance_size_slug: apps-s-1vcpu-0.5gb
    instance_count: 1
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: VALKEY_URL
        scope: RUN_TIME
        value: ${cache.DATABASE_URL}

jobs:
  - name: migrate
    kind: PRE_DEPLOY
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /api
    run_command: alembic upgrade head
    instance_size_slug: apps-s-1vcpu-0.5gb

static_sites:
  - name: web
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /web
    build_command: npm run build
    output_dir: out
    environment_slug: node-js
    envs:
      - key: NEXT_PUBLIC_API_URL
        scope: BUILD_TIME
        value: ${api.PUBLIC_URL}

databases:
  - name: db
    engine: PG
    production: false
  - name: cache
    engine: VALKEY
    production: false

ingress:
  rules:
    - match:
        path:
          prefix: /api
      component:
        name: api
    - match:
        path:
          prefix: /
      component:
        name: web

alerts:
  - rule: DEPLOYMENT_FAILED
  - rule: DOMAIN_FAILED
```

**Generated `.env.example`:**

```bash
# Database - auto-injected from App Platform
# Format: postgresql://user:pass@host:port/db?sslmode=require
DATABASE_URL=${db.DATABASE_URL}

# Individual database components (if needed)
# DB_HOST=${db.HOSTNAME}
# DB_PORT=${db.PORT}
# DB_USER=${db.USERNAME}
# DB_PASSWORD=${db.PASSWORD}
# DB_NAME=${db.DATABASE}

# Cache (Valkey) - auto-injected from App Platform
# Format: rediss://user:pass@host:port
VALKEY_URL=${cache.DATABASE_URL}

# Secrets (set manually in App Platform console after deploy)
SECRET_KEY=your-secret-key-here

# Frontend build-time variables (set at build time)
NEXT_PUBLIC_API_URL=https://your-app.ondigitalocean.app/api
```

**Note on DATABASE_URL:** The `${db.DATABASE_URL}` bindable variable automatically contains the full connection string including SSL settings. You don't need to construct it manually.

**Architecture diagram:**

```mermaid
graph TB
    subgraph "App Platform"
        Web[web<br/>Next.js Static]
        API[api<br/>Python :8000]
        Jobs[jobs<br/>Worker]
        Migrate[migrate<br/>PRE_DEPLOY]
        
        DB[(PostgreSQL)]
        Cache[(Valkey)]
    end
    
    User((User)) --> Web
    Web --> API
    API --> DB
    API --> Cache
    Jobs --> DB
    Jobs --> Cache
    Migrate --> DB
```

---

## Documentation References

- App Spec Reference: https://docs.digitalocean.com/products/app-platform/reference/app-spec/
- Pricing: https://docs.digitalocean.com/products/app-platform/details/pricing/
- Regions: https://docs.digitalocean.com/products/app-platform/details/availability/
- Buildpacks: https://docs.digitalocean.com/products/app-platform/reference/buildpacks/
- Databases: https://docs.digitalocean.com/products/databases/
- Deploy to DO Button: https://docs.digitalocean.com/products/app-platform/how-to/add-deploy-do-button/
