#!/usr/bin/env python3
"""setup_env.py - bring the Claude environment up on a new PC, with approval before every change.

What it does
  1. Checks prerequisites (Python, git, Claude Code CLI, Node) and reports; it never installs them.
  2. Lists every action it could take and asks y/N for each group:
       A. pip install --user -r requirements.txt   (PyYAML)
       B. copy the common sub-agents to ~/.claude/agents/   (existing files are kept)
       C. copy the global slash command(s) (/ai-guide) to ~/.claude/commands/   (existing files are kept)
  3. Runs a harmless self-test of init_project.py in a temp folder.
  4. Prints the guide list for things it will NOT touch (account skills, plugins, settings, manual steps).

Safety
  - Interactive prompt is the default. --plan prints everything and changes nothing.
  - No terminal input (CI, pipes) behaves like --plan. --yes approves actions A, B and C explicitly.
  - It never edits settings.json, never installs plugins, never deletes anything.

Usage
  python setup_env.py                   # ask before each action
  python setup_env.py --plan            # read-only guide
  python setup_env.py --lang en         # copy the English agent files (default: kr)
  python setup_env.py --write-checklist SETUP_CHECKLIST.md
  python setup_env.py --export-backup   # refresh backup/roster.json from roster.yaml (needs PyYAML)
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAUDE_HOME = Path.home() / ".claude"


def say(msg: str = "") -> None:
    print(msg)


def ask(question: str, args) -> bool:
    if args.plan:
        say(f"  [plan only] {question} -> not run")
        return False
    if args.yes:
        say(f"  [--yes] {question} -> approved")
        return True
    if not sys.stdin.isatty():
        say(f"  [no terminal] {question} -> not run (use --yes to approve explicitly)")
        return False
    try:
        return input(f"  {question} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def pip_install_requirements(req: Path) -> tuple[bool, str]:
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    cmd = [sys.executable, "-m", "pip", "install"] + ([] if in_venv else ["--user"]) + ["-r", str(req)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except Exception as e:  # noqa: BLE001
        return False, str(e)
    tail = (r.stdout + r.stderr).strip().splitlines()[-6:]
    return r.returncode == 0, "\n".join(tail)


def load_manifest(args) -> dict:
    """Read roster.yaml. If PyYAML is missing, offer to install it, else fall back to backup/roster.json."""
    try:
        import yaml  # type: ignore
        return yaml.safe_load((HERE / "roster.yaml").read_text(encoding="utf-8"))
    except ImportError:
        pass
    say("PyYAML is not installed (needed to read roster.yaml).")
    req = HERE / "requirements.txt"
    if req.exists() and ask("Install PyYAML now with pip (user install, or into the active venv)?", args):
        ok, out = pip_install_requirements(req)
        say(out)
        if ok:
            import importlib
            importlib.invalidate_caches()
            import yaml  # type: ignore
            return yaml.safe_load((HERE / "roster.yaml").read_text(encoding="utf-8"))
        say("pip install failed; see the message above.")
    bak = HERE / "backup" / "roster.json"
    if bak.exists():
        say("Using backup/roster.json instead (read-only plan; it may be older than roster.yaml).")
        return json.loads(bak.read_text(encoding="utf-8"))
    raise SystemExit("error: no PyYAML and no backup/roster.json. Install with: python -m pip install --user -r requirements.txt")


def check_prereqs(env: dict) -> list[str]:
    say("== 1. Prerequisites (checked, never auto-installed)")
    problems = []
    for item in env.get("prerequisites", []):
        name = item["name"]
        if name.lower() == "python":
            have = sys.version_info[:2]
            need = tuple(int(x) for x in str(item.get("min_version", "3.8")).split("."))
            ok = have >= need
            state = f"OK ({sys.version.split()[0]})" if ok else f"TOO OLD ({sys.version.split()[0]}, need {item['min_version']}+)"
        else:
            path = shutil.which(item.get("which", ""))
            ok = bool(path)
            state = f"OK ({path})" if ok else "MISSING"
        tag = "required" if item.get("required") else "optional"
        say(f"  - {name:<16} {state:<40} [{tag}] {item.get('purpose', '')}")
        if not ok:
            say(f"      get it: {item.get('hint', 'see official site')}")
            if item.get("required"):
                problems.append(name)
    return problems


def action_pip(env: dict, args) -> None:
    say("== 2. Python packages")
    req = HERE / env.get("python_requirements", "requirements.txt")
    if not req.exists():
        say(f"  requirements file not found: {req}")
        return
    try:
        import yaml  # type: ignore  # noqa: F401
        say("  PyYAML already installed. Nothing to do.")
        return
    except ImportError:
        pass
    pkgs = [l.strip() for l in req.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    say(f"  would run: {sys.executable} -m pip install [--user unless in a venv] -r {req.name}   ({', '.join(pkgs)})")
    if ask("Install these packages?", args):
        ok, out = pip_install_requirements(req)
        say(out)
        say("  installed." if ok else "  FAILED. On a managed/system Python, create a venv and run pip there, then run the scripts with that Python.")


def action_deploy_agents(env: dict, args) -> None:
    say("== 3. User-level sub-agents (~/.claude/agents)")
    names = env.get("user_level_deploy", {}).get("agents", [])
    dest_dir = CLAUDE_HOME / "agents"
    todo, kept = [], []
    for n in names:
        s, d = HERE / "lang" / args.lang / "agents" / f"{n}.md", dest_dir / f"{n}.md"
        if not s.exists():
            say(f"  skip {n}: source missing")
        elif d.exists():
            kept.append(d)
        else:
            todo.append((s, d))
    for d in kept:
        say(f"  keep existing {d}")
    if not todo:
        say("  nothing to copy.")
        return
    for s, d in todo:
        say(f"  would copy {s.name} -> {d}")
    if ask("Copy these agent files?", args):
        for s, d in todo:
            d.parent.mkdir(parents=True, exist_ok=True)
            d.write_bytes((s.read_text(encoding="utf-8")).encode("utf-8"))
            say(f"  copied {d}")


def action_deploy_commands(env: dict, args) -> None:
    say("== 3b. User-level slash commands (~/.claude/commands)")
    names = env.get("user_level_deploy", {}).get("commands", [])
    dest_dir = CLAUDE_HOME / "commands"
    todo, kept = [], []
    for n in names:
        s, d = HERE / "lang" / args.lang / "commands" / f"{n}.md", dest_dir / f"{n}.md"
        if not s.exists():
            say(f"  skip {n}: source missing")
        elif d.exists():
            kept.append(d)
        else:
            todo.append((s, d))
    for d in kept:
        say(f"  keep existing {d} (delete it to receive the newer version)")
    if not todo:
        say("  nothing to copy.")
        return
    for s, d in todo:
        say(f"  would copy {s.name} -> {d}")
    if ask("Copy these command files?", args):
        for s, d in todo:
            d.parent.mkdir(parents=True, exist_ok=True)
            d.write_bytes((s.read_text(encoding="utf-8")).encode("utf-8"))
            say(f"  copied {d}")


def self_test(args) -> None:
    say("== 4. Self-test of init_project.py (temp folder, removed afterwards)")
    script = HERE / "init_project.py"
    if not script.exists():
        say("  init_project.py not found next to this script.")
        return
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "requirements.txt").write_text("pytest\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "-I", str(script), "--root", td, "--dry-run", "--preset", "base", "--lang", args.lang],
                           capture_output=True, text=True, timeout=60)
    say("  PASS" if r.returncode == 0 else f"  FAIL (exit {r.returncode})\n{(r.stdout + r.stderr)[-500:]}")


def guide_lines(env: dict) -> list[str]:
    out = ["== 5. Guide list (not touched by this script)", ""]
    a = env.get("account_skills", {})
    out.append("Account skills")
    out.append("  keep:       " + ", ".join(a.get("keep", [])))
    out.append("  review off: " + ", ".join(a.get("review_off", [])))
    out.append("Plugins to review")
    out += [f"  - {x}" for x in env.get("plugins_review", [])]
    out.append("Settings to review (one at a time, measure after each)")
    out += [f"  - {x}" for x in env.get("settings_review", [])]
    out.append("Rollout order")
    out += [f"  {x}" for x in env.get("rollout", [])]
    out.append("External skills (approved after the review gate; see third_party/README.md)")
    ext = env.get("external_skills") or []
    out += [f"  - {x}" for x in ext] if ext else ["  (none approved yet)"]
    out.append("Manual steps")
    out += [f"  {i}. {x}" for i, x in enumerate(env.get("manual_steps", []), 1)]
    return out


def export_backup() -> int:
    try:
        import yaml  # type: ignore
    except ImportError:
        print("error: PyYAML is needed to export the backup. Run: python -m pip install --user -r requirements.txt", file=sys.stderr)
        return 2
    data = yaml.safe_load((HERE / "roster.yaml").read_text(encoding="utf-8"))
    dest = HERE / "backup" / "roster.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"wrote {dest}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", action="store_true", help="print the plan and guide; change nothing")
    ap.add_argument("--yes", action="store_true", help="approve the install/copy actions without prompting")
    ap.add_argument("--lang", choices=["kr", "en"], default="kr", help="language of the agent files to copy (default kr)")
    ap.add_argument("--write-checklist", metavar="FILE", help="also write the guide list to a text file")
    ap.add_argument("--export-backup", action="store_true", help="refresh backup/roster.json from roster.yaml")
    args = ap.parse_args()

    if args.export_backup:
        return export_backup()
    if args.plan and args.yes:
        ap.error("--plan and --yes cannot be combined")

    say(f"Claude environment setup  |  python {sys.version.split()[0]}  |  folder: {HERE}")
    env = load_manifest(args).get("environment", {})
    problems = check_prereqs(env)
    say()
    action_pip(env, args)
    say()
    action_deploy_agents(env, args)
    say()
    action_deploy_commands(env, args)
    say()
    self_test(args)
    say()
    lines = guide_lines(env)
    say("\n".join(lines))
    if args.write_checklist:
        Path(args.write_checklist).write_text("\n".join(lines) + "\n", encoding="utf-8")
        say(f"\nwrote {args.write_checklist}")
    if problems:
        say("\nMissing required tools: " + ", ".join(problems) + ". Install them, then run this script again.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
