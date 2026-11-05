"""Regression tests for scaffy.py CLI behavior (real subprocess runs in temp dirs)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPO, new_project, scaffy, snapshot

sys.path.insert(0, str(REPO))
import scaffy as scaffy_mod  # noqa: E402

GOVERNANCE = ["none", "lightweight", "standard", "strict"]
PLATFORMS = ["github", "gitlab", "azure-devops", "none"]


class TempDirCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()


class TestInit(TempDirCase):
    def test_every_governance_mode(self) -> None:
        for mode in GOVERNANCE:
            with self.subTest(mode=mode):
                root = new_project(self.tmp, f"gov-{mode}", "--governance", mode)
                collab = root / ".collab"
                for rel in ("collab-contract.md", "kanban-board.md", "context.md",
                            "project.yaml", "prompts/initial-prompt.md"):
                    self.assertTrue((collab / rel).is_file(), rel)
                for d in ("brainstorms", "session-summaries", "playbooks", "guides",
                          "project-plans", "skills", "supporting-artifacts", "audit"):
                    self.assertTrue((collab / d).is_dir(), d)
                yaml = (collab / "project.yaml").read_text()
                self.assertIn(f"governance_mode: {mode}", yaml)
                self.assertIn(f"project: gov-{mode}", yaml)

    def test_platforms(self) -> None:
        marker = {"github": ".github", "gitlab": ".gitlab", "azure-devops": ".azuredevops"}
        for plat in PLATFORMS:
            with self.subTest(platform=plat):
                root = new_project(self.tmp, f"plat-{plat}", "--platform", plat)
                self.assertIn(f"platform: {plat}", (root / ".collab/project.yaml").read_text())
                if plat in marker:
                    self.assertTrue(any(root.glob(marker[plat] + "*")), plat)

    def test_license(self) -> None:
        root = new_project(self.tmp, "lic", "--license", "mit")
        self.assertIn("MIT License", (root / "LICENSE").read_text())
        root = new_project(self.tmp, "nolic", "--license", "none")
        self.assertFalse((root / "LICENSE").exists())

    def test_ticket_prefix(self) -> None:
        root = new_project(self.tmp, "pfx", "--ticket-prefix", "scaf")
        self.assertIn("ticket_prefix: SCAF", (root / ".collab/project.yaml").read_text())
        root = new_project(self.tmp, "badpfx", "--ticket-prefix", "x!")
        self.assertIn("ticket_prefix: TASK", (root / ".collab/project.yaml").read_text())

    def test_description_saved_to_project_yaml(self) -> None:
        root = new_project(self.tmp, "desc", "--description", "Billing API:  v2\nrewrite")
        meta = scaffy_mod._parse_project_yaml(root / ".collab/project.yaml")
        self.assertEqual(meta["description"], "Billing API: v2 rewrite")
        root = new_project(self.tmp, "nodesc")
        meta = scaffy_mod._parse_project_yaml(root / ".collab/project.yaml")
        self.assertEqual(meta["description"], "")

    def test_upgrade_restores_context_with_saved_description(self) -> None:
        root = new_project(self.tmp, "desc", "--description", "Billing API")
        (root / ".collab/context.md").unlink()
        scaffy("--upgrade", "--path", str(root))
        self.assertIn("Billing API", (root / ".collab/context.md").read_text())

    def test_dry_run_writes_nothing(self) -> None:
        scaffy("--name", "dry", "--path", str(self.tmp), "--dry-run")
        self.assertFalse((self.tmp / "dry").exists())

    def test_rerun_without_force_keeps_user_edits(self) -> None:
        root = new_project(self.tmp)
        kanban = root / ".collab/kanban-board.md"
        kanban.write_text(kanban.read_text() + "\n- [ ] TASK-001: keep me\n")
        (root / "src.py").write_text("print('user code')\n")
        before = snapshot(root)
        scaffy("--name", "demo", "--path", str(self.tmp))
        after = snapshot(root)
        for rel, data in before.items():
            self.assertEqual(data, after[rel], rel)

    def test_invalid_name_rejected(self) -> None:
        proc = scaffy("--name", "bad/name", "--path", str(self.tmp), check=False)
        self.assertNotEqual(proc.returncode, 0)


class TestUpgrade(TempDirCase):
    def test_upgrade_is_idempotent(self) -> None:
        root = new_project(self.tmp)
        scaffy("--upgrade", "--path", str(root))
        first = snapshot(root)
        out = scaffy("--upgrade", "--path", str(root)).stdout
        self.assertEqual(first, snapshot(root))
        self.assertNotIn("add    ", out)

    def test_upgrade_restores_missing_file_and_dir(self) -> None:
        root = new_project(self.tmp)
        (root / ".collab/guides/git-guidelines.md").unlink()
        (root / ".collab/skills").rmdir()
        scaffy("--upgrade", "--path", str(root))
        self.assertTrue((root / ".collab/guides/git-guidelines.md").is_file())
        self.assertTrue((root / ".collab/skills").is_dir())

    def test_upgrade_without_force_keeps_edits(self) -> None:
        root = new_project(self.tmp)
        contract = root / ".collab/collab-contract.md"
        contract.write_text("custom contract\n")
        scaffy("--upgrade", "--path", str(root))
        self.assertEqual(contract.read_text(), "custom contract\n")

    def test_force_upgrade_never_touches_user_owned_files(self) -> None:
        root = new_project(self.tmp, "demo", "--license", "mit")
        collab = root / ".collab"
        edits = {
            collab / "kanban-board.md": "- [ ] TASK-001: MY REAL TASK\n",
            collab / "context.md": "# real context\n",
            collab / "project.yaml": (collab / "project.yaml").read_text() + "agents:\n  - claude\n",
            root / "LICENSE": "Copyright 2026 Me\n",
        }
        for path, text in edits.items():
            path.write_text(text)
        out = scaffy("--upgrade", "--path", str(root), "--force").stdout
        for path, text in edits.items():
            self.assertEqual(path.read_text(), text, path.name)
        self.assertIn("keep   .collab/kanban-board.md", out)

    def test_force_upgrade_backs_up_replaced_files(self) -> None:
        root = new_project(self.tmp)
        contract = root / ".collab/collab-contract.md"
        original = contract.read_text()
        contract.write_text("custom contract\n")
        scaffy("--upgrade", "--path", str(root), "--force")
        self.assertEqual(contract.read_text(), original)
        backups = list((root / ".collab/.upgrade-backups").rglob("collab-contract.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "custom contract\n")

    def test_force_upgrade_skips_current_files_without_backup(self) -> None:
        root = new_project(self.tmp)
        scaffy("--upgrade", "--path", str(root), "--force")
        self.assertFalse((root / ".collab/.upgrade-backups").exists())

    def test_force_upgrade_dry_run_writes_nothing(self) -> None:
        root = new_project(self.tmp)
        (root / ".collab/collab-contract.md").write_text("custom\n")
        before = snapshot(root)
        out = scaffy("--upgrade", "--path", str(root), "--force", "--dry-run").stdout
        self.assertEqual(before, snapshot(root))
        self.assertIn("update .collab/collab-contract.md", out)

    def test_upgrade_without_collab_fails(self) -> None:
        proc = scaffy("--upgrade", "--path", str(self.tmp), check=False)
        self.assertNotEqual(proc.returncode, 0)

    def test_upgrade_without_project_yaml_fails(self) -> None:
        (self.tmp / ".collab").mkdir()
        proc = scaffy("--upgrade", "--path", str(self.tmp), check=False)
        self.assertNotEqual(proc.returncode, 0)

    def test_upgrade_dry_run_writes_nothing(self) -> None:
        root = new_project(self.tmp)
        (root / ".collab/guides/git-guidelines.md").unlink()
        before = snapshot(root)
        scaffy("--upgrade", "--path", str(root), "--dry-run")
        self.assertEqual(before, snapshot(root))

    def test_upgrade_migrates_ideas_dir(self) -> None:
        root = new_project(self.tmp)
        collab = root / ".collab"
        (collab / "brainstorms/brainstorm-template.md").unlink()
        (collab / "brainstorms").rmdir()
        (collab / "ideas").mkdir()
        (collab / "ideas/my-idea.md").write_text("idea\n")
        scaffy("--upgrade", "--path", str(root))
        self.assertEqual((collab / "brainstorms/my-idea.md").read_text(), "idea\n")


class TestProjectYamlParser(TempDirCase):
    def parse(self, text: str) -> dict:
        p = self.tmp / "project.yaml"
        p.write_text(text)
        return scaffy_mod._parse_project_yaml(p)

    def test_valid(self) -> None:
        meta = self.parse("project: x\ngovernance_mode: strict\n# comment\n\n")
        self.assertEqual(meta["project"], "x")
        self.assertEqual(meta["governance_mode"], "strict")

    def test_malformed_lines_ignored(self) -> None:
        meta = self.parse("garbage line\nproject: x\n  - list item\n")
        self.assertEqual(meta.get("project"), "x")


class TestChatRendering(unittest.TestCase):
    def test_claude_session_markdown(self) -> None:
        entries = [
            {"type": "user", "timestamp": "2026-11-04T15:00:00Z",
             "message": {"content": "hello there"}},
            {"type": "assistant", "timestamp": "2026-11-04T15:00:05Z",
             "message": {"content": [
                 {"type": "thinking", "thinking": "secret"},
                 {"type": "text", "text": "hi back"},
                 {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
             ]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "abcdef123456", "content": "file.txt"}]}},
            {"type": "summary", "summary": "ignored"},
        ]
        md = scaffy_mod._session_to_markdown(entries, "sess-1")
        self.assertIn("**Session:** `sess-1`", md)
        self.assertIn("hello there", md)
        self.assertIn("hi back", md)
        self.assertIn("`Bash`", md)
        self.assertIn("file.txt", md)
        self.assertNotIn("secret", md)

    def test_load_jsonl_skips_bad_lines(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            p.write_text('{"type": "user"}\nnot json\n\n{"type": "assistant"}\n')
            self.assertEqual(len(scaffy_mod._load_jsonl(p)), 2)

    def test_gemini_session_markdown(self) -> None:
        events = [
            {"sessionId": "g-1", "projectHash": "h", "startTime": "t0"},
            {"type": "user", "content": [{"text": "question"}]},
            {"type": "gemini", "content": "answer",
             "toolCalls": [{"name": "read_file", "args": {"path": "a"}}]},
        ]
        md = scaffy_mod._gemini_session_to_markdown(events, "src.jsonl")
        for s in ("`g-1`", "question", "answer", "read_file"):
            self.assertIn(s, md)


if __name__ == "__main__":
    unittest.main()
