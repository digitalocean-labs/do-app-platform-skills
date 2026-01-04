# Component Types Reference

Detailed reference for App Platform component types.

---

## Services (HTTP Workloads)

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

### Service with Dockerfile

```yaml
services:
  - name: api
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    dockerfile_path: Dockerfile
    http_port: 8080
    instance_size_slug: apps-s-1vcpu-1gb
```

### Service with Buildpack

```yaml
services:
  - name: api
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    environment_slug: node-js
    build_command: npm run build
    run_command: npm start
    http_port: 8080
```

---

## Workers (Background Processors)

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

### Worker with Internal HTTP

Workers can expose internal HTTP endpoints (not publicly routable):

```yaml
workers:
  - name: internal-api
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    http_port: 8080  # Internal only, accessible via PRIVATE_URL
    instance_size_slug: apps-s-1vcpu-0.5gb
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
```

Other components access via `${internal-api.PRIVATE_URL}`.

---

## Jobs (One-time/Scheduled Tasks)

**When to use:** Database migrations, scheduled reports, cleanup tasks.

### Pre-Deploy Job (Migrations)

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

### Post-Deploy Job

```yaml
jobs:
  - name: warm-cache
    kind: POST_DEPLOY
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    run_command: python warm_cache.py
    instance_size_slug: apps-s-1vcpu-0.5gb
```

### Failed Deploy Job

```yaml
jobs:
  - name: notify-failure
    kind: FAILED_DEPLOY
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    run_command: ./notify_slack.sh
    instance_size_slug: apps-s-1vcpu-0.5gb
```

### Scheduled Job (Cron)

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
    instance_size_slug: apps-s-1vcpu-0.5gb
```

**Job kinds:**
| Kind | When it runs |
|------|--------------|
| `PRE_DEPLOY` | Before new containers start |
| `POST_DEPLOY` | After successful deployment |
| `FAILED_DEPLOY` | If deployment fails |
| `SCHEDULED` | On cron schedule |

---

## Static Sites

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

### SPA Configuration

For single-page applications, route all paths to index.html:

```yaml
static_sites:
  - name: spa
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    build_command: npm run build
    output_dir: dist
    catchall_document: index.html  # Routes all paths to index.html
```

### Common Output Directories

| Framework | output_dir |
|-----------|------------|
| Vite | `dist` |
| Create React App | `build` |
| Next.js (static) | `out` |
| Astro | `dist` |
| Hugo | `public` |
| Gatsby | `public` |

---

## Functions (Serverless)

**When to use:** Event-driven endpoints, lightweight APIs.

```yaml
functions:
  - name: webhook
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /functions
    envs:
      - key: API_KEY
        scope: RUN_TIME
        type: SECRET
```

Functions are automatically scaled and billed per invocation.

---

## Component Selection Guide

```
What does this component do?
├── Serves HTTP to users/external systems?
│   ├── Static content (HTML/JS/CSS)? → static_sites
│   ├── Server-rendered or API? → services
│   └── Event-driven endpoints? → functions
├── Processes background tasks?
│   ├── Long-running consumer? → workers
│   └── One-time/scheduled task? → jobs
└── Internal service (no public access)?
    └── workers (with http_port for internal HTTP)
```

---

## Monorepo Configuration

For components from the same repository, use `source_dir`:

```yaml
services:
  - name: api
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /packages/api
    dockerfile_path: packages/api/Dockerfile
    http_port: 8080

  - name: admin
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /packages/admin
    http_port: 3000

static_sites:
  - name: web
    git:
      repo_clone_url: https://github.com/owner/repo.git
      branch: main
    source_dir: /packages/web
    build_command: npm run build
    output_dir: dist
```

**Key:** `source_dir` is relative to repository root, starts with `/`.
