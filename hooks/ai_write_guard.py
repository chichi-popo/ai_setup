#!/usr/bin/env python3
"""PreToolUse(Write|Edit) guard for the explorer agent: it may write only under <project>/.ai/.
Registered in explorer.md frontmatter (agent-scoped, so the main session is not affected).
Exit 2 blocks, 0 allows. Bad or empty stdin blocks (fail closed). Stdlib only, Python 3.8+."""
from __future__ import annotations

import json
import os
import sys


def inside_ai(root: str, path: str) -> bool:
    root = os.path.normcase(os.path.realpath(root))
    p = path if os.path.isabs(path) else os.path.join(root, path)
    p = os.path.normcase(os.path.realpath(p))
    ai = os.path.join(root, ".ai")
    return p.startswith(ai + os.sep)


def main() -> int:
    try:
        d = json.loads(sys.stdin.read())
        path = (d.get("tool_input") or {}).get("file_path") or ""
    except (ValueError, AttributeError):
        print("explorer write blocked: unreadable hook input", file=sys.stderr)
        return 2
    root = os.environ.get("CLAUDE_PROJECT_DIR") or (d.get("cwd") if isinstance(d, dict) else None) or os.getcwd()
    if path and inside_ai(root, path):
        return 0
    print("explorer may write only under .ai/ (report anything else as BLOCKED: <reason>)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
