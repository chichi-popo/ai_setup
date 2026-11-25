# dispatch: single loop first, agents only when they pay for themselves
Default: the main session works alone with skills. Agents are tools; use 0-3 per task and never all three by reflex. For a task not in the table, work without agents and fix the success criterion, verifier and stop condition first.

## 1. Structure by task type
| Task | Agents (count) | Human approval | Why |
| --- | --- | --- | --- |
| Small code fix | none (0) | before commit | context stays continuous |
| Modify existing code | explorer only on first entry to the repo (0-1) | before commit | analysis feeds the edit |
| Complex feature | reviewer after tests pass (1) | right after design, before commit | independent check |
| Bug with several suspects | parallel explorers (2-3) | before commit | wide search, cost rises |
| Large refactor | parallel only for independent modules (§3), one per module | before commit | otherwise sequential in main |
| Tech stack comparison, literature or prior-art survey | one explorer per axis, parallel (2-3) | none | independent research |
| Report / paper / patent | evidence-verifier (1) | outline, final | numbers must match sources |
| PPT | evidence-verifier on slide numbers (1) | storyline, final | storyline and taste stay in main |
| Architecture / ADR | optional reviewer once before approval (0-1) | right after design | a human decides |
| UI/UX | none (0) | per screen | taste is iterated with the user |

For feature work, when the skills exist: requirements-analysis (if vague) → system-architect (new dependency, schema, public API or architecture; design dialogue and approval) → code-change.

## 2. Calling rules
- Before delegating: can it run without depending on my next step, can the result be judged from the output alone, is it a wide survey? If none, do it myself. Do not split sequential work by role, delegate one- or two-file edits, or call an agent to confirm my own result.
- Foreground by default. Parallel or background only when the time or thoroughness gain is clear; tell the user tokens rise.
- Agents do not inherit the conversation. Put all needed context (constraints included) in the task text and delegate one step at a time. Format: `step / goal line (required only when the outcome is clear) / read / write (output file name) / do not`
- Output contract: conclusion (1-3 lines), evidence, issues (max 5, by importance), Uncertainty, Next action. Ask follow-ups only when needed; do not request process logs.
- To the reviewer pass the request (goal line, success criteria), changed files and diff, check command and result, and the paths of the tests and validation data the change depends on (for the validity judgment); never chat history, reasoning or self-assessment. It is read-only; the main session reproduces or verifies each finding, fixes only valid ones, and reports rejected ones with reasons. Record counts in `reviewer_defects` and `rejected_findings` of `eval_log.csv`.

## 3. Parallel work
Parallel by default only for research. Independent module implementation runs in parallel only when all hold:
1. Interfaces are fixed and written down.
2. No shared mutable state or files between workers.
3. Each worker has its own git worktree or branch.
4. Each result can be verified alone (exit code of the test command).
5. The main session re-runs the full checks after merging; the reviewer judges only the merged result.

Run at most 2 heavy builds or test runs at the same time.

## 4. Model and effort level
Tiers, mapped to the models available (cost and names change). The user picks the main model.
- Classification, short summaries, file lists: low-cost (haiku-class), low
- Exploration, evidence gathering: low-cost to mid, low to medium
- Ordinary implementation, document drafts: mid (sonnet-class), medium
- Complex design, hard reasoning, security review: high-capability, high
- Final verification: match the difficulty of what is verified, medium to high

Change model, effort level or mode only at a task boundary (/clear); changing mid-session can invalidate the prompt cache.

## 5. hook vs skill
- hook (deterministic): format, lint, running tests; blocking dangerous commands, path limits; re-injecting memory after compaction.
- skill (judgment): coding approach, review procedure; problem-solving strategy; project knowledge, document structure.

## 6. External skills
Use only those approved through the review gate in `third_party/README.md`. Off by default. When approved, add one line of usage conditions to the table below; if it is not in the table, do not use it.
| skill | Presets that enable it | Usage condition | Approved on |
| --- | --- | --- | --- |
| interview-me | any preset (projects where `init_project.py --ext interview-me` was run) | At the start of a new feature, document or screen: at most 5 questions, one at a time. Not for bug fixes, small edits, maintenance or non-interactive runs. Save the result to INTENT (`.ai/INTENT.md` or `.ai/intent/`), not `docs/intent/` | 2026-11-25 |

## 7. Default stop conditions
Use these when a skill gives no value (delegation retries included). If the same step fails twice in a row, or the same issue is sent back three times, stop and report evidence, what was tried, and where it is stuck.

## 8. Approval record
For approved artifacts (spec, design note, outline, storyline, composition plan): if `.claude/hooks/approval_hash.py` exists, run `record <file>` to store the hash, and `check <file>` must return 0 before follow-up work. If the file changed after approval, get approval again. Without the hook, write `UNVERIFIED: approval`.

## 9. BLOCKED
If evidence, permission or input is missing, do not invent: write `blocked / tried / needed` to `.ai/BLOCKED.md`, then stop and report (fold into Uncertainty). A read-only agent writes `BLOCKED: <reason>` on the first line of its conclusion and the main session records it.
