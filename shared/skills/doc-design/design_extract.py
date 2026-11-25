#!/usr/bin/env python3
"""design_extract.py (v2.4, doc-design skill) - read design values straight out of a .pptx/.potx/.docx/.dotx reference.

  python design_extract.py <reference file> [--out .ai/design/DESIGN.md] [--force] [--lang kr|en]

Reads (no rendering, no guessing):
  pptx/potx: theme colours (dk1, lt1, dk2, lt2, accent1-6, hlink), major/minor fonts (latin + East Asian),
             slide size, slide layout names, master title/body text sizes
  docx/dotx: theme colours and fonts, document default font/size, Title/Heading 1-3/Normal/Caption styles
             (font, size, bold, colour, spacing, line spacing), page size and margins
Writes a DESIGN.md draft (stdout, or --out; an existing file is not overwritten without --force).
Role names (primary/secondary/accent) are a suggestion from theme slots; confirm them with the user.
Stdlib only, Python 3.8+."""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
W = "{%s}" % NS["w"]
SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"]
EMU_IN = 914400.0


def xml(z: zipfile.ZipFile, name: str):
    try:
        return ET.fromstring(z.read(name))
    except KeyError:
        return None


def theme_info(root) -> dict:
    out = {"colors": {}, "major": {}, "minor": {}, "name": ""}
    if root is None:
        return out
    out["name"] = root.get("name", "")
    cs = root.find(".//a:clrScheme", NS)
    if cs is not None:
        for slot in SLOTS:
            el = cs.find(f"a:{slot}", NS)
            if el is None:
                continue
            c = el.find("a:srgbClr", NS)
            if c is not None:
                out["colors"][slot] = c.get("val", "").upper()
            else:
                c = el.find("a:sysClr", NS)
                if c is not None:
                    out["colors"][slot] = (c.get("lastClr") or c.get("val", "")).upper()
    for kind in ("major", "minor"):
        f = root.find(f".//a:fontScheme/a:{kind}Font", NS)
        if f is None:
            continue
        lat, ea = f.find("a:latin", NS), f.find("a:ea", NS)
        out[kind]["latin"] = lat.get("typeface", "") if lat is not None else ""
        out[kind]["ea"] = ea.get("typeface", "") if ea is not None else ""
        if not out[kind]["ea"]:
            for fe in f.findall("a:font", NS):
                if fe.get("script") == "Hang":
                    out[kind]["ea"] = fe.get("typeface", "")
    return out


def rels_target(z: zipfile.ZipFile, part: str, rtype_end: str) -> str:
    p = PurePosixPath(part)
    rels = xml(z, str(p.parent / "_rels" / (p.name + ".rels")))
    if rels is None:
        return ""
    for r in rels.findall("rel:Relationship", NS):
        if r.get("Type", "").endswith(rtype_end):
            t = r.get("Target", "")
            parts = []
            for seg in (p.parent / t).parts:
                if seg == "..":
                    parts.pop()
                else:
                    parts.append(seg)
            return "/".join(parts)
    return ""


def pptx_info(z: zipfile.ZipFile) -> dict:
    info = {"kind": "pptx"}
    master = "ppt/slideMasters/slideMaster1.xml"
    theme_part = rels_target(z, master, "/theme") or "ppt/theme/theme1.xml"
    info["theme"] = theme_info(xml(z, theme_part))
    pres = xml(z, "ppt/presentation.xml")
    if pres is not None:
        sz = pres.find("p:sldSz", NS)
        if sz is not None:
            info["size"] = (int(sz.get("cx", 0)) / EMU_IN, int(sz.get("cy", 0)) / EMU_IN)
    layouts = []
    for n in sorted((n for n in z.namelist() if re.match(r"ppt/slideLayouts/slideLayout\d+\.xml$", n)),
                    key=lambda s: int(re.findall(r"\d+", s)[-1])):
        r = xml(z, n)
        c = r.find("p:cSld", NS) if r is not None else None
        layouts.append((c.get("name") if c is not None else "") or PurePosixPath(n).stem)
    info["layouts"] = layouts
    m = xml(z, master)
    sizes = {}
    if m is not None:
        for key, path in (("title", "p:txStyles/p:titleStyle/a:lvl1pPr/a:defRPr"),
                          ("body", "p:txStyles/p:bodyStyle/a:lvl1pPr/a:defRPr"),
                          ("body2", "p:txStyles/p:bodyStyle/a:lvl2pPr/a:defRPr")):
            el = m.find(path, NS)
            if el is not None and el.get("sz"):
                sizes[key] = int(el.get("sz")) / 100.0
    info["master_sizes"] = sizes
    info["slides"] = len([n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)])
    return info


def w_attr(el, name):
    return el.get(W + name) if el is not None else None


