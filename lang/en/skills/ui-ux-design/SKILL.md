---
name: ui-ux-design
description: Propose screen structure, user flows, states, and UI copy for web/app features, then iterate with the user. Use for UI/UX design and critique before frontend implementation.
---
# ui-ux-design

## Loop contract
- Success criterion: every screen has a purpose, a primary action, all states (empty, loading, error, success, no permission) and the wording of every label and message. Each user flow reaches its goal within the set number of steps. Accessibility basics (contrast, keyboard path, touch target) are checked.
- Verifier: the user reviews each screen (iterative, taste-based work, so it runs in the main session, not an agent). Optionally the `reviewer` makes a last pass with the checklist below.
- Stop condition: if one screen does not converge after 3 revisions, show two alternatives side by side and let the user choose. If blocked, follow the BLOCKED rule in dispatch.md.

## Procedure
1. Confirm users, task, device, and the requirement IDs this screen satisfies.
2. Draw the flow first in Mermaid: nodes (screens) and edges (actions), including failure paths.
3. For each screen decide layout regions, components, states and copy. Reuse the project's design tokens and components; never add a new component quietly, list it as a request.
4. Checklist: one primary action per screen. Destructive actions ask for confirmation. Errors say what happened and what to do. Touch target 44 px or more. Text contrast 4.5:1 or more. Every flow works by keyboard.
5. When handing off to implementation, include the component list, state table and copy table.

## Output template
```
## Screen: <name>  (requirements: <ID>)
Purpose / primary action:
Regions: ...
| State | What the user sees | Copy |
Accessibility notes:
Open questions:
```
