---
paths:
  - "**/*.dart"
  - "**/pubspec.yaml"
  - "**/analysis_options.yaml"
---
# stack-flutter-dart: Flutter·Dart 점검표

> 출처: ECC(MIT) `rules/dart`, `flutter-reviewer` 발췌 요약(third_party/ECC@ccd8da1). 프로젝트 규칙(CLAUDE.md, project-conventions, 이미 고른 상태관리·라우팅·DI 방식)이 이 파일보다 우선한다.
>
> 적용 범위: 이번에 쓰거나 고치는 코드에만 적용한다. 수정 범위 밖의 위반은 고치지 말고 보고만 한다(프로젝트의 최소 변경 원칙이 우선).

## Dart 점검
- 형식·이름: `dart format`, 파일은 snake_case, 클래스는 PascalCase, 비공개는 `_`. 여러 줄 인자 끝에 trailing comma. `package:` import를 쓰고 기능 사이에 상대 경로(`../`)를 쓰지 않는다. 생성 파일(`.g.dart`, `.freezed.dart`)은 직접 고치지 않는다.
- 불변·널: `final`/`const`(`const` 생성자), 공개 API는 수정 불가 컬렉션, 상태 변경은 `copyWith`. `!`와 `late`를 피하고(`?.`, `??`, Dart 3 패턴), 필수 인자는 `required`.
- 타입: 암시적 `dynamic`을 피한다(`strict-casts`, `strict-inference`, `strict-raw-types`). 닫힌 상태는 sealed 클래스와 `default` 없는 완전한 `switch`.
- 오류·비동기: `on` 절로 예외 타입을 지정하고 bare `catch (e)`와 `Error` 하위 타입 잡기를 금지한다. 제어 흐름에 예외를 쓰지 않는다. Future는 `await`하거나 `unawaited()`로 의도를 밝히고, `await` 없는 `async`를 만들지 않는다. `await` 뒤 `BuildContext`를 쓰기 전에 `context.mounted`를 확인한다. 운영 코드에 `print`를 남기지 않는다.

## Flutter 위젯·상태 점검
- 비즈니스 로직을 `build()`나 콜백에 두지 않는다. API·DB는 위젯에서 직접 부르지 않고 서비스/리포지토리를 거친다. 프로젝트가 고른 상태관리(BLoC, Riverpod, Provider 등)의 관례를 따른다.
- 상태: `isLoading`/`isError`/`hasData`를 따로 두지 말고 sealed 타입이나 해당 솔루션의 비동기 상태 타입을 쓴다. 모든 상태 변형을 빠짐없이 처리하고 로딩·성공·오류를 구분해 모델링한다. 불변 상태 클래스는 `==`/`hashCode`를 구현한다. `build()` 안에서 `.listen()`을 호출하지 않는다. 여러 책임을 가진 거대한 상태 관리자를 만들지 않는다.
- 위젯 구성: `build()`가 약 80줄을 넘으면 위젯 클래스로 분리하고 `_build*()` 헬퍼 메서드는 클래스로 뺀다. 모든 필드가 `final`이면 `const` 생성자. 가변 지역 상태가 없으면 `StatelessWidget`. 목록 항목에는 안정적인 `ValueKey`. 색·글꼴은 `Theme.of(context)`로, 간격은 이름 있는 상수로.
- 계층: 도메인 계층은 `package:flutter`나 데이터 계층을 import하지 않는다. DTO는 리포지토리 경계에서 도메인 모델로 매핑한다. 의존은 생성자 주입으로 받고, 순환 의존과 다른 패키지의 `src/` import를 금지한다.

## 수명주기·성능·오류
- `initState`에서 만든 컨트롤러·구독·타이머·`StreamController`는 `dispose()`에서 해제한다. `setState` 전에 `mounted`를 확인하고 `BuildContext`를 오래 사는 객체에 저장하지 않는다.
- 성능: 큰 목록은 `ListView.builder`. `build()` 안에서 정렬·필터·정규식·I/O를 하지 않는다. 상태 구독 범위를 좁히고 `MediaQuery.sizeOf`를 쓴다. 이미지는 `cacheWidth`/`cacheHeight`, 애니메이션 투명도는 `AnimatedOpacity`.
- 오류: `FlutterError.onError`와 `PlatformDispatcher.instance.onError`를 설정하고, 릴리스에서 `ErrorWidget.builder`를 사용자화한다. 예외 원문을 UI에 노출하지 말고 사용자용 문구로 바꾼다.
- 접근성·플랫폼: 이미지 `semanticLabel`, 아이콘 `tooltip`, 터치 대상 48x48 이상, 색만으로 의미를 전달하지 않기, `SafeArea`, 뒤로 가기 동작, 하드코딩 문자열 대신 지역화.

## 보안·플랫폼 점검
- 비밀: 소스에 API 키·토큰을 두지 않는다(`--dart-define` 값도 진짜 비밀은 아니므로 서버 비밀은 백엔드 프록시). 토큰·개인정보는 `flutter_secure_storage`에만 저장하고 `SharedPreferences`나 평문 파일에는 저장하지 않는다. 로그아웃 때 인증 상태를 지우고 토큰·비밀번호를 로그에 남기지 않는다.
- 네트워크·입력: HTTPS만 쓰고 Android `network_security_config.xml`로 평문 트래픽을 막는다(iOS는 ATS). 모든 HTTP 클라이언트에 타임아웃. 딥링크는 `Uri.tryParse` 후 스킴·호스트·경로를 검증한다. SQL은 매개변수화.
- Android: `AndroidManifest.xml`에는 필요한 권한만, `Activity`·`Service`·`BroadcastReceiver`는 필요할 때만 export하고 아니면 `android:exported="false"`. 암시적 intent filter가 있는 export 컴포넌트는 다른 앱이 접근할 수 있다. 민감한 화면은 `FLAG_SECURE`.
- WebView: `webview_flutter` v4+, JavaScript는 필요할 때만, URL 검증, Dart 콜백을 JavaScript에 노출하지 않는다. 릴리스는 `--obfuscate --split-debug-info`, 그 산출물은 버전 관리 밖에 둔다. 심각한 보안 문제는 다른 점검보다 먼저 보고한다.

## 테스트·검사 도구
- 테스트: `flutter_test`/`dart:test`, 모킹은 `mocktail`/`mockito`, BLoC은 `bloc_test`, 시간은 `fake_async`. 복잡한 의존성은 mock보다 손으로 쓴 fake. 상태 전이(loading→success, loading→error, retry, empty)를 모두 시험하고 비동기 시험은 `pumpAndSettle`이나 명시적 `pump(Duration)`로 한다.
- 검사: 프로젝트에 이미 있는 것만 실행한다(`dart format`, `flutter analyze`, `flutter test`). 새 패키지 설치는 승인을 받는다. 확신이 80% 미만인 지적은 보고하지 않고 비슷한 지적은 묶어서 보고한다.
