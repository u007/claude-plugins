# context-status

Claude Code status line showing, in order:

```
<model> · <dir> · <git branch> · ctx <bar> NN% (used/total) · <chained statusline>
```

e.g. `Opus 5.5 · ocode · main · ctx █░░░░░░░░░ 6% (57.9k/1000.0k) · ● cognee: agent_sessions · local`

## Layout

| File | Role |
| --- | --- |
| `bin/context-statusline.sh` | Entrypoint registered as `statusLine` in `~/.claude/settings.json`. Just `exec`s the renderer so it inherits stdin. |
| `bin/context_statusline_render.py` | The renderer. All logic lives here. |
| `bin/prev_command.txt` | The status line that was configured before this plugin; its output is appended so chaining keeps working. Blank it to disable chaining. |
| `bin/test_context_statusline.py` | Test suite. |

## Payload fields consumed

Claude Code pipes a JSON context on stdin. This plugin reads only:

- `model.display_name` (falls back to `model.id`)
- `workspace.current_dir`
- `context_window.{used_percentage,total_input_tokens,context_window_size}`

**There is no branch field in the payload.** `workspace.git_worktree` is set
only for linked worktrees and carries a path; `worktree.branch` exists only
for agent-isolation worktrees. The branch is therefore read from the repo's
`HEAD` file — deliberately *not* by shelling out to `git`, which keeps the
status line off the process-spawn path (no ~30ms per refresh, and no way for
a hung `git` to stall the UI). `_git_dir` handles normal repos, linked
worktrees and submodules (`.git` is a file containing `gitdir: <path>`, which
may be relative), and bare repos.

Every segment is best-effort: missing data, a non-repo directory, a detached
HEAD or a broken chained command degrade by dropping a segment rather than
showing a placeholder. A detached HEAD renders as `@<short-sha>`; an unborn
branch still renders its name, matching `git branch --show-current`.

## Tests

```sh
python3 bin/test_context_statusline.py
```

Standard library only, no dependencies. Pipes payloads through the renderer
exactly as Claude Code does and asserts the rendered line. Uses real
throwaway git repos (including a linked worktree) for the branch cases.
