# jev-guard

Claude Code plugin. PostToolUse hook port of ocode's inbound-content guardrail (`~/www/ocode/internal/agent/content_guard_typesafe.go`), judged by TypeSafe Jev (`POST https://api.typesafe.ai/v1/systemone`, model `jev-latest`).

- **Scans:** WebFetch, WebSearch, every `mcp__*` tool, and Bash only when it runs a network binary (curl, wget, nc, ncat, http, https, ftp, sftp) against a non-loopback host. Local Bash/Read output is never scanned.
- **Flagged:** result replaced via `updatedToolOutput` with a withheld notice, plus `decision: block` and `additionalContext` as a backstop. Claude Code hooks cannot ask the user post-tool, so there is no approve dialog (ocode asks; this denies).
- **Unvetted** (no `TYPESAFE_API_KEY`, judge error/timeout, low-confidence clean < 0.6): result delivered, but the model is told it is unvetted. Over 32 chunks of 6000 chars: flagged.
- **Unverified:** the `tool_response` shape for WebFetch/WebSearch/MCP. The replacement mirrors the original's type; check with a real flagged result.

## Setup

1. **Get a TypeSafe API key** for the Jev judge.
2. **Export it in your shell profile** (`~/.zshrc` on macOS default zsh):

   ```sh
   export TYPESAFE_API_KEY=<your-key>
   ```

   Keep the real key out of the repo. `.env.example` holds only a placeholder.
3. **Open a new terminal** so the profile is loaded. Confirm it is set:

   ```sh
   [ -n "$TYPESAFE_API_KEY" ] && echo set || echo "not set"
   ```

4. **Start Claude Code from that terminal.** Apps launched from the Dock or Spotlight do not read `~/.zshrc`, so they will not see the variable. Without the variable, results are delivered as unvetted.

## Install

From the marketplace (see the repo-level README for the marketplace steps):

```
/plugin install jev-guard@personal-plugins
```

To test without installing, from a clone of the repo:

```sh
claude --plugin-dir ./jev-guard
```

Not yet verified end to end on a clean machine.
