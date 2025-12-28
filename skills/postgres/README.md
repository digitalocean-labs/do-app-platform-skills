# Postgres Skill

Part of the **App Platform Skills** router. Configures DigitalOcean Managed Postgres databases with two distinct paths based on use case.

## Key Insight: Bindable Variables

**DigitalOcean stores credentials for users created via their interface** (Console, API, `doctl`). App Platform can automatically retrieve these credentials and populate bindable variables like `${db.DATABASE_URL}`.

This means for most apps, **you never need to manually manage database passwords**.

## Two Paths

| Aspect | **Path A: Bindable Variables** | **Path B: Schema Isolation** |
|--------|-------------------------------|------------------------------|
| User creation | `doctl databases user create` | Raw SQL (`CREATE USER`) |
| Password management | **DO manages automatically** | You manage (GitHub Secrets) |
| App spec integration | `${db.DATABASE_URL}` | Manual env vars |
| Use case | **Most apps** | Multi-tenant SaaS |
| Permission setup | Required via doadmin | Required via doadmin |

## Location

```
skills/postgres/
├── SKILL.md                          # Main skill document (v2.1)
├── scripts/
│   ├── secure_setup.sh               # 🔐 Hands-free setup (bash)
│   ├── secure_setup.py               # 🔐 Hands-free setup (python)
│   ├── create_schema_user.py         # Create schema + user (Path B manual)
│   ├── list_schemas_users.py         # Audit schemas and permissions
│   ├── generate_connection_string.py # Generate connection strings
│   ├── add_client.py                 # Add tenant (multi-tenant setup)
│   ├── cleanup_client.py             # Remove tenant
│   └── get_admin_conn.sh             # Helper: get admin connection via doctl
└── templates/
    ├── orm/
    │   ├── prisma.template.prisma
    │   ├── sqlalchemy.template.py
    │   └── drizzle.template.ts
    └── migrations/
        └── alembic.template.py
```

## Quick Start: Path A (Recommended)

```bash
# 1. Create database and user via doctl
CLUSTER_ID=$(doctl databases list --format ID,Name --no-header | grep my-cluster | awk '{print $1}')
doctl databases db create $CLUSTER_ID myappdb
doctl databases user create $CLUSTER_ID myappuser

# 2. Grant permissions (REQUIRED - even with Path A!)
ADMIN_URL=$(doctl databases connection $CLUSTER_ID --format Uri --no-header)
psql "$ADMIN_URL" -c "GRANT CONNECT ON DATABASE myappdb TO myappuser;"
psql "$ADMIN_URL" -d myappdb -c "GRANT ALL ON SCHEMA public TO myappuser;"

# 3. Reference in app spec with bindable variables
# See SKILL.md for full app spec example
```

## Quick Start: Path B (Schema Isolation)

**Option 1: Hands-Free Secure Setup (Recommended)**

```bash
# Single command — password never visible, goes straight to GitHub Secrets
./scripts/secure_setup.sh \
  --admin-url "$ADMIN_URL" \
  --app-name myapp \
  --schema myapp \
  --repo owner/repo \
  --env production
```

**Option 2: Manual Setup**

```bash
# Generate SQL files
python scripts/create_schema_user.py myapp myapp_user "$(openssl rand -base64 32)" \
  --generate --output-dir ./sql

# Review and execute
psql "$ADMIN_URL" -f sql/db-setup.sql
psql "$ADMIN_URL" -f sql/db-users.sql  
psql "$ADMIN_URL" -f sql/db-permissions.sql

# Store credentials in GitHub Secrets manually
gh secret set DATABASE_URL --repo owner/repo --body "postgresql://..."
```

## The Permission Gap

**Critical**: Even with Path A, users created via doctl have NO permissions by default. You must still:

```sql
-- As doadmin
GRANT CONNECT ON DATABASE myappdb TO myappuser;
\c myappdb
GRANT ALL ON SCHEMA public TO myappuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO myappuser;
```

## Integration with Router

This skill is called when user mentions:
- "database", "postgres", "schema", "permissions", "connection string", "bindable variables"

It integrates with:
- **designer**: For app spec database attachment
- **deployment**: For GitHub Secrets (Path B only)
- **dev-containers**: For local Postgres matching production
- **troubleshooting**: For connectivity issues
