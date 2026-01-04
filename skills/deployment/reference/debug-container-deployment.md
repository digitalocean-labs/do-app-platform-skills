# Debug Container for Complex Deployments

Deploy a diagnostic container to verify infrastructure before deploying your full application.

**Source**: [github.com/bikramkgupta/do-app-debug-container](https://github.com/bikramkgupta/do-app-debug-container)

---

## The Problem

For complex applications with multiple database connections and third-party integrations, deploying a debug container first can save hours of iteration.

```
Traditional approach for complex apps:
Push code → Wait 5-7 min → Fails → Check logs → Guess → Repeat

With debug container:
Deploy debug worker (~30-45s) → Run built-in diagnostics → Verify ALL connections →
If works → Proceed with full app
If fails → Fix infrastructure, not code
```

---

## When to Use This Pattern

**Use debug container when:**
- App has 3+ external integrations
- Deployment keeps failing with connection errors
- Setting up new managed databases for the first time
- Migrating from one database cluster to another
- Verifying VPC + trusted sources configuration

**Skip this when:**
- Simple app with 1-2 services
- Issue is clearly application code (syntax errors, etc.)
- Already verified infrastructure works

---

## Deploy the Debug Container

Add this worker to your app spec temporarily:

```yaml
# Add to .do/app.yaml temporarily
workers:
  - name: debug
    image:
      registry_type: GHCR
      registry: ghcr.io
      repository: bikramkgupta/do-app-debug-container-python
      # OR: bikramkgupta/do-app-debug-container-node
      tag: latest
    instance_size_slug: apps-s-1vcpu-2gb
    envs:
      # Mirror ALL environment variables from your main service
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: REDIS_URL
        scope: RUN_TIME
        value: ${cache.DATABASE_URL}
      - key: MONGODB_URI
        scope: RUN_TIME
        value: ${mongo.DATABASE_URL}
      - key: KAFKA_BROKERS
        scope: RUN_TIME
        value: ${kafka.HOSTNAME}:${kafka.PORT}
      # Add any other integrations...
```

---

## Included Tools

The debug container includes **all diagnostic tools pre-installed**:

### Database Clients
- `psql` - PostgreSQL
- `mysql` - MySQL
- `mongosh` - MongoDB
- `redis-cli` - Redis/Valkey
- `kcat` - Kafka

### Network Tools
- `curl` - HTTP requests
- `dig` - DNS lookups
- `nmap` - Port scanning
- `tcpdump` - Packet capture
- `netcat` - Raw TCP/UDP

### Diagnostic Scripts
- `diagnose.sh` - Comprehensive diagnostics
- `test-db.sh` - Database connectivity tests
- `test-connectivity.sh` - Network reachability tests
- `test-spaces.sh` - DO Spaces connectivity

### Other
- `doctl` - Pre-installed and auto-updated

---

## Verification Workflow

After deploying, connect and run built-in diagnostics.

### For AI Assistants

Use the `do-app-sandbox` SDK:

```python
from do_app_sandbox import Sandbox

# Connect to the debug container
debug = Sandbox.get_from_id(app_id="your-app-id", component="debug")

# Run comprehensive diagnostics
result = debug.exec("./diagnose.sh")
print(result.stdout)

# Test specific database types
debug.exec("./test-db.sh postgres")
debug.exec("./test-db.sh redis")

# Test network and Spaces
debug.exec("./test-connectivity.sh")
debug.exec("./test-spaces.sh")
```

### For Humans

Use the interactive console:

```bash
doctl apps console $APP_ID debug

# Inside the container:
./diagnose.sh
./test-db.sh postgres
./test-connectivity.sh
```

---

## Lifecycle Management

### While Debugging

Keep the debug worker running.

### When Pausing

Archive the app to stop compute costs while preserving configuration:

```yaml
name: my-app
maintenance:
  archive: true
```

### When Done

Remove the debug worker from your app spec and redeploy, or delete standalone debug apps entirely.

---

## Available Debug Container Images

| Language | Image |
|----------|-------|
| Python | `ghcr.io/bikramkgupta/do-app-debug-container-python:latest` |
| Node.js | `ghcr.io/bikramkgupta/do-app-debug-container-node:latest` |

---

## Example: Verifying Multi-Database Setup

```bash
# Connect to debug container
doctl apps console $APP_ID debug

# Run full diagnostics
./diagnose.sh

# Output shows:
# ✓ PostgreSQL: Connected (latency: 12ms)
# ✓ Redis: Connected (latency: 3ms)
# ✓ MongoDB: Connected (latency: 18ms)
# ✗ Kafka: Connection refused (check KAFKA_BROKERS)
# ✓ Spaces: Bucket accessible

# Now you know Kafka config is wrong before deploying app code
```

---

## Troubleshooting Debug Container

| Issue | Fix |
|-------|-----|
| Container won't start | Check instance size (needs at least 1vCPU-2GB) |
| Can't connect with console | App must be deployed and running |
| Scripts not found | Ensure using correct image (python or node) |
| Database test fails | Verify env vars match bindable variable names |

---

## Integration with Other Skills

- **troubleshooting skill**: For detailed debugging workflows beyond initial setup
- **postgres skill**: For database-specific diagnostics
- **networking skill**: For VPC and connectivity issues
