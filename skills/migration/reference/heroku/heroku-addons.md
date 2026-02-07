# Heroku Add-on Migration Reference

Mapping Heroku add-ons to DigitalOcean managed services and external alternatives.

## Table of Contents

1. [Add-on Detection](#add-on-detection)
2. [Data Services](#data-services)
3. [Caching](#caching)
4. [Queues and Messaging](#queues-and-messaging)
5. [Logging and Monitoring](#logging-and-monitoring)
6. [Email](#email)
7. [Search](#search)
8. [Storage](#storage)
9. [Scheduler](#scheduler)
10. [Other Common Add-ons](#other-common-add-ons)

---

## Add-on Detection

Add-ons are declared in `app.json` or provisioned via CLI. Parse from:

```json
// app.json
{
  "addons": [
    "heroku-postgresql:essential-0",
    "heroku-redis:premium-0",
    {"plan": "heroku-postgresql:essential-0", "options": {"version": "16"}}
  ]
}
```

Also check `heroku.yml`:
```yaml
setup:
  addons:
    - plan: heroku-postgresql:essential-0
```

**Runtime detection**: If no `app.json` or `heroku.yml`, check environment variable references in code for `DATABASE_URL`, `REDIS_URL`, `MONGODB_URI`, `CLOUDAMQP_URL`, etc.

---

## Data Services

| Heroku Add-on | DO Managed Service | App Spec Config | Env Var Binding |
|--------------|-------------------|-----------------|-----------------|
| `heroku-postgresql` | Managed PostgreSQL | `databases: [{engine: PG}]` | `${db.DATABASE_URL}` |
| `jawsdb` (MySQL) | Managed MySQL | `databases: [{engine: MYSQL}]` | `${db.DATABASE_URL}` |
| `mongolab` / `mongohq` | Managed MongoDB | `databases: [{engine: MONGODB}]` | `${db.DATABASE_URL}` |

### PostgreSQL Plan Mapping

| Heroku Plan | DO Equivalent | App Spec | Notes |
|------------|---------------|----------|-------|
| `essential-0` (10K rows) | Dev database | `production: false` | For testing |
| `essential-1` to `essential-2` | Dev database | `production: false` | Small apps |
| `standard-0` and above | Managed DB cluster | `production: true` | Production workloads |
| `premium-0` and above | Managed DB cluster | `production: true` | High availability |

### App Spec Database Example

```yaml
databases:
  - name: db
    engine: PG
    version: "16"
    production: false    # Dev database (test env)
    # production: true   # Managed DB cluster (prod env)
```

---

## Caching

| Heroku Add-on | DO Managed Service | Notes |
|--------------|-------------------|-------|
| `heroku-redis` | **Managed Valkey** | Redis EOL on DO. Valkey is wire-compatible |
| `heroku-valkey` | **Managed Valkey** | Direct mapping |
| `memcachier` | **Managed Valkey** | Valkey supports memcached protocol |
| `rediscloud` | **Managed Valkey** | External option: keep Redis Cloud |

### Valkey App Spec Example

```yaml
databases:
  - name: valkey
    engine: VALKEY
    version: "8"
    production: false    # Dev (test env)
```

### Code Migration for Redis → Valkey

Valkey is a drop-in replacement for Redis. The wire protocol is identical. Changes needed:

1. **Environment variable**: `REDIS_URL` → keep or rename to `VALKEY_URL`
2. **Client library**: No change needed (`redis-py`, `ioredis`, etc. all work with Valkey)
3. **App spec binding**: `${valkey.DATABASE_URL}` for the connection URL
4. **Optional**: Update config/variable names in code for clarity

```yaml
# App spec: keep REDIS_URL key for backward compatibility
envs:
  - key: REDIS_URL
    scope: RUN_TIME
    value: ${valkey.DATABASE_URL}
```

---

## Queues and Messaging

| Heroku Add-on | DO Equivalent | Notes |
|--------------|--------------|-------|
| `cloudamqp` (RabbitMQ) | **No DO managed equivalent** | Keep CloudAMQP (external) OR self-host on Droplet |
| `heroku-kafka` | **Managed Kafka** | `doctl databases create --engine kafka` |
| `amazon-sqs` (via env) | **No DO equivalent** | Keep SQS (external) OR use Kafka |

### Kafka App Spec

```yaml
# Kafka is NOT supported in app spec databases section
# Create separately and reference via environment variable
envs:
  - key: KAFKA_BROKERS
    scope: RUN_TIME
    type: SECRET    # User sets from doctl databases connection-details
```

**Important**: Kafka, unlike Postgres/MySQL/Valkey, is NOT bindable via app spec. Provision separately with `doctl databases create` and set connection details as env vars.

---

## Logging and Monitoring

| Heroku Add-on | Migration Path | Notes |
|--------------|---------------|-------|
| `papertrail` | Keep Papertrail (external) | Update log drain URL to App Platform |
| `logentries` | Keep or migrate to Papertrail | Update log drain URL |
| `coralogix` | Keep Coralogix (external) | Update log drain URL |
| `new-relic` | Keep New Relic (external) | Update env vars (`NEW_RELIC_LICENSE_KEY`) |
| `scout` | Keep Scout (external) | Update env vars |
| `librato` | Keep Librato (external) | Update env vars |
| `heroku-metrics` | App Platform Insights | Built-in, no add-on needed |

**Action**: For all logging/monitoring add-ons, migrate the environment variables to GitHub Secrets. The services themselves remain external.

---

## Email

| Heroku Add-on | Migration Path | Notes |
|--------------|---------------|-------|
| `sendgrid` | Keep SendGrid (external) | Move `SENDGRID_API_KEY` to GitHub Secrets |
| `mailgun` | Keep Mailgun (external) | Move `MAILGUN_API_KEY` to GitHub Secrets |
| `postmark` | Keep Postmark (external) | Move `POSTMARK_API_TOKEN` to GitHub Secrets |
| `sparkpost` | Keep SparkPost (external) | Move env vars to GitHub Secrets |

**Action**: All email providers are external. Only change is credential management (Heroku config vars → GitHub Secrets).

---

## Search

| Heroku Add-on | Migration Path | Notes |
|--------------|---------------|-------|
| `bonsai` (Elasticsearch) | **Managed OpenSearch** | `doctl databases create --engine opensearch` |
| `searchbox` (Elasticsearch) | **Managed OpenSearch** | API-compatible with Elasticsearch |
| `algolia` | Keep Algolia (external) | Move env vars to GitHub Secrets |

### OpenSearch Note

DO Managed OpenSearch is API-compatible with Elasticsearch. If the app uses Elasticsearch client libraries, they typically work with OpenSearch. Check client version compatibility.

---

## Storage

| Heroku Add-on | Migration Path | Notes |
|--------------|---------------|-------|
| `cloudinary` | Keep Cloudinary (external) OR migrate to Spaces | Move env vars to GitHub Secrets |
| `cloudcube` (S3) | **DO Spaces** | S3-compatible API, update endpoint + credentials |
| `bucketeer` (S3) | **DO Spaces** | S3-compatible API, update endpoint + credentials |

### Spaces Migration (from S3-compatible add-ons)

```python
# Heroku (Bucketeer/CloudCube) → DO Spaces
# Change endpoint, keep S3 API pattern

# Before (Heroku add-on)
s3 = boto3.client('s3',
    endpoint_url=os.environ['BUCKETEER_ENDPOINT'],
    aws_access_key_id=os.environ['BUCKETEER_AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['BUCKETEER_AWS_SECRET_ACCESS_KEY']
)

# After (DO Spaces)
s3 = boto3.client('s3',
    endpoint_url=os.environ['SPACES_ENDPOINT'],       # e.g., https://nyc3.digitaloceanspaces.com
    aws_access_key_id=os.environ['SPACES_KEY'],
    aws_secret_access_key=os.environ['SPACES_SECRET']
)
```

---

## Scheduler

| Heroku Add-on | App Platform Equivalent | Notes |
|--------------|------------------------|-------|
| `scheduler` (10 min / hourly / daily) | `jobs` with `kind: CRON_TRIGGER` | No UI, defined in app spec |

### App Spec Cron Job

```yaml
jobs:
  - name: scheduled-task
    kind: CRON_TRIGGER
    cron: "0 */1 * * *"          # Every hour (was: Heroku Scheduler hourly)
    run_command: python tasks/cleanup.py
    instance_size_slug: apps-s-1vcpu-0.5gb
    instance_count: 1
```

### Heroku Scheduler Frequency → Cron Expression

| Heroku Scheduler | Cron Expression | Notes |
|-----------------|-----------------|-------|
| Every 10 minutes | `*/10 * * * *` | |
| Hourly | `0 * * * *` | |
| Daily | `0 0 * * *` | Midnight UTC |

---

## Other Common Add-ons

| Heroku Add-on | Migration Path | Notes |
|--------------|---------------|-------|
| `heroku-exec` (SSH) | `doctl apps console` | Different mechanism |
| `ssl` (SSL endpoint) | Built-in SSL | Free with App Platform, auto-provisioned |
| `pgbackups` | Built-in DB backups | `doctl databases backups list` |
| `heroku-ci` | GitHub Actions | Different CI platform |
| `review-apps` | Preview environments | GitHub integration, different config |

---

## Add-on Migration Checklist Template

For each add-on found in `app.json`:

```
[ ] Identify add-on: <addon-name>:<plan>
[ ] Determine migration path: DO Managed / External (keep) / Replace
[ ] If DO Managed: Add to app spec databases section
[ ] If External: Move env vars from Heroku config to GitHub Secrets
[ ] If Replace: Update code references (client libs, endpoints, env var names)
[ ] Test connectivity from App Platform to service
[ ] Verify data migration plan (if stateful service)
```
