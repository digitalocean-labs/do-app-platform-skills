---
name: app-platform-migration
description: Migrate applications from Heroku, AWS, Render, Railway, Fly.io, or Docker Compose to DigitalOcean App Platform. Use when converting existing apps, mapping services, refactoring platform-specific code, or creating app specs from other platform configurations.
---

# App Platform Migration Skill

Migrate existing applications to DigitalOcean App Platform with honest capability assessment.

## Philosophy

This skill is an honest partner, not a magic wand. It:

1. **Analyzes thoroughly** before proposing changes
2. **Maps what it can** with confidence
3. **Acknowledges gaps** clearly and specifically
4. **Asks before proceeding** when uncertain
5. **Never guesses** or ignores incompatibilities

> **Tip**: For complex multi-step migrations, use the **planner** skill first. For all available skills, see [root SKILL.md](../../SKILL.md).

---

## Quick Decision

```
What's your source platform?
├── Heroku (Procfile, app.json) → See Quick Start below
├── Docker Compose → See Quick Start below
├── Render/Railway/Fly.io → See Quick Start below
├── AWS ECS/App Runner → Complex migration, see reference
└── Just Dockerfile → See Quick Start below
```

---

## Supported Platforms

| Platform | Config Files | Support Level |
|----------|--------------|---------------|
| **Heroku** | `Procfile`, `app.json` | Full |
| **Docker Compose** | `docker-compose.yml` | Full |
| **Render** | `render.yaml` | Full |
| **Railway** | `railway.json`, `railway.toml` | Full |
| **Fly.io** | `fly.toml` | Full |
| **AWS ECS** | Task Definition JSON | Partial |
| **AWS App Runner** | `apprunner.yaml` | Partial |
| **Generic Docker** | `Dockerfile` only | Full |

---

## Migration Workflow

```
Phase 1: DISCOVERY
├── Clone/access repository
├── Detect source platform
├── Analyze architecture
└── Inventory all services

Phase 2: MAPPING
├── Map services → App Platform components
├── Map databases → Managed databases
├── Map storage → Spaces
├── Map secrets → GitHub Secrets
└── Identify unmappable items → REPORT TO USER

Phase 3: REFACTORING
├── Create target branch(es)
├── Update environment variables
├── Remove platform-specific code
├── Update Dockerfile if needed
└── Generate app spec

Phase 4: VALIDATION
├── Validate: doctl apps spec validate
├── Review changes with user
└── Generate migration checklist

Phase 5: HANDOFF
├── Push branches to repo
├── Provide manual steps checklist
└── Suggest deployment skill
```

---

## Quick Start

### Basic Migration

```bash
# User provides repo URL
"Migrate this app to App Platform: https://github.com/myorg/myapp"

# AI will:
# 1. Clone and analyze
# 2. Detect platform
# 3. Present mapping proposal
# 4. Ask for approval
# 5. Create branch with refactored code + app spec
```

### With Branch Specification

```bash
"Migrate my Heroku app. Put test config in 'migrate/test', prod in 'migrate/prod'"
```

**Full workflows**: See [workflow-examples.md](reference/workflow-examples.md)

---

## Quick Mapping Reference

### Heroku

| Heroku | App Platform |
|--------|--------------|
| `web` process | `services` |
| `worker` process | `workers` |
| `release` phase | `jobs` (PRE_DEPLOY) |
| `heroku-postgresql` | Managed Postgres |
| `heroku-redis` | Managed Valkey |
| Config Vars | GitHub Secrets |

### Docker Compose

| Docker Compose | App Platform |
|----------------|--------------|
| `services.<name>.ports` | `services` |
| `services.<name>` (no ports) | `workers` |
| `services.postgres` | Managed Postgres |
| `services.redis` | Managed Valkey |
| `volumes` | Spaces (no persistent volumes) |

**Full mapping tables**: See [platform-mappings.md](reference/platform-mappings.md)

---

## Unmappable Items (Quick Reference)

| Source | Issue | Options |
|--------|-------|---------|
| CloudFront CDN | No DO CDN | External CDN (Cloudflare) or skip |
| AWS Secrets Manager | Different model | GitHub Secrets |
| Persistent volumes | Not supported | Spaces for files, managed DB for data |
| ARM containers | AMD64 only | Rebuild for AMD64 |

**Full list**: See [platform-mappings.md](reference/platform-mappings.md#unmappable-items)

---

## Output Artifacts

| File | Purpose |
|------|---------|
| `.do/app.yaml` | App Platform specification |
| `.do/deploy.template.yaml` | Deploy to DO button |
| `MIGRATION.md` | Migration checklist and status |
| `.env.example` | Environment variable template |

**App spec templates**: See [app-spec-generation.md](reference/app-spec-generation.md)

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/detect_platform.py` | Detect source platform from files |
| `scripts/analyze_architecture.py` | Analyze application architecture |
| `scripts/generate_app_spec.py` | Generate .do/app.yaml |
| `scripts/generate_checklist.py` | Generate migration checklist |

---

## Reference Files

- **[platform-mappings.md](reference/platform-mappings.md)** - Full platform detection, all mapping tables, gotchas
- **[code-refactoring.md](reference/code-refactoring.md)** - Env var updates, S3/Valkey migration, data migration
- **[workflow-examples.md](reference/workflow-examples.md)** - Heroku, Docker Compose, AWS ECS walkthroughs
- **[app-spec-generation.md](reference/app-spec-generation.md)** - Test/prod spec templates, defaults

---

## Common Issues (Quick Fixes)

| Issue | Cause | Fix |
|-------|-------|-----|
| App spec validation fails | Invalid YAML | Check indentation, `doctl apps spec validate` |
| Database connection fails | Wrong URL format | Use `${db.DATABASE_URL}` binding |
| Build fails | Missing dependencies | Check Dockerfile build deps |
| Port binding fails | Wrong PORT handling | Bind to `$PORT` or `0.0.0.0:8080` |
| Health check fails | Wrong path | Verify `/health` endpoint exists |

**Full troubleshooting**: See [code-refactoring.md](reference/code-refactoring.md#troubleshooting-code-changes)

---

## Integration with Other Skills

- **→ deployment**: GitHub Actions workflow after migration
- **→ postgres**: Complex database setup, schema isolation
- **→ devcontainers**: Local dev environment post-migration
- **→ troubleshooting**: Debug container for migration issues

---

## Documentation Links

- [App Spec Reference](https://docs.digitalocean.com/products/app-platform/reference/app-spec/)
- [Heroku Migration Guide](https://docs.digitalocean.com/products/app-platform/how-to/migrate-from-heroku/)
- [Deploy to DO Button](https://docs.digitalocean.com/products/app-platform/how-to/add-deploy-do-button/)
