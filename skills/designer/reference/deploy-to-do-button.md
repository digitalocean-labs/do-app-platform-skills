# Deploy to DigitalOcean Button Reference

Complete guide to creating Deploy to DO buttons for public repositories.

---

## Overview

The Deploy to DO button allows one-click deployment of public GitHub repositories to App Platform.

**Requirements:**
- Public GitHub repository
- `.do/deploy.template.yaml` in repository root

---

## app.yaml vs deploy.template.yaml

| Aspect | app.yaml | deploy.template.yaml |
|--------|----------|----------------------|
| Wrapper | None | `spec:` key required |
| Git source | `github:` block | `git:` block with `repo_clone_url` |
| Usage | `doctl apps create --spec` | Deploy to DO button |
| Repo visibility | Any | **Public only** |

---

## Conversion Example

### app.yaml (for CLI/API)

```yaml
name: my-app
region: nyc

services:
  - name: web
    github:
      repo: owner/repo
      branch: main
      deploy_on_push: false
    http_port: 8080
    instance_size_slug: apps-s-1vcpu-1gb
    health_check:
      http_path: /health
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}

databases:
  - name: db
    engine: PG
    production: false
```

### deploy.template.yaml (for button)

```yaml
spec:
  name: my-app
  region: nyc

  services:
    - name: web
      git:
        repo_clone_url: https://github.com/owner/repo.git
        branch: main
      http_port: 8080
      instance_size_slug: apps-s-1vcpu-1gb
      health_check:
        http_path: /health
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}

  databases:
    - name: db
      engine: PG
      production: false
```

**Key differences:**
1. Wrapped in `spec:` key
2. Uses `git:` + `repo_clone_url` instead of `github:` + `repo`
3. Full HTTPS URL with `.git` suffix

---

## Button Styles

| Style | Image URL |
|-------|-----------|
| Blue | `https://www.deploytodo.com/do-btn-blue.svg` |
| Blue Ghost | `https://www.deploytodo.com/do-btn-blue-ghost.svg` |
| White | `https://www.deploytodo.com/do-btn-white.svg` |
| White Ghost | `https://www.deploytodo.com/do-btn-white-ghost.svg` |

---

## Button HTML/Markdown

### Markdown (for README.md)

```markdown
[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/OWNER/REPO/tree/BRANCH)
```

### HTML (for websites)

```html
<a href="https://cloud.digitalocean.com/apps/new?repo=https://github.com/OWNER/REPO/tree/BRANCH">
  <img src="https://www.deploytodo.com/do-btn-blue.svg" alt="Deploy to DigitalOcean">
</a>
```

### With specific refspec

```markdown
[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/OWNER/REPO/tree/v1.0.0)
```

---

## Environment Variable Prompts

Variables without values prompt the user during deployment:

```yaml
spec:
  name: my-app
  services:
    - name: web
      envs:
        # Will prompt user for value (no default)
        - key: API_KEY
          scope: RUN_TIME
          type: SECRET

        # Has default, user can edit
        - key: LOG_LEVEL
          scope: RUN_TIME
          value: "info"

        # Bindable - auto-populated, no prompt
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}
```

### Prompt behavior

| Configuration | User Experience |
|---------------|-----------------|
| No `value` field | Required prompt, must fill |
| `value: ""` | Optional prompt, can leave empty |
| `value: "default"` | Pre-filled, can edit |
| `value: ${db.X}` | Auto-populated, no prompt |

---

## Complete Template Example

```yaml
spec:
  name: fastapi-starter
  region: nyc

  services:
    - name: api
      git:
        repo_clone_url: https://github.com/owner/fastapi-starter.git
        branch: main
      dockerfile_path: Dockerfile
      http_port: 8000
      instance_size_slug: apps-s-1vcpu-1gb
      instance_count: 1
      health_check:
        http_path: /health
        initial_delay_seconds: 10
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}
        - key: SECRET_KEY
          scope: RUN_TIME
          type: SECRET
        - key: DEBUG
          scope: RUN_TIME
          value: "false"

  jobs:
    - name: migrate
      kind: PRE_DEPLOY
      git:
        repo_clone_url: https://github.com/owner/fastapi-starter.git
        branch: main
      run_command: alembic upgrade head
      instance_size_slug: apps-s-1vcpu-0.5gb
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}

  databases:
    - name: db
      engine: PG
      production: false

  alerts:
    - rule: DEPLOYMENT_FAILED
```

---

## Validation

Always validate before committing:

```bash
doctl apps spec validate .do/deploy.template.yaml
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "invalid spec" | Missing `spec:` wrapper | Wrap entire content in `spec:` |
| "invalid git source" | Using `github:` block | Use `git:` with `repo_clone_url` |
| Button shows error | Private repository | Must be public |
| "branch not found" | Wrong branch in URL | Verify branch exists |
| Variables not prompting | Has default value | Remove `value:` for required prompt |

---

## Best Practices

1. **Keep it simple** — Include only essential components
2. **Use dev databases** — Cheaper for first deployment
3. **Mark secrets as SECRET** — Ensures encryption
4. **Include health checks** — Enables reliable deployments
5. **Add alerts** — Notifies on deployment failures
6. **Document env vars** — Add comments for required secrets

---

## README Template

```markdown
# My App

One-click deploy to DigitalOcean App Platform:

[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/OWNER/REPO/tree/main)

## Configuration

After deployment, set these environment variables in the App Platform console:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Application secret key |
| `API_KEY` | External API key |

## What Gets Deployed

- **api** — FastAPI backend (Python)
- **db** — PostgreSQL database (dev tier)
```
