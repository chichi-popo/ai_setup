---
paths:
  - "**/*.cs"
  - "**/*.xaml"
  - "**/*.csproj"
---
# stack-csharp-windows: C#·Windows 데스크톱 점검표

> 출처: ECC(MIT) `rules/csharp`, `csharp-reviewer`, `windows-desktop-e2e`(시험성) 발췌 요약(third_party/ECC@ccd8da1) + 자체 작성 "데스크톱 UI" 절(WPF·WinUI·WinForms, 측정 전 가설). 프로젝트 규칙(CLAUDE.md, 기존 코드 관례)이 이 파일보다 우선한다.
>
> 적용 범위: 이번에 쓰거나 고치는 코드에만 적용한다. 수정 범위 밖의 위반은 고치지 말고 보고만 한다(프로젝트의 최소 변경 원칙이 우선).

## C# 점검
- nullable reference types를 켜고 `!`로 경고를 덮지 않는다. 캐스트는 `is`/`as`로 확인하고 `dynamic`은 쓰지 않는다.
- `.Result`, `.Wait()`, `GetAwaiter().GetResult()` 금지(UI 스레드에서는 교착). `async void`는 이벤트 핸들러에만. 공개 async API는 `CancellationToken`을 받는다.
- 빈 `catch {}`와 예외 삼키기 금지(구체 예외를 처리하거나 `throw;`). `IDisposable`/`IAsyncDisposable`은 `using`/`await using`.
- 값 모델은 `record`, 상속하지 않는 클래스는 `sealed`. 공유 가변 정적 필드를 만들지 않는다. 메서드 약 50줄, 중첩 4단계 이내.

## 보안
- 비밀(API 키, 연결 문자열)을 소스·설정 파일에 두지 않고 사용자 비밀·환경 변수·보안 저장소를 쓴다. 토큰·비밀번호·개인정보를 로그에 남기지 않는다.
- SQL은 매개변수화(ADO.NET, Dapper, EF Core). `Process.Start` 인자에 검증 없는 입력을 쓰지 않는다. 사용자 입력 경로는 `Path.GetFullPath`로 풀고 허용 루트 접두사를 확인한다. `BinaryFormatter`를 쓰지 않는다.
- 스택 트레이스·SQL·파일 경로를 사용자에게 보이는 오류 메시지에 넣지 않는다.

## 데스크톱 UI (WPF·WinUI·WinForms)
- UI 요소는 UI 스레드에서만 만진다. 백그라운드에서는 `Dispatcher.InvokeAsync`(WPF), `DispatcherQueue.TryEnqueue`(WinUI), `Control.Invoke`(WinForms)를 쓰고, 오래 걸리는 작업은 `Task.Run`으로 UI 밖에서 한다.
- WPF·WinUI는 로직을 ViewModel에 두고 code-behind는 UI 전용으로 한다. 바인딩 경로 오타는 컴파일되지 않고 출력 창에만 나타나므로 `nameof`와 컴파일 타임 바인딩(WinUI `x:Bind`)을 우선한다.
- 이벤트 `+=`에는 짝이 되는 `-=`를 둔다(긴 수명 객체가 짧은 수명 View를 붙들어 누수). WinForms의 `Pen`·`Brush`·`Bitmap`은 `using`으로 해제한다. `*.Designer.cs`와 생성 파일은 직접 고치지 않는다.
- 시험성: 상호작용 컨트롤에 안정적인 AutomationId를 준다(WPF `x:Name`, WinForms `AccessibleName`, WinUI `AutomationProperties.AutomationId`).

## 검사·테스트
- 프로젝트에 이미 있는 도구만 쓴다: `dotnet build`, `dotnet format --verify-no-changes`, `dotnet test`. 새 패키지 설치는 승인을 받는다.
- 프로젝트의 테스트 프레임워크(xUnit 등)를 따른다. ViewModel과 서비스 로직은 UI 없이 시험하고 시험 이름은 동작 기준으로 짓는다. 확신이 80% 미만인 지적은 보고하지 않는다.
