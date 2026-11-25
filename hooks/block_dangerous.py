#!/usr/bin/env python3
"""PreToolUse(Bash) guard (v2.1). Blocks irreversible deletion, history rewrite, secret exposure
and pipe-to-shell installs. Reads the hook JSON from stdin; exit code 2 blocks the call and
sends stderr back to the model. Stdlib only, Python 3.8+.

Design notes
- Rule IDs: R1 force push, R2 hard reset / discarding the working tree, R3 destructive SQL,
  R4 recursive delete of a protected target, R5 secret exposure, R6 pipe-to-shell.
- The command is split into segments (; && || | newline) and each segment is tokenized, so the
  words inside a commit message or an echo are not mistaken for a command.
- Only the rule id and a timestamp go to .ai/hook_blocks.log. The command text is never logged
  (it may contain secrets).
- Never blocks on its own errors (parse problems -> exit 0).
- Known limits: a command built at run time (variables, eval, base64), a script file that
  deletes things, and `find -delete` are NOT detected. This is a seatbelt, not a sandbox.
  deny rules in settings.json and the user's own review remain the real boundary.
- DRAFT: verify the stdin field names (tool_input.command) against the current hooks docs.
"""
import json
import os
import re
import shlex
import sys
import time
from pathlib import Path

PRINTERS = {"echo", "printf", "write-host", "write-output"}
SAFE_FIRST = PRINTERS | {"grep", "rg", "egrep", "fgrep", "man", "help"}

PROTECTED_EXACT = {
    "/", "/*", "~", "~/*", "$home", "${home}", "$home/*", "*", ".", "./*", "..", "../*",
    ".git", ".ai", ".claude", "%userprofile%", "$env:userprofile", "$env:homepath",
}
SYSTEM_DIRS = {"usr", "etc", "home", "var", "bin", "sbin", "lib", "opt", "root", "boot", "windows", "users"}

SECRET_NAME = re.compile(
    r"(^|[\\/])(\.env(\.[\w.-]+)?|id_rsa[\w.-]*|id_ed25519[\w.-]*|[^\\/]+\.(pem|key|p12|pfx)|\.npmrc|\.netrc|credentials)$",
    re.IGNORECASE,
)
SECRET_OK_SUFFIX = (".example", ".sample", ".template", ".dist")
SECRET_DIR = re.compile(r"(^|[\\/])secrets?[\\/]", re.IGNORECASE)
READERS = {"cat", "type", "more", "less", "head", "tail", "bat", "xxd", "od", "strings", "get-content", "gc", "cp", "copy",
           "scp", "rsync", "curl", "wget", "base64", "source", ".", "nano", "vi", "vim", "code", "notepad"}
SECRET_VAR = re.compile(r"\$(\{|env:)?\w*(key|token|secret|passw|credential)\w*", re.IGNORECASE)

SQL = re.compile(r"\b(drop\s+(table|database|schema)|truncate\s+table)\b", re.IGNORECASE)
PIPE_SHELL = re.compile(
    r"\b(curl|wget|iwr|invoke-webrequest)\b[^|;&]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?|pwsh|powershell|iex|invoke-expression)\b",
    re.IGNORECASE,
)

MSG = {
    "R1": "force push rewrites shared history",
    "R2": "hard reset / discarding the working tree loses uncommitted work",
    "R3": "destructive SQL (drop/truncate)",
    "R4": "recursive delete of a protected or very broad target",
    "R5": "this would expose a secret file or a secret environment variable",
    "R6": "piping a download into a shell runs unreviewed code",
}


def _split(cmd: str):
    """Split on ; && || | & and newlines, but not inside single or double quotes."""
    segs, cur, quote, i = [], [], None, 0
    while i < len(cmd):
        c = cmd[i]
        if quote:
            cur.append(c)
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
            cur.append(c)
        elif c in ";\n|&":
            if c in "|&" and i + 1 < len(cmd) and cmd[i + 1] == c:
                i += 1
            elif c == "&" and i + 1 < len(cmd) and cmd[i + 1] == ">":
                cur.append(c)
                i += 1
                continue
            segs.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    segs.append("".join(cur))
    return segs


def _strip(tok: str) -> str:
    tok = tok.strip()
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in "\"'":
        tok = tok[1:-1]
    return tok


def _tokens(seg: str):
    try:
        toks = shlex.split(seg, posix=False)
    except Exception:
        toks = seg.split()
    return [_strip(t) for t in toks if t.strip()]


def _is_protected(tok: str) -> bool:
    n = tok.replace("\\", "/").lower()
    while len(n) > 1 and n.endswith("/"):
        n = n[:-1]
    if n in PROTECTED_EXACT or tok.lower() in PROTECTED_EXACT:
        return True
    if re.fullmatch(r"[a-z]:(/\*?)?", n):          # C:  C:\  C:/*
        return True
    m = re.fullmatch(r"(?:[a-z]:)?/([a-z]+)(?:/\*)?", n)   # /usr  /etc/*  C:\Windows
    return bool(m and m.group(1) in SYSTEM_DIRS)


