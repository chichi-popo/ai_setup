#!/usr/bin/env python3
"""Approval hash record (v2.2 A1). Usage:
  python .claude/hooks/approval_hash.py record <file>   append 'date | path | sha256' to .ai/approvals.md
  python .claude/hooks/approval_hash.py check  <file>   exit 0 if the file matches its last record, else 1 (re-approval needed)
Stdlib only, Python 3.8+. The project root is CLAUDE_PROJECT_DIR or the current directory."""
from __future__ import annotations

import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path


def root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(root().resolve()).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def last_hash(log: Path, key: str):
    if not log.exists():
        return None
    found = None
    for line in log.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = [x.strip() for x in line.split("|")]
        if len(parts) == 3 and parts[1] == key:
            found = parts[2]
    return found


def main(argv: list) -> int:
    if len(argv) != 3 or argv[1] not in ("record", "check"):
        print(__doc__)
        return 2
    target = Path(argv[2])
    if not target.is_file():
        print(f"BLOCKED: not a file: {target}")
        return 2
    log = root() / ".ai" / "approvals.md"
    key, h = rel(target), digest(target)
    if argv[1] == "record":
        log.parent.mkdir(parents=True, exist_ok=True)
        new = not log.exists()
        with open(log, "a", encoding="utf-8", newline="\n") as f:
            if new:
                f.write("# approvals\n\n<!-- date | path | sha256 -->\n")
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M')} | {key} | {h}\n")
        print(f"recorded {key} {h[:12]}")
        return 0
    prev = last_hash(log, key)
    if prev is None:
        print(f"NOT APPROVED: no record for {key} (record after approval)")
        return 1
    if prev != h:
        print(f"CHANGED since approval: {key} (re-approval needed)")
        return 1
    print(f"approved: {key} {h[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
