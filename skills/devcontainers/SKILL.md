---
name: devcontainers
description: Set up local development environments with production parity for DigitalOcean App Platform. Use when setting up local dev, adding devcontainer to a project, running App Platform apps locally, or configuring backing services (Postgres, Redis, Kafka, S3).
---

# Dev Containers Skill

Set up local development environments with production parity for DigitalOcean App Platform applications.

**Primary value**: 30-second feedback loops instead of 7-minute deploy cycles.

## Quick Decision

```
What do you need?
├── New project setup → Workflow 1
├── Existing App Platform app → Workflow 2
└── CLI-only testing (no IDE) → See cli-workflow.md
```

---

## Quick Start: Clone and Copy

```bash
# Clone the reference devcontainer
git clone --depth 1 https://github.com/bikramkgupta/do-app-devcontainer.git /tmp/devcontainer-ref

# Copy to your project
cp -r /tmp/devcontainer-ref/.devcontainer /path/to/your-project/

# Clean up
rm -rf /tmp/devcontainer-ref
```

Then customize `COMPOSE_PROFILES` in `.devcontainer/devcontainer.json`:
```json
"containerEnv": {
  "COMPOSE_PROFILES": "app,postgres,minio"
}
```

---

## Available Profiles

| Profile | Service | Use When |
|---------|---------|----------|
| `postgres` | PostgreSQL 18 | SQL database |
| `mysql` | MySQL 8 | MySQL database |
| `mongo` | MongoDB 8 | Document database |
| `valkey` | Valkey 8 | Redis-compatible cache |
| `kafka` | Confluent Kafka 7.7 | Message streaming |
| `minio` | RustFS | S3-compatible storage |
| `opensearch` | OpenSearch 3.0 | Full-text search |

---

## Connection Strings

| Service | Connection String |
|---------|-------------------|
| PostgreSQL | `postgresql://postgres:password@postgres:5432/app` |
| MySQL | `mysql://mysql:mysql@mysql:3306/app` |
| MongoDB | `mongodb://mongodb:mongodb@mongo:27017/app?authSource=admin` |
| Valkey | `redis://valkey:6379` |
| Kafka | `kafka:9092` |
| RustFS | `http://minio:9000` (creds: `rustfsadmin/rustfsadmin`) |
| OpenSearch | `http://opensearch:9200` |

**Inside container**: Use service names (e.g., `postgres:5432`)
**From host**: Use `docker compose port` to find mapped ports

---

## Workflow 1: New Project Setup

**Trigger:** "I'm building a [language] app with [services]"

1. Copy `.devcontainer/` from reference repo (see Quick Start)
2. Set `COMPOSE_PROFILES` based on required services
3. Create `env-devcontainer.example` with connection strings
4. Open in VS Code/Cursor → "Reopen in Container"

**devcontainer.json template:**
```json
{
  "name": "App Platform Dev Environment",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspaces/app",
  "features": {
    "ghcr.io/devcontainers/features/github-cli:1": {},
    "ghcr.io/devcontainers/features/node:1": {},
    "ghcr.io/devcontainers/features/python:1": {},
    "ghcr.io/devcontainers-extra/features/uv:1": {},
    "ghcr.io/devcontainers-extra/features/digitalocean-cli:1": {},
    "ghcr.io/anthropics/devcontainer-features/claude-code:1": {},
    "ghcr.io/devcontainers/features/docker-outside-of-docker:1": {}
  },
  "containerEnv": {
    "COMPOSE_PROFILES": "app,postgres"
  },
  "initializeCommand": "cd \"${localWorkspaceFolder}\" && bash .devcontainer/init.sh",
  "postCreateCommand": ".devcontainer/post-create.sh",
  "remoteUser": "vscode",
  "shutdownAction": "stopCompose"
}
```

---

## Workflow 2: Add to Existing App Platform App

**Trigger:** "I have an App Platform app, help me run it locally"

1. Read `.do/app.yaml` to detect services
2. Map App Platform → local containers:

| App Platform | Local Profile |
|--------------|---------------|
| `databases[].engine: PG` | `postgres` |
| `databases[].engine: MYSQL` | `mysql` |
| `databases[].engine: MONGODB` | `mongo` |
| `databases[].engine: REDIS` | `valkey` |
| Spaces attachment | `minio` |

3. Generate environment mapping:
```bash
# Production (App Platform injects)
# DATABASE_URL=${db.DATABASE_URL}

# Local Development
DATABASE_URL=postgresql://postgres:password@postgres:5432/app
```

---

## Environment Template

```bash
# env-devcontainer.example

# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/app

# Cache
REDIS_URL=redis://valkey:6379

# S3-compatible storage (RustFS)
SPACES_ENDPOINT=http://minio:9000
SPACES_KEY_ID=rustfsadmin
SPACES_SECRET_KEY=rustfsadmin
SPACES_BUCKET_NAME=my-app-local
SPACES_FORCE_PATH_STYLE=true
```

---

## What You Get from Reference Repo

```
.devcontainer/
├── devcontainer.json           # IDE configuration
├── docker-compose.yml          # All 7 backing services
├── init.sh                     # Git worktree support
├── post-create.sh              # Post-creation setup
├── .env                        # Generated (gitignored)
└── tests/                      # Service connectivity tests
    ├── agent-test.sh           # E2E validation
    ├── run-all-tests.sh        # Master test runner
    └── test-*.sh               # Individual service tests
```

---

## Testing Services

```bash
# Test all running services
.devcontainer/tests/run-all-tests.sh --all

# Test specific services
.devcontainer/tests/run-all-tests.sh postgres minio

# List available tests
.devcontainer/tests/run-all-tests.sh --list
```

---

## Health Check Timing

| Service | Ready Time |
|---------|------------|
| PostgreSQL, MySQL, MongoDB, Valkey, RustFS | <10s |
| Kafka | 60s+ (KRaft init) |
| OpenSearch | 30-60s (JVM warmup) |

---

## Quick Troubleshooting

| Issue | Fix |
|-------|-----|
| Port conflict | Config uses dynamic ports (`127.0.0.1:0:PORT`), should not conflict |
| Git commands fail | Rebuild container to re-run `init.sh` |
| Kafka slow to start | Wait 60s+, check: `docker compose logs kafka` |
| OpenSearch OOM | Increase heap: `OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g` |
| Permission denied | Run: `sudo chown -R vscode:vscode /home/vscode` |

---

## Reference Files

| File | Content |
|------|---------|
| [service-templates.md](reference/service-templates.md) | All 7 docker-compose service blocks |
| [s3-storage-patterns.md](reference/s3-storage-patterns.md) | RustFS setup, local vs production |
| [agent-verification.md](reference/agent-verification.md) | CLI testing workflow for AI agents |
| [cli-workflow.md](reference/cli-workflow.md) | Port forwarding, env loading, startup |
| [language-configurations.md](reference/language-configurations.md) | Node, Python, Go hot reload configs |

---

## Limitations

This skill does **not** handle:
- Cloud deployment → use **deployment** skill
- Production app specs → use **designer** skill
- Database migrations → bring your own migration tool
- DigitalOcean Functions → not containerizable
- SSL/TLS → local uses HTTP; production handles SSL automatically

---

## Integration with Other Skills

- **→ designer**: Design production app spec after local testing
- **→ deployment**: Set up GitHub Actions CI/CD
- **→ postgres**: Configure managed database permissions
- **→ troubleshooting**: Debug production issues

---

## External References

- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [Docker Compose](https://docs.docker.com/compose/)
- [Reference Implementation](https://github.com/bikramkgupta/do-app-devcontainer)
