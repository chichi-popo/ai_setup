---
name: code-change
description: Implement, fix or refactor code with a verifiable loop (surgical edits, independent tests, deterministic checks), then hand the result to the reviewer agent. Use for any code edit, bug fix, UI change or feature in a project that has a test/build command.
---
# code-change

## 루프 계약
- 성공 기준: CLAUDE.md의 테스트/빌드 명령이 종료 코드 0이고, 목표 한 줄이 참임을 결정적 검사로 보인다. 요청한 동작은 변경 전 실패·변경 후 통과하는 테스트로 입증한다. 계산·판정 로직은 독립 증거 2종 이상(손 계산, 독립된 두 방법, 성질 테스트), UI는 화면 확인을 포함한다.
- 검증자: 결정적 명령 먼저. 사소하지 않은 변경(파일 약 3개 초과, 보안 관련, 공개 API)은 새 컨텍스트의 reviewer가 이어서 본다. reviewer는 결과와 함께 테스트·검증 데이터의 타당성도 판정한다.
- 중단 조건: 같은 검사가 2번 연속 실패하거나 reviewer FAIL로 같은 문제를 3번 되돌리면 멈추고 근거를 보고한 뒤 사용자에게 묻는다. 조용히 반복하지 않는다. 막히면 dispatch.md의 BLOCKED 규칙.

## 작성 원칙
- 단순하게: 요청을 푸는 최소 코드만. 요청 밖 기능·추상화·설정, 일어날 수 없는 경우의 오류 처리 금지.
- 고칠 곳만: 바뀐 모든 줄이 요청으로 추적돼야 한다. 요청 밖 코드의 포맷·이름 변경·정리·리팩터링 금지, 기존 스타일을 따른다. 다른 문제는 고치지 말고 보고서에 적는다. 내 변경의 잔여물만 치운다.
- 완료는 확인으로: 명령과 종료 코드로 확인하기 전에는 완료라고 하지 않는다("될 것이다"는 근거가 아님). 자기 결과물을 스스로 최종 판정하지 않는다.
- 응답: 변경한 파일, diff 또는 코드 블록, 명령 + 종료 코드, 남은 위험만. 인사말·서론·반복 요약 없이. 주석은 이유가 자명하지 않은 곳에만.

## 절차
1. 목표 한 줄과 확인 방법을 정한다(`.ai/INTENT.md`가 있으면 사용). 설계 결정(새 의존성, 스키마, 공개 API)이 암시되면 코딩 전에 멈추고 묻는다(`system-architect`가 있으면 그 설계 대화로). 큰 목표는 `.ai/repo_audit_map.md`의 환경 준비 점검표가 채워졌는지 먼저 본다.
2. 기존 프로젝트 첫 진입: 수정 전에 `explorer`로 `.ai/repo_audit_map.md`를 완성한다. 이미 감사한 영역의 작은 작업은 건너뛴다.
3. 테스트를 먼저 쓰거나 찾는다(버그는 재현 테스트부터, 실패 확인). 테스트는 내가 쓰고 reviewer는 쓰지 않는다. 기대값은 구현이 아니라 독립된 근거(명세, 손 계산, 문서, 기존 결과, 다른 방법)에서 가져온다. 경계·이상·대표값을 섞고 같은 입력이 반복되지 않게 한다. 데이터 생성기는 중복·편향을 확인한다.
4. 테스트를 만족하는 가장 작은 변경만 한다. 바꾼 함수·API·스키마의 호출부와 형제 경로(생성·이동 ↔ 수정·삭제, body ↔ query·header 등)를 함께 점검한다. 자격증명은 환경변수·시크릿 매니저로 받고(하드코딩 금지), 로컬 서비스는 localhost·내부망에 바인딩한다.
5. 결정적 검사를 돌리고 명령과 종료 코드를 붙여 넣는다.
   - 테스트·빌드·린트: CLAUDE.md 관리 블록의 명령. `run_check.py`가 있으면 `python .claude/hooks/run_check.py -- <명령>`(`.ai/last_check.json`에 기록).
   - 커버리지: `check_test_coverage.py`와 리포트가 있으면 `python .claude/hooks/check_test_coverage.py --min <값> --files <변경 파일>`을 실행한다. 종료 코드 3(리포트 없음)이면 `UNVERIFIED: coverage`로 적고 넘어간다.
6. UI 변경은 실행해 화면을 확인한다(캡처 도구나 결정적 UI 검사가 있으면 사용). 수단이 없으면 `UNVERIFIED: screen`.
7. 사소하지 않은 변경은 reviewer에게 위임한다(입력은 dispatch.md의 reviewer 입력 규칙). 관련 kb 결정·진행 카드 경로(`.ai/kb/...`)가 있으면 지시문에 함께 넣는다.
8. reviewer 지적은 하나씩 직접 재현하거나 근거를 확인해 맞는 것만 고치고, 기각은 사유를 남긴다.
9. FAIL이면 원인별로 그 단계로만 되돌리고 5단계부터 다시 한다.
   - CODE: 구현 → 4로
   - TEST: 테스트·검증 데이터 → 3으로(기대값을 구현에 맞추지 않는다)
   - SPEC: 요구사항 → requirements-analysis, 사용자 확인
   - ENV: 환경·도구 → 보고하고 멈춤
10. 완료 보고 후 커밋은 승인을 받고 한다.

## 위임
`.claude/rules/dispatch.md`를 따른다(0~3개, 포그라운드, 지시문 양식, 출력 계약, 병렬은 §3 조건을 모두 충족하는 독립 모듈만).

## 보고 형식
```
Goal: <목표 한 줄>
Changed: <파일 목록>
Check: <명령> -> exit <코드> (<통과 n / 실패 n>)
Evidence: <독립 증거 2종 / 화면 확인>  (계산·판정 로직, UI일 때)
Review: PASS | FAIL | skipped (<사유>)
Findings: 수용 <n> / 기각 <n> (<기각 사유 한 줄씩>)
Open risks: <없음 | 목록, UNVERIFIED 포함>
```
