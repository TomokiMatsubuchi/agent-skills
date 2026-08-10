---
name: g-review
description: Run the review workflow migrated from Anti-Gravity CLI against local Git changes or a GitHub pull request. Use only when the user explicitly invokes g-review or $g-review; do not trigger for ordinary review requests.
---

# G Review

Perform a read-only, evidence-based review. Find demonstrable bugs, security issues, performance problems, and maintainability risks; skip praise and stylistic preferences.

## Select the target

- If the user supplies a GitHub PR URL or number, review the PR.
- Otherwise review the current repository's branch, staged, and working-tree changes.
- Honor any user-supplied scope or base ref.

For a local review:

1. Read repository instructions and `git status`.
2. Use the merge base with the repository's default branch, normally `origin/HEAD`, so committed and uncommitted branch changes are included.
3. If no default branch can be resolved, review staged and working-tree diffs and disclose that committed branch-only changes may be missing.
4. Use at least five context lines and preserve old/new line numbers.

For a PR review:

1. Read the PR title, body, base/head refs, existing review context, and full diff using an available GitHub connector or `gh`.
2. Read relevant repository files locally when available.
3. Keep the review read-only unless the user explicitly asks to publish it.
4. If publishing, submit one review as `COMMENT`. Never approve or request changes unless explicitly asked.

## Analyze

1. State the change's intent in one sentence.
2. Read every changed file.
3. Trace changed functions through callers, dependencies, configuration, and tests using repository search.
4. Focus on production logic. Review tests for incorrect or missing coverage of material behavior.
5. Run the smallest safe, relevant checks when useful.
6. Report only issues introduced or exposed by the change.

## Findings

- Anchor each finding to a changed line. For PRs, use the left line for deletions and the right line for additions.
- Explain the concrete failure path and impact. Do not ask the author to "check", "verify", or "ensure" something.
- Keep one root cause per finding. Combine repeated instances and name the other locations.
- Include a minimal, correctly indented suggestion only when clearly safe.
- Do not report formatting, license headers, future dates or versions, missing trailing newlines, or speculative concerns.

Use these severities:

- `CRITICAL`: exploitable security flaw, data loss, or system-wide failure.
- `HIGH`: functional failure on a common path, serious concurrency/resource issue, or severe performance regression.
- `MEDIUM`: limited functional bug, missing trust-boundary validation, or concrete maintainability defect.
- `LOW`: small but substantive issue, including meaningful test or documentation defects.

## Report

Start with `# Change summary: ...`, then order verified findings by severity and file:

````markdown
## File: path/to/file
### L42: [HIGH] Concise issue title

Concrete failure path and impact.

Suggested change:
```diff
-old code
+new code
```
````

If there are no findings, write `No issues found.` and briefly state any checks not run or residual testing gap.
