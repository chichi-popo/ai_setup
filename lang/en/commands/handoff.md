---
description: Save this session's work summary to .ai/handoff.md (or .ai/handoff/handoff_<slug>.md for a separate topic)
disable-model-invocation: true
argument-hint: [focus topic] | [topic-slug -- focus]
---
# /handoff: record a session handoff

Argument: `$ARGUMENTS`

## Target and argument
- `<slug> -- focus`: write to `.ai/handoff/handoff_<slug>.md` and update the `## Active topics` table (topic | status | next action | file) in the root `.ai/handoff.md`. A new topic file is created only in this form (the part after `--` may be empty).
- A single slug-shaped word whose file already exists: update that topic file.
- Anything else (including an empty argument): write to `.ai/handoff.md` and treat the whole argument as the focus topic or instruction. With a focus, summarize mainly that topic and cut everything else to one line or less.
- A slug is lowercase ASCII letters, digits and hyphens, 30 characters or fewer (put a non-English topic name in the H1). After writing, if two or more tracks are active or the root exceeds 100 lines, suggest splitting in one line.

## Previous version
If the target file exists, copy it before overwriting to `.ai/archive/handoff/<file name>_<previous written date YYYYMMDD>.md` (the written date is the first line `# Handoff (date)`, else the modified date; append `_2` if the name exists). Do not create `.bak_` files, and write the copied path in one line at the top of the new file.

Analyze the conversation and code changes and write these four sections.

## 1. Goal and current state
- The problem being solved and a summary of how much is done

## 2. Files changed or created
- Changed file paths and the key change in each (do not paste whole code)

## 3. Key technical decisions and dead ends
- The chosen approach, constraints, failed approaches: context the next session must not repeat. Suggest raising decisions it must not repeat to a card with `python .ai/kb.py new decision|issue --title "..."` (run only after approval).

## 4. Next steps
- Concrete action items to run right away
