# Database Configuration Reference

Complete guide to configuring databases in App Platform specs.

---

## Database Types

App Platform supports two database types:

| Type | Creation | Management | Cost |
|------|----------|------------|------|
| **Dev Database** | Automatic | App Platform | ~$7/mo |
| **Managed Database** | Manual (doctl/console) | DO Databases | Varies |

---

## Dev Databases

Dev databases are fully managed by App Platform. They don't appear in your DO Databases console.

### Supported Engines

| Engine | Dev DB Available |
|--------|------------------|
| PostgreSQL (`PG`) | Yes |
| Valkey (`VALKEY`) | Yes |
| MySQL (`MYSQL`) | No |
| MongoDB (`MONGODB`) | No |
| Kafka (`KAFKA`) | No |
| OpenSearch (`OPENSEARCH`) | No |

### Dev Database Configuration

```yaml
databases:
  - name: db
    engine: PG
    production: false  # or omit entirely
    version: "16"      # optional: 13, 14, 15, 16
```

**Characteristics:**
- $7/month, 1GB storage limit
- PostgreSQL and Valkey only
- Good for development, testing, small production apps
- Automatically provides bindable variables
- Cannot configure trusted sources

### Dev Valkey Configuration

```yaml
databases:
  - name: cache
    engine: VALKEY
    production: false
```

---

## Managed Databases

Managed databases are full DigitalOcean Managed Database clusters.

**You must create the cluster first**, then reference it in your app spec.

### Step 1: Create Cluster

```bash
# PostgreSQL
doctl databases create my-app-db \
  --engine pg \
  --region nyc \
  --size db-s-1vcpu-1gb \
  --version 16

# Valkey
doctl databases create my-app-cache \
  --engine valkey \
  --region nyc \
  --size db-s-1vcpu-1gb

# MySQL
doctl databases create my-app-mysql \
  --engine mysql \
  --region nyc \
  --size db-s-1vcpu-1gb \
  --version 8

# MongoDB
doctl databases create my-app-mongo \
  --engine mongodb \
  --region nyc \
  --size db-s-1vcpu-1gb
```

### Step 2: Create Database and User

```bash
# Get cluster ID
CLUSTER_ID=$(doctl databases list --format ID,Name --no-header | grep my-app-db | awk '{print $1}')

# Create database within cluster
doctl databases db create $CLUSTER_ID myappdb

# Create user (DO generates and stores password)
doctl databases user create $CLUSTER_ID myappuser
```

### Step 3: Reference in App Spec

```yaml
databases:
  - name: db
    engine: PG
    production: true
    cluster_name: my-app-db
    db_name: myappdb
    db_user: myappuser
```

**Important:** Users must be created via DigitalOcean interface (console, API, doctl)—not via raw SQL. App Platform retrieves credentials only for DO-managed users.

---

## Database Decision Tree

```
What data storage do you need?
├── Relational data?
│   ├── PostgreSQL OK? → PG (dev DB available)
│   └── MySQL required? → MYSQL (managed only)
├── Caching/sessions/queues? → VALKEY (dev DB available)
├── Document store? → MONGODB (managed only)
├── Search? → OPENSEARCH (managed only)
└── Event streaming? → KAFKA (managed only, special setup)

Dev DB or Managed?
├── Testing/small app (<1GB data)? → Dev DB (production: false)
└── Production/scaling/features? → Managed (production: true)
    └── Create cluster first: doctl databases create ...
```

---

## Bindable Variables

Both dev and managed databases expose connection details via bindable variables.

| Variable | Description | Example |
|----------|-------------|---------|
| `${db.DATABASE_URL}` | Full connection string | `postgresql://user:pass@host:25060/db?sslmode=require` |
| `${db.HOSTNAME}` | Database host | `cluster-do-user-123.db.ondigitalocean.com` |
| `${db.PORT}` | Database port | `25060` |
| `${db.USERNAME}` | Database user | `myappuser` |
| `${db.PASSWORD}` | Database password | (auto-populated) |
| `${db.DATABASE}` | Database name | `myappdb` |
| `${db.CA_CERT}` | CA certificate | (certificate content) |

