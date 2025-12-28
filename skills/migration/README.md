# Migration Skill

**Migrate existing applications from other platforms to DigitalOcean App Platform.**

## Quick Start

```bash
"Migrate my app from Heroku to App Platform: https://github.com/myorg/myapp"
```

## Supported Platforms

| Platform | Support |
|----------|---------|
| Heroku | ✅ Full |
| Docker Compose | ✅ Full |
| Render | ✅ Full |
| Railway | ✅ Full |
| Fly.io | ✅ Full |
| AWS ECS | ⚠️ Partial |
| AWS App Runner | ⚠️ Partial |

## What It Does

1. **Analyzes** your existing app configuration
2. **Maps** services, databases, and dependencies to App Platform equivalents
3. **Identifies** what can't be automatically migrated (asks for your input)
4. **Refactors** code to remove platform-specific dependencies
5. **Generates** App Platform spec and migration checklist

## Philosophy

This skill is an **honest partner**:
- Maps what it can confidently
- Clearly reports what it cannot map
- Asks for decisions when multiple options exist
- Never guesses or skips items silently

## Output

- `.do/app.yaml` — App Platform specification
- `.do/deploy.template.yaml` — Deploy button template
- `MIGRATION.md` — Checklist with mapping status
- Code changes in migration branch(es)

## Next Steps

After migration, use:
- **deployment skill** → Set up CI/CD with GitHub Actions
- **postgres skill** → Complex database setup
- **devcontainers skill** → Local development environment

## See Also

- [Full SKILL.md](./SKILL.md) for detailed workflows
- [Migration Brief](../../04-migration-brief.md) for product requirements
