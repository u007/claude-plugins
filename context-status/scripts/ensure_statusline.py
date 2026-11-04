#!/usr/bin/env python3
"""SessionStart hook: register this plugin's status line in user settings.

Claude Code plugins cannot declare `statusLine`; it is read only from
settings.json. This hook writes it for the user:

    no statusLine set                     -> set it to this plugin's script
    statusLine already runs context-status
      from a different path (old version) -> repoint it at this install
    statusLine is something else          -> leave it alone, log to stderr

The settings file is `$CLAUDE_CONFIG_DIR/settings.json`, default
`~/.claude/settings.json`. Invalid JSON raises: a settings file we cannot
parse is never overwritten.
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "context-statusline.sh"
# Matches both .../context-status/bin/... and the versioned cache layout
# .../context-status/<version>/bin/...
_MANAGED = re.compile(r"/context-status/(?:[^/]+/)?bin/context-statusline\.sh$")


def _settings_path():
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    base = Path(config_dir) if config_dir else Path.home() / ".claude"
    return base / "settings.json"


def _write_atomic(path, data):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".settings-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        if path.exists():
            os.chmod(tmp, path.stat().st_mode & 0o777)
        os.replace(tmp, path)
    except OSError as exc:
        print(f"context-status: could not write {path}: {exc}", file=sys.stderr)
        os.unlink(tmp)
        raise


def main():
    path = _settings_path()
    command = str(_SCRIPT)

    if path.exists():
        with open(path, encoding="utf-8") as fh:
            settings = json.load(fh)
    else:
        settings = {}

    current = settings.get("statusLine")
    if current is None:
        message = "context-status: status line enabled. Restart Claude Code to see it."
    else:
        existing = current.get("command", "") if isinstance(current, dict) else ""
        if existing == command:
            return
        if not _MANAGED.search(existing):
            print(
                f"context-status: statusLine in {path} is not managed by this plugin; "
                "leaving it unchanged",
                file=sys.stderr,
            )
            return
        message = "context-status: status line path updated. Restart Claude Code."

    settings["statusLine"] = {"type": "command", "command": command}
    _write_atomic(path, settings)
    print(json.dumps({"systemMessage": message}))


if __name__ == "__main__":
    main()
