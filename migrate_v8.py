#!/usr/bin/env python3
"""migrate_v8.py (v2.4) - retire the old AI Control v8 system from one project, keeping every original byte.

  python migrate_v8.py --root <project>                  dry run: show what would happen (default)
  python migrate_v8.py --root <project> --apply          do it
  python migrate_v8.py --root <project> --retire-memory  after the cards are made: move .ai/memory away once
                                                         `kb.py check --coverage` reports no missing IDs

--apply does, in order:
  1. Copies verbatim into .ai/archive/legacy-v8/<date>/: CLAUDE.md, AGENTS.md, GEMINI.md, .ai/system_prompt.md, .ai/.mode,
     .ai/profiles/*, .ai/memory/**, .ai/manuals/** (SHA-256 checked). Nothing is summarized.
  2. Removes the v8 instruction files: CLAUDE.md/AGENTS.md/GEMINI.md only if they are the v8 merged profile
     (hard links to .ai/system_prompt.md), .ai/system_prompt.md, .ai/.mode, .ai/profiles/. Keeps .ai/memory (cards
     come first), .ai/manuals, .ai/scripts, .ai/archive.
  3. Removes the project from the refresh-ai registry (default C:\\AI_Tools\\ai-profiles\\registry.txt; backup first),
     so the logon task no longer rewrites CLAUDE.md.
Then: init_project.py --preset <name>, merge_settings.py, split .ai/memory into cards (kb/MIGRATION_PROMPT.*.md),
kb.py check --coverage .ai/archive/legacy-v8/<date>/memory, and finally --retire-memory.
Stdlib only, Python 3.8+."""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

V8_MARKERS = ("[MASTER SYSTEM DIRECTIVE", "[CURRENT MODE:")
TOP = ("CLAUDE.md", "AGENTS.md", "GEMINI.md")


def is_v8(p: Path) -> bool:
    try:
        head = p.read_text(encoding="utf-8-sig", errors="ignore")[:4000]
    except OSError:
        return False
    return any(m in head for m in V8_MARKERS)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def collect(root: Path) -> list:
    """(source, relative destination) pairs to archive."""
    ai = root / ".ai"
    out = [(root / n, n) for n in TOP if (root / n).exists()]
    for n in ("system_prompt.md", ".mode"):
        if (ai / n).exists():
            out.append((ai / n, f".ai/{n}"))
    for d in ("profiles", "memory", "manuals"):
        base = ai / d
        if base.is_dir():
            # os.walk tolerates broken or unreadable links (e.g. profile links to a moved central folder)
            for dirpath, _dirs, files in os.walk(base, followlinks=False):
                for name in sorted(files):
                    p = Path(dirpath) / name
                    out.append((p, f".ai/{d}/{p.relative_to(base).as_posix()}"))
    return out


def default_registry(script_dir: Path) -> Path:
    for c in (Path(r"C:\AI_Tools\ai-profiles\registry.txt"), script_dir / "ai-profiles" / "registry.txt"):
        if c.exists():
            return c
    return Path(r"C:\AI_Tools\ai-profiles\registry.txt")


def norm(p: str) -> str:
    return os.path.normcase(os.path.normpath(p.strip().lstrip("\ufeff")))


