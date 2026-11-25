---
description: Show how to apply AI_Tools presets and stack bundles to a project (init_project.py usage, preset summary, examples)
disable-model-invocation: true
---
# /ai-guide: AI_Tools usage guide (v2.4.6)

Show the guide below as is. If `$ARGUMENTS` is given, show only that topic's section (`presets`, `stack`, `skill`, `ext`, `commands`, `examples`, `cautions`). If the tool folder is not `C:\AI_Tools`, read paths as the folder that holds `init_project.py`. If a list looks outdated, read `roster.yaml` in the tool folder and report the difference (do not edit it).

## Basic flow
1. See what would be copied with `--dry-run`. 2. Apply. 3. Merge hooks and deny rules with `merge_settings.py`. 4. If the project uses a language, add its checklist bundle with `--stack`, only the skills you need with `--skill`, and external skills one at a time with `--ext`.

## Main commands
```powershell
python C:\AI_Tools\init_project.py --root <project> --preset <name> --dry-run
python C:\AI_Tools\init_project.py --root <project> --preset <name>
python C:\AI_Tools\merge_settings.py <project>
python C:\AI_Tools\init_project.py --root <project> --stack vue-ts,python-ml --dry-run
python C:\AI_Tools\init_project.py --check-lang; python C:\AI_Tools\hooks\selftest_hooks.py; python C:\AI_Tools\tests\selftest_v24.py
```
- `--preset`: `apply_preset` copies the preset's skills, agents, rules, and knowledge stubs into the project's `.claude/` and also creates CLAUDE.md, `.ai/` (kb, INTENT), and AGENTS.md. Existing files are kept.
- `--stack` (without `--preset`): copies only the bundle's rule files into `.claude/rules/`. It touches nothing else, so it is safe for existing projects.
- `--force`: overwrites existing files, including filled `project-*` stubs and rules you edited, so diff first.

## Preset summary (per roster.yaml)
| Preset | Use | skills | agents | Note |
|---|---|---|---|---|
| `base` | common base | code-change | explorer, reviewer | rule dispatch |
| `new-fullstack` | new app or web development | + requirements-analysis, blueprint, system-architect, ui-ux-design | same as base | 4 knowledge stubs, design approval gate |
| `legacy-maintenance` | changing existing code | code-change | explorer, reviewer | write repo_audit_map on first entry |
| `research-code` | research and experiment code | code-change | explorer, reviewer | notebook or experiment exit code is the check |
| `doc-analysis` | document and requirements analysis | requirements-analysis, doc-design | explorer, evidence-verifier | pdf, docx |
| `ux-design` | screen design | ui-ux-design | explorer, evidence-verifier | taste decisions in the main session |
| `report-ppt` | reports and presentations | tech-writing, ppt-structuring, doc-design | explorer, evidence-verifier | docx, pptx, xlsx |
| `paper-patent` | papers and patents | tech-writing, doc-design | explorer, evidence-verifier | WebSearch, docx, pdf |
| `research` | web research | tech-writing | researcher, explorer, evidence-verifier | WebSearch, WebFetch, source URL and access date required |

## Stack bundles
| Bundle | Rule file | Loads when |
|---|---|---|
| `python-ml` | stack-python-ml | touching `*.py`, `*.ipynb` |
| `vue-ts` | stack-vue-ts | touching `*.vue`, `*.ts`, `*.js`, `*.css` |
| `flutter-dart` | stack-flutter-dart | touching `*.dart`, `pubspec.yaml`, `analysis_options.yaml` |
| `kotlin-android` | stack-kotlin-android | touching `*.kt`, `*.kts` |
| `csharp-windows` | stack-csharp-windows | touching `*.cs`, `*.xaml`, `*.csproj` (WPF, WinUI, WinForms) |
| `cpp-qt-cmake` | stack-cpp-qt-cmake | touching `*.cpp`, `*.h`, `*.hpp`, `CMakeLists.txt`, `*.cmake` (Qt, CMake) |

## Specific skills only (--skill)
Check with `python C:\AI_Tools\init_project.py --root <project> --skill blueprint,system-architect --dry-run`, then run it with `--skill ...`. Names are the folder names under `lang/en/skills/`. It touches only `.claude/skills/` (helper files included) and changes no CLAUDE.md, kb or preset line. Existing files are kept; only `--force` overwrites.

## External skills (--ext)
| Name | Use | Note |
|---|---|---|
| `hwpx` | edit and create Hancom documents (.hwpx, .hwp); plain reading needs no skill | copies an 8MB engine into the project, integrity check before install, package installs after approval |
| `interview-me` | before a new feature, document or screen, ask one question at a time with a guess | integrity check before install. To use it, the project's dispatch.md §6 table needs a row too (it is in the template) |

Check with `python C:\AI_Tools\init_project.py --root <project> --ext hwpx --dry-run`, then run it with `--ext hwpx`.

## Global slash commands (`~/.claude/commands/`, loaded only when typed)
- `/ai-guide [topic]`: this guide.
- `/intent [topic-slug] [-- one-line description]`: record project intent. Default is `.ai/INTENT.md`; a topic approved or changed separately goes to `.ai/intent/intent_<slug>.md` (a bare slug counts as the decision to split).
- `/handoff [focus topic] | [topic-slug -- focus]`: session handoff. Default is `.ai/handoff.md`; a separate topic goes to `.ai/handoff/handoff_<slug>.md`. The previous file is copied to `.ai/archive/handoff/` before overwriting (no `.bak_`).
- Install: step 3b of `python C:\AI_Tools\setup_env.py` (copies after approval). **Existing files are not overwritten**, so after changing a command here, back up and delete that file in `~/.claude/commands/` and run it again.

## Examples
```powershell
# new Vue project
python C:\AI_Tools\init_project.py --root D:\work\app --preset new-fullstack --dry-run
python C:\AI_Tools\init_project.py --root D:\work\app --preset new-fullstack
python C:\AI_Tools\merge_settings.py D:\work\app
python C:\AI_Tools\init_project.py --root D:\work\app --stack vue-ts
# add only the Python checklist to an existing project
python C:\AI_Tools\init_project.py --root D:\work\ml --stack python-ml --dry-run
python C:\AI_Tools\init_project.py --root D:\work\ml --stack python-ml
# only two design skills / add the interview skill before starting work
python C:\AI_Tools\init_project.py --root D:\work\ml --skill blueprint,system-architect --dry-run
python C:\AI_Tools\init_project.py --root D:\work\ml --ext interview-me --dry-run
```

## Cautions
- `init_project.py` refuses projects still managed by v8. Run `migrate_v8.py` first (dry-run, then `--apply`).
- Files already copied are not refreshed when the tool folder changes. Copy only the files you need by hand and avoid `--force`.
- `--skill`, `--ext` and `--stack` are additive only (do not combine them with `--preset`). `--ext` checks integrity against `MANIFEST.sha256` before installing.
- The bundles are an untested draft (`third_party/ECC@ccd8da1/REVIEW.md`). Apply them to a project under measurement only after the measurement ends.
- See also: `README.md`, `roster.yaml`, `lang/kr/rules/dispatch.md`, `third_party/README.md`.
