#!/usr/bin/env bash
# Enable or verify bucket access logging (idempotent)
#
# Required env vars:
#   DO_SPACES_ENDPOINT    - e.g., https://nyc3.digitaloceanspaces.com
#   SRC_BUCKET            - Source bucket to enable logging on
#   LOG_BUCKET            - Target bucket for logs
#   LOG_PREFIX            - Log prefix (e.g., access-logs/myapp/)
#
# Requires AWS credentials to be present (AWS_PROFILE or AWS_* env vars)

set -euo pipefail
cd "$(dirname "$0")/.."

source scripts/_lib.sh

# Check dependencies
need aws
need jq

# Validate required env vars
req_env DO_SPACES_ENDPOINT
req_env SRC_BUCKET
req_env LOG_BUCKET
req_env LOG_PREFIX

# Verify AWS credentials are available
if [[ -z "${AWS_ACCESS_KEY_ID:-}" && -z "${AWS_PROFILE:-}" ]]; then
  die "AWS credentials required. Set AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or AWS_PROFILE"
fi

echo "=============================================="
echo "Enable Bucket Logging"
echo "=============================================="
echo "Source:  ${SRC_BUCKET}"
echo "Target:  ${LOG_BUCKET}"
echo "Prefix:  ${LOG_PREFIX}"
echo ""

# Ensure log bucket exists
ensure_bucket "${LOG_BUCKET}"

# Enable logging
put_logging "${SRC_BUCKET}" "${LOG_BUCKET}" "${LOG_PREFIX}"

# Verify
echo ""
echo "=============================================="
echo "Verification"
echo "=============================================="
get_logging "${SRC_BUCKET}"
