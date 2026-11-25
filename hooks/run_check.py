#!/usr/bin/env python3
"""Run a check command and record the result (v2.3 A5 prerequisite). Usage:
  python .claude/hooks/run_check.py -- <command ...>
Runs the command, writes .ai/last_check.json {cmd, exit, time} and exits with the same code.
Stdlib only, Python 3.8+. The project root is CLAUDE_PROJECT_DIR or the current directory."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


def main(argv: list) -> int:
    args = argv[1:]
    if args and args[0] == "--":
        args = args[1:]
    if not args:
        print(__doc__)
        return 2
    if len(args) == 1:
        proc = subprocess.run(args[0], shell=True)
        cmd = args[0]
    else:
        try:
            proc = subprocess.run(args)
        except FileNotFoundError:
            print(f"BLOCKED: command not found: {args[0]}")
            return 127
        cmd = " ".join(args)
    out = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()) / ".ai" / "last_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"cmd": cmd, "exit": proc.returncode, "time": time.time()}, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv))
