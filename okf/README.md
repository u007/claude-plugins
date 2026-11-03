# okf

Claude Code plugin for working with an OKF (Open Knowledge Format) v0.1 knowledge bundle: a `docs/` directory of markdown files with YAML frontmatter, a marked `docs/index.md` and an append-only `docs/log.md`.

- **Skill `okf`:** the workflow. Look up the bundle before any task, write docs only for durable knowledge, deduplicate first, keep `index.md` and `log.md` in sync, deprecate instead of delete.
- **SessionStart hook:** when the project has `docs/index.md` with `okf_version`, tells Claude to dispatch the `context` agent for the lookup before any task. Silent when there is no bundle. POSIX `sh` only, so it works in the desktop app, which does not load shell profiles.

- **Agents `context` and `context-writer`:** Haiku subagents (`okf:context`, `okf:context-writer`) shipped with the plugin. `context` is read-only (no write tools) and returns a lookup digest before a task; `context-writer` updates docs, log and index after a task with durable knowledge. The main agent decides what is durable, briefs the writer, and checks `git diff docs/` afterwards. If the agents are unavailable, the skill is followed directly.

The skill is instructions, not automation. Nothing writes docs or regenerates the index for Claude: Claude follows the skill. The hook only makes the lookup reminder reliable.

## Install

```sh
claude plugin marketplace add u007/claude-plugins
claude plugin install okf@personal-plugins
```

Then remove any standalone copy at `~/.claude/skills/okf` so the skill is not listed twice.

Test without installing:

```sh
claude --plugin-dir ./okf
```

Not yet verified end to end in the desktop app.
