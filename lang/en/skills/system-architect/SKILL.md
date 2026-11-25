---
name: system-architect
description: Design app/web system architecture with options, trade-offs, a Mermaid structure diagram, and an ADR. Use after requirements are approved or when evaluating architecture changes.
---
# system-architect

## Loop contract
- Success criterion: every architecture decision has 2+ options compared on criteria taken from the approved requirements, a recommendation, and an ADR. Every non-functional requirement maps to an implementation mechanism.
- Verifier: the user approves the design (human gate). Optionally the `reviewer` checks consistency of the diagram, the ADR and requirement coverage.
- Stop condition: if design edits continue 3 times without approval, summarize the disagreement and ask the user to decide. The agent never finalizes a decision alone. If blocked, follow the BLOCKED rule in dispatch.md.

## Procedure
1. Read the approved spec. For a big goal, check that the environment readiness checklist in `.ai/repo_audit_map.md` is filled in. List the non-functional drivers first (load, latency, security, deployment, team skills, budget). If a parent intent file exists (`.ai/INTENT.md` or `.ai/intent/intent_<slug>.md`), put its path on the first line of the design doc; do not make decisions that widen the intent's out-of-scope list, raise them as open questions (`UNVERIFIED`).
2. Narrow the design by Socratic dialogue first. Do not ask what the repository, spec or material already answers; say what you checked. Ask one question at a time, and only when the answer would change the design (otherwise propose a default with the reason). Early on, ask open questions without example answers about the goal, why now, success criteria and non-goals; after that, build each question on the user's last answer. Once the why is clear and the choices can be named, show each option with concrete pros and cons and your recommendation. Do not re-ask what the user already decided. For a small or already clear request, skip the questions: present the design and ask for approval.
3. For each component set the name, responsibility, interface and state owner. One owner per piece of state.
4. For each major decision tabulate the options: criteria x options, with evidence or marked "assumption".
5. Draw the structure in Mermaid (context, container, key sequence). Keep one diagram to about 15 nodes or fewer.
6. Play the design back in chunks of about 200-300 words (what you understood), each followed by a confirming question. Mark your own choices as "my call", separate from what the user agreed.
7. Write the ADR. Before approval, do not write code, scaffolding, install dependencies or create projects (reading and exploring are fine). Status stays `Proposed` until the user approves. When approved, change it to `Accepted` and store the hash as dispatch.md's approval record rule says; get re-approval if the design changes after approval. For a project-level decision, propose one line plus the ADR link for the decision log in `.ai/INTENT.md` (record after approval).
8. List risks, what could not be verified, and the cheapest experiment that would reduce each risk.

## ADR template
```
# ADR-<n>: <decision>
Status: Proposed | Accepted | Superseded
Context: <drivers, constraints, requirement IDs>
Options: <A / B / C, one line of pros and cons each>
Decision: <chosen option>  (approved by: <user, date>)
Consequences: <good, bad, follow-up work>
```

## Style
Write comparisons as tables. No adjectives without numbers. Separate "confirmed" from "assumed".
