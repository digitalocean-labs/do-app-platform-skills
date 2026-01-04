# DigitalOcean App Platform Skills

Claude/Agent skills for DigitalOcean App Platform - deployment, migration, networking, database configuration, and troubleshooting.

## What Are Skills?

Skills are structured prompts and documentation that help AI assistants (like Claude) perform specialized tasks. Each skill contains domain knowledge, best practices, code patterns, and decision trees for a specific area of App Platform.

## Available Skills

| Skill | Description | Key Artifacts |
|-------|-------------|---------------|
| [**designer**](skills/designer/) | Natural language → production-ready App Spec | `.do/app.yaml` |
| [**deployment**](skills/deployment/) | GitHub Actions CI/CD and deployment workflows | `.github/workflows/` |
| [**migration**](skills/migration/) | Migrate from Heroku, AWS, Docker Compose, etc. | `.do/app.yaml`, checklist |
| [**networking**](skills/networking/) | Domains, routing, CORS, VPC, static IPs | App spec snippets |
| [**postgres**](skills/postgres/) | PostgreSQL configuration, security, multi-tenant | SQL scripts |
| [**managed-db-services**](skills/managed-db-services/) | MySQL, MongoDB, Valkey, Kafka, OpenSearch | App spec snippets |
| [**spaces**](skills/spaces/) | S3-compatible object storage | CORS config |
| [**ai-services**](skills/ai-services/) | Gradient AI serverless inference | App spec snippets |
| [**troubleshooting**](skills/troubleshooting/) | Debug running apps with container access | Diagnostic reports |
| [**devcontainers**](skills/devcontainers/) | Local development with production parity | `.devcontainer/` |

## Quick Start

### With Claude Code CLI

```bash
# Clone the repo
git clone https://github.com/bikramkgupta/do-app-platform-skills.git

# Reference skills in your prompts
claude "Using the designer skill from ./do-app-platform-skills/skills/designer/SKILL.md, create an app spec for my Python API with PostgreSQL"
```

### With Claude Projects

1. Create a new Claude Project
2. Add the relevant `SKILL.md` files to the project knowledge
3. Start chatting about your App Platform needs

### Direct Usage

Copy the contents of any `SKILL.md` file into your conversation with Claude as context.

## Use Cases

| Task | Skills to Use |
|------|---------------|
| Generate an App Spec from description | designer |
| Migrate from Heroku | migration |
| Set up subdomain routing with CORS | networking |
| Debug database connection issues | troubleshooting, networking |
| Configure CI/CD pipeline | deployment |
| Set up PostgreSQL with connection pooling | postgres |

## Philosophy

These skills are **opinionated playbooks**, not documentation replicas:

- They make decisions (VPC by default, GitHub Actions for CI/CD)
- They generate artifacts (app specs, workflows, scripts)
- They defer to docs only for edge cases
- They never handle credentials directly

**Key principle**: Skills only contain DO-specific knowledge the LLM doesn't have from training.

## Skill Structure

```
skills/
├── skill-name/
│   ├── README.md      # Quick overview and when to use
│   ├── SKILL.md       # Concise router (150-350 lines)
│   ├── reference/     # Detailed docs (loaded on-demand)
│   ├── templates/     # (optional) Reusable templates
│   └── scripts/       # (optional) Helper scripts
```

## Skill Dependency Graph

```
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

## Contributing

Contributions welcome! Please:

1. Follow the existing skill structure
2. Include practical examples and code snippets
3. Document limitations and gotchas
4. Test with Claude before submitting

## License

MIT License - See [LICENSE](LICENSE) for details.

## Resources

- [App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
- [App Spec Reference](https://docs.digitalocean.com/products/app-platform/reference/app-spec/)
- [doctl CLI](https://docs.digitalocean.com/reference/doctl/)
