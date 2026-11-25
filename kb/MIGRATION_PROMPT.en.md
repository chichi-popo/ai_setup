# Migration prompt: `.ai/memory` -> kb cards (paste into Claude Code as is)

```
Move the documents in .ai/memory/ (plan, checklist, context, memory, ...) into kb cards. Split, do not summarize.

Rules
1. The originals are already kept verbatim under .ai/archive/legacy-v8/. Do not edit or delete .ai/memory files.
2. By default one section (##, ###) becomes one card; split sections longer than 40 lines by topic.
   Copy sentences as they are; do not shorten or rewrite them (only write a new one-line title).
3. Types
   - checklist / plan step tables and remaining work -> progress (one milestone = one card, keep the checkboxes)
   - decisions and approved recommendations in plan (IDs like H1, L3) -> decision (one decision = one card; keep the original ID in the card id: D-M8-L3)
   - problem -> fix -> rule entries in memory.md -> issue (by topic)
   - structure, invariants, directories in context.md -> map (by area)
   - docs/, .ai/scripts/, design files -> asset (`python .ai/kb.py new asset <path>`, one-line summary)
4. Create each card with `python .ai/kb.py new <type> --id <id> --title "<title>" --tags a,b --related X,Y`, then fill the body.
   Link related cards with related and [[id]] in the body (progress card -> the decision cards of that step).
   updated = the date written in the original (today if none).
5. Progress cards of finished milestones get status: done.
6. Write .ai/NOW.md in 10 lines or fewer: what is in progress, next action (1-2 items backed by the checklist; wait for approval), blockers. Point to cards with [[id]].
7. Finally run and show:
   python .ai/kb.py check --coverage .ai/archive/legacy-v8/<date>/.ai/memory
   Keep adding missing content as cards until MISSING is 0 and ERROR is 0. Only list the WARN lines.
8. Do not cd to another folder in Bash; run every command with paths relative to the project root.
9. Report the card count, INDEX.md size in bytes and remaining WARN lines, then stop. I will retire .ai/memory myself with migrate_v8.py --retire-memory after approving.
```
