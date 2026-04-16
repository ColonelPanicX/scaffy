#!/usr/bin/env python3
"""
scafrag — cross-project RAG-lite query companion for scaffy workspaces.

Discovers .collab/ workspaces under a root directory, indexes their content,
and provides CLI search, context dumps, and portfolio status views.

Usage:
  python3 scafrag.py index [--root PATH]
  python3 scafrag.py query QUERY [--top N] [--format text|json|markdown]
  python3 scafrag.py context PROJECT [--format text|json|markdown]
  python3 scafrag.py status [--format text|json|markdown]
  python3 scafrag.py projects [--format text|json|markdown]

Requires Python 3.9+. Zero external dependencies.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Version guard
# ---------------------------------------------------------------------------

MIN_PYTHON = (3, 9)
if sys.version_info < MIN_PYTHON:
    sys.exit(f"scafrag requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INDEX_PATH = Path.home() / ".scafrag" / "index.json"
INDEX_VERSION = 1
BM25_K1 = 1.5
BM25_B = 0.75

# ---------------------------------------------------------------------------
# Minimal YAML parser
# Handles only flat key: value pairs as written by scaffy's project.yaml.
# ---------------------------------------------------------------------------


def _parse_project_yaml(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            result[key.strip()] = val.strip().strip('"').strip("'")
    return result


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    """Lowercase and split on non-alphanumeric characters, drop single chars."""
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) > 1]


# ---------------------------------------------------------------------------
# BM25 scoring
# ---------------------------------------------------------------------------


def _bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    corpus: list[list[str]],
) -> float:
    """Score one document against query using BM25."""
    n = len(corpus)
    avg_dl = sum(len(d) for d in corpus) / max(n, 1)
    dl = len(doc_tokens)

    tf_map: dict[str, int] = {}
    for t in doc_tokens:
        tf_map[t] = tf_map.get(t, 0) + 1

    doc_set = set(doc_tokens)
    score = 0.0
    for term in set(query_tokens):
        tf = tf_map.get(term, 0)
        if tf == 0:
            continue
        df = sum(1 for d in corpus if term in set(d))
        idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
        tf_norm = (tf * (BM25_K1 + 1)) / (
            tf + BM25_K1 * (1 - BM25_B + BM25_B * dl / max(avg_dl, 1))
        )
        score += idf * tf_norm

    return score


# ---------------------------------------------------------------------------
# Snippet extraction
# ---------------------------------------------------------------------------


def _extract_snippet(text: str, query_tokens: list[str], chunk_size: int = 40) -> str:
    """Return the passage in text with the highest query token density."""
    words = text.split()
    if not words:
        return ""

    best_i = 0
    best_hits = -1

    for i in range(len(words)):
        chunk = " ".join(words[i : i + chunk_size]).lower()
        hits = sum(1 for t in query_tokens if t in chunk)
        if hits > best_hits:
            best_hits = hits
            best_i = i

    pad = 5
    start_i = max(0, best_i - pad)
    end_i = min(len(words), best_i + chunk_size + pad)
    snippet = re.sub(r"\s+", " ", " ".join(words[start_i:end_i])).strip()

    prefix = "…" if start_i > 0 else ""
    suffix = "…" if end_i < len(words) else ""
    return prefix + snippet + suffix


# ---------------------------------------------------------------------------
# Kanban lane parser
# ---------------------------------------------------------------------------


def _parse_kanban_lanes(text: str) -> dict[str, int]:
    """Count tasks per lane in a kanban-board.md file."""
    lane_map = {
        "backlog": "backlog",
        "sprint backlog": "todo",
        "to do": "todo",
        "in progress": "in_progress",
        "blocked": "blocked",
        "in review": "in_review",
        "done": "done",
    }
    lanes: dict[str, int] = {k: 0 for k in lane_map.values()}

    current_lane: str | None = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)(?:\s*\(.*\))?$", line)
        if m:
            heading = m.group(1).strip().lower()
            current_lane = lane_map.get(heading)
            continue
        if current_lane and re.match(r"^\s*-\s+\[[ x]\]", line):
            lanes[current_lane] = lanes[current_lane] + 1

    return lanes


# ---------------------------------------------------------------------------
# Content collection per project
# ---------------------------------------------------------------------------


def _collect_content(collab_path: Path) -> dict[str, str]:
    """Read and return text content from key .collab/ files."""
    content: dict[str, str] = {}

    for fname in ("context.md", "kanban-board.md"):
        fpath = collab_path / fname
        if fpath.exists():
            content[fname] = fpath.read_text(encoding="utf-8", errors="replace")

    # Agent profile — check prompts/ first (v1.5+), fall back to root
    for profile_path in (
        collab_path / "prompts" / "agent-profile.md",
        collab_path / "agent-profile.md",
    ):
        if profile_path.exists():
            content["agent-profile.md"] = profile_path.read_text(
                encoding="utf-8", errors="replace"
            )
            break

    # Session summaries — concatenate all (skip template)
    sessions_dir = collab_path / "session-summaries"
    if sessions_dir.exists():
        texts = [
            f.read_text(encoding="utf-8", errors="replace")
            for f in sorted(sessions_dir.glob("*.md"))
            if f.name != "session-summary-template.md"
        ]
        if texts:
            content["session-summaries"] = "\n\n---\n\n".join(texts)

    return content


# ---------------------------------------------------------------------------
# Index build
# ---------------------------------------------------------------------------


def _build_index(root: Path) -> dict[str, Any]:
    projects: dict[str, Any] = {}

    for yaml_path in sorted(root.rglob(".collab/project.yaml")):
        collab_path = yaml_path.parent
        project_root = collab_path.parent
        try:
            meta = _parse_project_yaml(
                yaml_path.read_text(encoding="utf-8", errors="replace")
            )
        except OSError:
            continue

        name = meta.get("name") or project_root.name
        content = _collect_content(collab_path)
        kanban_lanes = _parse_kanban_lanes(content.get("kanban-board.md", ""))
        combined = "\n\n".join(content.values())

        projects[name] = {
            "name": name,
            "path": str(project_root),
            "description": meta.get("description", ""),
            "governance": meta.get("governance", ""),
            "created": meta.get("date", ""),
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "content": content,
            "combined_text": combined,
            "kanban_lanes": kanban_lanes,
        }

    return {
        "version": INDEX_VERSION,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "projects": projects,
    }


def _save_index(index: dict[str, Any]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")


def _load_index() -> dict[str, Any]:
    if not INDEX_PATH.exists():
        sys.exit("No index found. Run:  scafrag index --root PATH")
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_index(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"Not a directory: {root}")

    print(f"Scanning {root} …", file=sys.stderr)
    index = _build_index(root)
    count = len(index["projects"])
    _save_index(index)
    print(f"Indexed {count} project(s) → {INDEX_PATH}", file=sys.stderr)
    for name in sorted(index["projects"]):
        print(f"  • {name}", file=sys.stderr)


def cmd_query(args: argparse.Namespace) -> None:
    index = _load_index()
    projects = index["projects"]

    query_tokens = _tokenize(args.query)
    if not query_tokens:
        sys.exit("Query is empty after tokenization.")

    corpus = [
        (name, _tokenize(p["combined_text"])) for name, p in projects.items()
    ]
    corpus_lists = [tokens for _, tokens in corpus]

    results = []
    for name, doc_tokens in corpus:
        score = _bm25_score(query_tokens, doc_tokens, corpus_lists)
        if score > 0:
            p = projects[name]
            results.append(
                {
                    "project": name,
                    "path": p["path"],
                    "score": round(score, 4),
                    "description": p["description"],
                    "snippet": _extract_snippet(p["combined_text"], query_tokens),
                }
            )

    results.sort(key=lambda r: r["score"], reverse=True)
    results = results[: args.top]

    _output(results, args.format, "query", query=args.query)


def cmd_context(args: argparse.Namespace) -> None:
    index = _load_index()
    projects = index["projects"]

    name = args.project
    if name not in projects:
        matches = [k for k in projects if name.lower() in k.lower()]
        if not matches:
            sys.exit(
                f"Project '{name}' not found. "
                "Run 'scafrag projects' to see available projects."
            )
        if len(matches) > 1:
            sys.exit(
                f"Ambiguous name '{name}'. Matches: {', '.join(sorted(matches))}"
            )
        name = matches[0]

    p = projects[name]
    _output(
        {
            "project": name,
            "path": p["path"],
            "description": p["description"],
            "governance": p["governance"],
            "created": p["created"],
            "indexed_at": p["indexed_at"],
            "kanban_lanes": p["kanban_lanes"],
            "content": p["content"],
        },
        args.format,
        "context",
    )


def cmd_status(args: argparse.Namespace) -> None:
    index = _load_index()
    rows = [
        {
            "project": name,
            "path": p["path"],
            "description": p["description"],
            **{k: p["kanban_lanes"].get(k, 0) for k in
               ("backlog", "todo", "in_progress", "blocked", "in_review", "done")},
        }
        for name, p in sorted(index["projects"].items())
    ]
    _output(rows, args.format, "status", built_at=index.get("built_at", ""))


def cmd_projects(args: argparse.Namespace) -> None:
    index = _load_index()
    rows = [
        {
            "project": name,
            "path": p["path"],
            "description": p["description"],
            "governance": p["governance"],
            "created": p["created"],
            "indexed_at": p["indexed_at"],
        }
        for name, p in sorted(index["projects"].items())
    ]
    _output(rows, args.format, "projects", built_at=index.get("built_at", ""))


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _output(data: Any, fmt: str, cmd: str, **meta: Any) -> None:
    if fmt == "json":
        print(json.dumps({"command": cmd, "meta": meta, "data": data}, indent=2))
    elif fmt == "markdown":
        _render_markdown(data, cmd, meta)
    else:
        _render_text(data, cmd, meta)


def _render_text(data: Any, cmd: str, meta: dict[str, Any]) -> None:  # noqa: C901
    if cmd == "query":
        print(f'Results for: "{meta.get("query", "")}"\n')
        if not data:
            print("  No results found.")
            return
        for i, r in enumerate(data, 1):
            print(f"  {i}. {r['project']}  (score: {r['score']})")
            print(f"     {r['path']}")
            if r["description"]:
                print(f"     {r['description']}")
            print(f"     {r['snippet']}")
            print()

    elif cmd == "context":
        lanes = data["kanban_lanes"]
        print(f"=== {data['project']} ===")
        print(f"Path:        {data['path']}")
        print(f"Description: {data['description']}")
        print(f"Governance:  {data['governance']}")
        print(f"Created:     {data['created']}")
        print(
            f"Kanban:      Backlog:{lanes.get('backlog', 0)}  "
            f"Todo:{lanes.get('todo', 0)}  "
            f"WIP:{lanes.get('in_progress', 0)}  "
            f"Blocked:{lanes.get('blocked', 0)}  "
            f"Done:{lanes.get('done', 0)}"
        )
        for fname, text in data["content"].items():
            print(f"\n--- {fname} ---\n")
            print(text[:2000])
            if len(text) > 2000:
                print(f"\n[… {len(text) - 2000} more chars — use --format json for full content]")

    elif cmd == "status":
        built = meta.get("built_at", "")
        if built:
            print(f"Portfolio Status  (index: {built[:19].replace('T', ' ')} UTC)\n")
        hdr = f"{'PROJECT':<26} {'BKL':>4} {'TODO':>4} {'WIP':>4} {'BLK':>4} {'REV':>4} {'DONE':>4}  DESCRIPTION"
        print(hdr)
        print("-" * len(hdr))
        for r in data:
            desc = (r["description"] or "")[:40]
            print(
                f"{r['project']:<26} "
                f"{r['backlog']:>4} {r['todo']:>4} {r['in_progress']:>4} "
                f"{r['blocked']:>4} {r['in_review']:>4} {r['done']:>4}  {desc}"
            )

    elif cmd == "projects":
        built = meta.get("built_at", "")
        if built:
            print(f"Indexed projects  (index: {built[:19].replace('T', ' ')} UTC)\n")
        for r in data:
            print(f"  {r['project']}")
            print(f"    Path:        {r['path']}")
            if r["description"]:
                print(f"    Description: {r['description']}")
            if r["governance"]:
                print(f"    Governance:  {r['governance']}")
            print(f"    Indexed:     {r['indexed_at'][:19].replace('T', ' ')} UTC")
            print()


def _render_markdown(data: Any, cmd: str, meta: dict[str, Any]) -> None:
    if cmd == "query":
        print(f"## Search: `{meta.get('query', '')}`\n")
        if not data:
            print("_No results found._")
            return
        for i, r in enumerate(data, 1):
            print(f"### {i}. {r['project']}  _(score: {r['score']})_")
            print(f"- **Path:** `{r['path']}`")
            if r["description"]:
                print(f"- **Description:** {r['description']}")
            print(f"\n> {r['snippet']}\n")

    elif cmd == "context":
        lanes = data["kanban_lanes"]
        print(f"# {data['project']}\n")
        print("| Field | Value |")
        print("|---|---|")
        print(f"| Path | `{data['path']}` |")
        print(f"| Description | {data['description']} |")
        print(f"| Governance | {data['governance']} |")
        print(f"| Created | {data['created']} |")
        print(
            f"| Kanban | "
            f"Backlog: {lanes.get('backlog', 0)} / "
            f"Todo: {lanes.get('todo', 0)} / "
            f"WIP: {lanes.get('in_progress', 0)} / "
            f"Blocked: {lanes.get('blocked', 0)} / "
            f"Done: {lanes.get('done', 0)} |"
        )
        print()
        for fname, text in data["content"].items():
            print(f"## {fname}\n\n```\n{text[:1500]}\n```\n")

    elif cmd == "status":
        built = meta.get("built_at", "")
        print("## Portfolio Status\n")
        if built:
            print(f"_Index: {built[:19].replace('T', ' ')} UTC_\n")
        print("| Project | Backlog | Todo | WIP | Blocked | Review | Done | Description |")
        print("|---|---|---|---|---|---|---|---|")
        for r in data:
            desc = (r["description"] or "")[:40]
            print(
                f"| {r['project']} | {r['backlog']} | {r['todo']} | "
                f"{r['in_progress']} | {r['blocked']} | {r['in_review']} | "
                f"{r['done']} | {desc} |"
            )

    elif cmd == "projects":
        built = meta.get("built_at", "")
        print("## Indexed Projects\n")
        if built:
            print(f"_Index: {built[:19].replace('T', ' ')} UTC_\n")
        print("| Project | Path | Governance | Indexed |")
        print("|---|---|---|---|")
        for r in data:
            print(
                f"| {r['project']} | `{r['path']}` | {r['governance']} | "
                f"{r['indexed_at'][:10]} |"
            )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scafrag",
        description="Cross-project RAG-lite query companion for scaffy workspaces.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  scafrag index --root ~/code\n"
            "  scafrag query 'authentication middleware'\n"
            "  scafrag context compligator\n"
            "  scafrag status --format markdown\n"
            "  scafrag projects --format json\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # index
    p_idx = sub.add_parser("index", help="Scan for .collab/ workspaces and build index.")
    p_idx.add_argument(
        "--root",
        default=".",
        metavar="PATH",
        help="Root directory to scan (default: current directory)",
    )

    # query
    p_qry = sub.add_parser("query", help="Search across all indexed projects.")
    p_qry.add_argument("query", help="Search query string")
    p_qry.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Number of results to return (default: 5)",
    )
    p_qry.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
    )

    # context
    p_ctx = sub.add_parser("context", help="Full context dump for one project.")
    p_ctx.add_argument("project", help="Project name (partial match supported)")
    p_ctx.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
    )

    # status
    p_sts = sub.add_parser(
        "status", help="Portfolio view — all projects with kanban lane counts."
    )
    p_sts.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
    )

    # projects
    p_prj = sub.add_parser("projects", help="List all indexed projects.")
    p_prj.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
    )

    args = parser.parse_args()

    dispatch = {
        "index": cmd_index,
        "query": cmd_query,
        "context": cmd_context,
        "status": cmd_status,
        "projects": cmd_projects,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
