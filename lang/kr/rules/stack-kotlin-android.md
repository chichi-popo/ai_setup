---
paths:
  - "**/*.kt"
  - "**/*.kts"
---
# stack-kotlin-android: Kotlin·Android 점검표

> 출처: ECC(MIT) `rules/kotlin`, `kotlin-reviewer`, `android-clean-architecture`, `kotlin-coroutines-flows` 발췌 요약(third_party/ECC@ccd8da1). 프로젝트 규칙(CLAUDE.md, project-conventions)과 기존 코드 관례가 이 파일보다 우선한다.
>
> 적용 범위: 이번에 쓰거나 고치는 코드에만 적용한다. 수정 범위 밖의 위반은 고치지 말고 보고만 한다(프로젝트의 최소 변경 원칙이 우선).

## Kotlin 점검
- 불변·널: `val`을 기본으로, 값 타입은 `data class`, 상태 갱신은 `copy`. 공개 API는 읽기 전용 컬렉션(`List`, `Map`, `Set`). `!!`를 쓰지 않고 `?.`, `?:`, `requireNotNull()`/`checkNotNull()`을 쓴다.
- 닫힌 상태는 sealed 클래스와 `else` 없는 완전한 `when`. 이름은 클래스·인터페이스 PascalCase, 함수·속성 camelCase, 상수 SCREAMING_SNAKE_CASE, 인터페이스에 `I` 접두사 금지.
- 확장 함수는 수신 타입 이름의 파일에 두고 `Any` 같은 지나치게 일반적인 타입에는 붙이지 않는다. 범위 함수(`let`, `run`, `apply`, `also`)는 중첩 2단계 이하. Java식 패턴(정적 유틸 클래스, getter/setter)과 문자열 `+` 대신 최상위 함수, 속성, 문자열 템플릿.
- 오류: `Result<T>`나 sealed 타입, `runCatching`. **`CancellationException`은 잡지 않거나 반드시 다시 던진다.** 제어 흐름에 `try-catch`를 쓰지 않는다.

## 코루틴·Flow 점검
- `GlobalScope`를 쓰지 않고 구조화된 범위(`viewModelScope`, `coroutineScope`)를 쓴다. 자식 실패가 서로 독립이어야 하면 `supervisorScope`. 병렬 작업은 `coroutineScope` + `async`.
- 데이터베이스·네트워크 호출은 `withContext(Dispatchers.IO)`로, `Dispatchers.Main`에서 하지 않는다. 긴 루프는 취소를 확인한다.
- `StateFlow`에 가변 컬렉션을 넣지 않는다(`_state.update { it.copy(list = it.list + item) }`처럼 복사). `init {}`에서 Flow를 바로 수집하지 말고 `stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), 초기값)` 또는 범위에서 `launch`한다. Activity·Fragment에서 Flow 수집은 `repeatOnLifecycle`로 한다.
- Compose를 쓸 때: 불안정한(가변) 파라미터, 부수 효과는 `LaunchedEffect`나 ViewModel에서, `NavController`는 깊이 넘기지 말고 람다로, `LazyColumn`에는 안정적인 `key()`, `remember` 키 누락, 파라미터 안 객체 생성을 점검한다. `@Composable` 안에서 `remember` 없이 Flow를 만들지 않는다.

## 구조·Android 점검
- `domain`은 Android·Ktor·Room 등 프레임워크를 import하지 않는다(순수 Kotlin). 엔티티·DTO는 UI에 노출하지 않고 도메인 모델로 매핑한다. 복잡한 로직은 ViewModel이 아니라 UseCase에 둔다. 모듈 순환 의존 금지. 의존은 생성자 주입(Hilt, Koin)으로 받는다. ViewModel은 단일 상태 객체, 이벤트 입력, 단방향 흐름.
- `Activity`·`Fragment` 참조를 싱글톤이나 ViewModel에 저장하지 않는다(Context 누수). 사용자에게 보이는 문자열은 `strings.xml`. 직렬화 클래스에는 `@Keep`이나 ProGuard/R8 규칙. Gradle 버전은 `libs.versions.toml`로 관리한다.

## 보안 점검
- 비밀: 소스에 API 키·토큰·인증 정보를 두지 않는다(로컬은 `local.properties`(git 제외), 릴리스는 CI 비밀로 만든 `BuildConfig`). 민감 값은 `EncryptedSharedPreferences`/Keystore, 토큰은 안전 저장소에 둔다. 로그아웃 때 인증 상태를 지우고, 민감 작업에는 `BiometricPrompt`. 토큰·개인정보·비밀을 로그에 남기지 않는다.
- 네트워크·입력: HTTPS만 쓰고 `network_security_config.xml`로 평문 트래픽을 막는다. 민감한 엔드포인트는 인증서 고정, 모든 HTTP 클라이언트에 타임아웃. 서버 응답과 사용자 입력을 검증한다. Room·SQLDelight는 매개변수화 쿼리, 사용자 입력 파일 경로는 정화한다.
- 컴포넌트: export된 `Activity`·`Service`·`BroadcastReceiver`와 딥링크·intent filter는 보호 장치 없이 두지 않는다. WebView는 JavaScript를 필요할 때만 켜고 URL을 검증하며 `@JavascriptInterface`로 민감 데이터를 노출하지 않는다. 직렬화·리플렉션 라이브러리의 R8 keep 규칙을 두고 릴리스 빌드를 시험한다. 심각한 보안 문제는 다른 점검보다 먼저 보고한다.

## 테스트·검사 도구
- 테스트: `kotlin.test`/JUnit, Flow는 Turbine, 코루틴은 `kotlinx-coroutines-test`(`runTest`, TestDispatcher). 복잡한 의존성은 mock보다 손으로 쓴 fake, Room은 인메모리 DB. 기능마다 최소한 ViewModel과 UseCase를 시험한다. 시험 이름은 백틱 서술형.
- 검사: 프로젝트에 이미 있는 것만 실행한다(`./gradlew build`/`test`, ktlint, detekt). 새 패키지 설치는 승인을 받는다. 확신이 80% 미만인 지적은 보고하지 않고 비슷한 지적은 묶어서 보고한다.