Replace `db` with your database component name.

### Usage

```yaml
services:
  - name: api
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
```

---

## Connection Pools (PostgreSQL Only)

For high-traffic apps, use connection pools.

### Create Pool

```bash
# Via console: Databases → Cluster → Connection Pools → Add
# Or via API
```

### Reference in App Spec

```yaml
envs:
  - key: DATABASE_POOL_URL
    scope: RUN_TIME
    value: ${db.my-pool-name.DATABASE_URL}
```

Where `my-pool-name` is the pool name you created.

---

## Valkey/Redis Configuration

Use Valkey for caching, sessions, or queues. Redis is EOL on DigitalOcean.

### Dev Valkey

```yaml
databases:
  - name: cache
    engine: VALKEY
    production: false
```

### Managed Valkey

```bash
doctl databases create my-app-cache --engine valkey --region nyc --size db-s-1vcpu-1gb
```

```yaml
databases:
  - name: cache
    engine: VALKEY
    production: true
    cluster_name: my-app-cache
```

### Usage

```yaml
envs:
  - key: VALKEY_URL
    scope: RUN_TIME
    value: ${cache.DATABASE_URL}

  # For legacy Redis clients
  - key: REDIS_URL
    scope: RUN_TIME
    value: ${cache.DATABASE_URL}
```

---

## Trusted Sources

Managed databases can restrict connections to trusted sources.

### Without VPC

App Platform can be added automatically:

```bash
doctl databases firewalls append <cluster-id> --rule app:<app-id>
```

### With VPC (Recommended)

Add the app's VPC egress private IP:

```bash
# Find IP from inside container
ip addr show | grep "inet 10\."

# Add to firewall
doctl databases firewalls append <cluster-id> --rule ip_addr:10.x.x.x
```

### Limitations

| Engine | Trusted Sources Support |
|--------|------------------------|
| PostgreSQL | Yes |
| MySQL | Yes |
| Valkey | Yes |
| MongoDB | Yes |
| Kafka | **No** — must be disabled |
| OpenSearch | Limited — breaks log forwarding |

**Build time:** Cannot connect with trusted sources enabled. Use PRE_DEPLOY job for migrations.

---

## Debug Pattern

Deploy a minimal Alpine worker to verify database connectivity:

```yaml
workers:
  - name: debug
    image:
      registry_type: DOCKER_HUB
      registry: library
      repository: alpine
      tag: latest
    run_command: sleep infinity
    instance_size_slug: apps-s-1vcpu-0.5gb
    envs:
      - key: DB_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: DB_HOST
        scope: RUN_TIME
        value: ${db.HOSTNAME}
```

Deploy, then use Console tab to verify:

```bash
echo $DB_URL
echo $DB_HOST
```

Remove debug worker once verified.

---

## Complete Examples

### Single Database

```yaml
name: my-app
region: nyc

services:
  - name: api
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}

databases:
  - name: db
    engine: PG
    production: false
```

### PostgreSQL + Valkey

```yaml
databases:
  - name: db
    engine: PG
    production: false

  - name: cache
    engine: VALKEY
    production: false

services:
  - name: api
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: VALKEY_URL
        scope: RUN_TIME
        value: ${cache.DATABASE_URL}
```

### Production Managed Database

```yaml
databases:
  - name: db
    engine: PG
    production: true
    cluster_name: prod-db
    db_name: myapp
    db_user: myappuser

services:
  - name: api
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `${db.X}` not resolving | Typo in database name | Verify `name:` matches |
| "cluster not found" | Cluster doesn't exist | Create via `doctl databases create` |
| "user not found" | User created via SQL | Create via `doctl databases user create` |
| Connection refused | Trusted sources | Add app to firewall rules |
| SSL error | Missing sslmode | `DATABASE_URL` includes it automatically |

---

## See Also

- **[postgres skill](../../postgres/SKILL.md)** — Advanced PostgreSQL patterns
- **[managed-db-services skill](../../managed-db-services/SKILL.md)** — MySQL, MongoDB, Kafka, OpenSearch
- **[networking skill](../../networking/SKILL.md)** — VPC and trusted sources setup
