# C:\AI_Tools — v2.4.4 (2026-11-16 정리, 2026-11-20 갱신)

2026-11-16에 `redesign_v2` 폴더를 이 루트로 꺼내고 v8 시스템을 퇴역시켰다. 이전 문서의 `C:\AI_Tools\redesign_v2\...` 경로는 `C:\AI_Tools\...`로 읽는다.

## 구성
| 경로 | 내용 |
|---|---|
| `init_project.py`, `merge_settings.py`, `migrate_v8.py`, `setup_env.py` | 프로젝트 초기화, settings·hook 병합, v8 프로젝트 이관, 새 PC 설정 |
| `roster.yaml`, `backup/roster.json`, `settings.snippet.json`, `requirements.txt` | 프리셋·구성 정의(roster.json은 PyYAML이 없을 때 쓰는 사본) |
| `lang/{kr,en}/` | skill·agent·rule·지식 스텁·템플릿 |
| `hooks/`, `kb/`, `shared/`, `design/`, `global/` | hook 스크립트, kb 카드 기억, doc-design 공용 스크립트, 기본 디자인 값, 전역 CLAUDE.md(r3) |
| `tests/`, `third_party/`, `GLOSSARY.md` | 자체 시험, 외부 skill 도입 절차, 용어 |
| `eval_add.py`, `eval_log.csv`, `eval_run.ps1` | 측정 기록(eval_run.ps1의 `eval_set`은 기기 A에만 있음) |
| `ai-manuals/` | v8 디자인 매뉴얼(v8 프로젝트의 report 프로필이 참조, `design/default.DESIGN.md`의 출처) |
| `_notion-sync/` | Notion 체크리스트 동기화 hook(`~/.claude/settings.json`에서 사용) |
| `AI_Tools_v2.4.1_overlay_20261116.zip` | 아직 적용하지 않은 v2.4.1(hook 절대 경로). 루트 구조용으로 경로를 고친 판 |
| `AI_Tools_v2.4.2_overlay_20261118.zip` | v2.4.1에 `/blueprint`(설계서) skill 추가(누적 overlay, 기기 A·B 배포용). 설명은 zip 안 `README_v2.4.2.md` |
| `AI_Tools_v2.4.3_overlay_20261118.zip` | v2.4.2에 tech-writing 문체 통합, 퇴고 참조 파일(`revise_prompts.md`)과 `numcheck.py` 추가(누적 overlay). 설명은 zip 안 `README_v2.4.3.md` |
| `AI_Tools_v2.4.4_overlay_20261120.zip` | v2.4.3에 언어 점검표 번들(`--stack python-ml,vue-ts`), 전역 커맨드 `/ai-guide`, `third_party/ECC@ccd8da1/` 추가(누적 overlay). 설명은 zip 안 `README_v2.4.4.md` |
| `third_party/humanizer@a32f244/` | blader/humanizer 고정본(MIT, SKILL.md는 스킬로 설치하지 않음). 26패턴을 재구성한 `lang/{kr,en}/skills/tech-writing/humanize_patterns.md`(퇴고 요청 때만 읽음)의 원본과 `REVIEW.md`(2026-11-23) |
| `_backup/` | `AI_Tools_20260720_배포.7z`(v8 배포본) + `AI_Tools_pre_cleanup_20261116.zip`(정리 직전 전체, 249개, sha256 목록 동봉) |

## 자주 쓰는 명령
```powershell
python C:\AI_Tools\init_project.py --root <프로젝트> --preset <legacy-maintenance|report-ppt|paper-patent|...>
python C:\AI_Tools\merge_settings.py <프로젝트>
python C:\AI_Tools\init_project.py --root <프로젝트> --stack <python-ml|vue-ts|flutter-dart|kotlin-android|csharp-windows|cpp-qt-cmake>[,...] --dry-run   # 규칙 번들만 추가(기존 프로젝트에 안전)
python C:\AI_Tools\init_project.py --root <프로젝트> --skill <스킬명>[,...] --dry-run   # 지정한 스킬 폴더만 추가(CLAUDE.md·kb 변경 없음)
python C:\AI_Tools\migrate_v8.py --root <v8 프로젝트>            # dry-run, 확인 후 --apply
python C:\AI_Tools\init_project.py --check-lang; python C:\AI_Tools\hooks\selftest_hooks.py; python C:\AI_Tools\tests\selftest_v24.py
```

