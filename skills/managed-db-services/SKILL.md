---
name: managed-db-services
description: Configure DigitalOcean Managed MySQL, MongoDB, Valkey, Kafka, and OpenSearch for App Platform using bindable variables
version: 1.0.0
author: Bikram Gupta
triggers:
  - "mysql"
  - "mongodb"
  - "mongo"
  - "valkey"
  - "redis"
  - "kafka"
  - "opensearch"
  - "elasticsearch"
  - "managed database"
dependencies:
  - designer (for app spec database attachment)
  - deployment (for GitHub Actions integration)
  - postgres (for complex multi-tenant patterns — use postgres skill instead)
tools:
  required:
    - doctl (authenticated)
  optional:
    - Database-specific CLI (mysql, mongosh, etc.)
---

# Managed Database Services Skill

Configure DigitalOcean Managed MySQL, MongoDB, Valkey (Redis), Kafka, and OpenSearch for App Platform applications.

---

## Philosophy

**This skill covers DO-specific configuration only.** The LLM already knows:
- SQL syntax, queries, ORMs (Prisma, Drizzle, SQLAlchemy)
- MongoDB aggregation pipelines, Mongoose
- Redis commands, caching patterns
- Kafka producer/consumer patterns
- OpenSearch/Elasticsearch queries

**This skill teaches:**
- Bindable variable names and patterns
- doctl commands for cluster/user management
- Trusted sources (firewall) configuration
- App spec attachment syntax

---

## Critical Constraints

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    APP PLATFORM DATABASE LIMITATIONS                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DEV DATABASES (production: false)                                           │
│  ─────────────────────────────────────────────────────────────────────────   │
│  • Only PostgreSQL supported (not MySQL, MongoDB, Kafka, etc.)               │
│  • Cannot create additional databases — only default database available      │
│  • Region-locked to app region — cannot migrate independently                │
│  • If app migrates to new region, dev DB becomes inaccessible                │
│                                                                              │
│  TRUSTED SOURCES + BUILD PHASE                                               │
│  ─────────────────────────────────────────────────────────────────────────   │
│  • Cannot connect to managed DBs with trusted sources during BUILD phase     │
│  • App's network info is only available AFTER build completes                │
│  • Run-time connections with trusted sources work fine                       │
│  • Workaround: Use PRE_DEPLOY job (runs at runtime) for migrations           │
│                                                                              │
│  ENGINE-SPECIFIC CONSTRAINTS                                                 │
│  ─────────────────────────────────────────────────────────────────────────   │
│  • Kafka: Trusted sources NOT supported at all — must be disabled            │
│  • OpenSearch: Logging doesn't work with trusted sources enabled             │
│           (regular database connections still work)                          │
│  • MongoDB: Database names cannot contain capital letters in app spec        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Trusted Sources: Build vs Run Time

| Phase | Trusted Sources | Works? |
|-------|-----------------|--------|
| **Build time** | Enabled | ❌ No — app network not yet configured |
| **Run time** | Enabled | ✅ Yes — app is trusted source |
| **PRE_DEPLOY job** | Enabled | ✅ Yes — runs at runtime |
| **Kafka (any phase)** | Enabled | ❌ No — not supported at all |

**If you need DB access during build** (e.g., Prisma generate with introspection):
1. Temporarily disable trusted sources, OR
2. Move DB operations to a PRE_DEPLOY job

### VPC + Trusted Sources: The Correct Workflow

**Recommended:** Use VPC + IP-based trusted sources for production databases.

> **Critical:** With VPC enabled, you cannot simply add "App Platform" to trusted sources. You must find the app's **VPC egress private IP** and whitelist that specific IP address.

**Step 1:** Enable VPC in your app spec:
```yaml
vpc:
  id: <your-vpc-uuid>
```

**Step 2:** Deploy the app and find the VPC egress IP:
```bash
# From inside the container
doctl apps console <app_id> <component>
ip addr show | grep "inet 10\."
# Look for 10.x.x.x — this is your VPC egress IP
```

