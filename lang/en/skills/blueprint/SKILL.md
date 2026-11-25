---
name: blueprint
description: Fill .ai/BLUEPRINT.md (the 설계서 build contract) by asking questions before building a new app or web project. Use before any coding when a new app/web project has no .ai/BLUEPRINT.md, or when the user runs /blueprint or asks for a 설계서.
---
# blueprint

## Loop contract
- Success criterion: every field of the blueprint (features, screens, data, three security lines) is filled or left as `[TODO]` in the question list, and the user approved it. No feature, screen or table absent from the blueprint exists in the code.
- Verifier: user approval (human gate). Then, if `system-architect` is available, it reviews data, security and stack in its design dialogue. Optionally `reviewer` checks that the implementation matches the blueprint.
- Stop condition: if the same field gets no answer after two questions, or the blueprint is edited three times without approval, stop and summarize the remaining fields and options for the user. If blocked, follow the BLOCKED rule in dispatch.md.

## Procedure
1. Read first: `.ai/INTENT.md`, `CLAUDE.md`, the repository (README, package and config files), and any existing `.ai/BLUEPRINT.md`. Do not ask what these already answer; say what you checked.
2. If `.ai/BLUEPRINT.md` exists, do not recreate it. Ask only about empty or `[TODO]` fields. If the extra instruction is a change request, fix the blueprint before the code, add one line to section 5, then read only the changed part and change only that part of the code.
3. Ask one question at a time. Ask only when the answer changes the design; otherwise propose a default with its reason. Do not re-ask what the user already decided. Early on, ask who uses it, what it is for, and what is not built this time as open questions without example answers. Mark what you chose as "my judgment", separate from what the user agreed. Write questions, explanations and summaries in the user's language (Korean if they write Korean) and never switch languages mid-conversation, including labels like "Question 3".
4. Write in the format below. The one-line description and project goal live in `.ai/INTENT.md` (link only here). If `.ai/INTENT.md` is empty, propose a draft from the same answers and record it only after approval.
5. When complete, get user approval (status: requirements approved; record the hash now per the approval-record rule in dispatch.md). Before approval, do not write code, scaffold, install dependencies or create the project (reading and exploring are fine). After approval, if `system-architect` is available, review data, security and stack in its design dialogue; if there are problems, report them to the user, ask or propose again, then fix the blueprint.
6. When the final decision is made, set the status to `final` and record the hash per the approval-record rule in dispatch.md, recording the hash again (if `approval_hash.py` is missing, write `UNVERIFIED: approval`). Re-approve after any later change. Implementation starts with `code-change` after final approval.
7. It is a new file, so register it with `python .ai/kb.py new asset .ai/BLUEPRINT.md`, and fill the card body: `What` (app name, users, number of screens and features in one line) and `When to read` (before implementing, changing or reviewing). When the blueprint changes, refresh the card summary and `updated`.

## Format (about 60 lines, one fact per line)
```
# 설계서: (app name)
Status: draft | requirements approved | final
Goal and scope: see .ai/INTENT.md

## 1. Features: who can do what
- (user 1):
- (user 2, e.g. admin):
Not built this time:
-

## 2. Screens: which screens, in what order
1. (screen name): what it must show
Common: (e.g. mobile first, large text, all text in Korean)

## 3. Data: the tables the app remembers
- (table name): column1, column2, column3

## 4. Security: three lines
1. Key storage: API keys live only in the environment variable file (.env). Never in screen code or on GitHub.
2. Login permissions: (who must log in, who can see what)
3. Database access rules: (enforce with database rules. e.g. a user cannot read another person's data)

## 5. Change log
- (date) (what changed and why)
```

## Do not
- Do not fill an ambiguous field on your own. If unknown, leave `[TODO]` and ask.
- Do not put features, screens or tables into the code that are not in the blueprint. If one seems needed, propose a blueprint change.
- Do not read `.env` or key values, and do not write them into the blueprint.

## Style
Use plain words. Add a one-line explanation to technical terms. Give numbers units.

Extra instruction: $ARGUMENTS
