# Designer Skill

Transform natural language application descriptions into production-ready DigitalOcean App Platform specifications.

## What This Skill Does

- Converts descriptions like "I need a web app with..." into `.do/app.yaml`
- Analyzes existing repositories to generate app specs
- Creates Deploy to DigitalOcean button configurations
- Designs multi-component architectures (services, workers, jobs, static sites)

## Quick Start

```bash
# User says: "I need a Python API with PostgreSQL"
# Skill produces:
.do/
├── app.yaml              # App Platform specification
└── deploy.template.yaml  # Deploy to DO button
```

## Key Decisions This Skill Makes

| Decision | Default | Rationale |
|----------|---------|-----------|
| Instance size | `apps-s-1vcpu-1gb` | Good starting point |
| Database | Dev database | Cost-effective for development |
| Cache | Valkey (not Redis) | Redis is EOL |
| Build method | Dockerfile if present | More control |
| Health check | `/health` or `/healthz` | Industry standard |
| Region | `nyc` | Good default |

## Files

- `SKILL.md` — Complete skill documentation with workflows
- `reference/component-types.md` — Services, workers, jobs, static sites
- `reference/architecture-patterns.md` — 5 complete architecture patterns
- `reference/environment-variables.md` — Scopes, types, placeholders
- `reference/deploy-to-do-button.md` — Button setup and templates
- `reference/database-configuration.md` — Dev vs managed databases

## Integration

| Direction | Skill | Integration |
|-----------|-------|-------------|
| → | deployment | Deploy the generated app spec |
| → | devcontainers | Create local dev environment |
| → | postgres | Advanced database configuration |
| → | networking | Custom domains, CORS, VPC |
| ← | migration | Converts from other platforms |

## Related Skills

- **deployment** — Ship the app spec to production
- **planner** — Generate staged deployment plans
- **postgres** — Configure database permissions
