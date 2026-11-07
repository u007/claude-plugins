# Code Quality Rules

- **No flags or optional parameters that change behavior** unless explicitly asked. No `force`, `dryRun`, `verbose`, `skipX`, `enableY`.
- **No fallbacks, no workarounds, unless explicitly requested.** No `value ?? default`, `value || default`, optional-chaining that treats `undefined` as success, silent retries, `@ts-ignore` / `as any` casts, skipped tests, or patches around a root cause. Fix the cause. If a fallback is genuinely needed, ask first and state why. Code and tests fail fast and loudly.
- **No try-catch bypasses.** Only wrap operations that may legitimately fail. **Never an empty `catch` block.**
- **Never use `ON CONFLICT ... DO UPDATE` / `onConflictDoUpdate` (upsert-on-conflict).** Use an explicit query instead: check whether the row exists, then issue a separate `INSERT` or `UPDATE` accordingly.
- **Always log caught errors** with what was attempted and the error, via structured logging. Only exceptions: known benign case (still log at debug/warn) or caller-directed suppression. Either needs an inline `// intentionally not logged: <reason>` comment.
- **Track incomplete work in TODO.md.** Any stub, deferral, or partial implementation: add a TODO.md entry and tell the user explicitly.
- **Use the shared process spawn path.** If a codebase has a central supervisor/registry/spawn helper, route every new process spawn through it. Never add raw `exec.Command`, `bash -c`, etc. outside that lifecycle. If no shared path exists, build it first.
- **All listings sorted and paginated** unless a code comment (`// unsorted per spec`) or instruction says otherwise.
- DRY.
- Verify file paths exist before editing.
- Prefer separate script files over inline heredocs with complex substitution.
- Check write permissions before creating files; if read-only, say so and offer alternatives.
- Code quality analysis output always includes: file paths, line numbers, severity, effort estimate, prioritized recommendations.

## Test Safety

- **Never remove existing tests** unless refactoring them, the covered logic genuinely changed, or the feature no longer exists. Unsure? Stop and ask with reasoning and a recommendation.
