# code-quality

Injects code quality rules at session start: no fallbacks, error logging, no upsert, TODO tracking, test safety.

SessionStart hook (`startup|clear|compact`, not `resume`) prints `rules.md` as session context. Edit `rules.md` to change the rules. A missing file makes the hook exit non-zero.

Install:

```
/plugin install code-quality --marketplace u007/claude-plugins
```
