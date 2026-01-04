# Environment Variables Reference

Complete guide to environment variables, scopes, types, and placeholders.

---

## Scopes

| Scope | Available | Use Case | Example |
|-------|-----------|----------|---------|
| `RUN_TIME` | Only at runtime | Secrets, DB URLs, API keys | `DATABASE_URL`, `JWT_SECRET` |
| `BUILD_TIME` | Only during build | Public API URLs, feature flags | `NEXT_PUBLIC_API_URL`, `VITE_API_BASE` |
| `RUN_AND_BUILD_TIME` | Both | NPM tokens, shared config | `NPM_TOKEN`, `NODE_ENV` |

### Scope Selection Guide

```
When is this variable needed?
├── Only when app runs? → RUN_TIME
│   Examples: DATABASE_URL, API_KEY, JWT_SECRET
├── Only during build? → BUILD_TIME
│   Examples: NEXT_PUBLIC_*, VITE_*, PUBLIC_URL
└── Both build and run? → RUN_AND_BUILD_TIME
    Examples: NPM_TOKEN, NODE_ENV
```

---

## Types

| Type | Behavior |
|------|----------|
| `GENERAL` | Plain text, visible in UI |
| `SECRET` | Encrypted, hidden in UI after first save |

```yaml
envs:
  # General - visible
  - key: LOG_LEVEL
    scope: RUN_TIME
    type: GENERAL
    value: info

  # Secret - encrypted, hidden
  - key: API_KEY
    scope: RUN_TIME
    type: SECRET
    value: your-api-key
```

---

## Bindable Variable Placeholders

Bindable variables are automatically populated by App Platform.

### Database Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `${db.DATABASE_URL}` | Full connection string | `postgresql://user:pass@host:25060/db?sslmode=require` |
| `${db.HOSTNAME}` | Database host | `cluster-do-user-123.db.ondigitalocean.com` |
| `${db.PORT}` | Database port | `25060` |
| `${db.USERNAME}` | Database user | `myappuser` |
| `${db.PASSWORD}` | Database password | (auto-populated) |
| `${db.DATABASE}` | Database name | `myappdb` |
| `${db.CA_CERT}` | CA certificate (for TLS) | (certificate content) |

Replace `db` with your database component name.

### Connection Pool Variables

| Variable | Description |
|----------|-------------|
| `${db.pool-name.DATABASE_URL}` | Connection pool URL |
| `${db.pool-name.HOSTNAME}` | Pool hostname |
| `${db.pool-name.PORT}` | Pool port |

### Component URL Variables

| Variable | Description |
|----------|-------------|
| `${service-name.PRIVATE_URL}` | Internal URL (VPC only) |
| `${service-name.PUBLIC_URL}` | Public URL |
| `${APP_URL}` | App's default URL |
| `${APP_DOMAIN}` | App's domain |

---

## Common Patterns

### Database Connection

```yaml
envs:
  # Full connection string (recommended)
  - key: DATABASE_URL
    scope: RUN_TIME
    value: ${db.DATABASE_URL}

  # Or individual components
  - key: DB_HOST
    scope: RUN_TIME
    value: ${db.HOSTNAME}
  - key: DB_PORT
    scope: RUN_TIME
    value: ${db.PORT}
  - key: DB_USER
    scope: RUN_TIME
    value: ${db.USERNAME}
  - key: DB_PASSWORD
    scope: RUN_TIME
    value: ${db.PASSWORD}
  - key: DB_NAME
    scope: RUN_TIME
    value: ${db.DATABASE}
```

### Cache Connection (Valkey/Redis)

```yaml
envs:
  - key: VALKEY_URL
    scope: RUN_TIME
    value: ${cache.DATABASE_URL}

  # Or for legacy Redis clients
  - key: REDIS_URL
    scope: RUN_TIME
    value: ${cache.DATABASE_URL}
```

### Internal Service Communication

```yaml
# API service
services:
  - name: api
    envs:
      - key: AUTH_SERVICE_URL
        scope: RUN_TIME
        value: ${auth.PRIVATE_URL}

# Auth worker (internal)
workers:
  - name: auth
    http_port: 8080  # Internal HTTP
```

### Frontend Build Variables

```yaml
static_sites:
  - name: frontend
    envs:
      # Next.js public variables
      - key: NEXT_PUBLIC_API_URL
        scope: BUILD_TIME
        value: ${api.PUBLIC_URL}

      # Vite public variables
      - key: VITE_API_BASE
        scope: BUILD_TIME
        value: /api

      # Feature flags
      - key: NEXT_PUBLIC_FEATURE_X
        scope: BUILD_TIME
        value: "true"
```

