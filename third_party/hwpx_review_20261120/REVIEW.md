# HWPX 후보 읽기 전용 검토 — jkf87/hwpx-skill vs airmang/hwpx-plugins (2026-11-20)

사용자 승인: 두 후보를 읽기 전용으로 비교하고 하나의 SKILL.md로 통합할 수 있는지 검토. **설치·실행·코드 복사는 하지 않았다**(third_party 절차 2단계 "원본 고정"은 도입을 결정할 때 수행). 이 폴더에는 검토 기록만 둔다.

## 1. 고정한 판본
| 후보 | 커밋 | 커밋일 | 라이선스 | 크기 |
|---|---|---|---|---|
| jkf87/hwpx-skill | ba90fc5ae15f4aead8dab4f9d69d4830b9569859 | 2026-09-15 | README에 MIT 표기. **저장소 루트에 LICENSE 파일 없음**(licenses/에는 제3자 MIT 2건만) | 파일 161개, 16MB(WASM 바이너리 포함) |
| airmang/hwpx-plugins | c6196cfe2e9bfcb32fb29889af7c500e8aa8dacf | 2026-11-16 | Apache-2.0(LICENSE, NOTICE 있음) | 파일 920개, 17MB. Claude 플러그인 폴더 9MB(엔진 8.3MB) |

## 2. 무엇을 읽었고 읽지 않았나 (게이트의 "전부 읽었다"는 두 후보 모두 아니오)
- 읽음: 두 SKILL.md(jkf87 전문, airmang는 앞 50줄과 라우팅·안전 수칙 제목·키워드 grep), `chat-engine.md` 앞 40줄, `.mcp.json`, `plugin.json`, `VENDOR.json`, `pyproject.toml`, `network_policy.py` 앞부분, jkf87 `convert_hwp.py`·`rhwp_convert.mjs`·`convert_hwp_hancom.ps1`(레지스트리 부분)·`hwpx_guard_hook.py` 앞부분.
- grep으로만 확인: 네트워크 호출, subprocess, 삭제, COM, 레지스트리 패턴.
- 읽지 않음: jkf87 스크립트 약 50개의 본문, airmang 엔진(8.3MB)의 본문, 바이너리(`rhwp_bg.wasm`).
- 따라서 REVIEW 게이트 "스크립트·바이너리를 전부 읽었다"는 **아니오**. 이 상태로는 설치하지 않는다.

## 3. 후보별 사실

### jkf87/hwpx-skill
- 방식: 스크립트 모음. Markdown·JSON 명세로 한글 문서 생성(공문, 요약·계획·검토보고, 연구학교 계획서 등 **공공·교육청 양식 중심**), 양식 채우기, HWP→HWPX 변환(Windows는 한컴 COM 우선, 없으면 Node 18+와 번들 WASM).
- 네트워크: 스크립트에 외부 접속 없음(grep). 보이는 URL은 XML 네임스페이스와 주석뿐.
- 삭제: 임시 파일 정리(`unlink`, `rmtree`)만.
- subprocess: 같은 스킬의 스크립트 호출, 한컴 변환 호출.
- 한컴 COM: `HWPFrame.HwpObject`를 호출하고 레지스트리 `HKCU\Software\HNC\HwpAutomation\Modules`를 **읽기만** 한다(쓰기 없음).
- SKILL.md가 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/...`를 지시한다(스킬 폴더 스크립트에 한정되지만 실행 정책 우회라 정책 확인 필요).
- 훅: 전달 전 점검 훅 3개 동봉(`hwpx_guard_hook.py` 등). 등록은 사용자가 settings에 직접 해야 하며 우리는 쓰지 않는다.
- 의존성: lxml, jsonschema, Pillow, pywin32(Windows), Node 18+(rhwp 경로).
- 한계(저장소 스스로 밝힘): 한컴 렌더·육안 검토가 필요. 정적 통과와 한컴 열림은 다르다. 파이썬 내장 변환기는 복잡한 표·글상자에서 한컴에서 안 열리는 HWPX를 만들 수 있다.
- 우리 용도와의 거리: 문서 유형 대부분이 공문·교육청·연구학교. 논문·특허·기술 보고서에는 `markdown` 범용 유형과 `technical-report`가 가장 가깝다.

### airmang/hwpx-plugins
- 방식: MCP 서버가 기본 경로인 플러그인(`.mcp.json`이 `uv run --frozen ... hwpx-automation-mcp`). **MCP 도구 설명은 서버가 뜨면 상시 로드되어** 우리 원칙("MCP 형태 제외")과 충돌한다.
- 대안 경로: 스킬 폴더의 `engine/`에 `python-hwpx` 6.12.0과 `python-hwpx-automation` 7.5.0이 원본 그대로 들어 있고(`VENDOR.json`에 PyPI wheel URL과 sha256), `chat-engine.md`가 "MCP 없이, 설치·인터넷 접속 없이 Python으로 쓰는 절차"를 설명한다.
- `.hwp`: 읽기·추출은 `.hwp`를 그대로 열고, 편집은 `.hwpx` 사본을 만들어 한다. `.hwp`로 다시 쓰는 기능은 실험 단계(내용 일부 손실 가능)라고 스스로 밝힌다.
- 안전: 편집 전 자동 백업, 영수증·검증 계약, 원본 덮어쓰기 금지, 출력 검증 실패 시 원본 보존, SSRF 기본 차단 정책(`network_policy.py`).
- 네트워크: 엔진에 HTTP 관련 코드가 있다(SSRF 정책, 원격 렌더 전송 서버 `render_transport.py`, `hwp_support.py`). 용도는 선택 기능(원격 렌더)이며 우리 사용 경로에서 쓰이는지는 **읽지 않아 확인 못 함**. `chat-engine.md`는 "인터넷에 접속하지 않는다"고 쓴다.
- 의존성: Python ≥3.10, lxml, pydantic, cryptography(chat-engine 경로). MCP 경로는 `uv`, Python 3.12.
- 크기: SKILL.md 28.6KB, chat-engine.md 29.7KB(호출 시에만 읽힘), 설명(description)이 길다("…반드시 사용하세요"로 넓은 트리거).
- 최신성: 2026-11-16 갱신, 릴리스 노트 다수.

## 4. 게이트 요약 (third_party/README 3단계)
| 항목 | jkf87 | airmang |
|---|---|---|
| 스크립트·바이너리 전부 읽음 | 아니오(WASM 바이너리, 스크립트 본문 미독) | 아니오(엔진 8.3MB 미독) |
| 네트워크 호출 없음/명확 | 예(없음, grep) | 부분(엔진에 선택 기능용 HTTP 코드, 사용 경로 미확인) |
| 파일 삭제·설정 수정 없음 | 예(임시 파일만, 레지스트리 읽기만) | 미확인(엔진 안에 삭제 코드가 여러 곳, 용도 미독) |
| description이 좁음 | 예 | 부분(넓은 어구) |
| 기존 스킬과 중복 아님 | 예(HWPX는 공백) | 예 |
| 문체 강제 없음 | 예 | 예 |
| 라이선스 | **루트 LICENSE 없음**(README만 MIT) | Apache-2.0(NOTICE 유지 의무) |
| MCP 상시 비용 없음 | 예 | **MCP 경로는 아니오, chat-engine 경로는 예** |
| 결정 | 보류 | 보류 |

## 5. 하나의 SKILL.md로 통합 가능한가
- **코드 통합은 권하지 않는다.** 두 코드베이스는 데이터 모델·검증 방식·의존성이 다르고(스크립트 vs `python-hwpx` 엔진), 라이선스(MIT 표기만 있는 쪽 / Apache-2.0)와 업데이트 추적도 따로 해야 한다. 섞으면 "한 번에 하나" 원칙과 출처 추적이 깨진다.
- **지시문 통합(얇은 라우터 SKILL.md 1개)은 가능**하다: 우리가 쓰는 짧은 SKILL.md(약 2KB) 하나가 "읽기·편집·양식 채움은 엔진 폴더의 절차, 새 문서는 …"으로 안내하고, 후보의 본문 문서는 `references/`로 두어 필요할 때만 읽게 한다. 단, **엔진은 하나만** 둔다.
- 권고: **1단계는 airmang의 `engine/` + 자체 작성 얇은 SKILL.md(MCP 없이 chat-engine 절차만)**. 이유: ① `.hwp`를 한컴 없이도 읽고 `.hwpx`로 편집 ② 해시 고정된 배포본 ③ 편집 전 백업·검증 ④ 공공 양식에 치우치지 않음. 2단계(공백이 확인될 때만): 한컴 COM 변환 충실도가 필요하면 jkf87의 `convert_hwp_hancom.ps1` 한 파일만 별도 검토.
- 이 권고는 **직접 시험 전**이다. 서식 충실도, 한컴에서 열리는지, 논문·특허 양식에서 표·번호가 유지되는지는 시험하지 않았다.

## 6. 시험 계획 (사용자 몫, Windows + 한컴 필요, 이 세션은 한컴을 실행하지 못한다)
1. 격리 폴더에 후보 폴더를 복사(업무 폴더 아님). 설치 명령은 쓰지 않고 `chat-engine.md` 절차만 사용.
2. 실제 제출 양식 1건(.hwpx)과 .hwp 1건으로: 읽기·텍스트 추출 → 값 채우기 → 한글에서 열어 육안 확인.
3. 새 문서 1건(제안서나 기술 보고서 Markdown → HWPX), 한글에서 열어 확인.
4. 각 단계에서 `/context` 증가량(스킬 목록 + 호출 시 본문)과 토큰, `eval_log.csv`에 `structure=ext:hwpx`.
5. pass^3: 같은 작업 3회 모두 한글에서 열리고 내용 손실이 없어야 통과.

## 7. 결정 요청
1. 1단계로 airmang 엔진 + 얇은 SKILL.md 방식을 진행해도 되는지(승인 시 `third_party/hwpx-airmang@c6196cf/` 고정, 엔진 해시 대조, 얇은 SKILL.md 작성 후 시험 폴더에서 확인).
2. 엔진 전체를 읽는 대신 `VENDOR.json`의 sha256과 PyPI wheel 해시를 대조하는 방식(공급망 확인)을 허용할지.
