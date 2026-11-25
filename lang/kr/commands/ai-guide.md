---
description: Show how to apply AI_Tools presets and stack bundles to a project (init_project.py usage, preset summary, examples)
disable-model-invocation: true
---
# /ai-guide: AI_Tools 적용 안내 (v2.4.6)

아래 안내를 그대로 보여 준다. `$ARGUMENTS`가 있으면 그 주제(`presets`, `stack`, `skill`, `ext`, `commands`, `examples`, `cautions`)의 절만 보여 준다. 도구 폴더가 `C:\AI_Tools`가 아니면 `init_project.py`가 있는 폴더로 바꿔 읽는다. 목록이 의심되면 도구 폴더의 `roster.yaml`을 읽어 차이를 알려 준다(수정하지 않는다).

## 기본 흐름
1. `--dry-run`으로 무엇이 복사되는지 본다. 2. 적용한다. 3. `merge_settings.py`로 hook과 deny 규칙을 병합한다. 4. 쓰는 언어가 있으면 `--stack`으로 점검 번들을, 필요한 스킬만 `--skill`로, 외부 스킬은 `--ext`로 하나씩 추가한다.

## 주요 명령
```powershell
python C:\AI_Tools\init_project.py --root <프로젝트> --preset <이름> --dry-run
python C:\AI_Tools\init_project.py --root <프로젝트> --preset <이름>
python C:\AI_Tools\merge_settings.py <프로젝트>
python C:\AI_Tools\init_project.py --root <프로젝트> --stack vue-ts,python-ml --dry-run
python C:\AI_Tools\init_project.py --check-lang; python C:\AI_Tools\hooks\selftest_hooks.py; python C:\AI_Tools\tests\selftest_v24.py
```
- `--preset`: `apply_preset`이 프리셋의 skills, agents, rules, knowledge 스텁을 프로젝트 `.claude/`로 복사하고 CLAUDE.md, `.ai/`(kb, INTENT), AGENTS.md도 만든다. 이미 있는 파일은 유지한다.
- `--stack`(`--preset` 없이): 번들의 규칙 파일만 `.claude/rules/`에 복사한다. 다른 것은 건드리지 않아 기존 프로젝트에 안전하다.
- `--force`: 기존 파일을 덮어쓴다. 채워 둔 `project-*` 스텁과 직접 고친 규칙도 지우므로 쓰기 전에 diff를 본다.

## 프리셋 요약 (roster.yaml 기준)
| 프리셋 | 용도 | skill | agent | 비고 |
|---|---|---|---|---|
| `base` | 공통 바탕 | code-change | explorer, reviewer | 규칙 dispatch |
| `new-fullstack` | 새 앱·웹 개발 | + requirements-analysis, blueprint, system-architect, ui-ux-design | base와 같음 | 지식 스텁 4종, 설계 승인 게이트 |
| `legacy-maintenance` | 기존 코드 수정 | code-change | explorer, reviewer | 첫 진입에 repo_audit_map 작성 |
| `research-code` | 연구·실험 코드 | code-change | explorer, reviewer | 노트북·실험 종료 코드가 검사 |
| `doc-analysis` | 문서·요구사항 분석 | requirements-analysis, doc-design | explorer, evidence-verifier | pdf, docx |
| `ux-design` | 화면 설계 | ui-ux-design | explorer, evidence-verifier | 취향 조율은 메인 세션 |
| `report-ppt` | 보고서·발표 | tech-writing, ppt-structuring, doc-design | explorer, evidence-verifier | docx, pptx, xlsx |
| `paper-patent` | 논문·특허 | tech-writing, doc-design | explorer, evidence-verifier | WebSearch, docx, pdf |
| `research` | 웹 자료 조사 | tech-writing | researcher, explorer, evidence-verifier | WebSearch, WebFetch, 출처 URL·접근일 필수 |

## 스택 번들
| 번들 | 규칙 파일 | 로드 조건 |
|---|---|---|
| `python-ml` | stack-python-ml | `*.py`, `*.ipynb`를 다룰 때 |
| `vue-ts` | stack-vue-ts | `*.vue`, `*.ts`, `*.js`, `*.css`를 다룰 때 |
| `flutter-dart` | stack-flutter-dart | `*.dart`, `pubspec.yaml`, `analysis_options.yaml`을 다룰 때 |
| `kotlin-android` | stack-kotlin-android | `*.kt`, `*.kts`를 다룰 때 |
| `csharp-windows` | stack-csharp-windows | `*.cs`, `*.xaml`, `*.csproj`를 다룰 때 (WPF·WinUI·WinForms) |
| `cpp-qt-cmake` | stack-cpp-qt-cmake | `*.cpp`, `*.h`, `*.hpp`, `CMakeLists.txt`, `*.cmake`를 다룰 때 (Qt·CMake) |

