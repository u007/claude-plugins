import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parent / "communication_style.py"
sys.path.insert(0, str(SCRIPT.parent))
import communication_style  # noqa: E402


def run_hook(payload: dict) -> str:
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT)], input=json.dumps(payload), capture_output=True, text=True, check=True
    ).stdout


class Hook(unittest.TestCase):
    def test_emits_session_start_context(self):
        spec = json.loads(run_hook({"source": "startup"}))["hookSpecificOutput"]
        self.assertEqual(spec["hookEventName"], "SessionStart")
        self.assertIn("ASD-STE100", spec["additionalContext"])
        self.assertIn("Never rotate synonyms", spec["additionalContext"])
        self.assertIn("override this standard", spec["additionalContext"])

    def test_injects_on_clear_and_compact(self):
        for source in ("clear", "compact"):
            self.assertIn("hookSpecificOutput", json.loads(run_hook({"source": source})))

    def test_silent_on_resume(self):
        self.assertEqual(run_hook({"source": "resume"}), "")

    def test_missing_standard_raises(self):
        with mock.patch.object(communication_style, "STANDARD", Path("/nonexistent/standard.md")):
            with self.assertRaises(FileNotFoundError):
                communication_style.build_output()


class Manifests(unittest.TestCase):
    def test_plugin_and_marketplace_agree(self):
        root = SCRIPT.parent.parent
        plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
        market = json.loads((root.parent / ".claude-plugin" / "marketplace.json").read_text())
        entry = next(p for p in market["plugins"] if p["name"] == plugin["name"])
        self.assertEqual(entry["version"], plugin["version"])
        self.assertEqual(entry["description"], plugin["description"])


if __name__ == "__main__":
    unittest.main()
