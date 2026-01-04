# Environment Variable Mapping Reference

This document provides mapping patterns for environment variables across platforms.

## Heroku → App Platform

### Database Variables

| Heroku Variable | App Platform Binding | Notes |
|-----------------|---------------------|-------|
| `DATABASE_URL` | `${db.DATABASE_URL}` | Auto-bound when database attached |
| `REDIS_URL` | `${cache.DATABASE_URL}` | Use Valkey instead of Redis |
| `HEROKU_POSTGRESQL_*_URL` | `${db.DATABASE_URL}` | Heroku adds color-coded URLs |

### Common Variables

| Heroku Pattern | App Platform Pattern | Notes |
|----------------|---------------------|-------|
| `PORT` | `$PORT` | Auto-set by platform |
| `SECRET_KEY_BASE` | `SECRET_KEY` | Set in GitHub Secrets |
| `RAILS_ENV` | `RAILS_ENV` | Set `production` |
| `NODE_ENV` | `NODE_ENV` | Set `production` |
| `WEB_CONCURRENCY` | `WEB_CONCURRENCY` | Adjust for instance size |

### Add-on Variables

| Heroku Add-on | Variables | App Platform Equivalent |
|---------------|-----------|------------------------|
| Papertrail | `PAPERTRAIL_API_TOKEN` | Log forwarding (built-in) |
| SendGrid | `SENDGRID_API_KEY` | Keep external, set in Secrets |
| Cloudinary | `CLOUDINARY_URL` | Keep external OR use Spaces |
| New Relic | `NEW_RELIC_*` | Keep external |

## Docker Compose → App Platform

### Service Discovery

| Compose Pattern | App Platform Pattern |
|-----------------|---------------------|
| `http://api:3000` | `http://api:3000` (internal) OR `${APP_URL}` |
| `postgres://db:5432` | `${db.DATABASE_URL}` |
| `redis://cache:6379` | `${cache.DATABASE_URL}` |

### Volume-based Config

| Compose Pattern | App Platform Equivalent |
|-----------------|------------------------|
| `./config:/app/config` | Include in image OR use env vars |
| `./secrets:/run/secrets` | Use `type: SECRET` env vars |
| `data:/var/lib/data` | Use managed database or Spaces |

## AWS ECS → App Platform

### Secrets Manager

```yaml
# ECS Task Definition
secrets:
  - name: DATABASE_URL
    valueFrom: arn:aws:secretsmanager:region:account:secret:myapp/prod/db

# App Platform (via GitHub Secrets)
envs:
  - key: DATABASE_URL
    scope: RUN_TIME
    type: SECRET
```

### Parameter Store

```yaml
# ECS Task Definition
secrets:
  - name: API_KEY
    valueFrom: arn:aws:ssm:region:account:parameter/myapp/api-key

# App Platform (via GitHub Secrets)
envs:
  - key: API_KEY
    scope: RUN_TIME
    type: SECRET
```

### S3 Credentials

```yaml
# ECS (using IAM role)
# No explicit credentials, uses task role

# App Platform (using Spaces)
envs:
  - key: SPACES_ENDPOINT
    value: https://nyc3.digitaloceanspaces.com
  - key: SPACES_REGION
    value: nyc3
  - key: SPACES_KEY
    type: SECRET
  - key: SPACES_SECRET
    type: SECRET
  - key: SPACES_BUCKET
    value: myapp-uploads
```

## Render → App Platform

### Direct Mappings

| Render | App Platform |
|--------|-------------|
| `envVars[].key` | `envs[].key` |
| `envVars[].value` | `envs[].value` |
| `envVars[].fromDatabase` | Bindable: `${db.DATABASE_URL}` |
| `envVars[].sync: false` | `scope: BUILD_TIME` |

## Railway → App Platform

### Railway Variables

| Railway | App Platform |
|---------|-------------|
| `${{RAILWAY_*}}` | Use explicit values |
| `${{Postgres.*}}` | `${db.DATABASE_URL}` |
| `${{Redis.*}}` | `${cache.DATABASE_URL}` |

## Fly.io → App Platform

### Fly Secrets

```bash
# Fly.io
fly secrets set DATABASE_URL=postgres://...

# App Platform (via GitHub Secrets)
gh secret set DATABASE_URL --env staging
```

### Fly Environment

| Fly Variable | App Platform Equivalent |
|--------------|------------------------|
| `FLY_APP_NAME` | `${APP_NAME}` |
| `FLY_REGION` | `${APP_REGION}` |
| `PRIMARY_REGION` | Not applicable |

## Variable Scopes

App Platform supports different variable scopes:

```yaml
envs:
  # Available during build and runtime
  - key: NODE_ENV
    value: production
    scope: RUN_AND_BUILD_TIME  # Default
  
  # Build only (not in running container)
  - key: NPM_TOKEN
    scope: BUILD_TIME
    type: SECRET
  
  # Runtime only (not during build)
  - key: DATABASE_URL
    scope: RUN_TIME
    value: ${db.DATABASE_URL}
```

## Secret Types

```yaml
envs:
  # Regular variable (visible in UI)
  - key: LOG_LEVEL
    value: info
  
  # Secret (masked in UI, encrypted)
  - key: API_KEY
    type: SECRET
  
  # General secret (shared across components)
  - key: SHARED_SECRET
    type: GENERAL
```

## Bindable Variables

These variables can reference other components:

| Pattern | Source |
|---------|--------|
| `${db.DATABASE_URL}` | Database connection string |
| `${db.CA_CERT}` | Database CA certificate |
| `${db.HOSTNAME}` | Database hostname |
| `${db.PORT}` | Database port |
| `${db.USERNAME}` | Database username |
| `${db.PASSWORD}` | Database password |
| `${db.DATABASE}` | Database name |
| `${app.name}` | App name |
| `${service.name.URL}` | Service internal URL |
