#!/usr/bin/env bash
# Context Status statusLine entrypoint.
# Claude Code pipes the statusline JSON on stdin; hand it to the renderer.
exec python3 "$(dirname "$0")/context_statusline_render.py"
