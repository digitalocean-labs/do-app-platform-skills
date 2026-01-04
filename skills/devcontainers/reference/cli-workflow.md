# CLI-Only DevContainer Workflow

Complete workflow for running devcontainers via CLI (without VS Code/Cursor IDE features).

## Overview

When running devcontainers via `devcontainer up` from CLI, several features that IDEs handle automatically are **NOT available**. AI agents must handle these manually.

---

## 1. Port Forwarding (MANDATORY)

**Problem:** The `app` container doesn't expose ports to the host. VS Code/Cursor auto-forward ports, but CLI mode does not.

**Solution:** Create socat port-forwarding containers:

```bash
# Get the docker network name (usually <project>_devcontainer-network)
NETWORK=$(docker network ls --filter "name=devcontainer-network" --format "{{.Name}}" | head -1)

# Get the app container name
APP_CONTAINER=$(docker compose -f .devcontainer/docker-compose.yml ps app --format "{{.Name}}" | head -1)

# Forward each port your application needs (example: 3000, 3001, 3002)
docker run -d --rm --name port-forward-3000 \
  --network $NETWORK \
  -p 3000:3000 \
  alpine/socat tcp-listen:3000,fork,reuseaddr tcp-connect:$APP_CONTAINER:3000

docker run -d --rm --name port-forward-3001 \
  --network $NETWORK \
  -p 3001:3001 \
  alpine/socat tcp-listen:3001,fork,reuseaddr tcp-connect:$APP_CONTAINER:3001
```

**Cleanup:** Port forwarders auto-remove on stop (`--rm` flag), or manually:
```bash
docker rm -f port-forward-3000 port-forward-3001
```

---

## 2. Platform-Specific node_modules

**Problem:** If `node_modules` was installed on macOS/Windows host, native binaries (esbuild, sharp, etc.) won't work in the Linux container.

**Symptom:** Errors like `Error: The platform "linux" is incompatible with this module`

**Solution:** Always reinstall inside the container:
```bash
docker exec -w /workspaces/app $APP_CONTAINER bash -c "rm -rf node_modules && npm install"
```

**Prevention:** Add to `.gitignore` and don't commit `node_modules`.

---

## 3. Environment Variable Loading

**Problem:** `.env` files aren't auto-loaded when running npm scripts via `docker exec`.

**Solution:** Export variables before running commands:
```bash
# Pattern: source .env then run command
docker exec -w /workspaces/app $APP_CONTAINER bash -c \
  "export \$(cat .env | grep -v '^#' | xargs) && npm run dev"
```

**Alternative:** Create a wrapper script in the project:
```bash
# scripts/with-env.sh
#!/bin/bash
set -a
source .env
set +a
exec "$@"
```

Then use: `docker exec ... bash -c "./scripts/with-env.sh npm run dev"`

---

## 4. Application Service Startup

**Problem:** `devcontainer up` only starts infrastructure services (postgres, kafka, etc.). Application services must be started manually.

**Solution:** Discover and start services from `package.json` scripts:
```bash
# List available dev scripts
docker exec -w /workspaces/app $APP_CONTAINER bash -c "npm run 2>&1 | grep 'dev:'"

# Start services in background (adjust based on project)
docker exec -d -w /workspaces/app $APP_CONTAINER bash -c \
  "export \$(cat .env | grep -v '^#' | xargs) && npm run dev:api > /tmp/api.log 2>&1"

docker exec -d -w /workspaces/app $APP_CONTAINER bash -c \
  "export \$(cat .env | grep -v '^#' | xargs) && npm run dev:web > /tmp/web.log 2>&1"

# Check logs
docker exec $APP_CONTAINER cat /tmp/api.log
```

---

## 5. SSL/TLS Mismatch (Local vs Production)

**Problem:** Database migration scripts configured for production (SSL required) fail locally (no SSL).

**Symptom:** `Error: The server does not support SSL connections`

**Solutions:**

