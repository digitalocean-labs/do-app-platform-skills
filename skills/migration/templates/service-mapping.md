# Service Mapping Reference

This document provides detailed mapping patterns for migrating services from various platforms to DigitalOcean App Platform.

## Component Type Mapping

### HTTP Services

| Source Platform | Source Type | App Platform Type |
|-----------------|-------------|-------------------|
| Heroku | `web` (Procfile) | `services` |
| Docker Compose | Service with `ports` | `services` |
| Render | `type: web` | `services` |
| Railway | Service with port | `services` |
| Fly.io | `[http_service]` | `services` |
| AWS ECS | Container with port mapping | `services` |

### Background Workers

| Source Platform | Source Type | App Platform Type |
|-----------------|-------------|-------------------|
| Heroku | `worker` (Procfile) | `workers` |
| Docker Compose | Service without `ports` | `workers` |
| Render | `type: worker` | `workers` |
| Railway | Service without port | `workers` |
| Fly.io | `[processes]` without http | `workers` |
| AWS ECS | Container without port | `workers` |

### Jobs (One-time / Scheduled)

| Source Platform | Source Type | App Platform Type | Kind |
|-----------------|-------------|-------------------|------|
| Heroku | `release` (Procfile) | `jobs` | `PRE_DEPLOY` |
| Heroku | Scheduler add-on | `jobs` | `CRON_TRIGGER` |
| Render | `type: cron` | `jobs` | `CRON_TRIGGER` |
| AWS ECS | Scheduled task | `jobs` | `CRON_TRIGGER` |

### Static Sites

| Source Platform | Source Type | App Platform Type |
|-----------------|-------------|-------------------|
| Render | `type: static` | `static_sites` |
| Netlify | Static site | `static_sites` |
| Vercel | Static export | `static_sites` |

## Database Mapping

### PostgreSQL

| Source | App Platform Configuration |
|--------|---------------------------|
| Heroku `heroku-postgresql` | `engine: PG` |
| Docker `postgres:15` | `engine: PG, version: "15"` |
| AWS RDS PostgreSQL | `engine: PG` |
| Render PostgreSQL | `engine: PG` |

```yaml
# Testing (Dev Database - $7/month)
databases:
  - name: db
    engine: PG
    production: false

# Production (Managed - $15+/month)
databases:
  - name: db
    engine: PG
    production: true
    cluster_name: myapp-prod-db  # Must exist
```

### MySQL

| Source | App Platform Configuration |
|--------|---------------------------|
| Docker `mysql:8` | `engine: MYSQL` |
| AWS RDS MySQL | `engine: MYSQL` |
| Heroku ClearDB | `engine: MYSQL` |

```yaml
# MySQL requires managed database (no dev option)
databases:
  - name: mysqldb
    engine: MYSQL
    production: true
    cluster_name: myapp-mysql
```

### MongoDB

| Source | App Platform Configuration |
|--------|---------------------------|
| Docker `mongo:6` | `engine: MONGODB` |
| Heroku mLab | External (Atlas) recommended |

```yaml
# MongoDB requires managed database
databases:
  - name: mongodb
    engine: MONGODB
    production: true
    cluster_name: myapp-mongo
```

### Redis / Valkey

⚠️ **Important**: Redis is End-of-Life on DigitalOcean. Use Valkey instead.

| Source | App Platform Configuration |
|--------|---------------------------|
| Heroku `heroku-redis` | `engine: VALKEY` |
| Docker `redis:7` | `engine: VALKEY` |
| AWS ElastiCache Redis | `engine: VALKEY` |

```yaml
# Testing (Dev Valkey)
databases:
  - name: cache
    engine: VALKEY
    production: false

# Production (Managed Valkey)
databases:
  - name: cache
    engine: VALKEY
    production: true
    cluster_name: myapp-cache
```

## Storage Mapping

### Object Storage

| Source | Recommendation |
|--------|---------------|
| AWS S3 | DigitalOcean Spaces |
| Heroku (via S3) | DigitalOcean Spaces |
| Cloudinary | Keep external OR Spaces |
| MinIO (local) | DigitalOcean Spaces |

```python
# S3 → Spaces configuration
import boto3

s3 = boto3.client('s3',
    endpoint_url=os.environ['SPACES_ENDPOINT'],  # https://nyc3.digitaloceanspaces.com
    region_name=os.environ['SPACES_REGION'],      # nyc3
    aws_access_key_id=os.environ['SPACES_KEY'],
    aws_secret_access_key=os.environ['SPACES_SECRET']
)

# Bucket operations remain the same
s3.upload_file('file.txt', os.environ['SPACES_BUCKET'], 'file.txt')
```

