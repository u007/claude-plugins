# personal-plugins

Personal Claude Code plugin marketplace (`personal-plugins`).

| Plugin | Path | What it does |
| --- | --- | --- |
| `context-status` | `context-status/` | Status line: model, dir, git branch, context usage. |
| `jev-guard` | `jev-guard/` | PostToolUse guardrail: scans inbound web/MCP/network results with TypeSafe Jev. |

## Layout

- `.claude-plugin/marketplace.json`: marketplace manifest listing both plugins.
- Each plugin folder is self-contained with its own `.claude-plugin/plugin.json`.

## Local use

The marketplace is registered as a directory source in `~/.claude/settings.json`
(`extraKnownMarketplaces.personal-plugins`). `~/.claude/plugins/personal-plugins`
and `~/.claude/plugins/context-status` are symlinks into this repo.

Install a plugin: `/plugin install jev-guard@personal-plugins`.

The `context-status` statusline is wired by absolute path in `~/.claude/settings.json`
(`statusLine.command`), not through plugin install.

## Tests

```sh
python3 context-status/bin/test_context_statusline.py
```
