---
description: Record or update project intent. Default is .ai/INTENT.md; a topic that is approved or changed separately goes to .ai/intent/intent_<slug>.md
disable-model-invocation: true
argument-hint: [topic-slug] [-- one-line description]
---
# /intent: record or update project intent

Argument: `$ARGUMENTS`

## Reading the argument
Use the first case that matches. A slug is lowercase ASCII letters, digits and hyphens, 30 characters or fewer.
1. Empty: the root `.ai/INTENT.md` is the target.
2. Contains `--`: the part before it is the topic and the part after it is a one-line description. If the topic is not slug-shaped, treat it as a topic name and propose a slug. If the part before is empty, it is the description-only case (case 4).
3. No `--` and the whole argument is slug-shaped: slug only.
4. Anything else (a sentence with non-ASCII text or spaces): description only.
A slug is only a label. Do not guess what it means.

## Choose the target
5. Read `.ai/INTENT.md` (if it is missing, create it with the sections: goal line / scope in and out / users / constraints / key decisions / open questions / completion check) and list `.ai/intent/intent_*.md`. If the target file already exists, follow "Update"; if not, follow "Create".
6. With a slug, the target is `intent_<slug>.md`. If no file matches exactly but a similar name exists (for example `opening` and `openings`), ask once whether to update it or create a new one. Typing a slug yourself is the decision to split, so do not ask about the split conditions; if they are not met yet, only say so in one line.
7. With a description only (no slug), compare it with the title and goal line of each listed file; if one covers the same topic, propose updating that file. Otherwise a change to the overall goal, scope, users or constraints goes to the root, and one limited to a specific feature, screen or document goes to a detail file. For a detail file, summarize the description into a 2 to 3 word slug (lowercase ASCII and hyphens, for example "door swing direction" becomes door-swing; use a different word if the name already exists). No split decision exists here, so check the split conditions (INTENT.md over 45 lines, two or three or more features approved or changed separately, parallel sessions); if none applies, recommend the root and follow the user's decision. Show the chosen slug on the first question line as `(file: intent_<slug>.md)` so the user can correct it.
8. With a slug only and no matching file, ask only for a one-line description of this intent. Do not build choices from a guessed meaning of the slug (such as tidying the root).

## Create
9. If the goal, audience, completion criterion or constraint is missing and the direction would change, ask one question at a time before writing. Attach a guess to each question (use `interview-me` if it is installed) and do not ask what the description already tells you. Before confirming, read back the out-of-scope items too, and write only after an explicit yes from the user. Leave anything not settled under `open questions` as `UNVERIFIED`.
10. A detail file is 40 lines or fewer, one fact per line: title (`# INTENT: <title>`) / parent relation / goal line / scope (in and out) / completion check / open questions / change log (date | one line, optional). It must not widen the root's out-of-scope list; if it needs to, propose the root change first. On conflict the root wins.
11. In the root, create or update one line of the `## Sub-intents` table (path | one line). The root stays at 60 lines or fewer.

## Update
12. Read the target file and show its current content in 3 lines or fewer.
13. With no description, ask once "what do you want to change or add?" and offer a guess: an item under `open questions` or an empty section. With a description, ask questions one at a time, each with a guess, to pin down how to apply it. For example, for "add a door swing direction option": which direction combinations are supported, and how the completion check changes.
14. Once settled, show the changed lines as `before → after` and apply only after an explicit yes from the user. If the file would pass 40 lines, shorten it or propose a split. Record a change of intent (moving something in or out of scope, a changed completion check) in the `change log` with the date and one line, and update the root table if the one-line summary changed.

## Common
15. Changes to an existing file are proposed first and applied after approval. For an approved file run `record <file>` with `.claude/hooks/approval_hash.py` if it exists. For a file outside version control, put a copy in `.ai/archive/intent/<file name>_<YYYYMMDD>.md` before changing it.
16. At the end report the written path and line count and do not start implementation. Implementation happens in a new session. Even if the argument mixes in a work instruction ("write a ..."), write only the intent file. Point to design (system-architect) and the test list as the next steps after the intent is approved.
