#!/usr/bin/env python3
"""numcheck.py - compare numbers, citations and Fig/Table/Eq references of two texts (before/after editing).
  python numcheck.py BEFORE AFTER      (.md .txt .docx)  -> exit 0 identical, 1 differences, 2 usage/read error
Order and wording may change; the multiset of tokens must not. Stdlib only."""
import re
import sys
import zipfile
from collections import Counter

CITE = re.compile(r"\[\s*\d+(?:\s*[-,–]\s*\d+)*\s*\]")
REF = re.compile(r"(?:Fig(?:ure)?s?\.?|Tables?|Eqs?\.?|Equations?|그림|표|식)\s*\(?\d+(?:\.\d+)?[a-z]?\)?", re.I)
NUM = re.compile(r"\d+(?:[.,]\d+)*")


def load(p):
    if p.lower().endswith(".docx"):
        with zipfile.ZipFile(p) as z:
            x = z.read("word/document.xml").decode("utf-8", "replace")
        return re.sub(r"<[^>]+>", " ", x.replace("</w:p>", "\n"))
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def tokens(t):
    t = re.sub(r"\s+", " ", t)
    c = Counter()
    for kind, rx in (("cite", CITE), ("ref", REF)):
        for m in rx.findall(t):
            c[(kind, re.sub(r"\s+", "", m).lower())] += 1
        t = rx.sub(" ", t)
    for m in NUM.findall(t):
        c[("num", m)] += 1
    return c


def main(a):
    if len(a) != 2:
        print(__doc__)
        return 2
    try:
        b, c = tokens(load(a[0])), tokens(load(a[1]))
    except (OSError, zipfile.BadZipFile, KeyError) as e:
        print(f"cannot read: {e}")
        return 2
    gone, new = b - c, c - b
    for lab, d in (("MISSING in after", gone), ("ADDED in after", new)):
        for (k, v), n in sorted(d.items()):
            print(f"{lab}: {k} {v} x{n}")
    print("numcheck: " + ("SAME" if not gone and not new else f"DIFF ({sum(gone.values())} missing, {sum(new.values())} added)"))
    return 0 if not gone and not new else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
