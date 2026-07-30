---
name: notion-api
description: Use the official Notion REST API to search, read, create, and update pages, blocks, databases, and data sources. Trigger when a user asks to operate on Notion content through an API token, automate Notion without an MCP connector, inspect a Notion schema, or troubleshoot a Notion API request.
---

# Notion API

Use `scripts/notion.sh` for authenticated requests. It uses API version `2026-03-11` by default and requires `NOTION_API_KEY`; never print or persist the token.

## Workflow

1. Check that `NOTION_API_KEY` is set. If it is missing, ask the user to create a Notion connection, share the target page or database with it, and export the token locally.
2. Search for the target when its ID is unknown. Do not assume search exhaustively lists all accessible content; prefer an ID supplied by the user.
3. Retrieve the target before changing it. For data-source entries, retrieve the data source first and match its property schema exactly.
4. Perform the smallest requested operation. Do not trash pages or blocks, change schemas, or overwrite content unless explicitly requested.
5. Inspect the response and report the affected page or object ID. Follow `has_more` and `next_cursor` when complete results are required.

Run requests from this skill directory:

```bash
scripts/notion.sh POST /v1/search '{"query":"Project Alpha","page_size":10}'
scripts/notion.sh GET /v1/pages/PAGE_ID
scripts/notion.sh GET '/v1/blocks/PAGE_ID/children?page_size=100'
scripts/notion.sh GET /v1/data_sources/DATA_SOURCE_ID
scripts/notion.sh POST /v1/data_sources/DATA_SOURCE_ID/query '{"page_size":100}'
```

For JSON bodies with shell-sensitive content, put the body in a temporary file and pass `@/absolute/path/body.json` as the third argument.

## Page content

- A page response contains properties, not its body. Read the body with `GET /v1/blocks/{page_id}/children`.
- Recursively fetch children for blocks whose `has_children` is `true`.
- Append blocks with `PATCH /v1/blocks/{block_id}/children`.
- Create a page with `POST /v1/pages`. Use a `page_id` parent for a normal child page or a `data_source_id` parent for a data-source entry.
- When creating an entry, use property names and value shapes returned by `GET /v1/data_sources/{data_source_id}`.

## Guardrails

- Treat `401` as an invalid token and `403` or `404` as a likely capability or sharing problem; do not claim the object is absent until access is checked.
- On `429`, honor `Retry-After` and retry only the failed request.
- File URLs returned by Notion are temporary; do not store them as permanent links.
- API version `2026-03-11` uses current names such as `in_trash` and `meeting_notes`. Override with `NOTION_VERSION` only when compatibility with an existing integration requires it.
- Consult the official Notion API reference before using an endpoint or property shape not covered here.

## Helper

`scripts/notion.sh METHOD /v1/path [JSON|@FILE]` adds authentication, version, and JSON headers and makes `curl` fail on HTTP errors while preserving the response body.
