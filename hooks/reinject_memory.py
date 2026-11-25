#!/usr/bin/env python3
"""SessionStart(compact) hook: re-inject a capped memory summary after compaction. DRAFT, untested live.
Stdout of a SessionStart hook is added to context (verify in current docs).
Caps keep injected text small: first 60 lines of plan.md and context.md each, each line cut at 160 characters.
Keep the limits in sync with MEM_MAX_LINES / MEM_MAX_CHARS in init_project.py (files should already obey them)."""
from pathlib import Path

MAX_LINES = 60
MAX_CHARS = 160
root = Path(".ai/memory")
out = []
for name in ("plan.md", "context.md"):
    f = root / name
    if f.exists():
        lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        out.append(f"## {name} (first {MAX_LINES} lines)")
        for l in lines[:MAX_LINES]:
            out.append(l if len(l) <= MAX_CHARS else l[:MAX_CHARS] + " [...cut]")
        if len(lines) > MAX_LINES:
            out.append(f"[... {len(lines) - MAX_LINES} more lines; archive finished items to .ai/memory/archive/]")
        if any(len(l) > MAX_CHARS for l in lines):
            out.append(f"[WARNING: {name} has lines over {MAX_CHARS} chars; run init_project.py --check-memory]")
print("\n".join(out))
