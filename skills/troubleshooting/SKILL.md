---
name: app-platform-troubleshooting
description: Debug running App Platform applications by accessing containers, analyzing logs, running diagnostics, and applying fixes
version: 1.0.0
author: Bikram Gupta
github_repo: https://github.com/bikramkgupta/do-app-sandbox
triggers:
  - "debug"
  - "troubleshoot"
  - "broken"
  - "failing"
  - "error"
  - "crash"
  - "502"
  - "503"
  - "logs"
  - "health check"
  - "container access"
  - "why is my app"
  - "app won't start"
  - "connection refused"
  - "out of memory"
dependencies:
  required:
    - doctl (authenticated)
    - python 3.10+
    - do-app-sandbox SDK
  optional:
    - jq (for JSON parsing)
    - psql (for database testing)
---

# App Platform Troubleshooting Skill

## Philosophy

**Goal**: Transform the painful debugging cycle into rapid diagnosis and fix.

Traditional debugging:
```
See error → Check logs in console → Guess problem → Change code → Push → Wait 5-7 min → Check → Repeat
```

With this skill:
```
See error → Diagnose (logs/shell) → Identify root cause → Apply fix → Verify → Commit proper fix
```

**Key Principles**:
1. **Diagnose before fixing** — Understand the root cause, don't guess
2. **Test before committing** — Verify fixes work before permanent changes
3. **Minimize cycles** — Avoid wasting 5-7 minute deploy cycles on guesses
4. **Escalate appropriately** — Know when to involve support

---

## Decision Tree: How to Troubleshoot

```
┌─────────────────────────────────────────────────────────────────┐
│                     TROUBLESHOOTING REQUEST                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │ Is the app deployed and │
                │ has running containers? │
                └─────────────────────────┘
                      │           │
                  YES │           │ NO (build/deploy failed)
                      ▼           ▼
        ┌─────────────────┐    ┌─────────────────────────┐
        │ Can we access   │    │ LOGS-ONLY MODE          │
        │ the container   │    │ • Fetch build logs      │
        │ shell?          │    │ • Fetch deploy logs     │
        │                 │    │ • Analyze error codes   │
        └─────────────────┘    │ • Fix code, redeploy    │
              │       │        └─────────────────────────┘
          YES │       │ NO
              ▼       ▼
    ┌─────────────┐  ┌─────────────────────────┐
    │ LIVE MODE   │  │ LOGS-ONLY MODE          │
    │ • SDK exec  │  │ • Fetch runtime logs    │
    │ • File ops  │  │ • Fetch crash logs      │
    │ • Diagnostics│  │ • Pattern matching     │
    │ • Hot fixes │  │ • Fix code, redeploy   │
    └─────────────┘  └─────────────────────────┘
```

---

## Prerequisites

### Required: doctl CLI

```bash
# Check if installed and authenticated
doctl account get

# If not authenticated
doctl auth init
```

### Required: do-app-sandbox SDK (for live troubleshooting)

```bash
# Install with uv (preferred)
uv pip install do-app-sandbox

# Or with pip
pip install do-app-sandbox
```

### Getting App and Component Information

```bash
# List all apps
doctl apps list --format ID,Spec.Name

# Get component names for an app
doctl apps get <app_id> -o json | jq -r '.[0].spec.services[].name, .[0].spec.workers[].name, .[0].spec.jobs[].name'

# Get deployment status
doctl apps get <app_id> -o json | jq -r '.[0].active_deployment.phase'
# Phases: PENDING_BUILD, BUILDING, PENDING_DEPLOY, DEPLOYING, ACTIVE, ERROR, CANCELED
```

### SDK Shell Prompt Compatibility

**CRITICAL**: The SDK uses `pexpect` to detect when commands complete by matching shell prompt patterns. If your container's prompt doesn't match the expected patterns, the SDK will timeout or hang.

#### Supported Prompt Formats

The SDK recognizes these prompt patterns (from `executor.py`):

| Pattern | Example | Source |
|---------|---------|--------|
| `sandbox@host:/path$ ` | `sandbox@app-abc123:/app$ ` | Default sandbox images |
| `devcontainer@host:/path$ ` | `devcontainer@workspace:/home$ ` | DevContainer images |
| `user@host:/path$ ` or `#` | `root@container:/# ` | Standard Linux prompts |

#### Diagnosing Prompt Mismatch

If SDK commands timeout but the container is running:

```bash
# Connect directly to see the actual prompt
doctl apps console <app_id> <component>

# Observe what prompt appears, for example:
# - "myapp> "           (custom prompt - NOT supported)
# - "node@abc123:/$ "   (supported)
# - "# "                (minimal root - may not match)
```

