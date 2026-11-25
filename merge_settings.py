#!/usr/bin/env python3
"""Merge the v2.4 hook/permission entries into <project>/.claude/settings.json (idempotent; appends, never drops your rules).
  python merge_settings.py <project_root> [--hook-path abs|env|rel] [--no-kb] [--status] [--drop-status] [--no-ask]
Adds:
  PreToolUse(Bash) block_dangerous, the 10 deny rules, permissions.ask git commit/push (skip with --no-ask),
  v2.4 kb hooks (skip with --no-kb):
    SessionStart(startup|clear|compact) -> kb.py hook-start   (prints NOW + INDEX, about 1-3k tokens)
    PostToolUse(Edit|Write|MultiEdit)   -> kb.py hook-build   (rebuilds INDEX when a card/NOW changed; no output)
    permissions.allow  Bash(python .ai/kb.py:*)               (kb commands write only under .ai/)
  SessionStart(startup) status.py only with --status (kb hook-start covers it). --drop-status removes it.
v2.4.1 hook paths (--hook-path, default abs):
  abs  python "D:/path/to/project/.claude/hooks/x.py"   works whatever folder the session has cd'ed into (default)
  env  python "$CLAUDE_PROJECT_DIR/.claude/hooks/x.py"  portable across PCs; needs the hook shell to expand the variable
  rel  python .claude/hooks/x.py                         v2.4 behaviour; breaks after a `cd` inside the session
v2.4.1 also copies AI_Tools/hooks/*.py into <project>/.claude/hooks/ when missing or different (--no-copy-hooks to skip),
so the registered scripts always exist.
  Existing entries for the same scripts (any of the three forms, any old root) are rewritten to the chosen form,
  so rerunning this after moving or copying the project fixes the paths. Rerun it on each PC (paths differ).
A .bak_<time> copy is made first. Stdlib only, Python 3.8+."""
from __future__ import annotations

import json
import re
import shutil
import sys
import time
from pathlib import Path

DENY = ["Read(./.env)", "Read(./.env.*)", "Read(**/*.pem)", "Read(**/*.key)", "Read(**/secrets/**)", "Read(**/*.p12)",
        "Read(**/*.pfx)", "Read(~/.ssh/**)", "Bash(git push --force:*)", "Bash(rm -rf /:*)"]
ASK = ["Bash(git commit:*)", "Bash(git push:*)"]
KB_ALLOW = "Bash(python .ai/kb.py:*)"
# managed scripts: relative path (forward slashes) -> identity
MANAGED = re.compile(r'^python3?\s+"?(?:.*?[\\/])?(\.claude[\\/]hooks[\\/][\w.-]+\.py|\.ai[\\/]kb\.py)"?(\s.*)?$')


def ident(cmd: str):
    m = MANAGED.match((cmd or "").strip())
    if not m:
        return None
    return m.group(1).replace("\\", "/"), (m.group(2) or "").strip()


def make(script: str, args: str, mode: str, root: str) -> str:
    if mode == "rel":
        path = script
    elif mode == "env":
        path = '"$CLAUDE_PROJECT_DIR/' + script + '"'
    else:
        path = '"' + root + "/" + script + '"'
    return f"python {path}" + (f" {args}" if args else "")


def all_hooks(d: dict):
    for event, groups in d.get("hooks", {}).items():
        for g in groups:
            for h in g.get("hooks", []):
                yield event, g, h


def add_hook(d: dict, event: str, matcher: str, cmd: str) -> bool:
    want = ident(cmd)
    groups = d.setdefault("hooks", {}).setdefault(event, [])
    if any(ident(h.get("command", "")) == want for g in groups for h in g.get("hooks", [])):
        return False
    groups.append({"matcher": matcher, "hooks": [{"type": "command", "command": cmd}]})
    return True


