#!/usr/bin/env python3
"""Render the Claude Code status line.

Reads the statusLine JSON Claude Code pipes on stdin and prints, in order:

    <model> · <dir> · <git branch> · ctx <bar> NN% (used/total) · <chained>

The model, directory and branch segments are best-effort: any segment whose
data is missing (or whose git directory can't be resolved) is dropped rather
than printed empty, so the line degrades gracefully instead of showing
placeholders.

The trailing segment re-invokes the previously configured statusLine command
(if any, recorded in prev_command.txt) with the same stdin so its output is
preserved alongside ours. That chained command is bounded by a timeout: this
script runs on the UI render path, and a hung status line would freeze the
display.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

_PREV_COMMAND_PATH = Path(__file__).resolve().parent / "prev_command.txt"

BAR_WIDTH = 10

# Bound for the chained status line. This is the only subprocess on the
# status-line path; the branch is read from HEAD without spawning git.
PREV_TIMEOUT_SECONDS = 5


def _format_tokens(n):
    if n is None:
        return "?"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def _render_bar(pct):
    filled = round(BAR_WIDTH * pct / 100)
    filled = max(0, min(BAR_WIDTH, filled))
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def _context_segment(data):
    cw = data.get("context_window") or {}
    pct = cw.get("used_percentage")
    total = cw.get("total_input_tokens")
    size = cw.get("context_window_size")

    if pct is None:
        return "ctx —"

    bar = _render_bar(pct)
    return f"ctx {bar} {pct}% ({_format_tokens(total)}/{_format_tokens(size)})"


def _model_segment(data):
    """The active model, e.g. "Opus 4.7".

    `display_name` is Claude Code's own short label; fall back to the raw
    `id` for models it has no label for (custom/gateway ids).
    """
    model = data.get("model")
    if not isinstance(model, dict):
        return ""
    for key in ("display_name", "id"):
        name = model.get(key)
        if isinstance(name, str) and name.strip():
            return name.strip()
        # intentionally not logged: a non-string here is a malformed payload,
        # not a defect in this script, and the id is tried next regardless.
    return ""


def _dir_segment(data):
    """The basename of the session's working directory."""
    workspace = data.get("workspace")
    if not isinstance(workspace, dict):
        return ""
    current = workspace.get("current_dir")
    if not isinstance(current, str) or not current.strip():
        return ""
    current = current.strip().rstrip("/")
    # "/" strips to "", and so does "//" — fall back to the raw path so the
    # segment is never an empty slot between two separators.
    return os.path.basename(current) or current


def _git_dir(cwd):
    """Resolve the git directory for `cwd`, or None if it isn't a repo.

    Three layouts, in the order git itself checks them:
      * `cwd/.git` is a directory  -> a normal repo
      * `cwd/.git` is a file       -> linked worktree / submodule, holding
                                     `gitdir: <path>` (path may be relative
                                     to `cwd`)
      * `cwd` itself holds HEAD    -> a bare repo
    """
    dot_git = os.path.join(cwd, ".git")
    if os.path.isdir(dot_git):
        return dot_git
    if os.path.isfile(dot_git):
        try:
            with open(dot_git, encoding="utf-8", errors="replace") as fh:
                pointer = fh.read().strip()
        except OSError:
            # intentionally not logged: an unreadable .git pointer file just
            # means this directory's branch can't be determined.
            return None
        if not pointer.startswith("gitdir:"):
            return None
        target = pointer[len("gitdir:"):].strip()
        if not target:
            return None
        if not os.path.isabs(target):
            # Relative pointers (submodules) are relative to the worktree
            # root; normpath so the resolved path has no ".." left in it.
            target = os.path.normpath(os.path.join(cwd, target))
        return target if os.path.isdir(target) else None
    if os.path.isfile(os.path.join(cwd, "HEAD")) and os.path.isdir(
        os.path.join(cwd, "objects")
    ):
        return cwd
    return None


def _branch_from_head(git_dir):
    """The branch name from a git directory's HEAD, or '' if not determinable.

    Returns `@<short-sha>` for a detached HEAD, matching `git branch
    --show-current` being empty there. An unborn branch (fresh `git init`,
    no commits) still names its branch, exactly as git reports it.
    """
    try:
        with open(os.path.join(git_dir, "HEAD"), encoding="utf-8", errors="replace") as fh:
            head = fh.read().strip()
    except OSError:
        # intentionally not logged: a missing/unreadable HEAD means no branch
        # segment; HEAD is absent in some bare/partial layouts.
        return ""
    if not head:
        return ""

    if head.startswith("ref:"):
        ref = head[len("ref:"):].strip()
        prefix = "refs/heads/"
        return ref[len(prefix):] if ref.startswith(prefix) else ""
    if re.fullmatch(r"[0-9a-fA-F]{40,64}", head):
        return "@" + head[:7]
    return ""


def _branch_segment(data):
    """Current git branch, or `@<short-sha>` when HEAD is detached.

    Claude Code's statusline payload has no branch field — `workspace.git_worktree`
    is set only for linked worktrees (and carries a path, not a branch), and
    top-level `worktree.branch` exists only for agent-isolation worktrees — so
    the branch is read from the repo's HEAD file.

    Reading HEAD rather than shelling out to `git` keeps the status line off
    the process-spawn path entirely: no ~30ms per refresh, and no way for a
    slow or hung git to stall the UI.
    """
    workspace = data.get("workspace")
    if not isinstance(workspace, dict):
        return ""
    cwd = workspace.get("current_dir")
    if not isinstance(cwd, str) or not cwd.strip():
        return ""

    git_dir = _git_dir(cwd)
    return _branch_from_head(git_dir) if git_dir else ""


def _prev_segment(raw_stdin):
    if not _PREV_COMMAND_PATH.exists():
        return ""
    try:
        command = _PREV_COMMAND_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        # intentionally not logged: an unreadable prev_command.txt just means
        # there is no chained status line to preserve.
        return ""
    if not command:
        return ""
    try:
        result = subprocess.run(
            command,
            shell=True,
            input=raw_stdin,
            capture_output=True,
            timeout=PREV_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        # intentionally not logged: a hung chained status line must not block
        # ours; its output is lost for this render only.
        return ""
    except (OSError, subprocess.SubprocessError):
        # intentionally not logged: the chained command is third-party and its
        # failure is not actionable from here.
        return ""
    return result.stdout.decode("utf-8", errors="replace").strip()


def main():
    raw_stdin = sys.stdin.buffer.read()
    try:
        data = json.loads(raw_stdin.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        # intentionally not logged: unparseable stdin still yields a usable
        # line (no model/dir/branch, placeholder context) instead of nothing.
        data = {}
    if not isinstance(data, dict):
        # intentionally not logged: a non-object payload (array/string/null)
        # carries none of the fields we read, so treat it as empty.
        data = {}

    segments = [
        _model_segment(data),
        _dir_segment(data),
        _branch_segment(data),
        _context_segment(data),
    ]

    prev = _prev_segment(raw_stdin)
    if prev:
        segments.append(prev)

    print(" · ".join(segment for segment in segments if segment))


if __name__ == "__main__":
    main()
