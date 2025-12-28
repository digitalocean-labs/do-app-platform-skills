---
name: app-platform-migration
description: Migrate existing applications from other platforms (Heroku, AWS, Render, Railway, Fly.io, Docker Compose) to DigitalOcean App Platform with code refactoring, service mapping, and honest capability assessment
version: 1.0.0
author: Bikram Gupta
triggers:
  - "migrate"
  - "convert"
  - "move from Heroku"
  - "move from AWS"
  - "move from Render"
  - "move from Railway"
  - "move from Fly"
  - "existing app"
  - "port my app"
  - "migration"
  - "heroku to digitalocean"
  - "aws to digitalocean"
dependencies:
  required:
    - git
    - gh (GitHub CLI, authenticated)
    - doctl (authenticated)
  optional:
    - python 3.10+ (via uv)
    - node 20+ (via nvm)
  skills:
    - deployment (deploys the generated app spec)
    - postgres (for database migration guidance)
    - devcontainers (for local dev post-migration)
    - troubleshooting (when migrations fail)
artifacts:
  produced:
    - .do/app.yaml (App Platform specification)
    - .do/deploy.template.yaml (Deploy to DO button)
    - MIGRATION.md (migration checklist and status)
    - .env.example (environment variable template)
    - .env.migration (mapped environment variables)
  consumed:
    - Procfile (Heroku)
    - app.json (Heroku)
    - docker-compose.yml
    - Dockerfile
    - render.yaml (Render)
    - fly.toml (Fly.io)
    - railway.json (Railway)
    - ECS Task Definition (AWS)
    - apprunner.yaml (AWS)
---

# App Platform Migration Skill

## Philosophy

**This skill is an honest partner, not a magic wand.** Migration between platforms involves many permutations—some map cleanly, others require human decisions. This skill:

1. **Analyzes thoroughly** before proposing any changes
2. **Maps what it can** with confidence
3. **Acknowledges gaps** clearly and specifically
4. **Asks before proceeding** when uncertain
5. **Never guesses** or ignores incompatibilities to finish faster

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MIGRATION PHILOSOPHY                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ✅ "I've mapped 4 of 6 services. Here's what I found for the other 2:" │
│     - CloudFront CDN: App Platform doesn't have CDN. Options: [...]     │
│     - Secrets Manager: Recommend GitHub Secrets. Need your input.       │
│                                                                          │
│  ❌ "Migration complete! Your app is ready to deploy."                  │
│     (When actually 2 services were silently skipped)                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## What This Skill Does

**Input**: Existing application running on another platform (or Docker Compose)

**Output**:
1. **Refactored code** ready for App Platform (in a new branch)
2. **App spec** (`.do/app.yaml`) for deployment
3. **Migration checklist** with status of each component
4. **Environment mapping** showing old → new variable names

**What migration means here:**
- Code changes to remove platform-specific dependencies
- Configuration conversion to App Platform format
- Service mapping to DO equivalents
- NOT: Running the app, data migration, DNS cutover (those are separate steps)

---

## Supported Source Platforms

| Platform | Config Files | Support Level |
|----------|--------------|---------------|
| **Heroku** | `Procfile`, `app.json` | ✅ Full |
| **Docker Compose** | `docker-compose.yml` | ✅ Full |
| **Render** | `render.yaml` | ✅ Full |
| **Railway** | `railway.json`, `railway.toml` | ✅ Full |
| **Fly.io** | `fly.toml` | ✅ Full |
| **AWS ECS** | Task Definition JSON | ⚠️ Partial (needs review) |
| **AWS App Runner** | `apprunner.yaml` | ⚠️ Partial |
| **AWS Elastic Beanstalk** | `Dockerrun.aws.json` | ⚠️ Partial |
| **Generic Docker** | `Dockerfile` only | ✅ Full |

---

