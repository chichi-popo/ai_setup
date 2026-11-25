# 외부 스킬 검토표 — ECC 점검표 발췌 (번들 1: python-ml, vue-ts)

- 이름 / 출처 URL: Everything Claude Code (ECC) — https://github.com/affaan-m/ECC
- 커밋 SHA (고정본): ccd8da1a724b7b9baf1b6b711073840f8e143313 (VERSION 2.2.3, 커밋일 2026-11-19)
- 검토일 / 검토자: 2026-11-20 / Claude (사용자 초롱 승인 하에 진행)
- 도입 목적 (한 문장, 지금 필요한 작업): Python·ML과 Vue3·TS 코드를 쓰고 리뷰할 때 쓸 언어별 점검 기준을 상시 비용 없이(경로 조건부 로드) 갖춘다.

**형태**: ECC를 설치하지 않는다. 훅·agent·명령·스킬은 가져오지 않고, 규칙·reviewer 문서의 점검 항목만 한국어/영어 요약으로 `lang/{kr,en}/rules/stack-*.md`에 옮겼다. 원문 사본은 이 폴더(참조 전용)에 둔다.

## 게이트 (모두 "예"여야 통과)

| 항목 | 예/아니오 | 근거(파일·줄) |
|---|---|---|
| SKILL.md 전문을 읽었다 | 예(해당 파일 전문. SKILL.md 아님: agent 2개와 규칙 14개) | agents/python-reviewer.md, agents/mle-reviewer.md, rules/python/(coding-style, patterns, security, testing 4개. fastapi.md·hooks.md는 읽지 않아 사본에서 제외), rules/typescript/(5 전부), rules/vue/(5 전부). 일부는 출력 폭 제한으로 줄 끝이 잘려 읽은 부분이 있어, frontmatter 줄과 소개 문단은 별도로 전문 확인함 |
| 포함된 스크립트·바이너리를 전부 읽었다 | 없음 | 가져온 것은 .md 파일뿐. 실행 파일 없음 |
| 네트워크 호출이 없거나, 있다면 목적과 대상이 명확하다 | 예(없음) | 가져온 파일 내 URL은 문서 링크(vuejs.org 등)뿐이며 명령이 아님. `grep -E "curl|fetch\(|child_process|rm -rf"` 해당 없음 |
| 환경 변수·홈 폴더·비밀 파일을 읽지 않는다 | 예 | 번들은 읽기 전용 점검 문장만 포함. 코드 예시의 `os.environ`/`process.env`는 "하드코딩 금지" 예시 |
| 파일 삭제·git 이력 변경·설정 파일 수정을 하지 않는다 | 예 | 번들 규칙에 해당 동작 없음. 설치·훅 등록 없음 |
| description이 좁다(특정 작업에서만 발동) | 예 | 규칙 파일은 description이 없고 `paths:`(`*.py`, `*.ipynb` / `*.vue`, `*.ts`, `*.js`, `*.css`)에 해당하는 파일을 다룰 때만 로드. 상시 목록 비용 0. **다만 `*.js`·`*.css`는 설정·유틸 파일에도 걸려 로드 빈도가 높음(측정 필요)** |
| 기존 역할 스킬과 중복되지 않는다 | 예 | 기존 `code-change`는 절차(테스트·승인), 번들은 언어별 점검 기준. reviewer 에이전트 지시문과 겹치는 일반 항목은 번들에서 제외하지 못한 부분이 있을 수 있어 시험에서 확인 |
| 문체·출력 형식을 강제하지 않는다 | 예 | 출력 형식·말투 규정 없음(ECC 원문의 `[SEVERITY]` 출력 형식과 승인 기준은 가져오지 않음) |
| 라이선스가 회사 사용에 문제없다 | 예(MIT) | LICENSE 동봉, 저작권 표기 유지 |
| 회사 보안 정책상 외부 코드 사용이 허용된다(확인 방법: 사용자 답변 2026-11-20) | 조건부 예 | 사용자 지침: 외부 문서 요약 사용은 **매번 사용자에게 물어본 뒤 반영**한다(기본값). 번들은 요약만 담고 코드·훅은 없으나, 이후 ECC에서 항목을 추가할 때마다 이 확인을 거친다 |

