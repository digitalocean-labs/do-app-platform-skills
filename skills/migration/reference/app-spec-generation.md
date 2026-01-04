# App Spec Generation

App spec templates for testing and production environments.

---

## Testing Environment Spec

Use for initial migration testing with dev databases and smaller instances.

```yaml
# .do/app.yaml (testing)
spec:
  name: myapp-test
  region: nyc

  services:
    - name: web
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/test
      dockerfile_path: Dockerfile
      http_port: 8000
      instance_size_slug: apps-s-1vcpu-1gb
      instance_count: 1
      health_check:
        http_path: /health
        initial_delay_seconds: 10
        period_seconds: 10
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}
        - key: VALKEY_URL
          scope: RUN_TIME
          value: ${cache.DATABASE_URL}
        - key: SECRET_KEY
          scope: RUN_TIME
          type: SECRET

  workers:
    - name: celery
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/test
      dockerfile_path: Dockerfile
      instance_size_slug: apps-s-1vcpu-0.5gb
      instance_count: 1
      run_command: celery -A tasks worker
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}
        - key: VALKEY_URL
          scope: RUN_TIME
          value: ${cache.DATABASE_URL}

  jobs:
    - name: migrate
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/test
      dockerfile_path: Dockerfile
      kind: PRE_DEPLOY
      instance_size_slug: apps-s-1vcpu-0.5gb
      run_command: python manage.py migrate
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}

  databases:
    - name: db
      engine: PG
      production: false  # Dev database for testing

    - name: cache
      engine: VALKEY
      production: false
```

---

## Production Environment Spec

Use for production with managed databases, dedicated CPU, and autoscaling.

```yaml
# .do/app.yaml (production)
spec:
  name: myapp-prod
  region: nyc

  services:
    - name: web
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/prod
      dockerfile_path: Dockerfile
      http_port: 8000
      instance_size_slug: apps-d-1vcpu-2gb  # Dedicated CPU
      instance_count: 2  # Multiple instances
      autoscaling:
        min_instance_count: 2
        max_instance_count: 5
        metrics:
          - name: cpu_utilization
            threshold: 80
      health_check:
        http_path: /health
        initial_delay_seconds: 10
        period_seconds: 10
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}
        - key: VALKEY_URL
          scope: RUN_TIME
          value: ${cache.DATABASE_URL}
        - key: SECRET_KEY
          scope: RUN_TIME
          type: SECRET

  workers:
    - name: celery
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/prod
      dockerfile_path: Dockerfile
      instance_size_slug: apps-d-1vcpu-1gb
      instance_count: 2
      run_command: celery -A tasks worker
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}
        - key: VALKEY_URL
          scope: RUN_TIME
          value: ${cache.DATABASE_URL}

  jobs:
    - name: migrate
      git:
        repo_clone_url: https://github.com/myorg/myapp.git
        branch: migrate/prod
      dockerfile_path: Dockerfile
      kind: PRE_DEPLOY
      instance_size_slug: apps-s-1vcpu-1gb
      run_command: python manage.py migrate
      envs:
        - key: DATABASE_URL
          scope: RUN_TIME
          value: ${db.DATABASE_URL}

  databases:
    - name: db
      engine: PG
      production: true  # Managed database
      cluster_name: myapp-prod-db  # Must exist

    - name: cache
      engine: VALKEY
      production: true
      cluster_name: myapp-prod-cache  # Must exist
```

---

## Deploy to DO Button Template

Create `.do/deploy.template.yaml` for one-click deployment:

```yaml
spec:
  name: myapp
  region: nyc

  services:
    - name: web
      github:
        repo: myorg/myapp
        branch: main
        deploy_on_push: true
      dockerfile_path: Dockerfile
      http_port: 8000
      instance_size_slug: apps-s-1vcpu-1gb
      health_check:
        http_path: /health

  databases:
    - name: db
      engine: PG
      production: false
```

---

## Environment-Specific Differences

| Aspect | Testing | Production |
|--------|---------|------------|
| Database | `production: false` (dev) | `production: true` + `cluster_name` |
| Instance size | `apps-s-1vcpu-1gb` | `apps-d-1vcpu-2gb` (dedicated) |
| Instance count | 1 | 2+ with autoscaling |
| Branch | `migrate/test` | `migrate/prod` or `main` |
| deploy_on_push | `true` | `false` (use GitHub Actions) |

---

## Opinionated Defaults

| Decision | Default | Rationale |
|----------|---------|-----------|
| Target branch naming | `migrate/test`, `migrate/prod` | Clear purpose |
| Test environment | Dev databases, small instances | Cost-effective testing |
| Production environment | Managed databases, dedicated CPU | Reliability |
| Secrets handling | GitHub Secrets | Security, AI never sees values |
| Health check path | `/health` or `/healthz` | Industry standard |
| Instance size (test) | `apps-s-1vcpu-1gb` | Good baseline |
| Instance size (prod) | `apps-d-1vcpu-2gb` | Dedicated CPU |
| Redis replacement | Valkey | Redis EOL on DO |
| deploy_on_push | `true` for test, `false` for prod | GitOps with control |
