---
name: app-platform-router
description: Routes DigitalOcean App Platform tasks to specialized sub-skills for focused, precise responses
version: 1.0.0
author: Bikram Gupta
triggers:
  - "app platform"
  - "digitalocean app"
  - "do app"
  - "app spec"
  - "deploy to app platform"
  - "migrate to app platform"
  - "set up app platform"
  - "app platform help"
---

# App Platform Skills — Router

## Overview

This skill routes DigitalOcean App Platform tasks to specialized sub-skills. Each sub-skill is optimized for a specific workflow, keeping context focused and responses precise.

**Philosophy**: These skills are opinionated playbooks, not documentation replicas. They make decisions for you (VPC by default, GitHub Actions for CI/CD, etc.) and only defer to docs for edge cases.

**Key Principle**: Skills contain only DO-specific knowledge the LLM doesn't have from training. Generic SQL, SDK patterns, and programming concepts are NOT duplicated here.

## Available Skills

### Development Phase

| Skill | Purpose | Key Artifacts |
|-------|---------|---------------|
| **devcontainers** | Local development environment with prod parity | `.devcontainer/`, `docker-compose.dev.yml` |
| **hot-reload** | Cloud development with no container rebuild | App Platform hot reload template |

### Architecture Phase

| Skill | Purpose | Key Artifacts |
|-------|---------|---------------|
| **designer** | Natural language → production-ready App Spec | `.do/app.yaml` |
| **migration** | Convert existing apps (Heroku, AWS, etc.) to App Platform | `.do/app.yaml`, migration checklist |

### Operations Phase

| Skill | Purpose | Key Artifacts |
|-------|---------|---------------|
| **deployment** | Ship code to production via GitHub Actions | `.github/workflows/deploy.yml` |
| **troubleshooting** | Debug running apps with pre-built debug container, analyze logs | Fixes, diagnostic reports |

### Data Services

| Skill | Purpose | Key Artifacts |
|-------|---------|---------------|
| **postgres** | Full PostgreSQL setup: schemas, users, permissions, multi-tenant | SQL scripts (user-executed) |
| **managed-db-services** | MySQL, MongoDB, Valkey, Kafka, OpenSearch (bindable vars) | App spec snippets |
| **spaces** | S3-compatible object storage configuration | CORS config, app spec snippets |

### AI & Experimentation

| Skill | Purpose | Key Artifacts |
|-------|---------|---------------|
| **ai-services** | Gradient AI inference endpoints | App spec snippets |
| **sandbox** | Disposable cloud environments for code execution, AI agents | Sandbox instances |

---

## Routing Decision Tree

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │ Setting up development? │
                └─────────────────────────┘
                      │           │
              "local" │           │ "cloud" / "test in App Platform"
                      ▼           ▼
              ┌───────────┐  ┌───────────┐
              │devcontainers│  │hot-reload │
              └───────────┘  └───────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │ Designing or creating?  │
                └─────────────────────────┘
                      │           │
             "new app"│           │ "migrate" / "convert" / "move from"
                      ▼           ▼
              ┌───────────┐  ┌───────────┐
              │ designer  │  │ migration │
              └───────────┘  └───────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │    Shipping code?       │
                └─────────────────────────┘
                              │
                      "deploy" / "ship" / "release"
                              ▼
                      ┌───────────┐
                      │deployment │
                      └───────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │   Something broken?     │
                └─────────────────────────┘
                              │
                      "broken" / "failing" / "debug" / "logs"
                              ▼
                    ┌───────────────┐
                    │troubleshooting│
                    └───────────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │ Configuring data?       │
                └─────────────────────────┘
                      │           │           │
           "postgres" │  "mysql"  │           │ "storage" / "S3" / "spaces"
           (complex)  │  "mongo"  │           │
                      │  "valkey" │           │
                      │  "kafka"  │           │
                      │  "opensearch"         │
                      ▼           ▼           ▼
              ┌───────────┐  ┌─────────────────────┐  ┌───────────┐
              │ postgres  │  │ managed-db-services │  │  spaces   │
              └───────────┘  └─────────────────────┘  └───────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │ AI inference needed?    │
                └─────────────────────────┘
                              │
                      "gradient" / "LLM" / "inference"
                              ▼
                      ┌─────────────┐
                      │ ai-services │
                      └─────────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │ Disposable environment? │
                │ AI agent execution?     │
                └─────────────────────────┘
                              │
              "sandbox" / "disposable" / "run code" / "agent"
                              ▼
                      ┌───────────┐
                      │  sandbox  │
                      └───────────┘