## v8 퇴역 상태
- 삭제: refresh/switch/init-ai 스크립트와 .bat, setup-ai.ps1, ai-profiles(registry 포함), ai-agents, v8 가이드 문서. 원본은 `_backup/`의 두 압축 파일에 있다.
- 아직 v8인 프로젝트 6개(TEST, asd_diagnosis, 내용기반, 개발공부, 전력설비 예지보전, 환경정보수집장치)는 지금의 CLAUDE.md로 계속 동작한다. 자동 갱신·`switch-ai`만 안 된다. `.ai\profiles` 링크는 끊긴 상태라 무시한다.
- 그 프로젝트를 다시 쓸 때 `migrate_v8.py`(registry가 없으면 그 단계만 건너뜀) → `init_project.py` → `merge_settings.py` 순서로 옮긴다.
- `~/.claude/agents`의 v8 agent 7개는 지우지 않았다(v8 프로젝트 지침이 이름으로 부름).

## v2.4.1 적용(선택, 기기 B)
```powershell
& {
  $ErrorActionPreference = 'Stop'
  $ov = Join-Path $env:TEMP 'v241_overlay'
  if (Test-Path -LiteralPath $ov) { Remove-Item -LiteralPath $ov -Recurse -Force }
  Expand-Archive -LiteralPath 'C:\AI_Tools\AI_Tools_v2.4.1_overlay_20261116.zip' -DestinationPath $ov
  python "$ov\apply_overlay.py" --target C:\AI_Tools --dry-run   # 예상: 6 updated, 0 new, 49 identical
  python "$ov\apply_overlay.py" --target C:\AI_Tools
  if ($LASTEXITCODE) { throw 'overlay 실패 (C:\AI_Tools\_backup\pre_v241_<날짜>로 되돌림)' }
  foreach ($p in 'D:\02_PRIVATE\00_DEV_PRIVATE\notion-app', 'D:\01_WORK\00_DEVELOP\content_dataset_collector') {
    python C:\AI_Tools\merge_settings.py $p; if ($LASTEXITCODE) { throw "merge 실패: $p" }
    python C:\AI_Tools\init_project.py --root $p --preset legacy-maintenance --force; if ($LASTEXITCODE) { throw "init 실패: $p" }
  }
  '[OK] v2.4.1 반영'
}
```

## v2.4.2 적용 (`/blueprint`, 기기 A·B)
`AI_Tools_v2.4.2_overlay_20261118.zip` 안 `README_v2.4.2.md`의 적용 블록을 따른다(이 PC는 이미 같은 변경이 들어 있어 전부 identical). 요약: overlay 적용 → `~/.claude/agents/reviewer.md` 교체 → `new-fullstack` 프로젝트마다 `init_project.py --root <프로젝트> --preset new-fullstack`(`--force` 없이). 누적 overlay라 v2.4.1 zip은 따로 적용하지 않아도 된다.

## v2.4.3 적용 (tech-writing 퇴고, 기기 A·B)
`AI_Tools_v2.4.3_overlay_20261118.zip` 안 `README_v2.4.3.md`를 따른다. 누적 overlay라 이전 zip은 따로 적용하지 않아도 된다. 기존 프로젝트는 `init_project`가 skill 사본을 덮어쓰지 않으므로 README의 `tech-writing` 폴더 복사 블록을 쓴다(`--force` 금지).

## v2.4.4 적용 (언어 점검표 번들 + /ai-guide, 기기 A·B)
`AI_Tools_v2.4.4_overlay_20261120.zip` 안 `README_v2.4.4.md`를 따른다. 누적 overlay라 이전 zip은 따로 적용하지 않아도 된다. 이 PC는 이미 같은 변경이 들어 있다. 전역 커맨드는 `python C:\AI_Tools\setup_env.py`의 3b 단계에서 승인하면 `~/.claude/commands/ai-guide.md`로 복사된다(새 세션에서 `/ai-guide`). 번들은 시험 전 초안이라 `third_party/ECC@ccd8da1/REVIEW.md`의 시험을 마치기 전에는 프로젝트에 적용하지 않는다.
