#!/usr/bin/env python3
"""Coverage gate for the code-change skill (v2.1). NOT an event hook: the main session runs it
as a deterministic check after the tests. Stdlib only, Python 3.8+.

  python .claude/hooks/check_test_coverage.py [--min 70] [--report PATH] [--files a.py b.ts ...]

Reads an existing coverage report (it never runs the tests):
  coverage.xml (Cobertura: coverage.py, jest/vitest cobertura), coverage/coverage-summary.json
  (istanbul json-summary), coverage/lcov.info.
Prints one line per result. Exit codes: 0 ok (or no --min given), 1 below --min,
3 no readable report (prints `UNVERIFIED: coverage`). With --files, the gate applies to the
listed changed files only (matched by path suffix); files absent from the report are listed as
UNCOVERED-OR-UNREPORTED and make the gate fail when --min is given.
"""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CANDIDATES = ["coverage.xml", "coverage/cobertura-coverage.xml", "coverage/coverage-summary.json",
              "coverage/lcov.info", "lcov.info", "htmlcov/coverage.json"]


def norm(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def read_cobertura(path: Path):
    root = ET.parse(path).getroot()
    files = {}
    for cls in root.iter("class"):
        fn = cls.get("filename")
        if not fn:
            continue
        hit = tot = 0
        for ln in cls.iter("line"):
            tot += 1
            hit += 1 if int(ln.get("hits", "0")) > 0 else 0
        h, t = files.get(norm(fn), (0, 0))
        files[norm(fn)] = (h + hit, t + tot)
    return files


def read_summary_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    files = {}
    for k, v in data.items():
        if k == "total" or not isinstance(v, dict) or "lines" not in v:
            continue
        files[norm(k)] = (int(v["lines"].get("covered", 0)), int(v["lines"].get("total", 0)))
    return files


def read_coveragepy_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    files = {}
    for k, v in (data.get("files") or {}).items():
        s = v.get("summary", {})
        files[norm(k)] = (int(s.get("covered_lines", 0)), int(s.get("num_statements", 0)))
    return files


def read_lcov(path: Path):
    files, cur, hit, tot = {}, None, 0, 0
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("SF:"):
            cur, hit, tot = norm(line[3:].strip()), 0, 0
        elif line.startswith("DA:") and cur:
            parts = line[3:].split(",")
            tot += 1
            hit += 1 if len(parts) > 1 and parts[1].strip() not in ("0", "") else 0
        elif line.startswith("end_of_record") and cur:
            files[cur] = (hit, tot)
            cur = None
    return files


def load(report: Path):
    name = report.name.lower()
    if name.endswith(".xml"):
        return read_cobertura(report)
    if name == "coverage-summary.json":
        return read_summary_json(report)
    if name.endswith(".json"):
        return read_coveragepy_json(report)
    return read_lcov(report)


def pct(h, t):
    return 100.0 if t == 0 else 100.0 * h / t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=float, default=None)
    ap.add_argument("--report", default=None)
    ap.add_argument("--files", nargs="*", default=None)
    a = ap.parse_args()

    report = Path(a.report) if a.report else next((Path(c) for c in CANDIDATES if Path(c).is_file()), None)
    if report is None or not report.is_file():
        print("UNVERIFIED: coverage (no report found; run the project's coverage command first)")
        return 3
    try:
        files = load(report)
    except Exception as e:
        print(f"UNVERIFIED: coverage (could not read {report}: {type(e).__name__})")
        return 3
    if not files:
        print(f"UNVERIFIED: coverage ({report} has no per-file data)")
        return 3

    if a.files:
        want = [norm(f) for f in a.files]
        rows, missing = [], []
        for w in want:
            m = [k for k in files if k == w or k.endswith("/" + w) or w.endswith("/" + k)]
            if not m:
                missing.append(w)
            else:
                h, t = files[m[0]]
                rows.append((w, h, t))
        for w, h, t in rows:
            print(f"{pct(h, t):5.1f}%  {h}/{t} lines  {w}")
        for w in missing:
            print(f"UNCOVERED-OR-UNREPORTED  {w}")
        h = sum(r[1] for r in rows)
        t = sum(r[2] for r in rows)
        total = pct(h, t) if rows else 0.0
        print(f"changed-files coverage: {total:.1f}% ({report})")
        if a.min is not None and (missing or total < a.min):
            print(f"FAIL: below --min {a.min:g}" + (" or unreported files" if missing else ""))
            return 1
        return 0

    h = sum(v[0] for v in files.values())
    t = sum(v[1] for v in files.values())
    total = pct(h, t)
    print(f"total line coverage: {total:.1f}% ({h}/{t} lines, {len(files)} files, {report})")
    if a.min is not None and total < a.min:
        low = sorted(files.items(), key=lambda kv: pct(*kv[1]))[:3]
        for k, v in low:
            print(f"  lowest: {pct(*v):5.1f}%  {k}")
        print(f"FAIL: below --min {a.min:g}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