## The Migration Process

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MIGRATION WORKFLOW                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 1: DISCOVERY                                                      │
│  ─────────────────                                                       │
│  • Clone/access repository                                               │
│  • Detect source platform                                                │
│  • Analyze architecture                                                  │
│  • Inventory all services and dependencies                               │
│                                                                          │
│  Phase 2: MAPPING                                                        │
│  ────────────────                                                        │
│  • Map services → App Platform components                                │
│  • Map databases → Managed databases                                     │
│  • Map storage → Spaces                                                  │
│  • Map secrets → GitHub Secrets pattern                                  │
│  • Identify unmappable items → REPORT TO USER                           │
│                                                                          │
│  Phase 3: REFACTORING                                                    │
│  ───────────────────                                                     │
│  • Create target branch(es)                                              │
│  • Update environment variable references                                │
│  • Remove platform-specific code                                         │
│  • Update Dockerfile if needed                                           │
│  • Generate app spec                                                     │
│                                                                          │
│  Phase 4: VALIDATION                                                     │
│  ──────────────────                                                      │
│  • Validate app spec: doctl apps spec validate                           │
│  • Review changes with user                                              │
│  • Generate migration checklist                                          │
│                                                                          │
│  Phase 5: HANDOFF                                                        │
│  ────────────────                                                        │
│  • Push branches to repo                                                 │
│  • Provide checklist for manual steps                                    │
│  • Suggest deployment skill for next steps                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Basic Migration

```bash
# User provides repo URL
"Migrate this app to App Platform: https://github.com/myorg/myapp"

# AI assistant will:
# 1. Clone and analyze
# 2. Detect platform (Heroku, Compose, etc.)
# 3. Present mapping proposal
# 4. Ask for approval before making changes
# 5. Create migration branch with refactored code + app spec
```

### With Branch Specification

```bash
# Specify output branches
"Migrate my Heroku app to App Platform. 
 Put testing config in branch 'migrate/test' 
 and production config in branch 'migrate/prod'"
```

### From Local Directory

```bash
# If user has repo cloned locally
"I have a Heroku app in /path/to/myapp - migrate it to App Platform"
```

---

## Phase 1: Discovery

### Automatic Platform Detection

The skill detects the source platform by looking for these files:

```python
PLATFORM_INDICATORS = {
    'heroku': ['Procfile', 'app.json', 'heroku.yml'],
    'docker_compose': ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml'],
    'render': ['render.yaml', 'render.yml'],
    'railway': ['railway.json', 'railway.toml'],
    'fly': ['fly.toml'],
    'aws_ecs': ['**/task-definition.json', '**/ecs-task-definition.json'],
    'aws_apprunner': ['apprunner.yaml', 'apprunner.yml'],
    'aws_beanstalk': ['Dockerrun.aws.json', '.elasticbeanstalk/'],
    'generic_docker': ['Dockerfile'],  # Fallback
}
```

### Architecture Analysis

The skill analyzes the repository to understand:

```yaml
analysis_output:
  architecture_type: monolith | microservices | full-stack | static-site
  runtime: nodejs | python | go | ruby | php | java | rust | dotnet
  build_method: dockerfile | docker-compose | buildpack
  
  components:
    - name: web
      type: service
      port: 3000
      has_dockerfile: true
      source_dir: /
      
    - name: worker
      type: worker
      source_dir: /worker
      
  dependencies:
    databases:
      - type: postgres
        source: "heroku-postgresql" | "docker: postgres:15" | "RDS"
        
    caches:
      - type: redis
        source: "heroku-redis" | "docker: redis:7"
        
    storage:
      - type: s3
        source: "AWS S3" | "Heroku:cloudinary"
        
    queues:
      - type: rabbitmq
        source: "docker: rabbitmq"
```

---

## Phase 2: Mapping

### Service Mapping Table

The skill maps source platform concepts to App Platform equivalents:

#### Heroku → App Platform

| Heroku | App Platform | Notes |
|--------|--------------|-------|
| `web` process | `services` component | Direct mapping |
| `worker` process | `workers` component | Direct mapping |
| `release` phase | `jobs` (pre-deploy) | `kind: PRE_DEPLOY` |
| `scheduler` (hourly/daily) | `jobs` (cron) | `kind: CRON_TRIGGER` |
| `heroku-postgresql` | Managed Postgres | Dev: `production: false`, Managed: `production: true` |
| `heroku-redis` | Managed Valkey | Redis EOL on DO, use Valkey |
| `papertrail` | Log forwarding | Configure in App Platform |
| `sendgrid` | External (keep) | Just update env vars |
| `cloudamqp` | External OR migrate | No direct equivalent |
| `memcachier` | Use Valkey | Valkey supports memcached protocol |
| Config Vars | Environment variables | Use GitHub Secrets pattern |