def font_of(rpr, theme) -> str:
    if rpr is None:
        return ""
    rf = rpr.find("w:rFonts", NS)
    if rf is None:
        return ""
    names = []
    for direct, th in (("ascii", "asciiTheme"), ("eastAsia", "eastAsiaTheme")):
        v = w_attr(rf, direct)
        if not v and w_attr(rf, th):
            t = w_attr(rf, th)
            kind = "major" if t.startswith("major") else "minor"
            v = theme[kind].get("ea" if "EastAsia" in t else "latin", "") + f" ({t})"
        if v and v not in names:
            names.append(v)
    return " / ".join(names)


def docx_info(z: zipfile.ZipFile) -> dict:
    info = {"kind": "docx"}
    theme = theme_info(xml(z, "word/theme/theme1.xml"))
    info["theme"] = theme
    st = xml(z, "word/styles.xml")
    styles = {}
    if st is not None:
        d = st.find("w:docDefaults/w:rPrDefault/w:rPr", NS)
        dsz = w_attr(d.find("w:sz", NS), "val") if d is not None and d.find("w:sz", NS) is not None else None
        info["default"] = {"font": font_of(d, theme), "size": int(dsz) / 2 if dsz else None}
        want = {"title": "Title", "heading 1": "Heading 1", "heading 2": "Heading 2", "heading 3": "Heading 3",
                "normal": "Normal", "caption": "Caption"}
        for s in st.findall("w:style", NS):
            nm = w_attr(s.find("w:name", NS), "val") or ""
            key = want.get(nm.lower())
            if not key:
                continue
            rpr, ppr = s.find("w:rPr", NS), s.find("w:pPr", NS)
            szel = rpr.find("w:sz", NS) if rpr is not None else None
            col = rpr.find("w:color", NS) if rpr is not None else None
            sp = ppr.find("w:spacing", NS) if ppr is not None else None
            line = w_attr(sp, "line")
            rule = w_attr(sp, "lineRule") or "auto"
            styles[key] = {
                "font": font_of(rpr, theme),
                "size": int(w_attr(szel, "val")) / 2 if szel is not None and w_attr(szel, "val") else None,
                "bold": rpr is not None and rpr.find("w:b", NS) is not None and w_attr(rpr.find("w:b", NS), "val") not in ("0", "false"),
                "color": (w_attr(col, "val") or "").upper() if col is not None else "",
                "before": int(w_attr(sp, "before")) / 20 if w_attr(sp, "before") else None,
                "after": int(w_attr(sp, "after")) / 20 if w_attr(sp, "after") else None,
                "line": (int(line) / 240 if rule == "auto" else f"{int(line) / 20}pt") if line else None,
            }
    info["styles"] = styles
    doc = xml(z, "word/document.xml")
    if doc is not None:
        sects = doc.findall(".//w:sectPr", NS)
        if sects:
            s = sects[-1]
            pg, mar = s.find("w:pgSz", NS), s.find("w:pgMar", NS)
            if pg is not None:
                info["page"] = (int(w_attr(pg, "w") or 0) / 1440, int(w_attr(pg, "h") or 0) / 1440)
            if mar is not None:
                info["margins"] = {k: int(w_attr(mar, k) or 0) / 1440 for k in ("top", "bottom", "left", "right")}
    return info


def fmt(v, unit="") -> str:
    if v is None or v == "":
        return "-"
    if isinstance(v, float):
        v = ("%.2f" % v).rstrip("0").rstrip(".")
    return f"{v}{unit}"


