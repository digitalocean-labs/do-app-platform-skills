---
name: spaces
description: Configure DigitalOcean Spaces (S3-compatible object storage) for App Platform applications
version: 1.0.0
author: Bikram Gupta
triggers:
  - "spaces"
  - "object storage"
  - "S3"
  - "file upload"
  - "bucket"
  - "static assets"
  - "static site"
dependencies:
  - designer (may include Spaces in app architecture)
  - deployment (Spaces credentials via GitHub Secrets)
  - devcontainers (MinIO for local S3-compatible storage)
tools:
  required:
    - doctl (for bucket management)
  optional:
    - s3cmd or aws cli (for file operations)
artifacts:
  - spaces-cors.json (CORS configuration)
  - App spec environment variables snippet
---

# Spaces Skill

Configure DigitalOcean Spaces (S3-compatible object storage) for App Platform applications.

---

## Philosophy

**This skill covers DO-specific configuration only.** The LLM already knows:
- S3 SDK usage (boto3, @aws-sdk/client-s3)
- Presigned URL patterns
- Object storage concepts

**This skill teaches:**
- Spaces endpoint URLs and regions
- CORS configuration via Console
- App spec environment variable patterns
- CDN enablement

---

## Credential Handling

Spaces uses Access Key + Secret Key (like AWS S3):

```
┌─────────────────────────────────────────────────────────────────┐
│  RECOMMENDED: GitHub Secrets                                     │
│  ─────────────────────────────────────────────────────────────   │
│  1. User creates Spaces keys in DO Console (API → Spaces Keys)  │
│  2. User adds to GitHub Secrets:                                │
│     - SPACES_ACCESS_KEY                                         │
│     - SPACES_SECRET_KEY                                         │
│  3. App spec references secrets                                 │
│  4. Agent never sees credentials                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start: File Upload Storage

### Step 1: Create Bucket (User Action)

```markdown
## Create Spaces Bucket

1. Go to DigitalOcean Console → Spaces Object Storage
2. Create new Space:
   - Name: myapp-uploads
   - Region: nyc3 (match your app region)
   - File Listing: Restricted (private)
3. Note the endpoint: nyc3.digitaloceanspaces.com
```

### Step 2: Create Access Keys (User Action)

```markdown
## Create Access Keys

1. Go to API → Spaces Keys
2. Generate New Key
3. Save both Access Key and Secret Key securely
4. Add to GitHub Secrets:
   - SPACES_ACCESS_KEY
   - SPACES_SECRET_KEY
```

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

Configure CORS in DO Console (Spaces → Settings → CORS).

### Private Uploads (Presigned URLs)

```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://myapp.com", "https://*.ondigitalocean.app"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3600
    }
  ]
}
```

### Public Assets (CDN)

```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 86400
    }
  ]
}
```

---

## Common Patterns

### Pattern 1: Server-Side Uploads

```
User → App API → Spaces (private bucket)
                    ↓
              Presigned URL for download
```

App handles upload, stores in Spaces, returns presigned download URL.

### Pattern 2: Direct Upload (Presigned URLs)

```
Browser → App API (get presigned URL) → Browser uploads directly to Spaces
```

More efficient for large files — bypasses your server.

> **Warning**: Presigned URLs bypass CDN caching. Files accessed via presigned URLs are served directly from origin, which can result in doubled bandwidth charges if you have CDN enabled. Use presigned URLs for private/authenticated access; use CDN URLs for public static assets.

### Pattern 3: Static Assets with CDN

```
Build process → Spaces (public bucket + CDN)
                    ↓
              Browser loads from CDN edge
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

## SDK Configuration Snippets

### Node.js (@aws-sdk/client-s3)

```javascript
const { S3Client, PutObjectCommand, GetObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');

const s3 = new S3Client({
  endpoint: process.env.SPACES_ENDPOINT,
  region: 'us-east-1', // Required placeholder - actual datacenter determined by endpoint
  forcePathStyle: false, // Use virtual-hosted-style URLs
  credentials: {
    accessKeyId: process.env.SPACES_ACCESS_KEY,
    secretAccessKey: process.env.SPACES_SECRET_KEY,
  },
});
```

### Python (boto3)

```python
import boto3
import os

s3 = boto3.client(
    's3',
    endpoint_url=os.environ['SPACES_ENDPOINT'],
    region_name='us-east-1',  # Required placeholder - actual datacenter determined by endpoint
    aws_access_key_id=os.environ['SPACES_ACCESS_KEY'],
    aws_secret_access_key=os.environ['SPACES_SECRET_KEY'],
)
```

### Go

```go
sess := session.Must(session.NewSession(&aws.Config{
    Endpoint:         aws.String(os.Getenv("SPACES_ENDPOINT")),
    Region:           aws.String("us-east-1"), // Required placeholder - actual datacenter determined by endpoint
    S3ForcePathStyle: aws.Bool(false),         // Use virtual-hosted-style URLs
    Credentials: credentials.NewStaticCredentials(
        os.Getenv("SPACES_ACCESS_KEY"),
        os.Getenv("SPACES_SECRET_KEY"),
        "",
    ),
}))
client := s3.New(sess)
```

---

## doctl Commands

```bash
# List buckets
doctl spaces list

# Create bucket (alternative to Console)
doctl spaces create myapp-uploads --region nyc3

# Delete bucket
doctl spaces delete myapp-uploads --force

# List objects
doctl spaces list-objects myapp-uploads

# Upload file
doctl spaces put myapp-uploads/path/file.txt ./local-file.txt

# Download file
doctl spaces get myapp-uploads/path/file.txt ./local-file.txt
```

---

## Local Development

Use MinIO for local S3-compatible storage:

```yaml
# docker-compose.yml (from devcontainers skill)
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
    volumes:
      - minio-data:/data

volumes:
  minio-data:
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

## Troubleshooting

### "Access Denied"

**Cause**: Wrong credentials or bucket permissions.

**Fix**:
1. Verify keys in GitHub Secrets match DO Console
2. Check bucket is in correct region
3. Ensure bucket policy allows your operation

### "CORS error in browser"

**Cause**: CORS not configured or wrong origin.

**Fix**:
1. Go to Spaces → Settings → CORS
2. Add your app domain to AllowedOrigins
3. Include `https://*.ondigitalocean.app` for App Platform preview URLs

### "SignatureDoesNotMatch"

**Cause**: Endpoint URL mismatch or wrong region.

**Fix**:
```javascript
// Ensure endpoint includes https:// and matches bucket region
endpoint: 'https://nyc3.digitaloceanspaces.com'  // ✓
endpoint: 'nyc3.digitaloceanspaces.com'          // ✗
```

---

## Integration with Other Skills

### → designer skill

Designer includes Spaces environment variables when architecting apps with file storage.

### → deployment skill

Spaces credentials stored in GitHub Secrets, referenced in app spec.

### → devcontainers skill

MinIO provides local Spaces parity for development.

### → sandbox skill

Sandboxes can use Spaces for large file transfers (>250KB).

---

## Documentation Links

- [Spaces Overview](https://docs.digitalocean.com/products/spaces/)
- [Using AWS SDKs with Spaces](https://docs.digitalocean.com/products/spaces/how-to/use-aws-sdks/)
- [Spaces API Reference](https://docs.digitalocean.com/reference/api/spaces-api/)
- [CORS Configuration](https://docs.digitalocean.com/products/spaces/how-to/configure-cors/)
- [CDN](https://docs.digitalocean.com/products/spaces/how-to/enable-cdn/)
- [doctl spaces reference](https://docs.digitalocean.com/reference/doctl/reference/spaces/)
