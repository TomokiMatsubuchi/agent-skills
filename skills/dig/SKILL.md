---
name: dig
description: Deeply interview the user to uncover hidden assumptions, risks, and undecided trade-offs in a plan, then write the discoveries back into the plan. Use when the user says "dig", "challenge assumptions", "stress test plan", "find risks in plan", "前提を疑って", "計画を深掘り", or "プランに穴が無いか".
---

# Dig

Stress-test a plan through depth-first, iterative questioning. Challenge premises, make hidden decisions explicit, and pursue each high-risk thread until it stops producing useful discoveries.

## Prepare

1. Locate and read the active plan through the environment's native plan tools or an explicitly referenced plan file.
2. If no persisted plan exists, create `./PLAN.md` from the plan in the conversation.
3. Read applicable project instructions such as `AGENTS.md` and `CLAUDE.md`, plus specifications referenced by the plan.
4. Build an internal inventory of:
   - stated goals and constraints;
   - implicit assumptions;
   - major missing topics.

Do not ask questions until this context is understood.

## Rank assumptions

Classify assumptions as feasibility, user, scope, dependency, timeline, or architecture. Rank them by impact if wrong and start with the highest-risk assumption.

## Investigate

Run focused rounds of 2–3 questions:

- Use the environment's structured question tool when available; otherwise ask the same structured questions in chat.
- Give 2–4 concrete options per question, each with brief pros and cons.
- Do not add an `Other` option when the tool already permits a custom answer.
- Prefer options consistent with existing project patterns.
- Avoid broad clarification. Probe assumptions, trade-offs, failure modes, scale, dependency fallbacks, security/privacy, maintenance ownership, migration, and rollback.

After each answer round:

1. Identify new assumptions revealed by the answers.
2. Follow the most consequential thread before switching topics.
3. Reach at least two levels of depth on each major high-risk topic.
4. Record confirmed discoveries and decisions in the plan before asking the next round.

Use this structure without overwriting unrelated plan content:

```markdown
## Dig Discoveries

### Round N

| Assumption | Finding | Impact | Decision |
|---|---|---|---|
| ... | ... | High/Medium/Low | ... |

## Decisions

| Topic | Decision | Rationale | Risk | Notes |
|---|---|---|---|---|
| ... | ... | ... | High/Medium/Low | ... |
```

## Stop condition

Finish when all of these are true, or when the user asks to stop:

- all high-risk assumptions are addressed;
- major topics reached two levels of depth;
- trade-offs and critical failure modes were discussed;
- no consequential new question remains;
- the plan contains every confirmed decision.

Do not loop for completeness theater. Stop when another round would not materially improve the plan.

## Summarize

Report concisely:

- rounds and questions completed;
- highest-impact discoveries and decisions;
- unresolved risks;
- recommended next actions;
- the updated plan location.

Adapted from [fumiya-kume/claude-code `dig`](https://github.com/fumiya-kume/claude-code/tree/master/dig), licensed under GPL-3.0.
