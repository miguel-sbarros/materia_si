---
description: Plan the next step of Captus development — interview the user first, then write a focused step plan + spec.
---

You are scoping the **next concrete step** of the Captus CRM build. Your job is to produce a clear, executable plan for **one step** — not to start coding, and not to assume direction the user hasn't given.

## 1. Orient (read state, don't ask what you can find out)

Read, in order:
- `CLAUDE.md` (this repo) — principles, stack, reuse map, conventions.
- The master plan: `~/.claude/plans/estou-construindo-um-projeto-woolly-kazoo.md` — phases P0–P5 and what each delivers.
- `specs/` — which feature specs already exist.
- `git log --oneline -15` and `git status` — what's actually been built vs planned.

From this, determine **where the project currently is** and **what the natural next step is** (the next unfinished phase, or a sub-step within the current one). State your read of the current position in one or two sentences before asking anything.

## 2. Interview the user — ask, do not assume

This is the core of the command. Before writing any plan, use **AskUserQuestion** to resolve the decisions that would otherwise be guesses. Ask about whatever is genuinely open for the next step — typically some of:

- **Which step next** — confirm the next phase/sub-step, or let the user redirect.
- **Scope/boundaries** — how far this step goes; what's explicitly out.
- **Approach** — when there's a real fork (e.g. which screen to wire first, which import format, sync vs background, schema shape), present the options with trade-offs and a recommendation.
- **Acceptance criteria** — what "done" looks like for this step (these become the spec's criteria and the pytest assertions).

Rules:
- **Never invent architectural direction.** If you're unsure, ask — that's the whole point of this command.
- Put your recommended option first and label it "(Recommended)", with a one-line why.
- Only ask about things that actually change what you'd do. Don't ask about settled decisions in `CLAUDE.md` (LLM provider, layering, no-JWT, pgvector, TDD) — those are fixed; honor them.
- One round of questions is usually enough; ask a second round only if an answer opens a new fork.

## 3. Produce the step plan

After the user answers, write:

1. **A spec file** at `specs/<feature-or-step>.md` containing: the requirement/acceptance criteria (cite the REQ code from the rubric where relevant), the Pydantic/DB schema for this step, and the test cases that will prove it (Spec-Driven Development).
2. **A short step plan** (in your reply, or appended to the spec) listing the files to create/change, the tests to write **first** (TDD), and the verification command(s) that confirm the step works end-to-end.

Keep it tight: enough to execute without re-deriving decisions, no padding. Reference existing code to reuse (especially the `sales_context_system` assets in the reuse map) rather than writing new code where a port exists.

## 4. Hand off

End by stating the single verification that proves the step is done, and confirm the user is ready for you to implement it (write tests first, then make them pass).
