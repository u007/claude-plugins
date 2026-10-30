#!/usr/bin/env python3
"""SessionStart / PostToolUse hook: announce the git worktree or branch.

Reads the hook JSON on stdin and works out where the session is:

    worktree <name> (branch <branch>)   inside a linked worktree
    branch <branch>                     in a normal checkout
    branch @<short-sha>                 detached HEAD

The announcement goes to the user (`systemMessage`) and to Claude
(`additionalContext`). SessionStart always announces. PostToolUse announces
only when the location differs from the last announcement for this session,
so a run of unrelated Bash calls stays silent.

Like the context-status line, this reads the repo's HEAD file instead of
spawning git: the hook runs after every Bash call and must stay cheap.
"""

import json
import os
import re
import sys
import tempfile

# A linked worktree's git dir is <main>/.git/worktrees/<name>. Submodules also
# have a `.git` file, but point into .git/modules/, so the parent dir tells
# the two apart.
_WORKTREES_DIR = "worktrees"


def _git_dir(cwd):
    """The git directory for `cwd`, or None if it isn't a repo."""
    dot_git = os.path.join(cwd, ".git")
    if os.path.isdir(dot_git):
        return dot_git
    if os.path.isfile(dot_git):
        try:
            with open(dot_git, encoding="utf-8", errors="replace") as fh:
                pointer = fh.read().strip()
        except OSError as exc:
            print(f"branch-indicator: could not read {dot_git}: {exc}", file=sys.stderr)
            return None
        if not pointer.startswith("gitdir:"):
            return None
        target = pointer[len("gitdir:"):].strip()
        if not target:
            return None
        if not os.path.isabs(target):
            target = os.path.normpath(os.path.join(cwd, target))
        return target if os.path.isdir(target) else None
    if os.path.isfile(os.path.join(cwd, "HEAD")) and os.path.isdir(
        os.path.join(cwd, "objects")
    ):
        return cwd
    return None


def _branch_from_head(git_dir):
    """Branch name, `@<short-sha>` when detached, or '' if not determinable."""
    head_path = os.path.join(git_dir, "HEAD")
    try:
        with open(head_path, encoding="utf-8", errors="replace") as fh:
            head = fh.read().strip()
    except OSError as exc:
        print(f"branch-indicator: could not read {head_path}: {exc}", file=sys.stderr)
        return ""
    if head.startswith("ref:"):
        ref = head[len("ref:"):].strip()
        prefix = "refs/heads/"
        return ref[len(prefix):] if ref.startswith(prefix) else ""
    if re.fullmatch(r"[0-9a-fA-F]{40,64}", head):
        return "@" + head[:7]
    return ""


def _worktree_name(git_dir):
    """The linked worktree's name, or '' when `git_dir` is not a linked worktree."""
    parent = os.path.dirname(git_dir)
    if os.path.basename(parent) != _WORKTREES_DIR:
        return ""
    return os.path.basename(git_dir)


def describe(cwd):
    """Human-readable location for `cwd`, or '' when it isn't in a git repo."""
    git_dir = _git_dir(cwd)
    if not git_dir:
        return ""
    branch = _branch_from_head(git_dir)
    worktree = _worktree_name(git_dir)
    if worktree and branch:
        return f"worktree {worktree} (branch {branch})"
    if worktree:
        return f"worktree {worktree}"
    if branch:
        return f"branch {branch}"
    return ""


def _state_path(session_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)
    return os.path.join(tempfile.gettempdir(), f"branch-indicator-{safe}")


def _last_announced(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return None


def _remember(path, text):
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError as exc:
        print(f"branch-indicator: could not write {path}: {exc}", file=sys.stderr)


def main():
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        print(f"branch-indicator: unparseable hook input: {exc}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("branch-indicator: hook input is not a JSON object", file=sys.stderr)
        return 1

    cwd = data.get("cwd")
    session_id = data.get("session_id")
    event = data.get("hook_event_name")
    if not isinstance(cwd, str) or not cwd:
        print("branch-indicator: hook input has no cwd", file=sys.stderr)
        return 1
    if not isinstance(session_id, str) or not session_id:
        print("branch-indicator: hook input has no session_id", file=sys.stderr)
        return 1
    if event not in ("SessionStart", "PostToolUse"):
        print(f"branch-indicator: unexpected hook event {event!r}", file=sys.stderr)
        return 1

    location = describe(cwd)
    if not location:
        return 0

    state = _state_path(session_id)
    if event == "PostToolUse" and _last_announced(state) == location:
        return 0
    _remember(state, location)

    json.dump(
        {
            "systemMessage": f"git: {location}",
            "hookSpecificOutput": {
                "hookEventName": event,
                "additionalContext": f"Working in git {location}.",
            },
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
