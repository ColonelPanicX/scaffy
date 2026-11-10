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
                          "project-plans", "skills", "inbox", "audit"):
                    self.assertTrue((collab / d).is_dir(), d)
                yaml = (collab / "project.yaml").read_text(encoding="utf-8")
                self.assertIn(f"governance_mode: {mode}", yaml)
                self.assertIn(f"project: gov-{mode}", yaml)

    def test_platforms(self) -> None:
        marker = {"github": ".github", "gitlab": ".gitlab", "azure-devops": ".azuredevops"}
        for plat in PLATFORMS:
            with self.subTest(platform=plat):
                root = new_project(self.tmp, f"plat-{plat}", "--platform", plat)
                self.assertIn(f"platform: {plat}", (root / ".collab/project.yaml").read_text(encoding="utf-8"))
                if plat in marker:
                    self.assertTrue(any(root.glob(marker[plat] + "*")), plat)

    def test_license(self) -> None:
        root = new_project(self.tmp, "lic", "--license", "mit")
        self.assertIn("MIT License", (root / "LICENSE").read_text(encoding="utf-8"))
        root = new_project(self.tmp, "nolic", "--license", "none")
        self.assertFalse((root / "LICENSE").exists())

    def test_ticket_prefix(self) -> None:
        root = new_project(self.tmp, "pfx", "--ticket-prefix", "scaf")
        self.assertIn("ticket_prefix: SCAF", (root / ".collab/project.yaml").read_text(encoding="utf-8"))
        root = new_project(self.tmp, "badpfx", "--ticket-prefix", "x!")
        self.assertIn("ticket_prefix: TASK", (root / ".collab/project.yaml").read_text(encoding="utf-8"))

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
        self.assertIn("Billing API", (root / ".collab/context.md").read_text(encoding="utf-8"))

    def test_north_star_draft_shipped(self) -> None:
        root = new_project(self.tmp, "ns")
        ns = (root / ".collab/north-star.md").read_text(encoding="utf-8")
        self.assertIn("# North Star — ns", ns)
        self.assertIn("_Status: draft_", ns)
        for heading in ("## Problem", "## Non-Goals", "## Off-Course Signals", "## Revision Log"):
            self.assertIn(heading, ns)
        self.assertNotIn("{", ns)
        contract = (root / ".collab/collab-contract.md").read_text(encoding="utf-8")
        self.assertIn("## North Star", contract)
        self.assertIn("north-star.md", (root / ".collab/prompts/initial-prompt.md").read_text(encoding="utf-8"))

    def test_brainstorm_session_template_shipped(self) -> None:
        root = new_project(self.tmp, "bs")
        tpl = (root / ".collab/brainstorms/brainstorm-session-template.md").read_text(encoding="utf-8")
        self.assertIn("_Status: in-session_", tpl)
        for heading in ("## Framing", "## Ideas", "## Clusters", "## Evaluation",
                        "## Shortlist", "## Parked / Rejected", "## Proposed Next Steps"):
            self.assertIn(heading, tpl)
        self.assertNotIn("{", tpl)
        self.assertIn("### Brainstorm Sessions", (root / ".collab/collab-contract.md").read_text(encoding="utf-8"))

    def test_open_session_sort_rule_is_date_aware(self) -> None:
        root = new_project(self.tmp, "sortrule")
        contract = (root / ".collab/collab-contract.md").read_text(encoding="utf-8")
        self.assertIn("don't sort them alphabetically", contract)
        self.assertIn("Order by year, then month, then day", contract)
        self.assertNotIn("sort by filename date", contract)
        for skill in Path(__file__).resolve().parent.parent.glob("skills/*/scaffy/SKILL.md"):
            text = skill.read_text(encoding="utf-8")
            self.assertIn("Order by year, then month, then day", text, skill)
            self.assertNotIn("sort by filename date", text, skill)

    def test_agent_bridge_dir_and_playbook_shipped(self) -> None:
        root = new_project(self.tmp, "ab")
        bridge_dir = root / ".collab/agent-bridge"
        self.assertTrue(bridge_dir.is_dir())
        self.assertEqual(list(bridge_dir.iterdir()), [])
        pb = (root / ".collab/playbooks/agent-bridge-playbook.md").read_text(encoding="utf-8")
        for heading in ("## 1. When to Use a Bridge", "## 4. File Formats", "## 7. Closing a Bridge"):
            self.assertIn(heading, pb)
        self.assertNotIn("{", pb)
        self.assertIn("## Agent Bridges", (root / ".collab/collab-contract.md").read_text(encoding="utf-8"))
        self.assertIn("agent-bridge/", (root / ".collab/readme.md").read_text(encoding="utf-8"))
        for skill in Path(__file__).resolve().parent.parent.glob("skills/*/scaffy/SKILL.md"):
            text = skill.read_text(encoding="utf-8")
            self.assertIn("## Agent Bridge Protocol", text, skill)
            self.assertIn("`bridge open <name>`", text, skill)

    def test_dry_run_writes_nothing(self) -> None:
        scaffy("--name", "dry", "--path", str(self.tmp), "--dry-run")
        self.assertFalse((self.tmp / "dry").exists())

    def test_rerun_without_force_keeps_user_edits(self) -> None:
        root = new_project(self.tmp)
        kanban = root / ".collab/kanban-board.md"
        kanban.write_text(kanban.read_text(encoding="utf-8") + "\n- [ ] TASK-001: keep me\n")
        (root / "src.py").write_text("print('user code')\n", encoding="utf-8")
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
        contract.write_text("custom contract\n", encoding="utf-8")
        scaffy("--upgrade", "--path", str(root))
        self.assertEqual(contract.read_text(encoding="utf-8"), "custom contract\n")

    def test_force_upgrade_never_touches_user_owned_files(self) -> None:
        root = new_project(self.tmp, "demo", "--license", "mit")
        collab = root / ".collab"
        edits = {
            collab / "kanban-board.md": "- [ ] TASK-001: MY REAL TASK\n",
            collab / "context.md": "# real context\n",
            collab / "project.yaml": (collab / "project.yaml").read_text(encoding="utf-8") + "agents:\n  - claude\n",
            root / "LICENSE": "Copyright 2026 Me\n",
        }
        for path, text in edits.items():
            path.write_text(text, encoding="utf-8")
        out = scaffy("--upgrade", "--path", str(root), "--force").stdout
        for path, text in edits.items():
            self.assertEqual(path.read_text(encoding="utf-8"), text, path.name)
        self.assertIn("keep   .collab/kanban-board.md", out)

    def test_upgrade_adds_north_star_and_protects_it(self) -> None:
        root = new_project(self.tmp)
        ns = root / ".collab/north-star.md"
        ns.unlink()
        scaffy("--upgrade", "--path", str(root))
        self.assertIn("_Status: draft_", ns.read_text(encoding="utf-8"))
        ns.write_text("# North Star\n_Status: agreed_\n", encoding="utf-8")
        scaffy("--upgrade", "--path", str(root), "--force")
        self.assertEqual(ns.read_text(encoding="utf-8"), "# North Star\n_Status: agreed_\n")

    def test_upgrade_adds_agent_bridge_and_keeps_bridges(self) -> None:
        root = new_project(self.tmp)
        bridge_dir = root / ".collab/agent-bridge"
        pb = root / ".collab/playbooks/agent-bridge-playbook.md"
        bridge_dir.rmdir()
        pb.unlink()
        scaffy("--upgrade", "--path", str(root))
        self.assertTrue(bridge_dir.is_dir())
        self.assertTrue(pb.is_file())
        room = bridge_dir / "login-timeout"
        room.mkdir()
        (room / "transcript.md").write_text("## from=dev ts=2026-11-09T12:00:00Z\nhi\n", encoding="utf-8")
        scaffy("--upgrade", "--path", str(root), "--force")
        self.assertEqual(sorted(p.name for p in bridge_dir.iterdir()), ["login-timeout"])
        self.assertIn("hi", (room / "transcript.md").read_text(encoding="utf-8"))

    def test_upgrade_moves_supporting_artifacts_to_inbox(self) -> None:
        root = new_project(self.tmp)
        collab = root / ".collab"
        (collab / "inbox").rmdir()
        old = collab / "supporting-artifacts"
        (old / "diagrams").mkdir(parents=True)
        (old / "diagrams/flow.md").write_text("flow\n", encoding="utf-8")
        scaffy("--upgrade", "--path", str(root))
        self.assertFalse(old.exists())
        self.assertEqual((collab / "inbox/diagrams/flow.md").read_text(encoding="utf-8"), "flow\n")

    def test_upgrade_merges_into_existing_inbox_without_clobbering(self) -> None:
        root = new_project(self.tmp)
        collab = root / ".collab"
        old = collab / "supporting-artifacts"
        old.mkdir()
        (old / "spec.md").write_text("old spec\n", encoding="utf-8")
        (old / "notes.md").write_text("notes\n", encoding="utf-8")
        (collab / "inbox/spec.md").write_text("inbox spec\n", encoding="utf-8")
        out = scaffy("--upgrade", "--path", str(root)).stdout
        self.assertEqual((collab / "inbox/notes.md").read_text(encoding="utf-8"), "notes\n")
        self.assertEqual((collab / "inbox/spec.md").read_text(encoding="utf-8"), "inbox spec\n")
        self.assertEqual((old / "spec.md").read_text(encoding="utf-8"), "old spec\n")
        self.assertIn("move it by hand", out)

    def test_upgrade_migration_dry_run_moves_nothing(self) -> None:
        root = new_project(self.tmp)
        collab = root / ".collab"
        (collab / "inbox").rmdir()
        (collab / "supporting-artifacts").mkdir()
        (collab / "supporting-artifacts/a.md").write_text("a\n", encoding="utf-8")
        before = snapshot(root)
        scaffy("--upgrade", "--path", str(root), "--dry-run")
        self.assertEqual(snapshot(root), before)

    def test_force_upgrade_backs_up_replaced_files(self) -> None:
        root = new_project(self.tmp)
        contract = root / ".collab/collab-contract.md"
        original = contract.read_text(encoding="utf-8")
        contract.write_text("custom contract\n", encoding="utf-8")
        scaffy("--upgrade", "--path", str(root), "--force")
        self.assertEqual(contract.read_text(encoding="utf-8"), original)
        backups = list((root / ".collab/.upgrade-backups").rglob("collab-contract.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "custom contract\n")

    def test_force_upgrade_skips_current_files_without_backup(self) -> None:
        root = new_project(self.tmp)
        scaffy("--upgrade", "--path", str(root), "--force")
        self.assertFalse((root / ".collab/.upgrade-backups").exists())

    def test_force_upgrade_dry_run_writes_nothing(self) -> None:
        root = new_project(self.tmp)
        (root / ".collab/collab-contract.md").write_text("custom\n", encoding="utf-8")
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
        for f in (collab / "brainstorms").iterdir():
            f.unlink()
        (collab / "brainstorms").rmdir()
        (collab / "ideas").mkdir()
        (collab / "ideas/my-idea.md").write_text("idea\n", encoding="utf-8")
        scaffy("--upgrade", "--path", str(root))
        self.assertEqual((collab / "brainstorms/my-idea.md").read_text(encoding="utf-8"), "idea\n")


class TestProjectYamlParser(TempDirCase):
    def parse(self, text: str) -> dict:
        p = self.tmp / "project.yaml"
        p.write_text(text, encoding="utf-8")
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
            p.write_text('{"type": "user"}\nnot json\n\n{"type": "assistant"}\n', encoding="utf-8")
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
