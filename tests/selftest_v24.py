#!/usr/bin/env python3
"""selftest_v24.py - offline checks for the v2.4 additions (kb, init_project kb/AGENTS/DESIGN, migrate_v8,
design_extract, merge_settings). Works in temporary folders only. Stdlib only, Python 3.8+.
  python tests/selftest_v24.py        -> last line 'v2.4 selftest: ALL OK (...)' or the failures"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
PY = sys.executable
KB = HERE / "kb" / "kb.py"
fails, n = [], 0


def run(args, cwd=None, inp=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([PY] + [str(a) for a in args], cwd=cwd, input=inp, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    return r.returncode, r.stdout + r.stderr


def ok(cond, label, detail=""):
    global n
    n += 1
    if not cond:
        fails.append(label + (f" :: {detail[-400:]}" if detail else ""))


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((text).encode("utf-8"))


def kb_tests(tmp: Path):
    root = tmp / "kbproj"
    (root / ".ai").mkdir(parents=True)
    (root / ".ai" / "kb.py").write_text(KB.read_text(encoding="utf-8"), encoding="utf-8")
    k = root / ".ai" / "kb.py"
    write(root / "docs" / "spec.md", "# 명세\n## 3.2 위젯 뷰\n위젯은 뷰 순서를 따른다.\n")
    write(root / ".ai" / "NOW.md", "# NOW\n- 진행: [[P-001]]\n")
    c, o = run([k, "new", "progress", "--title", "M8-2 위젯 뷰", "--tags", "M8"])
    ok(c == 0 and (root / ".ai/kb/progress/P-001.md").exists(), "kb new progress", o)
    c, o = run([k, "new", "decision", "--id", "D-M8-L1", "--title", "viewId 필드", "--related", "P-001"])
    ok(c == 0, "kb new decision with explicit id", o)
    c, o = run([k, "new", "decision", "--id", "X-1", "--title", "bad"])
    ok(c == 2, "kb new rejects wrong prefix", o)
    c, o = run([k, "new", "asset", "docs/spec.md", "--title", "명세"])
    ok(c == 0 and (root / ".ai/kb/asset/A-docs-spec.md").exists(), "kb new asset", o)
    idx = (root / ".ai/INDEX.md").read_text(encoding="utf-8")
    ok("[[P-001]]" in idx and "[[D-M8-L1]]" in idx and "docs/spec.md" in idx, "INDEX lists cards", idx)
    c, o = run([k, "search", "위젯을"])
    ok(c == 0 and "docs/spec.md:2-3" in o, "search strips Korean particle and returns line range", o)
    c, o = run([k, "search", "viewId", "--type", "decision"])
    ok(c == 0 and "D-M8-L1" in o and "spec.md" not in o, "search --type limits to cards", o)
    c, o = run([k, "check"])
    ok(c == 0 and "0 error(s)" in o, "check clean project", o)
    write(root / ".ai/kb/issue/I-001.md", "---\nid: I-001\ntype: issue\ntitle: t\nstatus: active\nupdated: 2026-01-01\nrelated: [\"[[NOPE]]\"]\n---\nx\n")
    c, o = run([k, "check"])
    ok(c == 1 and "broken link [[NOPE]]" in o, "check finds broken link", o)
    (root / ".ai/kb/issue/I-001.md").unlink()
    write(root / "docs" / "new.md", "# new\n")
    c, o = run([k, "check"])
    ok("unregistered asset: docs/new.md" in o, "check lists unregistered asset", o)
    write(tmp / "old" / "plan.md", "결정 L1 승인, L9 보류\n")
    c, o = run([k, "check", "--coverage", str(tmp / "old")])
    ok(c == 1 and "MISSING L9" in o and "MISSING L1" not in o, "coverage reports only uncovered ids", o)
    c, o = run([k, "wrapup"])
    rep = list((root / ".ai/archive/reports").glob("*.md"))
    ok(c == 0 and rep and "[[D-M8-L1]]" in rep[0].read_text(encoding="utf-8"), "wrapup writes report", o)
    c, o = run([k, "hook-start"])
    ok(c == 0 and "[kb]" in o and "[[P-001]]" in o and "D-M8-L1" in o, "hook-start prints NOW and INDEX", o)
    before = (root / ".ai/INDEX.md").stat().st_mtime
    write(root / ".ai/kb/map/M-001.md", "---\nid: M-001\ntype: map\ntitle: 지도\nstatus: active\nupdated: 2026-11-13\nrelated: [\"[[P-001]]\"]\n---\nx\n")
    c, o = run([k, "hook-build"], cwd=root, inp=json.dumps({"tool_input": {"file_path": str(root / ".ai/kb/map/M-001.md")}}))
    ok(c == 0 and "[[M-001]]" in (root / ".ai/INDEX.md").read_text(encoding="utf-8"), "hook-build rebuilds INDEX", o)
    c, o = run([k, "hook-build"], cwd=root, inp="not json")
    ok(c == 0, "hook-build never fails", o)
    write(root / ".ai" / "intent" / "intent_openings.md", "# INTENT: 문 여닫이\n여닫이반경 확보가 목표다. 결정 L7 확정.\n")
    c, o = run([k, "search", "여닫이반경"])
    ok(c == 0 and ".ai/intent/intent_openings.md" in o, "search indexes .ai/intent", o)
    write(tmp / "old2" / "plan.md", "결정 L7 승인\n")
    c, o = run([k, "check", "--coverage", str(tmp / "old2")])
    ok(c == 0 and "MISSING L7" not in o, "coverage counts ids written in .ai/intent", o)


def ooxml(path: Path, files: dict):
    with zipfile.ZipFile(path, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)


THEME = ('<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="T"><a:themeElements>'
         '<a:clrScheme name="c"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
         '<a:dk2><a:srgbClr val="0F2A4A"/></a:dk2><a:lt2><a:srgbClr val="EEEEEE"/></a:lt2><a:accent1><a:srgbClr val="123456"/></a:accent1>'
         '<a:accent2><a:srgbClr val="5B7FA6"/></a:accent2><a:accent3><a:srgbClr val="F2A93B"/></a:accent3></a:clrScheme>'
         '<a:fontScheme name="f"><a:majorFont><a:latin typeface="Cambria"/><a:ea typeface=""/><a:font script="Hang" typeface="맑은 고딕"/></a:majorFont>'
         '<a:minorFont><a:latin typeface="Calibri"/><a:ea typeface="나눔고딕"/></a:minorFont></a:fontScheme></a:themeElements></a:theme>')


def design_tests(tmp: Path):
    ex = HERE / "shared" / "skills" / "doc-design" / "design_extract.py"
    pp = tmp / "ref.pptx"
    ooxml(pp, {
        "ppt/presentation.xml": '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldSz cx="12192000" cy="6858000"/></p:presentation>',
        "ppt/slideMasters/slideMaster1.xml": '<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="4000"/></a:lvl1pPr></p:titleStyle><p:bodyStyle><a:lvl1pPr><a:defRPr sz="1600"/></a:lvl1pPr></p:bodyStyle></p:txStyles></p:sldMaster>',
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme2.xml"/></Relationships>',
        "ppt/theme/theme2.xml": THEME,
        "ppt/slideLayouts/slideLayout1.xml": '<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld name="표지"/></p:sldLayout>',
        "ppt/slideLayouts/slideLayout2.xml": '<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld name="본문 2단"/></p:sldLayout>',
    })
    c, o = run([ex, pp])
    ok(c == 0 and "#123456 | accent1" in o and "맑은 고딕" in o and "나눔고딕" in o and "13.33\" x 7.5\"" in o
       and "표지, 본문 2단" in o and "title 40pt" in o, "design_extract pptx (theme via master rels)", o)
    dx = tmp / "ref.docx"
    W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    ooxml(dx, {
        "word/theme/theme1.xml": THEME,
        "word/styles.xml": f'<w:styles {W}><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:asciiTheme="minorHAnsi" w:eastAsiaTheme="minorEastAsia"/><w:sz w:val="22"/></w:rPr></w:rPrDefault></w:docDefaults>'
                           f'<w:style w:styleId="1"><w:name w:val="heading 1"/><w:pPr><w:spacing w:before="480" w:after="120" w:line="276" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Cambria" w:eastAsia="맑은 고딕"/><w:b/><w:sz w:val="36"/><w:color w:val="0F2A4A"/></w:rPr></w:style></w:styles>',
        "word/document.xml": f'<w:document {W}><w:body><w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:bottom="1440" w:left="1800" w:right="1800"/></w:sectPr></w:body></w:document>',
    })
    c, o = run([ex, dx, "--lang", "en"])
    ok(c == 0 and "| Heading 1 | Cambria / 맑은 고딕 | 18pt | Y | #0F2A4A | 24pt/6pt | 1.15 |" in o
       and "Calibri (minorHAnsi) / 나눔고딕 (minorEastAsia), 11pt" in o and "left 1.25\"" in o, "design_extract docx (styles, theme fonts, margins)", o)
    out = tmp / "d" / "x.md"
    c, _ = run([ex, dx, "--out", out])
    c2, o2 = run([ex, dx, "--out", out])
    ok(c == 0 and c2 == 1 and "exists" in o2, "design_extract does not overwrite without --force", o2)
    c, o = run([ex, tmp / "a.png"])
    ok(c == 2, "design_extract refuses images", o)


def init_tests(tmp: Path):
    ip = HERE / "init_project.py"
    p = tmp / "newproj"
    write(p / "docs" / "a.md", "# a\n")
    c, o = run([ip, "--root", p, "--preset", "report-ppt"])
    ok(c == 0, "init report-ppt", o)
    ok((p / ".ai/kb.py").exists() and (p / ".ai/NOW.md").exists() and (p / ".ai/INDEX.md").exists()
       and (p / ".ai/kb/decision").is_dir(), "init creates kb", o)
    ok(not (p / ".ai/memory").exists(), "init no longer creates .ai/memory", o)
    cm = (p / "CLAUDE.md").read_text(encoding="utf-8")
    ok("kb.py search" in cm and "progress 카드" in cm, "CLAUDE.md block has kb rules", cm)
    ag = (p / "AGENTS.md").read_text(encoding="utf-8")
    ok("kb.py search" in ag and len(ag.splitlines()) <= 15, "AGENTS.md pointer, 15 lines max", ag)
    d = (p / ".ai/design/DESIGN.md").read_text(encoding="utf-8")
    ok("base: " in d and "default.DESIGN.md" in d and "{{" not in d, "DESIGN.md with resolved base", d)
    ok((p / ".claude/skills/doc-design/design_extract.py").exists() and (p / ".claude/skills/doc-design/SKILL.md").exists(),
       "doc-design skill folder copied with helper script", o)
    c, o = run([p / ".ai/kb.py", "check"])
    ok(c == 0 and "0 error(s)" in o, "fresh project passes kb check (NOW template comment is not a link)", o)
    cfg = json.loads((p / ".ai/kb.json").read_text(encoding="utf-8"))
    ok("docs" in cfg["asset_dirs"], "kb.json asset_dirs detected", str(cfg))
    kbp = p / ".ai/kb.py"
    kbp.write_text(kbp.read_text(encoding="utf-8") + "\n# old\n", encoding="utf-8")
    c, o = run([ip, "--root", p])
    ok(c == 0 and "# old" not in kbp.read_text(encoding="utf-8"), "managed kb.py refreshed on rerun", o)
    kbp.write_text("print('mine')\n", encoding="utf-8")
    c, o = run([ip, "--root", p])
    ok("print('mine')" in kbp.read_text(encoding="utf-8") and "locally edited" in o, "unmanaged kb.py kept", o)
    # v8 project
    v = tmp / "v8proj"
    write(v / ".ai" / "system_prompt.md", "# [MASTER SYSTEM DIRECTIVE: CORE PROTOCOL v8.0]\nold rules\n")
    write(v / ".ai" / ".mode", "coding")
    write(v / ".ai" / "memory" / "plan.md", "# plan\n## M8\n결정 L3 승인\n")
    for nme in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"):
        try:
            os.link(v / ".ai" / "system_prompt.md", v / nme)
        except OSError:
            write(v / nme, (v / ".ai" / "system_prompt.md").read_text(encoding="utf-8"))
    c, o = run([ip, "--root", v])
    ok(c == 3 and "migrate_v8.py" in o, "init refuses a v8-managed project", o)
    c, o = run([ip, "--root", v, "--allow-legacy", "--no-agents-md"])
    ok(c == 0 and "MASTER SYSTEM DIRECTIVE" in (v / "AGENTS.md").read_text(encoding="utf-8")
       and "AI-INIT:BEGIN" not in (v / "AGENTS.md").read_text(encoding="utf-8"), "hard link broken: AGENTS.md untouched", o)


def migrate_tests(tmp: Path):
    mg = HERE / "migrate_v8.py"
    v = tmp / "v8m"
    write(v / ".ai" / "system_prompt.md", "# [MASTER SYSTEM DIRECTIVE: CORE PROTOCOL v8.0]\nold rules\n")
    write(v / ".ai" / ".mode", "coding")
    write(v / ".ai" / "profiles" / "base.md", "base profile\n")
    try:
        os.symlink(str(tmp / "no_such_central" / "coding.md"), str(v / ".ai" / "profiles" / "coding.md"))
    except (OSError, NotImplementedError):
        pass  # Windows without symlink rights: the broken-link case is skipped
    write(v / ".ai" / "memory" / "plan.md", "# plan\n## M8\n결정 L3 승인\n")
    write(v / ".ai" / "manuals" / "ppt_design_guideline.md", "guide\n")
    for nme in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"):
        try:
            os.link(v / ".ai" / "system_prompt.md", v / nme)
        except OSError:
            write(v / nme, (v / ".ai" / "system_prompt.md").read_text(encoding="utf-8"))
    reg = tmp / "registry.txt"
    reg.write_text("\ufeffD:\\other\\proj\n" + str(v) + "\n", encoding="utf-8")
    c, o = run([mg, "--root", v, "--registry", reg])
    ok(c == 0 and (v / "CLAUDE.md").exists() and "dry run" in o, "migrate dry run changes nothing", o)
    c, o = run([mg, "--root", v, "--registry", reg, "--apply"])
    arch = list((v / ".ai/archive/legacy-v8").glob("*"))
    ok(c == 0 and arch and (arch[0] / "CLAUDE.md").read_text(encoding="utf-8").startswith("# [MASTER")
       and (arch[0] / ".ai/memory/plan.md").exists() and (arch[0] / ".ai/profiles/base.md").exists(), "migrate archives verbatim", o)
    ok(not (v / "CLAUDE.md").exists() and not (v / ".ai/.mode").exists() and not (v / ".ai/profiles").exists()
       and (v / ".ai/memory/plan.md").exists() and (v / ".ai/manuals/ppt_design_guideline.md").exists(), "migrate removes v8 files, keeps memory/manuals", o)
    r = reg.read_text(encoding="utf-8-sig")
    ok(str(v) not in r and "D:\\other\\proj" in r and list(tmp.glob("registry.txt.bak_*")), "registry line removed with backup", r)
    c, o = run([HERE / "init_project.py", "--root", v, "--preset", "legacy-maintenance"])
    ok(c == 0, "init after migrate", o)
    ex = (v / ".claude/agents/explorer.md").read_text(encoding="utf-8")
    ok(f'command: \'python "{v.resolve().as_posix()}/.claude/hooks/ai_write_guard.py"\'' in ex, "explorer hook path made absolute", ex[:400])
    ok("`cd`" in (v / "CLAUDE.md").read_text(encoding="utf-8"), "CLAUDE.md block has the no-cd rule", "")
    c, o = run([mg, "--root", v, "--retire-memory"])
    ok(c == 1 and "MISSING L3" in o, "retire refuses while ids are uncovered", o)
    c, o = run([v / ".ai/kb.py", "new", "decision", "--id", "D-M8-L3", "--title", "L3 결정"])
    c, o = run([mg, "--root", v, "--retire-memory"])
    ok(c == 0 and not (v / ".ai/memory").exists(), "retire moves memory once covered", o)


def settings_tests(tmp: Path):
    ms = HERE / "merge_settings.py"
    p = tmp / "sp"
    write(p / ".claude" / "settings.json", json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}, "hooks": {
        "SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": "python .claude/hooks/status.py"}]}],
        "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/block_dangerous.py"}]}],
        "PostToolUse": [{"matcher": "TodoWrite", "hooks": [{"type": "command", "command": "node C:/x/notion-todo-sync.js"}]}]}}))
    rootp = p.resolve().as_posix()
    c, o = run([ms, p, "--drop-status"])
    d = json.loads((p / ".claude/settings.json").read_text(encoding="utf-8"))
    cmds = [h["command"] for ev in d["hooks"].values() for g in ev for h in g["hooks"]]
    ok(c == 0 and f'python "{rootp}/.ai/kb.py" hook-start' in cmds and f'python "{rootp}/.ai/kb.py" hook-build' in cmds,
       "merge adds kb hooks with absolute paths", o)
    ok(f'python "{rootp}/.claude/hooks/block_dangerous.py"' in cmds and "python .claude/hooks/block_dangerous.py" not in cmds
       and cmds.count(f'python "{rootp}/.claude/hooks/block_dangerous.py"') == 1, "relative block_dangerous rewritten to absolute, no duplicate", o)
    ok((p / ".claude/hooks/block_dangerous.py").exists() and (p / ".claude/hooks/ai_write_guard.py").exists(), "merge copies hook scripts", o)
    ok(not any("status.py" in x for x in cmds) and "node C:/x/notion-todo-sync.js" in cmds, "status dropped, foreign hooks untouched", o)
    ok("Bash(python .ai/kb.py:*)" in d["permissions"]["allow"] and "Bash(ls:*)" in d["permissions"]["allow"], "kb allow rule added, old allow kept", o)
    c, o = run([ms, p])
    ok(c == 0 and "already up to date" in o, "merge is idempotent", o)
    c, o = run([ms, p, "--hook-path", "env"])
    d = json.loads((p / ".claude/settings.json").read_text(encoding="utf-8"))
    cmds = [h["command"] for ev in d["hooks"].values() for g in ev for h in g["hooks"]]
    ok(c == 0 and 'python "$CLAUDE_PROJECT_DIR/.ai/kb.py" hook-start' in cmds and len([x for x in cmds if "block_dangerous" in x]) == 1,
       "--hook-path env rewrites in place", o)


def numcheck_tests(tmp: Path):
    nc = HERE / "shared" / "skills" / "tech-writing" / "numcheck.py"
    a, same, reord, num, cite, ref = (tmp / f"nc_{k}.md" for k in ("a", "same", "reord", "num", "cite", "ref"))
    base = "Latency fell from 120 ms to 45 ms (30 runs) [1, 2]. Fig. 3 shows it. 그림 4 and Table 2 agree."
    write(a, base)
    write(same, base.replace("shows it", "presents the result"))
    write(reord, "그림 4 and Table 2 agree. Fig. 3 shows it. Latency fell from 120 ms to 45 ms (30 runs) [1, 2].")
    write(num, base.replace("45 ms", "54 ms"))
    write(cite, base.replace("[1, 2]", "[1, 3]"))
    write(ref, base.replace("Fig. 3", "Fig. 4"))
    ok(run([nc, a, same])[0] == 0 and run([nc, a, reord])[0] == 0, "numcheck: rewording and reordering are SAME")
    for f, lab in ((num, "number"), (cite, "citation"), (ref, "figure ref")):
        c, o = run([nc, a, f])
        ok(c == 1 and "DIFF" in o, f"numcheck detects changed {lab}", o)
    ok(run([nc, a])[0] == 2 and run([nc, a, tmp / "none.md"])[0] == 2, "numcheck usage/read errors exit 2")
    p = tmp / "twproj"
    write(p / "docs" / "a.md", "# a\n")
    c, o = run([HERE / "init_project.py", "--root", p, "--preset", "report-ppt"])
    sk = p / ".claude" / "skills" / "tech-writing"
    ok(c == 0 and (sk / "numcheck.py").exists() and (sk / "revise_prompts.md").exists() and (sk / "SKILL.md").exists(),
       "init copies tech-writing helper files (numcheck.py, revise_prompts.md)", o)


def humanize_tests(tmp: Path):
    """v2.4.6: humanize_patterns.md (kr/en) + third_party/humanizer pin."""
    import hashlib
    import re
    ids = {}
    for lang in ("kr", "en"):
        f = HERE / "lang" / lang / "skills" / "tech-writing" / "humanize_patterns.md"
        ok(f.exists(), f"humanize_patterns.md exists ({lang})")
        txt = f.read_text(encoding="utf-8") if f.exists() else ""
        ids[lang] = re.findall(r"(?m)^\| (H\d+) \|", txt)
        rows = [l for l in txt.splitlines() if re.match(r"\| H\d+ \|", l)]
        ok(rows and all(re.search(r"\| [\u25cb\u25b3\u00d7] \| [\u25cb\u25b3\u00d7] \| [\u25cb\u25b3\u00d7] \|$", l) for l in rows),
           f"humanize_patterns rows end with three type marks ({lang})")
        ok("AlphaEvolve" not in txt and "Rajhans" not in txt and "Korattur" not in txt, f"humanize_patterns copies no upstream example ({lang})")
        for name in ("SKILL.md", "revise_prompts.md"):
            g = HERE / "lang" / lang / "skills" / "tech-writing" / name
            ok("humanize_patterns.md" in g.read_text(encoding="utf-8"), f"{name} references humanize_patterns.md ({lang})")
    ok(ids["kr"] == ids["en"] == [f"H{i}" for i in range(1, 21)], "humanize_patterns IDs H1..H20 match in kr/en", str(ids))
    tp = HERE / "third_party" / "humanizer@a32f244"
    man = tp / "MANIFEST.sha256"
    bad = []
    if man.exists():
        for line in man.read_text(encoding="utf-8").splitlines():
            h, _, name = line.partition("  ")
            fp = tp / name
            if not fp.is_file() or hashlib.sha256(fp.read_bytes()).hexdigest() != h:
                bad.append(name)
    ok(man.exists() and not bad, "third_party/humanizer pin matches MANIFEST.sha256", str(bad))
    rv = (tp / "REVIEW.md").read_text(encoding="utf-8") if (tp / "REVIEW.md").exists() else ""
    ok("[x] **" in rv and "a32f24407364c74c812b43c15926d638bee1e072" in rv, "humanizer REVIEW.md records decision and SHA")
    p = tmp / "hzproj"
    write(p / "docs" / "a.md", "# a\n")
    c, o = run([HERE / "init_project.py", "--root", p, "--preset", "paper-patent"])
    ok(c == 0 and (p / ".claude" / "skills" / "tech-writing" / "humanize_patterns.md").exists(),
       "init copies humanize_patterns.md with tech-writing", o)


def stack_tests(tmp: Path):
    """v2.4.4: init_project --stack (additive rule bundles), /ai-guide command, setup_env command deploy."""
    import hashlib
    import importlib.util
    import re
    ip = HERE / "init_project.py"
    roster = HERE / "roster.yaml"
    try:
        import yaml
        ros = yaml.safe_load(roster.read_text(encoding="utf-8"))
    except ImportError:
        ros = json.loads((HERE / "backup" / "roster.json").read_text(encoding="utf-8"))
    stacks = ros.get("stacks", {})
    ok(set(stacks) >= {"python-ml", "vue-ts", "flutter-dart", "kotlin-android", "csharp-windows", "cpp-qt-cmake"}, "roster has the six stacks", str(list(stacks)))
    for lang in ("kr", "en"):
        for name, spec in stacks.items():
            for r in spec.get("rules", []):
                f = HERE / "lang" / lang / "rules" / f"{r}.md"
                txt = f.read_text(encoding="utf-8") if f.exists() else ""
                ok(txt.startswith("---\npaths:\n"), f"stack rule {lang}/{r} exists with paths frontmatter", txt[:60])
    p = tmp / "stackproj"
    write(p / "a.py", "print(1)\n")
    c, o = run([ip, "--root", p, "--stack", "python-ml", "--dry-run"])
    ok(c == 0 and "would copy stack-python-ml.md" in o and not (p / ".claude").exists(), "stack dry-run writes nothing", o)
    c, o = run([ip, "--root", p, "--stack", "python-ml"])
    ok(c == 0 and (p / ".claude/rules/stack-python-ml.md").exists(), "stack copies the rule file", o)
    ok(not (p / "CLAUDE.md").exists() and not (p / ".ai").exists() and not (p / "AGENTS.md").exists(),
       "stack alone creates only .claude/rules (no CLAUDE.md, .ai, AGENTS.md)", o)
    c, o = run([ip, "--root", p, "--stack", "python-ml"])
    ok(c == 0 and "kept existing" in o, "stack rerun keeps the existing file", o)
    c, o = run([ip, "--root", p, "--stack", "nope"])
    ok(c == 2 and "unknown stack" in o, "stack rejects an unknown name", o)
    q = tmp / "stackproj2"
    write(q / "a.py", "print(1)\n")
    c, o = run([ip, "--root", q, "--stack", "vue-ts, python-ml", "--lang", "en"])
    ok(c == 0 and "Python and ML checklist" in (q / ".claude/rules/stack-python-ml.md").read_text(encoding="utf-8")
       and (q / ".claude/rules/stack-vue-ts.md").exists(), "stack accepts a list and --lang en", o)
    # existing v2.4 project: only the new rule file may appear, nothing else changes
    e = tmp / "existing"
    write(e / "a.py", "print(1)\n")
    c, o = run([ip, "--root", e, "--preset", "new-fullstack"])
    def snap(root):
        return {x.relative_to(root).as_posix(): hashlib.md5(x.read_bytes()).hexdigest() for x in root.rglob("*") if x.is_file()}
    before = snap(e)
    c, o = run([ip, "--root", e, "--stack", "vue-ts,python-ml"])
    after = snap(e)
    added = set(after) - set(before)
    ok(c == 0 and added == {".claude/rules/stack-vue-ts.md", ".claude/rules/stack-python-ml.md"}
       and all(after[k] == v for k, v in before.items()), "stack on an existing project only adds the rule files", f"{o} {added}")
    # /ai-guide command
    names_ps = set(ros.get("presets", {}))
    for lang in ("kr", "en"):
        f = HERE / "lang" / lang / "commands" / "ai-guide.md"
        g = f.read_text(encoding="utf-8")
        ok("disable-model-invocation: true" in g.split("---")[1], f"ai-guide {lang} is not model-invocable", g[:200])
        rows = set(re.findall(r"^\| `([a-z-]+)` \|", g, re.M))
        exts = set(ros.get("externals", {}))
        ok(rows == names_ps | set(stacks) | exts, f"ai-guide {lang} lists exactly the roster presets, stacks, and externals", f"{rows ^ (names_ps | set(stacks) | exts)}")
    # setup_env deploys the command without overwriting
    sys.dont_write_bytecode = True  # importing setup_env must not leave a __pycache__ in the tool folder
    spec = importlib.util.spec_from_file_location("setup_env_t", HERE / "setup_env.py")
    se = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(se)
    se.CLAUDE_HOME = tmp / "fakehome" / ".claude"
    class A:  # minimal args
        plan = False
        yes = True
        lang = "kr"
    import io, contextlib
    buf = io.StringIO()
    env = ros.get("environment", {})
    ok("ai-guide" in env.get("user_level_deploy", {}).get("commands", []), "roster deploys the ai-guide command", "")
    with contextlib.redirect_stdout(buf):
        se.action_deploy_commands(env, A)
    d = se.CLAUDE_HOME / "commands" / "ai-guide.md"
    ok(d.exists() and "AI_Tools" in d.read_text(encoding="utf-8"), "setup_env copies ai-guide to ~/.claude/commands", buf.getvalue())
    d.write_text("mine\n", encoding="utf-8")
    with contextlib.redirect_stdout(buf):
        se.action_deploy_commands(env, A)
    ok(d.read_text(encoding="utf-8") == "mine\n", "setup_env keeps an existing command file", buf.getvalue())


def research_tests(tmp: Path):
    """v2.4.5: research preset + researcher agent."""
    ip = HERE / "init_project.py"
    r = tmp / "res"
    r.mkdir()
    c, o = run([ip, "--root", r, "--preset", "research"])
    ag = r / ".claude/agents"
    ok(c == 0 and (ag / "researcher.md").exists() and (ag / "evidence-verifier.md").exists() and (ag / "explorer.md").exists()
       and not (ag / "reviewer.md").exists() and not (r / ".claude/skills/code-change").exists()
       and (r / ".claude/skills/tech-writing/SKILL.md").exists(), "research preset: researcher+verifier+explorer, no reviewer/code-change", o)
    rs = (ag / "researcher.md").read_text(encoding="utf-8")
    ok("WebSearch" in rs and "WebFetch" in rs and "Bash" not in rs.split("---")[1] and "ai_write_guard.py" in rs
       and "/ai_write_guard.py" in rs.replace("\\", "/"), "researcher: web tools, no Bash, write-guard hook with absolute path", rs[:500])
    for lang in ("kr", "en"):
        q = tmp / f"res_{lang}"
        q.mkdir()
        c, o = run([ip, "--root", q, "--preset", "research", "--lang", lang])
        txt = (q / ".claude/agents/researcher.md").read_text(encoding="utf-8")
        ok(c == 0 and ("UNVERIFIED" in txt) and ("llms.txt" in txt), f"researcher {lang} keeps UNVERIFIED and llms.txt lines", o)


def ext_tests(tmp: Path):
    """v2.4.5: init_project --ext (pinned external skill, manifest-verified, additive)."""
    import hashlib
    import importlib.util
    ip = HERE / "init_project.py"
    spec = importlib.util.spec_from_file_location("ip_mod", ip)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    # manifest verification on a throw-away tree
    b = tmp / "ext_src"
    write(b / "a.md", "A\n")
    write(b / "engine" / "x.py", "x = 1\n")
    man = tmp / "man.sha256"
    h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    man.write_text(f"{h(b / 'a.md')}  a.md\n{h(b / 'engine' / 'x.py')}  engine/x.py\n", encoding="utf-8")
    ok(m.verify_manifest(b, man, ["a.md", "engine"]) == [], "manifest verifies clean files", "")
    write(b / "engine" / "x.py", "x = 2\n")
    ok(any("mismatch" in e for e in m.verify_manifest(b, man, ["engine"])), "manifest catches a changed file", "")
    write(b / "engine" / "extra.py", "y\n")
    ok(any("not in manifest" in e for e in m.verify_manifest(b, man, ["engine"])), "manifest catches an extra file", "")
    # the line ranges in our hwpx SKILL.md must still match the pinned chat-engine.md headings
    ce = (HERE / "third_party/hwpx-airmang@c6196cf/skill/chat-engine.md").read_text(encoding="utf-8").split("\n")
    marks = {11: "## 1.", 82: "### ", 101: "## 2.", 115: "## 3.", 167: "## 작업 절차", 181: "## W1", 203: "## W2", 265: "## W3", 360: "## W4", 411: "## W5"}
    ok(all(ce[n - 1].startswith(h) for n, h in marks.items()) and len(ce) >= 521, "hwpx SKILL.md line ranges match the pinned chat-engine.md", str([n for n, h in marks.items() if not ce[n - 1].startswith(h)]))
    # real install into a throw-away project
    p = tmp / "ext_proj"
    p.mkdir()
    c, o = run([ip, "--root", p, "--ext", "nope"])
    ok(c == 2 and "unknown external" in o, "unknown --ext is an error", o)
    c, o = run([ip, "--root", p, "--ext", "hwpx", "--dry-run"])
    ok(c == 0 and not (p / ".claude").exists() and "would copy" in o, "--ext dry-run writes nothing", o)
    c, o = run([ip, "--root", p, "--ext", "hwpx"])
    sk = p / ".claude/skills/hwpx"
    ok(c == 0 and (sk / "SKILL.md").exists() and (sk / "chat-engine.md").exists() and (sk / "engine/VENDOR.json").exists()
       and not (sk / "references").exists() and not (sk / "scripts").exists(), "--ext installs SKILL.md, chat-engine.md, engine/ only", o)
    sd = (sk / "SKILL.md").read_text(encoding="utf-8")
    ok("mcp__" not in sd and "chat-engine.md" in sd and len(sd) < 4000, "our hwpx SKILL.md is short and points to chat-engine.md", sd[:200])
    c, o = run([ip, "--root", p, "--ext", "hwpx"])
    ok(c == 0 and "copied 0 file(s)" in o, "--ext again keeps everything", o)
    c, o = run([ip, "--root", p, "--ext", "hwpx", "--lang", "en", "--force"])
    ok(c == 0 and "edit and create" in (sk / "SKILL.md").read_text(encoding="utf-8"), "--ext --lang en --force replaces SKILL.md", o)
    # v2.4.6: interview-me (own SKILL.md inside the pinned folder, covered by the manifest)
    tp = HERE / "third_party/interview-me@8c99fa3"
    q = tmp / "ext_proj2"
    q.mkdir()
    c, o = run([ip, "--root", q, "--ext", "interview-me", "--dry-run"])
    ok(c == 0 and not (q / ".claude").exists() and "would copy" in o, "--ext interview-me dry-run writes nothing", o)
    c, o = run([ip, "--root", q, "--ext", "interview-me"])
    isk = q / ".claude/skills/interview-me"
    ok(c == 0 and sorted(f.name for f in isk.iterdir()) == ["LICENSE", "SKILL.md"]
       and (isk / "SKILL.md").read_bytes() == (tp / "install/SKILL.md").read_bytes(), "--ext interview-me installs the narrowed SKILL.md and LICENSE only", o)
    ok((isk / "SKILL.md").read_bytes() != (tp / "SKILL.md").read_bytes(), "installed interview-me is the narrowed variant, not the original", "")
    import shutil
    bad = tmp / "ext_src2"
    shutil.copytree(tp, bad / "third_party/interview-me@8c99fa3")
    (bad / "third_party/interview-me@8c99fa3/install/SKILL.md").write_text("tampered\n", encoding="utf-8")
    r = tmp / "ext_proj3"
    r.mkdir()
    spec = {"source": "third_party/interview-me@8c99fa3", "manifest": "third_party/interview-me@8c99fa3/MANIFEST.sha256",
            "skill": "interview-me", "own": "install/SKILL.md", "copy": ["LICENSE"]}
    import io, contextlib
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc = m.apply_external(r, bad, "interview-me", spec, False, False, "kr")
    ok(rc == 2 and "sha256 mismatch" in err.getvalue() and not (r / ".claude").exists(), "a tampered own SKILL.md is refused before anything is copied", err.getvalue())


def skill_tests(tmp: Path):
    """v2.4.6: init_project --skill (named skill folders only, no CLAUDE.md/kb change, additive)."""
    ip = HERE / "init_project.py"
    p = tmp / "skill_proj"
    p.mkdir()
    write(p / "CLAUDE.md", "# mine\n")
    c, o = run([ip, "--root", p, "--skill", "nope"])
    ok(c == 2 and "unknown skill" in o and "available" in o, "unknown --skill is an error", o)
    c, o = run([ip, "--root", p, "--skill", ""])
    ok(c != 0, "empty --skill is not a silent success", o)
    c, o = run([ip, "--root", p, "--skill", "tech-writing,system-architect", "--dry-run"])
    ok(c == 0 and not (p / ".claude").exists() and "would copy" in o, "--skill dry-run writes nothing", o)
    c, o = run([ip, "--root", p, "--skill", "tech-writing,system-architect"])
    sk = p / ".claude" / "skills"
    ok(c == 0 and (sk / "system-architect" / "SKILL.md").is_file() and (sk / "tech-writing" / "SKILL.md").is_file(),
       "--skill copies the named skill folders", o)
    ok((sk / "tech-writing" / "humanize_patterns.md").is_file() and (sk / "tech-writing" / "numcheck.py").is_file(),
       "--skill copies helper files and shared/skills extras", o)
    ok((p / "CLAUDE.md").read_text(encoding="utf-8") == "# mine\n" and not (p / ".ai").exists() and not (p / "AGENTS.md").exists()
       and not (p / ".claude" / "agents").exists() and not (p / ".claude" / "rules").exists(),
       "--skill touches only .claude/skills (no CLAUDE.md, .ai, AGENTS.md, agents, rules)", o)
    sa = sk / "system-architect" / "SKILL.md"
    sa.write_text("local edit\n", encoding="utf-8")
    c, o = run([ip, "--root", p, "--skill", "system-architect"])
    ok(c == 0 and sa.read_text(encoding="utf-8") == "local edit\n" and "kept existing" in o, "--skill keeps an existing file", o)
    c, o = run([ip, "--root", p, "--skill", "system-architect", "--force"])
    ok(c == 0 and sa.read_text(encoding="utf-8") != "local edit\n", "--skill --force overwrites", o)
    c, o = run([ip, "--root", p, "--skill", "system-architect", "--lang", "en", "--force"])
    ok(c == 0 and "Loop contract" in sa.read_text(encoding="utf-8"), "--skill --lang en uses the English skill", o)


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for f in (kb_tests, design_tests, init_tests, migrate_tests, settings_tests, numcheck_tests, humanize_tests, stack_tests, research_tests, ext_tests, skill_tests):
            try:
                f(tmp)
            except Exception as e:  # report and continue
                fails.append(f"{f.__name__} crashed: {e!r}")
    for f in fails:
        print("FAIL " + f)
    print(f"v2.4 selftest: " + ("ALL OK" if not fails else f"{len(fails)} FAILED") + f" ({n} checks: kb, design_extract, init_project, migrate_v8, merge_settings, numcheck, humanize, stack, research, ext, skill)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
