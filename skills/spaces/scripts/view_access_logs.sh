#!/usr/bin/env bash
# View and optionally download Spaces access logs
#
# Required env vars:
#   DO_SPACES_ENDPOINT    - e.g., https://nyc3.digitaloceanspaces.com
#   LOG_BUCKET            - Bucket containing logs
#   LOG_PREFIX            - Log prefix (e.g., access-logs/myapp/)
#
# Options:
#   --tail N              - Show only last N log entries (default: show all)
#   --sync                - Download logs to ./spaces-access-logs/
#   --grep PATTERN        - Filter logs by pattern (requires --sync)
#
# Requires AWS credentials to be present (AWS_PROFILE or AWS_* env vars)

set -euo pipefail
cd "$(dirname "$0")/.."

source scripts/_lib.sh

# Check dependencies
need aws

# Validate required env vars
req_env DO_SPACES_ENDPOINT
req_env LOG_BUCKET
req_env LOG_PREFIX

# Parse arguments
TAIL_N=0
DO_SYNC=0
GREP_PATTERN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tail)
      TAIL_N="${2:-50}"
      shift 2
      ;;
    --sync)
      DO_SYNC=1
      shift
      ;;
    --grep)
      GREP_PATTERN="${2:-}"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [--tail N] [--sync] [--grep PATTERN]"
      echo ""
      echo "Options:"
      echo "  --tail N        Show only last N log entries"
      echo "  --sync          Download logs to ./spaces-access-logs/"
      echo "  --grep PATTERN  Filter synced logs by pattern"
      exit 0
      ;;
    *)
      die "Unknown argument: $1 (use --help for usage)"
      ;;
  esac
done

LOG_URI="s3://${LOG_BUCKET}/${LOG_PREFIX}"

echo "=============================================="
echo "Spaces Access Logs"
echo "=============================================="
echo "Location: ${LOG_URI}"
echo ""

echo "--- Log Objects ---"
if [[ "$TAIL_N" -gt 0 ]]; then
  aws_spaces s3 ls "${LOG_URI}" --recursive | tail -n "${TAIL_N}"
else
  aws_spaces s3 ls "${LOG_URI}" --recursive
fi

if [[ "$DO_SYNC" == "1" ]]; then
  echo ""
  echo "--- Syncing Logs Locally ---"
  mkdir -p ./spaces-access-logs
  aws_spaces s3 sync "${LOG_URI}" ./spaces-access-logs/
  echo "Synced to: ./spaces-access-logs/"

  if [[ -n "$GREP_PATTERN" ]]; then
    echo ""
    echo "--- Searching for: ${GREP_PATTERN} ---"
    grep -r "$GREP_PATTERN" ./spaces-access-logs/ || echo "No matches found"
  fi
fi

echo ""
echo "Note: Access logs may take several minutes to appear after bucket activity."
