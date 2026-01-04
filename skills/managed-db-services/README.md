# Managed Database Services Skill

Configure DigitalOcean Managed MySQL, MongoDB, Valkey (Redis), Kafka, and OpenSearch for App Platform applications.

## What This Skill Does

- Configures **bindable variables** for managed database connections
- Sets up **trusted sources** for secure database access
- Provides engine-specific connection patterns (SSL, auth, ports)
- Documents **critical constraints** (Kafka limitations, VPC behavior)

## Quick Start

```yaml
# Add managed database to app spec
databases:
  - name: db
    engine: MYSQL        # or MONGODB, REDIS, KAFKA, OPENSEARCH
    production: true     # REQUIRED for bindable variables
    cluster_name: my-cluster
    db_user: myappuser

services:
  - name: api
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
```

## Key Decisions This Skill Makes

| Decision | Default | Rationale |
|----------|---------|-----------|
| Dev databases | PostgreSQL only | Other engines require `production: true` |
| Trusted sources | VPC CIDR for VPC apps | `app:` rules whitelist public IP only |
| Kafka access | IP-based rules | `app:` rules not supported for Kafka |
| SSL mode | Required | All engines require TLS |

## Files

- `SKILL.md` — Complete skill documentation with decision tree
- `reference/mysql.md` — Connection pools, user privileges
- `reference/mongodb.md` — User roles, authSource configuration
- `reference/valkey.md` — Eviction policies, SSL protocol
- `reference/kafka.md` — SASL auth, SSL certs, Schema Registry
- `reference/opensearch.md` — ACLs, logging limitations

## Integration

| Direction | Skill | Integration |
|-----------|-------|-------------|
| → | designer | Generates `databases:` block |
| → | deployment | Bindable vars handle credentials |
| → | networking | VPC + trusted sources |
| → | troubleshooting | Debug container for connectivity |

## Related Skills

- **postgres** — For complex PostgreSQL (schema isolation, multi-tenant)
- **designer** — Include databases in app architecture
- **networking** — Configure VPC and trusted sources
