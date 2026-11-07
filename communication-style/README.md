# communication-style

SessionStart hook that injects the Agent Communication & Style Standard (ASD-STE100 structural limits plus software-domain overrides), ported from `ocode` (`internal/agent/prompt.go`).

The text lives in `standard.md`. Edit it there; the hook is `cat standard.md`, so a missing file makes it exit non-zero. Works unchanged in ocode, which runs the same SessionStart hook with empty stdin.

```
/plugin install communication-style@personal-plugins
```

Test: `python3 tests/test_rule_plugins.py`

Precedence: the standard itself says explicit user instructions and project docs override it. Your `~/.claude/CLAUDE.md` rules (caveman mode, Flow Context, ULTRATHINK) therefore win on conflict.

To prefer this standard over caveman, remove the "Communication: Caveman Mode" section from `~/.claude/CLAUDE.md`. To turn this plugin off, run `/plugin disable communication-style@personal-plugins`.

Injected on `startup`, `clear` and `compact`. Skipped on `resume`, where the earlier context is restored.