## 특정 스킬만 (--skill)
`python C:\AI_Tools\init_project.py --root <프로젝트> --skill blueprint,system-architect --dry-run` 확인 후 `--skill ...`. 이름은 `lang/kr/skills/`의 폴더명이다. `.claude/skills/`만 건드리며(보조 파일 포함) CLAUDE.md·kb·프리셋 줄은 바꾸지 않는다. 기존 파일은 유지하고 `--force`만 덮어쓴다.

## 외부 스킬 (--ext)
| 이름 | 용도 | 비고 |
|---|---|---|
| `hwpx` | 한글(.hwpx, .hwp) 편집·생성 (단순 읽기는 스킬 없이) | 프로젝트에 엔진 8MB 복사, 설치 전 무결성 검사, 패키지 설치는 승인 후 |
| `interview-me` | 새 기능·문서·화면 착수 전 한 번에 하나씩 묻고 추측으로 확인 | 설치 전 무결성 검사. 쓰려면 그 프로젝트 dispatch.md §6 표에도 행을 둔다(템플릿에 있음) |

`python C:\AI_Tools\init_project.py --root <프로젝트> --ext hwpx --dry-run` 확인 후 `--ext hwpx`.

## 전역 슬래시 명령 (`~/.claude/commands/`, 입력할 때만 로드)
- `/ai-guide [주제]`: 이 안내.
- `/intent [주제-slug] [-- 한 줄 설명]`: 프로젝트 의도 기록. 기본은 `.ai/INTENT.md`, 따로 승인·변경되는 주제는 `.ai/intent/intent_<slug>.md`로 분리(slug만 쓰면 분리 결정으로 본다).
- `/handoff [중점 주제] | [주제-slug -- 중점]`: 세션 인계. 기본은 `.ai/handoff.md`, 주제 분리는 `.ai/handoff/handoff_<slug>.md`. 이전본은 `.ai/archive/handoff/`로 복사한 뒤 덮어쓴다(`.bak_` 없음).
- 설치: `python C:\AI_Tools\setup_env.py`의 3b 단계(승인 후 복사). **기존 파일은 덮어쓰지 않으므로**, 도구 쪽 명령을 고친 뒤에는 `~/.claude/commands/`의 해당 파일을 백업·삭제하고 다시 실행한다.

## 예시
```powershell
# 새 Vue 프로젝트
python C:\AI_Tools\init_project.py --root D:\work\app --preset new-fullstack --dry-run
python C:\AI_Tools\init_project.py --root D:\work\app --preset new-fullstack
python C:\AI_Tools\merge_settings.py D:\work\app
python C:\AI_Tools\init_project.py --root D:\work\app --stack vue-ts
# 이미 쓰던 프로젝트에 Python 점검만 추가
python C:\AI_Tools\init_project.py --root D:\work\ml --stack python-ml --dry-run
python C:\AI_Tools\init_project.py --root D:\work\ml --stack python-ml
# 설계 스킬 두 개만 추가 / 착수 전 인터뷰 스킬 추가
python C:\AI_Tools\init_project.py --root D:\work\ml --skill blueprint,system-architect --dry-run
python C:\AI_Tools\init_project.py --root D:\work\ml --ext interview-me --dry-run
```

## 주의
- v8로 관리되던 프로젝트는 `init_project.py`가 막는다. 먼저 `migrate_v8.py`(dry-run 후 `--apply`)를 쓴다.
- 이미 복사된 파일은 도구 쪽을 고쳐도 갱신되지 않는다. 필요한 파일만 직접 복사하고 `--force`는 피한다.
- `--skill`·`--ext`·`--stack`은 추가 전용이다(`--preset`과 함께 쓰지 않는다). `--ext`는 설치 전 `MANIFEST.sha256`로 무결성을 검사한다.
- 번들은 아직 시험 전 초안이다(`third_party/ECC@ccd8da1/REVIEW.md`). 진행 중인 측정 프로젝트에는 측정이 끝난 뒤 적용한다.
- 더 보기: `README.md`, `roster.yaml`, `lang/kr/rules/dispatch.md`, `third_party/README.md`.
