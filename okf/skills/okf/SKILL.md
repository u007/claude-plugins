---
name: okf
description: Work with an OKF (Open Knowledge Format) v0.1 knowledge bundle, a docs/ directory of markdown files with YAML frontmatter plus a marked index.md and an append-only log.md. Defines the workflow - look up the bundle BEFORE starting work, update docs AFTER durable knowledge is produced, deduplicate before writing, and keep index.md and log.md in sync. Use at the start of any task in a repo whose docs/index.md contains okf_version, and whenever creating, auditing, or editing bundle docs.
when_to_use: At the start of ANY task (feature, fix, investigation, question about why or how a decision was made) in a repo where docs/index.md has an okf_version marker - run the lookup step first. Also when the user mentions OKF, a knowledge bundle, .okfignore, docs/.okf.lock, or asks to create, annotate, audit, deprecate or clean up curated docs.
---

# OKF knowledge bundle (v0.1)

A bundle is a `docs/` directory of curated markdown files with YAML frontmatter. It records decisions, gotchas, playbooks and concepts that are not obvious from code or git history.

This skill is the whole mechanism: nothing runs automatically. Follow the steps below yourself, in order.

## 0. Is there a bundle?
Check `docs/index.md` at the project root. It is a bundle only if its frontmatter has `okf_version: "0.1"`. If the file is missing, or exists without the marker (mkdocs, docusaurus, hand-written), there is no bundle: skip this skill, and never overwrite that `index.md`. Create a bundle only if the user asks (see Init).

## Delegate to a Haiku subagent
Do the bundle legwork (exploration, context lookup, doc updates) in a Haiku subagent, not in the main conversation. It keeps doc dumps out of the main context and is cheap. Use the Agent tool with `model: "haiku"`.
- **Lookup:** `subagent_type: "Explore"` (read-only). Brief it with the task topic and the bundle path, and ask for steps 1.1 to 1.4 below. It returns a short digest: relevant doc paths, the facts that matter, anything stale or contradicted by code, and "none matched" if so. Work from the digest. Read a cited doc yourself only when the digest is not enough.
- **Update:** `subagent_type: "general-purpose"` (it needs write tools). You decide whether the task produced durable knowledge (step 2), because you have the conversation. If yes, give the subagent a self-contained brief, since it cannot see the conversation: what was decided, found or changed, why, the files involved, and what you already verified. Tell it to invoke the `okf` skill and follow steps 3 and 4 (dedupe, write, lock, log, index) and to report the paths it created, updated or deprecated.
- **One writer:** run at most one update subagent at a time, and do not edit the bundle yourself while it runs.
- **Check its work:** Haiku is a weaker model. After an update, run `git diff docs/` (and `git status docs/`) and confirm the doc says what you told it, the log entry exists, the index lists the doc, and nothing unrelated changed. Fix or revert problems before reporting done.
- If you are already running as a subagent and cannot dispatch another, do the steps directly.

## 1. BEFORE work: look up
Do this before reading code or editing anything, for every task. Run it in the Haiku lookup subagent described above.
1. Read `docs/index.md` (the catalogue: `- [title](path) - description`).
2. Search for the task's topic. List docs whose title, description, tags or path match. Search the bodies too: `grep -ril "<term>" docs --include='*.md'`. Ranking that works: a match in the title weighs 3, description 2, body 1; with several terms, require all of them to appear.
3. Read every relevant doc in full. Skip `status: deprecated` docs unless checking history, and respect `.okfignore`.
4. Verify any code claim in a doc against the code before relying on it. Citations rot (see Gotchas).
5. State briefly which docs you used, or that none matched. Then do the work.

## 2. AFTER work: decide whether to write
Update the bundle only for durable knowledge produced by this task: a decision and its reason, a gotcha or surprising failure, a playbook that worked, a schema or architecture change. Q&A, routine edits and chat-only discussion are no-ops. If in doubt, do nothing. Say in one line whether you updated the bundle and why or why not.

