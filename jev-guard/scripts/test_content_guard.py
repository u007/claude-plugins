#!/usr/bin/env python3
"""Tests for content_guard.py (stdlib unittest, no network: the judge is stubbed)."""
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_guard as g

REDIRECT = {
    "bytes": 621, "code": 302, "codeText": "Found",
    "result": "REDIRECT DETECTED: use WebFetch again with these parameters:\n- url: \"https://x\"",
    "url": "https://rustdesk.com/download",
}


def verdict(choice, conf):
    return {"answers": {"verdict": {"type": "choice", "choice": choice, "confidence": conf},
                        "concern": {"type": "choice", "choice": "tool_coercion" if choice == "flagged" else "none"}}}


def run(tool, tool_input, tool_response, judge_result=None, key="k"):
    payload = json.dumps({"tool_name": tool, "tool_input": tool_input, "tool_response": tool_response})
    env = {"TYPESAFE_API_KEY": key} if key else {}
    out = io.StringIO()
    with mock.patch.dict(os.environ, env, clear=True), \
            mock.patch("sys.stdin", io.StringIO(payload)), \
            mock.patch.object(g, "judge", return_value=judge_result) as j, \
            mock.patch.object(g, "log"), redirect_stdout(out):
        g.main()
    return (json.loads(out.getvalue()) if out.getvalue() else None), j


class Redirect(unittest.TestCase):
    def test_webfetch_redirect_not_judged(self):
        out, j = run("WebFetch", {"url": "https://rustdesk.com/download"}, REDIRECT, verdict("flagged", 0.9))
        j.assert_not_called()
        self.assertNotIn("decision", out)
        self.assertIn("redirect", out["hookSpecificOutput"]["additionalContext"])

    def test_non_redirect_still_judged(self):
        resp = {**REDIRECT, "code": 200, "result": "plain page"}
        _, j = run("WebFetch", {"url": "u"}, resp, verdict("clean", 1.0))
        j.assert_called_once()


class Outcomes(unittest.TestCase):
    def test_flagged_blocks_and_names_concern(self):
        out, _ = run("WebFetch", {"url": "u"}, {"result": "x"}, verdict("flagged", 0.88))
        self.assertEqual(out["decision"], "block")
        self.assertIn("tool_coercion", out["reason"])
        self.assertIn("0.88", out["reason"])

    def test_low_confidence_clean_is_withheld_with_distinct_notice(self):
        out, _ = run("WebFetch", {"url": "u"}, {"result": "x"}, verdict("clean", 0.3))
        self.assertEqual(out["decision"], "block")
        self.assertIn("could not confirm", out["reason"])
        self.assertNotIn("steer", out["reason"])

    def test_oversize_is_truncated_to_scanned_prefix(self):
        text = "a" * (g.CHUNK_CHARS * (g.CHUNK_CAP + 1))
        out, j = run("WebFetch", {"url": "u"}, {"result": text}, verdict("clean", 1.0))
        self.assertEqual(j.call_count, g.CHUNK_CAP)
        self.assertNotIn("decision", out)
        delivered = out["hookSpecificOutput"]["updatedToolOutput"]["result"]
        self.assertTrue(delivered.startswith("a" * (g.CHUNK_CHARS * g.CHUNK_CAP)))
        self.assertLess(delivered.count("a"), len(text))
        self.assertIn("truncated", delivered)

    def test_oversize_with_flagged_chunk_blocks(self):
        text = "a" * (g.CHUNK_CHARS * (g.CHUNK_CAP + 1))
        out, _ = run("WebFetch", {"url": "u"}, {"result": text}, verdict("flagged", 0.95))
        self.assertEqual(out["decision"], "block")

    def test_clean_is_silent(self):
        out, _ = run("WebFetch", {"url": "u"}, {"result": "x"}, verdict("clean", 1.0))
        self.assertIsNone(out)

    def test_no_key_is_announced(self):
        out, j = run("WebFetch", {"url": "u"}, {"result": "x"}, key=None)
        j.assert_not_called()
        self.assertIn("NOT scanned", out["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