#### Docker Compose → App Platform

| Docker Compose | App Platform | Notes |
|----------------|--------------|-------|
| `services.<name>.ports` | `services` with `http_port` | First port becomes http_port |
| `services.<name>` (no ports) | `workers` | Background processes |
| `services.postgres` | Managed Postgres | Extract version from image |
| `services.redis` | Managed Valkey | |
| `services.mongodb` | Managed MongoDB | |
| `volumes` (named) | ⚠️ **Spaces or ephemeral** | No persistent volumes yet |
| `volumes` (bind mounts) | ⚠️ **Not supported** | Dev-only pattern |
| `depends_on` | Health checks | Implicit ordering |
| `networks` | Internal networking | Automatic within app |
| `build.context` | `source_dir` | |
| `environment` | `envs` array | |

#### Render → App Platform

| Render | App Platform | Notes |
|--------|--------------|-------|
| `services[type=web]` | `services` | Direct mapping |
| `services[type=worker]` | `workers` | Direct mapping |
| `services[type=cron]` | `jobs` | `kind: CRON_TRIGGER` |
| `services[type=static]` | `static_sites` | Direct mapping |
| `databases` | Managed databases | |
| `envVars` | `envs` | |
| `autoDeploy` | `deploy_on_push` | |
| `healthCheckPath` | `health_check.http_path` | |
| `region` | `region` | Map to closest DO region |

#### AWS ECS → App Platform

| AWS ECS | App Platform | Notes |
|---------|--------------|-------|
| Container definition | Component | One container = one component |
| `portMappings` | `http_port` | First port mapping |
| `environment` | `envs` | |
| `secrets` (SSM) | ⚠️ **GitHub Secrets** | Different pattern |
| `secrets` (Secrets Manager) | ⚠️ **GitHub Secrets** | Different pattern |
| ALB target groups | Built-in routing | Automatic |
| Service Discovery | Internal networking | Use service names |
| RDS | Managed Postgres/MySQL | May need VPC |
| ElastiCache | Managed Valkey | |
| S3 | Spaces | Compatible API |
| CloudWatch Logs | Built-in + forwarding | |
| IAM roles | ⚠️ **Not applicable** | Different auth model |

### Unmappable Items

These require user decisions:

| Source | Issue | Options |
|--------|-------|---------|
| **CloudFront CDN** | No DO CDN | 1. Use external CDN (Cloudflare) 2. Skip (App Platform has edge caching) |
| **AWS Secrets Manager** | Different model | GitHub Secrets (recommended) or external vault |
| **Persistent volumes** | Not supported (until Q1 2026) | Spaces for files, managed DB for data |
| **Custom domains with complex routing** | Limited routing | May need external load balancer |
| **WebSockets with sticky sessions** | Limited | Works for basic WS, no sticky |
| **ARM containers** | AMD64 only | Rebuild for AMD64 |
| **Privileged containers** | gVisor sandbox | May not be compatible |

---

## Phase 3: Refactoring

### Code Changes

The skill may need to modify code for these patterns:

#### 1. Environment Variable Updates

```python
# Before (Heroku-specific)
DATABASE_URL = os.environ.get('DATABASE_URL')
# Heroku uses postgres:// which SQLAlchemy doesn't like
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# After (App Platform)
DATABASE_URL = os.environ.get('DATABASE_URL')
# App Platform uses postgresql:// already - no modification needed
```

#### 2. Port Binding

```javascript
// Before (Heroku)
const PORT = process.env.PORT || 3000;

// After (App Platform) - same pattern works!
const PORT = process.env.PORT || 8080;  // Default 8080 is more common
```

#### 3. AWS SDK Removal/Replacement

```python
# Before (AWS Secrets Manager)
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='myapp/prod/db')

# After (App Platform) - use environment variables directly
import os
DATABASE_URL = os.environ['DATABASE_URL']  # Set via GitHub Secrets
```

#### 4. S3 to Spaces Migration

