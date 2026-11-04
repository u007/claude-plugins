#!/usr/bin/env python3
"""Tests for ensure_statusline.py (stdlib unittest, no install step)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "ensure_statusline.py"
TARGET = str(SCRIPT.parent.parent / "bin" / "context-statusline.sh")


class EnsureStatusline(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.settings = self.dir / "settings.json"

    def run_hook(self):
        env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.dir)}
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
        )

    def read(self):
        return json.loads(self.settings.read_text())

    def test_creates_settings_when_missing(self):
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.read()["statusLine"], {"type": "command", "command": TARGET}
        )
        self.assertIn("systemMessage", json.loads(result.stdout))

    def test_adds_statusline_and_keeps_other_keys(self):
        self.settings.write_text(json.dumps({"model": "x", "env": {"A": "1"}}))
        self.run_hook()
        data = self.read()
        self.assertEqual(data["model"], "x")
        self.assertEqual(data["env"], {"A": "1"})
        self.assertEqual(data["statusLine"]["command"], TARGET)

    def test_silent_when_already_correct(self):
        self.settings.write_text(
            json.dumps({"statusLine": {"type": "command", "command": TARGET}})
        )
        result = self.run_hook()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_repoints_stale_managed_path(self):
        old = "/x/cache/personal-plugins/context-status/1.0.0/bin/context-statusline.sh"
        self.settings.write_text(
            json.dumps({"statusLine": {"type": "command", "command": old}})
        )
        self.run_hook()
        self.assertEqual(self.read()["statusLine"]["command"], TARGET)

    def test_leaves_foreign_statusline_alone(self):
        foreign = {"type": "command", "command": "/usr/local/bin/mine.sh"}
        self.settings.write_text(json.dumps({"statusLine": foreign}))
        result = self.run_hook()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.read()["statusLine"], foreign)
        self.assertIn("not managed", result.stderr)

    def test_invalid_json_fails_and_is_not_overwritten(self):
        self.settings.write_text("{not json")
        result = self.run_hook()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.settings.read_text(), "{not json")


if __name__ == "__main__":
    unittest.main()
