# airmang/hwpx-plugins 고정본 (참조·설치 원본, Claude가 읽는 경로 아님)

- 출처: https://github.com/airmang/hwpx-plugins
- 커밋: c6196cfe2e9bfcb32fb29889af7c500e8aa8dacf (커밋일 2026-11-16, plugin 2.4.0 = python-hwpx 6.12.0 + python-hwpx-automation 7.5.0)
- 고정일: 2026-11-20 (사용자 승인)
- 라이선스: Apache-2.0 (LICENSE, NOTICE 동봉. 이 폴더를 복사·재배포할 때 두 파일을 유지한다)
- 포함: `skill/` = 저장소의 `plugins/claude/hwpx-plugin/skills/hwpx/` 전체(엔진 포함, 수정 없음), `plugin.json`, LICENSE, NOTICE
- 사용하는 것: `skill/chat-engine.md`, `skill/engine/` 만 프로젝트로 복사한다(`init_project.py --ext hwpx`). 상류 `skill/SKILL.md`(MCP 우선, 29KB)와 `references/`, `scripts/`, `examples/`는 복사하지 않는다. SKILL.md는 우리가 쓴 짧은 것(`lang/{kr,en}/skills/hwpx/SKILL.md`)을 쓴다.
- 무결성: `MANIFEST.sha256`(복사 대상 파일의 sha256). `init_project.py --ext`가 복사 전에 대조하고 하나라도 다르면 중단한다.
- 공급망 확인(2026-11-20): `engine/VENDOR.json`의 wheel 3개(python-hwpx 6.12.0, python-hwpx-automation 7.5.0, tomli 2.4.1)를 PyPI(files.pythonhosted.org)에서 받아 sha256이 모두 일치함을 확인했고, wheel을 풀어 `engine/`과 파일 단위로 비교해 내용 차이 0건(엔진에만 있는 파일: VENDOR.json, docs/llms.txt, docs/stable-api.md. wheel에만 있는 파일: 패키지 메타데이터 RECORD/WHEEL 등과 py.typed)을 확인했다.
- 읽지 않은 것: 엔진 본문(8.3MB)의 코드. 위 대조는 "PyPI 배포본과 같다"는 뜻이지 "코드를 검토했다"는 뜻이 아니다.
