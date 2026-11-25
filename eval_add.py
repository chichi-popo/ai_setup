import argparse, csv, datetime, io, json, os, re, sys

HEADER = ["date", "task_id", "task_desc", "structure", "run", "model_main", "effort", "input_tokens", "output_tokens",
          "model_calls", "cache_ratio", "elapsed_min", "success_0_1", "rework_count", "quality_1_5", "notes",
          "reviewer_defects", "rejected_findings", "cache_read_tokens", "cache_write_tokens", "cost_usd", "api_sec"]

ap = argparse.ArgumentParser(description="append one run to eval_log.csv. Use --auto <run folder> to read the numbers from the Claude Code session transcript instead of typing /usage values")
ap.add_argument("--log", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_log.csv"))
ap.add_argument("--auto", default=None, metavar="RUN_DIR", help="run folder; reads tokens, cost, times from that folder's newest session transcript")
ap.add_argument("--dry-run", action="store_true", help="print the row but do not write it")
ap.add_argument("--task", required=True); ap.add_argument("--desc", default=""); ap.add_argument("--structure", required=True)
ap.add_argument("--run", required=True); ap.add_argument("--model", default=None); ap.add_argument("--effort", default=None)
ap.add_argument("--in", dest="tin", type=int, default=None); ap.add_argument("--out", dest="tout", type=int, default=None)
ap.add_argument("--cache-read", type=int, default=None); ap.add_argument("--cache-write", type=int, default=None)
ap.add_argument("--cost", type=float, default=None); ap.add_argument("--api-sec", type=float, default=None)
ap.add_argument("--wall-before", type=float, default=None, help="manual mode: Total duration (wall) in seconds at the first /usage")
ap.add_argument("--wall-after", type=float, default=None, help="manual mode: Total duration (wall) in seconds at the last /usage")
ap.add_argument("--success", type=int, choices=[0, 1], required=True); ap.add_argument("--rework", type=int, default=0)
ap.add_argument("--quality", type=int, choices=[1, 2, 3, 4, 5], default=None, help="optional; leave out to keep the column empty"); ap.add_argument("--notes", default="")
ap.add_argument("--reviewer-defects", default=""); ap.add_argument("--rejected-findings", default="")
a = ap.parse_args()


def parse_ts(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def text_of(content):
    if isinstance(content, str):
        return content
    out = []
    for b in content or []:
        if isinstance(b, dict):
            out.append(str(b.get("text", "")))
    return " ".join(out)


def norm_path(p):
    return p.replace("\\", "/").rstrip("/").lower()


def find_transcript(run_dir):
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    root = os.path.join(base, "projects")
    full = os.path.abspath(run_dir)
    cand_dir = os.path.join(root, re.sub(r"[^A-Za-z0-9]", "-", full))
    files = []
    if os.path.isdir(cand_dir):
        files = [os.path.join(cand_dir, n) for n in os.listdir(cand_dir) if n.endswith(".jsonl")]
    if not files and os.path.isdir(root):
        want = norm_path(full)
        for d in os.listdir(root):
            dd = os.path.join(root, d)
            if not os.path.isdir(dd):
                continue
            for n in os.listdir(dd):
                if not n.endswith(".jsonl"):
                    continue
                fp = os.path.join(dd, n)
                try:
                    with open(fp, encoding="utf-8", errors="replace") as f:
                        for _ in range(60):
                            line = f.readline()
                            if not line:
                                break
                            try:
                                c = json.loads(line).get("cwd")
                            except Exception:
                                continue
                            if c:
                                if norm_path(c) == want:
                                    files.append(fp)
                                break
                except OSError:
                    pass
    if not files:
        sys.exit("no session transcript found for " + full + " under " + root + ". Use manual mode (--in/--out/...) instead.")
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def analyze(path):
    recs = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    recs.append(json.loads(line))
                except Exception:
                    pass
    cost = None
    ids = {}
    first_ts = last_ts = None
    modes = set()
    flags = []
    effort = None
    for r in recs:
        t = r.get("type")
        if t == "cost-state":
            cost = r
        elif t == "mode" and r.get("mode"):
            modes.add(r["mode"])
        elif t == "user" and not r.get("isSidechain"):
            txt = text_of((r.get("message") or {}).get("content"))
            if "<command-name>" in txt or "<local-command" in txt or r.get("isMeta"):
                continue
            ts = r.get("timestamp")
            if ts:
                first_ts = first_ts or parse_ts(ts)
                last_ts = parse_ts(ts)
        elif t == "assistant" and not r.get("isSidechain"):
            m = r.get("message") or {}
            u = m.get("usage") or {}
            mid = m.get("id") or r.get("uuid")
            cur = ids.setdefault(mid, {"input": 0, "output": 0, "cr": 0, "cw": 0, "model": m.get("model")})
            cur["input"] = max(cur["input"], u.get("input_tokens", 0) or 0)
            cur["output"] = max(cur["output"], u.get("output_tokens", 0) or 0)
            cur["cr"] = max(cur["cr"], u.get("cache_read_input_tokens", 0) or 0)
            cur["cw"] = max(cur["cw"], u.get("cache_creation_input_tokens", 0) or 0)
            if r.get("effort"):
                effort = r["effort"]
            ts = r.get("timestamp")
            if ts:
                first_ts = first_ts or parse_ts(ts)
                last_ts = parse_ts(ts)
            content = m.get("content")
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        nm = b.get("name", "")
                        if nm in ("EnterPlanMode", "ExitPlanMode") and "plan-mode" not in flags:
                            flags.append("plan-mode")
                        if "eval_private" in json.dumps(b.get("input", {}), ensure_ascii=True).lower() and "ESCAPE?" not in flags:
                            flags.append("ESCAPE?")
    out = {"file": path, "calls": len(ids), "modes": modes, "flags": flags, "effort": effort, "cost_state": cost,
           "tr": {"input": sum(v["input"] for v in ids.values()), "output": sum(v["output"] for v in ids.values()),
                  "cr": sum(v["cr"] for v in ids.values()), "cw": sum(v["cw"] for v in ids.values())}}
    out["elapsed_sec"] = (last_ts - first_ts).total_seconds() if first_ts and last_ts else None
    if ids:
        models = {}
        for v in ids.values():
            models[v["model"]] = models.get(v["model"], 0) + v["output"]
        out["model"] = max(models, key=models.get)
    return out


notes = [a.notes] if a.notes else []
vals = {"model": a.model, "effort": a.effort, "tin": a.tin, "tout": a.tout, "cr": a.cache_read, "cw": a.cache_write,
        "cost": a.cost, "api": a.api_sec, "elapsed_sec": None, "calls": ""}
if a.wall_before is not None and a.wall_after is not None:
    vals["elapsed_sec"] = a.wall_after - a.wall_before

if a.auto:
    files = find_transcript(a.auto)
    info = analyze(files[0])
    print("transcript:", info["file"])
    if len(files) > 1:
        print("WARNING: %d sessions were opened in this folder; using the newest. Check that it is the run you mean." % len(files))
        notes.append("multi-session")
    cs = info["cost_state"]
    if cs:
        mu = cs.get("modelUsage") or {}
        auto_in = sum(v.get("inputTokens", 0) for v in mu.values())
        auto_out = sum(v.get("outputTokens", 0) for v in mu.values())
        auto_cr = sum(v.get("cacheReadInputTokens", 0) for v in mu.values())
        auto_cw = sum(v.get("cacheCreationInputTokens", 0) for v in mu.values())
        auto_cost = cs.get("totalCostUSD")
        auto_api = (cs.get("totalAPIDuration") or 0) / 1000.0
        if mu and not vals["model"]:
            vals["model"] = max(mu, key=lambda k: mu[k].get("costUSD", 0))
        tr = info["tr"]
        if tr["output"] and abs(auto_out - tr["output"]) / max(auto_out, tr["output"]) > 0.03:
            print("WARNING: cost-state output tokens (%d) differ from transcript sum (%d): cost-state may be stale or subagents were used. Compare with /usage." % (auto_out, tr["output"]))
    else:
        print("WARNING: no cost-state record in the transcript; tokens come from the message sums, cost and api_sec stay blank unless you pass --cost/--api-sec.")
        tr = info["tr"]
        auto_in, auto_out, auto_cr, auto_cw, auto_cost, auto_api = tr["input"], tr["output"], tr["cr"], tr["cw"], None, None
        vals["model"] = vals["model"] or info.get("model")
    for k, v in (("tin", auto_in), ("tout", auto_out), ("cr", auto_cr), ("cw", auto_cw), ("cost", auto_cost), ("api", auto_api)):
        if vals[k] is None:
            vals[k] = v
    vals["effort"] = vals["effort"] or info["effort"]
    if vals["elapsed_sec"] is None:
        vals["elapsed_sec"] = info["elapsed_sec"]
    vals["calls"] = info["calls"]
    for fl in info["flags"]:
        notes.append(fl)
    extra = sorted(m for m in info["modes"] if m != "normal")
    if extra:
        notes.append("modes=" + "/".join(extra))

missing = [n for n, k in (("--model", "model"), ("--effort", "effort"), ("--in", "tin"), ("--out", "tout")) if vals[k] is None]
if vals["elapsed_sec"] is None:
    missing.append("--wall-before/--wall-after")
if missing:
    sys.exit("missing values: " + ", ".join(missing) + " (pass them, or use --auto RUN_DIR)")
for k in ("cr", "cw"):
    if vals[k] is None:
        vals[k] = 0

with open(a.log, encoding="utf-8-sig", newline="") as f:
    first = f.readline().strip()
if first.split(",") != HEADER:
    sys.exit("eval_log.csv header differs from the expected 22 columns. Fix the header first (see checklist A-5f).")
total_in = vals["tin"] + vals["cr"] + vals["cw"]
ratio = "" if total_in == 0 else "%.3f" % (vals["cr"] / total_in)
cost = "" if vals["cost"] is None else round(vals["cost"], 4)
api = "" if vals["api"] is None else round(vals["api"], 1)
row = [datetime.date.today().isoformat(), a.task, a.desc, a.structure, a.run, vals["model"], vals["effort"], vals["tin"], vals["tout"],
       vals["calls"], ratio, "%.2f" % (vals["elapsed_sec"] / 60.0), a.success, a.rework, "" if a.quality is None else a.quality, ";".join(notes),
       a.reviewer_defects, a.rejected_findings, vals["cr"], vals["cw"], cost, api]
buf = io.StringIO(); csv.writer(buf, lineterminator="\n").writerow(row)
if a.dry_run:
    print("dry-run:", buf.getvalue().strip())
else:
    with open(a.log, "a", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())
    print("appended:", buf.getvalue().strip())
