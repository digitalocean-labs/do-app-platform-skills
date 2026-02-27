# DigitalOcean App Platform Skills

DigitalOcean App Platform Skills is an open-source, production-focused skills repository for AI coding assistants that helps engineers design, migrate, deploy, and operate applications on DigitalOcean App Platform. It is for platform engineers, backend/full-stack developers, DevOps teams, and AI-agent workflow builders who want repeatable App Platform outcomes using structured skill playbooks.

## Overview

This repository provides modular “skills” that combine concise routing guidance (`SKILL.md`), deeper reference material, templates, and optional scripts for specific App Platform domains.

At a high level, the project enables a workflow where an AI assistant can:

1. Interpret an engineering goal (for example: “migrate my Heroku app to DigitalOcean”).
2. Load the most relevant skill(s).
3. Generate or refine concrete artifacts (for example: `.do/app.yaml`, workflow definitions, migration checklists, SQL scripts, troubleshooting reports).
4. Follow opinionated, secure defaults aligned with DigitalOcean App Platform practices.

### Repository Architecture

- `skills/` contains domain-specific skills (designer, deployment, migration, networking, postgres, troubleshooting, and more).
- `shared/` contains cross-cutting references and canonical schema/config artifacts (including `skill-schema.json`, regions/instance-size defaults, and platform patterns).
- `architecture/Docs/` contains project-level architecture, governance, quality strategy, and operational guidance.
- `scripts/` contains validation and analytics tooling for repository quality and usage analysis.
- `tests/` contains comprehensive Python test suites for workflows, validation logic, edge cases, and skill-specific behavior.

### Documentation Map

- Project architecture and governance: [architecture/Docs/README.md](architecture/Docs/README.md)
- Skill authoring model and standards: [architecture/Docs/skills-and-content-model.md](architecture/Docs/skills-and-content-model.md)
- Testing strategy: [TESTING.md](TESTING.md)
- Security policy: [SECURITY.md](SECURITY.md)

## Getting Started

### Prerequisites

Before using or contributing to this repository, ensure the following are available:

- **Operating system:** macOS, Linux, or Windows with a POSIX-compatible shell environment recommended.
- **Python:** `3.11+` (recommended `3.12`) for local scripts and test tooling.
- **DigitalOcean CLI (`doctl`):** `1.82.0+` (recommended `1.100.0+`) for App Spec v2 compatibility and platform operations.
- **Node.js:** `20+` (recommended `22 LTS`) when working with Node-based target applications in examples/workflows.
- **Git:** latest stable for repository workflows.
- **DigitalOcean account + API token:** required for authenticated platform operations and deployment testing.
- **Optional tooling:** `gh` (GitHub CLI), Docker, and PostgreSQL client utilities for deeper local validation workflows.

Recommended version check commands:

```bash
python3 --version
doctl version
node --version
git --version
```

### Installation

Clone the repository and set up a local development environment:

```bash
# 1) Clone repository
git clone https://github.com/digitalocean-labs/do-app-platform-skills.git
cd do-app-platform-skills

# 2) Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3) Install development dependencies
pip install -r requirements-dev.txt

# 4) Authenticate doctl (required for platform-integrated workflows)
doctl auth init

# 5) Run baseline validation/tests
python scripts/validate_skills.py
pytest -q
```

Install as an assistant skill source (example paths):

```bash
# Claude Code
mkdir -p ~/.claude/skills
ln -s "$PWD" ~/.claude/skills/do-app-platform-skills

# Codex
mkdir -p ~/.codex/skills
ln -s "$PWD" ~/.codex/skills/do-app-platform-skills

# Cursor
mkdir -p ~/.cursor/skills
ln -s "$PWD" ~/.cursor/skills/do-app-platform-skills
```

### Quick Start

Minimal workflow to begin using this project in an AI-assisted session:

1. Open your application repository in your AI coding assistant.
2. Ensure this repository is available as a skill source (cloned or linked).
3. Use a focused instruction that references App Platform skills explicitly.

Example prompt:

```text
Create a production-ready App Platform spec for my Python FastAPI API with managed PostgreSQL.
Use the DigitalOcean App Platform skills and output .do/app.yaml with secure defaults.
```

Expected output from a typical first run:

- Initial `.do/app.yaml` scaffold suitable for App Platform.
- Service/database wiring guidance.
- Follow-up recommendations for CI/CD and troubleshooting skill handoff.

## Usage

Use the repository by selecting the skill matching your current objective and chaining skills as work matures from design to operations.

### Typical Skill Selection Flow

- **Design / first App Spec:** start with `skills/designer/`
- **Migration from other platforms:** use `skills/migration/`
- **CI/CD and release workflows:** use `skills/deployment/`
- **Network, domains, CORS, VPC:** use `skills/networking/`
- **PostgreSQL and data-layer concerns:** use `skills/postgres/` and `skills/managed-db-services/`
- **Production diagnosis and incident response:** use `skills/troubleshooting/`

### Common Usage Patterns

- **Greenfield:** Designer → Deployment → Troubleshooting
- **Lift-and-shift migration:** Migration → Designer refinements → Deployment
- **Database-centric modernization:** Postgres/Managed DB → Designer integration → Deployment

### Validation and Quality Commands

```bash
# Validate repository skill content and structure
python scripts/validate_skills.py

# Run all tests
pytest -q

# Run targeted suites (examples)
pytest tests/test_migration -q
pytest tests/test_validation -q
```

For deeper system design and operating guidance, see:

- [architecture/Docs/developer-guide.md](architecture/Docs/developer-guide.md)
- [architecture/Docs/operations-runbook.md](architecture/Docs/operations-runbook.md)
- [architecture/Docs/testing-and-quality.md](architecture/Docs/testing-and-quality.md)

## Roadmap / Status

**Status: Active development and production-oriented hardening.**

Current maturity characteristics:

- Broad skill coverage across design, migration, deployment, networking, database, and troubleshooting domains.
- Established validation and test infrastructure with targeted edge-case coverage.
- Ongoing improvements to skill quality, reference depth, and workflow robustness.

Near-term roadmap themes:

- Expand and refine high-value migration/deployment templates.
- Strengthen schema and rule validation for safer agent output.
- Improve analytics-driven iteration on skill usefulness and discoverability.
- Continue quality and governance alignment for open-source collaboration at scale.

## Security

See [SECURITY.md](SECURITY.md) for how to report vulnerabilities.

## Contributing

We welcome community contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

Additional contributor references:

- [CLAUDE.md](CLAUDE.md)
- [SKILL.md](SKILL.md)
- [architecture/Docs/governance.md](architecture/Docs/governance.md)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file.

## Trademarks

DigitalOcean and related marks are trademarks of DigitalOcean.
