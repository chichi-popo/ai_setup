---
name: code-change
description: Implement, fix or refactor code with a verifiable loop (surgical edits, independent tests, deterministic checks), then hand the result to the reviewer agent. Use for any code edit, bug fix, UI change or feature in a project that has a test/build command.
---
# code-change

## Loop contract
- Success criterion: the CLAUDE.md test/build command exits 0 and a deterministic check shows the goal line is true. The requested behavior is proven by a test that fails before the change and passes after. Calculation or decision logic needs 2+ independent pieces of evidence (hand calculation, two independent methods, property test); UI changes include a screen check.
- Verifier: deterministic command first. Non-trivial changes (more than about 3 files, security-related, public API) go next to the reviewer in a fresh context. The reviewer judges the result and also the validity of tests and validation data.
- Stop condition: if the same check fails twice in a row, or the reviewer FAIL sends the same issue back three times, stop, report evidence, and ask the user. Never repeat silently. If blocked, follow the BLOCKED rule in dispatch.md.

## Writing principles
- Simple: only the minimum code that solves the request. No features, abstractions or settings beyond the request; no error handling for cases that cannot happen.
- Touch only what must change: every changed line traces to the request. Do not reformat, rename, tidy or refactor code outside the request; follow existing style. Report other problems in the write-up instead of fixing them. Clean up only leftovers from my own change.
- Done means verified: do not say done before confirming with a command and its exit code ("it should work" is not evidence). Never make the final judgment on my own output.
- Reply: changed files, diff or code block, command + exit code, remaining risks only. No greeting, preamble or repeated summary. Comment only where the reason is not obvious.

## Procedure
1. Set the goal line and how to check it (use `.ai/INTENT.md` if it exists). If a design decision is implied (new dependency, schema, public API), stop before coding and ask (through the `system-architect` dialogue if that skill exists). For a big goal, first check that the environment readiness checklist in `.ai/repo_audit_map.md` is filled in.
2. First entry to an existing project: have `explorer` complete `.ai/repo_audit_map.md` before editing. Skip small tasks inside an already audited area.
3. Write or find the test first (bugs: reproduction test first, confirm it fails). I write the tests; the reviewer does not. Take expected values from independent evidence (spec, hand calculation, documents, existing results, another method), not from the implementation. Mix boundary, abnormal and typical values and avoid repeating the same input. Check a data generator for duplicates and bias.
4. Make only the smallest change that satisfies the test. Check the call sites and sibling paths of any changed function, API or schema (create/move vs update/delete, body vs query/header). Take credentials from environment variables or a secret manager (never hard-code them) and bind local services to localhost or the internal network.
5. Run the deterministic checks and paste the command and exit code.
   - Test/build/lint: the commands in the CLAUDE.md managed block. If `run_check.py` exists, run `python .claude/hooks/run_check.py -- <command>` (recorded in `.ai/last_check.json`).
   - Coverage: if `check_test_coverage.py` and a coverage report exist, run `python .claude/hooks/check_test_coverage.py --min <value> --files <changed files>`. Exit code 3 (no report): write `UNVERIFIED: coverage` and move on.
6. For UI changes, run it and check the screen (use a capture tool or deterministic UI check if available). Without a means, `UNVERIFIED: screen`.
7. Delegate non-trivial changes to the reviewer (input per the reviewer input rule in dispatch.md). Include the paths of related kb decision/progress cards (`.ai/kb/...`) in the task text when they exist.
8. Reproduce or verify each reviewer finding yourself, fix only the valid ones, and record the reason for rejected ones.
9. On FAIL, split by cause, go back only to that step, and rerun from step 5.
   - CODE: implementation -> step 4
   - TEST: tests/validation data -> step 3 (never fit expected values to the implementation)
   - SPEC: requirements -> requirements-analysis, confirm with the user
   - ENV: environment/tools -> report and stop
10. After the completion report, commit only with approval.

## Delegation
Follow `.claude/rules/dispatch.md` (0-3 agents, foreground, task format, output contract, parallel only for independent modules that meet every §3 condition).

## Report format
```
Goal: <goal line>
Changed: <files>
Check: <command> -> exit <code> (<passed n / failed n>)
Evidence: <2 independent pieces / screen check>  (calculation or decision logic, UI)
Review: PASS | FAIL | skipped (<reason>)
Findings: accepted <n> / rejected <n> (<one-line reason each>)
Open risks: <none | list, including UNVERIFIED>
```
