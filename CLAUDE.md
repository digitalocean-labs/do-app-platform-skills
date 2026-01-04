# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **knowledge/skill repository** for DigitalOcean App Platform, not a traditional application. It contains structured documentation and helper scripts designed to assist AI agents (like Claude) with DO App Platform deployments.

**No build system** - this is documentation with embedded scripts, not compiled code.

## Repository Structure

```
SKILL.md                    # Router - dispatches requests to appropriate sub-skills
shared/                     # Common reference data used by all skills
  ├── AppSpec-Reference.md  # Field-level syntax, constraints, regex patterns
  ├── bindable-variables.md # Database and component variable reference
  ├── credential-patterns.md# Secure credential handling patterns
  ├── instance-sizes.yaml   # Instance sizing and pricing
  ├── regions.yaml          # Available regions and platform mappings
  └── opinionated-defaults.yaml
skills/                     # 11 specialized sub-skills (designer, deployment, postgres, etc.)
  └── skill-name/
      ├── README.md         # Quick overview
      ├── SKILL.md          # Concise router (150-350 lines)
      ├── reference/        # Detailed documentation (loaded on-demand)
      ├── scripts/          # Helper bash/Python scripts
      └── templates/        # Reusable configurations
```

## Architecture

### Skill Routing
The root `SKILL.md` is a router with a decision tree that directs user requests to specialized skills:
- Natural language → trigger phrase matching → route to skill
- Skills are self-contained but reference shared data

### Key Skills
- **designer** - Natural language → App Spec generation
- **deployment** - GitHub Actions CI/CD setup
- **migration** - Platform migration (Heroku, AWS, Render, etc.)
- **postgres** - Database configuration and multi-tenant patterns
- **troubleshooting** - Debug and diagnostics

### Credential Handling (Critical)
Three-tier hierarchy enforced throughout:
1. **GitHub Secrets** (preferred) - encrypted, per-environment
2. **Bindable Variables** - auto-populated by DO for managed services
3. **Ephemeral** - generate → use → delete (never display passwords)

Reference: `shared/credential-patterns.md`

### Opinionated Defaults
All skills reference `shared/opinionated-defaults.yaml` for consistency:
- Instance: `apps-s-1vcpu-1gb`
- Region: `nyc`
- PostgreSQL: v16
- Python: 3.12 with `uv`
- Valkey (not Redis)
- VPC-only networking

## Required CLI Tools

These are prerequisites for users, not dev dependencies:
- `doctl` (DigitalOcean CLI)
- `gh` (GitHub CLI)
- `psql` (PostgreSQL client)
- Docker/Docker Compose

## AI Assistant Patterns

- Use `do_app_sandbox` SDK for shell access (not `doctl apps console`)
- Debug container: `ghcr.io/bikramkgupta/do-app-debug-container-python`
- Artifact handoff protocol: state what was created, suggest next skill

## Working with Skills

When modifying skills:
1. YAML frontmatter should only have `name` + `description` (description includes "Use when..." triggers)
2. Keep SKILL.md concise (150-350 lines), move detailed content to `reference/` subdirectory
3. Reference shared data rather than duplicating defaults
4. Follow credential-safe patterns for any scripts that handle secrets
