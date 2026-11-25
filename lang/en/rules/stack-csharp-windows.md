---
paths:
  - "**/*.cs"
  - "**/*.xaml"
  - "**/*.csproj"
---
# stack-csharp-windows: C# and Windows desktop checklist

> Source: condensed from ECC (MIT) `rules/csharp`, `csharp-reviewer`, and `windows-desktop-e2e` (testability) (third_party/ECC@ccd8da1) plus the self-written "Desktop UI" section (WPF, WinUI, WinForms; hypothesis until measured). Project rules (CLAUDE.md, existing code conventions) win over this file.
>
> Scope: apply to the code you write or change now. Report violations outside the change instead of fixing them (the project's surgical-change rule wins).

## C# checks
- Enable nullable reference types and do not silence warnings with `!`. Check casts with `is`/`as` and do not use `dynamic`.
- Never use `.Result`, `.Wait()`, or `GetAwaiter().GetResult()` (they deadlock on the UI thread). `async void` only for event handlers. Public async APIs take a `CancellationToken`.
- No empty `catch {}` and no swallowed exceptions (handle a specific exception or `throw;`). Use `using`/`await using` for `IDisposable`/`IAsyncDisposable`.
- Use `record` for value models and `sealed` for classes that are not inherited. Do not create shared mutable static fields. Keep methods to about 50 lines and nesting to 4 levels.

## Security
- Keep secrets (API keys, connection strings) out of source and config files; use user secrets, environment variables, or a secure store. Never log tokens, passwords, or personal data.
- Parameterize SQL (ADO.NET, Dapper, EF Core). Do not pass unvalidated input to `Process.Start` arguments. Resolve user-supplied paths with `Path.GetFullPath` and check the allowed root prefix. Do not use `BinaryFormatter`.
- Keep stack traces, SQL, and file paths out of user-visible error messages.

## Desktop UI (WPF, WinUI, WinForms)
- Touch UI elements only on the UI thread. From the background use `Dispatcher.InvokeAsync` (WPF), `DispatcherQueue.TryEnqueue` (WinUI), or `Control.Invoke` (WinForms), and run long work outside the UI with `Task.Run`.
- In WPF and WinUI keep logic in the ViewModel and keep code-behind UI-only. A binding path typo does not fail the compile and shows up only in the output window, so prefer `nameof` and compile-time binding (WinUI `x:Bind`).
- Pair every event `+=` with a `-=` (a long-lived object holding a short-lived View leaks). Release WinForms `Pen`, `Brush`, and `Bitmap` with `using`. Do not edit `*.Designer.cs` or generated files by hand.
- Testability: give interactive controls a stable AutomationId (WPF `x:Name`, WinForms `AccessibleName`, WinUI `AutomationProperties.AutomationId`).

## Checks and tests
- Use only the tools the project already has: `dotnet build`, `dotnet format --verify-no-changes`, `dotnet test`. Ask before installing new packages.
- Follow the project's test framework (xUnit and the like). Test ViewModel and service logic without the UI and name tests by behavior. Do not report findings you are less than 80% sure of.
