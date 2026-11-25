#!/usr/bin/env python3
"""Token-free status (v2.2 A5): reads files only, prints at most 10 lines. Run it by hand, or as a SessionStart(startup) hook.
Shows: top of .ai/NOW.md (v2.4 kb; else .ai/memory/plan.md), BLOCKED.md presence, last 3 approvals, changed file count (if git), last check result.
Stdlib only, Python 3.8+."""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
ai = root / ".ai"
out = []


def text(p: Path):
    try:
        return p.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


src = ai / "NOW.md" if (ai / "NOW.md").exists() else ai / "memory" / "plan.md"  # v2.4: kb NOW.md first
plan = [l.strip() for l in text(src) if l.strip() and not l.startswith(("#", "<!--"))][:3]
out.append(("now: " if src.name == "NOW.md" else "plan: ") + (" / ".join(x[:80] for x in plan) if plan else "(none)"))
out.append("BLOCKED: " + ("YES (.ai/BLOCKED.md)" if (ai / "BLOCKED.md").exists() else "no"))
appr = [l for l in text(ai / "approvals.md") if l.count("|") == 2][-3:]
out.append("approvals: " + (" ; ".join(a.split("|")[1].strip() + " " + a.split("|")[0].strip() for a in appr) if appr else "(none)"))
try:
    g = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, timeout=5)
    if g.returncode == 0:
        out.append(f"changed files: {len([l for l in g.stdout.splitlines() if l.strip()])}")
except (OSError, subprocess.SubprocessError):
    pass
try:
    c = json.loads((ai / "last_check.json").read_text(encoding="utf-8"))
    age = int((time.time() - float(c.get("time", 0))) / 60)
    out.append(f"last check: exit {c.get('exit')} ({age} min ago): {str(c.get('cmd', ''))[:60]}")
except (OSError, ValueError):
    out.append("last check: (none)")
print("\n".join(out[:10]))
