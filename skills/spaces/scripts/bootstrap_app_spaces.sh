#!/usr/bin/env bash
# Bootstrap Spaces for an application
# Creates: Spaces key, source bucket, log bucket, enables logging
#
# Required env vars:
#   DO_SPACES_REGION      - e.g., nyc3, sfo3, syd1
#   DO_SPACES_ENDPOINT    - e.g., https://nyc3.digitaloceanspaces.com
#   APP_NAME              - Application name (used for naming)
#   SRC_BUCKET            - Source bucket name
#   LOG_BUCKET            - Log bucket name
#   LOG_PREFIX            - Log prefix (e.g., access-logs/myapp/)
#   DO_SPACES_KEY_NAME    - Name for the Spaces key
#
# Optional:
#   SKIP_MINT_KEY=1       - Skip key creation if AWS_* already set

set -euo pipefail
cd "$(dirname "$0")/.."

source scripts/_lib.sh

# Check dependencies
need doctl
need aws
need jq

# Validate required env vars
req_env DO_SPACES_REGION
req_env DO_SPACES_ENDPOINT
req_env APP_NAME
req_env SRC_BUCKET
req_env LOG_BUCKET
req_env LOG_PREFIX
req_env DO_SPACES_KEY_NAME

echo "=============================================="
echo "Bootstrap Spaces for app: ${APP_NAME}"
echo "=============================================="
echo "Region:     ${DO_SPACES_REGION}"
echo "Endpoint:   ${DO_SPACES_ENDPOINT}"
echo "Source:     ${SRC_BUCKET}"
echo "Logs:       ${LOG_BUCKET}"
echo "Prefix:     ${LOG_PREFIX}"
echo "Key Name:   ${DO_SPACES_KEY_NAME}"
echo ""

# Step 1: Create Spaces key (unless skipped)
if [[ "${SKIP_MINT_KEY:-0}" == "1" ]]; then
  info "SKIP_MINT_KEY=1 set; assuming AWS_* credentials already available"
  req_env AWS_ACCESS_KEY_ID
  req_env AWS_SECRET_ACCESS_KEY
else
  mint_spaces_key_to_env "${DO_SPACES_KEY_NAME}"
fi

# Step 2: Create log bucket first (required as logging target)
ensure_bucket "${LOG_BUCKET}"

# Step 3: Create source bucket
ensure_bucket "${SRC_BUCKET}"

# Step 4: Enable access logging
put_logging "${SRC_BUCKET}" "${LOG_BUCKET}" "${LOG_PREFIX}"

# Step 5: Verify
echo ""
echo "=============================================="
echo "Current logging configuration"
echo "=============================================="
get_logging "${SRC_BUCKET}"

echo ""
echo "=============================================="
echo "Bootstrap complete!"
echo "=============================================="
echo ""
echo "NEXT STEPS:"
echo "1. Save the Access Key and Secret Key to your secret manager"
echo "2. Add to GitHub Secrets: SPACES_ACCESS_KEY, SPACES_SECRET_KEY"
echo "3. Reference in your app spec (see SKILL.md)"
echo ""
