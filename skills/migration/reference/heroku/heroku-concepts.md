# Heroku Concepts Reference

Heroku configuration file schemas and platform concepts — only what's needed for parsing and migration.

## Table of Contents

1. [Procfile](#procfile)
2. [app.json](#appjson)
3. [heroku.yml](#herokuyml)
4. [Buildpacks](#buildpacks)
5. [Pipelines and Heroku Flow](#pipelines-and-heroku-flow)
6. [Heroku CLI → doctl Mapping](#heroku-cli--doctl-mapping)

---

## Procfile

Format: `<process-type>: <command>`

### Process Types and Migration Rules

| Process Type | Heroku Behavior | App Platform Mapping |
|-------------|-----------------|---------------------|
| `web` | Receives HTTP traffic, must bind to `$PORT` | `services` component with `http_port` |
| `worker` | Background process, no HTTP traffic | `workers` component |
| `release` | Runs once before deploy, gates deployment | `jobs` with `kind: PRE_DEPLOY` |
| `clock` | Scheduled tasks (custom) | `workers` or `jobs` with `kind: CRON_TRIGGER` |
| Custom names | Background processes | `workers` component |

### Parsing Rules

```
# Extract process types
web: gunicorn app:app --bind 0.0.0.0:$PORT     → service, run_command: "gunicorn app:app"
worker: celery -A tasks worker --loglevel=info  → worker, run_command: "celery -A tasks worker --loglevel=info"
release: python manage.py migrate               → job (PRE_DEPLOY), run_command: "python manage.py migrate"
clock: python clock.py                          → worker, run_command: "python clock.py"
```

**Important**: Strip `--bind 0.0.0.0:$PORT` and similar port binding flags from web commands. App Platform handles port binding via `http_port` in the app spec.

---

## app.json

Application manifest used for Review Apps, Heroku Button, and CI. Key fields for migration:

### Fields That Map to App Spec

```json
{
  "name": "myapp",
  "description": "My application",
  "buildpacks": [
    {"url": "heroku/nodejs"},
    {"url": "heroku/python"}
  ],
  "env": {
    "SECRET_KEY": {
      "description": "Django secret key",
      "required": true
    },
    "DEBUG": {
      "description": "Debug mode",
      "value": "false"
    },
    "DATABASE_URL": {
      "required": true
    }
  },
  "addons": [
    "heroku-postgresql:essential-0",
    "heroku-redis:premium-0",
    {"plan": "heroku-postgresql:essential-0", "options": {"version": "16"}}
  ],
  "formation": {
    "web": {"quantity": 1, "size": "basic"},
    "worker": {"quantity": 1, "size": "standard-1x"}
  },
  "scripts": {
    "postdeploy": "python manage.py seed_db"
  }
}
```

### Migration Rules

| app.json Field | App Spec Mapping | Notes |
|----------------|-----------------|-------|
| `buildpacks` | `buildpacks` in component or Dockerfile | See [Buildpacks](#buildpacks) |
| `env` (required, no value) | `envs` with `type: SECRET` | Prompt user to set in GitHub Secrets |
| `env` (with value) | `envs` with `value` | Direct mapping, check if sensitive |
| `addons` | `databases` section | See [heroku-addons.md](heroku-addons.md) |
| `formation` | `instance_count` + `instance_size_slug` | See [heroku-mapping.md](heroku-mapping.md) |
| `scripts.postdeploy` | `jobs` with `kind: POST_DEPLOY` | One-time setup, not every deploy |

---

## heroku.yml

Docker-based build manifest. Presence indicates the app uses Docker (stack set to `container`).

### Structure

```yaml
build:
  docker:
    web: Dockerfile              # Dockerfile path for web process
    worker: Dockerfile.worker    # Dockerfile path for worker
  config:
    PYTHON_VERSION: "3.11"       # Build-time only, NOT runtime

setup:
  addons:
    - plan: heroku-postgresql:essential-0
  config:
    RAILS_ENV: production        # Runtime config vars

release:
  image: web                     # Which built image to use
  command:
    - python manage.py migrate   # Release phase command

run:
  web: gunicorn myapp:app        # Overrides Dockerfile CMD
  worker: celery -A tasks worker
```

### Migration Rules

| heroku.yml Section | App Spec Mapping | Notes |
|-------------------|-----------------|-------|
| `build.docker.<process>` | `dockerfile_path` in component | Direct path mapping |
| `build.config` | Build-time env vars | Use `scope: BUILD_TIME` in app spec |
| `setup.addons` | `databases` section | Same as app.json addons |
| `setup.config` | `envs` with `scope: RUN_TIME` | Runtime config |
| `release.command` | `jobs` with `kind: PRE_DEPLOY` | Same as Procfile release |
| `run.<process>` | `run_command` in component | Overrides Dockerfile CMD |

**Key difference**: When `heroku.yml` exists, always use Dockerfile-based builds in the app spec. Never mix heroku.yml with buildpack approach.

---

## Buildpacks

Heroku detects buildpacks automatically or from explicit configuration.

### Detection (file presence → buildpack)

| File | Heroku Buildpack | App Platform Approach |
|------|-----------------|----------------------|
| `package.json` | heroku/nodejs | CNB buildpack OR Dockerfile |
| `requirements.txt`, `Pipfile`, `setup.py` | heroku/python | CNB buildpack OR Dockerfile |
| `Gemfile` | heroku/ruby | CNB buildpack OR Dockerfile |
| `go.mod` | heroku/go | CNB buildpack OR Dockerfile |
| `pom.xml`, `build.gradle` | heroku/java | CNB buildpack OR Dockerfile |
| `composer.json` | heroku/php | Dockerfile (recommended) |

### Multi-Buildpack Translation

Heroku supports chaining buildpacks (e.g., Node.js for frontend assets + Python for backend). On App Platform:

- **Simple cases**: Single CNB buildpack with `build_command` that handles both
- **Complex cases**: Multi-stage Dockerfile (recommended)
- **Example**: Node.js + Python → Dockerfile with node build stage + python runtime stage

### Buildpack Configuration in app.json

```json
"buildpacks": [
  {"url": "heroku/nodejs"},
  {"url": "heroku/python"}
]
```

Maps to EITHER:
```yaml
# Option A: CNB (single buildpack apps)
services:
  - name: web
    build_command: npm run build && pip install -r requirements.txt
```

OR:
```yaml
# Option B: Dockerfile (multi-buildpack or complex builds)
services:
  - name: web
    dockerfile_path: Dockerfile
```

---

## Pipelines and Heroku Flow

Heroku's CI/CD model. Understanding this is critical for migrating the full development workflow.

### Pipeline Stages

| Heroku Stage | App Platform Equivalent | Notes |
|-------------|------------------------|-------|
| Development | Local dev (devcontainers skill) | No direct equivalent |
| Review | Preview environments | Triggered by PR, not identical to Review Apps |
| Staging | Separate app or branch deploy | Configure in GitHub Actions |
| Production | Production app | Deploy via GitHub Actions promotion |

### Heroku Flow Components → App Platform + GitHub

| Heroku Flow | Migration Target | How |
|-------------|-----------------|-----|
| Pipelines | GitHub Actions workflow | Environments: staging, production |
| Review Apps | App Platform preview deployments | `deploy_on_push: true` on PR branches |
| Heroku CI | GitHub Actions CI job | `test` job in workflow |
| Promotion (slug) | GitHub Actions deploy job | Build once, deploy to environments |
| Automatic deploys | `deploy_on_push: true` | Branch-based auto-deploy |

### Pipeline Migration Note

Heroku pipeline promotion copies a compiled slug between stages (instant, binary-identical). GitHub Actions equivalent: build artifact once in CI, deploy same artifact to staging and production environments. This is a workflow change — document it clearly for the user.

---

## Heroku CLI → doctl Mapping

Quick reference for users familiar with Heroku CLI:

| Heroku CLI | doctl Equivalent | Notes |
|-----------|-----------------|-------|
| `heroku create` | `doctl apps create --spec .do/app.yaml` | Spec-driven, not imperative |
| `heroku config` | App spec `envs` section | No CLI equivalent for listing |
| `heroku config:set KEY=val` | Update app spec + redeploy | Or GitHub Secrets |
| `heroku ps` | `doctl apps list-deployments` | Different model |
| `heroku ps:scale web=2` | Update `instance_count` in spec | Spec-driven scaling |
| `heroku logs --tail` | `doctl apps logs <id> --follow` | Similar |
| `heroku run bash` | `doctl apps console` (interactive) | Or sandbox skill |
| `heroku addons:create` | Create managed DB via doctl/console | `doctl databases create` |
| `heroku pg:backups` | `doctl databases backups list` | Similar |
| `heroku pipelines:promote` | GitHub Actions deployment | Different model entirely |
| `heroku maintenance:on` | No equivalent | Use deployment strategy |
