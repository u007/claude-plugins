# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Claude Code plugin marketplace (`personal-plugins`) holding two plugins. The marketplace manifest is `.claude-plugin/marketplace.json`; each plugin has its own `.claude-plugin/plugin.json`. Plugin `source` paths in the marketplace are relative (`./context-status`, `./jev-guard`).

## Commands

```sh
# Status line tests (stdlib unittest, no install step)
python3 context-status/bin/test_context_statusline.py

# Single test: ClassName.method_name
python3 context-status/bin/test_context_statusline.py ModelSegment.test_shows_model_display_name

# Validate marketplace + every plugin manifest (exit 1 on errors; add --strict for CI)
claude plugin validate .

# jev-guard has no test suite; at minimum check it compiles
python3 -m py_compile jev-guard/scripts/content_guard.py
```

Delete any `__pycache__` the test run leaves behind. It is gitignored, but do not commit it.

## Architecture

### context-status: statusLine renderer

- Registered in the user's `~/.claude/settings.json` as `statusLine.command`, which points at `bin/context-statusline.sh`. It is not wired through plugin install; the absolute path is what matters.
- Claude Code pipes a JSON payload on stdin. `context_statusline_render.py` reads only `model`, `workspace.current_dir` and `context_window`, and builds one line: model · dir · branch · context bar · chained output.
- Every segment is best-effort. Missing data drops the segment rather than rendering a placeholder. Keep it that way when adding segments.
- The branch is read from the repo's `HEAD` file, not by spawning `git`. This is deliberate: the status line runs on every refresh and must not spawn processes or block on a hung `git`. `_git_dir` handles normal repos, linked worktrees, submodules and bare repos.
- `bin/prev_command.txt` is a shell command whose output is appended to the line (`shell=True`, with a 5s timeout). It preserves a previously configured status line. Blanking the file disables chaining. Its path is resolved via `__file__`, so it works through the `~/.claude/plugins/context-status` symlink.

### jev-guard: PostToolUse inbound-content guardrail

- `hooks/hooks.json` registers one PostToolUse hook, matching `WebFetch|WebSearch|Bash|mcp__.*`, that runs `scripts/content_guard.py`.
- `source_for()` decides what gets scanned. Bash is scanned only when the command invokes a network binary (`curl`, `wget`, `nc`, ...) against a non-loopback host. Local Bash and Read output is never scanned.
- The result text is split into 6000-char chunks (max 32, larger results are flagged as unscannable), and the chunks are judged in parallel against the TypeSafe Jev API.
- Three outcomes:
  - **Flagged:** `decision: block` plus `updatedToolOutput` with the same response shape and a withheld notice.
  - **Unvetted** (no `TYPESAFE_API_KEY`, judge error or timeout, or confidence below 0.6 on a clean verdict): the result is delivered, and the model is told it is unvetted. Failures are never silent.
  - **Clean:** no output.
- `TYPESAFE_API_KEY` is read from the environment only. `.env.example` holds a placeholder. Never add a real key to the repo.

## Conventions specific to this repo

- The `plugin.json` and the marketplace entry must agree on name and version. `claude plugin tag` checks this.
- Plugin folder names are part of the install identity (`jev-guard@personal-plugins`). Do not rename them.
- Keep the marketplace name `personal-plugins`. It is referenced from user settings.
- Do not commit personal paths or usernames. Use `$HOME` or `~` in shipped config and fixtures.
