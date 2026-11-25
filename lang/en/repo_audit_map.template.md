# repo_audit_map: {{PROJECT}}

> Status: draft made by init_project.py ([auto] = filled automatically). The explorer completes the [TODO] items.
> Rules: every statement carries `path:line` evidence. No guesses; unknown = `UNKNOWN`. Read-only (never edit source). Excluded, never opened: .env*, *.pem, *.key, credentials*, secrets*.

## 0. Verdict header (filled by the explorer last)
- Audit result: [TODO: COMPLETE | PARTIAL | BLOCKED]
- Audit time: [TODO: date, commit hash]
- Confidence: [TODO: high | medium | low, one-line reason]

## 1. Stack and commands [auto]
| Stack | Package manager | Main dependencies |
| --- | --- | --- |
{{STACK_ROWS}}

| Command | Value | Verification (exit code) |
| --- | --- | --- |
| build | [TODO] | [TODO] |
| test | [TODO] | [TODO] |
| lint | [TODO] | [TODO] |
| run | [TODO] | [TODO] |

## 2. Entry points [auto candidates, confirmed by the explorer]
{{ENTRY_ROWS}}

| Entry point | Role | Evidence (path:line) |
| --- | --- | --- |
| [TODO] | [TODO] | [TODO] |

## 3. Structure and dependencies
- Source file count (auto): {{CODE_FILES}}
- Top-level layout: [TODO: directory -> role, one line each]
- Module dependency direction: [TODO: A -> B, mark cycles]
- External services (DB, API, queue): [TODO: name, config location]
- Build/CI files: [TODO]

## 4. Tests and quality baseline
| Item | Value | Evidence |
| --- | --- | --- |
| Test files / framework | [TODO] | |
| Last run result | [TODO: passed/failed counts] | |
| Coverage (if measurable) | [TODO: % or UNKNOWN] | |
| Lint / type-check status | [TODO] | |

## 5. Document / research / patent assets [auto count]
- Summary: {{DOC_SUMMARY}}

| Asset | Type | Topic (one line) | Linked code/results | Citable as evidence |
| --- | --- | --- | --- | --- |
| [TODO] | paper/patent/report/spec | | | yes/no |

## 6. Risks and unknowns
| Risk / unknown | Why it matters | Next check |
| --- | --- | --- |
| [TODO] | | |

## 7. Map of where it is safe to change
- Low risk (tested, isolated): [TODO]
- High risk (untested, shared state, many dependents): [TODO]
- Do not touch (generated, vendored): [TODO]

## 8. Recommended first task
- [TODO: one task, with success criterion, verifier and stop condition]

## 9. Environment readiness checklist (if empty, fill it before a big goal)
| Area | Means | Status (OK / none / UNKNOWN) |
| --- | --- | --- |
| Can see | [TODO: screen capture, render means] | |
| Can know | [TODO: spec, decision records, `.ai/INTENT.md`] | |
| Can verify | [TODO: tests, fake services, data-access MCP] | |