1. **Environment-aware connection:** Check `PG_SSLMODE` or detect local endpoints:
```typescript
const isLocal = process.env.DATABASE_URL?.includes('localhost') ||
                process.env.DATABASE_URL?.includes('postgres:');
const ssl = isLocal ? false : { rejectUnauthorized: false };
```

2. **Use psql directly for local migrations:**
```bash
# Run SQL directly against local postgres
docker exec -i $(docker compose -f .devcontainer/docker-compose.yml ps postgres --format "{{.Name}}") \
  psql -U postgres -d app -f /path/to/migration.sql
```

---

## Complete CLI Workflow Checklist

For AI agents testing via CLI, follow this order:

```bash
# 1. Start devcontainer
devcontainer up --workspace-folder .

# 2. Wait for infrastructure services
sleep 30  # Kafka/OpenSearch need time

# 3. Get container reference
APP_CONTAINER=$(docker compose -f .devcontainer/docker-compose.yml ps app --format "{{.Name}}" | head -1)
NETWORK=$(docker network ls --filter "name=devcontainer-network" --format "{{.Name}}" | head -1)

# 4. Reinstall dependencies (if needed)
docker exec -w /workspaces/app $APP_CONTAINER bash -c "rm -rf node_modules && npm install"

# 5. Set up port forwarding
docker run -d --rm --name pf-3000 --network $NETWORK -p 3000:3000 \
  alpine/socat tcp-listen:3000,fork,reuseaddr tcp-connect:$APP_CONTAINER:3000

# 6. Run migrations/setup
docker exec -w /workspaces/app $APP_CONTAINER bash -c \
  "export \$(cat .env | grep -v '^#' | xargs) && npm run db:migrate"

# 7. Start application services
docker exec -d -w /workspaces/app $APP_CONTAINER bash -c \
  "export \$(cat .env | grep -v '^#' | xargs) && npm run dev > /tmp/app.log 2>&1"

# 8. Verify services are accessible from host
curl http://localhost:3000/health

# 9. Cleanup when done
docker rm -f pf-3000
docker compose -f .devcontainer/docker-compose.yml stop
```

---

## Key Insights

1. **`devcontainer up` is always first** - Never run `docker compose up` directly without it
2. **Service profiles** - Only services in `COMPOSE_PROFILES` start with `devcontainer up`
3. **Health checks matter** - Kafka needs 60s+, OpenSearch needs 30-60s
4. **Test from inside container** - Network names (postgres, minio) only resolve inside the container
5. **AWS CLI fallback** - RustFS test tries uv -> pip -> standalone installer

---

## Helper Scripts

### Git Worktree Support (`init.sh`)

```bash
#!/bin/bash
# Git worktree support for devcontainers
gitdir="$(git rev-parse --git-common-dir)"
case $gitdir in
    /*) ;;
    *) gitdir="$PWD/$gitdir"
esac

project_name="$(basename "$PWD")"

sed -i.bak '/^GIT_COMMON_DIR=/d' ".devcontainer/.env" 2>/dev/null || true
sed -i.bak '/^COMPOSE_PROJECT_NAME=/d' ".devcontainer/.env" 2>/dev/null || true
rm -f ".devcontainer/.env.bak" 2>/dev/null || true

[ -n "$(tail -c 1 ".devcontainer/.env" 2>/dev/null)" ] && echo "" >> ".devcontainer/.env"

echo "COMPOSE_PROJECT_NAME=$project_name" >> ".devcontainer/.env"
echo "GIT_COMMON_DIR=$gitdir" >> ".devcontainer/.env"
```

### Post-Create Setup (`post-create.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "DevContainer Post-Create Setup"

# Fix ownership of credential directories
for dir in /home/vscode/.config /home/vscode/.claude /home/vscode/.codex; do
    if [ -d "$dir" ]; then
        sudo chown -R vscode:vscode "$dir"
    fi
done

echo "DevContainer Ready!"
```
