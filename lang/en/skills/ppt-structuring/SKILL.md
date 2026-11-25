---
name: ppt-structuring
description: Structure a presentation from existing work (3-point slide bullets plus a separate spoken script), then build the file with the pptx skill. Use for presentation and talk preparation.
---
# ppt-structuring

## Loop contract
- Success criterion: each slide has one message (the title states the conclusion), at most 3 bullets, and a script block. Every number on the slides matches the source report. Slide count and timing fit the talk length (about 1.5-2 minutes per content slide).
- Verifier: `evidence-verifier` checks slide numbers and claims against the source. The user reviews the storyline before the file is built (human gate).
- Stop condition: after 2 storyline revisions the user picks one of two structures. File building allows up to 2 fix rounds after rendering, then report the remaining layout issues. If blocked, follow the BLOCKED rule in dispatch.md.

## Procedure
1. Confirm audience, talk length, the decision or message wanted, and the source documents.
2. Write the storyline as a list of slide titles, each title a conclusion. Get approval and store the hash as dispatch.md's approval record rule says.
3. Make two separate blocks per slide.
   - Slide text: at most 3 noun-phrase bullets (no full sentences, keep it terse).
   - Spoken script: 2-4 conversational lines, including the hand-off to the next slide.
4. Where there is a comparison, use a chart or diagram instead of prose. Give every slide with data a source line.
5. Build the file with the pptx skill only after the storyline and numbers are approved (re-approve if the storyline changed). Put the script in the speaker notes. The look (master, colours, fonts, margins) follows the `doc-design` skill and `.ai/design/DESIGN.md` (if present).
6. Render each slide to an image and check overflow and readability.

## Template
```
### Slide <n>: <conclusion title>
Slide text:
- ...
- ...
- ...
Script: "..." (transition: ...)
Source: <file / section>
```
