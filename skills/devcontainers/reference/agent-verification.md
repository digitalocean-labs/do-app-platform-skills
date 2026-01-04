# Agent Verification Workflow

Complete CLI-based testing workflow for AI agents to verify devcontainer setups before handing off to users.

## Prerequisites

Install DevContainer CLI on the host:

```bash
npm install -g @devcontainers/cli
devcontainer --version
```

---

## End-to-End Test Flow

### Step 1: Pre-Flight Checks

```bash
# Verify Docker is running
docker info > /dev/null 2>&1 || { echo "Docker not running"; exit 1; }

# Verify workspace has devcontainer config
[ -f ".devcontainer/devcontainer.json" ] || { echo "Not a devcontainer workspace"; exit 1; }
```

### Step 2: Provision Environment (REQUIRED FIRST)

Always run `devcontainer up` first. This command:
- Builds/starts the app container
- Starts services defined in `COMPOSE_PROFILES`
- Runs post-create setup scripts
- Mounts the workspace properly

```bash
devcontainer up --workspace-folder .
```

> **Important:** This command is idempotent--if containers are running, it attaches. If down, it starts them.

### Step 3: Start Additional Services

If `COMPOSE_PROFILES` doesn't include all services (default is `app,postgres,minio`), start the rest:

```bash
# Start services not in COMPOSE_PROFILES
docker compose -f .devcontainer/docker-compose.yml \
  --profile mysql \
  --profile mongo \
  --profile valkey \
  --profile kafka \
  --profile opensearch \
  up -d

# Wait for health checks (Kafka and OpenSearch need 30-60s)
sleep 30

# Verify all services are healthy
docker compose -f .devcontainer/docker-compose.yml ps
```

**Alternative:** Modify `COMPOSE_PROFILES` to include all services upfront:
```json
"COMPOSE_PROFILES": "app,postgres,minio,mysql,mongo,valkey,kafka,opensearch"
```

### Step 4: Execute Tests Inside Container

Get the container name and run tests via `docker exec`:

```bash
# Get app container name
APP_CONTAINER=$(docker compose -f .devcontainer/docker-compose.yml ps app --format "{{.Name}}" | head -1)

# Run individual test scripts (recommended approach)
docker exec -w /workspaces/app $APP_CONTAINER bash .devcontainer/tests/test-postgres.sh
docker exec -w /workspaces/app $APP_CONTAINER bash .devcontainer/tests/test-rustfs.sh
docker exec -w /workspaces/app $APP_CONTAINER bash .devcontainer/tests/test-mysql.sh
docker exec -w /workspaces/app $APP_CONTAINER bash .devcontainer/tests/test-mongo.sh
docker exec -w /workspaces/app $APP_CONTAINER bash .devcontainer/tests/test-valkey.sh
docker exec -w /workspaces/app $APP_CONTAINER bash .devcontainer/tests/test-kafka.sh
docker exec -w /workspaces/app $APP_CONTAINER bash .devcontainer/tests/test-opensearch.sh
```

> **Why `docker exec` instead of `devcontainer exec`?** The `run-all-tests.sh` script uses `docker compose` internally to detect running services. If Docker isn't in the container's PATH (common with Docker-out-of-Docker), this fails. Running individual test scripts directly bypasses this issue.

### Step 5: Validate Results

Expected: **77 tests passed, 0 failed** (when all 7 services are running)

```bash
# Check test report if generated
cat .devcontainer/tests/TEST-REPORT.md
```

### Step 6: Graceful Shutdown

Free up ports and memory:

```bash
# Stop all containers
docker compose -f .devcontainer/docker-compose.yml stop

# Verify containers stopped
docker compose -f .devcontainer/docker-compose.yml ps
# Should show no running containers
```

---

## Automated Test Script

Use `agent-test.sh` to automate the entire workflow:

```bash
.devcontainer/tests/agent-test.sh
```

This script:
1. Runs pre-flight checks
2. Provisions the devcontainer
3. Starts all services
4. Executes all test scripts
5. Reports results with colored output
6. Shuts down containers
7. Returns exit code 0 (success) or 1 (failure)

---

## Self-Correction Rules

| Symptom | Action |
|---------|--------|
| "Port already allocated" | Stop conflicting local service (postgres, mysql, etc.) on host |
| "Command not found: psql" | Agent is running on host, not in container. Use `docker exec` |
| "Container timed out" | Check logs: `docker compose -f .devcontainer/docker-compose.yml logs <service>` |
| "Dev container not found" | Restart: `devcontainer up --workspace-folder .` |
| "Service not running" | Start it: `docker compose -f .devcontainer/docker-compose.yml --profile <service> up -d` |
| "docker: command not found" (in container) | Use `docker exec` from host instead of `devcontainer exec` |
| "Failed to install awscli" | Test script auto-falls back to AWS CLI v2 standalone installer |
| Kafka/OpenSearch unhealthy | Wait longer (60-90s) or check memory limits |

---

## Testing Services

The devcontainer includes a test suite to verify all services are working:

```bash
# Test all running services
.devcontainer/tests/run-all-tests.sh --all

# Test specific services
.devcontainer/tests/run-all-tests.sh postgres minio

# List available tests
.devcontainer/tests/run-all-tests.sh --list
```

---

## Key Testing Insights

1. **`devcontainer up` is always first** -- Never run `docker compose up` directly without it
2. **Service profiles** -- Only services in `COMPOSE_PROFILES` start with `devcontainer up`
3. **Health checks matter** -- Kafka needs 60s+, OpenSearch needs 30-60s
4. **Test from inside container** -- Network names (postgres, minio) only resolve inside the container
5. **AWS CLI fallback** -- RustFS test tries uv -> pip -> standalone installer

---

## Sample Test Output

```
=== DevContainer Agent Test ===
[OK] Docker is running
[OK] devcontainer.json found
[OK] Provisioning devcontainer...
[OK] Starting all service profiles...
[OK] Waiting for services to be healthy...

Running tests:
  [PASS] test-postgres.sh (11 tests)
  [PASS] test-mysql.sh (11 tests)
  [PASS] test-mongo.sh (11 tests)
  [PASS] test-valkey.sh (11 tests)
  [PASS] test-rustfs.sh (11 tests)
  [PASS] test-kafka.sh (11 tests)
  [PASS] test-opensearch.sh (11 tests)

=== Results ===
Total: 77 passed, 0 failed
Exit code: 0
```

---

## Debugging Failed Tests

### Check service logs

```bash
docker compose -f .devcontainer/docker-compose.yml logs postgres
docker compose -f .devcontainer/docker-compose.yml logs kafka
```

### Check container health

```bash
docker compose -f .devcontainer/docker-compose.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"
```

### Enter container interactively

```bash
docker exec -it $APP_CONTAINER bash
```

### Run test with verbose output

```bash
docker exec -w /workspaces/app $APP_CONTAINER bash -x .devcontainer/tests/test-postgres.sh
```
