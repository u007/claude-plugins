# git-safety

Injects git safety rules at session start: no bare git reset --soft in shared repos.

SessionStart hook (`startup|clear|compact`, not `resume`) prints `rules.md` as session context. Edit `rules.md` to change the rules. A missing file makes the hook exit non-zero.

Install:

```
/plugin install git-safety --marketplace u007/claude-plugins
```
