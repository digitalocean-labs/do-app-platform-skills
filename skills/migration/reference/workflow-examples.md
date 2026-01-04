# Workflow Examples

Detailed end-to-end migration workflows for each source platform.

---

## Workflow 1: Heroku to App Platform

**User says**: "Migrate my Heroku app https://github.com/myorg/myapp to App Platform"

**AI Assistant Flow**:

### 1. Clone and Analyze

```bash
git clone https://github.com/myorg/myapp /tmp/migration-work
cd /tmp/migration-work
```

### 2. Detect Platform

```
Found: Procfile, app.json
Platform: Heroku
```

### 3. Analyze Procfile

```
web: gunicorn app:app
worker: celery -A tasks worker
release: python manage.py migrate
```

### 4. Analyze app.json for Add-ons

```json
{
  "addons": ["heroku-postgresql:hobby-dev", "heroku-redis:hobby-dev"]
}
```

### 5. Present Mapping Proposal

```
I've analyzed your Heroku app. Here's what I found:

COMPONENTS:
  web → services.web (gunicorn on port 8000)
  worker → workers.celery
  release → jobs.migrate (pre-deploy)

DATABASES:
  heroku-postgresql → databases.db (dev database)
  heroku-redis → databases.cache (Valkey - Redis is EOL on DO)

ENVIRONMENT VARIABLES:
- DATABASE_URL: Auto-bound from db
- REDIS_URL → VALKEY_URL: Need to update code references
- SECRET_KEY: Set in GitHub Secrets

CODE CHANGES NEEDED:
1. Update Redis connection to use VALKEY_URL
2. Remove Heroku-specific DATABASE_URL fix

Shall I proceed with this migration plan?
```

### 6. On Approval, Execute

```bash
git checkout -b migrate/test
# Make code changes
# Generate app spec
# Commit and push
```

### 7. Present Results

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

---

## Workflow 2: Docker Compose to App Platform

**User says**: "I have a docker-compose app, convert it to App Platform"

### User's docker-compose.yml

```yaml
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

### AI Assistant Analysis

```
I've analyzed your Docker Compose setup:

SERVICES DETECTED:
  api → services.api (port 3000, /api directory)
  worker → workers.worker (/worker directory)
  db (postgres:15) → databases.db (Managed Postgres)
  cache (redis:7) → databases.cache (Managed Valkey)

REQUIRES ATTENTION:
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

---

## Workflow 3: AWS ECS to App Platform (Complex)

**User says**: "Migrate my ECS service to App Platform"

### AI Assistant Analysis

```
I've analyzed your ECS Task Definition. This is a more complex migration:

MAPPABLE (3 of 6 items):
  Container: api → services.api
  Container: worker → workers.worker
  RDS PostgreSQL → databases.db (will need VPC or trusted sources)

REQUIRES YOUR DECISION (3 items):

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

## Migration Report Template

The skill generates `MIGRATION.md` after completing migration:

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

### Successfully Mapped

| Source | Target | Notes |
|--------|--------|-------|
| web (Procfile) | services.web | Port 3000, nodejs buildpack |
| worker (Procfile) | workers.background | Same code, no port |
| heroku-postgresql | databases.db | Dev database, migrate data separately |

### Requires Your Decision

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