## 번들에 넣지 않은 것
- "Prompt Defense Baseline" 6줄, `[SEVERITY]` 출력 형식, APPROVE/BLOCK 판정, `common` 규칙 전체(상시 19.9KB), 훅 문서(rules/*/hooks.md의 prettier·tsc 자동 실행 제안은 우리 훅 정책과 충돌 소지), 다른 agent 위임 목록, 프레임워크별(Django/FastAPI/Flask) 항목, Feature-Sliced Design 권고.
- 자체 작성: Vue 번들의 "UI 간결화" 절(가설)은 2026-11-20 축약 때 삭제했다(필요하면 `_backup/pre_vue_trim_20261120/`에서 복원).

## 격리 시험 결과
- (아직 안 함) 시험 폴더 / 기대 동작 / 실제 동작 / 예상 밖 동작을 시험 후 기입.
- 확인할 것: ① `paths:` 규칙이 해당 파일을 읽거나 편집할 때만 로드되는가 ② reviewer 서브에이전트에도 적용되는가 ③ `/context` 전후 증가량 ④ 같은 과제를 번들 있음/없음으로 3회씩(pass^3).

## 측정 (eval_log.csv, structure=`ext:ecc-checklists`)

| 작업 | 기준선 토큰 | 켠 상태 토큰 | 품질(1~5) 기준선 → 켠 상태 |
|---|---|---|---|
| (시험 후 기입) | | | |

## 결정

- [ ] 도입(번들을 프로젝트에 적용)  - [x] 보류(시험 전 초안: 파일 배치·구조 검사만 통과)  - [ ] 거부
- 사유: 격리 시험·측정이 남았다(사내 정책 게이트는 "매번 확인" 조건으로 통과). 시험 통과 전에는 기존 프로젝트에 적용하지 않는다.

## 추가 검토: stack-flutter-dart, stack-kotlin-android (2026-11-20, 사용자 승인 후 반영)
- 읽은 것: agents/flutter-reviewer.md, agents/kotlin-reviewer.md, rules/dart/(5 전부), rules/kotlin/(5 전부). 모두 .md이며 실행 파일·스크립트 없음.
- 일부만 읽은 것: skills/android-clean-architecture/SKILL.md, skills/kotlin-coroutines-flows/SKILL.md는 제한된 범위만 읽고 코루틴·계층 항목 확인용으로 사용했다. 사본은 대조용으로 동봉.
- 읽지 않은 것(사본에 넣지 않음): skills/flutter-dart-code-review(23KB), skills/dart-flutter-patterns(16KB). 필수 항목이 rules·agent로 충분해 제외했다.
- 가져오지 않은 것: "Prompt Defense Baseline", 출력 형식·APPROVE/BLOCK 판정, hooks.md의 자동 실행 제안(dart format/ktlint 등을 자동 실행), 다른 agent 위임 목록.
- `paths:` 조건: Dart = `*.dart`, `pubspec.yaml`, `analysis_options.yaml`; Kotlin = `*.kt`, `*.kts`. 둘 다 파일을 다룰 때만 로드.
- 크기(kr): flutter-dart 5.9KB, kotlin-android 5.1KB. Vue 번들과 비슷한 수준이며 측정 전.
- 한계: Java, Compose 세부, Gradle 설정 파일(`build.gradle.kts` 외 Groovy)은 범위 밖. `AndroidManifest.xml` 점검은 Dart 번들 문장에만 있고 파일 조건에는 넣지 않았다(`.xml` 로드 빈도 우려).
- 결정: 위 "보류"와 동일. 격리 시험(cyber_watcher, notion-app) 후 기입.

## Vue 번들 축약 (2026-11-20)
- 시험 1 결과(cyber-web): A→B 컨텍스트 증가 차이 약 2.5k 토큰으로 예산 1.5k 초과. 로드 동작(`.vue`를 읽은 뒤에만 로드)은 기대대로.
- 조치: kr 3,296자 → 1,829자. 삭제: "UI 간결화" 절, Vitest 세부(검사·테스트 한 절로 병합), 컴포저블 반환 형식·SFC 블록 순서·생명주기 훅 등록 시점·Pinia `$reset` 등 세부. 추가: "기존 파일이 JS면 그 언어를 따른다"(JS 프로젝트에서 `lang="ts"` 누락을 지적하던 잡음 방지).
- 다음: 축약본으로 시험 1을 다시 하여 A/B 증가 차이를 기록(목표 ≤ 1.5k, 기대 약 1.4k).
- 축약 후 재측정(cyber-web, 시험 1, 단일 실행): A 44.1k→59.8k(+15.7k), B 44.1k→61.5k(+17.4k) → B−A 약 1.7k(축약 전 약 2.5k). 시작 시점은 A·B 동일(44.1k). 같은 조건 반복 편차가 약 0.5k라 오차를 감안하면 예산 1.5k 경계. 판단: 추가 축약은 보류하고 시험 4(품질 A/B)로 판정.

## 추가 검토: stack-csharp-windows, stack-cpp-qt-cmake (2026-11-20, 사용자 승인 후 반영)
- 전문 확인: rules/csharp(5), rules/cpp(5), agents/csharp-reviewer, agents/cpp-reviewer. 모두 .md, 실행 파일 없음.
- 일부만 읽음(사본 동봉): skills/windows-desktop-e2e(30KB, 핵심 개념·프레임워크별 시험성 설정·Qt 절 제목만 확인, pywinauto 예제 코드는 읽지 않음), skills/cpp-coding-standards(22KB, 절 제목과 끝의 체크리스트만 확인).
- 읽지 않음·미포함: skills/dotnet-patterns(제목만 훑음, ASP.NET·EF 중심이라 제외), skills/csharp-testing, skills/cpp-testing(키워드만 확인).
- 가져오지 않음: Prompt Defense Baseline, `[SEVERITY]` 출력 형식, APPROVE/BLOCK 판정, hooks.md의 자동 실행 제안(dotnet format/build/test, clang-format/tidy 자동 실행), ASP.NET Core·EF Core·Blazor·Minimal API·Repository·Options·ApiResponse 패턴(서버 중심이라 데스크톱 앱에 맞지 않음), 90% 이상 커버리지 목표.
- **ECC에는 WPF·WinUI·WinForms·Qt·CMake 내용이 거의 없다**(windows-desktop-e2e의 시험성 설정 외). 두 번들의 "데스크톱 UI"와 "Qt" 절은 자체 작성한 가설이며 출처 검증이 없다. 측정 전에는 도입하지 않는다.
- `paths:` 조건: C# = `*.cs`, `*.xaml`, `*.csproj`; C++ = `*.cpp`, `*.cc`, `*.cxx`, `*.h`, `*.hpp`, `CMakeLists.txt`, `*.cmake`. `.h`는 C 프로젝트에서도 로드된다.
- 크기(kr): csharp-windows 1,945자, cpp-qt-cmake 2,159자(Vue 축약본 1,829자가 약 1.7k 토큰이었음, 이 둘은 약간 더 클 수 있음, 측정 전).
- 결정: 위 "보류"와 동일. 시험 프로젝트가 아직 없다(WPF/WinUI/WinForms/Qt 중 실제 프로젝트 지정 필요).
