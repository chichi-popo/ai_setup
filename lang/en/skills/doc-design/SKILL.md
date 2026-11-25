---
name: doc-design
description: Decide and apply the look of PPT and Word deliverables (colours, fonts, margins, slide master, Word styles) from a reference or the project DESIGN.md, before the pptx/docx skill builds the file. Use whenever a .pptx or .docx is created or restyled.
---
# doc-design

Owns the look only (colours, fonts, margins, layout, master, styles). Content structure belongs to `ppt-structuring` and `tech-writing`; the account pptx/docx skills build the file.

## Loop contract
- Success: every value used traces to `.ai/design/DESIGN.md` -> `style:` -> `base:`. Charts and tables are editable native objects. Rendered images show no overflow, overlap or contrast problems. No source value, label or unit is missing.
- Verifier: look at the rendered slide/page images yourself and tick the checklist item by item. Numbers: `evidence-verifier` (if present).
- Stop: after 2 rounds of fixes following a render, report the remaining layout problems as a list and stop. If reference values conflict with DESIGN.md, ask instead of choosing. When blocked, follow the BLOCKED rule in dispatch.md.

## Procedure
1. Read `.ai/design/DESIGN.md`. If missing, create it under `.ai/design/` from the template (AI_Tools `lang/en/DESIGN.template.md`) with the shared default path in `base:`.
2. Before building, ask whether the user can give a reference or template (.pptx/.potx/.docx/.dotx file, image/PDF, URL). If DESIGN.md already has `source:`, use it and do not ask again.
3. If there is a reference, read its values.
   - Office files: `python .claude/skills/doc-design/design_extract.py <file> --out .ai/design/extract_<name>.md` returns the theme values verbatim (colour slots, heading/body fonts including East Asian fonts, slide size and layout names, Word styles and margins).
   - Images, PDFs, URLs: look and write estimates marked `UNVERIFIED: colour value (estimated from image)`.
   - Confirm the role mapping (primary, secondary, accent) and the don'ts with the user, then copy them into DESIGN.md. Put template files in `template_pptx:` / `template_docx:` and register them with `python .ai/kb.py new asset <path>`.
4. Without a reference, use DESIGN.md and base. If a new mood is needed and an approved catalogue skill (pptx-design-styles or similar) is on, show 2-3 candidates and write the chosen name in `style:`. Formal reports, paper and patent talks prefer base.
5. Fix the master (PPT) or styles (Word) first: canvas size, title/body/footer slots, margin grid, layout kinds (cover, agenda, section, body 1/2 columns, table/chart, closing). With a template file, build on that file instead of imitating it. In Word, modify the built-in styles (Title, Heading 1-3, Normal, Caption).
6. Build with the pptx/docx skill. Charts and tables as native objects; colours only from the palette.
7. Render every page/slide to an image, check, and fill in the checklist. Record the approved DESIGN.md hash per the approval rule in dispatch.md.

## Checklist
- [ ] Asked about a reference (or used DESIGN.md `source:`)
- [ ] Colours stay in the DESIGN.md palette and one colour dominates
- [ ] Fonts and sizes stay in the DESIGN.md ranges (East Asian font included)
- [ ] One master/style set throughout (no per-slide margin or title moves)
- [ ] Charts and tables are editable and carry every source value, label and unit (omissions reported)
- [ ] Renders show no overflow, overlap or contrast problems

## Don'ts
- Copying this skill into a project to edit it (values go in DESIGN.md only).
- Using colours estimated from an image as if confirmed.
- Delivering a docx that imitates an HWP form as the official submission (HWP: content draft only by default and a person moves it into the form. Only when the `hwpx` skill is installed and the user asks for a file, save a `.hwpx` and tell them to open it in Hancom to check).
- Turning on a compressed-reply skill while writing reports, papers or patents.
