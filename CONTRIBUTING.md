# Contributing to App Platform Skills

Thank you for your interest in contributing! This document provides guidelines for contributions.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Skill Structure](#skill-structure)
- [Writing Skills](#writing-skills)
- [Writing Scripts](#writing-scripts)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

This project follows the [DigitalOcean Community Code of Conduct](https://www.digitalocean.com/community/pages/code-of-conduct).

---

## Getting Started

### Prerequisites

- Python 3.11+
- `doctl` CLI installed and authenticated
- `gh` CLI for GitHub operations

### Setup

```bash
git clone https://github.com/digitalocean/do-app-platform-skills.git
cd do-app-platform-skills

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

---

## Skill Structure

Every skill follows this structure:

```
skills/
└── skill-name/
    ├── README.md           # Quick overview (required)
    ├── SKILL.md            # Main skill file (required)
    ├── reference/          # Detailed documentation
    ├── scripts/            # Helper scripts
    └── templates/          # Reusable configurations
```

### SKILL.md Requirements

```yaml
---
name: skill-name
description: Brief description. Use when [trigger phrases].
---
```

- Keep to 150-350 lines
- Include Quick Decision tree
- Link to reference files for details

---

## Writing Skills

### Philosophy

Skills are **opinionated playbooks**, not documentation replicas:

1. **Make decisions** — Recommend the best option
2. **Generate artifacts** — Produce `.do/app.yaml`, SQL scripts
3. **Reference, don't duplicate** — Use `shared/` for common data

### Credential Handling

**Never handle credentials directly**. Follow the hierarchy:

1. **GitHub Secrets** (preferred)
2. **Bindable Variables** (DO-managed)
3. **Ephemeral** (generate → use → delete)

```python
# ❌ WRONG
print(f"Password: {password}")

# ✅ CORRECT
subprocess.run(["gh", "secret", "set", "DB_URL", "--env", env])
```

---

## Writing Scripts

### Python Requirements

1. Use type hints
2. Include docstrings
3. Handle errors gracefully
4. Use shared configuration from `shared/`

```python
def detect_platform(repo_path: str) -> Dict[str, Any]:
    """Detect source platform from repository.
    
    Args:
        repo_path: Path to repository
        
    Returns:
        Detection result with platform and confidence
    """
```

### Bash Requirements

```bash
#!/bin/bash
set -euo pipefail  # Strict mode

# Never echo secrets
```

---

## Testing

### All PRs Must Include Tests

```
tests/
├── conftest.py
├── test_migration/
├── test_postgres/
└── test_shared/
```

### Running Tests

```bash
pytest tests/ -v
pytest tests/ --cov=skills
```

---

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally
- [ ] YAML files validated
- [ ] No credentials in code
- [ ] Documentation updated

### PR Requirements

1. One approval required
2. All CI checks must pass
3. Security review for credential changes

---

## Style Guidelines

| Type | Convention | Example |
|------|------------|---------|
| Directories | kebab-case | `managed-db-services` |
| Python files | snake_case | `detect_platform.py` |
| Python classes | PascalCase | `PlatformDetector` |
| Environment vars | SCREAMING_SNAKE | `DATABASE_URL` |

### Commit Messages

```
type(scope): description

feat(migration): add Railway detection
fix(postgres): handle special characters
docs(designer): add monorepo example
```

---

## Questions?

Open an issue or join [DigitalOcean Community](https://www.digitalocean.com/community).