#### Fixing Prompt Mismatch

**Option 1**: Modify the SDK's `executor.py` to add your pattern:

```python
# In do_app_sandbox/executor.py
PROMPT_PATTERNS = [
    re.compile(rb"sandbox@[^:]+:[^$]+\$ "),
    re.compile(rb"devcontainer@[^:]+:[^$]+\$ "),
    re.compile(rb"[a-zA-Z0-9_-]+@[^:]+:[^$#]+[$#] "),
    re.compile(rb"myapp> "),  # Add your custom pattern
]
```

**Option 2**: Modify your container to use a standard prompt format in the Dockerfile or entrypoint:

```bash
# Set standard PS1 prompt
export PS1='\u@\h:\w\$ '
```

#### When This Happens

- Connecting to custom-built images (not sandbox/devcontainer)
- Containers with minimal shells (busybox, alpine with ash)
- Apps that modify PS1 for branding
- Containers running as unusual users

---

## Mode 1: Live Troubleshooting (Shell Access)

When the container is running, use the SDK for direct access.

### Connect to Running App

```python
from do_app_sandbox import Sandbox

# Connect to existing app (works with ANY App Platform app)
app = Sandbox.get_from_id(
    app_id="ea1525eb-7e39-4fc5-91d4-5c8dc187581f",
    component="web"  # Your component name (service/worker)
)

# Verify connection
result = app.exec("whoami")
print(f"Connected as: {result.stdout.strip()}")
```

### Common Diagnostic Commands

```python
# System overview
app.exec("uname -a")                    # System info
app.exec("free -m")                     # Memory usage
app.exec("df -h")                       # Disk usage
app.exec("ps aux")                      # Running processes
app.exec("top -b -n 1 | head -20")      # CPU/memory by process

# Environment check
app.exec("env | sort")                  # All environment variables
app.exec("echo $PORT")                  # Check PORT is set
app.exec("echo $DATABASE_URL")          # Check DB connection string

# Network diagnostics
app.exec("netstat -tlnp 2>/dev/null || ss -tlnp")  # Listening ports
app.exec("curl -v localhost:8080/health")           # Health check
app.exec("curl -I localhost:8080")                  # HTTP headers

# Application logs (if app writes to files)
app.exec("tail -100 /var/log/app.log 2>/dev/null || echo 'No log file'")
app.exec("ls -la /app")                 # Application files
```

### File Operations

```python
# Read a file from container
content = app.filesystem.read_file("/app/config.py")
print(content)

# List directory
files = app.filesystem.list_dir("/app")
for f in files:
    print(f"  {f.name} ({'dir' if f.is_dir else 'file'})")

# Download file for local analysis
app.filesystem.download_file("/app/logs/error.log", "./error.log")

# Upload a diagnostic script
app.filesystem.upload_file("./diagnostic.sh", "/tmp/diagnostic.sh")
app.exec("chmod +x /tmp/diagnostic.sh && /tmp/diagnostic.sh")
```

### Database Connectivity Testing

> **TIP**: If you're unsure whether the issue is infrastructure or application code, consider the **Debug Container** (see below) first. It deploys in ~30-45 seconds with all diagnostic tools pre-installed and isolates the problem definitively.

```python
# Check if DATABASE_URL is set
result = app.exec("echo $DATABASE_URL")
db_url = result.stdout.strip()
if not db_url:
    print("ERROR: DATABASE_URL not set - database not attached?")
else:
    print(f"DATABASE_URL: {db_url[:50]}...")  # Truncate for security

# Test PostgreSQL connection
result = app.exec("pg_isready -d \"$DATABASE_URL\" 2>&1 || echo 'pg_isready not found or failed'")
print(result.stdout)

# Python-based DB test
db_test_script = '''
import os
try:
    import psycopg2
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("SELECT version()")
    print(f"✓ Connected: {cur.fetchone()[0][:50]}")
    cur.close()
    conn.close()
except ImportError:
    print("✗ psycopg2 not installed")
except Exception as e:
    print(f"✗ Connection failed: {e}")
'''
app.filesystem.write_file("/tmp/db_test.py", db_test_script)
result = app.exec("python3 /tmp/db_test.py")
print(result.stdout)
```

### Hot Fix Workflow

**CRITICAL**: Hot fixes are TEMPORARY. Always commit proper fixes to your repo.

