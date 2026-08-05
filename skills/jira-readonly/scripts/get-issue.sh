#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 <base_url> <email> <api_token> <issue_key>" >&2
  exit 2
fi

base_url=${1%/}
issue_key=$4

if [[ ! "$issue_key" =~ ^[A-Z][A-Z0-9_]*-[1-9][0-9]*$ ]]; then
  echo "Invalid Jira issue key: $issue_key" >&2
  exit 2
fi

curl --fail-with-body --silent --show-error \
  --user "$2:$3" \
  --header 'Accept: application/json' \
  "$base_url/rest/api/3/issue/$issue_key"
