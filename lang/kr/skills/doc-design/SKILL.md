---
name: doc-design
description: Decide and apply the look of PPT and Word deliverables (colours, fonts, margins, slide master, Word styles) from a reference or the project DESIGN.md, before the pptx/docx skill builds the file. Use whenever a .pptx or .docx is created or restyled.
---
# doc-design

모양(색·글꼴·여백·레이아웃·마스터·스타일)만 맡는다. 내용 구성은 `ppt-structuring`·`tech-writing`, 파일 생성은 계정의 pptx·docx skill이 한다.

## 루프 계약
- 성공 기준: 쓰는 값이 모두 `.ai/design/DESIGN.md` → `style:` → `base:` 순으로 추적된다. 차트·표는 편집 가능한 네이티브 객체다. 렌더링 이미지에서 넘침·겹침·대비 문제가 없다. 원본의 값·라벨·단위가 빠지지 않았다.
- 검증자: 렌더링(슬라이드·페이지 이미지)을 직접 보고, 아래 체크리스트를 항목별로 확인한다. 숫자는 `evidence-verifier`(있으면).
- 중단 조건: 렌더링 후 수정 2회 뒤에도 남는 레이아웃 문제는 목록으로 보고하고 멈춘다. 레퍼런스 값과 DESIGN.md가 충돌하면 고르지 말고 묻는다. 막히면 dispatch.md의 BLOCKED 규칙.

## 절차
1. `.ai/design/DESIGN.md`를 읽는다. 없으면 `.ai/design/`에 템플릿(AI_Tools `lang/kr/DESIGN.template.md`)으로 만들고 `base:`에 공통 기본값 경로를 적는다.
2. 만들기 전에 사용자에게 참고 템플릿·레퍼런스(.pptx/.potx/.docx/.dotx 파일, 이미지·PDF, URL)를 줄 수 있는지 묻는다. 이미 DESIGN.md에 `source:`가 있으면 그것을 쓰고 다시 묻지 않는다.
3. 레퍼런스가 있으면 값을 읽는다.
   - Office 파일: `python .claude/skills/doc-design/design_extract.py <파일> --out .ai/design/extract_<이름>.md` → 파일 내부 테마 값(색 슬롯, 제목·본문 글꼴과 한글 글꼴, 슬라이드 크기·레이아웃 이름, Word 스타일·여백)을 그대로 얻는다.
   - 이미지·PDF·URL: 직접 보고 근사값을 적되 `UNVERIFIED: 색상값(이미지 추정)`으로 표시한다.
   - 역할 매핑(primary·secondary·accent)과 금지 사항을 사용자에게 확인받아 DESIGN.md에 옮긴다. 템플릿 파일은 `template_pptx:`·`template_docx:`에 적고 `python .ai/kb.py new asset <경로>`로 등록한다.
4. 레퍼런스가 없으면 DESIGN.md·base로 진행한다. 분위기를 새로 골라야 하고 카탈로그 skill(pptx-design-styles 등, 승인된 것)이 켜져 있으면 후보 2~3개를 보여 주고 고른 이름을 `style:`에 적는다. 공식 보고·논문·특허 발표는 base를 우선한다.
5. 마스터(PPT)·스타일(Word)을 먼저 확정한다: 캔버스 크기, 제목·본문·footer 자리, 여백 격자, 레이아웃 종류(표지·목차·섹션·본문 1단/2단·표·차트·마무리). 템플릿 파일이 있으면 그 파일을 기반으로 만든다(새로 흉내 내지 않음). Word는 내장 스타일(Title, Heading 1~3, Normal, Caption)을 수정해 쓴다.
6. pptx·docx skill로 파일을 만든다. 차트·표는 네이티브 객체, 색은 팔레트 안에서만.
7. 페이지·슬라이드마다 이미지로 렌더링해 확인하고 체크리스트를 채운다. 승인된 DESIGN.md는 dispatch.md의 승인 기록 규칙대로 해시를 남긴다.

## 체크리스트
- [ ] 레퍼런스 제공 여부를 확인했다(또는 DESIGN.md `source:`를 썼다)
- [ ] 색이 DESIGN.md 팔레트 안에 있고 한 색이 우세하다
- [ ] 글꼴·크기가 DESIGN.md 범위 안이다(한글 글꼴 포함)
- [ ] 마스터·스타일 하나로 일관된다(슬라이드마다 여백·제목 위치를 바꾸지 않음)
- [ ] 차트·표가 편집 가능한 객체이고 원본 값·라벨·단위가 다 들어갔다(뺀 것은 보고)
- [ ] 렌더링에서 넘침·겹침·대비 문제가 없다

## 하지 말 것
- 프로젝트마다 이 skill을 복사해 고치기(값은 DESIGN.md에만).
- 이미지에서 추정한 색을 확인된 값처럼 쓰기.
- HWP 양식을 흉내 낸 docx를 공식 제출본처럼 내기(HWP는 기본이 내용 초안까지만이고 사람이 양식에 옮긴다. `hwpx` 스킬이 설치되어 있고 사용자가 파일을 요청했을 때만 `.hwpx`로 저장하며, 한글에서 열어 확인하라고 안내한다).
- 보고서·논문·특허 작업 중 압축 응답 skill 켜기.
