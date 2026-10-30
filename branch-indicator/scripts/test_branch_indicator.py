#!/usr/bin/env python3
"""Tests for branch_indicator.py (stdlib unittest, no install step)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "branch_indicator.py"
SHA = "a" * 40


def make_repo(root, head="ref: refs/heads/main\n"):
    git = Path(root) / ".git"
    git.mkdir(parents=True)
    (git / "HEAD").write_text(head)
    return Path(root)


def make_worktree(main, wt_root, name, head="ref: refs/heads/feature\n"):
    wt_git = Path(main) / ".git" / "worktrees" / name
    wt_git.mkdir(parents=True)
    (wt_git / "HEAD").write_text(head)
    Path(wt_root).mkdir(parents=True)
    (Path(wt_root) / ".git").write_text(f"gitdir: {wt_git}\n")
    return Path(wt_root)


def run_hook(cwd, event="SessionStart", session_id="s1", tmpdir=None, raw=None):
    payload = raw if raw is not None else json.dumps(
        {"cwd": str(cwd), "session_id": session_id, "hook_event_name": event}
    )
    env = {**os.environ, "TMPDIR": tmpdir} if tmpdir else os.environ
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )


class Describe(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        sys.path.insert(0, str(SCRIPT.parent))
        self.addCleanup(sys.path.remove, str(SCRIPT.parent))
        import branch_indicator

        self.describe = branch_indicator.describe

    def test_normal_repo_shows_branch(self):
        repo = make_repo(Path(self.tmp.name) / "repo")
        self.assertEqual(self.describe(str(repo)), "branch main")

    def test_detached_head_shows_short_sha(self):
        repo = make_repo(Path(self.tmp.name) / "repo", head=SHA + "\n")
        self.assertEqual(self.describe(str(repo)), "branch @aaaaaaa")

    def test_linked_worktree_shows_name_and_branch(self):
        main = make_repo(Path(self.tmp.name) / "main")
        wt = make_worktree(main, Path(self.tmp.name) / "wt-x", "wt-x")
        self.assertEqual(self.describe(str(wt)), "worktree wt-x (branch feature)")

    def test_linked_worktree_detached(self):
        main = make_repo(Path(self.tmp.name) / "main")
        wt = make_worktree(main, Path(self.tmp.name) / "wt-x", "wt-x", head=SHA + "\n")
        self.assertEqual(self.describe(str(wt)), "worktree wt-x (branch @aaaaaaa)")

    def test_submodule_is_not_a_worktree(self):
        main = make_repo(Path(self.tmp.name) / "main")
        mod_git = main / ".git" / "modules" / "sub"
        mod_git.mkdir(parents=True)
        (mod_git / "HEAD").write_text("ref: refs/heads/dev\n")
        sub = Path(self.tmp.name) / "main" / "sub"
        sub.mkdir()
        (sub / ".git").write_text("gitdir: ../.git/modules/sub\n")
        self.assertEqual(self.describe(str(sub)), "branch dev")

    def test_not_a_repo_is_empty(self):
        self.assertEqual(self.describe(self.tmp.name), "")


class Hook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = tempfile.mkdtemp(dir=self.tmp.name)
        self.repo = make_repo(Path(self.tmp.name) / "repo")

    def test_session_start_announces_to_user_and_claude(self):
        result = run_hook(self.repo, tmpdir=self.state)
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout)
        self.assertEqual(out["systemMessage"], "git: branch main")
        hso = out["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "SessionStart")
        self.assertEqual(hso["additionalContext"], "Working in git branch main.")

    def test_post_tool_use_announces_first_then_is_silent_when_unchanged(self):
        first = run_hook(self.repo, event="PostToolUse", tmpdir=self.state)
        self.assertIn("branch main", first.stdout)
        second = run_hook(self.repo, event="PostToolUse", tmpdir=self.state)
        self.assertEqual(second.returncode, 0)
        self.assertEqual(second.stdout, "")

    def test_post_tool_use_announces_again_after_change(self):
        run_hook(self.repo, event="PostToolUse", tmpdir=self.state)
        (self.repo / ".git" / "HEAD").write_text("ref: refs/heads/other\n")
        result = run_hook(self.repo, event="PostToolUse", tmpdir=self.state)
        self.assertIn("branch other", result.stdout)

    def test_session_start_announces_even_if_unchanged(self):
        run_hook(self.repo, tmpdir=self.state)
        again = run_hook(self.repo, tmpdir=self.state)
        self.assertIn("branch main", again.stdout)

    def test_sessions_do_not_share_state(self):
        run_hook(self.repo, event="PostToolUse", session_id="a", tmpdir=self.state)
        other = run_hook(self.repo, event="PostToolUse", session_id="b", tmpdir=self.state)
        self.assertIn("branch main", other.stdout)

    def test_outside_repo_is_silent(self):
        result = run_hook(self.tmp.name, tmpdir=self.state)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_bad_input_fails_loudly(self):
        result = run_hook(self.repo, raw="not json", tmpdir=self.state)
        self.assertEqual(result.returncode, 1)
        self.assertIn("unparseable hook input", result.stderr)

    def test_missing_cwd_fails_loudly(self):
        raw = json.dumps({"session_id": "s", "hook_event_name": "SessionStart"})
        result = run_hook(self.repo, raw=raw, tmpdir=self.state)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no cwd", result.stderr)


if __name__ == "__main__":
    unittest.main()