**Step 3:** Add the IP to database trusted sources:
```bash
CLUSTER_ID=$(doctl databases list --format ID,Name --no-header | grep my-db | awk '{print $1}')

# Use ip_addr rule (NOT app rule) for VPC
doctl databases firewalls append $CLUSTER_ID --rule ip_addr:10.x.x.x
```

**Why this matters:**
- `--rule app:<app-id>` only works when NOT using VPC
- With VPC, traffic comes from the VPC egress IP, not the app's public identity
- The database firewall only sees the IP address, not the app ID

### Trusted Sources Compatibility by Engine

| Engine | Trusted Sources | VPC Support | Notes |
|--------|-----------------|-------------|-------|
| PostgreSQL | ✅ Supported | ✅ Yes | Use VPC egress IP |
| MySQL | ✅ Supported | ✅ Yes | Use VPC egress IP |
| MongoDB | ✅ Supported | ✅ Yes | Use VPC egress IP |
| Valkey/Redis | ✅ Supported | ✅ Yes | Use VPC egress IP |
| **Kafka** | ❌ **NOT SUPPORTED** | ✅ Yes | Must disable trusted sources |
| OpenSearch | ⚠️ Partial | ✅ Yes | Logging requires trusted sources disabled |

---

## Common Pattern: Bindable Variables

All DO Managed Databases use the same bindable variable pattern:

```yaml
# .do/app.yaml
databases:
  - name: db                      # Component name (used in ${db.VAR_NAME})
    engine: <ENGINE>              # MYSQL, MONGODB, REDIS, KAFKA, OPENSEARCH
    production: true              # REQUIRED for bindable variables
    cluster_name: my-cluster      # Must match existing cluster name
    db_name: myappdb              # Database within cluster (where applicable)
    db_user: myappuser            # User created via doctl

services:
  - name: api
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}   # Auto-populated by App Platform
```

### Available Bindable Variables (All Engines)

| Variable | Description |
|----------|-------------|
| `${db.DATABASE_URL}` | Full connection string |
| `${db.HOSTNAME}` | Database host |
| `${db.PORT}` | Database port |
| `${db.USERNAME}` | Database user |
| `${db.PASSWORD}` | Database password (auto-populated) |
| `${db.DATABASE}` | Database name |
| `${db.CA_CERT}` | CA certificate for TLS |

Where `db` is the component name from your app spec.

---

## Common doctl Commands (All Engines)

```bash
# List all database clusters
doctl databases list

# Get cluster details
doctl databases get <cluster-id>

# Create user (DO manages password — you never see it)
doctl databases user create <cluster-id> <username>

# List users
doctl databases user list <cluster-id>

# Create database within cluster
doctl databases db create <cluster-id> <db-name>

# List databases
doctl databases db list <cluster-id>

# Get connection details
doctl databases connection <cluster-id>

# Trusted sources (firewall)
doctl databases firewalls append <cluster-id> --rule app:<app-id>
doctl databases firewalls list <cluster-id>
```

---

## MySQL

### Create Cluster and User

```bash
# Create cluster
doctl databases create my-mysql \
  --engine mysql \
  --region nyc3 \
  --size db-s-1vcpu-2gb \
  --version 8

# Get cluster ID
CLUSTER_ID=$(doctl databases list --format ID,Name --no-header | grep my-mysql | awk '{print $1}')

# Create database
doctl databases db create $CLUSTER_ID myappdb

# Create user (DO stores password internally)
doctl databases user create $CLUSTER_ID myappuser

# Add App Platform to trusted sources
APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | grep my-app | awk '{print $1}')
doctl databases firewalls append $CLUSTER_ID --rule app:$APP_ID
```

### App Spec