```python
# 1. Download the problematic file
app.filesystem.download_file("/app/src/buggy.py", "./buggy.py")

# 2. Analyze and create fix (agent does this)
# ... edit ./buggy.py locally ...

# 3. Upload patched file
app.filesystem.upload_file("./fixed.py", "/app/src/buggy.py")

# 4. Restart the application process
# For Python apps using gunicorn:
result = app.exec("pkill -HUP gunicorn 2>/dev/null || echo 'No gunicorn found'")

# For Node.js apps:
result = app.exec("pkill -HUP node 2>/dev/null || echo 'No node found'")

# 5. Verify the fix
import time
time.sleep(2)
result = app.exec("curl -s localhost:8080/health")
print(f"Health check: {result.stdout}")

# 6. REMIND USER TO COMMIT
print("⚠️  IMPORTANT: This is a temporary fix!")
print("⚠️  Commit the fix to your repository and deploy properly.")
```

---

## Mode 2: Logs-Only Troubleshooting

When shell access isn't available or the app is crashing.

### Fetch Logs with doctl

```bash
# Runtime logs (most common)
doctl apps logs <app_id> <component> --type run

# Follow logs in real-time
doctl apps logs <app_id> <component> --type run --follow

# Build logs (if build failed)
doctl apps logs <app_id> <component> --type build

# Deploy logs (if deploy failed)
doctl apps logs <app_id> <component> --type deploy

# Crash logs (after container crash)
doctl apps logs <app_id> --type=run_restarted

# Crash logs for specific component
doctl apps logs <app_id> <component> --type=run_restarted
```

### Log Analysis Patterns

When analyzing logs, look for these patterns:

| Pattern | Likely Cause | Quick Investigation |
|---------|--------------|---------------------|
| `bind: address already in use` | Port conflict or not using $PORT | Check if app uses PORT env var |
| `ECONNREFUSED 127.0.0.1:5432` | Database not attached or wrong URL | Check DATABASE_URL env |
| `Module not found` / `ModuleNotFoundError` | Missing dependency | Check requirements.txt/package.json |
| `Permission denied` | File permissions | Check file ownership/chmod |
| `OOMKilled` / exit code 137 | Out of memory | Upgrade instance size |
| `Health check failed` | /health returns non-200 or timeout | Test health endpoint locally |
| `SIGTERM` / exit code 143 | Graceful shutdown (normal) | Handle SIGTERM in app |
| `EACCES` | Network permission | Usually localhost vs 0.0.0.0 |
| `SSL SYSCALL error` | DB SSL configuration | Check sslmode in connection string |
| `ETIMEOUT` | Network/DNS timeout | Check VPC configuration |

---

## Error Code Reference

### Build Errors

| Error Type | Exit Code | Cause | Fix |
|------------|-----------|-------|-----|
| BuildJobFailed | - | Build script failed | Check build logs for specific error |
| BuildJobExitNonZero | varies | Build command returned error | Fix build command or dependencies |
| BuildJobTimeout | - | Build took > 60 min | Optimize build or split components |
| BuildJobOutOfMemory | - | Build OOM | Reduce build dependencies or upgrade |

### Container Exit Codes

