---
description: Save this session's work summary to .ai/handoff.md (or .ai/handoff/handoff_<slug>.md for a separate topic)
disable-model-invocation: true
argument-hint: [focus topic] | [topic-slug -- focus]
---
# /handoff: 세션 인계 기록

인자: `$ARGUMENTS`

## 대상과 인자
- `<slug> -- 중점`: `.ai/handoff/handoff_<slug>.md`에 쓰고 루트 `.ai/handoff.md`의 `## 활성 주제` 표(주제 | 상태 | 다음 행동 | 파일)를 갱신한다. 새 주제 파일은 이 형식일 때만 만든다(`--` 뒤는 비어도 된다).
- slug 형식 단어 하나이고 그 파일이 이미 있으면 그 주제 파일을 갱신한다.
- 그 밖(빈 인자 포함)은 `.ai/handoff.md`에 쓰고, 인자 전체를 중점 주제·지시로 본다. 중점이 있으면 그 주제 위주로 요약하고 나머지는 한 줄 이내로 줄인다.
- slug는 영문 소문자·숫자·하이픈 30자 이하(한글 주제는 H1에). 쓴 뒤 활성 트랙이 2개 이상이거나 루트가 100줄을 넘으면 분리를 한 줄로 제안한다.

## 이전본
쓸 파일이 있으면 덮어쓰기 전에 `.ai/archive/handoff/<파일명>_<이전본 작성일 YYYYMMDD>.md`로 복사한다(작성일은 첫 줄 `# Handoff (날짜)`, 없으면 수정일, 이름이 있으면 `_2`). `.bak_` 파일은 만들지 않고 복사 경로를 새 파일 첫머리에 한 줄로 적는다.

대화와 코드 변경을 분석해 아래 4개 섹션으로 쓴다.

## 1. 작업 목표 및 현재 상태
- 해결하려던 문제와 완료된 진행률 요약

## 2. 수정 및 생성된 파일
- 변경된 파일 경로와 핵심 수정 내용 (전체 코드 복붙 금지)

## 3. 주요 기술적 결정 및 시행착오
- 선택한 방식, 제약, 실패한 접근 등 다음 세션이 반복하면 안 되는 맥락. 반복하면 안 되는 결정은 `python .ai/kb.py new decision|issue --title "..."` 카드로 올리길 제안한다(실행은 승인 후).

## 4. 다음 할 일 (Next Steps)
- 이어서 바로 실행할 구체적 액션 아이템
