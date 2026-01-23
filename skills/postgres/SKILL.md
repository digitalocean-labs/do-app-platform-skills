---
name: postgres
version: 1.0.0
min_doctl_version: "1.82.0"
description: Configure DigitalOcean Managed Postgres with bindable variables or schema isolation. Use when setting up databases, creating users, managing permissions, configuring multi-tenant schemas, or troubleshooting database connectivity on App Platform.
related_skills: [designer, networking]
deprecated: false
---

# Postgres Skill

Configure DigitalOcean Managed Postgres databases with proper security isolation and production-ready defaults.

## Quick Decision

```
Need multiple isolated schemas in one database?
├── YES → Path B (Schema Isolation)
└── NO  → Path A (Bindable Variables) ✅ RECOMMENDED
```

---

## Path A: Bindable Variables (Recommended)

Use when: Single app per database, standard CRUD applications.

### Quick Start

```bash
# 1. Create cluster + user via doctl (DO stores password internally)
doctl databases create my-app-db --engine pg --region nyc3 --size db-s-1vcpu-2gb
CLUSTER_ID=$(doctl databases list --format ID,Name --no-header | grep my-app-db | awk '{print $1}')
doctl databases db create $CLUSTER_ID myappdb
doctl databases user create $CLUSTER_ID myappuser

# 2. Grant permissions (REQUIRED - users have no access by default!)
# Run: scripts/grant_permissions.sql as doadmin

# 3. Reference in app spec
```

```yaml
# .do/app.yaml
databases:
  - name: db
    engine: PG
    production: true
    cluster_name: my-app-db
    db_name: myappdb
    db_user: myappuser

services:
  - name: api
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
```

**Full guide**: See [path-a-bindable-vars.md](reference/path-a-bindable-vars.md)

---

## Path B: Schema Isolation

Use when: Multi-tenant SaaS, multiple apps sharing one cluster, schema-level isolation needed.

### Quick Start

```bash
# Hands-free setup (requires gh CLI)
./scripts/secure_setup.sh \
  --admin-url "$ADMIN_URL" \
  --app-name myapp \
  --schema myapp \
  --repo owner/repo
```

Password flows directly to GitHub Secrets — never displayed.

**Full guide**: See [path-b-schema-isolation.md](reference/path-b-schema-isolation.md)

---

## Available Bindable Variables

| Variable | Example |
|----------|---------|
| `${db.DATABASE_URL}` | `postgresql://user:pass@host:25060/db?sslmode=require` |
| `${db.HOSTNAME}` | `my-db-do-user-123.db.ondigitalocean.com` |
| `${db.PORT}` | `25060` |
| `${db.USERNAME}` | `myappuser` |
| `${db.PASSWORD}` | (auto-populated) |
| `${db.DATABASE}` | `myappdb` |
| `${db.CA_CERT}` | (certificate content) |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/secure_setup.sh` | Hands-free Path B setup with GitHub Secrets |
| `scripts/create_schema_user.py` | Create isolated schema + user |
| `scripts/list_schemas_users.py` | Audit existing schemas/users |
| `scripts/generate_connection_string.py` | Build connection strings |

---

## Reference Files

- **[path-a-bindable-vars.md](reference/path-a-bindable-vars.md)** — Full Path A workflow, connection pools, multi-app setup
- **[path-b-schema-isolation.md](reference/path-b-schema-isolation.md)** — Full Path B workflow, multi-tenant patterns
- **[orm-configurations.md](reference/orm-configurations.md)** — Prisma, SQLAlchemy, Drizzle, TypeORM configs
- **[database-migrations.md](reference/database-migrations.md)** — Alembic, Prisma Migrate, Drizzle Migrate
- **[doctl-reference.md](reference/doctl-reference.md)** — All `doctl databases` commands
- **[troubleshooting.md](reference/troubleshooting.md)** — Common errors and fixes
- **[bundled-scripts.md](reference/bundled-scripts.md)** — Script usage documentation

---

## Common Issues (Quick Fixes)

| Error | Fix |
|-------|-----|
| "permission denied for schema" | Run permission SQL as doadmin |
| "relation does not exist" | Check `search_path` or use schema-qualified names |
| "too many connections" | Create connection pool via doctl |
| "SSL connection required" | Add `?sslmode=require` to connection string |
| Bindable vars not populated | Verify `production: true` and names match exactly |

**Full troubleshooting**: See [troubleshooting.md](reference/troubleshooting.md)

---

## Integration with Other Skills

- **→ designer**: Add database block to app spec
- **→ deployment**: GitHub Actions workflow with DATABASE_URL secret
- **→ devcontainers**: Local Postgres with prod parity
- **→ troubleshooting**: Debug container for connectivity testing
