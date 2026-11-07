# frontend-standards

Injects frontend standards at session start: use the present UI library, semantic HTML, micro-interaction care.

SessionStart hook (`startup|clear|compact`, not `resume`) prints `rules.md` as session context. Edit `rules.md` to change the rules. A missing file makes the hook exit non-zero.

Install:

```
/plugin install frontend-standards --marketplace u007/claude-plugins
```
