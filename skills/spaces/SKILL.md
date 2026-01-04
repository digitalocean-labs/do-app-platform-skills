---
name: spaces
description: Configure DigitalOcean Spaces (S3-compatible object storage) for App Platform applications. Use when setting up file uploads, static asset hosting, CDN-backed storage, or presigned URL workflows.
---

# Spaces Skill

Configure DigitalOcean Spaces (S3-compatible object storage) for App Platform applications.

## Philosophy

**This skill covers DO-specific configuration only.** Claude already knows S3 SDK usage, presigned URL patterns, and object storage concepts.

**This skill teaches:** Spaces endpoint URLs, CORS configuration, app spec patterns, and CDN enablement.

> **Tip**: For complex multi-step projects, consider using the **planner** skill. For an overview of all skills, see the [root SKILL.md](../../SKILL.md).

---

## Credential Handling

Spaces uses Access Key + Secret Key (like AWS S3). Store in GitHub Secrets:

1. User creates Spaces keys in DO Console (API → Spaces Keys)
2. User adds to GitHub Secrets: `SPACES_ACCESS_KEY`, `SPACES_SECRET_KEY`
3. App spec references secrets
4. Agent never sees credentials

---

## Quick Start: File Upload Storage

### Step 1: Create Bucket

**Option A: s3cmd (Recommended if configured)**

```bash
# Check if s3cmd is configured for Spaces
grep "host_base" ~/.s3cfg  # Should show: *.digitaloceanspaces.com

# Create bucket
s3cmd mb s3://myapp-uploads

# Verify
s3cmd ls
```

> **Note**: `doctl spaces` manages API keys, NOT buckets. Use s3cmd or Console for bucket operations.

**Option B: Console**

1. Go to DigitalOcean Console → Spaces Object Storage
2. Create Space: name `myapp-uploads`, region `nyc3`, File Listing: Restricted
3. Note endpoint: `nyc3.digitaloceanspaces.com`

### Step 2: Create Access Keys (User Action)

1. Go to API → Spaces Keys
2. Generate New Key
3. Add to GitHub Secrets: `SPACES_ACCESS_KEY`, `SPACES_SECRET_KEY`

### Step 3: App Spec Configuration

```yaml
services:
  - name: api
    envs:
      - key: SPACES_BUCKET
        value: myapp-uploads
      - key: SPACES_REGION
        value: nyc3
      - key: SPACES_ENDPOINT
        value: https://nyc3.digitaloceanspaces.com
      - key: SPACES_ACCESS_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${SPACES_ACCESS_KEY}
      - key: SPACES_SECRET_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${SPACES_SECRET_KEY}
```

---

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `SPACES_BUCKET` | Bucket name | `myapp-uploads` |
| `SPACES_REGION` | Region code | `nyc3`, `sfo3`, `ams3`, `sgp1`, `fra1` |
| `SPACES_ENDPOINT` | API endpoint | `https://nyc3.digitaloceanspaces.com` |
| `SPACES_ACCESS_KEY` | Access key ID | (from DO Console) |
| `SPACES_SECRET_KEY` | Secret access key | (from DO Console) |
| `SPACES_CDN_ENDPOINT` | CDN URL (if enabled) | `https://myapp-uploads.nyc3.cdn.digitaloceanspaces.com` |

---

## CORS Configuration

Configure in DO Console (Spaces → Settings → CORS).

### Private Uploads (Presigned URLs)

```json
{
  "CORSRules": [{
    "AllowedOrigins": ["https://myapp.com", "https://*.ondigitalocean.app"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }]
}
```

### Public Assets (CDN)

```json
{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 86400
  }]
}
```

---

## Common Patterns

### Pattern 1: Server-Side Uploads

```
User → App API → Spaces (private bucket) → Presigned URL for download
```

App handles upload, stores in Spaces, returns presigned download URL.

### Pattern 2: Direct Upload (Presigned URLs)

```
Browser → App API (get presigned URL) → Browser uploads directly to Spaces
```

More efficient for large files — bypasses your server.

> **Warning**: Presigned URLs bypass CDN caching. Use presigned URLs for private access; use CDN URLs for public static assets.

### Pattern 3: Static Assets with CDN

```
Build process → Spaces (public bucket + CDN) → Browser loads from CDN edge
```

Best for images, CSS, JS bundles.

---

## URL Patterns

| Type | URL Format |
|------|------------|
| Standard | `https://<bucket>.<region>.digitaloceanspaces.com/<key>` |
| CDN | `https://<bucket>.<region>.cdn.digitaloceanspaces.com/<key>` |
| Custom Domain | `https://assets.myapp.com/<key>` (requires DNS setup) |

**Examples:**
```
Standard: https://myapp-uploads.nyc3.digitaloceanspaces.com/images/photo.jpg
CDN:      https://myapp-uploads.nyc3.cdn.digitaloceanspaces.com/images/photo.jpg
```

---

## SDK Configuration

For SDK setup in Node.js, Python, and Go, see [sdk-configuration.md](reference/sdk-configuration.md).

Quick example (Node.js):
```javascript
const s3 = new S3Client({
  endpoint: process.env.SPACES_ENDPOINT,
  region: 'us-east-1', // Required placeholder
  credentials: {
    accessKeyId: process.env.SPACES_ACCESS_KEY,
    secretAccessKey: process.env.SPACES_SECRET_KEY,
  },
});
```

---

## doctl Commands

```bash
# List buckets
doctl spaces list

# Create bucket
doctl spaces create myapp-uploads --region nyc3

# Delete bucket
doctl spaces delete myapp-uploads --force

# List objects
doctl spaces list-objects myapp-uploads

# Upload/download
doctl spaces put myapp-uploads/path/file.txt ./local.txt
doctl spaces get myapp-uploads/path/file.txt ./local.txt
```

---

## Local Development

Use MinIO for local S3-compatible storage:

```yaml
# docker-compose.yml
services:
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
```

Local environment variables:
```bash
SPACES_ENDPOINT=http://localhost:9000
SPACES_REGION=us-east-1
SPACES_ACCESS_KEY=minioadmin
SPACES_SECRET_KEY=minioadmin
SPACES_BUCKET=local-bucket
```

---

## Quick Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| BucketAlreadyExists (409) | Name taken globally | Use unique prefix: `mycompany-myapp-uploads` |
| Access Denied (403) | Wrong credentials/region | Verify keys match DO Console, check region |
| CORS error | Origin not allowed | Add domain to CORS in Spaces Settings |
| SignatureDoesNotMatch | Endpoint format wrong | Use `https://nyc3.digitaloceanspaces.com` (no trailing slash) |
| SlowDown (503) | Rate limiting | Implement exponential backoff |

**Full troubleshooting guide**: See [troubleshooting.md](reference/troubleshooting.md)

---

## Reference Files

- **[sdk-configuration.md](reference/sdk-configuration.md)** — Node.js, Python, Go SDK setup
- **[troubleshooting.md](reference/troubleshooting.md)** — Detailed error resolution

---

## Integration with Other Skills

- **→ designer**: Includes Spaces environment variables when architecting apps
- **→ deployment**: Spaces credentials stored in GitHub Secrets
- **→ devcontainers**: MinIO provides local Spaces parity

---

## Documentation Links

- [Spaces Overview](https://docs.digitalocean.com/products/spaces/)
- [Using AWS SDKs with Spaces](https://docs.digitalocean.com/products/spaces/how-to/use-aws-sdks/)
- [CORS Configuration](https://docs.digitalocean.com/products/spaces/how-to/configure-cors/)
- [CDN](https://docs.digitalocean.com/products/spaces/how-to/enable-cdn/)
