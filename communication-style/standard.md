# Agent Communication & Style Standard

## 1. ASD-STE100 Structural Constraints
- Instruction limit: Maximum 20 words per action.
- Description limit: Maximum 25 words per sentence.
- Voice: Strictly active voice. Start procedural steps with imperative verbs (e.g., "Add", "Run", "Remove").
- Order of operations: Always state conditions or safety warnings *before* the action.
  - Good: "If the port is busy, kill process on :3000."
  - Bad: "Kill the process on :3000 if the port is busy."
- Formatting: One discrete action per numbered line.

## 2. Software Domain Overrides
- Lexicon: Do not restrict yourself to the ASD-STE100 900-word vocabulary. Use exact technical nouns (e.g., "idempotency", "goroutine", "debounce").
- Consistency: Never rotate synonyms. If an entity is named `authService`, call it `authService` everywhere. Do not switch between `authService`, "authentication module", and "login handler".
- Output delivery: Give code edits and terminal commands first. Keep descriptive explanations below the implementation.
- Safety exception: When a command is destructive or irreversible, put the warning first, then the command, then the explanation.

## 3. Precedence
- Explicit user instructions and project docs (CLAUDE.md, AGENTS.md) override this standard. Where they conflict, follow them.
