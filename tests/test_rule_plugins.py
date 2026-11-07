import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ["communication-style", "working-principles", "code-quality", "git-safety", "frontend-standards"]


RULES_FILE = {"communication-style": "standard.md"}


class RulePlugins(unittest.TestCase):
    def test_manifests_agree(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        for name in PLUGINS:
            plugin = json.loads((ROOT / name / ".claude-plugin" / "plugin.json").read_text())
            entry = next(p for p in market["plugins"] if p["name"] == name)
            self.assertEqual(plugin["name"], name)
            self.assertEqual(entry["version"], plugin["version"])
            self.assertEqual(entry["description"], plugin["description"])

    def test_hook_outputs_rules_and_skips_resume(self):
        for name in PLUGINS:
            hooks = json.loads((ROOT / name / "hooks" / "hooks.json").read_text())
            group = hooks["hooks"]["SessionStart"][0]
            self.assertEqual(group["matcher"], "startup|clear|compact")
            command = group["hooks"][0]["command"].replace("${CLAUDE_PLUGIN_ROOT}", str(ROOT / name))
            out = subprocess.run(command, shell=True, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True).stdout
            self.assertEqual(out, (ROOT / name / RULES_FILE.get(name, "rules.md")).read_text())
            self.assertTrue(out.strip())

    def test_missing_file_exits_nonzero(self):
        for name in PLUGINS:
            hooks = json.loads((ROOT / name / "hooks" / "hooks.json").read_text())
            command = hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"].replace(
                "${CLAUDE_PLUGIN_ROOT}", "/nonexistent-plugin-root"
            )
            result = subprocess.run(command, shell=True, stdin=subprocess.DEVNULL, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)

    def test_key_rules_present(self):
        expect = {
            "communication-style": "brevity wins",
            "working-principles": "Flow Context",
            "code-quality": "onConflictDoUpdate",
            "git-safety": "git reset --soft",
            "frontend-standards": "Library discipline",
        }
        for name, needle in expect.items():
            self.assertIn(needle, (ROOT / name / RULES_FILE.get(name, "rules.md")).read_text())


if __name__ == "__main__":
    unittest.main()
