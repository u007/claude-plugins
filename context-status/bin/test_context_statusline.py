#!/usr/bin/env python3
"""Tests for context_statusline_render.py.

Runs the renderer exactly the way Claude Code does (JSON on stdin, segment
string on stdout) and asserts the rendered status line.

    python3 test_context_statusline.py

No third-party dependencies; run it from anywhere.
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_RENDERER = _HERE / "context_statusline_render.py"


def render(payload, raw=None):
    """Pipe `payload` (dict or pre-serialized str) into the renderer."""
    stdin = raw if raw is not None else json.dumps(payload)
    result = subprocess.run(
        [sys.executable, str(_RENDERER)],
        input=stdin.encode("utf-8"),
        capture_output=True,
        timeout=30,
    )
    # The renderer must never fail the status line: a nonzero exit leaves a
    # blank/garbled line in the user's terminal.
    assert result.returncode == 0, (
        "renderer exited %d: %s" % (result.returncode, result.stderr.decode())
    )
    return result.stdout.decode("utf-8").strip()


def segments(line):
    """Split a rendered status line into its ` · `-joined segments.

    Asserting on exact segment membership (rather than substring presence) is
    what makes length-sensitive expectations — a 7-char short sha, say —
    actually pinned.
    """
    return line.split(" · ")


def load_renderer():
    """Import the renderer as a module, for testing internals directly."""
    spec = importlib.util.spec_from_file_location("ctx_renderer", _RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(*args, cwd=None):
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        env={
            **os.environ,
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
        },
    )


class GitRepo:
    """A throwaway git repo, optionally on a branch and optionally detached."""

    def __init__(self, branch="main", detached=False, commit=True):
        self.dir = tempfile.mkdtemp(prefix="context-status-test-")
        git("init", "-b", branch, cwd=self.dir)
        if commit:
            (Path(self.dir) / "README.md").write_text("hi\n", encoding="utf-8")
            git("add", ".", cwd=self.dir)
            git(
                "-c", "user.email=t@example.com",
                "-c", "user.name=Test",
                "commit", "-m", "init",
                cwd=self.dir,
            )
        if detached:
            sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.dir, capture_output=True, check=True,
            ).stdout.decode().strip()
            git("checkout", "--detach", sha, cwd=self.dir)

    @property
    def path(self):
        return self.dir


def payload(**overrides):
    """A statusline payload matching Claude Code 2.1.284's documented shape."""
    base = {
        "session_id": "abc-123",
        "model": {"id": "claude-opus-4-7", "display_name": "Opus 4.7"},
        "workspace": {"current_dir": "/src/ocode", "added_dirs": []},
        "version": "2.1.284",
        "output_style": {"name": "default"},
        "cost": {"total_cost_usd": 0.42, "total_duration_ms": 1000},
        "context_window": {
            "total_input_tokens": 84000,
            "total_output_tokens": 1200,
            "context_window_size": 200000,
            "used_percentage": 42,
            "remaining_percentage": 58,
        },
        "exceeds_200k_tokens": False,
    }
    for key, value in overrides.items():
        if value is None:
            base.pop(key, None)
        else:
            base[key] = value
    return base


class ModelSegment(unittest.TestCase):
    def test_shows_model_display_name(self):
        out = render(payload())
        self.assertIn("Opus 4.7", out)

    def test_model_appears_before_context(self):
        out = render(payload())
        self.assertLess(out.index("Opus 4.7"), out.index("ctx"))

    def test_falls_back_to_model_id_when_display_name_missing(self):
        out = render(payload(model={"id": "claude-sonnet-4-5"}))
        self.assertIn("claude-sonnet-4-5", out)

    def test_falls_back_to_model_id_when_display_name_blank(self):
        out = render(payload(model={"id": "claude-haiku-4-5", "display_name": "  "}))
        self.assertIn("claude-haiku-4-5", out)

    def test_omits_segment_when_model_absent(self):
        out = render(payload(model=None))
        self.assertNotIn("claude-opus-4-7", out)
        self.assertNotIn("None", out)
        # ...and the rest of the line survives.
        self.assertIn("ctx", out)

    def test_does_not_crash_on_non_dict_model(self):
        out = render(payload(model="opus"))
        self.assertIn("ctx", out)


