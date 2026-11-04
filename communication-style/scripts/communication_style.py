#!/usr/bin/env python3
"""SessionStart hook: inject the communication standard as additionalContext."""
import json
import sys
from pathlib import Path

STANDARD = Path(__file__).resolve().parent.parent / "standard.md"


def build_output() -> dict:
    # Missing file raises: fail loudly rather than silently dropping the standard.
    text = STANDARD.read_text(encoding="utf-8").strip()
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "[communication_style]\n" + text,
        }
    }


def main() -> int:
    payload = json.load(sys.stdin)
    # On resume the earlier transcript, with the standard already in it, is restored.
    if payload.get("source") == "resume":
        return 0
    json.dump(build_output(), sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
