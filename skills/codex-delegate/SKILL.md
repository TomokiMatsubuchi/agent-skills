---
name: codex-delegate
description: Delegate hands-on work from a parent AI to one or more Codex instances through `codex app-server`. Use implicitly when a task needs substantive repository investigation, implementation, testing, or other execution while the parent retains planning and final judgment. Also use for deep reasoning, high-impact decisions, independent review, or multiple perspectives, and whenever the user explicitly asks to involve Codex. Skip trivial questions or edits where delegation costs more than doing the work directly.
---

# Codex Delegate

Keep the parent AI responsible for understanding the goal, choosing the direction, decomposing work, integrating results, and answering the user. Delegate bounded investigation, implementation, and verification to Codex.

## Default split

1. Have the parent frame the problem, constraints, and success criteria.
2. Delegate concrete execution with `scripts/delegate_app_server.py`.
3. Have the parent inspect the evidence or diff, resolve conflicts, and make the final decision.

Delegate by default when meaningful repository exploration, implementation, test execution, or mechanical work is required. A user request to implement or modify something authorizes a child to write within that same scope; it does not authorize destructive actions, unrelated changes, or new external side effects.

Skip delegation for a quick factual answer, a trivial one-file edit, or work the parent can complete faster than starting a child.

## Delegation patterns

- **Investigation:** Run one child with `--sandbox read-only --approval never`. Ask for evidence, paths, risks, and a concise recommendation.
- **Implementation:** Run one child with `--sandbox workspace-write --approval never`. Give exact scope, constraints, expected checks, and permission boundaries. Inspect its diff and rerun the relevant check in the parent context.
- **Review or discussion:** Run two or three separate read-only children with distinct roles, such as correctness, simplicity, and operational risk. Keep their first passes independent, then have the parent compare disagreements and synthesize a decision.
- **Deep reasoning:** Ask independent children to challenge assumptions or propose alternatives. If needed, give a final critic the parent’s draft synthesis and ask it to identify the strongest unresolved flaw.

Do not let multiple writing children modify overlapping files. Use one writer, or give writers disjoint scopes. Parallelize only independent read-only work or clearly disjoint implementation.

## App-server workflow

1. Read `references/app-server-notes.md` before editing the script or relying on app-server semantics.
2. Write a self-contained child prompt containing the task, cwd, scope boundaries, expected output or checks, and whether files may be modified.
3. Use read-only mode for investigation and review:

```bash
python3 ~/.cursor/skills/codex-delegate/scripts/delegate_app_server.py \
  --cwd "$PWD" \
  --sandbox read-only \
  --approval never \
  "Investigate the current branch for likely test risks. Do not modify files. Return concise findings with file paths."
```

4. For an authorized implementation task, use `--sandbox workspace-write`. Avoid `danger-full-access`.
5. Treat every child result as evidence, not truth. Verify important claims, diffs, and checks in the parent context.
6. Report the integrated outcome to the user; do not dump raw child transcripts unless requested.

## Script behavior

`scripts/delegate_app_server.py` starts `codex app-server --stdio`, sends the JSON-RPC initialization handshake, creates an ephemeral thread, starts one turn, streams `item/agentMessage/delta` output, and exits when `turn/completed` arrives.

Useful options:

- `--dry-run`: print the JSON-RPC messages that would be sent without starting Codex.
- `--model MODEL`: override the child model for the thread.
- `--cwd PATH`: set the child Codex working directory.
- `--sandbox read-only|workspace-write`: set the child sandbox.
- `--approval never|on-request|untrusted`: set the child approval policy.
- `--developer-instructions TEXT`: add child-only developer instructions.
- `--json`: emit a machine-readable summary instead of plain text.
- `--raw-log PATH`: save raw app-server messages for debugging.

If app-server emits approval or user-input requests, the script rejects unsupported requests by default rather than hanging. Retry with a narrower read-only prompt or explicitly extend the app-server client to support the required interaction.

If startup fails with a sqlite/state-runtime error under `~/.codex`, rerun the script with the necessary execution approval. `codex app-server` needs access to Codex's local state even when the child task itself is read-only.