| Code | Signal | Meaning | Action |
|------|--------|---------|--------|
| 0 | - | Clean exit (but shouldn't exit) | App started then stopped - check if designed to stay running |
| 1 | - | General error | Check logs for exception/error |
| 2 | - | Shell builtin misuse | Check entrypoint syntax |
| 126 | - | Command not executable | Check file permissions (chmod +x) |
| 127 | - | Command not found | Missing dependency or PATH issue |
| 134 | SIGABRT | Abort (crash/assertion) | Check app error handling |
| 137 | SIGKILL | Killed (usually OOM) | Increase memory or optimize app |
| 139 | SIGSEGV | Segmentation fault | Debug memory access issues |
| 143 | SIGTERM | Graceful shutdown | Normal during redeploy - handle SIGTERM |
| 217 | - | Python fatal error | Check Python logs for corruption |
| 255 | - | Unknown/out-of-range | Unhandled exception - check logs |

### Deploy Errors

| Error Type | Cause | Fix |
|------------|-------|-----|
| ContainerCommandNotExecutable | Run command doesn't exist | Clear custom run command, test in console |
| ContainerExitNonZero | App crashed on start | Check logs, fix startup code |
| ContainerHealthChecksFailed | Health endpoint not responding | Verify /health returns 200, check PORT |
| ContainerOutOfMemory | App OOM on startup | Increase instance size or optimize |

---

## Health Check Debugging

### Default Health Check Behavior

- App Platform checks HTTP on port 8080 (or configured port)
- Default path: `/` (can be customized to `/health`)
- Must return 2xx status code
- Timeout applies (default varies)

### Common Health Check Issues

**1. App not listening on correct port**
```python
# Verify PORT environment variable
result = app.exec("echo $PORT")
print(f"PORT env: {result.stdout.strip()}")

# Check what's actually listening
result = app.exec("netstat -tlnp 2>/dev/null || ss -tlnp")
print(result.stdout)
```

**2. App listening on localhost instead of 0.0.0.0**
```python
# This is a common mistake - check the listening address
result = app.exec("ss -tlnp | grep ':8080'")
# Should show: 0.0.0.0:8080 or *:8080
# NOT: 127.0.0.1:8080
```

**3. Health endpoint returns non-200**
```python
result = app.exec("curl -v localhost:8080/health")
print(result.stdout)
print(result.stderr)  # curl verbose output goes to stderr
```

### Health Check Configuration

```yaml
# In app spec
health_check:
  http_path: /health
  port: 8080
  initial_delay_seconds: 30  # Delay before first check
  period_seconds: 10         # Interval between checks
  timeout_seconds: 5         # Timeout per check
  success_threshold: 1       # Consecutive successes to be healthy
  failure_threshold: 5       # Consecutive failures to be unhealthy

# Optional: Liveness check (auto-restarts on failure)
liveness_health_check:
  http_path: /health
  port: 8080
  initial_delay_seconds: 10
  period_seconds: 10
  timeout_seconds: 5
  success_threshold: 1
  failure_threshold: 6
```

---

## Networking and Routing Issues

> **For comprehensive networking documentation, see the [networking skill](../networking/SKILL.md).**

### DNS Issues

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Domain not resolving | `dig example.com` or `nslookup example.com` | Check CNAME/A record at registrar, allow up to 72h propagation |
| SSL certificate error | Check CAA records: `dig example.com CAA` | Add both `letsencrypt.org` and `pki.goog` to CAA records |
| Wildcard domain not working | Check TXT validation in DO console | Add TXT record provided by DO, re-validate |
| Domain shows "pending" | DNS not propagated or wrong records | Verify nameservers or CNAME, wait for propagation |

**Diagnosis commands:**

```bash
# Check DNS resolution
dig example.com
nslookup example.com

# Check CAA records
dig example.com CAA

# Check nameservers
dig example.com NS

# Test from container
doctl apps console <app_id> <component>
# Inside container:
nslookup example.com
curl -I https://example.com
```

### CORS Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `No 'Access-Control-Allow-Origin' header` | Origin not in `allow_origins` | Add exact or regex pattern to `cors.allow_origins` |
| `Method not allowed in CORS` | Method not in `allow_methods` | Add method (e.g., `PUT`, `DELETE`) to `cors.allow_methods` |
| `Preflight request fails` | OPTIONS not allowed | Add `OPTIONS` to `cors.allow_methods` |
| `Credentials not supported` | Using regex with `allow_credentials` | Use exact origins only with `allow_credentials: true` |
| `Request header not allowed` | Custom header not in list | Add header to `cors.allow_headers` |

**Debugging CORS:**

```bash
# Test CORS preflight
curl -X OPTIONS https://api.example.com/endpoint \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization" \
  -v

# Check response headers
curl -I https://api.example.com/endpoint \
  -H "Origin: https://app.example.com"
```

**CORS config example:**

```yaml
ingress:
  rules:
    - component:
        name: api
      match:
        path:
          prefix: /api
      cors:
        allow_origins:
          - exact: https://app.example.com
          - exact: https://admin.example.com
        allow_methods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS  # Required for preflight
        allow_headers:
          - Content-Type
          - Authorization
        allow_credentials: true  # Requires exact origins
```

### Routing Issues

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Wrong component serves request | Ingress rule order issue | Put more specific rules first |
| Path rewrite not working | Wrong rewrite syntax | Use `component.rewrite` field |
| Subdomain not routing | Missing authority match | Add `match.authority.exact` field |
| 404 on valid path | Missing ingress rule | Add rule for the path |
| Redirect not working | Wrong redirect syntax | Check `redirect.authority` and `redirect.uri` |

**Debugging routing:**

```bash
# Test which component serves a request
curl -I https://api.example.com/endpoint
curl -I https://app.example.com/dashboard

# Check app spec routing
doctl apps spec get <app_id> | grep -A 20 "ingress:"
```

**Common routing mistakes:**

```yaml
# WRONG: Less specific rule first (catches everything)
ingress:
  rules:
    - component:
        name: frontend
      match:
        path:
          prefix: /       # This catches /api too!
    - component:
        name: api
      match:
        path:
          prefix: /api    # Never reached

# CORRECT: More specific rules first
ingress:
  rules:
    - component:
        name: api
      match:
        path:
          prefix: /api    # Specific path first
    - component:
        name: frontend
      match:
        path:
          prefix: /       # Catch-all last
```

### VPC Connectivity Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| App not in VPC | Cannot reach managed DB | Add `vpc.id` to app spec |
| Trusted sources blocking | Connection refused | Add VPC egress IP to trusted sources (see below) |
| Wrong trusted source rule | Connection refused | Use `ip_addr` rule, not `app` rule when using VPC |
| Wrong connection string | Connection timeout | Use internal hostname (via `${db.DATABASE_URL}`) |
| Cross-region access | Cannot reach resource | Use VPC peering for cross-datacenter access |
| Kafka with trusted sources | Connection fails | Kafka does NOT support trusted sources — disable them |

**Critical VPC + Trusted Sources Fix:**

> With VPC enabled, you cannot use `--rule app:<app-id>`. You must find the VPC egress IP and use `--rule ip_addr:<ip>`.

```bash
# Step 1: Find your app's VPC egress IP (from inside container)
doctl apps console <app_id> <component>
ip addr show | grep "inet 10\."
# Note the 10.x.x.x IP

# Step 2: Add IP to database trusted sources
doctl databases firewalls append <cluster-id> --rule ip_addr:10.x.x.x

# Step 3: Verify
doctl databases firewalls list <cluster-id>
```

**Diagnosis:**

```python
# Check if app is in VPC (look for private network interface)
result = app.exec("ip addr show")
print(result.stdout)
# Should see a 10.x.x.x interface if VPC is enabled

# Get the VPC egress IP
result = app.exec("ip addr show | grep 'inet 10\\.'")
print(f"VPC egress IP: {result.stdout.strip()}")

# Test internal DNS resolution
result = app.exec("nslookup db-postgresql-nyc3-12345.db.ondigitalocean.com 2>&1")
print(result.stdout)

# Test database connectivity from container
result = app.exec("nc -zv db-postgresql-nyc3-12345.db.ondigitalocean.com 25060 2>&1")
print(result.stdout)
```

### Static IP / Egress Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| External API blocks requests | 403 from third-party API | Enable dedicated egress: `egress.type: DEDICATED_IP` |
| Egress IP not working for functions | Functions use shared IPs | Functions don't support dedicated egress |
| Log forwarding uses wrong IP | Logs still from shared IP | Log forwarding has separate routing |

**Get your egress IPs:**

```bash
doctl apps get <app_id> -o json | jq '.[] | .dedicated_ips'
```

### Internal Service Communication Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| Service-to-service fails | Connection refused | Use `${service.PRIVATE_URL}` not hardcoded URLs |
| Internal port not reachable | Timeout on custom port | Add port to `internal_ports` array |
| Worker can't reach service | Connection timeout | Workers can only make outbound requests |

**Testing internal communication:**

```python
# From one service, test reaching another
result = app.exec("curl -v http://api:8080/health")
print(result.stdout)

# Test internal port
result = app.exec("curl -v http://api:9090/internal-endpoint")
print(result.stdout)

# Check if internal ports are configured
result = app.exec("env | grep PRIVATE_URL")
print(result.stdout)
```

---

## Debug Container: Isolate Infrastructure Issues

**Source**: [github.com/bikramkgupta/do-app-debug-container](https://github.com/bikramkgupta/do-app-debug-container)

**Key Insight**: When troubleshooting database/network issues, you're debugging multiple layers at once. The debug container isolates infrastructure from application in ~30-45 seconds, with **all diagnostic tools pre-installed**.

### Why Use the Debug Container

| Aspect | Debug Container | Full App Redeploy |
|--------|-----------------|-------------------|
| Deploy time | ~30-45 seconds | 5-7 minutes |
| Database clients | Pre-installed (psql, mysql, mongosh, redis-cli, kcat) | None |
| Network tools | Pre-installed (curl, dig, nmap, tcpdump, netcat) | None |
| Diagnostic scripts | Built-in (`diagnose.sh`, `test-db.sh`, `test-connectivity.sh`) | None |
| doctl | Pre-installed + auto-updated | None |
| Purpose | Pure infrastructure validation | Everything |

**Available Images**:
- `ghcr.io/bikramkgupta/do-app-debug-container-python` — Python 3.x runtime
- `ghcr.io/bikramkgupta/do-app-debug-container-node` — Node.js 20.x runtime

Both images include identical diagnostic tooling. Choose based on your application's runtime.

**Decision Logic**:
```
Database/Network Connection Issue?
│
├─ Step 1: Deploy debug container (~30-45s)
├─ Step 2: Container shows startup banner with detected connections
├─ Step 3: Run built-in diagnostic scripts
│
├─ If debug container works → Issue is in APPLICATION code
└─ If debug container fails → Issue is INFRASTRUCTURE (credentials, network, trusted sources)
```

### Step 1: Add Debug Worker to App Spec

**For existing apps** — add this worker component to your app spec:

```yaml
workers:
  - name: debug
    image:
      registry_type: GHCR
      registry: ghcr.io
      repository: bikramkgupta/do-app-debug-container-python
      tag: latest
    instance_size_slug: apps-s-1vcpu-2gb
    envs:
      # Mirror environment variables from your services
      # IMPORTANT: "your-db-name" must match the "name" in your databases section
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${your-db-name.DATABASE_URL}
      # Add other database connections as needed:
      # - key: REDIS_URL
      #   scope: RUN_TIME
      #   value: ${cache.DATABASE_URL}
      # - key: MONGODB_URI
      #   scope: RUN_TIME
      #   value: ${mongo.DATABASE_URL}

databases:
  - name: your-db-name   # ← This name is what you reference in ${your-db-name.XXXX}
    engine: PG
    production: true
    cluster_name: your-cluster-name
    db_name: your-database
    db_user: your-user
```

**Environment Variable Mirroring**: Copy the `envs` section from your existing service to the debug worker. This ensures the debug container has the same connection strings and can test the exact same infrastructure your app uses.

> **CRITICAL: Bindable Variable Syntax**
>
> In `${your-db-name.DATABASE_URL}`, the `your-db-name` part is **NOT** a reserved keyword—it's the **literal name** you defined in your `databases` section.
>
> | If your database is named... | Use this syntax... |
> |------------------------------|-------------------|
> | `name: your-db-name` | `${your-db-name.DATABASE_URL}` |
> | `name: postgres` | `${postgres.DATABASE_URL}` |
> | `name: main-db` | `${main-db.DATABASE_URL}` |
> | `name: myapp-postgres` | `${myapp-postgres.DATABASE_URL}` |
>
> **Common mistake**: Using `${foo.DATABASE_URL}` when your database is named `bar` will result in the literal string `${foo.DATABASE_URL}` appearing in your env var instead of the actual connection string.

### Step 2: Deploy and Connect

```bash
# Deploy the updated spec
doctl apps update <app-id> --spec app-spec.yaml

# Wait ~30-45 seconds, then connect via console
doctl apps console <app-id> debug
```

On connection, you'll see a **startup banner** showing:
- Available diagnostic scripts
- Detected database connections
- Pre-installed tools

### Step 3: Run Built-in Diagnostics

The debug container includes ready-to-use diagnostic scripts:

```bash
# Full system diagnostic report
./diagnose.sh

# Test specific database type
./test-db.sh postgres    # PostgreSQL
./test-db.sh mysql       # MySQL
./test-db.sh mongo       # MongoDB
./test-db.sh redis       # Redis/Valkey
./test-db.sh kafka       # Kafka
./test-db.sh opensearch  # OpenSearch

# Test network connectivity to external services
./test-connectivity.sh

# Test DigitalOcean Spaces access
./test-spaces.sh
```

**Manual checks** (if needed):

```bash
# Check environment variables
env | grep -E 'DATABASE|REDIS|MONGO|KAFKA' | sort

# Test DNS resolution
dig $DB_HOST

# Test port connectivity
nc -zv $DB_HOST $DB_PORT

# Direct database connection tests (clients pre-installed)
psql "$DATABASE_URL" -c "SELECT 1;"
mysql -h $MYSQL_HOST -u $MYSQL_USER -p$MYSQL_PASSWORD -e "SELECT 1;"
mongosh "$MONGODB_URI" --eval "db.runCommand({ping:1})"
redis-cli -u "$REDIS_URL" PING
```

### Interpreting Results

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Variables empty | Database not attached | Check `databases` section in app spec |
| Variables show `${your-db-name.X}` literally | **Database name mismatch** — the name in `${name.X}` doesn't match your `databases[].name` | Verify your database's `name` field and use that exact string |
| DNS fails | Network/region mismatch | Check region match, VPC settings |
| `nc` connection refused | Trusted sources blocking | Add App Platform to trusted sources in DB settings |
| Auth failed | User created via SQL not DO | Recreate user via `doctl databases user create` |
| SSL error | Missing sslmode | Use `${your-db-name.DATABASE_URL}` which includes `?sslmode=require` |

### Standalone Debug App (Alternative)

If you don't want to touch your production app, deploy a separate debug app:

```yaml
name: db-debug
region: nyc

workers:
  - name: debug
    image:
      registry_type: GHCR
      registry: ghcr.io
      repository: bikramkgupta/do-app-debug-container-python
      tag: latest
    instance_size_slug: apps-s-1vcpu-2gb
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: REDIS_URL
        scope: RUN_TIME
        value: ${cache.DATABASE_URL}

databases:
  - name: db
    engine: PG
    production: true
    cluster_name: your-cluster-name
    db_name: your-database
    db_user: your-user
  - name: cache
    engine: REDIS
    production: true
    cluster_name: your-valkey-cluster
```

```bash
doctl apps create --spec db-debug.yaml
# ... run diagnostics ...
doctl apps delete <debug-app-id>
```

### Debug Container Lifecycle Management

The debug container should only run when actively troubleshooting. Manage its lifecycle to avoid unnecessary costs:

**While actively debugging**: Keep the debug worker running.

**When done for now but may need later**: Archive the app to stop compute charges while preserving configuration.

```yaml
# Add to your app spec to archive
name: db-debug
maintenance:
  archive: true
  # Optional: show an offline page while archived
  # offline_page_url: https://example.com/images/maintenance.png

workers:
  - name: debug
    # ... rest of config
```

```bash
# Archive via CLI
doctl apps update <app-id> --spec archived-spec.yaml
```

**When completely done**: Delete the debug worker or app entirely.

```bash
# Remove debug worker from app spec and redeploy
# Or delete standalone debug app
doctl apps delete <debug-app-id>
```

### When to Use the Debug Container

✅ **Use debug container when:**
- App deploys but can't connect to database
- Setting up a new managed database
- Migrating from dev database to managed database
- Troubleshooting "connection refused" errors
- Verifying bindable variables work
- Testing VPC connectivity and trusted sources
- Diagnosing network issues to external services

❌ **Skip this when:**
- Using dev database (simpler setup)
- Issue is clearly application-level (logs show queries failing, not connection)
- You already verified infrastructure works

---

## Memory and Performance Issues

### Diagnosis

```python
# Memory overview
result = app.exec("free -m")
print(result.stdout)

# Top memory consumers
result = app.exec("ps aux --sort=-%mem | head -10")
print(result.stdout)

# Top CPU consumers
result = app.exec("ps aux --sort=-%cpu | head -10")
print(result.stdout)

# Node.js specific: heap info
result = app.exec("node -e \"console.log(process.memoryUsage())\" 2>/dev/null || echo 'N/A'")
print(result.stdout)
```

### Solutions

| Issue | Signs | Fix |
|-------|-------|-----|
| Memory leak | Gradual increase, eventual OOM | Profile app, fix leaks |
| Insufficient memory | Immediate OOM on startup | Upgrade instance size |
| Connection pool exhaustion | DB errors, high connection count | Configure pool limits |
| High CPU on idle | Busy loops, poor algorithms | Profile and optimize |

---

## Testing Strategy

**CRITICAL**: Since troubleshooting involves scaffolding and automated fixes, testing is essential.

### Test Before Fix

```python
# Always capture baseline state before making changes
def capture_baseline(app):
    baseline = {
        "health": app.exec("curl -s localhost:8080/health").stdout,
        "processes": app.exec("ps aux").stdout,
        "env": app.exec("env | sort").stdout,
        "disk": app.exec("df -h").stdout,
    }
    return baseline

baseline = capture_baseline(app)
```

### Verify After Fix

```python
def verify_fix(app, baseline, expected_changes):
    """Verify that fix was applied correctly."""
    current = capture_baseline(app)
    
    # Check health improved
    health_ok = "200" in current["health"] or "ok" in current["health"].lower()
    
    # Check processes are running
    process_ok = expected_changes.get("process") in current["processes"]
    
    return {
        "health_check": health_ok,
        "process_running": process_ok,
        "baseline_health": baseline["health"],
        "current_health": current["health"],
    }
```

### Rollback Strategy

```python
# Before making changes, save original state
original_file = app.filesystem.read_file("/app/config.py")

# Make changes
app.filesystem.write_file("/app/config.py", new_content)

# If something goes wrong, rollback
app.filesystem.write_file("/app/config.py", original_file)
```

---

## Deployment Cycle Awareness

**CRITICAL**: Standard deployments take 5-7 minutes. Don't poll frequently.

### If Using Standard Deploy (No Hot Reload)

```bash
# Trigger deployment
doctl apps create-deployment <app_id>

# For forced rebuild
doctl apps create-deployment <app_id> --force-rebuild
```

```python
# Wait appropriately (don't waste tokens checking every 30s)
import time

def wait_for_deployment(app_id, timeout=420):  # 7 minutes default
    """Wait for deployment to complete."""
    import subprocess
    import json
    
    start = time.time()
    last_phase = None
    
    while time.time() - start < timeout:
        result = subprocess.run(
            ["doctl", "apps", "get", app_id, "-o", "json"],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        phase = data[0]["active_deployment"]["phase"]
        
        if phase != last_phase:
            print(f"Deployment phase: {phase}")
            last_phase = phase
        
        if phase == "ACTIVE":
            return True
        elif phase in ("ERROR", "CANCELED"):
            return False
        
        # Sleep longer for standard deploys
        time.sleep(30)  # 30 seconds between checks
    
    return False
```

### If Using Hot Reload

Hot reload skips build/push cycles. Changes apply in seconds.
Refer to **hot-reload skill** for setup.

---

## Restart and Rebuild Commands

### Restart (No Code Change)

```bash
# Restart all components (rolling restart)
doctl apps restart <app_id>

# Restart specific component
doctl apps restart <app_id> --components web
```

### Force Rebuild

```bash
# Redeploy with latest code (uses cached build if unchanged)
doctl apps create-deployment <app_id>

# Force full rebuild (ignores cache)
doctl apps create-deployment <app_id> --force-rebuild
```

---

## Diagnostic Scripts

### General Health Check Script

```bash
#!/bin/bash
# Save as diagnostic.sh, upload and run

echo "=== System Info ==="
uname -a
echo ""

echo "=== Memory ==="
free -m
echo ""

echo "=== Disk ==="
df -h
echo ""

echo "=== Environment (filtered) ==="
env | grep -E 'PORT|DATABASE|REDIS|NODE_ENV|PYTHON' | sort
echo ""

echo "=== Processes ==="
ps aux --sort=-%mem | head -15
echo ""

echo "=== Network Listeners ==="
netstat -tlnp 2>/dev/null || ss -tlnp
echo ""

echo "=== Health Check ==="
curl -s -o /dev/null -w "%{http_code}" localhost:${PORT:-8080}/health 2>/dev/null || echo "FAILED"
echo ""
```

### Database Connectivity Script (Python)

```python
#!/usr/bin/env python3
# Save as db_check.py

import os
import sys

def check_postgres():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("✗ DATABASE_URL not set")
        return False
    
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"✓ PostgreSQL connected: {version[:60]}...")
        
        cur.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
        connections = cur.fetchone()[0]
        print(f"✓ Active connections: {connections}")
        
        cur.close()
        conn.close()
        return True
    except ImportError:
        print("✗ psycopg2 not installed")
        return False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = check_postgres()
    sys.exit(0 if success else 1)
```

---

## When to Escalate

### Contact DigitalOcean Support

- Internal error persists after redeploy
- Resource limit issues (need increase)
- Suspected platform issues (multiple apps affected)
- VPC/networking issues that can't be diagnosed
- Database managed service issues

### Information to Gather Before Escalating

```bash
# App ID and status
doctl apps get <app_id> -o json > app_info.json

# Recent logs
doctl apps logs <app_id> <component> --type run > runtime.log
doctl apps logs <app_id> <component> --type build > build.log
doctl apps logs <app_id> --type=run_restarted > crash.log

# App spec
doctl apps spec get <app_id> > app_spec.yaml
```

---

## Quick Reference: Common Fixes

| Problem | Quick Fix |
|---------|-----------|
| App exits immediately | Check if listening on $PORT, not hardcoded port |
| 502 errors | Check health endpoint, verify app is running |
| Database connection fails | **Use Debug Container first** (~30-45s), then verify DATABASE_URL, VPC, trusted sources |
| Build fails | Check dependencies, review build logs |
| OOM kills | Upgrade instance size or optimize memory usage |
| Health checks fail | Ensure app listens on 0.0.0.0, not localhost |
| Slow startup | Increase initial_delay_seconds in health check |
| SDK timeout on exec | Check shell prompt compatibility (see Prerequisites) |

---

## Related Skills

| Skill | When to Use |
|-------|-------------|
| **deployment** | After fixing, deploy proper changes |
| **dev-containers** | Reproduce issues locally |
| **hot-reload** | Fast iteration during debugging |
| **postgres** | Database-specific configuration issues |

---

## Documentation Links

- [App Platform Logs](https://docs.digitalocean.com/products/app-platform/how-to/view-logs/)
- [Error Reference](https://docs.digitalocean.com/products/app-platform/reference/error-codes/)
- [Health Checks](https://docs.digitalocean.com/products/app-platform/how-to/manage-health-checks/)
- [App Spec Reference](https://docs.digitalocean.com/products/app-platform/reference/app-spec/)