```python
# Before (AWS S3)
import boto3
s3 = boto3.client('s3',
    region_name='us-east-1',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
)

# After (Spaces - S3 compatible)
import boto3
s3 = boto3.client('s3',
    endpoint_url=os.environ['SPACES_ENDPOINT'],  # https://nyc3.digitaloceanspaces.com
    region_name=os.environ['SPACES_REGION'],      # nyc3
    aws_access_key_id=os.environ['SPACES_KEY'],
    aws_secret_access_key=os.environ['SPACES_SECRET']
)
```

### Branch Strategy

The skill creates branches for different environments:

```bash
# User specifies:
# - test_branch: "migrate/test"
# - prod_branch: "migrate/prod"

# Skill creates:
# migrate/test
#   └── .do/app.yaml (dev database, smaller instances)
#   └── .do/deploy.template.yaml
#   └── MIGRATION.md
#   └── (refactored code)

# migrate/prod  
#   └── .do/app.yaml (managed database, production instances)
#   └── .do/deploy.template.yaml
#   └── MIGRATION.md
#   └── (refactored code)
```

---

## Phase 4: Validation

### App Spec Validation

```bash
# Always validate generated spec
doctl apps spec validate .do/app.yaml
```

### Migration Report

The skill generates `MIGRATION.md`:

```markdown
# Migration Report: myapp (Heroku → App Platform)

## Summary

| Metric | Value |
|--------|-------|
| Source Platform | Heroku |
| Components Detected | 4 |
| Successfully Mapped | 3 |
| Requires Decision | 1 |
| Migration Branch | migrate/test |

## Component Mapping

### ✅ Successfully Mapped

| Source | Target | Notes |
|--------|--------|-------|
| web (Procfile) | services.web | Port 3000, nodejs buildpack |
| worker (Procfile) | workers.background | Same code, no port |
| heroku-postgresql | databases.db | Dev database, migrate data separately |

### ⚠️ Requires Your Decision

| Source | Issue | Options |
|--------|-------|---------|
| cloudinary | No direct equivalent | **Option A**: Keep Cloudinary (update env vars only) **Option B**: Migrate to Spaces |

## Environment Variables

| Original Name | New Name | Source | Action Required |
|---------------|----------|--------|-----------------|
| DATABASE_URL | DATABASE_URL | heroku-postgresql → db | Auto-bound: `${db.DATABASE_URL}` |
| REDIS_URL | VALKEY_URL | heroku-redis → valkey | Need to create Valkey cluster |
| CLOUDINARY_URL | CLOUDINARY_URL | External | Keep same, set in GitHub Secrets |
| SECRET_KEY | SECRET_KEY | Config Var | Set in GitHub Secrets |

## Code Changes Made

- [ ] Updated `config/database.py`: Removed postgres:// URL fix (line 23)
- [ ] Updated `Dockerfile`: Changed base image to python:3.11-slim
- [ ] Created `.do/app.yaml`
- [ ] Created `.do/deploy.template.yaml`

## Next Steps

1. **Review changes**: `git diff main..migrate/test`
2. **Set GitHub Secrets**: 
   ```bash
   gh secret set SECRET_KEY --env staging
   gh secret set CLOUDINARY_URL --env staging
   ```
3. **Create Valkey cluster** (if using Redis):
   ```bash
   doctl databases create myapp-valkey --engine valkey --region nyc --size db-s-1vcpu-1gb
   ```
4. **Deploy**: Use the **deployment skill** to set up GitHub Actions
5. **Migrate data**: See Data Migration section below

## Data Migration

### PostgreSQL

```bash
# 1. Export from Heroku
heroku pg:backups:capture --app myapp
heroku pg:backups:download --app myapp

# 2. Create DO database (if using managed)
doctl databases create myapp-db --engine pg --region nyc --size db-s-1vcpu-1gb

# 3. Get connection string
doctl databases connection myapp-db --format URI

# 4. Restore
pg_restore -d "postgresql://..." latest.dump
```

### Files (if using Spaces)

```bash
# Sync from Cloudinary/S3 to Spaces
aws s3 sync s3://old-bucket s3://new-bucket \
  --endpoint-url https://nyc3.digitaloceanspaces.com
```
```

---

## Workflow Examples

### Workflow 1: Heroku to App Platform

**User says**: "Migrate my Heroku app https://github.com/myorg/myapp to App Platform"

**AI Assistant Flow**:

1. **Clone and analyze**:
   ```bash
   git clone https://github.com/myorg/myapp /tmp/migration-work
   cd /tmp/migration-work
   ```

2. **Detect platform**:
   ```
   Found: Procfile, app.json
   Platform: Heroku
   ```

3. **Analyze Procfile**:
   ```
   web: gunicorn app:app
   worker: celery -A tasks worker
   release: python manage.py migrate
   ```

4. **Analyze app.json for add-ons**:
   ```json
   {
     "addons": ["heroku-postgresql:hobby-dev", "heroku-redis:hobby-dev"]
   }
   ```

5. **Present mapping proposal**:
   ```
   I've analyzed your Heroku app. Here's what I found:

   COMPONENTS:
   ✅ web → services.web (gunicorn on port 8000)
   ✅ worker → workers.celery
   ✅ release → jobs.migrate (pre-deploy)

   DATABASES:
   ✅ heroku-postgresql → databases.db (dev database)
   ✅ heroku-redis → databases.cache (Valkey - Redis is EOL on DO)

   ENVIRONMENT VARIABLES:
   - DATABASE_URL: Auto-bound from db
   - REDIS_URL → VALKEY_URL: Need to update code references
   - SECRET_KEY: Set in GitHub Secrets

   CODE CHANGES NEEDED:
   1. Update Redis connection to use VALKEY_URL
   2. Remove Heroku-specific DATABASE_URL fix

   Shall I proceed with this migration plan?
   ```

6. **On approval, execute**:
   ```bash
   git checkout -b migrate/test
   # Make code changes
   # Generate app spec
   # Commit and push
   ```

7. **Present results**:
   ```
   Migration branch created: migrate/test
   
   Files created:
   - .do/app.yaml
   - .do/deploy.template.yaml
   - MIGRATION.md
   - .env.example

   Code changes:
   - config/celery.py: Updated VALKEY_URL reference
   
   Next steps:
   1. Review: git diff main..migrate/test
   2. Set secrets: gh secret set SECRET_KEY --env staging
   3. Deploy: Use deployment skill
   ```

### Workflow 2: Docker Compose to App Platform

**User says**: "I have a docker-compose app, convert it to App Platform"

```yaml
# User's docker-compose.yml
version: '3.8'
services:
  api:
    build: ./api
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgres://postgres:password@db:5432/app
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache

  worker:
    build: ./worker
    environment:
      - DATABASE_URL=postgres://postgres:password@db:5432/app
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache

  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=app
      - POSTGRES_PASSWORD=password

  cache:
    image: redis:7

volumes:
  pgdata:
```

**AI Assistant Analysis**:

```
I've analyzed your Docker Compose setup:

SERVICES DETECTED:
✅ api → services.api (port 3000, /api directory)
✅ worker → workers.worker (/worker directory)
✅ db (postgres:15) → databases.db (Managed Postgres)
✅ cache (redis:7) → databases.cache (Managed Valkey)

⚠️ REQUIRES ATTENTION:
- Volume 'pgdata': App Platform doesn't support persistent volumes.
  For Postgres, this is fine - Managed DB handles persistence.
  
- Hardcoded DATABASE_URL: Currently points to 'db:5432'. 
  Will be replaced with ${db.DATABASE_URL} binding.

CODE CHANGES NEEDED:
1. Update any hardcoded connection strings to use environment variables
2. Ensure apps bind to 0.0.0.0, not localhost

Generated app spec will use:
- Dev database (production: false) for testing
- Instance size: apps-s-1vcpu-1gb

Shall I proceed?
```

### Workflow 3: AWS ECS to App Platform (Complex)

**User says**: "Migrate my ECS service to App Platform"

**AI Assistant Analysis**:

