# Spaces Troubleshooting

Detailed troubleshooting for common DigitalOcean Spaces issues.

## Setup

All examples assume:
```bash
export EP="--endpoint-url https://nyc3.digitaloceanspaces.com"
```

---

## BucketAlreadyExists (409)

**Cause**: Bucket name is already taken (globally unique namespace).

**Symptoms**:
```
An error occurred (BucketAlreadyExists): The requested bucket name is not available.
```

**Fix**:

1. If it's your bucket, treat as success (idempotent check):
```bash
# Check if bucket exists and is yours
aws $EP s3api head-bucket --bucket myapp-uploads 2>/dev/null \
  && echo "Bucket exists and accessible" \
  || aws $EP s3api create-bucket --bucket myapp-uploads
```

2. If bucket belongs to someone else, choose a different name:
```bash
# Add company/project prefix
aws $EP s3api create-bucket --bucket mycompany-myapp-uploads
```

**Best practice**: Use naming convention `<company>-<project>-<purpose>` to avoid conflicts.

---

## Access Denied (403)

**Cause**: Wrong credentials, bucket permissions, or region mismatch.

**Symptoms**:
```
An error occurred (AccessDenied): Access Denied
```

**Diagnostic steps**:

1. Verify credentials are set:
```bash
echo "Access Key: ${AWS_ACCESS_KEY_ID:0:8}..."  # First 8 chars only
[[ -n "$AWS_SECRET_ACCESS_KEY" ]] && echo "Secret Key: (set)" || echo "Secret Key: NOT SET"
```

2. Verify bucket region matches endpoint:
```bash
# If bucket is in nyc3, endpoint must be:
export EP="--endpoint-url https://nyc3.digitaloceanspaces.com"

# Wrong region = Access Denied
```

3. Check bucket exists and is accessible:
```bash
aws $EP s3api head-bucket --bucket myapp-uploads
# Exit code 0 = exists and accessible
# Exit code 254 = exists but no access (wrong key)
# Exit code 255 = doesn't exist
```

4. List buckets to verify key works at all:
```bash
aws $EP s3 ls
# If this fails, your credentials are wrong
```

5. Regenerate keys if necessary:
```bash
# Create new key
doctl spaces keys create "myapp-new-key" --output json

# Update AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
# Then delete old key
```

---

## CORS Error in Browser

**Cause**: CORS not configured or missing your app origin.

**Symptoms**:
```
Access to XMLHttpRequest at 'https://bucket.nyc3.digitaloceanspaces.com/...'
from origin 'https://myapp.com' has been blocked by CORS policy
```

**Diagnostic**:

```bash
# Check current CORS config
aws $EP s3api get-bucket-cors --bucket myapp-uploads
# Error means no CORS configured
```

**Fix**:

1. Create CORS configuration:
```bash
cat > /tmp/cors.json << 'EOF'
{
  "CORSRules": [
    {
      "AllowedOrigins": [
        "https://myapp.com",
        "https://*.ondigitalocean.app"
      ],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3600
    }
  ]
}
EOF
```

2. Apply CORS:
```bash
aws $EP s3api put-bucket-cors \
  --bucket myapp-uploads \
  --cors-configuration file:///tmp/cors.json
```

3. Include `https://*.ondigitalocean.app` for App Platform preview URLs

4. Wait 1-2 minutes for CORS changes to propagate

**Verify**:
```bash
aws $EP s3api get-bucket-cors --bucket myapp-uploads
```

---

## SignatureDoesNotMatch

**Cause**: Endpoint URL format issue or clock skew.

**Symptoms**:
```
An error occurred (SignatureDoesNotMatch): The request signature we calculated does not match the signature you provided.
```

**Fix**:

1. Ensure endpoint includes `https://`:
```bash
# Correct
export EP="--endpoint-url https://nyc3.digitaloceanspaces.com"

# Wrong - missing protocol
export EP="--endpoint-url nyc3.digitaloceanspaces.com"
```

2. Ensure no trailing slash:
```bash
# Correct
--endpoint-url https://nyc3.digitaloceanspaces.com

# Wrong - trailing slash
--endpoint-url https://nyc3.digitaloceanspaces.com/
```

3. Check system clock (signature includes timestamp):
```bash
# Compare with NTP server
date
curl -s http://worldtimeapi.org/api/ip | jq .datetime

# If off by more than 15 minutes, sync:
# Linux
sudo ntpdate pool.ntp.org
# macOS
sudo sntp -sS pool.ntp.org
```

4. Verify secret key has no extra whitespace:
```bash
# Check for trailing newline or space
echo -n "$AWS_SECRET_ACCESS_KEY" | xxd | tail -1
# Should end with the last character of your key, not 0a (newline) or 20 (space)
```

---

## SlowDown (503)

**Cause**: Rate limiting - too many requests.

**Symptoms**:
```
An error occurred (SlowDown): Please reduce your request rate.
```

**Fix**:

