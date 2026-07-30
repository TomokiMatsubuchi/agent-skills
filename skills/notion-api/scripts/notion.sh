#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "usage: $0 METHOD /v1/path [JSON|@FILE]" >&2
  exit 2
fi

token=${NOTION_API_KEY:-}
if [[ -z "$token" ]]; then
  echo "NOTION_API_KEY is not set" >&2
  exit 2
fi

method=$1
path=$2
version=${NOTION_VERSION:-2026-03-11}

if [[ "$path" != /v1/* ]]; then
  echo "path must start with /v1/" >&2
  exit 2
fi

args=(
  --silent --show-error --fail-with-body
  --request "$method"
  "https://api.notion.com$path"
  --header "Authorization: Bearer $token"
  --header "Notion-Version: $version"
  --header "Content-Type: application/json"
)

if [[ $# -eq 3 ]]; then
  args+=(--data-binary "$3")
fi

curl "${args[@]}"
