"""Shared helpers: run scaffy/scafrag as real CLI subprocesses inside temp dirs."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCAFFY = REPO / "scaffy.py"
SCAFRAG = REPO / "scafrag.py"


def run(script: Path, *args: str, home: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if home is not None:
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL,
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"{script.name} {' '.join(args)} exited {proc.returncode}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def scaffy(*args: str, **kw) -> subprocess.CompletedProcess:
    return run(SCAFFY, *args, **kw)


def scafrag(*args: str, **kw) -> subprocess.CompletedProcess:
    return run(SCAFRAG, *args, **kw)


def new_project(parent: Path, name: str = "demo", *extra: str) -> Path:
    """Scaffold a fresh project under parent/name and return its root."""
    scaffy("--name", name, "--path", str(parent), *extra)
    return parent / name


def snapshot(root: Path) -> dict[str, bytes]:
    """Map every file under root (relative path) to its bytes."""
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }
