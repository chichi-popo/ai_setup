# Claude Code ↔ Notion 체크리스트 동기화 (A안)

TodoWrite로 만든 할일을 Notion 체크리스트 DB에 자동 생성하고, 완료 처리 시 Notion 상태도 자동으로 "완료"로 바꿔주는 훅입니다. LLM 호출 없이 로컬 스크립트가 Notion API를 직접 호출하므로 토큰 비용은 없습니다.

## 구성 파일

- `notion-todo-sync.js` : 훅 스크립트 (Node.js, 전역 1개만 있으면 됨)
- `_notion_prop.example.json` : 프로젝트별 설정 템플릿

## 설치 순서

### 1. 스크립트 배치

`notion-todo-sync.js`를 `C:\AI_Tools\_notion-sync\notion-todo-sync.js` 로 저장합니다. (이미 이 경로에 저장되어 있습니다.)

### 2. Notion 인테그레이션 발급 및 공유

1. https://www.notion.so/my-integrations 에서 "New integration" 생성 → 시크릿 토큰(`secret_...`) 복사
2. 체크리스트 DB, 프로젝트 DB, 영역 DB(모두 관계로 연결된 DB) 각각의 우측 상단 `···` → `연결 추가` 에서 방금 만든 인테그레이션 공유

### 3. 환경변수 설정 (Windows, PowerShell)

```powershell
setx NOTION_TOKEN "secret_여기에_토큰"
setx NOTION_CHECKLIST_DB_ID "226f9796-01ef-40e4-9a6d-752c30042d7a"
```

설정 후 VS Code(터미널)를 재시작해야 반영됩니다.

### 4. 훅 등록

`%USERPROFILE%\.claude\settings.json` (없으면 새로 생성)에 아래 내용을 병합합니다. 이미 `hooks` 키가 있다면 배열에 추가만 하세요.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [
          {
            "type": "command",
            "command": "node \"C:/AI_Tools/_notion-sync/notion-todo-sync.js\""
          }
        ]
      }
    ]
  }
}
```

Claude Code의 `/hooks` 명령으로 메뉴에서 등록해도 동일합니다 (Event: PostToolUse, Matcher: TodoWrite, Command: 위 node 명령).

### 5. 프로젝트별 연동 설정

Notion과 연동하고 싶은 각 프로젝트 폴더에 `.ai/_notion_prop.json` 파일을 만듭니다 (`_notion_prop.example.json` 참고).

```
C:\AI_Tools\프로젝트A\.ai\_notion_prop.json
```

```json
{
  "proj": "내용기반",
  "area": "회사"
}
```

이 파일이 없는 프로젝트는 동기화 대상에서 자동으로 제외됩니다.

### 6. 동작 확인

해당 프로젝트에서 Claude Code로 TodoWrite를 한 번 실행(체크리스트 생성)해보고, Notion DB에 항목이 생기는지 확인합니다. 문제가 있으면 `<프로젝트>\.claude\notion-sync.log` 에러 로그를 확인하세요.

## 동작 방식 요약

- 새 todo 발견 → Notion 페이지 생성 (이름/상태/프로젝트 relation 채움)
- todo 상태 변경(pending→수집, in_progress→진행중, completed→완료) → 기존 Notion 페이지 상태만 업데이트
- 목록에서 todo가 사라짐(삭제) → 기존 Notion 페이지 상태를 "취소"로 변경하고 추적 목록에서 제거 (동일 문구가 나중에 다시 생기면 새 페이지로 취급)
- 재정렬(순서)은 동기화하지 않음 (범위 밖, 필요하면 추후 추가)
- 프로젝트-영역 relation 페이지 ID는 프로젝트별 상태 파일(`.claude/notion-todo-state.json`)에 캐시되어 매번 재조회하지 않음

## 알아둘 점

- Notion 상태 속성이 "select"인지 "status" 타입인지 스크립트가 자동 감지해서 맞는 형식으로 호출합니다.
- 오류가 나도 Claude Code 작업 자체는 막지 않고 로그만 남깁니다.
- Node.js 18 이상 필요 (전역 `fetch` 사용). 현재 확인된 버전: v22 이상이면 문제없습니다.