def migrate(root: Path, apply: bool, registry: Path) -> int:
    ai = root / ".ai"
    pairs = collect(root)
    if not pairs:
        print("nothing to migrate: no v8 files found")
        return 0
    dest = ai / "archive" / "legacy-v8" / time.strftime("%Y%m%d")
    if dest.exists():
        dest = Path(str(dest) + time.strftime("_%H%M%S"))
    print(f"archive -> {dest}")
    bad = 0
    for src, r in pairs:
        try:
            data = src.read_bytes()
        except OSError as e:
            print(f"  [unreadable, name only] {r}: {e}")
            if apply:
                (dest / (r + ".UNREADABLE.txt")).parent.mkdir(parents=True, exist_ok=True)
                (dest / (r + ".UNREADABLE.txt")).write_text(f"{src}\n{e}\n", encoding="utf-8")
            continue
        links = ""
        try:
            n = src.stat().st_nlink
            links = f" (hard links x{n})" if n > 1 else ""
        except OSError:
            pass
        print(f"  copy {r} ({len(data)} bytes){links}")
        if apply:
            t = dest / r
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_bytes(data)
            if sha(t.read_bytes()) != sha(data):
                print(f"  ERROR checksum mismatch: {t}")
                bad += 1
    if bad:
        print("stopped: archive copy failed; nothing removed")
        return 1
    removals = []
    for n in TOP:
        p = root / n
        if p.exists():
            if is_v8(p):
                removals.append(p)
            else:
                print(f"  keep {n}: not the v8 profile (edit it yourself if needed)")
    for n in ("system_prompt.md", ".mode"):
        if (ai / n).exists():
            removals.append(ai / n)
    prof = ai / "profiles"
    for p in removals:
        print(f"  remove {p.relative_to(root).as_posix()}")
    if prof.exists():
        print("  remove .ai/profiles/")
    lines, hit = [], []
    if registry.exists():
        raw = registry.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        hit = [l for l in raw if l.strip() and norm(l) == norm(str(root))]
        lines = [l for l in raw if l not in hit]
        print(f"  registry {registry}: " + (f"remove {len(hit)} line(s)" if hit else "project not listed"))
    else:
        print(f"  registry not found ({registry}); skip")
    if not apply:
        print("dry run only. Rerun with --apply.")
        return 0
    for p in removals:
        p.unlink()
    if prof.exists():
        for dirpath, dirs, files in os.walk(prof, topdown=False, followlinks=False):
            for name in files:
                os.remove(os.path.join(dirpath, name))
            for name in dirs:
                q = os.path.join(dirpath, name)
                os.remove(q) if os.path.islink(q) else os.rmdir(q)
        os.rmdir(prof)
    if hit:
        shutil.copy2(registry, registry.with_name(registry.name + ".bak_" + time.strftime("%Y%m%d_%H%M%S")))
        registry.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8-sig")
        if not [l for l in lines if l.strip()]:
            print("  registry is now empty: the logon task can go too ->"
                  " Unregister-ScheduledTask -TaskName AI-Profile-Refresh-OnLogon -Confirm:$false")
    here = Path(__file__).resolve().parent
    print("done. Next:")
    print(f"  1) python {here / 'init_project.py'} --root \"{root}\" --preset <name> --dry-run   (then without --dry-run)")
    print(f"  2) python {here / 'merge_settings.py'} \"{root}\" --drop-status")
    print(f"  3) in Claude Code: paste {here / 'kb' / 'MIGRATION_PROMPT.kr.md'} (splits .ai/memory into cards)")
    print(f"  4) python .ai/kb.py check --coverage {(dest / '.ai' / 'memory').relative_to(root).as_posix()}")
    print(f"  5) python {Path(__file__).name} --root \"{root}\" --retire-memory")
    return 0


def retire(root: Path) -> int:
    mem = root / ".ai" / "memory"
    kb = root / ".ai" / "kb.py"
    if not mem.is_dir():
        print("no .ai/memory: nothing to retire")
        return 0
    if not kb.exists():
        print("error: .ai/kb.py missing; run init_project.py first")
        return 2
    r = subprocess.run([sys.executable, str(kb), "--root", str(root), "check", "--coverage", str(mem)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    missing = [l for l in r.stdout.splitlines() if l.startswith("MISSING ")]
    if missing:
        print("\n".join(missing[:40]))
        print(f"stopped: {len(missing)} id(s) from .ai/memory are not in any card yet")
        return 1
    dst = root / ".ai" / "archive" / "legacy-v8" / ("memory-retired-" + time.strftime("%Y%m%d_%H%M%S"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(mem), str(dst))
    print(f"moved .ai/memory -> {dst.relative_to(root).as_posix()} (coverage: 0 missing)")
    print("tip: to keep the verbatim v8 copies out of search results, add \".ai/archive/legacy-v8\" to search_exclude in .ai/kb.json")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--registry", default=None)
    ap.add_argument("--retire-memory", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory")
        return 2
    if a.retire_memory:
        return retire(root)
    reg = Path(a.registry) if a.registry else default_registry(Path(__file__).resolve().parent)
    return migrate(root, a.apply, reg)


if __name__ == "__main__":
    sys.exit(main())