```yaml
databases:
  - name: db
    engine: MYSQL
    production: true
    cluster_name: my-mysql
    db_name: myappdb
    db_user: myappuser

services:
  - name: api
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      # Or individual components:
      - key: MYSQL_HOST
        value: ${db.HOSTNAME}
      - key: MYSQL_PORT
        value: ${db.PORT}
      - key: MYSQL_USER
        value: ${db.USERNAME}
      - key: MYSQL_PASSWORD
        value: ${db.PASSWORD}
      - key: MYSQL_DATABASE
        value: ${db.DATABASE}
```

### Connection String Format

```
mysql://<user>:<password>@<host>:25060/<database>?ssl-mode=REQUIRED
```

### MySQL-Specific Notes

| Constraint | Details |
|------------|---------|
| Port | **25060** (not standard 3306) |
| SSL | Required (`ssl-mode=REQUIRED`) |
| Default database | `defaultdb` — cannot be deleted |
| Default user | `doadmin` — cannot be deleted |
| Trusted sources | Supported |
| Admin users | **Cannot create additional admins** — only `doadmin` has full privileges |

### Password Encryption

MySQL 8+ uses `caching_sha2_password` by default. Some older applications (PHP 7.1 and older) may have connection issues.

**Change via Console**: Databases → my-mysql → Users & Databases → More → Edit Password Encryption

| Encryption | Compatibility |
|------------|---------------|
| `caching_sha2_password` | MySQL 8+ default, more secure |
| `mysql_native_password` | Legacy, for older PHP/apps |

### Restricted Databases (Read-Only)

Users can SELECT from but cannot INSERT/UPDATE these system databases:

- `mysql`
- `sys`
- `metrics_user_telegraf`
- `performance_schema`
- `information_schema`

### User Privileges

Privileges are managed via SQL (not Console). Connect as `doadmin` and use GRANT/REVOKE:

```sql
-- Grant all on specific database
GRANT ALL ON myappdb.* TO 'myappuser'@'%';

-- Grant read-only
GRANT SELECT ON myappdb.* TO 'readonly_user'@'%';

-- Grant with ability to grant others
GRANT ALL ON myappdb.* TO 'myappuser'@'%' WITH GRANT OPTION;

-- Revoke privileges
REVOKE ALL ON myappdb.* FROM 'myappuser'@'%';

-- View privileges
SHOW GRANTS FOR 'myappuser';
```

### Connection Pools

```bash
# Create pool
doctl databases pool create $CLUSTER_ID myapp_pool \
  --db myappdb \
  --mode transaction \
  --size 25 \
  --user myappuser

# Reference in app spec
# value: ${db.myapp_pool.DATABASE_URL}
```

---

## MongoDB

### Create Cluster and User

```bash
# Create cluster
doctl databases create my-mongo \
  --engine mongodb \
  --region nyc3 \
  --size db-s-1vcpu-2gb \
  --version 7

CLUSTER_ID=$(doctl databases list --format ID,Name --no-header | grep my-mongo | awk '{print $1}')

# Create user
doctl databases user create $CLUSTER_ID myappuser

# Add to trusted sources
doctl databases firewalls append $CLUSTER_ID --rule app:$APP_ID
```

### App Spec

```yaml
databases:
  - name: db
    engine: MONGODB
    production: true
    cluster_name: my-mongo
    db_user: myappuser

services:
  - name: api
    envs:
      - key: MONGODB_URI
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
```

### Connection String Format

```
mongodb+srv://<user>:<password>@<host>/<database>?tls=true&authSource=admin
```

### MongoDB-Specific Notes

| Constraint | Details |
|------------|---------|
| Database naming | **Cannot contain capital letters** in app spec |
| Database creation | No separate `db_name` — created on first write |
| Connection string | Use `authSource=admin` |
| Replica set | Auto-configured by DO |
| Trusted sources | Supported (unlike Kafka) |
| Default users | `doadmin` (admin), `do-readonly` — cannot be deleted |
| User creation | **Must use DO interface** (Console/API/doctl) — not mongo shell |

### User Roles (API Only)

New users created via Console get admin permissions by default. For read-only or read-write users, use the API:

| Role | Permissions |
|------|-------------|
| Admin | Full access (default via Console) |
| Read/Write | Read and write to all databases |
| Read-Only | Read-only access |

```bash
# Create read-only user via API (not available in Console)
curl -X POST "https://api.digitalocean.com/v2/databases/$CLUSTER_ID/users" \
  -H "Authorization: Bearer $DO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "readonly-user", "role": "read-only"}'
```

---

## Valkey (Redis-Compatible)

### Create Cluster

```bash
# Create cluster
doctl databases create my-valkey \
  --engine redis \
  --region nyc3 \
  --size db-s-1vcpu-2gb \
  --version 7

CLUSTER_ID=$(doctl databases list --format ID,Name --no-header | grep my-valkey | awk '{print $1}')

# Add to trusted sources
doctl databases firewalls append $CLUSTER_ID --rule app:$APP_ID
```

### App Spec

```yaml
databases:
  - name: cache
    engine: REDIS
    production: true
    cluster_name: my-valkey

services:
  - name: api
    envs:
      - key: REDIS_URL
        scope: RUN_TIME
        value: ${cache.DATABASE_URL}
      # Or individual:
      - key: REDIS_HOST
        value: ${cache.HOSTNAME}
      - key: REDIS_PORT
        value: ${cache.PORT}
      - key: REDIS_PASSWORD
        value: ${cache.PASSWORD}
```

### Connection String Format

```
rediss://default:<password>@<host>:25061
```

### Valkey-Specific Notes

| Constraint | Details |
|------------|---------|
| Engine in app spec | `REDIS` (Valkey is Redis-compatible drop-in) |
| Protocol | `rediss://` (with SSL) — NOT `redis://` |
| Port | **25061** (not the standard 6379) |
| Default user | `default` (not configurable) |
| Database number | Always db 0 (no multi-db support) |
| Default eviction | `noeviction` — Valkey stops accepting writes when full |
| Trusted sources | Supported (unlike Kafka) |

### Eviction Policies

Default is `noeviction` which can cause Valkey to stop responding when memory is full.

**Change via Console**: Databases → my-valkey → Settings → Eviction Policy

| Policy | Behavior | Use Case |
|--------|----------|----------|
| `noeviction` | Error when full (default) | When app manages key deletion |
| `allkeys-lru` | Evict least recently used | **Recommended for caching** |
| `allkeys-lfu` | Evict least frequently used | Hot/cold data patterns |
| `volatile-ttl` | Evict keys with shortest TTL | When you set explicit TTLs |

> **Tip**: Use `INFO` command to monitor cache hits/misses and tune eviction policy.

---

## Kafka

> **Critical**: App Platform does NOT support Kafka with trusted sources enabled. You must disable trusted sources on the Kafka cluster before integrating with App Platform.

### Create Cluster

```bash
# Create cluster (use General Purpose for Schema Registry support)
doctl databases create my-kafka \
  --engine kafka \
  --region nyc3 \
  --size db-s-2vcpu-4gb \
  --version 3.7

CLUSTER_ID=$(doctl databases list --format ID,Name --no-header | grep my-kafka | awk '{print $1}')

# Create topic
doctl databases topics create $CLUSTER_ID my-topic \
  --partitions 3 \
  --replication-factor 2

# IMPORTANT: Do NOT add trusted sources for Kafka
# App Platform cannot connect to Kafka with trusted sources enabled
# doctl databases firewalls append $CLUSTER_ID --rule app:$APP_ID  # DON'T DO THIS
```

### Create Users with Permissions

Kafka user permissions are set at creation time:

```bash
# Create user via Console: Databases → my-kafka → Users & Topics tab
# Available permissions:
# - Admin: Manage Topics + read/write all Topics
# - Produce: Write to all Topics
# - Consume: Read from all Topics
# - Consume and Produce: Read and write all Topics

# Via doctl (creates with default permissions)
doctl databases user create $CLUSTER_ID myappuser
```

### App Spec

