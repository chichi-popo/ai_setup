#!/usr/bin/env python3
"""init_project.py v2.4 - project bootstrap for the Claude environment redesign.

v2.4: card memory (kb) replaces .ai/memory: creates .ai/kb/<type>/, .ai/NOW.md, .ai/kb.json, copies .ai/kb.py and builds
.ai/INDEX.md; writes a short AGENTS.md pointer for other AI tools; creates .ai/design/DESIGN.md when the preset has the
doc-design skill; copies whole skill folders (SKILL.md plus helper files); breaks hard links before writing CLAUDE.md;
v2.4.1: agent-scoped hook commands are written with the project's absolute path, and the block gets a no-`cd` rule.
refuses to touch a project still run by the old v8 system (CLAUDE.md = merged profile) unless --allow-legacy
(migrate first: python migrate_v8.py --root <project>).

What it does
  1. Scans the project (pruned walk, no node_modules traversal) for stacks,
     package manager, test/build commands, entry points and docs/paper/patent assets.
  2. Writes a managed block into CLAUDE.md. Text outside the block is never touched.
     v2.1: the block stays small (stack, commands, rules). Stack details and docs/research asset
     counts live in .ai/repo_audit_map.md; the block only points to it.
  3. Creates .ai/INTENT.md (goal, scope) and the kb card memory (v2.4) only if missing.
  4. For an existing codebase ("legacy") or a project with docs/research assets, writes a
     pre-filled .ai/repo_audit_map.md draft (the explorer completes it on first entry).
  5. With --preset, copies skills/agents/rules and (v2.1) project-knowledge skill stubs
     (.claude/skills/project-<slot>/SKILL.md, inactive until you fill them in).

Usage
  python init_project.py                 # scan current dir, apply
  python init_project.py --dry-run       # show what would be written
  python init_project.py --root path/to/project --mode legacy
  python init_project.py --check-memory --root path/to/project   # lint .ai/memory (read-only)
  python init_project.py --root path/to/project --skill blueprint,system-architect [--dry-run]   # v2.4.6: only these skill folders

Standard library only (Python 3.8+).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

BEGIN = "<!-- AI-INIT:BEGIN (managed by init_project.py; edit outside this block) -->"
KB_TYPES = ("progress", "decision", "issue", "map", "asset")
KB_MARK = "# managed-by: redesign_v2 kb"
V8_MARKERS = ("[MASTER SYSTEM DIRECTIVE", "[CURRENT MODE:")
END = "<!-- AI-INIT:END -->"

# Memory hygiene limits (single source of truth). Both must hold for every .ai/memory/*.md file.
MEM_MAX_LINES = 200       # total lines per memory file (target 50-100 for plan/context; archive the rest)
MEM_MAX_CHARS = 160       # characters per line; split long lines or move detail to archive/ or docs

PRUNE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", "dist", "build",
    "target", ".gradle", ".idea", ".vscode", ".dart_tool", ".next", ".nuxt", "coverage",
    ".pytest_cache", ".mypy_cache", ".ai", ".claude",
}
CODE_EXT = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".vue", ".dart", ".java", ".kt", ".c", ".cc",
    ".cpp", ".h", ".hpp", ".cu", ".go", ".rs", ".cs", ".swift", ".sql",
}
DOC_EXT = {".md", ".tex", ".pdf", ".docx", ".pptx", ".hwp", ".hwpx"}
DOC_DIR_HINTS = {"docs", "doc", "papers", "paper", "patents", "patent", "reports", "report", "specs"}
ENTRY_CANDIDATES = [
    "main.py", "app.py", "manage.py", "wsgi.py", "asgi.py", "server.py", "cli.py",
    "src/main.py", "src/main.ts", "src/main.js", "src/index.ts", "src/index.js", "index.js",
    "src/main.cpp", "main.cpp", "src/main.rs", "main.go", "cmd/main.go", "lib/main.dart",
    "src/App.vue", "src/App.tsx", "src/App.jsx",
]


def walk(root: Path):
    """Yield (relative path, is_code, is_doc) with directory pruning."""
    for cur, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in PRUNE_DIRS]
        for name in files:
            p = Path(cur) / name
            ext = p.suffix.lower()
            yield p.relative_to(root), ext in CODE_EXT, ext in DOC_EXT


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []


def detect_node(root: Path, found: dict) -> None:
    pkg = root / "package.json"
    if not pkg.exists():
        return
    data = read_json(pkg)
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    names = []
    for key, label in (("vue", "Vue"), ("nuxt", "Nuxt"), ("react", "React"), ("next", "Next.js"),
                       ("svelte", "Svelte"), ("express", "Express"), ("@nestjs/core", "NestJS"),
                       ("typescript", "TypeScript"), ("vite", "Vite")):
        if key in deps:
            ver = str(deps[key]).lstrip("^~")
            names.append(f"{label} {ver}")
    if (root / "pnpm-lock.yaml").exists():
        pm = "pnpm"
    elif (root / "yarn.lock").exists():
        pm = "yarn"
    elif (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        pm = "bun"
    else:
        pm = "npm"
    scripts = data.get("scripts", {})
    run = "npm run" if pm == "npm" else pm
    cmds = {}
    for k in ("test", "build", "lint", "dev"):
        if k in scripts:
            cmds[k] = f"{run} {k}" if k != "test" or pm != "npm" else "npm test"
    found["stacks"].append({"name": "Node/JS (" + ", ".join(names) + ")" if names else "Node/JS",
                            "pm": pm, "cmds": cmds, "deps": sorted(deps)[:15],
                            "main": data.get("main")})


def detect_python(root: Path, found: dict) -> None:
    has_req = (root / "requirements.txt").exists()
    has_py = (root / "pyproject.toml").exists()
    if not (has_req or has_py or (root / "setup.py").exists()):
        return
    deps: list[str] = []
    if has_req:
        deps += [l.split("==")[0].split(">=")[0].strip() for l in read_lines(root / "requirements.txt")
                 if l.strip() and not l.startswith(("#", "-"))]
    if has_py:
        try:
            import tomllib  # py3.11+
            data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8", errors="ignore"))
            for d in data.get("project", {}).get("dependencies", []):
                deps.append(d.split(";")[0].split("[")[0].split(">")[0].split("=")[0].split("<")[0].strip())
        except Exception:
            pass
    low = {d.lower() for d in deps}
    names = [label for key, label in (("torch", "PyTorch"), ("fastapi", "FastAPI"), ("django", "Django"),
                                       ("flask", "Flask"), ("numpy", "NumPy"), ("pytest", "pytest"))
             if key in low]
    pm = "uv" if (root / "uv.lock").exists() else "poetry" if (root / "poetry.lock").exists() else "pip"
    found["stacks"].append({"name": "Python (" + ", ".join(names) + ")" if names else "Python",
                            "pm": pm, "cmds": {"test": "pytest"}, "deps": sorted(set(deps))[:15]})


def detect_others(root: Path, found: dict) -> None:
    if (root / "pubspec.yaml").exists():
        found["stacks"].append({"name": "Flutter/Dart", "pm": "pub", "cmds": {"test": "flutter test"}, "deps": []})
    if (root / "CMakeLists.txt").exists():
        found["stacks"].append({"name": "C/C++ (CMake)", "pm": "cmake",
                                "cmds": {"build": "cmake -S . -B build && cmake --build build",
                                         "test": "ctest --test-dir build --output-on-failure"}, "deps": []})
    if (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
        found["stacks"].append({"name": "Java/Kotlin (Gradle)", "pm": "gradle",
                                "cmds": {"test": "./gradlew test"}, "deps": []})
    elif (root / "pom.xml").exists():
        found["stacks"].append({"name": "Java (Maven)", "pm": "maven", "cmds": {"test": "mvn test"}, "deps": []})
    if (root / "go.mod").exists():
        found["stacks"].append({"name": "Go", "pm": "go", "cmds": {"test": "go test ./..."}, "deps": []})
    if (root / "Cargo.toml").exists():
        found["stacks"].append({"name": "Rust", "pm": "cargo", "cmds": {"test": "cargo test"}, "deps": []})
    if list(root.glob("*.ipynb")) or (root / "notebooks").is_dir():
        found["notes"].append("Jupyter notebooks present: run-all exit code can serve as the deterministic check.")


def scan(root: Path) -> dict:
    found: dict = {"stacks": [], "notes": [], "entries": [], "docs": {}, "doc_dirs": [], "code_files": 0}
    detect_node(root, found)
    detect_python(root, found)
    detect_others(root, found)

    doc_counts: dict[str, int] = {}
    doc_dirs: set[str] = set()
    for rel, is_code, is_doc in walk(root):
        if is_code:
            found["code_files"] += 1
        if is_doc and rel.name.upper() != "CLAUDE.MD":
            doc_counts[rel.suffix.lower()] = doc_counts.get(rel.suffix.lower(), 0) + 1
        if rel.parts and rel.parts[0].lower() in DOC_DIR_HINTS and len(rel.parts) > 1:
            doc_dirs.add(rel.parts[0])
    found["docs"] = doc_counts
    found["doc_dirs"] = sorted(doc_dirs)
    found["entries"] = [e for e in ENTRY_CANDIDATES if (root / e).exists()]
    return found


STR = {
    "kr": {
        "ctx": "## 자동 감지한 컨텍스트", "mode": "- 모드: {mode} (소스 파일 {n}개)", "lang": "- 지침 언어: kr (원본 lang/kr)",
        "stack": "- 스택: {name} | 패키지 관리자: {pm}", "nostack": "- 스택: 감지하지 못함 (직접 채울 것)",
        "cmds": "## 명령 (완료라고 하기 전에 검사를 실행하고 종료 코드를 보여 줄 것)",
        "nocmd": "- 테스트/빌드 명령을 감지하지 못함. 첫 코드 변경 전에 하나를 정해 이 블록 밖 `## 프로젝트 명령`에 적을 것(블록은 다시 만들어지면 덮어쓰인다).",
        "assetref": "- 스택 상세, 진입점, 문서·연구 자산(개수·유형): `.ai/repo_audit_map.md`. 보고서/논문/특허는 그 자산을 근거로 인용하고 숫자는 출처와 일치해야 한다.",
        "rules": "## 작업 규칙",
        "first": "- 첫 진입: 코드를 고치기 전에 explorer를 실행해 `.ai/repo_audit_map.md`를 완성할 것.",
        "preset": "- 프리셋: {name}. 구조와 서브에이전트 배정: `.claude/rules/dispatch.md`.",
        "surgical": "- 최소 변경만: 요청 밖의 코드는 포맷하거나 건드리지 말 것.",
        "nocd": "- Bash에서 `cd`로 작업 폴더를 옮기지 않는다. 명령은 프로젝트 루트 기준 경로로 실행한다(`git -C`, `--root`, 경로 인자 사용).",
        "loop": "- 작업마다 루프 계약: 성공 기준, 검증자, 중단 조건 (스킬 참고).",
        "mem": "- 메모리 위생(.ai/memory/*.md): 파일당 {ml}줄 이하이고 한 줄은 {mc}자 이하. 끝난 항목은 archive/로 옮기고 긴 줄은 나눌 것.",
        "memrules": ("<!-- 규칙: 파일당 최대 {ml}줄(목표 50~100줄), 한 줄 최대 {mc}자, 한 줄에 사실 하나. -->\n"
                     "<!-- 끝났거나 낡은 항목은 archive/로 옮김. 점검: python init_project.py --check-memory -->\n"),
        "intent": "- 목표·범위·주요 결정: `.ai/INTENT.md`. 변경은 제안하고 사용자 승인 후 반영할 것.",
        "blueprint": "- 신규 구현이고 `.ai/BLUEPRINT.md`(설계서)가 없으면 코딩 전에 `/blueprint`로 설계서부터 만든다(승인 전 코딩 금지). 있으면 구현 전에 읽고, 설계서에 없는 기능·화면·표는 넣지 않는다.",
        "intent_tpl": ("# INTENT\n\n<!-- 프로젝트 공유 파일: 목표와 범위. 60줄 이하, 한 줄에 사실 하나. 변경은 제안 후 사용자 승인. -->\n\n"
                       "## 목표 한 줄\n- [TODO: 끝나면 무엇이 참인가]\n\n## 범위\n- 안: [TODO]\n- 밖: [TODO]\n\n"
                       "## 제약\n- [TODO]\n\n## 주요 결정\n- kb decision 카드로 관리한다(`.ai/INDEX.md`의 decision 절).\n\n"
                       "## 열린 질문\n- (없음)\n\n## 완료 확인\n- [TODO: 명령 또는 확인 방법]\n"),
        "kb": ["- 기억(kb): 세션 시작 때 주입되는 `.ai/NOW.md`(현재 상태)와 `.ai/INDEX.md`(카드 목차)로 위치를 잡고 필요한 카드만 연다. "
               "모르는 정보는 `python .ai/kb.py search \"키워드\"`를 먼저 하고 결과의 줄 범위만 읽는다. archive·docs를 통째로 읽지 않는다.",
               "- 기록: 작업 끝에 NOW.md(10줄 이하, 다음 행동 1~2개는 승인 전 착수 금지)와 progress 카드 체크를 갱신하고, "
               "새 결정·이슈는 `python .ai/kb.py new decision|issue --title \"...\"`로 카드 하나씩(40줄 이하) 만든다. 바뀐 결정은 기존 카드를 superseded로.",
               "- 새 문서·이미지·스크립트·템플릿은 `python .ai/kb.py new asset <경로>`로 등록한다. 진행 상태의 기준은 progress 카드다(TodoWrite·Notion 체크리스트는 보조, 다르면 카드가 우선).",
               "- 마무리 전 `python .ai/kb.py check`, 작업 요약 요청은 `python .ai/kb.py wrapup`."],
        "legacy_mem": "- 이전 메모리 `.ai/memory/`는 카드로 옮기는 중이다. 새 기록은 kb에만 하고, 옮긴 뒤 `kb.py check --coverage`로 누락을 확인한다.",
        "now_tpl": "# NOW\n<!-- 현재 상태 10줄 이하. 카드는 [[id]]로 가리킨다. 작업 끝마다 갱신. -->\n- 진행: (없음)\n- 다음 행동: (없음, 승인 전 착수 금지)\n- 막힌 것: 없음\n",
        "agents_md": ["# AGENTS.md",
                      "Codex·Gemini 등 다른 AI 도구용 짧은 안내다. Claude Code는 CLAUDE.md를 쓴다.",
                      "- 한국어로 답한다. 모호하면 먼저 묻고, 확인하지 못한 수치·사실은 `UNVERIFIED: <무엇>`으로 적는다.",
                      "- 사용자 승인 없이 커밋·푸시·배포·파일 삭제·외부 전송을 하지 않는다. .env·키·인증서를 읽지 않는다.",
                      "- 현재 상태 `.ai/NOW.md`, 목차 `.ai/INDEX.md`. 파일을 통째로 읽기 전에 `python .ai/kb.py search \"키워드\"`.",
                      "- 작업 끝: NOW.md와 progress 카드 갱신, 새 결정·이슈는 `python .ai/kb.py new decision|issue --title \"...\"`.",
                      "- 테스트·빌드 명령과 작업 규칙: `CLAUDE.md`의 AI-INIT 블록.",
                      "- Windows: 긴 명령은 `.ai/scripts/`에 저장해 실행, 대괄호 경로는 `-LiteralPath`, 한글 파일은 UTF-8."],
        "nostk": "| (감지된 것 없음) | - | - |", "noent": "- (일치하는 것 없음. explorer가 찾아야 함)", "nodoc": "없음",
        "notpl": "# repo_audit_map\n\n(템플릿을 찾지 못함: {path})\n",
    },
    "en": {
        "ctx": "## Auto-detected context", "mode": "- Mode: {mode} ({n} source files)", "lang": "- Instruction language: en (source lang/en)",
        "stack": "- Stack: {name} | package manager: {pm}", "nostack": "- Stack: not detected (fill in manually)",
        "cmds": "## Commands (run the check before claiming done; show the exit code)",
        "nocmd": "- no test/build command detected. Before the first code change, define one and write it under `## Project commands` outside this block (the block is regenerated and overwritten).",
        "assetref": "- Stack details, entry points, docs/research assets (counts, types): `.ai/repo_audit_map.md`. Reports/papers/patents cite those assets as evidence; numbers must match the source.",
        "rules": "## Working rules",
        "first": "- First entry: run the explorer and complete `.ai/repo_audit_map.md` before editing code.",
        "preset": "- Preset: {name}. Structure and sub-agent routing: `.claude/rules/dispatch.md`.",
        "surgical": "- Surgical changes only: do not reformat or touch code outside the request.",
        "nocd": "- Do not `cd` to another folder in Bash. Run commands with paths relative to the project root (use `git -C`, `--root`, path arguments).",
        "loop": "- Loop contract per task: success criterion, verifier, stop condition (see skills).",
        "mem": "- Memory hygiene (.ai/memory/*.md): at most {ml} lines per file AND at most {mc} characters per line. Archive finished items; split long lines.",
        "memrules": ("<!-- Rules: max {ml} lines per file (aim 50-100), max {mc} chars per line, one fact per line. -->\n"
                     "<!-- Move finished or stale items to archive/. Check: python init_project.py --check-memory -->\n"),
        "intent": "- Goal, scope, major decisions: `.ai/INTENT.md`. Propose changes and apply them only after user approval.",
        "blueprint": "- For a new build without `.ai/BLUEPRINT.md` (the 설계서), create it with `/blueprint` before coding (no coding before approval). If it exists, read it before implementing and add no feature, screen or table that is not in it.",
        "intent_tpl": ("# INTENT\n\n<!-- Project-shared file: goal and scope. At most 60 lines, one fact per line. Changes: propose, then user approval. -->\n\n"
                       "## One-line goal\n- [TODO: what is true when this is done]\n\n## Scope\n- In: [TODO]\n- Out: [TODO]\n\n"
                       "## Constraints\n- [TODO]\n\n## Major decisions\n- Kept as kb decision cards (decision section of `.ai/INDEX.md`).\n\n"
                       "## Open questions\n- (none)\n\n## Done check\n- [TODO: command or way to confirm]\n"),
        "kb": ["- Memory (kb): orient with the injected `.ai/NOW.md` (current state) and `.ai/INDEX.md` (card index); open only the cards you need. "
               "For anything else run `python .ai/kb.py search \"words\"` first and read only the returned line range. Never read archive/docs whole.",
               "- Record: at the end of a task update NOW.md (10 lines max; next 1-2 actions wait for approval) and the progress card checklist; "
               "each new decision/issue becomes one card via `python .ai/kb.py new decision|issue --title \"...\"` (40 lines max). A changed decision marks the old card superseded.",
               "- Register new docs, images, scripts and templates with `python .ai/kb.py new asset <path>`. Progress cards are the source of truth (TodoWrite/Notion checklists are secondary; on conflict the card wins).",
               "- Before finishing run `python .ai/kb.py check`; for a work summary run `python .ai/kb.py wrapup`."],
        "legacy_mem": "- Old memory in `.ai/memory/` is being moved into cards. Record only in kb; afterwards confirm with `kb.py check --coverage`.",
        "now_tpl": "# NOW\n<!-- Current state, at most 10 lines. Point to cards with [[id]]. Update at the end of each task. -->\n- Doing: (none)\n- Next action: (none; wait for approval)\n- Blocked: no\n",
        "agents_md": ["# AGENTS.md",
                      "Short guide for other AI tools (Codex, Gemini). Claude Code uses CLAUDE.md.",
                      "- Answer in Korean. Ask when unclear; write unverified numbers or facts as `UNVERIFIED: <what>`.",
                      "- No commit, push, deploy, file deletion or external sending without user approval. Do not read .env, keys or certificates.",
                      "- Current state `.ai/NOW.md`, index `.ai/INDEX.md`. Before reading a whole file, `python .ai/kb.py search \"words\"`.",
                      "- End of task: update NOW.md and the progress card; new decisions/issues via `python .ai/kb.py new decision|issue --title \"...\"`.",
                      "- Test/build commands and working rules: the AI-INIT block in `CLAUDE.md`.",
                      "- Windows: save long commands under `.ai/scripts/` and run them, use `-LiteralPath` for bracketed paths, read/write Korean files as UTF-8."],
        "nostk": "| (none detected) | - | - |", "noent": "- (none matched; explorer must locate)", "nodoc": "none",
        "notpl": "# repo_audit_map\n\n(template not found: {path})\n",
    },
}


def needs_audit_map(found: dict, mode: str) -> bool:
    """v2.1: asset counts moved out of CLAUDE.md, so every project that has something to record gets the map.
    Legacy codebases always; otherwise only when docs/research assets are present (doc folder or 3+ files)."""
    return mode == "legacy" or bool(found["doc_dirs"]) or sum(found["docs"].values()) >= 3


def render_block(found: dict, mode: str, lang: str = "kr") -> str:
    t = STR[lang]
    lines = [BEGIN, t["ctx"]]
    lines.append(t["mode"].format(mode=mode, n=found["code_files"]))
    lines.append(t["lang"])
    if found["stacks"]:
        for s in found["stacks"]:
            lines.append(t["stack"].format(name=s["name"], pm=s["pm"]))
    else:
        lines.append(t["nostack"])
    lines.append(t["cmds"])
    any_cmd = False
    for s in found["stacks"]:
        for k, v in s["cmds"].items():
            lines.append(f"- {k}: `{v}`  # {s['name'].split(' (')[0]}")
            any_cmd = True
    if not any_cmd:
        lines.append(t["nocmd"])
    lines.append(t["rules"])
    if found.get("audit_map"):
        lines.append(t["assetref"])
    if mode == "legacy":
        lines.append(t["first"])
    if found.get("preset"):
        lines.append(t["preset"].format(name=found["preset"]))
    lines.append(t["intent"])
    if found.get("blueprint"):
        lines.append(t["blueprint"])
    lines.append(t["surgical"])
    lines.append(t["nocd"])
    lines.append(t["loop"])
    lines.extend(t["kb"])
    if found.get("legacy_memory"):
        lines.append(t["legacy_mem"])
    lines.append(END)
    return "\n".join(lines) + "\n"


def lang_dir(src: Path, lang: str) -> Path:
    return src / "lang" / lang


def merge_claude_md(path: Path, block: str) -> str:
    """Replace the managed block if present, else append. Never touch other text."""
    if not path.exists():
        return "# Project instructions\n\n" + block
    text = path.read_text(encoding="utf-8", errors="ignore")
    if BEGIN in text and END in text:
        head, rest = text.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        return head + block.rstrip("\n") + tail
    sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    return text + sep + block


def render_audit_map(found: dict, root: Path, template: Path | None, lang: str = "kr") -> str:
    if template and template.exists():
        base = template.read_text(encoding="utf-8")
    else:
        base = STR[lang]["notpl"].format(path=template)
    stacks = "\n".join(f"| {s['name']} | {s['pm']} | {', '.join(s['deps'][:8]) or '-'} |" for s in found["stacks"]) \
        or STR[lang]["nostk"]
    entries = "\n".join(f"- `{e}`" for e in found["entries"]) or STR[lang]["noent"]
    docs = ", ".join(f"{ext} {n}" for ext, n in sorted(found["docs"].items())) or STR[lang]["nodoc"]
    base = base.replace("{{PROJECT}}", root.resolve().name)
    base = base.replace("{{STACK_ROWS}}", stacks)
    base = base.replace("{{ENTRY_ROWS}}", entries)
    base = base.replace("{{DOC_SUMMARY}}", docs)
    base = base.replace("{{CODE_FILES}}", str(found["code_files"]))
    return base


def load_roster(path: Path | None, src_dir: Path) -> dict:
    """Read roster.yaml (PyYAML). Without PyYAML fall back to backup/roster.json, warning if it looks stale."""
    if path and path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    yml = path or src_dir / "roster.yaml"
    try:
        import yaml  # type: ignore
    except ImportError:
        bak = src_dir / "backup" / "roster.json"
        if not bak.exists():
            raise SystemExit("error: PyYAML missing and no backup/roster.json. "
                             "Run: python -m pip install --user -r requirements.txt  (or python setup_env.py)")
        stale = yml.exists() and yml.stat().st_mtime > bak.stat().st_mtime
        print("warning: PyYAML not installed; using backup/roster.json"
              + (" (OLDER than roster.yaml; run setup_env.py --export-backup on a PC with PyYAML)" if stale else "")
              + ". Install: python -m pip install --user -r requirements.txt", file=sys.stderr)
        return json.loads(bak.read_text(encoding="utf-8"))
    return yaml.safe_load(yml.read_text(encoding="utf-8"))


def resolve_preset(roster: dict, name: str) -> dict:
    """Resolve 'extends' chain. Lists concatenate (parent first) and de-duplicate; 'remove' subtracts."""
    presets = roster.get("presets", {})
    if name not in presets:
        raise SystemExit(f"error: preset '{name}' not found. available: {', '.join(sorted(presets))}")
    chain, seen, cur = [], set(), name
    while cur:
        if cur in seen:
            raise SystemExit(f"error: circular extends at '{cur}'")
        seen.add(cur)
        chain.append(presets[cur])
        cur = presets[cur].get("extends")
    out: dict = {"skills": [], "agents": [], "rules": [], "knowledge": [], "hooks": [], "account_skills": [],
                 "mcp": [], "gates": [], "notes": []}
    for node in reversed(chain):  # base first
        for key in out:
            val = node.get(key, [])
            val = [val] if isinstance(val, str) else val
            for item in val:
                if item not in out[key]:
                    out[key].append(item)
        for key, items in node.get("remove", {}).items():
            out[key] = [x for x in out.get(key, []) if x not in items]
        if node.get("init_mode"):
            out["init_mode"] = node["init_mode"]
    return out


def apply_preset(root: Path, src: Path, preset: dict, dry: bool, force: bool, lang: str = "kr") -> list[str]:
    """Copy skills/agents/rules from the redesign folder into the project's .claude/."""
    msgs = []
    src = lang_dir(src, lang)
    plan = (("skills", lambda n: (src / "skills" / n / "SKILL.md", root / ".claude" / "skills" / n / "SKILL.md")),
            ("agents", lambda n: (src / "agents" / f"{n}.md", root / ".claude" / "agents" / f"{n}.md")),
            ("rules", lambda n: (src / "rules" / f"{n}.md", root / ".claude" / "rules" / f"{n}.md")),
            ("knowledge", lambda n: (src / "knowledge" / f"{n}.md",
                                     root / ".claude" / "skills" / f"project-{n}" / "SKILL.md")))
    shared = src.parent.parent / "shared" / "skills"
    for kind, mapper in plan:
        for n in preset[kind]:
            s, d = mapper(n)
            pairs = [(s, d)]
            if kind == "skills":  # v2.4: whole skill folder (helper files) + language-independent extras in shared/skills/<n>/
                for base in (s.parent, shared / n):
                    if base.is_dir():
                        pairs += [(f, d.parent / f.relative_to(base)) for f in sorted(base.rglob("*"))
                                  if f.is_file() and f.name != "SKILL.md" and "__pycache__" not in f.parts]
            for s2, d2 in pairs:
                if not s2.exists():
                    msgs.append(f"skip {kind}/{n}: source not found ({s2})")
                elif d2.exists() and not force:
                    msgs.append(f"kept existing {d2} (use --force to overwrite)")
                elif dry:
                    msgs.append(f"[dry-run] would copy {s2.name} -> {d2}")
                else:
                    d2.parent.mkdir(parents=True, exist_ok=True)
                    if s2.suffix in (".md", ".py", ".txt", ".json"):
                        text = s2.read_text(encoding="utf-8")
                        if kind == "agents":  # v2.4.1: agent-scoped hooks get an absolute path (survive a `cd` in the session)
                            text = re.sub(r'command:\s*"python \.claude/hooks/([\w.-]+\.py)"',
                                          lambda m: "command: 'python \"" + root.resolve().as_posix() + "/.claude/hooks/" + m.group(1) + "\"'", text)
                        d2.write_bytes(text.encode("utf-8"))
                    else:
                        shutil.copy2(s2, d2)
                    msgs.append(f"copied {d2}")
    if preset["knowledge"]:
        msgs.append("knowledge stubs are INACTIVE (disable-model-invocation: true). Fill in the [TODO] lines, then delete "
                    "that frontmatter line so Claude can load them; delete a stub you do not need.")
    if preset["hooks"]:
        msgs.append("hooks for this preset (merge_settings.py copies the scripts and registers block_dangerous + kb; "
                    "others stay manual via settings.snippet.json): " + ", ".join(preset["hooks"]))
    if preset["account_skills"]:
        msgs.append("account skills to keep enabled for this preset: " + ", ".join(preset["account_skills"]))
    if preset["mcp"]:
        msgs.append("MCP for this preset only: " + ", ".join(preset["mcp"]))
    if preset["gates"]:
        msgs.append("human approval gates: " + ", ".join(preset["gates"]))
    for n in preset["notes"]:
        msgs.append("note: " + n)
    return msgs


