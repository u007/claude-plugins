#!/bin/sh
# SessionStart hook: when the project has an OKF bundle (docs/index.md with an
# okf_version marker), tell Claude to run the okf skill's lookup step before
# any task. Silent otherwise. POSIX sh only: the desktop app does not load
# shell profiles, so python3 or other tools may not be on PATH.
dir="${CLAUDE_PROJECT_DIR:-$PWD}"
index="$dir/docs/index.md"
[ -f "$index" ] || exit 0
# okf_version must sit inside the leading YAML frontmatter (between the first two
# `---` lines), not anywhere in the first lines of the file.
awk '
  NR == 1 { if ($0 != "---") exit 1; next }
  $0 == "---" { closed = 1; exit }
  /^okf_version:/ { found = 1 }
  END { exit !(closed && found) }
' "$index" || exit 0
echo "OKF knowledge bundle detected at docs/ (docs/index.md has okf_version). Before starting ANY task in this project, invoke the okf skill and run its lookup step in a Haiku subagent (Agent tool, model haiku). After the task, have a Haiku subagent update the bundle per the skill's rules."
