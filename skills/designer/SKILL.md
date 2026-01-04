---
name: app-platform-designer
description: Transform natural language application descriptions into production-ready DigitalOcean App Platform specifications. Use when designing apps, creating app specs, generating deploy.template.yaml, or architecting multi-component applications.
---

# App Platform Designer Skill

Transform natural language descriptions into production-ready App Platform specifications.

**Primary question:** "I want to build [description]. What should my App Platform architecture look like?"

**Produces:**
- `.do/app.yaml` — App Platform specification
- `.do/deploy.template.yaml` — Deploy to DO button (public repos)
- `.env.example` — Environment variable template

---

## Quick Decision

```
What do you need?
├── Design new app from description → Workflow 1
├── Analyze repo and create spec → Workflow 2
├── Add Deploy to DO button → Workflow 3
└── Multi-environment setup → Workflow 4
```

---

## Workflow 1: Natural Language → App Spec

**Trigger:** "I need a web app with [description]"

1. **Gather requirements:**
   - What does the app do?
   - Language/framework?
   - Database needs?
   - Background processing?

2. **Decompose into components:**
   - HTTP-facing → `services`
   - Background processors → `workers`
   - One-time/scheduled → `jobs`
   - Static frontends → `static_sites`
   - Data stores → `databases`

3. **Generate spec** with health checks, env vars, routing

4. **Validate:** `doctl apps spec validate .do/app.yaml`

**Full guide:** See [architecture-patterns.md](reference/architecture-patterns.md)

---

## Workflow 2: Analyze Repository → App Spec

**Trigger:** "Here's my repo, create an app spec"

```
Check for:
├── Dockerfile → Use dockerfile build
├── package.json → Node.js app
├── requirements.txt / pyproject.toml → Python app
├── go.mod → Go app
├── Multiple directories with above → Monorepo
```

**Full guide:** See [component-types.md](reference/component-types.md)

---

## Workflow 3: Deploy to DO Button

**Trigger:** "Add Deploy to DigitalOcean button"

**Requirements:** Public GitHub repository

1. Create `.do/deploy.template.yaml` (wraps spec in `spec:` key, uses `git:` block)
2. Add button to README

```markdown
[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/OWNER/REPO/tree/BRANCH)
```

**Full guide:** See [deploy-to-do-button.md](reference/deploy-to-do-button.md)

---

## Opinionated Defaults

| Decision | Default | Rationale |
|----------|---------|-----------|
| Instance size | `apps-s-1vcpu-1gb` | Good starting point |
| Instance count | 1 | Start minimal |
| Database | Dev database | Cost-effective |
| Cache | Valkey (not Redis) | Redis is EOL |
| Build | Dockerfile if present | More control |
| Health check | `/health` or `/healthz` | Industry standard |
| Deploy on push | `true` | GitOps workflow |
| Region | `nyc` | Good default |
| Source format | `git:` block | Required for deploy.template.yaml |

---

## Component Summary

| Type | Use Case | Example |
|------|----------|---------|
| `services` | HTTP workloads | APIs, web apps |
| `workers` | Background processing | Queue consumers, internal APIs |
| `jobs` | One-time/scheduled | Migrations, reports |
| `static_sites` | Frontend/docs | React, Vue, marketing |
| `databases` | Data storage | PostgreSQL, Valkey |

**Full guide:** See [component-types.md](reference/component-types.md)

---

## Pattern Selection

```
What are you building?
├── Simple app (1 service)? → Pattern 1
├── Frontend + API? → Pattern 2
├── Need background processing? → Pattern 3
├── Monorepo? → Pattern 4
└── Complex SaaS? → Pattern 5
```

**Full patterns:** See [architecture-patterns.md](reference/architecture-patterns.md)

---

## Quick Start: Single Service + DB

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

## Quick Start: API + Frontend

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
        value: /api

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

## Environment-Portable Design

**All code must work in: local dev, Docker Compose, AND App Platform.**

| Principle | Implementation |
|-----------|----------------|
| Bind to `$PORT` | `process.env.PORT \|\| 3000` |
| Public services | Listed in `ingress.rules` |
| Internal services | Not in ingress, use `${name.PRIVATE_URL}` |
| Never hardcode | Use env vars with defaults |

```typescript
// Portable port binding
const port = process.env.PORT || 3000
server.listen({ port, host: '0.0.0.0' })
```

---

## Database Quick Reference

| Engine | Slug | Dev DB? | Notes |
|--------|------|---------|-------|
| PostgreSQL | `PG` | Yes | Recommended |
| Valkey | `VALKEY` | Yes | Use instead of Redis |
| MySQL | `MYSQL` | No | Managed only |
| MongoDB | `MONGODB` | No | Managed only |

**Full guide:** See [database-configuration.md](reference/database-configuration.md)

---

## Environment Variables Quick Reference

| Scope | Use Case |
|-------|----------|
| `RUN_TIME` | Secrets, DB URLs |
| `BUILD_TIME` | Public API URLs, feature flags |
| `RUN_AND_BUILD_TIME` | NPM tokens, shared config |

| Placeholder | Resolves To |
|-------------|-------------|
| `${db.DATABASE_URL}` | Database connection string |
| `${service.PRIVATE_URL}` | Internal service URL |
| `${service.PUBLIC_URL}` | Public service URL |

**Full guide:** See [environment-variables.md](reference/environment-variables.md)

---

## Ingress (Routing)

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

**For advanced routing:** See [networking skill](../networking/SKILL.md)

---

## Validation

```bash
doctl apps spec validate .do/app.yaml
doctl apps spec validate .do/deploy.template.yaml
```

| Error | Fix |
|-------|-----|
| `invalid component name` | Use lowercase, hyphens only |
| `unknown instance size` | Check instance-sizes.yaml |
| `invalid database reference` | Verify database name matches |
| `routes is deprecated` | Use `ingress.rules` |

---

## Instance Sizes

| Slug | CPU | RAM | Price | Use Case |
|------|-----|-----|-------|----------|
| `apps-s-1vcpu-0.5gb` | 1 shared | 512 MiB | $5/mo | Workers, jobs |
| `apps-s-1vcpu-1gb` | 1 shared | 1 GiB | $12/mo | Default |
| `apps-d-1vcpu-2gb` | 1 dedicated | 2 GiB | $39/mo | Production |

**Full list:** See [shared/instance-sizes.yaml](../../shared/instance-sizes.yaml)

---

## Reference Files

- **[component-types.md](reference/component-types.md)** — Services, workers, jobs, static sites
- **[architecture-patterns.md](reference/architecture-patterns.md)** — All 5 patterns with YAML
- **[environment-variables.md](reference/environment-variables.md)** — Scopes, types, placeholders
- **[deploy-to-do-button.md](reference/deploy-to-do-button.md)** — Template conversion, button HTML
- **[database-configuration.md](reference/database-configuration.md)** — Dev vs managed, bindable vars

---

## Shared References

- **[AppSpec-Reference.md](../../shared/AppSpec-Reference.md)** — Field-level syntax, constraints
- **[instance-sizes.yaml](../../shared/instance-sizes.yaml)** — All instance sizes and pricing
- **[regions.yaml](../../shared/regions.yaml)** — Available regions
- **[bindable-variables.md](../../shared/bindable-variables.md)** — All bindable variable patterns

---

## Integration with Other Skills

- **→ deployment**: Deploy the generated app spec via GitHub Actions
- **→ devcontainers**: Create local dev environment with prod parity
- **→ postgres**: Advanced database configuration
- **→ networking**: Custom domains, CORS, VPC
- **→ migration**: Convert from other platforms