def verify_manifest(base: Path, manifest: Path, items: list) -> list:
    """v2.4.5: sha256 check of the files an external skill copy will use. Returns a list of problems (empty = OK)."""
    import hashlib
    if not manifest.is_file():
        return [f"manifest not found: {manifest}"]
    want = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, _, rel = line.partition("  ")
            want[rel.strip()] = h.strip()
    bad = []
    for it in items:
        p = base / it
        files = [p] if p.is_file() else sorted(f for f in p.rglob("*") if f.is_file() and "__pycache__" not in f.parts)
        if not files:
            bad.append(f"nothing to copy for {it}")
        for f in files:
            rel = f.relative_to(base).as_posix()
            if rel not in want:
                bad.append(f"not in manifest: {rel}")
            elif hashlib.sha256(f.read_bytes()).hexdigest() != want[rel]:
                bad.append(f"sha256 mismatch: {rel}")
    return bad


def apply_external(root: Path, src_dir: Path, name: str, spec: dict, dry: bool, force: bool, lang: str) -> int:
    """v2.4.5: install one pinned external skill (third_party/...) into <root>/.claude/skills/<skill>/.
    SKILL.md is our own short one from lang/<lang>/skills/<skill>/; the vendor files listed in `copy` are verified against
    the manifest first. Additive: existing files are kept unless --force."""
    base = src_dir / spec["source"]
    items = list(spec.get("copy", []))
    if not base.is_dir():
        print(f"error: pinned source missing: {base}", file=sys.stderr)
        return 2
    own_rel = spec.get("own")  # v2.4.6: our narrowed SKILL.md lives inside the pinned folder (and is covered by its manifest)
    bad = verify_manifest(base, src_dir / spec["manifest"], items + ([own_rel] if own_rel else []))
    if bad:
        print("error: integrity check failed, nothing copied:\n  " + "\n  ".join(bad[:10]), file=sys.stderr)
        return 2
    skill = spec["skill"]
    own = (base / own_rel) if own_rel else lang_dir(src_dir, lang) / "skills" / skill / "SKILL.md"
    if not own.is_file():
        print(f"error: our SKILL.md not found: {own}", file=sys.stderr)
        return 2
    dest = root / ".claude" / "skills" / skill
    pairs = [(own, dest / "SKILL.md")]
    for it in items:
        p = base / it
        files = [p] if p.is_file() else sorted(f for f in p.rglob("*") if f.is_file() and "__pycache__" not in f.parts)
        pairs += [(f, dest / f.relative_to(base)) for f in files]
    n_new = n_keep = 0
    for s, d in pairs:
        if d.exists() and not force:
            n_keep += 1
        elif dry:
            n_new += 1
        else:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
            n_new += 1
    verb = "would copy" if dry else "copied"
    print(f"{verb} {n_new} file(s) into {dest}; kept {n_keep} existing (integrity verified against the manifest)")
    for n in spec.get("notes", []):
        print("note: " + n)
    print("dry run only; nothing written." if dry else "done.")
    return 0


