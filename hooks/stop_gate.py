#!/usr/bin/env python3
"""Stop hook (v2.3 A5). DRAFT, INACTIVE: register only after the Stop stdin fields are confirmed in a disposable repo.
Blocks stopping (exit 2 + reason on stderr) when .ai/last_check.json exists AND either its exit != 0 or a code file is
newer than the check. No last_check.json means no gate (document and doc-only projects are never blocked).
stop_hook_active true -> allow (prevents an endless loop). Bad or empty stdin -> allow. Stdlib only, Python 3.8+."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".vue", ".java", ".kt", ".go", ".rs", ".c", ".cc", ".cpp", ".h",
            ".cs", ".rb", ".php", ".swift", ".sh", ".ps1", ".sql", ".ipynb"}
PRUNE = {".git", ".ai", ".claude", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next",
         ".pytest_cache", ".mypy_cache", "target"}
MAX_FILES = 20000


def newer_code(root: Path, since: float):
    n = 0
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in PRUNE]
        for f in fn:
            n += 1
            if n > MAX_FILES:
                return None
            if os.path.splitext(f)[1].lower() in CODE_EXT:
                p = os.path.join(dp, f)
                try:
                    if os.path.getmtime(p) > since + 1:
                        return os.path.relpath(p, root)
                except OSError:
                    pass
    return None


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(data, dict) or data.get("stop_hook_active"):
        return 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    try:
        c = json.loads((root / ".ai" / "last_check.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    if c.get("exit") != 0:
        print(f"Do not finish: last check exited {c.get('exit')} ({str(c.get('cmd', ''))[:60]}). "
              "Fix it or report UNVERIFIED/BLOCKED with the reason.", file=sys.stderr)
        return 2
    changed = newer_code(root, float(c.get("time", 0)))
    if changed:
        print(f"Do not finish: {changed} changed after the last passing check. Re-run the check "
              "(python .claude/hooks/run_check.py -- <command>) or report UNVERIFIED.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
