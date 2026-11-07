# personal-plugins

Personal Claude Code plugin marketplace (`personal-plugins`).

| Plugin | Path | What it does |
| --- | --- | --- |
| `context-status` | `context-status/` | Status line: model, dir, git branch, context usage. |
| `jev-guard` | `jev-guard/` | PostToolUse guardrail: scans inbound web/MCP/network results with TypeSafe Jev. |
| `okf` | `okf/` | OKF knowledge bundle workflow skill plus SessionStart lookup reminder. |
| `branch-indicator` | `branch-indicator/` | Announces the git worktree (or branch) the session works in, at start and on change. |
| `communication-style` | `communication-style/` | SessionStart: injects the ASD-STE100 communication standard (ported from ocode). |
| `working-principles` | `working-principles/` | SessionStart: fix suggestion protocol, docs-as-truth, surgical changes, planning rules. |
| `code-quality` | `code-quality/` | SessionStart: no fallbacks, error logging, no upsert, TODO tracking, test safety. |
| `git-safety` | `git-safety/` | SessionStart: no bare `git reset --soft` in shared repos. |
| `frontend-standards` | `frontend-standards/` | SessionStart: use the present UI library, semantic HTML, UX care. |

## Installation

### 1. Add the marketplace

From GitHub, in a terminal:

```sh
claude plugin marketplace add https://github.com/u007/claude-plugins
# or the short form:
claude plugin marketplace add u007/claude-plugins
```

Or inside a Claude Code session:

```
/plugin marketplace add u007/claude-plugins
```

Check it was added:

```sh
claude plugin marketplace list
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

### 3. Install okf

```
/plugin install okf@personal-plugins
```

See [okf/README.md](okf/README.md).

### 4. Install context-status

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

### 5. Install branch-indicator

```
/plugin install branch-indicator@personal-plugins
```

See [branch-indicator/README.md](branch-indicator/README.md).

## Install a single plugin

Each plugin is independent. Install only the ones you want.

### Via the marketplace

Add the marketplace (step 1 above), then install one plugin by name:

```sh
claude plugin install jev-guard@personal-plugins
# or: okf@personal-plugins, context-status@personal-plugins, branch-indicator@personal-plugins
```

### Manually from a local clone

No marketplace needed. Clone the repo, then load one plugin directory for a session:

```sh
git clone https://github.com/u007/claude-plugins ~/www/personal-plugins
claude --plugin-dir ~/www/personal-plugins/jev-guard
```

`--plugin-dir` applies to that run only. To make it permanent, use the marketplace route with the local clone path (`/plugin marketplace add ~/www/personal-plugins`, then `/plugin install <name>@personal-plugins`).

Plugin-specific setup still applies: `TYPESAFE_API_KEY` for jev-guard, the `statusLine` entry for context-status.

## Claude desktop app

Plugins work in the **Code** tab of the desktop app, in local and SSH sessions. Cloud sessions have no plugin browser. The regular Claude chat tab does not load Claude Code plugins.

Quick install:

1. Open the **Code** tab and start a local session.
2. Add the marketplace by typing `/plugin marketplace add u007/claude-plugins` in the prompt.
3. Install the plugins you want, for example `/plugin install okf@personal-plugins`. Or open the plugin browser and pick them from `personal-plugins`.
4. Start a new session so the plugins load.

Prefer a terminal? Run steps 1 and 2 of [Installation](#installation) there. The desktop app's local sessions read the same settings files as the terminal, so the plugins show up in the Code tab with nothing more to do.

Manage, disable or uninstall later from **+ > Plugins > Manage plugins**.

`context-status` needs the extra `statusLine` entry from [Installation](#4-install-context-status) in `~/.claude/settings.json`. Whether the desktop Code tab renders a custom status line is not verified.

## Updating

Refresh the marketplace, then update the plugin:

```sh
claude plugin marketplace update personal-plugins
claude plugin update jev-guard@personal-plugins
```

Inside a session: `/plugin marketplace update personal-plugins`, then `/plugin update jev-guard@personal-plugins`. Restart Claude Code afterwards so the new version loads.

Updates are picked up only when the plugin `version` changes, so bump `version` in both the plugin's `plugin.json` and its `marketplace.json` entry when releasing.

If you installed from a local clone, pull first:

```sh
git -C ~/www/personal-plugins pull
```

`context-status` runs from the clone path in `~/.claude/settings.json`, so `git pull` alone updates it. No plugin update is needed for the status line script.

## Tests

```sh
python3 context-status/bin/test_context_statusline.py
python3 branch-indicator/scripts/test_branch_indicator.py
```