```

---

## Trigger Phrases Reference

| Route To | Trigger Phrases |
|----------|----------------|
| devcontainers | "local dev", "docker compose", "run locally", "devcontainer" |
| hot-reload | "cloud dev", "test in App Platform", "hot reload", "no rebuild" |
| designer | "design my app", "create app spec", "new application", "architect" |
| migration | "migrate", "convert", "move from Heroku", "move from AWS" |
| deployment | "deploy", "ship", "release", "GitHub Actions", "CI/CD" |
| troubleshooting | "broken", "failing", "debug", "logs", "502", "crash", "error" |
| postgres | "postgres", "postgresql", "schema isolation", "multi-tenant database" |
| managed-db-services | "mysql", "mongodb", "mongo", "valkey", "redis", "kafka", "opensearch" |
| spaces | "object storage", "S3", "Spaces", "file upload", "bucket" |
| ai-services | "gradient", "inference", "LLM endpoint", "AI platform" |
| sandbox | "sandbox", "disposable", "parallel experiments", "agentic workflow" |

---

## Third-Party Integrations (No Skill Needed)

For integrations not covered by dedicated skills (DataDog, Sentry, New Relic, Stripe, etc.):

1. **Get credentials** from the vendor
2. **Add to GitHub Secrets** (Repo → Settings → Secrets → Actions)
3. **Reference in app spec**:
   ```yaml
   envs:
     - key: DATADOG_API_KEY
       scope: RUN_TIME
       value: ${DATADOG_API_KEY}  # From GitHub Secrets
   ```
4. **Follow vendor documentation** for SDK/agent setup

→ The agent's training covers vendor-specific patterns — no skill required.

---

## Credential Handling Philosophy

**CRITICAL**: These skills are designed to keep credentials out of agent hands.

### Priority Order (Most to Least Preferred)

```
1. GITHUB SECRETS (RECOMMENDED DEFAULT)
   ├── Agent never sees credentials
   ├── User manually adds: Repo → Settings → Secrets → Actions
   ├── Workflow references: ${{ secrets.DATABASE_URL }}
   └── Agent generates workflow, user handles secrets

2. APP PLATFORM BINDABLE VARIABLES
   ├── For DO Managed Databases (Postgres, MySQL, MongoDB, etc.)
   ├── Credentials injected via ${db.DATABASE_URL}
   ├── Agent configures app spec, never sees credentials
   └── Best for: Apps using DO managed services

3. LOCAL .ENV + EPHEMERAL APP SPEC
   ├── User maintains .env file locally
   ├── Agent creates temp app spec with placeholders
   └── Substitutes values → Deploys → Deletes temp file

4. EXTERNAL SERVICES
   ├── Same patterns as #1 or #3
   └── User responsible for credential management
```

---

## Artifact Contracts

All skills produce and consume artifacts with consistent naming:

| Artifact | Filename | Producer | Consumer |
|----------|----------|----------|----------|
| App Spec | `.do/app.yaml` | designer, migration | deployment |
| Deploy Button | `.do/deploy.template.yaml` | designer, migration | GitHub |
| Dev Environment | `.devcontainer/devcontainer.json` | devcontainers | VS Code, Cursor |
| Docker Compose | `docker-compose.yml` | devcontainers | Docker Desktop |
| CI/CD Workflow | `.github/workflows/deploy.yml` | deployment | GitHub Actions |
| SQL Scripts | `db-*.sql` | postgres | User (manual execution) |
| CORS Config | `spaces-cors.json` | spaces | DO Console |
| Sandbox Instance | Runtime (no file) | sandbox | Code execution |

### Handoff Protocol

When a skill completes, it should:

1. **State the artifact(s) produced**: "Created `.do/app.yaml` with 3-component architecture"
2. **Indicate the file path**: Relative to project root
3. **Suggest next skill if applicable**: "To deploy this, use the **deployment skill**"

---

## Plugin/Tool Requirements

| Skill | Required | Optional |
|-------|----------|----------|
| devcontainers | filesystem, docker, git | gh |
| hot-reload | filesystem, doctl, git, python | gh, DigitalOcean MCP |
| designer | filesystem | — |
| migration | filesystem, doctl, git, python | gh, DigitalOcean MCP |
| deployment | filesystem, doctl, git, python | gh, GitHub MCP |
| troubleshooting | filesystem, python, doctl | — |
| postgres | filesystem, psql | — (scripts only) |
| managed-db-services | filesystem | — (app spec only) |
| spaces | filesystem | — |
| ai-services | filesystem | — |
| sandbox | filesystem, python, doctl | Spaces credentials |

---

## Sub-Skill Locations

```
app-platform-skills/
├── SKILL.md                              # This file (router)
├── skills/
│   ├── devcontainers/SKILL.md
│   ├── hot-reload/SKILL.md
│   ├── designer/SKILL.md
│   ├── migration/SKILL.md
│   ├── deployment/SKILL.md
│   ├── troubleshooting/SKILL.md
│   ├── postgres/SKILL.md
│   ├── managed-db-services/SKILL.md      # MySQL, MongoDB, Valkey, Kafka, OpenSearch
│   ├── spaces/SKILL.md
│   ├── ai-services/SKILL.md              # Gradient AI
│   └── sandbox/SKILL.md
└── shared/
    ├── app-spec-schema.yaml
    ├── artifact-contracts.md
    └── credential-patterns.md
```

---

## Opinionated Defaults Summary

| Domain | Default | Override Trigger |
|--------|---------|-----------------|
| Networking | VPC-only, internal routing | User explicitly requests public |
| CI/CD | GitHub + GitHub Actions | User specifies GitLab/Bitbucket |
| Secrets | GitHub Secrets | User has existing vault |
| Build | Dockerfile | User explicitly prefers buildpacks |
| Database | DO Managed + Bindable Variables | User has external DB |
| Monorepo | Supported by default (source_dir) | N/A |
| Python env | uv for package/venv management | User prefers pip/poetry |
| Node env | nvm for version management | User prefers n/volta |

---

## Escalation

If a task doesn't fit any skill or spans multiple skills ambiguously:

1. Ask clarifying question to determine primary intent
2. Suggest skill sequence if task is multi-phase
3. For truly novel tasks, fall back to App Platform documentation: https://docs.digitalocean.com/products/app-platform/