```
I've analyzed your ECS Task Definition. This is a more complex migration:

MAPPABLE (3 of 6 items):
✅ Container: api → services.api
✅ Container: worker → workers.worker  
✅ RDS PostgreSQL → databases.db (will need VPC or trusted sources)

⚠️ REQUIRES YOUR DECISION (3 items):

1. AWS Secrets Manager
   - You're using: myapp/prod/database, myapp/prod/api-key
   - App Platform doesn't have Secrets Manager equivalent
   
   OPTIONS:
   A) GitHub Secrets (RECOMMENDED)
      - Secrets stored in GitHub, injected via Actions
      - You manually set: gh secret set DATABASE_URL --env production
   
   B) External secrets manager (HashiCorp Vault, etc.)
      - App fetches secrets at runtime
      - More complexity, but centralized

   Which approach would you prefer?

2. CloudFront CDN
   - You're using CloudFront for static assets
   - App Platform doesn't include CDN
   
   OPTIONS:
   A) Use external CDN (Cloudflare - free tier available)
   B) Skip CDN (App Platform has some edge caching)
   C) Keep CloudFront pointing to new App Platform URL
   
   Which approach would you prefer?

3. IAM Role for S3 Access
   - Your containers use IAM roles for S3 access
   - App Platform uses Spaces with API keys
   
   OPTIONS:
   A) Migrate to Spaces (S3-compatible, need code changes)
   B) Keep S3, use access keys instead of IAM role
   
   Which approach would you prefer?

Once you answer these questions, I can proceed with the migration.
```

---

## App Spec Generation

### Testing Environment Spec

```yaml
# .do/app.yaml (testing)
spec:
  name: myapp-test
  region: nyc
  
  services:
    - name: web
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/test
      dockerfile_path: Dockerfile
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

  workers:
    - name: celery
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/test
      dockerfile_path: Dockerfile
      instance_size_slug: apps-s-1vcpu-0.5gb
      instance_count: 1
      run_command: celery -A tasks worker
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}
        - key: VALKEY_URL
          scope: RUN_TIME
          value: ${cache.DATABASE_URL}

  jobs:
    - name: migrate
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/test
      dockerfile_path: Dockerfile
      kind: PRE_DEPLOY
      instance_size_slug: apps-s-1vcpu-0.5gb
      run_command: python manage.py migrate
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}

  databases:
    - name: db
      engine: PG
      production: false  # Dev database for testing
      
    - name: cache
      engine: VALKEY
      production: false
```

### Production Environment Spec

```yaml
# .do/app.yaml (production)
spec:
  name: myapp-prod
  region: nyc
  
  services:
    - name: web
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/prod
      dockerfile_path: Dockerfile
      http_port: 8000
      instance_size_slug: apps-d-1vcpu-2gb  # Dedicated CPU
      instance_count: 2  # Multiple instances
      autoscaling:
        min_instance_count: 2
        max_instance_count: 5
        metrics:
          - name: cpu_utilization
            threshold: 80
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

  workers:
    - name: celery
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/prod
      dockerfile_path: Dockerfile
      instance_size_slug: apps-d-1vcpu-1gb
      instance_count: 2
      run_command: celery -A tasks worker
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}
        - key: VALKEY_URL
          scope: RUN_TIME
          value: ${cache.DATABASE_URL}

  jobs:
    - name: migrate
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/prod
      dockerfile_path: Dockerfile
      kind: PRE_DEPLOY
      instance_size_slug: apps-s-1vcpu-1gb
      run_command: python manage.py migrate
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}

  databases:
    - name: db
      engine: PG
      production: true  # Managed database
      cluster_name: myapp-prod-db  # Must exist

    - name: cache
      engine: VALKEY
      production: true
      cluster_name: myapp-prod-cache  # Must exist
```

---

## Known Limitations

### What This Skill Cannot Migrate

| Feature | Why | Alternative |
|---------|-----|-------------|
| Persistent volumes | Not supported until Q1 2026 | Use Spaces for files, managed DB for data |
| ARM containers | AMD64 only | Rebuild for AMD64 |
| Custom network policies | Simplified networking | Use internal service names |
| Multiple custom domains per service | Limited | Use external load balancer |
| Complex ALB routing rules | Basic routing only | May need ingress controller |
| Serverless functions (Lambda) | Different model | Use App Platform Functions or keep Lambda |
| Step Functions / workflows | No equivalent | Use external orchestration |
| Multi-region deployment | Single region per app | Deploy multiple apps |

### Platform-Specific Gotchas

#### Heroku
- `DATABASE_URL` format: Heroku uses `postgres://`, App Platform uses `postgresql://`
- Dyno types don't map 1:1 to instance sizes
- Review dynos become preview environments (different workflow)

