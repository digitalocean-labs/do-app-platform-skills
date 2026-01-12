# AWS CLI Operations for Spaces

Complete reference for managing DigitalOcean Spaces using the AWS CLI.

## Prerequisites

```bash
# Install AWS CLI v2
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Verify
aws --version
```

## Authentication

Spaces uses AWS-compatible credentials. Set via environment variables:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"  # Required placeholder
```

Or use a named profile in `~/.aws/credentials`:

```ini
[spaces]
aws_access_key_id = your-access-key
aws_secret_access_key = your-secret-key
```

Then: `aws --profile spaces ...`

---

## Endpoint Configuration

**Always include `--endpoint-url`** for Spaces operations:

```bash
# Set as variable for convenience
export EP="--endpoint-url https://nyc3.digitaloceanspaces.com"

# Or create an alias
alias aws-spaces='aws --endpoint-url https://nyc3.digitaloceanspaces.com'
```

### Available Endpoints

| Region | Endpoint |
|--------|----------|
| NYC3 | `https://nyc3.digitaloceanspaces.com` |
| SFO3 | `https://sfo3.digitaloceanspaces.com` |
| AMS3 | `https://ams3.digitaloceanspaces.com` |
| SGP1 | `https://sgp1.digitaloceanspaces.com` |
| FRA1 | `https://fra1.digitaloceanspaces.com` |
| SYD1 | `https://syd1.digitaloceanspaces.com` |

---

## Bucket Operations

### List Buckets

```bash
aws $EP s3 ls
```

### Create Bucket

```bash
aws $EP s3api create-bucket --bucket myapp-uploads

# Verify
aws $EP s3api head-bucket --bucket myapp-uploads
```

### Delete Bucket

Bucket must be empty first:

```bash
# Empty the bucket
aws $EP s3 rm s3://myapp-uploads --recursive

# Delete bucket
aws $EP s3 rb s3://myapp-uploads

# Force delete (empties and removes)
aws $EP s3 rb s3://myapp-uploads --force
```

### Check If Bucket Exists

```bash
aws $EP s3api head-bucket --bucket myapp-uploads 2>/dev/null && echo "exists" || echo "not found"
```

---

## Object Operations

### Upload File

```bash
# Single file
aws $EP s3 cp ./local-file.txt s3://myapp-uploads/path/file.txt

# With content type
aws $EP s3 cp ./image.png s3://myapp-uploads/images/photo.png \
  --content-type "image/png"

# With cache control (for CDN)
aws $EP s3 cp ./bundle.js s3://myapp-uploads/js/bundle.js \
  --cache-control "max-age=31536000"

# Make public
aws $EP s3 cp ./public.txt s3://myapp-uploads/public.txt \
  --acl public-read
```

### Download File

```bash
aws $EP s3 cp s3://myapp-uploads/path/file.txt ./local-file.txt
```

### List Objects

```bash
# List top-level
aws $EP s3 ls s3://myapp-uploads/

# List recursively
aws $EP s3 ls s3://myapp-uploads/ --recursive

# Human-readable sizes
aws $EP s3 ls s3://myapp-uploads/ --recursive --human-readable

# Summarize (count and size)
aws $EP s3 ls s3://myapp-uploads/ --recursive --summarize
```

### Delete Object

```bash
# Single object
aws $EP s3 rm s3://myapp-uploads/path/file.txt

# Multiple objects (by prefix)
aws $EP s3 rm s3://myapp-uploads/temp/ --recursive

# Dry run (show what would be deleted)
aws $EP s3 rm s3://myapp-uploads/temp/ --recursive --dryrun
```

### Copy/Move Objects

```bash
# Copy within bucket
aws $EP s3 cp s3://myapp-uploads/old/file.txt s3://myapp-uploads/new/file.txt

# Move (copy + delete)
aws $EP s3 mv s3://myapp-uploads/old/file.txt s3://myapp-uploads/new/file.txt

# Copy between buckets
aws $EP s3 cp s3://bucket-a/file.txt s3://bucket-b/file.txt
```

---

## Sync Operations

Sync is idempotent - only transfers changed files:

```bash
# Upload directory
aws $EP s3 sync ./local-dir/ s3://myapp-uploads/prefix/

# Download directory
aws $EP s3 sync s3://myapp-uploads/prefix/ ./local-dir/

# Delete files in destination not in source
aws $EP s3 sync ./local-dir/ s3://myapp-uploads/prefix/ --delete

# Exclude patterns
aws $EP s3 sync ./local-dir/ s3://myapp-uploads/prefix/ \
  --exclude "*.tmp" --exclude ".git/*"

# Include only specific patterns
aws $EP s3 sync ./local-dir/ s3://myapp-uploads/prefix/ \
  --exclude "*" --include "*.jpg" --include "*.png"

# Dry run
aws $EP s3 sync ./local-dir/ s3://myapp-uploads/prefix/ --dryrun
```

---

## CORS Configuration

### Get Current CORS

```bash
aws $EP s3api get-bucket-cors --bucket myapp-uploads
```

### Set CORS

```bash
cat > /tmp/cors.json << 'EOF'
{
  "CORSRules": [{
    "AllowedOrigins": ["https://myapp.com", "https://*.ondigitalocean.app"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }]
}
EOF

aws $EP s3api put-bucket-cors \
  --bucket myapp-uploads \
  --cors-configuration file:///tmp/cors.json
```

### Delete CORS

```bash
aws $EP s3api delete-bucket-cors --bucket myapp-uploads
```

---

## Access Logging

### Enable Logging

```bash
aws $EP s3api put-bucket-logging \
  --bucket myapp-uploads \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "myapp-logs",
      "TargetPrefix": "access-logs/myapp/"
    }
  }'
```

### Get Logging Status

```bash
aws $EP s3api get-bucket-logging --bucket myapp-uploads
```

### Disable Logging

```bash
aws $EP s3api put-bucket-logging \
  --bucket myapp-uploads \
  --bucket-logging-status '{}'
```

---

## ACL (Access Control)

### Get Bucket ACL

```bash
aws $EP s3api get-bucket-acl --bucket myapp-uploads
```

### Get Object ACL

```bash
aws $EP s3api get-object-acl --bucket myapp-uploads --key path/file.txt
```

### Set Object ACL

```bash
# Make public
aws $EP s3api put-object-acl \
  --bucket myapp-uploads \
  --key path/file.txt \
  --acl public-read

# Make private
aws $EP s3api put-object-acl \
  --bucket myapp-uploads \
  --key path/file.txt \
  --acl private
```

---

## Presigned URLs

Generate temporary URLs for private objects:

```bash
# Download URL (default 1 hour)
aws $EP s3 presign s3://myapp-uploads/private/file.txt

# Custom expiration (seconds)
aws $EP s3 presign s3://myapp-uploads/private/file.txt --expires-in 3600
```

> **Note**: For upload presigned URLs, use the SDK (boto3, @aws-sdk/client-s3) instead of CLI.

---

## Multipart Uploads

For large files (>100MB recommended):

### List In-Progress Uploads

```bash
aws $EP s3api list-multipart-uploads --bucket myapp-uploads
```

### Abort Stale Uploads

```bash
# Get upload ID from list-multipart-uploads
aws $EP s3api abort-multipart-upload \
  --bucket myapp-uploads \
  --key path/large-file.zip \
  --upload-id "upload-id-here"
```

> **Tip**: The `aws s3 cp` command automatically uses multipart for large files.

---

## Useful Patterns

### Idempotent Bucket Creation

```bash
bucket_exists() {
  aws $EP s3api head-bucket --bucket "$1" 2>/dev/null
}

ensure_bucket() {
  if bucket_exists "$1"; then
    echo "Bucket exists: $1"
  else
    aws $EP s3api create-bucket --bucket "$1"
    echo "Created bucket: $1"
  fi
}

ensure_bucket "myapp-uploads"
```

### Batch Upload with Progress

```bash
aws $EP s3 sync ./assets/ s3://myapp-uploads/assets/ \
  --only-show-errors \
  && echo "Upload complete"
```

### Find Large Objects

```bash
aws $EP s3 ls s3://myapp-uploads/ --recursive --human-readable \
  | sort -k3 -h | tail -20
```

### Count Objects

```bash
aws $EP s3 ls s3://myapp-uploads/ --recursive | wc -l
```

### Calculate Total Size

```bash
aws $EP s3 ls s3://myapp-uploads/ --recursive --summarize \
  | grep "Total Size"
```
