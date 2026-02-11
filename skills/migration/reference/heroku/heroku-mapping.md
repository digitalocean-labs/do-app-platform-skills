# Heroku to App Platform — Deep Mapping Reference

Comprehensive feature-by-feature mapping from Heroku to DigitalOcean App Platform.

## Table of Contents

1. [Component Type Mapping](#component-type-mapping)
2. [Build Configuration](#build-configuration)
3. [Environment Variables](#environment-variables)
4. [Instance Size Mapping](#instance-size-mapping)
5. [Region Mapping](#region-mapping)
6. [Networking and Routing](#networking-and-routing)
7. [Health Checks](#health-checks)
8. [Scaling](#scaling)
9. [Logging and Monitoring](#logging-and-monitoring)
10. [Gaps and Workarounds](#gaps-and-workarounds)

---

## Component Type Mapping

### Procfile Process → App Platform Component

| Heroku Process | App Platform Component | App Spec Key | Notes |
|---------------|----------------------|-------------|-------|
| `web` | Service | `services` | HTTP traffic, `http_port` required |
| `worker` | Worker | `workers` | No HTTP traffic, background processing |
| `release` | Pre-deploy Job | `jobs` (`kind: PRE_DEPLOY`) | Runs before each deploy, gates release |
| `clock` | Worker OR Cron Job | `workers` or `jobs` (`kind: CRON_TRIGGER`) | Worker if long-running, cron if periodic |
| Custom (e.g., `urgentworker`) | Worker | `workers` | Named worker, same concept |

### App Spec Component Template (from Procfile)

```yaml
# web: gunicorn app:app
services:
  - name: web
    run_command: gunicorn app:app
    http_port: 8000
    instance_size_slug: apps-s-1vcpu-1gb
    instance_count: 1
    health_check:
      http_path: /health

# worker: celery -A tasks worker
workers:
  - name: celery
    run_command: celery -A tasks worker
    instance_size_slug: apps-s-1vcpu-1gb
    instance_count: 1

# release: python manage.py migrate
jobs:
  - name: migrate
    kind: PRE_DEPLOY
    run_command: python manage.py migrate
    instance_size_slug: apps-s-1vcpu-0.5gb
    instance_count: 1
```

---

## Build Configuration

### Buildpack Apps (no Dockerfile, no heroku.yml)

```yaml
services:
  - name: web
    github:
      repo: myorg/myapp
      branch: main
      deploy_on_push: true
    # No dockerfile_path = auto-detect buildpack (CNB)
    build_command: npm run build    # If custom build needed
    run_command: node server.js     # From Procfile web entry
    http_port: 3000
```

### Docker Apps (heroku.yml present)

```yaml
services:
  - name: web
    github:
      repo: myorg/myapp
      branch: main
      deploy_on_push: true
    dockerfile_path: Dockerfile     # From heroku.yml build.docker.web
    run_command: gunicorn app:app   # From heroku.yml run.web (optional)
    http_port: 8000
```

### Build-Time Variables

Heroku `heroku.yml` → `build.config` sets build-time env vars. Map these:

```yaml
envs:
  - key: NODE_ENV
    scope: BUILD_TIME
    value: production
  - key: PYTHON_VERSION
    scope: BUILD_TIME
    value: "3.11"
```

---

## Environment Variables

### Config Var Translation

| Heroku Config Var | App Platform Treatment | Notes |
|------------------|----------------------|-------|
| `DATABASE_URL` | Bindable: `${db.DATABASE_URL}` | Auto-injected by managed DB |
| `REDIS_URL` | Bindable: `${valkey.DATABASE_URL}` | Rename to `VALKEY_URL` in code OR keep `REDIS_URL` key with Valkey binding |
| `PORT` | Not needed | App Platform sets `http_port` in spec |
| `SECRET_KEY`, `API_KEY`, etc. | `type: SECRET` | User sets via GitHub Secrets |
| `RAILS_ENV`, `NODE_ENV`, etc. | `value: production` | Direct value in spec |
| `HEROKU_APP_NAME` | Not available | Remove or use `APP_DOMAIN` if needed |
| `HEROKU_SLUG_COMMIT` | Not available | Use `COMMIT_HASH` from GitHub Actions |
| `HEROKU_DYNO_ID` | Not available | Remove |

### Env Var Scope Mapping

| Heroku Scope | App Platform Scope | Notes |
|-------------|-------------------|-------|
| Config vars (all dynos) | `scope: RUN_AND_BUILD_TIME` | Default scope |
| Build-time only (heroku.yml) | `scope: BUILD_TIME` | Build only |
| Runtime only | `scope: RUN_TIME` | Runtime only |

### App Spec Environment Block

```yaml
envs:
  # Bindable variable from managed database
  - key: DATABASE_URL
    scope: RUN_TIME
    value: ${db.DATABASE_URL}

  # Bindable variable from managed Valkey (was Redis on Heroku)
  - key: REDIS_URL
    scope: RUN_TIME
    value: ${valkey.DATABASE_URL}

  # Secret (user sets in GitHub Secrets or App Platform console)
  - key: SECRET_KEY
    scope: RUN_TIME
    type: SECRET

  # Plain value
  - key: NODE_ENV
    scope: RUN_AND_BUILD_TIME
    value: production
```

### DATABASE_URL Format

Heroku uses `postgres://user:pass@host:port/db`. Some frameworks (notably Django with `dj-database-url`, SQLAlchemy) accept this. Others require `postgresql://`.

App Platform bindable variables use the standard `postgresql://` format. If the Heroku app has a URL-fixing hack like:

```python
# Common Heroku fix — may no longer be needed
DATABASE_URL = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://', 1)
```

Flag this to the user: "This `postgres://` → `postgresql://` fix may no longer be needed on App Platform, since bindable variables use the standard format. Verify and remove if redundant."

---

## Instance Size Mapping

| Heroku Dyno Type | RAM | App Platform Slug | RAM |
|-----------------|-----|-------------------|-----|
| eco / basic | 512 MB | `apps-s-1vcpu-0.5gb` | 512 MB |
| standard-1x | 512 MB | `apps-s-1vcpu-1gb` | 1 GB |
| standard-2x | 1 GB | `apps-d-1vcpu-2gb` | 2 GB |
| performance-m | 2.5 GB | `apps-d-2vcpu-4gb` | 4 GB |
| performance-l | 14 GB | `apps-d-4vcpu-8gb` | 8 GB |

**Note**: Heroku eco/basic dynos sleep after 30 min of inactivity. App Platform `apps-s-*` (shared CPU) instances do NOT sleep but are resource-shared. For consistent availability, `apps-s-1vcpu-1gb` is the recommended minimum.

Reference: `shared/instance-sizes.yaml` for full list.

---

## Region Mapping

| Heroku Region | App Platform Region | Slug |
|--------------|--------------------|----|
| `us` (Virginia) | New York 1 | `nyc` |
| `eu` (Dublin/Frankfurt) | Frankfurt 1 | `fra` |
| `sydney` (Common Runtime) | Sydney 1 | `syd` |

App Platform supports additional regions. See `shared/regions.yaml` for full list.

---

## Networking and Routing

| Heroku Feature | App Platform Equivalent | Notes |
|---------------|------------------------|-------|
| HTTP routing (random) | HTTP routing (round-robin) | Similar, not identical |
| `heroku.com` domain | `ondigitalocean.app` domain | Free subdomain |
| Custom domains | Custom domains | Configure via app spec or console |
| SSL (auto) | SSL (auto via Let's Encrypt) | Direct equivalent |
| Internal routing (Private Spaces) | Internal networking (VPC) | Components communicate by service name |
| WebSockets | WebSockets supported | No sticky sessions |
| Sticky sessions | **NOT AVAILABLE** | Redesign if session affinity required |
| Request timeout (30s) | Request timeout (configurable) | App Platform more flexible |

### Internal Communication

Heroku Private Spaces use internal DNS. App Platform uses internal service names:

```
# Heroku (Private Spaces)
https://myworker.herokuapp.com  (internal routing)

# App Platform
http://worker:8080  (internal service name, private port)
```

In App Spec, use `internal_ports` for non-public service-to-service communication.

---

## Health Checks

| Heroku | App Platform | Notes |
|--------|-------------|-------|
| No built-in health check endpoint | `health_check.http_path` | Recommended: add `/health` endpoint |
| Boot timeout (60s for web) | Configurable health check | `initial_delay_seconds`, `period_seconds` |

### Recommended App Spec Health Check

```yaml
health_check:
  http_path: /health
  initial_delay_seconds: 10
  period_seconds: 10
  timeout_seconds: 5
  success_threshold: 1
  failure_threshold: 3
```

If the Heroku app has no health endpoint, recommend adding one as part of migration.

---

## Scaling

| Heroku | App Platform | Notes |
|--------|-------------|-------|
| `heroku ps:scale web=3` | `instance_count: 3` in spec | Spec-driven |
| Autoscaling (Performance dynos) | Autoscaling in spec | Min/max instances |
| Manual scaling via CLI | Update spec + redeploy | Or via console UI |

### Autoscaling Translation

```yaml
# Heroku: autoscaling on Performance dynos
# App Platform equivalent:
services:
  - name: web
    instance_count: 2
    autoscaling:
      min_instance_count: 2
      max_instance_count: 10
      metrics:
        cpu:
          percent: 70
```

---

## Logging and Monitoring

| Heroku | App Platform | Notes |
|--------|-------------|-------|
| `heroku logs --tail` | `doctl apps logs <id> --follow` | Similar CLI experience |
| Log drains | Log forwarding | Configure in App Platform settings |
| Papertrail add-on | External logging (keep) | Update log drain URL |
| Heroku Metrics | App Platform Insights | Different metrics dashboard |
| New Relic add-on | External APM (keep) | Update env vars |

---

## Gaps and Workarounds

Features that exist on Heroku but NOT on App Platform:

| Heroku Feature | Status on App Platform | Workaround |
|---------------|----------------------|-----------|
| Heroku Scheduler (UI) | No UI scheduler | Define `jobs` with `kind: CRON_TRIGGER` in app spec |
| Review Apps (auto per PR) | Preview environments | Available via GitHub integration, different configuration |
| Pipeline promotion (instant) | No slug promotion | GitHub Actions: build once, deploy to environments |
| `heroku run bash` (SSH-like) | `doctl apps console` | Interactive, similar concept |
| Maintenance mode | No toggle | Deploy a maintenance page or use DNS switching |
| Heroku Postgres forking | No fork feature | Create new DB + restore from backup |
| Preboot (zero-downtime) | Zero-downtime by default | App Platform handles this automatically |
| Private Spaces (VPC) | VPC networking | App Platform supports VPC, different configuration |