def render(info: dict, src: str, lang: str) -> str:
    kr = lang == "kr"
    t = info["theme"]
    c = t["colors"]
    L = []
    L.append(f"# DESIGN (추출 초안: {Path(src).name})" if kr else f"# DESIGN (extracted draft: {Path(src).name})")
    L.append("<!-- design_extract.py가 파일 내부 값(theme XML)을 그대로 읽은 초안. 역할 매핑은 제안이므로 사용자 확인 후 확정. -->" if kr else
             "<!-- Draft read verbatim from the file's theme XML by design_extract.py. Role mapping is a suggestion; confirm with the user. -->")
    L += ["base: (프로젝트 DESIGN.md의 base를 그대로 둔다)" if kr else "base: (keep the base line of the project DESIGN.md)",
          "style: (없음)" if kr else "style: (none)",
          f"source: {src} (theme-xml)",
          f"template_{info['kind']}: {src}", ""]
    L.append("## 색" if kr else "## Colours")
    L.append("| 역할(제안) | HEX | 테마 슬롯 |" if kr else "| Role (suggested) | HEX | Theme slot |")
    L.append("| --- | --- | --- |")
    for role, slot in (("primary", "accent1"), ("secondary", "accent2"), ("accent", "accent3"), ("text", "dk1"),
                       ("text-2", "dk2"), ("background", "lt1"), ("background-2", "lt2")):
        L.append(f"| {role} | {('#' + c[slot]) if c.get(slot) else '-'} | {slot} |")
    others = [s for s in SLOTS if s in c and s not in ("accent1", "accent2", "accent3", "dk1", "dk2", "lt1", "lt2")]
    if others:
        L.append(("- 나머지 슬롯: " if kr else "- Other slots: ") + ", ".join(f"{s} #{c[s]}" for s in others))
    L.append("")
    L.append("## 글꼴" if kr else "## Fonts")
    L.append(f"- {'제목(major)' if kr else 'Headings (major)'}: {t['major'].get('latin') or '-'} / {('한글' if kr else 'East Asian')} {t['major'].get('ea') or '-'}")
    L.append(f"- {'본문(minor)' if kr else 'Body (minor)'}: {t['minor'].get('latin') or '-'} / {('한글' if kr else 'East Asian')} {t['minor'].get('ea') or '-'}")
    if info["kind"] == "pptx":
        ms = info.get("master_sizes", {})
        L.append(f"- {'마스터 크기' if kr else 'Master sizes'}: title {fmt(ms.get('title'), 'pt')}, body {fmt(ms.get('body'), 'pt')}, body lvl2 {fmt(ms.get('body2'), 'pt')}")
        L += ["", "## 레이아웃 (PPT)" if kr else "## Layout (PPT)"]
        sz = info.get("size")
        if sz:
            L.append(f"- {'슬라이드 크기' if kr else 'Slide size'}: {fmt(sz[0])}\" x {fmt(sz[1])}\"")
        L.append(f"- {'슬라이드 마스터 레이아웃' if kr else 'Slide master layouts'} ({len(info['layouts'])}): " + (", ".join(info["layouts"]) or "-"))
        L.append(f"- {'참고 파일 슬라이드 수' if kr else 'Slides in reference'}: {info.get('slides', 0)}")
    else:
        dfl = info.get("default", {})
        L.append(f"- {'문서 기본값' if kr else 'Document default'}: {dfl.get('font') or '-'}, {fmt(dfl.get('size'), 'pt')}")
        L += ["", "## Word 스타일" if kr else "## Word styles",
              "| 스타일 | 글꼴 | 크기 | 굵게 | 색 | 앞/뒤 간격 | 줄 간격 |" if kr else "| Style | Font | Size | Bold | Colour | Before/after | Line |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
        for k in ("Title", "Heading 1", "Heading 2", "Heading 3", "Normal", "Caption"):
            s = info["styles"].get(k)
            if s:
                L.append(f"| {k} | {s['font'] or '-'} | {fmt(s['size'], 'pt')} | {'Y' if s['bold'] else '-'} | "
                         f"{('#' + s['color']) if s['color'] and s['color'] != 'AUTO' else '-'} | {fmt(s['before'], 'pt')}/{fmt(s['after'], 'pt')} | {fmt(s['line'])} |")
        L += ["", "## 여백·격자" if kr else "## Margins and grid"]
        if info.get("page"):
            L.append(f"- {'용지' if kr else 'Page'}: {fmt(info['page'][0])}\" x {fmt(info['page'][1])}\"")
        if info.get("margins"):
            m = info["margins"]
            L.append(f"- {'여백' if kr else 'Margins'}: top {fmt(m['top'])}\" bottom {fmt(m['bottom'])}\" left {fmt(m['left'])}\" right {fmt(m['right'])}\"")
    L += ["", "## 미확인" if kr else "## Unverified",
          "- UNVERIFIED: 역할 매핑(primary 등), 표·차트 규칙, 금지 사항은 사용자 확인 필요" if kr else
          "- UNVERIFIED: role mapping (primary etc.), table/chart rules and don'ts need user confirmation"]
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--out", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--lang", choices=["kr", "en"], default="kr")
    a = ap.parse_args()
    p = Path(a.file)
    ext = p.suffix.lower()
    if ext not in (".pptx", ".potx", ".pptm", ".docx", ".dotx", ".docm"):
        print("error: give a .pptx/.potx/.docx/.dotx file. Images and PDFs: read them yourself and mark values "
              "'UNVERIFIED: colour value (estimated from image)'.", file=sys.stderr)
        return 2
    try:
        with zipfile.ZipFile(p) as z:
            info = pptx_info(z) if ext.startswith((".pp", ".po")) else docx_info(z)
    except (zipfile.BadZipFile, OSError) as e:
        print(f"error: cannot open {p}: {e}", file=sys.stderr)
        return 2
    text = render(info, p.as_posix(), a.lang)
    if a.out:
        o = Path(a.out)
        if o.exists() and not a.force:
            print(f"error: {o} exists (use --force, or write elsewhere and merge by hand)", file=sys.stderr)
            return 1
        o.parent.mkdir(parents=True, exist_ok=True)
        o.write_bytes((text).encode("utf-8"))
        print(f"wrote {o}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
