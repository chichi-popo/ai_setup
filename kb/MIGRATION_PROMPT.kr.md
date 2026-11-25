# 이관 프롬프트: `.ai/memory` → kb 카드 (Claude Code에 그대로 붙여 넣기)

```
.ai/memory/ 의 문서(plan·checklist·context·memory 등)를 kb 카드로 옮겨 줘. 요약이 아니라 분할이다.

규칙
1. 원문은 .ai/archive/legacy-v8/ 에 이미 그대로 보관돼 있다. .ai/memory 파일은 고치거나 지우지 않는다.
2. 절(##, ###) 하나를 카드 하나로 옮기는 것을 기본으로 하고, 40줄을 넘는 절은 주제별로 여러 카드로 나눈다.
   문장은 원문 그대로 옮긴다. 줄이거나 바꿔 쓰지 않는다(제목 한 줄만 새로 쓴다).
3. 유형
   - checklist·plan의 단계표·남은 일 → progress (마일스톤 하나 = 카드 하나, 체크 항목 유지)
   - plan의 결정·추천안 승인 기록(H1, L3 같은 ID) → decision (결정 하나 = 카드 하나, id에 원래 ID를 살린다: D-M8-L3)
   - memory.md의 문제→해결→규칙 → issue (주제별)
   - context.md의 구조·불변식·디렉토리 → map (영역별)
   - docs/, .ai/scripts/, design 파일 → asset (`python .ai/kb.py new asset <경로>`, 한 줄 요약)
4. 카드는 `python .ai/kb.py new <유형> --id <id> --title "<제목>" --tags a,b --related X,Y`로 만든 뒤 본문을 채운다.
   서로 관계있는 카드는 related와 본문 [[id]]로 잇는다(진행 카드 → 그 단계의 결정 카드).
   updated는 원문에 적힌 날짜(없으면 오늘).
5. 끝난 마일스톤의 진행 카드는 status: done.
6. .ai/NOW.md를 10줄 이하로 쓴다: 진행 중인 것, 다음 행동(checklist 근거 1~2개, 승인 전 착수 금지), 막힌 것. 카드는 [[id]]로.
7. 마지막에 실행하고 결과를 보여 줘:
   python .ai/kb.py check --coverage .ai/archive/legacy-v8/<날짜>/.ai/memory
   MISSING이 0개, ERROR가 0개가 될 때까지 빠진 내용을 카드로 보충한다. WARN은 목록만 보고한다.
8. Bash에서 cd로 폴더를 옮기지 않는다. 모든 명령은 프로젝트 루트 기준 경로로 실행한다.
9. 카드 수, INDEX.md 크기(바이트), 남은 WARN을 보고하고 멈춘다. .ai/memory 정리는 내가 승인한 뒤 migrate_v8.py --retire-memory로 한다.
```
