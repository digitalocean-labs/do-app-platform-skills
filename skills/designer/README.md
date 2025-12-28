# Designer Skill

Transform natural language application descriptions into production-ready DigitalOcean App Platform specifications.

## What This Skill Does

- Generates `.do/app.yaml` — Complete App Platform specification
- Generates `.do/deploy.template.yaml` — Deploy to DO button (public repos only)
- Generates `.env.example` — Environment variable template
- Creates architecture diagrams for complex apps

## Quick Start

**From natural language:**
```
"I need a web app with a Python API, React frontend, and PostgreSQL database"
```

**From repository analysis:**
```
"Analyze my repo at github.com/owner/repo and create an app spec"
```

## Key Decisions This Skill Makes

| Decision | Default |
|----------|---------|
| Instance size | `apps-s-1vcpu-1gb` |
| Database | Dev database for testing |
| Cache | Valkey (not Redis) |
| Build | Dockerfile if present |
| Region | `nyc` |

## Files

- `SKILL.md` — Complete skill documentation with all workflows, patterns, and reference data

## Integration

This skill produces artifacts consumed by:
- **deployment** skill — Takes app spec and deploys
- **devcontainers** skill — Reads app spec for local environment parity

## Related Skills

- **networking** — Advanced routing, domains, CORS, VPC, static IPs
- **migration** — Convert from other platforms (produces app spec)
- **postgres** — Database schemas and users (after architecture is defined)
- **deployment** — Deploy the generated spec
