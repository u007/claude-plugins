# Git Safety Rules

- **Never run bare `git reset --soft` / `git reset --soft HEAD` without file paths.** Multiple agents may share the repo.
- Resetting specific files is allowed only after inspecting `git diff` and `git diff --cached` for that file. Unrelated changes present? Stop and inform the user.
