#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 4 ] || [ "$#" -gt 6 ]; then
  echo "Usage: $0 <base_url> <email> <api_token> <jql> [max_results] [next_page_token]" >&2
  exit 2
fi

base_url=${1%/}
max_results=${5:-20}

if [[ ! "$max_results" =~ ^[1-9][0-9]*$ ]]; then
  echo "max_results must be a positive integer" >&2
  exit 2
fi

args=(
  --fail-with-body --silent --show-error --get
  --user "$2:$3"
  --header 'Accept: application/json'
  --data-urlencode "jql=$4"
  --data-urlencode "maxResults=$max_results"
  --data-urlencode 'fields=summary,status,description,assignee'
)

if [ -n "${6:-}" ]; then
  args+=(--data-urlencode "nextPageToken=$6")
fi

curl "${args[@]}" "$base_url/rest/api/3/search/jql"
