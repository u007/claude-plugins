# jev-guard

Claude Code plugin. PostToolUse hook port of ocode's inbound-content guardrail (`~/www/ocode/internal/agent/content_guard_typesafe.go`), judged by TypeSafe Jev (`POST https://api.typesafe.ai/v1/systemone`, model `jev-latest`).

- **Scans:** WebFetch, WebSearch, every `mcp__*` tool, and Bash only when it runs a network binary (curl, wget, nc, ncat, http, https, ftp, sftp) against a non-loopback host. Local Bash/Read output is never scanned.
- **Flagged:** result replaced via `updatedToolOutput` with a withheld notice, plus `decision: block` and `additionalContext` as a backstop. Claude Code hooks cannot ask the user post-tool, so there is no approve dialog (ocode asks; this denies).
- **Unvetted** (no `TYPESAFE_API_KEY`, judge error/timeout, low-confidence clean < 0.6): result delivered, but the model is told it is unvetted. Over 32 chunks of 6000 chars: flagged.
- **Setup:** export `TYPESAFE_API_KEY` where Claude Code runs. Try it: `claude --plugin-dir ~/www/personal-plugins/jev-guard`.
- **Install:** `/plugin install jev-guard@personal-plugins` (marketplace: `~/www/personal-plugins`).
- **Unverified:** the `tool_response` shape for WebFetch/WebSearch/MCP. The replacement mirrors the original's type; check with a real flagged result.
