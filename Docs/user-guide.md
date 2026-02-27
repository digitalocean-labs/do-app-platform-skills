# User Guide

This guide preserves detailed usage and reference material that does not fit in the concise root README format.

## Version Compatibility

### Tool Requirements

| Tool | Minimum Version | Recommended | Notes |
|------|-----------------|-------------|-------|
| doctl | 1.82.0+ | 1.100.0+ | App spec v2 support |
| Python | 3.11+ | 3.12+ | For scripts |
| Node.js | 20+ | 22+ | LTS versions |
| PostgreSQL | 15+ | 16 | Default: 16 |

### Skills Version

All skills in this repository are versioned. Check each skill's frontmatter for:
- `version`: Semantic version (MAJOR.MINOR.PATCH)
- `min_doctl_version`: Minimum doctl CLI version required

```yaml
# Example from SKILL.md frontmatter
---
name: app-platform-designer
version: 1.0.0
min_doctl_version: "1.82.0"
---
```

### API Compatibility Matrix

| Skills Version | doctl Version | App Spec Version | Status |
|----------------|---------------|------------------|--------|
| 1.0.x | 1.82.0+ | v2 | ✅ Current |

### Checking Your doctl Version

```bash
doctl version
# doctl version 1.100.0-release

# Update if needed
brew upgrade doctl  # macOS
snap refresh doctl  # Linux
```

## What Are Skills?

Skills are structured prompts and documentation that help AI assistants (like Claude) perform specialized tasks. Each skill contains domain knowledge, best practices, code patterns, and decision trees for a specific area of App Platform.

## Example Prompts

| What You Want | Example Prompt |
|--------------|----------------|
| **Create a new app** | "Create an App Spec for my Node.js API with Redis caching. Use App Platform skills." |
| **Migrate from Heroku** | "Migrate this Heroku app to App Platform. Use the migration skill." |
| **Troubleshoot issues** | "My database connections are timing out. Use App Platform troubleshooting to diagnose." |
| **Set up CI/CD** | "Set up GitHub Actions to deploy on push to main. Use deployment skills." |
| **Configure networking** | "I need custom domain with SSL and CORS headers. Use networking skills." |
| **Database setup** | "Configure PostgreSQL with connection pooling for my Django app. Use postgres skills." |

## Available Skills

| Skill | Description | Key Artifacts |
|-------|-------------|---------------|
| [**designer**](../skills/designer/) | Natural language → production-ready App Spec | `.do/app.yaml` |
| [**deployment**](../skills/deployment/) | GitHub Actions CI/CD and deployment workflows | `.github/workflows/` |
| [**migration**](../skills/migration/) | Migrate from Heroku, AWS, Docker Compose, etc. | `.do/app.yaml`, checklist |
| [**networking**](../skills/networking/) | Domains, routing, CORS, VPC, static IPs | App spec snippets |
| [**postgres**](../skills/postgres/) | PostgreSQL configuration, security, multi-tenant | SQL scripts |
| [**managed-db-services**](../skills/managed-db-services/) | MySQL, MongoDB, Valkey, Kafka, OpenSearch | App spec snippets |
| [**spaces**](../skills/spaces/) | S3-compatible object storage | CORS config |
| [**ai-services**](../skills/ai-services/) | Gradient AI serverless inference | App spec snippets |
| [**troubleshooting**](../skills/troubleshooting/) | Debug running apps with container access | Diagnostic reports |
| [**devcontainers**](../skills/devcontainers/) | Local development with production parity | `.devcontainer/` |

## Alternative Usage Methods

### With Claude Projects (claude.ai)

1. Create a new Claude Project
2. Add the relevant `SKILL.md` files to the project knowledge
3. Start chatting about your App Platform needs

### Direct Context Injection

Copy the contents of any `SKILL.md` file into your conversation with any AI assistant as context.

## Philosophy

These skills are **opinionated playbooks**, not documentation replicas:

- They make decisions (VPC by default, GitHub Actions for CI/CD)
- They generate artifacts (app specs, workflows, scripts)
- They defer to docs only for edge cases
- They never handle credentials directly

**Key principle**: Skills only contain DO-specific knowledge the LLM doesn't have from training.

## Skill Structure

```text
skills/
├── skill-name/
│   ├── README.md      # Quick overview and when to use
│   ├── SKILL.md       # Concise router (150-350 lines)
│   ├── reference/     # Detailed docs (loaded on-demand)
│   ├── templates/     # (optional) Reusable templates
│   └── scripts/       # (optional) Helper scripts
```

## Skill Dependency Graph

```text
                    ┌─────────────┐
                    │  designer   │
                    └──────┬──────┘
                           │ produces .do/app.yaml
                           ▼
┌─────────────┐     ┌─────────────┐     ┌───────────────┐
│  migration  │────▶│ deployment  │────▶│troubleshooting│
└─────────────┘     └─────────────┘     └───────────────┘

    ┌──────────┐  ┌────────────┐  ┌────────────┐
    │ postgres │  │managed-db  │  │ networking │
    └──────────┘  └────────────┘  └────────────┘
         └──────────────┼──────────────┘
                        ▼
             (referenced by designer)
```

## Credential Safety

All skills follow this priority:

1. **GitHub Secrets** — Recommended, agent never sees credentials
2. **Bindable Variables** — `${db.DATABASE_URL}` injected automatically
3. **External Systems** — User manages entirely

## Resources

- [App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
- [App Spec Reference](https://docs.digitalocean.com/products/app-platform/reference/app-spec/)
- [doctl CLI](https://docs.digitalocean.com/reference/doctl/)