def check_memory(root: Path, max_lines: int, max_chars: int) -> int:
    """Read-only lint of .ai/memory/*.md (archive/ is skipped). Returns 0 if clean, 1 if violations."""
    mem = root / ".ai" / "memory"
    if not mem.is_dir():
        print(f"no memory folder: {mem}")
        return 0
    bad = 0
    for f in sorted(mem.glob("*.md")):
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        long_lines = [(i, len(l)) for i, l in enumerate(lines, 1) if len(l) > max_chars]
        problems = []
        if len(lines) > max_lines:
            problems.append(f"{len(lines)} lines (max {max_lines})")
        if long_lines:
            first = ", ".join(f"L{i}={n}" for i, n in long_lines[:5])
            more = f" (+{len(long_lines) - 5} more)" if len(long_lines) > 5 else ""
            problems.append(f"{len(long_lines)} line(s) over {max_chars} chars: {first}{more}")
        longest = max((len(l) for l in lines), default=0)
        status = "OK  " if not problems else "FAIL"
        print(f"{status} {f.name}: {len(lines)} lines, longest {longest} chars" + ("; " + "; ".join(problems) if problems else ""))
        bad += bool(problems)
    print("memory check: " + ("clean" if not bad else f"{bad} file(s) need cleanup (archive old items, split long lines)"))
    return 1 if bad else 0


def check_lang(src: Path) -> int:
    """Compare lang/en and lang/kr: same files, same frontmatter (name/description/tools/model), same
    decision tokens and placeholders, same heading count. Translation quality is NOT checked."""
    import re
    en, kr = lang_dir(src, "en"), lang_dir(src, "kr")
    tokens = ["PASS", "FAIL", "MATCH", "MISMATCH", "NO SOURCE", "COMPLETE", "PARTIAL", "BLOCKED", "UNKNOWN",
              "ASSUMPTION", "UNVERIFIED", "Proposed", "Accepted", "Superseded", "[TODO", "[auto"]
    fe = {p.relative_to(en).as_posix() for p in en.rglob("*.md")}
    fk = {p.relative_to(kr).as_posix() for p in kr.rglob("*.md")}
    bad = []
    for f in sorted(fe - fk):
        bad.append(f"{f}: missing in kr")
    for f in sorted(fk - fe):
        bad.append(f"{f}: missing in en")
    for f in sorted(fe & fk):
        a = (en / f).read_text(encoding="utf-8")
        b = (kr / f).read_text(encoding="utf-8")
        def front(t):
            m = re.match(r"---\n(.*?)\n---", t, re.S)
            return m.group(1) if m else ""
        if front(a) != front(b):
            bad.append(f"{f}: frontmatter differs (name/description/tools/model must be identical)")
        for tk in tokens:
            if (tk in a) != (tk in b):
                bad.append(f"{f}: token {tk!r} present in only one language")
        if sorted(re.findall(r"\{\{\w+\}\}", a)) != sorted(re.findall(r"\{\{\w+\}\}", b)):
            bad.append(f"{f}: {{{{placeholders}}}} differ")
        if len(re.findall(r"^#{1,3} ", a, re.M)) != len(re.findall(r"^#{1,3} ", b, re.M)):
            bad.append(f"{f}: heading count differs")
    for line in bad:
        print("DIFF " + line)
    print(f"lang check: {len(fe & fk)} file(s) compared, " + ("consistent" if not bad else f"{len(bad)} difference(s)"))
    return 1 if bad else 0


def write(path: Path, content: str, dry: bool, existed_ok: bool = True) -> str:
    """v2.4: if the file is hard-linked (old v8 CLAUDE.md = AGENTS.md = GEMINI.md), write a new file and swap it in,
    so the other names keep their old content instead of silently receiving this text."""
    links = 1
    try:
        links = path.stat().st_nlink if path.exists() else 1
    except OSError:
        pass
    note = f" (was hard-linked x{links}; link broken, other names unchanged)" if links > 1 else ""
    if dry:
        return f"[dry-run] would write {path}{note}"
    path.parent.mkdir(parents=True, exist_ok=True)
    if links > 1:
        tmp = path.with_name(path.name + ".tmp_init")
        tmp.write_bytes((content).encode("utf-8"))
        os.replace(tmp, path)
    else:
        path.write_bytes((content).encode("utf-8"))
    return f"wrote {path}{note}"


def detect_v8(root: Path) -> list:
    """Signs that the old AI Control v8 system (switch-ai / refresh-ai) still manages this project."""
    hits = []
    cm = root / "CLAUDE.md"
    if cm.exists():
        head = cm.read_text(encoding="utf-8-sig", errors="ignore")[:4000]
        if any(m in head for m in V8_MARKERS):
            hits.append("CLAUDE.md is a v8 merged profile")
    for rel_ in (".ai/.mode", ".ai/system_prompt.md", ".ai/profiles"):
        if (root / rel_).exists():
            hits.append(rel_ + " exists")
    return hits


def setup_kb(root: Path, src_dir: Path, found: dict, lang: str, dry: bool) -> list:
    """v2.4 card memory: folders, NOW.md, kb.json, kb.py (managed copy), INDEX.md."""
    out = []
    ai = root / ".ai"
    if not dry:
        for t in KB_TYPES:
            (ai / "kb" / t).mkdir(parents=True, exist_ok=True)
        (ai / "archive").mkdir(parents=True, exist_ok=True)
    now = ai / "NOW.md"
    if not now.exists():
        out.append(write(now, STR[lang]["now_tpl"], dry))
    cfg = ai / "kb.json"
    if not cfg.exists():
        dirs = [d for d in dict.fromkeys(found.get("doc_dirs", []) + ["docs", "design", ".ai/scripts", ".ai/design", ".ai/manuals"])
                if (root / d).is_dir()]
        body = {"lang": lang, "asset_dirs": dirs or ["docs"], "search_dirs": [d for d in dirs if not d.startswith(".ai/")] or ["docs"],
                "search_exclude": [], "graphify_out": "graphify-out", "graph_in_search": False}
        out.append(write(cfg, json.dumps(body, ensure_ascii=False, indent=2) + "\n", dry))
    srckb = src_dir / "kb" / "kb.py"
    dst = ai / "kb.py"
    if srckb.exists():
        new = srckb.read_text(encoding="utf-8")
        cur = dst.read_text(encoding="utf-8", errors="ignore") if dst.exists() else None
        if cur is None or (cur != new and KB_MARK in cur):
            out.append(write(dst, new, dry))
        elif cur != new:
            out.append(f"kept {dst} (no '{KB_MARK}' marker: locally edited)")
        if not dry:
            r = subprocess.run([sys.executable, str(dst), "--root", str(root), "build"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            out.append((r.stdout or r.stderr).strip() or "kb build: no output")
    else:
        out.append(f"skip kb.py: source not found ({srckb})")
    return out


def write_agents_md(root: Path, lang: str, dry: bool) -> str:
    """Short pointer for Codex/Gemini (Claude Code does not load AGENTS.md). Managed block; text outside is kept."""
    p = root / "AGENTS.md"
    lines = STR[lang]["agents_md"]
    block = BEGIN + "\n" + "\n".join(lines[2:]) + "\n" + END + "\n"
    if p.exists():
        txt = p.read_text(encoding="utf-8-sig", errors="ignore")
        if any(m in txt[:4000] for m in V8_MARKERS):
            return f"kept {p}: still the v8 profile (run migrate_v8.py first)"
        if BEGIN in txt and END in txt:
            head, rest = txt.split(BEGIN, 1)
            _, tail = rest.split(END, 1)
            return write(p, head + block.rstrip("\n") + tail, dry)
        return write(p, txt.rstrip("\n") + "\n\n" + block, dry)
    return write(p, lines[0] + "\n" + lines[1] + "\n\n" + block, dry)


def write_design(root: Path, src_dir: Path, lang: str, dry: bool) -> str:
    p = root / ".ai" / "design" / "DESIGN.md"
    if p.exists():
        return f"kept existing {p}"
    tpl = lang_dir(src_dir, lang) / "DESIGN.template.md"
    if not tpl.exists():
        return f"skip DESIGN.md: template not found ({tpl})"
    base = (src_dir / "design" / "default.DESIGN.md").resolve()
    text = tpl.read_text(encoding="utf-8").replace("{{PROJECT}}", root.resolve().name).replace("{{BASE}}", base.as_posix())
    return write(p, text, dry)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="project root (default: current dir)")
    ap.add_argument("--mode", choices=["auto", "new", "legacy"], default="auto")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--template", default=None, help="path to repo_audit_map.template.md")
    ap.add_argument("--preset", default=None, help="preset name from roster.yaml (e.g. legacy-maintenance)")
    ap.add_argument("--roster", default=None, help="path to a roster .yaml/.json (default: roster.yaml next to this script)")
    ap.add_argument("--force", action="store_true", help="overwrite existing .claude files when applying a preset")
    ap.add_argument("--lang", choices=["kr", "en"], default="kr", help="instruction language of skills/agents/rules/templates (default kr)")
    ap.add_argument("--check-lang", action="store_true", help="compare lang/en and lang/kr structure, then exit")
    ap.add_argument("--check-memory", action="store_true", help="lint .ai/memory/*.md for line count and line length, then exit")
    ap.add_argument("--mem-max-lines", type=int, default=MEM_MAX_LINES)
    ap.add_argument("--mem-max-chars", type=int, default=MEM_MAX_CHARS)
    ap.add_argument("--allow-legacy", action="store_true", help="write even if the old v8 system still manages the project (not recommended)")
    ap.add_argument("--stack", default=None,
                    help="comma list of language/framework rule bundles from roster.yaml `stacks:` (e.g. vue-ts,python-ml). "
                         "Without --preset it only copies the bundle's rule files into .claude/rules/ (path-conditional, additive; "
                         "nothing else in the project is touched)")
    ap.add_argument("--ext", default=None,
                    help="install one pinned external skill from roster.yaml `externals:` (e.g. hwpx) into .claude/skills/. "
                         "Additive (existing files kept unless --force); verifies the vendor files against the manifest first")
    ap.add_argument("--skill", default=None,
                    help="comma list of our own skills from lang/<lang>/skills/ (e.g. blueprint,system-architect). Without --preset it "
                         "copies only those skill folders (helper files included) into .claude/skills/; CLAUDE.md, kb and the rest are "
                         "not touched. Additive (existing files kept unless --force)")
    ap.add_argument("--no-agents-md", action="store_true", help="do not create/update the AGENTS.md pointer")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    if args.check_lang:
        return check_lang(Path(__file__).resolve().parent)
    if args.check_memory:
        return check_memory(root, args.mem_max_lines, args.mem_max_chars)

    preset = None
    src_dir = Path(__file__).resolve().parent
    if args.preset:
        roster_path = Path(args.roster) if args.roster else None
        try:
            preset = resolve_preset(load_roster(roster_path, src_dir), args.preset)
        except FileNotFoundError:
            print(f"error: roster not found: {roster_path or src_dir / 'roster.yaml'}", file=sys.stderr)
            return 2

    if args.ext and not args.preset and not args.stack:  # additive mode (v2.4.5): one pinned external skill
        exts = load_roster(Path(args.roster) if args.roster else None, src_dir).get("externals", {})
        if args.ext not in exts:
            print(f"error: unknown external {args.ext!r}. available: {', '.join(sorted(exts)) or '(none)'}", file=sys.stderr)
            return 2
        return apply_external(root, src_dir, args.ext, exts[args.ext], args.dry_run, args.force, args.lang)

    if args.skill is not None and not args.preset and not args.stack:  # additive mode (v2.4.6): only the named skill folders, no CLAUDE.md/kb change
        sdir = lang_dir(src_dir, args.lang) / "skills"
        avail = sorted(p.name for p in sdir.iterdir() if (p / "SKILL.md").is_file()) if sdir.is_dir() else []
        names = [s.strip() for s in args.skill.split(",") if s.strip()]
        bad = [n for n in names if n not in avail]
        if bad or not names:
            print(f"error: unknown skill(s) {bad or args.skill!r}. available: {', '.join(avail) or '(none)'}", file=sys.stderr)
            return 2
        plan = {"skills": list(dict.fromkeys(names)), "agents": [], "rules": [], "knowledge": [], "hooks": [], "account_skills": [],
                "mcp": [], "gates": [], "notes": []}
        print("\n".join(apply_preset(root, src_dir, plan, args.dry_run, args.force, args.lang)))
        print("note: only .claude/skills/ was touched. A preset line or CLAUDE.md hint (e.g. the blueprint line) is not added; "
              "existing files are kept (--force overwrites local edits, diff first).")
        print("done." if not args.dry_run else "dry run only; nothing written.")
        return 0

    if args.stack and not args.preset:  # additive mode (v2.4.4): only the stack rule files, safe for projects already on v2.4
        stacks = load_roster(Path(args.roster) if args.roster else None, src_dir).get("stacks", {})
        names = [s.strip() for s in args.stack.split(",") if s.strip()]
        bad = [n for n in names if n not in stacks]
        if bad:
            print(f"error: unknown stack(s) {bad}. available: {', '.join(sorted(stacks)) or '(none)'}", file=sys.stderr)
            return 2
        rules = []
        for n in names:
            for r in stacks[n].get("rules", []):
                if r not in rules:
                    rules.append(r)
        plan = {"skills": [], "agents": [], "rules": rules, "knowledge": [], "hooks": [], "account_skills": [],
                "mcp": [], "gates": [], "notes": []}
        print("\n".join(apply_preset(root, src_dir, plan, args.dry_run, args.force, args.lang)))
        print("note: existing rule files are kept (no update reaches a project that already has the file; "
              "--force overwrites local edits, diff first).")
        print("done." if not args.dry_run else "dry run only; nothing written.")
        return 0

    v8 = detect_v8(root)
    if v8 and not args.allow_legacy:
        print("error: the old v8 system still manages this project: " + "; ".join(v8), file=sys.stderr)
        print("  1) python migrate_v8.py --root <project>            (dry run: shows the plan)", file=sys.stderr)
        print("  2) python migrate_v8.py --root <project> --apply    (archives v8 files verbatim, removes them, unregisters refresh-ai)", file=sys.stderr)
        print("  3) run init_project.py again. (--allow-legacy skips this check; both rule sets would then load.)", file=sys.stderr)
        return 3

    print(f"scanning {root} ...")
    found = scan(root)
    mode = args.mode if args.mode != "auto" else ("legacy" if found["code_files"] >= 5 else "new")
    if preset and preset.get("init_mode") and args.mode == "auto":
        mode = preset["init_mode"]
    found["preset"] = args.preset if preset else None
    found["blueprint"] = bool(preset and "blueprint" in preset.get("skills", []))
    print(f"stacks: {[s['name'] for s in found['stacks']] or 'none'} | mode: {mode} | "
          f"docs: {sum(found['docs'].values())} | code files: {found['code_files']}")

    out = []
    found["audit_map"] = needs_audit_map(found, mode)
    found["legacy_memory"] = (root / ".ai" / "memory").is_dir() and any((root / ".ai" / "memory").glob("*.md"))
    block = render_block(found, mode, args.lang)
    out.append(write(root / "CLAUDE.md", merge_claude_md(root / "CLAUDE.md", block), args.dry_run))

    out.extend(setup_kb(root, src_dir, found, args.lang, args.dry_run))
    if not args.no_agents_md:
        out.append(write_agents_md(root, args.lang, args.dry_run))
    if preset and "doc-design" in preset.get("skills", []):
        out.append(write_design(root, src_dir, args.lang, args.dry_run))

    intent = root / ".ai" / "INTENT.md"
    if not intent.exists():
        out.append(write(intent, STR[args.lang]["intent_tpl"], args.dry_run))
    else:
        out.append(f"kept existing {intent}")

    if found["audit_map"]:
        target = root / ".ai" / "repo_audit_map.md"
        if target.exists():
            out.append(f"kept existing {target} (delete it to regenerate)")
        else:
            tpl = Path(args.template) if args.template else lang_dir(Path(__file__).resolve().parent, args.lang) / "repo_audit_map.template.md"
            out.append(write(target, render_audit_map(found, root, tpl, args.lang), args.dry_run))

    if preset:
        out.extend(apply_preset(root, src_dir, preset, args.dry_run, args.force, args.lang))
    out.append("next: python " + (src_dir / "merge_settings.py").as_posix() + " <project>  (registers the kb hooks; see settings.snippet.json)")
    if found["legacy_memory"]:
        out.append("note: .ai/memory/ found. Split it into cards (MIGRATION_PROMPT in AI_Tools/kb), then kb.py check --coverage.")

    print("\n".join(out))
    print("done." if not args.dry_run else "dry run only; nothing written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