1. Implement exponential backoff in your application:
```python
import time
import random

def upload_with_retry(s3_client, bucket, key, body, max_retries=5):
    for attempt in range(max_retries):
        try:
            return s3_client.put_object(Bucket=bucket, Key=key, Body=body)
        except s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'SlowDown':
                wait = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")
```

2. For CLI, add delays between operations:
```bash
for file in ./files/*; do
  aws $EP s3 cp "$file" s3://myapp-uploads/
  sleep 0.5  # Half second delay
done
```

3. Use batch operations where possible:
```bash
# Instead of many individual uploads
aws $EP s3 sync ./local-dir/ s3://myapp-uploads/prefix/
```

4. Consider CDN for high-traffic reads

---

## Upload Succeeds but File Not Found

**Cause**: Eventual consistency, wrong bucket/key, or region mismatch.

**Diagnostic**:
```bash
# List bucket contents
aws $EP s3 ls s3://myapp-uploads/uploads/

# Check if file exists with exact key
aws $EP s3api head-object --bucket myapp-uploads --key uploads/file.txt
```

**Fix**:

1. Wait a few seconds after upload before reading
2. Verify bucket name and key path are correct
3. Check if uploading to wrong bucket (environment mismatch):
```bash
# Verify which endpoint you're using
echo $EP

# List all buckets to find your file
aws $EP s3 ls s3://myapp-uploads/ --recursive | grep file.txt
```

---

## InvalidAccessKeyId

**Cause**: Access key doesn't exist or was deleted.

**Symptoms**:
```
An error occurred (InvalidAccessKeyId): The Access Key Id you provided does not exist in our records.
```

**Fix**:

1. Verify the key exists:
```bash
doctl spaces keys list --format ID,Name
```

2. If key was deleted, create new one:
```bash
doctl spaces keys create "myapp-spaces-key" --output json
```

3. Update your credentials:
```bash
export AWS_ACCESS_KEY_ID="new-key-id"
export AWS_SECRET_ACCESS_KEY="new-secret"
```

---

## NoSuchBucket

**Cause**: Bucket doesn't exist or wrong region.

**Symptoms**:
```
An error occurred (NoSuchBucket): The specified bucket does not exist.
```

**Fix**:

1. List all buckets to verify name:
```bash
aws $EP s3 ls
```

2. Check if bucket is in a different region:
```bash
# Try different endpoints
aws --endpoint-url https://nyc3.digitaloceanspaces.com s3 ls
aws --endpoint-url https://sfo3.digitaloceanspaces.com s3 ls
aws --endpoint-url https://ams3.digitaloceanspaces.com s3 ls
```

3. Create bucket if it doesn't exist:
```bash
aws $EP s3api create-bucket --bucket myapp-uploads
```

---

## Connection Timeout / Network Errors

**Cause**: Network issues, firewall, or endpoint problems.

**Symptoms**:
```
Could not connect to the endpoint URL
Connection timed out
```

**Fix**:

1. Verify endpoint is reachable:
```bash
curl -I https://nyc3.digitaloceanspaces.com
# Should return HTTP 403 (expected without auth)
```

2. Check DNS resolution:
```bash
nslookup nyc3.digitaloceanspaces.com
```

3. Check for firewall blocking HTTPS (port 443):
```bash
nc -zv nyc3.digitaloceanspaces.com 443
```

4. Try a different endpoint/region to rule out regional issues

---

## Large File Upload Fails

**Cause**: Timeout, memory issues, or network interruption.

**Symptoms**:
```
Upload failed partway through
Connection reset
```

**Fix**:

1. Use multipart upload (automatic for files >8MB with `aws s3 cp`):
```bash
# aws CLI handles multipart automatically
aws $EP s3 cp ./large-file.zip s3://myapp-uploads/large-file.zip
```

2. For very large files, increase multipart threshold:
```bash
aws configure set s3.multipart_threshold 64MB
aws configure set s3.multipart_chunksize 16MB
```

3. Resume interrupted uploads:
```bash
# List incomplete multipart uploads
aws $EP s3api list-multipart-uploads --bucket myapp-uploads

# Abort stale uploads
aws $EP s3api abort-multipart-upload \
  --bucket myapp-uploads \
  --key large-file.zip \
  --upload-id "upload-id-from-list"
```

---

## Debugging Checklist

When troubleshooting, check these in order:

1. **Credentials set?**
   ```bash
   [[ -n "$AWS_ACCESS_KEY_ID" ]] && echo "Access Key: set" || echo "Access Key: NOT SET"
   ```

2. **Correct endpoint?**
   ```bash
   echo "Endpoint: $EP"
   ```

3. **Key still valid?**
   ```bash
   doctl spaces keys list --format Name | grep myapp
   ```

4. **Bucket exists?**
   ```bash
   aws $EP s3 ls | grep myapp-uploads
   ```

5. **Can list bucket contents?**
   ```bash
   aws $EP s3 ls s3://myapp-uploads/
   ```

6. **Clock synchronized?**
   ```bash
   date
   ```
