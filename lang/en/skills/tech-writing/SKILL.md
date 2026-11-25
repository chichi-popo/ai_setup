---
name: tech-writing
description: Write result reports, papers, and patent drafts with numeric evidence and an academic register. Use for reports, papers, patent specifications and claims.
---
# tech-writing

## Loop contract
- Success criterion: (1) every number, quote and reference matches a source file (path + location). (2) The structure follows the approved outline. (3) No adjective lacks evidence. For patents, the detailed description supports every claim element.
- Verifier: a fresh-context `evidence-verifier` receives only the draft and the source list and returns a table: claim | source | MATCH / MISMATCH / NO SOURCE. Format (headings, numbering, reference style) is checked by script or docx/pdf skill output.
- Stop condition: if MISMATCH or NO SOURCE remains after two fix-and-verify rounds, stop and report to the user. Never cover a gap by polishing sentences. If blocked, follow the BLOCKED rule in dispatch.md.

## Procedure
1. Confirm type (report / paper / patent), reader, purpose in one line, length and language. Get outline approval before drafting and store its hash as dispatch.md's approval record rule says.
2. Build the evidence list from project assets (the document section of CLAUDE.md, section 5 of `.ai/repo_audit_map.md`, result files). Give each fact an ID `E1, E2...`.
3. Draft section by section. While writing, attach evidence IDs in the text; convert them to the final citation format at the end.
4. Verify with `evidence-verifier`. Fix the draft to match the source on MISMATCH, never the reverse.
5. Keep compression or terse-output skills off while writing (they hurt report quality).
6. For a revision request on an existing manuscript, read `revise_prompts.md` and `humanize_patterns.md` and follow their common procedure and applicability table. Report completion only when `numcheck.py` prints `SAME`.

## Style rules
- No cliches ("many people are ...", "in conclusion", "to sum up") or obvious moral closers. Do not use "moreover", "furthermore", "therefore" out of habit; show links through subject and causality. Formulaic patent claim/specification wording is exempt.
- Replace exaggerated or abstract modifiers ("pivotal", "innovative", "in-depth") with concrete facts and conditions.
- Mix short and long sentences. Avoid a teaching or over-friendly tone; write as a practitioner explaining plainly.
- Every sentence adds information the reader did not already have. Do not write a one-line closer that repeats the previous sentence, a run-up before the point ("We now look at..."), an objection no one raised ("One might think... but"), or a contrast that denies something no one claimed ("not X but Y"). Use a negation only to correct a belief the reader actually holds.
- Replace degree modifiers ("accurate", "various", "meaningful") with a criterion, range or condition, or drop them. Do not use unsourced authority ("studies show", "industry experts") or unsupported speculation or outlook. Terse list-style entries are the document's register; keep them.
- Add no speculation or generalities beyond the facts, numbers and experience the user provided. Never change or invent experimental numbers, variable names or logic structure.
- Objective register. Use passive or neutral phrasing where natural; no emotional intensifiers such as "very excellent" or "amazing".
- Use numbers: "latency fell from 120 ms to 45 ms (62.5% reduction, 30 runs)". State conditions, baseline and sample size.
- Write limitations in a separate paragraph.
- Paper: abstract (problem, method, results with numbers, implication) -> related work -> method -> experiments -> discussion -> limitations.
- Patent: background -> summary -> drawing description -> detailed description -> claims. Write the independent claim first and narrow with dependent claims. Define each term once and use it identically. Avoid "always", "never", "best" in claims.
- Patent and legal wording is a draft for expert review; do not assert legal conclusions.
- Do not: cite a source you have not opened, decide the conclusion first and fit evidence to it, change the content or structure of sections that were not requested.

## Output
Draft file + `evidence_table.md` (ID | fact | source path | location) + a list of remaining gaps. For a Word file, the look follows the `doc-design` skill and `.ai/design/DESIGN.md` (if present).
