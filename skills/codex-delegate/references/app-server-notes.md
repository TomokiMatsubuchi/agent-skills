# Codex app-server notes

These notes are based on the current local Codex manual and `codex app-server --help` output verified while creating this skill.

## When app-server fits

This skill delegates through `codex app-server`. Keep the implementation and guidance on the app-server path.

`codex app-server` is intended for rich clients and product integrations that need authentication, conversation history, approvals, and streamed agent events. In this skill, use that protocol boundary to start a separate child Codex turn and collect its streamed result.

## Protocol facts

- Default transport is stdio JSONL.
- A client must send `initialize`, then the `initialized` notification, before other methods.
- Create a conversation with `thread/start`.
- Start work with `turn/start` and `params.input` such as `[{ "type": "text", "text": "..." }]`.
- Stream assistant text from `item/agentMessage/delta`.
- Stop reading when `turn/completed` arrives.
- Generate local schemas matching the installed Codex version with:

```bash
codex app-server generate-json-schema --out /tmp/codex-appserver-schema
```

## Safety defaults

Use a read-only sandbox and `approvalPolicy=never` for child investigations so the app-server client cannot hang waiting for interactive approval. If the delegated task requires writes, confirm that the user really wants delegated implementation and prefer `workspace-write`.

`codex app-server` still reads and writes Codex's local state under `~/.codex`. In restricted sandboxes, startup may fail before a thread is created; rerun with an explicit execution approval rather than weakening the child task's sandbox.

Do not expose WebSocket listeners outside loopback from this skill. Stdio is the default and safest integration path.