### Secrets (User-Provided)

```yaml
envs:
  - key: JWT_SECRET
    scope: RUN_TIME
    type: SECRET
    value: PLACEHOLDER_CHANGE_ME

  - key: STRIPE_SECRET_KEY
    scope: RUN_TIME
    type: SECRET
    value: PLACEHOLDER_CHANGE_ME

  - key: SENDGRID_API_KEY
    scope: RUN_TIME
    type: SECRET
    value: PLACEHOLDER_CHANGE_ME
```

**Note:** Use descriptive placeholders. Users must update these in the console.

---

## Complete Example

```yaml
services:
  - name: api
    envs:
      # Database (bindable)
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}

      # Cache (bindable)
      - key: VALKEY_URL
        scope: RUN_TIME
        value: ${cache.DATABASE_URL}

      # Internal service (bindable)
      - key: AUTH_SERVICE_URL
        scope: RUN_TIME
        value: ${auth.PRIVATE_URL}

      # Secrets (user-provided)
      - key: JWT_SECRET
        scope: RUN_TIME
        type: SECRET
        value: CHANGE_ME

      - key: STRIPE_KEY
        scope: RUN_TIME
        type: SECRET
        value: CHANGE_ME

      # Config (general)
      - key: LOG_LEVEL
        scope: RUN_TIME
        value: info

      - key: NODE_ENV
        scope: RUN_AND_BUILD_TIME
        value: production

static_sites:
  - name: frontend
    envs:
      # Build-time only
      - key: NEXT_PUBLIC_API_URL
        scope: BUILD_TIME
        value: ${api.PUBLIC_URL}

      - key: NEXT_PUBLIC_STRIPE_KEY
        scope: BUILD_TIME
        value: pk_live_xxx
```

---

## Framework-Specific Patterns

### Next.js

```yaml
envs:
  # Server-side (runtime)
  - key: DATABASE_URL
    scope: RUN_TIME
    value: ${db.DATABASE_URL}

  # Client-side (build time, prefixed)
  - key: NEXT_PUBLIC_API_URL
    scope: BUILD_TIME
    value: /api

  - key: NEXT_PUBLIC_STRIPE_KEY
    scope: BUILD_TIME
    value: pk_live_xxx
```

### Vite (React/Vue/Svelte)

```yaml
envs:
  # Client-side (build time, prefixed)
  - key: VITE_API_URL
    scope: BUILD_TIME
    value: /api

  - key: VITE_FEATURE_FLAG
    scope: BUILD_TIME
    value: "true"
```

### Node.js/Express

```yaml
envs:
  - key: PORT
    scope: RUN_TIME
    value: "8080"

  - key: NODE_ENV
    scope: RUN_AND_BUILD_TIME
    value: production

  - key: DATABASE_URL
    scope: RUN_TIME
    value: ${db.DATABASE_URL}
```

### Python/Django

```yaml
envs:
  - key: DATABASE_URL
    scope: RUN_TIME
    value: ${db.DATABASE_URL}

  - key: DJANGO_SECRET_KEY
    scope: RUN_TIME
    type: SECRET
    value: CHANGE_ME

  - key: DJANGO_ALLOWED_HOSTS
    scope: RUN_TIME
    value: ".ondigitalocean.app,.example.com"

  - key: DEBUG
    scope: RUN_TIME
    value: "False"
```

---

## .env.example Template

Generate for documentation:

```bash
# Database - auto-injected from App Platform
DATABASE_URL=${db.DATABASE_URL}

# Cache - auto-injected from App Platform
VALKEY_URL=${cache.DATABASE_URL}

# Secrets - set in App Platform console
JWT_SECRET=your-secret-key-here
STRIPE_SECRET_KEY=sk_live_xxx

# Build-time config
NEXT_PUBLIC_API_URL=https://your-app.ondigitalocean.app/api
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Variable empty at runtime | Wrong scope | Use `RUN_TIME` or `RUN_AND_BUILD_TIME` |
| Variable empty at build | Wrong scope | Use `BUILD_TIME` or `RUN_AND_BUILD_TIME` |
| `${db.X}` not resolving | Typo in database name | Verify `name:` in databases block |
| Secret visible in UI | Type not set | Add `type: SECRET` |
| NEXT_PUBLIC_* empty | Wrong scope | Must be `BUILD_TIME` |
