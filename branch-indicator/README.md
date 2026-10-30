# branch-indicator

Tells you, and Claude, where the session is working:

| Situation | Shown |
| --- | --- |
| Inside a linked git worktree | `git: worktree <name> (branch <branch>)` |
| Normal checkout | `git: branch <branch>` |
| Detached HEAD | `git: branch @<short-sha>` |
| Not a git repo | nothing |

The message appears at session start and again whenever it changes (for example after `git switch`, `git checkout`, `cd` into a worktree, or `EnterWorktree` / `ExitWorktree`). Unchanged locations stay silent, so it does not repeat after every Bash call. The same text is also added to Claude's context, so the model knows which worktree it is editing.

## Install

```
/plugin install branch-indicator@personal-plugins
```

Requires `python3` on `PATH`. No setup beyond that.

## How it works

`scripts/branch_indicator.py` runs on `SessionStart` and after `Bash`, `EnterWorktree` and `ExitWorktree`. It reads the hook's `cwd`, resolves the git dir and reads `HEAD` directly (no `git` process). A linked worktree is recognised by its git dir living under `.git/worktrees/<name>`. The last announcement per session is kept in a file named `branch-indicator-<session_id>` in the system temp dir.

Malformed hook input or an unwritable state file is reported on stderr with a non-zero exit (input) or a logged warning (state), never swallowed.

The git-dir and `HEAD` parsing is a copy of the logic in `context-status`; plugins install independently, so they cannot share code.

## Tests

```sh
python3 branch-indicator/scripts/test_branch_indicator.py
```