class DirSegment(unittest.TestCase):
    def test_shows_basename_of_current_dir(self):
        out = render(payload())
        self.assertIn("ocode", out)

    def test_strips_trailing_slash(self):
        out = render(payload(workspace={"current_dir": "/src/ocode/"}))
        self.assertIn("· ocode ·", out)

    def test_omits_when_workspace_missing(self):
        out = render(payload(workspace=None))
        self.assertNotIn("· None", out)
        self.assertIn("Opus 4.7", out)

    def test_root_dir_does_not_render_empty_segment(self):
        out = render(payload(workspace={"current_dir": "/"}))
        self.assertNotIn("·  ·", out)


class BranchSegment(unittest.TestCase):
    def test_shows_current_branch(self):
        repo = GitRepo(branch="feature/statusline")
        out = render(payload(workspace={"current_dir": repo.path}))
        self.assertIn("feature/statusline", out)

    def test_branch_sits_between_dir_and_context(self):
        repo = GitRepo(branch="main")
        out = render(payload(workspace={"current_dir": repo.path}))
        self.assertLess(out.index(repo.path.rsplit("/", 1)[-1]), out.index("main"))
        self.assertLess(out.index("main"), out.index("ctx"))

    def test_detached_head_shows_short_sha(self):
        repo = GitRepo(branch="main", detached=True)
        out = render(payload(workspace={"current_dir": repo.path}))
        full_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo.dir, capture_output=True, check=True,
        ).stdout.decode().strip()
        # Exact segment, not a substring: the short sha must be exactly 7
        # chars. A substring check would also pass on the full 40-char sha.
        self.assertIn("@" + full_sha[:7], segments(out))
        self.assertNotIn("@" + full_sha, segments(out))

    def test_unborn_branch_still_shows_branch_name(self):
        repo = GitRepo(branch="trunk", commit=False)
        out = render(payload(workspace={"current_dir": repo.path}))
        self.assertIn("trunk", out)

    def test_omits_branch_outside_a_git_repo(self):
        with tempfile.TemporaryDirectory() as plain:
            out = render(payload(workspace={"current_dir": plain}))
            self.assertIn("ctx", out)
            self.assertNotIn("@", out)

    def test_omits_branch_when_dir_missing(self):
        out = render(payload(workspace={}))
        self.assertIn("Opus 4.7", out)
        self.assertNotIn("@", out)


class GitDirLayouts(unittest.TestCase):
    """The branch is read from HEAD, so the repo layouts that move the git
    directory out of `<cwd>/.git` must still resolve."""

    def test_linked_worktree_gitdir_file(self):
        repo = GitRepo(branch="main")
        wt = os.path.join(tempfile.mkdtemp(prefix="context-status-wt-"), "wt")
        git("worktree", "add", "-b", "wt-branch", wt, cwd=repo.dir)
        try:
            # Sanity: this really is the `.git`-is-a-file layout.
            self.assertTrue(os.path.isfile(os.path.join(wt, ".git")))
            out = render(payload(workspace={"current_dir": wt}))
            self.assertIn("wt-branch", out)
        finally:
            git("worktree", "remove", "--force", wt, cwd=repo.dir)

    def test_relative_gitdir_pointer(self):
        """Submodules record a relative `gitdir:`; resolve it against cwd."""
        with tempfile.TemporaryDirectory() as root:
            git_dir = os.path.join(root, "real-gitdir")
            os.makedirs(os.path.join(git_dir, "refs", "heads"))
            with open(os.path.join(git_dir, "HEAD"), "w", encoding="utf-8") as fh:
                fh.write("ref: refs/heads/relative-branch\n")
            work = os.path.join(root, "sub")
            os.makedirs(work)
            with open(os.path.join(work, ".git"), "w", encoding="utf-8") as fh:
                fh.write("gitdir: ../real-gitdir\n")
            out = render(payload(workspace={"current_dir": work}))
            self.assertIn("relative-branch", out)

    def test_absolute_gitdir_pointer(self):
        with tempfile.TemporaryDirectory() as root:
            git_dir = os.path.join(root, "abs-gitdir")
            os.makedirs(os.path.join(git_dir, "refs", "heads"))
            with open(os.path.join(git_dir, "HEAD"), "w", encoding="utf-8") as fh:
                fh.write("ref: refs/heads/absolute-branch\n")
            work = os.path.join(root, "sub")
            os.makedirs(work)
            with open(os.path.join(work, ".git"), "w", encoding="utf-8") as fh:
                fh.write(f"gitdir: {git_dir}\n")
            out = render(payload(workspace={"current_dir": work}))
            self.assertIn("absolute-branch", out)

    def test_bare_repo_head_at_top_level(self):
        with tempfile.TemporaryDirectory() as bare:
            git("init", "-b", "bare-branch", "--bare", cwd=bare)
            out = render(payload(workspace={"current_dir": bare}))
            self.assertIn("bare-branch", out)

    def test_malformed_gitdir_pointer_is_ignored(self):
        with tempfile.TemporaryDirectory() as work:
            with open(os.path.join(work, ".git"), "w", encoding="utf-8") as fh:
                fh.write("not-a-gitdir-pointer\n")
            out = render(payload(workspace={"current_dir": work}))
            self.assertIn("ctx", out)

    def test_dangling_gitdir_pointer_is_ignored(self):
        with tempfile.TemporaryDirectory() as work:
            with open(os.path.join(work, ".git"), "w", encoding="utf-8") as fh:
                fh.write("gitdir: /nonexistent/path/to/gitdir\n")
            out = render(payload(workspace={"current_dir": work}))
            self.assertIn("ctx", out)

    def test_head_pointing_outside_refs_heads_is_ignored(self):
        with tempfile.TemporaryDirectory() as work:
            git_dir = os.path.join(work, ".git")
            os.makedirs(os.path.join(git_dir, "refs", "heads"))
            with open(os.path.join(git_dir, "HEAD"), "w", encoding="utf-8") as fh:
                fh.write("ref: refs/pull/42/head\n")
            out = render(payload(workspace={"current_dir": work}))
            self.assertIn("ctx", out)
            self.assertNotIn("refs/pull", out)