def _git_sub(toks):
    """Return (subcommand, args) skipping git global options such as -C <path> and -c k=v."""
    i = 1
    while i < len(toks):
        t = toks[i]
        if t in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") and i + 1 < len(toks):
            i += 2
        elif t.startswith("-"):
            i += 1
        else:
            return t.lower(), toks[i + 1:]
    return "", []


def _secret_token(t: str) -> bool:
    t = t.lstrip("@<>")
    if "=@" in t:
        t = t.split("=@", 1)[1]
    if t.lower().endswith(SECRET_OK_SUFFIX):
        return False
    return bool(SECRET_NAME.search(t) or SECRET_DIR.search(t))


def _check_git(toks):
    sub, rest = _git_sub(toks)
    lrest = [a.lower() for a in rest]
    if sub == "push":
        short_f = any(a.startswith("-") and not a.startswith("--") and "f" in a[1:] for a in lrest)
        if "--force" in lrest or short_f or "--mirror" in lrest or any(a.startswith("+") and len(a) > 1 for a in lrest):
            return "R1"                       # --force-with-lease is deliberately allowed
    elif sub == "reset" and "--hard" in lrest:
        return "R2"
    elif sub == "clean":
        flags = [a for a in lrest if a.startswith("-")]
        dry = "-n" in flags or "--dry-run" in flags or any(a.startswith("-") and not a.startswith("--") and "n" in a[1:] for a in flags)
        forced = "--force" in flags or any(a.startswith("-") and not a.startswith("--") and "f" in a[1:] for a in flags)
        if forced and not dry:
            return "R2"
    elif sub == "checkout":
        if rest == ["."] or ("--" in rest and rest[rest.index("--") + 1:] in (["."], ["./"])):
            return "R2"
    elif sub == "restore":
        if "." in rest and "--staged" not in lrest:
            return "R2"
    elif sub == "add" and any(_secret_token(a) for a in rest):
        return "R5"
    return None


def _check_delete(first, args):
    recursive = False
    targets = []
    for a in args:
        l = a.lower()
        if first in ("rm", "rmdir", "unlink"):
            if l == "--no-preserve-root":
                return "R4"
            if l.startswith("--"):
                recursive = recursive or l == "--recursive"
                continue
            if l.startswith("-") and len(l) > 1:
                recursive = recursive or "r" in l[1:]
                continue
        if first in ("rmdir", "del", "erase", "rd") and l.startswith("/") and len(l) == 2:
            recursive = recursive or l == "/s"      # cmd.exe style switches: /s /q /f
            continue
        if first in ("remove-item", "ri") and l.startswith("-"):
            recursive = recursive or l.startswith("-r")
            continue
        targets.append(a)
    if recursive and any(_is_protected(t) for t in targets):
        return "R4"
    return None


def check_segment(seg: str):
    toks = _tokens(seg)
    while toks and (re.fullmatch(r"[A-Za-z_]\w*=\S*", toks[0]) or toks[0].lower() in ("sudo", "command", "time", "nohup")):
        toks = toks[1:]
    if not toks:
        return None
    first = os.path.basename(toks[0]).lower()
    if first.endswith(".exe"):
        first = first[:-4]
    args = toks[1:]

    if first in SAFE_FIRST:
        return None
    if first == "git":
        return _check_git(toks)
    if first in ("rm", "rmdir", "unlink", "del", "erase", "rd", "remove-item", "ri"):
        return _check_delete(first, args)

    if first in READERS:
        scan = args[:-1] if first in ("cp", "copy") and len(args) > 1 else args   # copying INTO .env is allowed
        if any(_secret_token(a) for a in scan):
            return "R5"
    if first == "printenv" and not args:
        return "R5"
    if first == "env" and not args:
        return "R5"
    if first in ("get-childitem", "gci", "ls", "dir") and any(a.lower().rstrip("\\/") == "env:" for a in args):
        return "R5"
    if SQL.search(seg):
        return "R3"
    return None


def check(cmd: str):
    """Return (rule_id, message) or None."""
    if not cmd or not cmd.strip():
        return None
    if PIPE_SHELL.search(cmd):
        return "R6", MSG["R6"]
    for seg in _split(cmd):
        seg = seg.strip()
        if not seg:
            continue
        toks = _tokens(seg)
        if toks and os.path.basename(toks[0]).lower() in PRINTERS:
            if SECRET_VAR.search(seg):
                return "R5", MSG["R5"]
            continue
        rid = check_segment(seg)
        if rid:
            return rid, MSG[rid]
    return None


def _log(rule_id: str) -> None:
    try:
        root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        d = root / ".ai"
        d.mkdir(exist_ok=True)
        with open(d / "hook_blocks.log", "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{rule_id}\n")
    except Exception:
        pass


def main() -> int:
    try:
        data = json.load(sys.stdin)
        cmd = (data.get("tool_input") or {}).get("command", "")
        hit = check(cmd)
    except Exception:
        return 0  # never block on the hook's own errors
    if hit:
        rid, why = hit
        _log(rid)
        print(f"Blocked by hook (rule {rid}): {why}. If the user really wants this, ask them to run it manually.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