```yaml
databases:
  - name: kafka
    engine: KAFKA
    production: true
    cluster_name: my-kafka

services:
  - name: api
    envs:
      # Recommended bindable variable pattern
      - key: KAFKA_BROKER
        scope: RUN_TIME
        value: ${kafka.HOSTNAME}:${kafka.PORT}
      - key: KAFKA_USERNAME
        scope: RUN_TIME
        value: ${kafka.USERNAME}
      - key: KAFKA_PASSWORD
        scope: RUN_TIME
        value: ${kafka.PASSWORD}
      - key: KAFKA_CA_CERT
        scope: RUN_TIME
        value: ${kafka.CA_CERT}
```

### Bindable Variables for Kafka

| Variable | Description |
|----------|-------------|
| `${kafka.HOSTNAME}` | Kafka broker hostname |
| `${kafka.PORT}` | Kafka broker port |
| `${kafka.USERNAME}` | Authentication username |
| `${kafka.PASSWORD}` | Authentication password |
| `${kafka.CA_CERT}` | CA certificate for TLS |

**Note**: Combine hostname and port for broker address: `${kafka.HOSTNAME}:${kafka.PORT}`

### SASL Authentication

DO Kafka uses SASL/SCRAM-SHA-256:

```javascript
// Node.js (kafkajs)
const kafka = new Kafka({
  brokers: [process.env.KAFKA_BROKER],
  ssl: true,
  sasl: {
    mechanism: 'scram-sha-256',
    username: process.env.KAFKA_USERNAME,
    password: process.env.KAFKA_PASSWORD,
  },
});
```

```python
# Python (confluent-kafka)
from confluent_kafka import Producer

producer = Producer({
    'bootstrap.servers': os.environ['KAFKA_BROKER'],
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'SCRAM-SHA-256',
    'sasl.username': os.environ['KAFKA_USERNAME'],
    'sasl.password': os.environ['KAFKA_PASSWORD'],
})
```

### Schema Registry (General Purpose Plans Only)

Schema Registry validates message structures and prevents data corruption.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHEMA REGISTRY REQUIREMENTS                                           │
├─────────────────────────────────────────────────────────────────────────┤
│  • Only available on General Purpose plans (not shared CPU)             │
│  • Must be enabled via Console: Databases → Settings → Schema Registry │
│  • Available on port 25065 using same hostname                          │
│  • If downscaling to shared CPU, must disable Schema Registry first     │
└─────────────────────────────────────────────────────────────────────────┘
```

**Enable via Console**: Databases → my-kafka → Settings → Schema Registry → Toggle On

**Schema Registry URL**: `https://<kafka-hostname>:25065`

### Kafka-Specific Notes

| Constraint | Details |
|------------|---------|
| Minimum size | `db-s-2vcpu-4gb` (Kafka requires more resources) |
| Trusted sources | **NOT SUPPORTED** — must be disabled |
| Authentication | SASL/SCRAM-SHA-256 required |
| Default retention | 7 days |
| Topic management | `doctl databases topics` commands |
| Schema Registry | General Purpose plans only, port 25065 |
| Default user | `doadmin` (cannot be deleted) |

---

## OpenSearch

### Create Cluster

```bash
# Create cluster
doctl databases create my-opensearch \
  --engine opensearch \
  --region nyc3 \
  --size db-s-2vcpu-4gb \
  --version 2

CLUSTER_ID=$(doctl databases list --format ID,Name --no-header | grep my-opensearch | awk '{print $1}')

# Create user
doctl databases user create $CLUSTER_ID myappuser

# Add to trusted sources
doctl databases firewalls append $CLUSTER_ID --rule app:$APP_ID
```

### App Spec

```yaml
databases:
  - name: search
    engine: OPENSEARCH
    production: true
    cluster_name: my-opensearch
    db_user: myappuser

services:
  - name: api
    envs:
      - key: OPENSEARCH_URL
        scope: RUN_TIME
        value: https://${search.USERNAME}:${search.PASSWORD}@${search.HOSTNAME}:${search.PORT}
```