class GitDirContract(unittest.TestCase):
    """`_git_dir` promises a real git directory or None.

    Pinned directly because the rendered output alone can't distinguish
    "returned None" from "returned a path whose HEAD then failed to open".
    """

    def setUp(self):
        self.mod = load_renderer()

    def test_normal_repo(self):
        repo = GitRepo()
        self.assertEqual(self.mod._git_dir(repo.path), os.path.join(repo.path, ".git"))

    def test_none_outside_a_repo(self):
        with tempfile.TemporaryDirectory() as plain:
            self.assertIsNone(self.mod._git_dir(plain))

    def test_none_for_dangling_gitdir_pointer(self):
        with tempfile.TemporaryDirectory() as work:
            with open(os.path.join(work, ".git"), "w", encoding="utf-8") as fh:
                fh.write("gitdir: /nonexistent/path/to/gitdir\n")
            self.assertIsNone(self.mod._git_dir(work))

    def test_none_for_empty_gitdir_pointer(self):
        with tempfile.TemporaryDirectory() as work:
            with open(os.path.join(work, ".git"), "w", encoding="utf-8") as fh:
                fh.write("gitdir:\n")
            self.assertIsNone(self.mod._git_dir(work))

    def test_follows_relative_gitdir_pointer(self):
        with tempfile.TemporaryDirectory() as root:
            real = os.path.join(root, "real-gitdir")
            os.makedirs(real)
            work = os.path.join(root, "sub")
            os.makedirs(work)
            with open(os.path.join(work, ".git"), "w", encoding="utf-8") as fh:
                fh.write("gitdir: ../real-gitdir\n")
            self.assertEqual(self.mod._git_dir(work), real)


class ContextSegment(unittest.TestCase):
    def test_renders_bar_percent_and_tokens(self):
        out = render(payload())
        self.assertIn("ctx", out)
        self.assertIn("42%", out)
        self.assertIn("84.0k", out)
        self.assertIn("200.0k", out)

    def test_unknown_context_renders_dash(self):
        out = render(payload(context_window=None))
        self.assertIn("ctx —", out)


class Robustness(unittest.TestCase):
    def test_malformed_json_does_not_crash(self):
        out = render(None, raw="{not json")
        self.assertTrue(out)

    def test_empty_object_does_not_crash(self):
        self.assertTrue(render({}))

    def test_chained_prev_command_output_is_preserved(self):
        marker = "zz-prev-marker"
        path = _HERE / "prev_command.txt"
        original = path.read_text(encoding="utf-8") if path.exists() else None
        try:
            path.write_text(
                "cat >/dev/null; printf '%s'" % marker, encoding="utf-8"
            )
            out = render(payload())
            self.assertIn(marker, out)
            self.assertLess(out.index("Opus 4.7"), out.index(marker))
        finally:
            if original is None:
                path.unlink()
            else:
                path.write_text(original, encoding="utf-8")

    def test_broken_prev_command_does_not_break_the_line(self):
        path = _HERE / "prev_command.txt"
        original = path.read_text(encoding="utf-8") if path.exists() else None
        try:
            path.write_text("exit 7", encoding="utf-8")
            out = render(payload())
            self.assertIn("Opus 4.7", out)
        finally:
            if original is None:
                path.unlink()
            else:
                path.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
