# working-principles

Injects working principles at session start: fix suggestion protocol, docs as source of truth, surgical changes, planning rules.

SessionStart hook (`startup|clear|compact`, not `resume`) prints `rules.md` as session context. Edit `rules.md` to change the rules. A missing file makes the hook exit non-zero.

Install:

```
/plugin install working-principles --marketplace u007/claude-plugins
```
