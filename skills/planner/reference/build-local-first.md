# Build Locally First

Validate builds locally before cloud deployment. Cloud builds take 5+ minutes to fail, wasting time on errors that could be caught instantly.

---

## The Tool: `doctl app dev build`

DigitalOcean provides official local build tooling that replicates the App Platform build environment:

```bash
# Prerequisites
doctl version  # Must be 1.82.0+
docker info    # Docker must be running

# Build a component using local app spec
doctl app dev build

# Build using spec from existing deployed app
doctl app dev build --app <APP_ID>

# Build with environment overrides
doctl app dev build --env-file .env.local
```

---

## Why Local Builds Matter

| Build Location | Feedback Time | Cost of Failure |
|----------------|---------------|-----------------|
| Cloud (App Platform) | 5-10 minutes | Wasted deploy cycle, confusing logs |
| Local (`doctl app dev build`) | 30-60 seconds | Immediate fix, clear error messages |

---

## Configuration Options

The `doctl app dev build` command supports:

| Flag | Purpose |
|------|---------|
| `--app` | Fetch App Spec from existing deployed app |
| `--spec` | Path to local app spec file |
| `--build-command` | Override build command for testing |
| `--env-file` | Environment variable overrides |
| `--timeout` | Build timeout duration |

These can also be configured in `.do/dev-config.yaml` for persistence.

---

## Health Check Validation

**The #1 cause of deploy failures is health check timeout.** Before cloud deployment:

1. **Define health endpoint in code**: Ensure `/health` (or your chosen path) returns HTTP 200
2. **Test locally**: `curl http://localhost:PORT/health` must return 200
3. **Match app spec**: Verify `health_check.http_path` in app spec matches actual endpoint
4. **Test under load**: Health check must respond within timeout (default 10s)

---

## Dev Config File

Create `.do/dev-config.yaml` for persistent local dev settings:

```yaml
# .do/dev-config.yaml
timeout: 600  # 10 minute timeout
env_file: .env.local
```
