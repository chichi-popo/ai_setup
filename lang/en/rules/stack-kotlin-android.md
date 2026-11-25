---
paths:
  - "**/*.kt"
  - "**/*.kts"
---
# stack-kotlin-android: Kotlin and Android checklist

> Source: condensed from ECC (MIT) `rules/kotlin`, `kotlin-reviewer`, `android-clean-architecture`, and `kotlin-coroutines-flows` (third_party/ECC@ccd8da1). Project rules (CLAUDE.md, project-conventions) and the existing code's conventions win over this file.
>
> Scope: apply to the code you write or change now. Report violations outside the change instead of fixing them (the project's surgical-change rule wins).

## Kotlin checks
- Immutability and null: default to `val`, use `data class` for value types and `copy` for state updates. Public APIs return read-only collections (`List`, `Map`, `Set`). Never use `!!`; use `?.`, `?:`, `requireNotNull()`/`checkNotNull()`.
- Model closed states with sealed classes and an exhaustive `when` without `else`. Names: PascalCase for classes and interfaces, camelCase for functions and properties, SCREAMING_SNAKE_CASE for constants, no `I` prefix on interfaces.
- Put extension functions in a file named after the receiver type and do not attach them to overly generic types such as `Any`. Nest scope functions (`let`, `run`, `apply`, `also`) at most 2 levels. Prefer top-level functions, properties, and string templates over Java-style patterns (static utility classes, getters/setters) and string `+`.
- Errors: `Result<T>` or sealed types, `runCatching`. **Never catch `CancellationException`, or always rethrow it.** Do not use `try-catch` for control flow.

## Coroutine and Flow checks
- No `GlobalScope`; use structured scopes (`viewModelScope`, `coroutineScope`). Use `supervisorScope` when child failures must be independent, and `coroutineScope` + `async` for parallel work.
- Run database and network calls in `withContext(Dispatchers.IO)`, not on `Dispatchers.Main`. Long loops check for cancellation.
- Do not put mutable collections in a `StateFlow` (copy, as in `_state.update { it.copy(list = it.list + item) }`). Do not collect a Flow directly in `init {}`; use `stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), initialValue)` or `launch` in a scope. Collect Flows in an Activity or Fragment with `repeatOnLifecycle`.
- When using Compose: check unstable (mutable) parameters, side effects belong in `LaunchedEffect` or the ViewModel, pass lambdas instead of a `NavController` deep into the tree, give `LazyColumn` items a stable `key()`, watch for missing `remember` keys and objects created inside parameters. Do not create a Flow inside a `@Composable` without `remember`.

## Structure and Android checks
- `domain` does not import Android, Ktor, Room, or any framework (pure Kotlin). Do not expose entities or DTOs to the UI; map them to domain models. Put complex logic in a UseCase, not in the ViewModel. No circular module dependencies. Receive dependencies by constructor injection (Hilt, Koin). A ViewModel uses a single state object, an event input, and one-way data flow.
- Do not store `Activity` or `Fragment` references in singletons or ViewModels (Context leaks). User-visible strings go in `strings.xml`. Serialized classes get `@Keep` or ProGuard/R8 rules. Manage Gradle versions in `libs.versions.toml`.

## Security checks
- Secrets: no API keys, tokens, or credentials in source (locally use git-ignored `local.properties`, for releases use `BuildConfig` generated from CI secrets). Keep sensitive values in `EncryptedSharedPreferences`/Keystore and tokens in secure storage. Clear auth state on logout, use `BiometricPrompt` for sensitive operations, and never log tokens, personal data, or secrets.
- Network and input: HTTPS only, block cleartext traffic with `network_security_config.xml`. Pin certificates for sensitive endpoints and set a timeout on every HTTP client. Validate server responses and user input. Use parameterized queries for Room and SQLDelight and sanitize file paths that come from user input.
- Components: do not leave exported `Activity`, `Service`, `BroadcastReceiver`, deep links, or intent filters without guards. For WebView, enable JavaScript only when needed, validate URLs, and never expose sensitive data through `@JavascriptInterface`. Keep R8 rules for serialization and reflection libraries and test release builds. Report a serious security problem before any other finding.

## Tests and check tools
- Tests: `kotlin.test`/JUnit, Turbine for Flows, `kotlinx-coroutines-test` (`runTest`, TestDispatcher) for coroutines. Prefer hand-written fakes over mocks for complex dependencies and an in-memory database for Room. At minimum test the ViewModel and UseCase of every feature. Use backtick-quoted descriptive test names.
- Checks: run only what the project already has (`./gradlew build`/`test`, ktlint, detekt). Ask before installing new packages. Do not report findings you are less than 80% sure of, and group similar findings into one.
