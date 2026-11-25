---
name: requirements-analysis
description: Turn requirement documents or rough requests into a structured specification with ambiguity questions. Use before design when input is a document, RFP, meeting note, or vague request.
---
# requirements-analysis

## Loop contract
- Success criterion: every requirement has an ID, a source location (file:page/line), a verifiable acceptance condition and a priority. Every ambiguity is either resolved by the user or listed as an open question. No requirement lacks a source.
- Verifier: a fresh-context `evidence-verifier` compares the spec with the source and reports requirements without a source and source statements not carried into a requirement.
- Stop condition: if the verifier returns FAIL twice or unresolved ambiguities exceed 10, stop and ask the user which to resolve first. If blocked, follow the BLOCKED rule in dispatch.md.

## Procedure
1. Set the goal line and scope (in/out). Mandatory only when the outcome is clear; optional for creative or exploratory work. For project-level goals put it in `.ai/INTENT.md`; if it already exists, only propose changes and record them after human approval.
2. List the input documents and their size. Leave reading of large inputs to `explorer` and receive an index (section -> topic), not the full text.
3. Extract requirements with these columns: ID | statement | type (functional / non-functional / constraint) | source | acceptance condition | priority.
4. Separate facts from assumptions. Mark assumptions `ASSUMPTION` and list them for approval.
5. Build the ambiguity list: question | why it blocks | options and default. If there are several interpretations, never pick one silently. Ask the user one at a time, and never ask what the document already answers.
6. Mark dependencies between requirements (A needs B). Do not split ordered work across several agents.
7. Get user approval. Store the hash of the approved spec as dispatch.md's approval record rule says, and get re-approval if it changes. Start design only after approval.

## Output template
```
# Spec: <name>  (source: <file>)
## Requirements
| ID | Statement | Type | Source | Acceptance condition | Priority |
## Assumptions (approval needed)
## Open questions
| # | Question | Blocks | Options (default first) |
## Out of scope
```
`.ai/INTENT.md` format (60 lines or fewer, one fact per line): goal line / scope in and out / constraints / key decisions (date | decision | reason | evidence link) / open questions / completion check.
INTENT storage and splitting (single file by default): automatic flows write only the root `.ai/INTENT.md`. Detailed intent files (`.ai/intent/intent_<slug>.md`) are created by the rules of the `/intent` command.

## Style
Write neutrally; no persuasive wording. Give numbers units. Quote legal or contractual text verbatim.
