#!/usr/bin/env python3
"""PostToolUse(Edit|Write) hook: format the touched file ONLY if the project already configures a formatter.
Respects the surgical-change rule: no config -> do nothing. Always exits 0 (never blocks).
DRAFT, simulated-input tested only; verify stdin fields (tool_input.file_path) against current hooks docs."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def has(root: Path, *names: str) -> bool:
    return any((root / n).exists() for n in names)


def pyproject_has(root: Path, needle: str) -> bool:
    p = root / "pyproject.toml"
    return p.exists() and needle in p.read_text(encoding="utf-8", errors="ignore")


def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=False, timeout=30, capture_output=True)
    except Exception:
        pass


try:
    data = json.load(sys.stdin)
    f = Path(data.get("tool_input", {}).get("file_path", ""))
except Exception:
    sys.exit(0)

if not f.is_file():
    sys.exit(0)
root = Path.cwd()
ext = f.suffix.lower()

if ext == ".py" and (has(root, "ruff.toml", ".ruff.toml") or pyproject_has(root, "[tool.ruff")) and shutil.which("ruff"):
    run(["ruff", "format", str(f)])
elif ext in {".js", ".ts", ".tsx", ".jsx", ".vue", ".json", ".css", ".md"}:
    pkg = root / "package.json"
    cfg = has(root, ".prettierrc", ".prettierrc.json", ".prettierrc.js", "prettier.config.js") or (
        pkg.exists() and '"prettier"' in pkg.read_text(encoding="utf-8", errors="ignore"))
    bin_ = root / "node_modules" / ".bin" / ("prettier.cmd" if sys.platform == "win32" else "prettier")
    if cfg and bin_.exists():
        run([str(bin_), "--write", str(f)])
sys.exit(0)
