# Code Refactoring Reference

Code changes required when migrating to DigitalOcean App Platform.

---

## Environment Variable Updates

### Python: DATABASE_URL Fix

```python
# Before (Heroku-specific)
DATABASE_URL = os.environ.get('DATABASE_URL')
# Heroku uses postgres:// which SQLAlchemy doesn't like
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# After (App Platform)
DATABASE_URL = os.environ.get('DATABASE_URL')
# App Platform uses postgresql:// already - no modification needed
```

### Node.js: Port Binding

```javascript
// Before (Heroku)
const PORT = process.env.PORT || 3000;

// After (App Platform) - same pattern works!
const PORT = process.env.PORT || 8080;  // Default 8080 is more common
```

---

## AWS SDK Removal/Replacement

### Secrets Manager to Environment Variables

```python
# Before (AWS Secrets Manager)
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='myapp/prod/db')

# After (App Platform) - use environment variables directly
import os
DATABASE_URL = os.environ['DATABASE_URL']  # Set via GitHub Secrets
```

---

## S3 to Spaces Migration

Spaces uses an S3-compatible API, so code changes are minimal.

### Python (boto3)

```python
# Before (AWS S3)
import boto3
s3 = boto3.client('s3',
    region_name='us-east-1',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
)

# After (Spaces - S3 compatible)
import boto3
s3 = boto3.client('s3',
    endpoint_url=os.environ['SPACES_ENDPOINT'],  # https://nyc3.digitaloceanspaces.com
    region_name=os.environ['SPACES_REGION'],      # nyc3
    aws_access_key_id=os.environ['SPACES_KEY'],
    aws_secret_access_key=os.environ['SPACES_SECRET']
)
```

### Node.js (AWS SDK v3)

```javascript
// Before (AWS S3)
const { S3Client } = require('@aws-sdk/client-s3');
const s3 = new S3Client({ region: 'us-east-1' });

// After (Spaces)
const s3 = new S3Client({
  endpoint: process.env.SPACES_ENDPOINT,
  region: process.env.SPACES_REGION,
  credentials: {
    accessKeyId: process.env.SPACES_KEY,
    secretAccessKey: process.env.SPACES_SECRET
  },
  forcePathStyle: true
});
```

---

## Redis to Valkey Migration

Redis is EOL on DigitalOcean. Use Valkey (Redis-compatible).

### Python (redis-py)

```python
# Before (Heroku Redis)
import redis
r = redis.from_url(os.environ['REDIS_URL'])

# After (Valkey) - same client works!
import redis
r = redis.from_url(os.environ['VALKEY_URL'])
```

### Node.js (ioredis)

```javascript
// Before
const Redis = require('ioredis');
const redis = new Redis(process.env.REDIS_URL);

// After - same client works!
const redis = new Redis(process.env.VALKEY_URL);
```

### Environment Variable Rename

Update all code references:
- `REDIS_URL` -> `VALKEY_URL`
- `REDIS_HOST` -> `VALKEY_HOST`
- `REDIS_PORT` -> `VALKEY_PORT`

---

## Branch Strategy

The skill creates branches for different environments:

```bash
# User specifies:
# - test_branch: "migrate/test"
# - prod_branch: "migrate/prod"

# Skill creates:
# migrate/test
#   |-- .do/app.yaml (dev database, smaller instances)
#   |-- .do/deploy.template.yaml
#   |-- MIGRATION.md
#   |-- (refactored code)

# migrate/prod
#   |-- .do/app.yaml (managed database, production instances)
#   |-- .do/deploy.template.yaml
#   |-- MIGRATION.md
#   |-- (refactored code)
```

---

## Git Operations

### Create Migration Branch

```bash
git checkout -b migrate/test
```

### Commit Migration Changes

```bash
git add .
git commit -m "Migration to DigitalOcean App Platform

- Added .do/app.yaml
- Added .do/deploy.template.yaml
- Updated environment variable references
- Created MIGRATION.md checklist"

git push origin migrate/test
```

---

## Data Migration

### PostgreSQL (from Heroku)

```bash
# 1. Export from Heroku
heroku pg:backups:capture --app myapp
heroku pg:backups:download --app myapp

# 2. Create DO database (if using managed)
doctl databases create myapp-db --engine pg --region nyc --size db-s-1vcpu-1gb

# 3. Get connection string
doctl databases connection myapp-db --format URI

# 4. Restore
pg_restore -d "postgresql://..." latest.dump
```

### Files (S3/Cloudinary to Spaces)

```bash
# Sync from old bucket to Spaces
aws s3 sync s3://old-bucket s3://new-bucket \
  --endpoint-url https://nyc3.digitaloceanspaces.com
```

---

## Troubleshooting Code Changes

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Port binding fails | Wrong PORT handling | Bind to `$PORT` or `0.0.0.0:8080` |
| Database connection fails | Wrong URL format | Ensure `${db.DATABASE_URL}` binding |
| S3 upload fails | Missing endpoint_url | Add Spaces endpoint configuration |
| Redis connection fails | Using wrong env var | Update to `VALKEY_URL` |

### Debug Locally

```bash
# Test locally with Docker
docker build -t test .
docker run -p 8080:8080 -e PORT=8080 test
```