### OpenSearch-Specific Notes

| Constraint | Details |
|------------|---------|
| Protocol | HTTPS with basic auth |
| Port | Typically 25060 |
| Compatibility | Elasticsearch clients work (OpenSearch is a fork) |
| Dashboard | Available at cluster URL |
| Default user | `doadmin` — cannot be deleted |
| User management | **API/CLI only** — Console doesn't support user management |
| Trusted sources | Supported for database connections |
| **Logging** | ⚠️ **NOT supported with trusted sources enabled** |

> **Note**: If you want App Platform to send logs to OpenSearch, you must disable trusted sources on the OpenSearch cluster. Regular database connections (queries, indexing) work fine with trusted sources.

### Access Control Lists (ACLs)

For fine-grained access control, use the API to create ACLs:

```bash
# List current ACLs
curl -X GET "https://api.digitalocean.com/v2/databases/$CLUSTER_ID/opensearch/acl" \
  -H "Authorization: Bearer $DO_TOKEN"

# Update ACLs (example: restrict user to specific index pattern)
curl -X PUT "https://api.digitalocean.com/v2/databases/$CLUSTER_ID/opensearch/acl" \
  -H "Authorization: Bearer $DO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "acl_enabled": true,
    "acls": [
      {"username": "myappuser", "index": "logs-*", "permission": "readwrite"}
    ]
  }'
```

---

## Troubleshooting

### "Connection refused"

**Cause**: App not in trusted sources.

**Fix**:
```bash
doctl databases firewalls append <cluster-id> --rule app:<app-id>
```

### "Access denied"

**Cause**: User not created via doctl or permissions not set.

**Fix**:
```bash
# Verify user exists
doctl databases user list <cluster-id>

# Create if missing
doctl databases user create <cluster-id> <username>
```

### "Bindable variables not populated"

**Cause**: Missing `production: true` or name mismatch.

**Fix**: Ensure app spec has:
```yaml
databases:
  - name: db
    production: true              # REQUIRED
    cluster_name: exact-name      # Must match doctl output exactly
```

### "SSL required"

**Cause**: Connection string missing SSL flag.

**Fix**: All DO managed databases require SSL. Ensure connection uses:
- MySQL: `?ssl-mode=REQUIRED`
- MongoDB: `?tls=true`
- Redis: `rediss://` (not `redis://`)
- Kafka: `security.protocol: 'SASL_SSL'`
- OpenSearch: `https://`

---

## When to Use Postgres Skill Instead

Use the **postgres skill** for:
- Schema isolation (multi-tenant)
- Complex permission management
- Multiple apps sharing one cluster with separate schemas
- Connection pool configuration
- Custom user privileges

This skill (managed-db-services) is for straightforward:
- One database per app
- Standard bindable variable patterns
- Basic cluster + user setup

---

## Integration with Other Skills

### → designer skill

Designer generates database attachment in app spec:

```yaml
databases:
  - name: db
    engine: MYSQL  # or MONGODB, REDIS, KAFKA, OPENSEARCH
    production: true
    cluster_name: my-cluster
```

### → deployment skill

No additional GitHub Secrets needed for DO managed services — bindable variables handle credentials automatically.

### → troubleshooting skill

For runtime connectivity issues, use troubleshooting skill's container debug pattern to verify environment variables.

---

## Documentation Links

- [Managed Databases Overview](https://docs.digitalocean.com/products/databases/)
- [MySQL](https://docs.digitalocean.com/products/databases/mysql/)
- [MongoDB](https://docs.digitalocean.com/products/databases/mongodb/)
- [Redis/Valkey](https://docs.digitalocean.com/products/databases/redis/)
- [Kafka](https://docs.digitalocean.com/products/databases/kafka/)
- [OpenSearch](https://docs.digitalocean.com/products/databases/opensearch/)
- [doctl databases reference](https://docs.digitalocean.com/reference/doctl/reference/databases/)