## 3. Writing a doc
(Done by the Haiku update subagent; see Delegation.)
1. **Deduplicate first.** Re-run the search for the doc's topic. If a doc already covers it, update that doc instead of creating a near-duplicate. If two existing docs overlap, merge the content into the better one and deprecate the other with a reason pointing at the survivor.
2. Verify every claim against the code or system before writing it down.
3. Write the doc (format below) at a bundle-relative path, one topic per doc. The path must stay inside `docs/` (no `..`, not absolute) and must not be `index.md` or `log.md`.
4. Set `timestamp` to now (RFC 3339) on create and on every content change.
5. Take the lock (see Concurrency), then do steps 3 to 5 inside it: write the doc, append to the log, regenerate the index.

### Doc format
```yaml
---
type: Concept            # Concept, Gotcha, Playbook, Decision, ...
title: Short title
description: One line, specific enough to tell docs apart in a search.
resource: path/or/url    # what the doc is about
tags: [area, topic]
timestamp: 2026-10-30T09:00:00Z
status: active           # or deprecated
deprecated_reason: why   # only when deprecated
---
```
`type` is required. A doc without this frontmatter is non-conforming: it stays in the bundle, gets listed under Unclassified, and should be annotated. Keep unknown frontmatter keys when you rewrite a doc.

## 4. Log and index (keep both in sync after every change)
**`docs/log.md`** is append-only history, newest day first:
```
# Directory Update Log

## 2026-10-30

* **Update**: what changed and why ([docs/path.md](/path.md))
```
Action is one of `Creation`, `Update`, `Deprecation`, `Deletion`. Add the entry under today's `## YYYY-MM-DD` heading, creating that heading directly under the title if it does not exist. The link target is the bundle-relative path with one leading `/`.

**`docs/index.md`** is regenerated, not hand-patched. Rebuild it from every doc's frontmatter:
- Frontmatter holds only `okf_version: "0.1"` (preserve the existing value).
- One `# <dir>` section per top-level directory, sorted by name. Root-level docs go under `# Concepts`.
- Entries inside a section sorted by title, case-insensitive: `- [title](relative/path.md) - description`. Use the path as the title if the title is empty. Append ` (deprecated)` for deprecated docs.
- Non-conforming docs go last under `# Unclassified` as `- [filename](path)`, sorted by path.
- Write to a temp file and rename it over `index.md`, so a failed run leaves the old index intact.

## Deprecate and clean up
- Deprecate, never delete, as the normal path: set `status: deprecated` and `deprecated_reason`, then log `Deprecation` and regenerate the index.
- Cleanup deletes deprecated docs. List them with path and reason first and delete only after the user confirms. Then log each `Deletion` and regenerate the index.

## Exclusions
Skipped as docs: `index.md`, `log.md`, dot-files and dot-directories, non-`.md` files, `PLAN-*.md` and `*.OCODE.md`. `docs/.okfignore` adds patterns, one per line (blank lines and `#` comments skipped). A pattern matches the basename and the bundle-relative path, and a trailing `/` matches directories. Put non-bundle markdown that lives under `docs/` (eval output, generated reports, drafts) in `.okfignore`, or it is counted as bundle docs and pollutes search and counts.

## Concurrency
Other writers may touch the bundle. Do every mutation (write doc, deprecate, delete, append log, regenerate index) as one sequence under an exclusive advisory lock on `docs/.okf.lock`, for example `flock docs/.okf.lock -c '<commands>'` where `flock` exists, or a Python `fcntl.flock` script. Never split the sequence across separate lock holds.

## Init and audit
- **Init** (only when asked, and only when no marker exists): refuse if `docs/index.md` exists without the marker. Otherwise create `index.md` containing the marker and an empty log, then annotate existing docs with frontmatter without changing their bodies. If the marker already exists, run an audit instead of failing.
- **Audit:** count conforming, non-conforming and deprecated docs. Report stale docs (contradict current code), duplicates, orphans (not reachable from the index or never referenced), and broken anchors.

## Gotchas
- **Line-anchor drift:** citations like `file.go:123` silently rot when lines are added above them. After editing a cited file, re-derive EVERY anchor on the page, checking both ends of ranges: extract each `\w+\.\w+:\d+`, print the real source line, compare. Prefer citing a symbol name to a line number. Do not trust an automated "anchors corrected" report.
- Bulk non-bundle markdown under `docs/` inflates counts and degrades lookup. Fix it with `.okfignore`.
- A folder named `docs/` is not a bundle. Only the `okf_version` marker in `index.md` makes it one.