def drop_hook(d: dict, event: str, script: str) -> int:
    groups = d.get("hooks", {}).get(event, [])
    n = 0
    for g in groups:
        before = len(g.get("hooks", []))
        g["hooks"] = [h for h in g.get("hooks", []) if (ident(h.get("command", "")) or ("",))[0] != script]
        n += before - len(g["hooks"])
    if groups:
        d["hooks"][event] = [g for g in groups if g.get("hooks")]
    return n


def main(argv: list) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    mode = "abs"
    if "--hook-path" in argv:
        i = argv.index("--hook-path")
        mode = argv[i + 1] if i + 1 < len(argv) else ""
        args = [a for a in args if a != mode]
    if len(args) != 1 or mode not in ("abs", "env", "rel"):
        print(__doc__)
        return 2
    root = Path(args[0]).resolve()
    rootp = root.as_posix()
    p = root / ".claude" / "settings.json"
    d = {}
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        shutil.copy2(p, p.with_name(p.name + ".bak_" + time.strftime("%Y%m%d_%H%M%S")))
    changed = []
    src_hooks = Path(__file__).resolve().parent / "hooks"
    if "--no-copy-hooks" not in argv and src_hooks.is_dir():
        dst = root / ".claude" / "hooks"
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src_hooks.glob("*.py")):
            t = dst / f.name
            if not t.exists() or t.read_bytes() != f.read_bytes():
                shutil.copy2(f, t)
                changed.append(f"copied hook {f.name}")
    # 1) rewrite existing managed entries to the chosen path form (fixes relative paths and old roots)
    for event, g, h in list(all_hooks(d)):
        idt = ident(h.get("command", ""))
        if idt:
            new = make(idt[0], idt[1], mode, rootp)
            if new != h.get("command"):
                changed.append(f"path {event}: {h.get('command')} -> {new}")
                h["command"] = new
    # 2) add missing entries
    if add_hook(d, "PreToolUse", "Bash", make(".claude/hooks/block_dangerous.py", "", mode, rootp)):
        changed.append("PreToolUse block_dangerous")
    if "--no-kb" not in argv:
        if not (root / ".ai" / "kb.py").exists():
            print("warning: .ai/kb.py not found; run init_project.py first (hooks added anyway)")
        if add_hook(d, "SessionStart", "startup|clear|compact", make(".ai/kb.py", "hook-start", mode, rootp)):
            changed.append("SessionStart kb hook-start")
        if add_hook(d, "PostToolUse", "Edit|Write|MultiEdit", make(".ai/kb.py", "hook-build", mode, rootp)):
            changed.append("PostToolUse kb hook-build")
    if "--status" in argv and add_hook(d, "SessionStart", "startup", make(".claude/hooks/status.py", "", mode, rootp)):
        changed.append("SessionStart status")
    if "--drop-status" in argv:
        n = drop_hook(d, "SessionStart", ".claude/hooks/status.py")
        if n:
            changed.append(f"removed SessionStart status ({n})")
    perms = d.setdefault("permissions", {})
    for key, rules, skip in (("deny", DENY, False), ("ask", ASK, "--no-ask" in argv),
                             ("allow", [KB_ALLOW], "--no-kb" in argv)):
        if skip:
            continue
        cur = perms.setdefault(key, [])
        for r in rules:
            if r not in cur:
                cur.append(r)
                changed.append(f"{key} {r}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((json.dumps(d, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"{p}: " + (f"{len(changed)} change(s), hook paths: {mode}" if changed else f"already up to date (hook paths: {mode})"))
    for c in changed:
        print("  + " + c)
    for event, g, h in all_hooks(d):
        idt = ident(h.get("command", ""))
        if idt and not (root / idt[0]).exists():
            print(f"warning: {event} hook script missing: {idt[0]}")
    has_status = any((ident(h.get("command", "")) or ("",))[0] == ".claude/hooks/status.py"
                     for g in d.get("hooks", {}).get("SessionStart", []) for h in g.get("hooks", []))
    if has_status and "--no-kb" not in argv:
        print("note: status.py is also registered at SessionStart; rerun with --drop-status to avoid a duplicate startup print")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
