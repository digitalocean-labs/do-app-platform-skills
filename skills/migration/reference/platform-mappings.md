# Platform Mapping Reference

Detailed service and component mappings from source platforms to DigitalOcean App Platform.

## Automatic Platform Detection

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

---

## Heroku to App Platform

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

### Heroku-Specific Gotchas

- **DATABASE_URL format**: Heroku uses `postgres://`, App Platform uses `postgresql://`
- **Dyno types** don't map 1:1 to instance sizes
- **Review dynos** become preview environments (different workflow)

---

## Docker Compose to App Platform

| Docker Compose | App Platform | Notes |
|----------------|--------------|-------|
| `services.<name>.ports` | `services` with `http_port` | First port becomes http_port |
| `services.<name>` (no ports) | `workers` | Background processes |
| `services.postgres` | Managed Postgres | Extract version from image |
| `services.redis` | Managed Valkey | |
| `services.mongodb` | Managed MongoDB | |
| `volumes` (named) | Spaces or ephemeral | No persistent volumes yet |
| `volumes` (bind mounts) | Not supported | Dev-only pattern |
| `depends_on` | Health checks | Implicit ordering |
| `networks` | Internal networking | Automatic within app |
| `build.context` | `source_dir` | |
| `environment` | `envs` array | |

### Docker Compose-Specific Gotchas

- `depends_on` doesn't guarantee startup order - use health checks
- Host networking not available
- Volume mounts don't persist

---

## Render to App Platform

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

---

## AWS ECS to App Platform

| AWS ECS | App Platform | Notes |
|---------|--------------|-------|
| Container definition | Component | One container = one component |
| `portMappings` | `http_port` | First port mapping |
| `environment` | `envs` | |
| `secrets` (SSM) | GitHub Secrets | Different pattern |
| `secrets` (Secrets Manager) | GitHub Secrets | Different pattern |
| ALB target groups | Built-in routing | Automatic |
| Service Discovery | Internal networking | Use service names |
| RDS | Managed Postgres/MySQL | May need VPC |
| ElastiCache | Managed Valkey | |
| S3 | Spaces | Compatible API |
| CloudWatch Logs | Built-in + forwarding | |
| IAM roles | Not applicable | Different auth model |

### AWS-Specific Gotchas

- IAM roles don't exist - use API keys or GitHub Secrets
- VPC peering may be needed for RDS access
- CloudWatch metrics to App Platform Insights (different metrics)

---

## Unmappable Items

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

---

## Architecture Analysis Output

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
