# SDK Configuration

Configure S3-compatible SDKs for DigitalOcean Spaces.

## Node.js (@aws-sdk/client-s3)

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

// Upload file
await s3.send(new PutObjectCommand({
  Bucket: process.env.SPACES_BUCKET,
  Key: 'uploads/file.txt',
  Body: fileBuffer,
}));

// Generate presigned download URL (1 hour expiry)
const url = await getSignedUrl(s3, new GetObjectCommand({
  Bucket: process.env.SPACES_BUCKET,
  Key: 'uploads/file.txt',
}), { expiresIn: 3600 });
```

## Python (boto3)

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

# Upload file
s3.upload_file('local-file.txt', os.environ['SPACES_BUCKET'], 'uploads/file.txt')

# Generate presigned download URL (1 hour expiry)
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': os.environ['SPACES_BUCKET'], 'Key': 'uploads/file.txt'},
    ExpiresIn=3600
)
```

## Go

```go
import (
    "os"
    "github.com/aws/aws-sdk-go/aws"
    "github.com/aws/aws-sdk-go/aws/credentials"
    "github.com/aws/aws-sdk-go/aws/session"
    "github.com/aws/aws-sdk-go/service/s3"
)

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

// Upload file
_, err := client.PutObject(&s3.PutObjectInput{
    Bucket: aws.String(os.Getenv("SPACES_BUCKET")),
    Key:    aws.String("uploads/file.txt"),
    Body:   bytes.NewReader(data),
})
```

## Environment Variables

All SDKs expect these environment variables:

| Variable | Example |
|----------|---------|
| `SPACES_ENDPOINT` | `https://nyc3.digitaloceanspaces.com` |
| `SPACES_BUCKET` | `myapp-uploads` |
| `SPACES_ACCESS_KEY` | (from DO Console) |
| `SPACES_SECRET_KEY` | (from DO Console) |
