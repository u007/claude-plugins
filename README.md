# personal-plugins

Personal Claude Code plugin marketplace (`personal-plugins`).

| Plugin | Path | What it does |
| --- | --- | --- |
| `context-status` | `context-status/` | Status line: model, dir, git branch, context usage. |
| `jev-guard` | `jev-guard/` | PostToolUse guardrail: scans inbound web/MCP/network results with TypeSafe Jev. |

## Installation

### 1. Add the marketplace

From GitHub:

```
/plugin marketplace add u007/claude-plugins
```

Or from a local clone:

```sh
git clone https://github.com/u007/claude-plugins ~/www/personal-plugins
```

```
/plugin marketplace add ~/www/personal-plugins
```

### 2. Install jev-guard

```
/plugin install jev-guard@personal-plugins
```

Then finish the setup in [jev-guard/README.md](jev-guard/README.md#setup): export `TYPESAFE_API_KEY` in your shell profile and start Claude Code from a terminal that loads it.

### 3. Install context-status

```
/plugin install context-status@personal-plugins
```

Installing the plugin does not switch the status line on. Point `statusLine` in `~/.claude/settings.json` at the script in your clone:

```json
{
  "statusLine": {
    "type": "command",
    "command": "/absolute/path/to/personal-plugins/context-status/bin/context-statusline.sh"
  }
}
```

Use the clone path, not the plugin cache path, so the command survives plugin updates.

`context-status/bin/prev_command.txt` chains a previous status line. The shipped value points at a cognee statusline that most machines do not have. Blank the file, or replace it with your own command, unless you use that one. A broken chained command only drops its own segment.

Not yet verified end to end on a clean machine.

## Tests

```sh
python3 context-status/bin/test_context_statusline.py
```
