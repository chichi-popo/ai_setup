---
paths:
  - "**/*.dart"
  - "**/pubspec.yaml"
  - "**/analysis_options.yaml"
---
# stack-flutter-dart: Flutter and Dart checklist

> Source: condensed from ECC (MIT) `rules/dart` and `flutter-reviewer` (third_party/ECC@ccd8da1). Project rules (CLAUDE.md, project-conventions, the state management, routing, and DI approach already chosen) win over this file.
>
> Scope: apply to the code you write or change now. Report violations outside the change instead of fixing them (the project's surgical-change rule wins).

## Dart checks
- Format and names: `dart format`, snake_case files, PascalCase classes, `_` for private members. Trailing commas on multi-line argument lists. Use `package:` imports and no relative (`../`) imports between features. Never edit generated files (`.g.dart`, `.freezed.dart`) by hand.
- Immutability and null: `final`/`const` (`const` constructors), unmodifiable collections in public APIs, `copyWith` for state changes. Avoid `!` and `late` (use `?.`, `??`, Dart 3 patterns) and mark required parameters `required`.
- Types: avoid implicit `dynamic` (`strict-casts`, `strict-inference`, `strict-raw-types`). Model closed states with sealed classes and an exhaustive `switch` without `default`.
- Errors and async: name exception types in `on` clauses; no bare `catch (e)` and no catching `Error` subtypes. Do not use exceptions for control flow. `await` Futures or mark intent with `unawaited()`, and do not write `async` without `await`. Check `context.mounted` before using `BuildContext` after an `await`. Leave no `print` in production code.

## Flutter widget and state checks
- Keep business logic out of `build()` and callbacks. Widgets do not call APIs or databases directly; go through a service or repository. Follow the conventions of the state management the project chose (BLoC, Riverpod, Provider, and so on).
- State: do not keep `isLoading`/`isError`/`hasData` as separate fields; use sealed types or the solution's async state type. Handle every state variant exhaustively and model loading, success, and error separately. Immutable state classes implement `==`/`hashCode`. Never call `.listen()` inside `build()`. Do not create one huge state manager with several responsibilities.
- Widget composition: extract a `build()` over about 80 lines into widget classes and turn `_build*()` helper methods into classes. Use a `const` constructor when all fields are `final`. Use `StatelessWidget` when there is no mutable local state. List items get a stable `ValueKey`. Use `Theme.of(context)` for colors and text styles and named constants for spacing.
- Layers: the domain layer does not import `package:flutter` or the data layer. Map DTOs to domain models at the repository boundary. Receive dependencies by constructor injection; forbid circular dependencies and imports of another package's `src/`.

## Lifecycle, performance, and errors
- Dispose controllers, subscriptions, timers, and `StreamController`s created in `initState` in `dispose()`. Check `mounted` before `setState` and never store `BuildContext` in long-lived objects.
- Performance: use `ListView.builder` for large lists. No sorting, filtering, regex, or I/O inside `build()`. Narrow state subscriptions and use `MediaQuery.sizeOf`. Images get `cacheWidth`/`cacheHeight`; animate opacity with `AnimatedOpacity`.
- Errors: set both `FlutterError.onError` and `PlatformDispatcher.instance.onError`, and customize `ErrorWidget.builder` for release. Do not show raw exceptions in the UI; map them to user-facing messages.
- Accessibility and platform: `semanticLabel` on images, `tooltip` on icons, tap targets of at least 48x48, no meaning conveyed by color alone, `SafeArea`, working back navigation, and localization instead of hardcoded strings.

## Security and platform checks
- Secrets: no API keys or tokens in source (`--dart-define` values are not truly secret, so use a backend proxy for server secrets). Store tokens and personal data only in `flutter_secure_storage`, never in `SharedPreferences` or plaintext files. Clear auth state on logout and never log tokens or passwords.
- Network and input: HTTPS only, block cleartext traffic with Android `network_security_config.xml` (ATS on iOS). Set a timeout on every HTTP client. Validate deep links with `Uri.tryParse` and check scheme, host, and path. Parameterize SQL.
- Android: declare only required permissions in `AndroidManifest.xml`, export `Activity`, `Service`, and `BroadcastReceiver` only when needed and otherwise set `android:exported="false"`. An exported component with an implicit intent filter is reachable by other apps. Use `FLAG_SECURE` on sensitive screens.
- WebView: `webview_flutter` v4+, JavaScript only when needed, validate URLs, never expose Dart callbacks to JavaScript. Release builds use `--obfuscate --split-debug-info` and keep that output out of version control. Report a serious security problem before any other finding.

## Tests and check tools
- Tests: `flutter_test`/`dart:test`, `mocktail`/`mockito` for mocks, `bloc_test` for BLoC, `fake_async` for time. Prefer hand-written fakes over mocks for complex dependencies. Test every state transition (loading to success, loading to error, retry, empty) and use `pumpAndSettle` or an explicit `pump(Duration)` in async tests.
- Checks: run only what the project already has (`dart format`, `flutter analyze`, `flutter test`). Ask before installing new packages. Do not report findings you are less than 80% sure of, and group similar findings into one.
