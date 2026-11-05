"""Regression tests for scafrag.py (index/query/context/status/projects)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import new_project, scafrag


class ScafragCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.root = self.tmp / "code"
        self.root.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def rag(self, *args: str, check: bool = True):
        return scafrag(*args, home=self.home, check=check)

    def rag_json(self, *args: str):
        return json.loads(self.rag(*args, "--format", "json").stdout)["data"]

    def add_summary(self, root: Path, name: str, text: str) -> None:
        (root / ".collab/session-summaries" / name).write_text(text)


class TestScafrag(ScafragCase):
    def test_index_and_projects(self) -> None:
        new_project(self.root, "alpha")
        new_project(self.root, "beta")
        out = self.rag("index", "--root", str(self.root))
        self.assertIn("2 project", out.stderr + out.stdout)
        self.assertTrue((self.home / ".scafrag/index.json").is_file())
        names = sorted(p["project"] for p in self.rag_json("projects"))
        self.assertEqual(names, ["alpha", "beta"])

    def test_query_ranks_matching_project(self) -> None:
        a = new_project(self.root, "alpha")
        new_project(self.root, "beta")
        self.add_summary(a, "11.01.2026-claude-summary.md", "Decided on kubernetes ingress.\n")
        self.rag("index", "--root", str(self.root))
        results = self.rag_json("query", "kubernetes ingress")
        self.assertEqual(results[0]["project"], "alpha")
        self.assertEqual(len(results), 1)

    def test_session_template_not_indexed(self) -> None:
        new_project(self.root, "alpha")
        self.rag("index", "--root", str(self.root))
        ctx = self.rag_json("context", "alpha")
        self.assertNotIn("session-summaries", ctx["content"])

    def test_context_partial_and_missing(self) -> None:
        new_project(self.root, "alpha-service")
        self.rag("index", "--root", str(self.root))
        self.assertEqual(self.rag_json("context", "alpha")["project"], "alpha-service")
        self.assertNotEqual(self.rag("context", "nope", check=False).returncode, 0)

    def test_status_counts_kanban(self) -> None:
        a = new_project(self.root, "alpha")
        kanban = a / ".collab/kanban-board.md"
        kanban.write_text(kanban.read_text().replace(
            "## Blocked", "## Blocked\n- [ ] TASK-009: stuck\n"))
        self.rag("index", "--root", str(self.root))
        row = self.rag_json("status")[0]
        self.assertEqual(row["blocked"], 1)

    def test_no_index(self) -> None:
        self.assertNotEqual(self.rag("projects", check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