### Persistent Volumes

⚠️ **Not Supported** until Q1 2026 (NFS support planned)

| Source | Workaround |
|--------|-----------|
| Docker volumes | Use managed database |
| EFS mounts | Use Spaces for files |
| NFS mounts | Wait for NFS support or use external |

## Queue/Message Broker Mapping

### RabbitMQ

❌ **No direct equivalent** on App Platform.

Options:
1. **External RabbitMQ**: CloudAMQP, Amazon MQ
2. **Use Kafka**: Supported on DigitalOcean Managed Databases
3. **Use Valkey**: For simple queue patterns (Redis-like)

### Kafka

✅ Supported via Managed Kafka

```yaml
databases:
  - name: kafka
    engine: KAFKA
    production: true
    cluster_name: myapp-kafka
```

### SQS / Celery

| Pattern | Recommendation |
|---------|---------------|
| Celery + Redis | Celery + Valkey |
| Celery + RabbitMQ | Celery + Valkey OR external RabbitMQ |
| SQS | External SQS or use Valkey |

## CDN Mapping

### CloudFront / CDN Services

❌ **No native CDN** on App Platform.

Options:
1. **Cloudflare** (free tier available): Point DNS through Cloudflare
2. **Fastly**: Enterprise CDN option
3. **Skip CDN**: App Platform has some edge caching built-in

## Health Checks

| Source | App Platform |
|--------|-------------|
| Heroku (automatic) | Must configure explicitly |
| ECS `healthCheck` | `health_check` block |
| Render `healthCheckPath` | `health_check.http_path` |

```yaml
services:
  - name: web
    health_check:
      http_path: /health
      initial_delay_seconds: 10
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 3
```

## Scaling Configuration

### Heroku Dynos → App Platform Instances

| Heroku | App Platform |
|--------|-------------|
| `standard-1x` | `apps-s-1vcpu-1gb` |
| `standard-2x` | `apps-s-2vcpu-4gb` |
| `performance-m` | `apps-d-2vcpu-4gb` |
| `performance-l` | `apps-d-4vcpu-8gb` |

### Autoscaling

```yaml
services:
  - name: web
    instance_size_slug: apps-d-1vcpu-2gb  # Dedicated required
    autoscaling:
      min_instance_count: 2
      max_instance_count: 10
      metrics:
        - type: CPU
          percent: 80
```

⚠️ Autoscaling only available on dedicated instances (`apps-d-*`).

## Networking

### Internal Service Communication

| Pattern | App Platform |
|---------|-------------|
| `http://api:3000` (Compose) | `http://api.${APP_DOMAIN}:80` (internal) |
| Service Discovery (ECS) | Use service names directly |
| Private networking | Automatic within app |

### External Database Access

```yaml
# App Platform automatically adds to trusted sources
# For external databases, you need VPC or IP allowlist

# Example: External RDS
services:
  - name: web
    envs:
      - key: DATABASE_URL
        value: postgres://user:pass@rds-endpoint:5432/db
```

## Logging

| Source | App Platform |
|--------|-------------|
| Papertrail | Log forwarding to Papertrail |
| CloudWatch | Built-in logs + forwarding |
| Datadog | Log forwarding to Datadog |

```yaml
# Log forwarding configuration (in app spec)
alerts:
  - rule: DEPLOYMENT_FAILED
  - rule: COMPONENT_RESTARTED
```

## Secrets Management

| Source | App Platform Pattern |
|--------|---------------------|
| AWS Secrets Manager | GitHub Secrets |
| Heroku Config Vars | GitHub Secrets |
| Vault | External (keep) or GitHub Secrets |

```yaml
# Pattern: Use GitHub Secrets for all sensitive values
envs:
  - key: DATABASE_URL
    scope: RUN_TIME
    type: SECRET  # Value set in GitHub Secrets
```

## Unmappable Items

These require special handling or alternatives:

| Item | Issue | Recommended Action |
|------|-------|-------------------|
| IAM Roles | Different auth model | Use API keys |
| VPC Peering | Limited | Use trusted sources |
| Step Functions | No equivalent | External orchestration |
| Lambda@Edge | No equivalent | Keep external |
| Custom domains (many) | Limited | External LB |
| WebSocket sticky sessions | Limited | Architecture review |
