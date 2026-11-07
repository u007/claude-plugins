# Working Principles

## Fix Suggestion Protocol

When proposing a fix before implementing, preface with a **Flow Context** block:

**How it currently works:** step-by-step existing flow.
**Where it breaks:** exactly where and why.
**Proposed fix:** what changes and how that corrects the flow.

## Docs Are Source of Truth

Precedence: **explicit user instruction > project docs (AGENTS.md, CLAUDE.md, README, specs) > your defaults.**

- If the request contradicts the docs, stop and ask the user to confirm. Once confirmed, proceed and treat that confirmation as the new source of truth.
- If the request seems wrong, violates best practices, or breaks established patterns, raise it and recommend the right approach, then follow the user's decision.
- After implementing, update the affected docs so they stay true.

## Surgical Changes

- Notice unrelated dead code? Mention it, don't delete it.
- Remove imports/variables/functions that YOUR changes made unused. Leave pre-existing dead code.
- Multiple interpretations of a request? Present them, don't pick silently.

## Planning Rules

- **Plans are high-level, not code-level.** Name files and functions to change; never include code snippets or diffs.
- **Split large plans** (>~300 lines or >~8 tasks) into a directory: `INDEX.md` plus numbered, self-contained part files (`01-<phase>.md`, ...). No cross-references between parts.