#### AWS
- IAM roles don't exist - use API keys or GitHub Secrets
- VPC peering may be needed for RDS access
- CloudWatch metrics → App Platform Insights (different metrics)

#### Docker Compose
- `depends_on` doesn't guarantee startup order - use health checks
- Host networking not available
- Volume mounts don't persist

---

## Integration with Other Skills

### → deployment skill
After migration, use deployment skill to set up CI/CD:
```bash
# Migration creates branches and app spec
# Deployment skill creates GitHub Actions workflow
```

### → postgres skill
For complex database setup:
```bash
# Migration identifies database needs
# Postgres skill handles:
# - Schema creation
# - User permissions
# - Connection pooling setup
```

### → devcontainers skill
For local development post-migration:
```bash
# After migration, use devcontainers to:
# - Create local dev environment matching App Platform
# - Set up backing services locally
```

### → troubleshooting skill
When migration issues occur:
```bash
# If deployed app has issues:
# - Use troubleshooting skill to debug
# - Check logs, connect to containers
```

---

## Command Reference

### Analysis Commands

```bash
# Clone repository
git clone <repo-url> /tmp/migration-work

# Check for platform indicators
ls -la Procfile app.json docker-compose.yml render.yaml fly.toml

# Analyze Dockerfile
cat Dockerfile | grep -E "^(FROM|EXPOSE|CMD|ENTRYPOINT)"

# Check environment files
cat .env.example
```

### Git Operations

```bash
# Create migration branch
git checkout -b migrate/test

# After changes
git add .
git commit -m "Migration to DigitalOcean App Platform

- Added .do/app.yaml
- Added .do/deploy.template.yaml
- Updated environment variable references
- Created MIGRATION.md checklist"

git push origin migrate/test
```

### Validation

```bash
# Validate app spec
doctl apps spec validate .do/app.yaml

# Lint Dockerfile
docker build --check .

# Test locally (if docker-compose exists)
docker-compose -f docker-compose.yml build
```

---

## Opinionated Defaults

| Decision | Default | Rationale |
|----------|---------|-----------|
| Target branch naming | `migrate/test`, `migrate/prod` | Clear purpose |
| Test environment | Dev databases, small instances | Cost-effective testing |
| Production environment | Managed databases, dedicated CPU | Reliability |
| Secrets handling | GitHub Secrets | Security, AI never sees values |
| Health check path | `/health` or `/healthz` | Industry standard |
| Instance size (test) | `apps-s-1vcpu-1gb` | Good baseline |
| Instance size (prod) | `apps-d-1vcpu-2gb` | Dedicated CPU |
| Redis replacement | Valkey | Redis EOL on DO |
| deploy_on_push | `true` for test, `false` for prod | GitOps with control |

---

## Troubleshooting Migration

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| App spec validation fails | Invalid YAML | Check indentation, use `doctl apps spec validate` |
| Database connection fails | Wrong URL format | Ensure `${db.DATABASE_URL}` binding |
| Build fails | Missing dependencies | Check Dockerfile, ensure all build deps |
| Port binding fails | Wrong PORT handling | Bind to `$PORT` or `0.0.0.0:8080` |
| Health check fails | Wrong path | Verify `/health` endpoint exists |
| Env vars empty | Scope wrong | Use `scope: RUN_TIME` for runtime vars |

### Debug Steps

```bash
# 1. Validate spec
doctl apps spec validate .do/app.yaml

# 2. Try local build
docker build -t test .

# 3. Test locally
docker run -p 8080:8080 -e PORT=8080 test

# 4. Check logs after deploy
doctl apps logs <app-id> --type build
doctl apps logs <app-id> --type deploy
doctl apps logs <app-id> --type run
```

---

## Documentation Links

- [App Spec Reference](https://docs.digitalocean.com/products/app-platform/reference/app-spec/)
- [Heroku Migration Guide](https://docs.digitalocean.com/products/app-platform/how-to/migrate-from-heroku/)
- [Deploy to DO Button](https://docs.digitalocean.com/products/app-platform/how-to/add-deploy-do-button/)
- [Environment Variables](https://docs.digitalocean.com/products/app-platform/how-to/use-environment-variables/)
- [Managed Databases](https://docs.digitalocean.com/products/databases/)
- [Spaces](https://docs.digitalocean.com/products/spaces/)
