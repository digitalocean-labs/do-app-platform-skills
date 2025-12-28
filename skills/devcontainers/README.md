---
name: dev-containers
description: Quick reference for dev-containers skill
---

# Dev Containers Skill

Part of the [App Platform Skills Package](../README.md).

## Purpose

Enable local development with production parity for DigitalOcean App Platform applications.

## Source of Truth

All devcontainer templates, docker-compose configurations, and test scripts live in the GitHub repo:

**`${DEVCONTAINER_REPO_URL}`** (default: https://github.com/bikramkgupta/do-app-devcontainer)

This skill provides **instructions on how to use them**, not duplicate copies.

> **Note:** `DEVCONTAINER_REPO_URL` is configured in the SKILL.md frontmatter. Override it there if the repo moves.

## Skill Files

```
skills/dev-containers/
├── SKILL.md        # Complete skill documentation (agent instructions)
└── README.md       # This file (quick reference)
```

## What the GitHub Repo Provides

```
.devcontainer/
├── devcontainer.json           # IDE configuration
├── docker-compose.yml          # All 7 backing services
├── init.sh                     # Git worktree support
├── post-create.sh              # Post-creation setup
├── docs/                       # Additional documentation
├── images/                     # Architecture diagrams
└── tests/                      # Service connectivity tests (77 tests)
    ├── agent-test.sh           # E2E validation for agents
    ├── run-all-tests.sh        # Master test runner
    └── test-*.sh               # Individual service tests
```

## Quick Usage

1. Clone the repo: `git clone --depth 1 ${DEVCONTAINER_REPO_URL}.git /tmp/ref`
2. Copy to project: `cp -r /tmp/ref/.devcontainer /path/to/your-project/`
3. Customize `COMPOSE_PROFILES` in `devcontainer.json`
4. Open in VS Code/Cursor → "Reopen in Container"

## Available Services

| Service | Profile | Port | Connection |
|---------|---------|------|------------|
| PostgreSQL 18 | `postgres` | 5432 | `postgresql://postgres:password@postgres:5432/app` |
| MySQL 8 | `mysql` | 3306 | `mysql://mysql:mysql@mysql:3306/app` |
| MongoDB 8 | `mongo` | 27017 | `mongodb://mongodb:mongodb@mongo:27017/app?authSource=admin` |
| Valkey 8 | `valkey` | 6379 | `redis://valkey:6379` |
| Kafka 7.7 | `kafka` | 9092 | `kafka:9092` |
| OpenSearch 3.0 | `opensearch` | 9200 | `http://opensearch:9200` |
| RustFS (S3) | `minio` | 9000/9001 | `http://minio:9000` |

## Agent Verification

After generating devcontainer files, agents should verify the setup works:

```bash
# Quick E2E test from host (after copying .devcontainer from repo)
.devcontainer/tests/agent-test.sh
```

This script:
1. Runs pre-flight checks (Docker, workspace)
2. Provisions the devcontainer via `devcontainer up`
3. Starts all 7 services
4. Executes 77 connectivity and CRUD tests
5. Reports results with colored output
6. Shuts down containers

See SKILL.md for detailed agent verification workflow.

## Related Skills

- **designer** — Create production app specs
- **deployment** — Set up CI/CD with GitHub Actions
- **hot-reload** — Cloud development without rebuild cycles
