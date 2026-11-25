---
paths:
  - "**/*.cpp"
  - "**/*.cc"
  - "**/*.cxx"
  - "**/*.h"
  - "**/*.hpp"
  - "**/CMakeLists.txt"
  - "**/*.cmake"
---
# stack-cpp-qt-cmake: C++·Qt·CMake 점검표

> 출처: ECC(MIT) `rules/cpp`, `cpp-reviewer`, `cpp-coding-standards`(체크리스트), `windows-desktop-e2e`(Qt 시험성) 발췌 요약(third_party/ECC@ccd8da1) + 자체 작성 "Qt·CMake" 절(측정 전 가설). 프로젝트 규칙(CLAUDE.md, 기존 코드 관례)이 이 파일보다 우선한다.
>
> 적용 범위: 이번에 쓰거나 고치는 코드에만 적용한다. 수정 범위 밖의 위반은 고치지 말고 보고만 한다(프로젝트의 최소 변경 원칙이 우선).

## C++ 점검
- RAII를 쓰고 맨 `new`/`delete`, `malloc`/`free`를 쓰지 않는다(`make_unique`, `make_shared`). 변수는 선언할 때 초기화하고 기본은 `const`/`constexpr`, 멤버 함수는 가능하면 `const`.
- C 배열과 `strcpy`/`sprintf`를 쓰지 않는다(`std::array`, `std::vector`, `std::string`). `reinterpret_cast`와 C 스타일 캐스트를 피한다. `nullptr`, `enum class`, 인자 하나 생성자는 `explicit`.
- Rule of Zero를 우선하고, 특수 멤버 함수를 하나라도 직접 정의하면 다섯 개를 모두 정의한다. 큰 객체는 `const&`, 작은 타입은 값 전달, sink 인자는 `std::move`. 헤더에 `using namespace`를 쓰지 않는다.
- 동시성: 잠금은 `lock_guard`/`scoped_lock`, 여러 뮤텍스는 `scoped_lock` 하나로 잠가 교착을 피한다. `std::thread`는 반드시 `join`한다. 공유 가변 상태는 동기화한다.
- 예외는 값으로 던지고 참조로 잡는다. 없을 수 있는 값은 `std::optional`. `system()`/`popen()`에 검증 없는 입력을 쓰지 않고 서식 문자열에 사용자 입력을 넣지 않는다.

## Qt (자체 작성)
- QObject는 부모-자식 관계로 소유한다. 부모가 있는 객체를 `delete`하거나 스마트 포인터에 넣지 않는다(이중 해제).
- `connect`는 함수 포인터 문법(`connect(a, &A::sig, b, &B::slot)`)으로 컴파일 타임에 검사한다. 람다가 `this`를 캡처하면 수명이 맞는지 확인한다.
- 위젯은 GUI 스레드에서만 만진다. 작업은 worker QObject를 `moveToThread`로 옮기고 스레드 사이 통신은 시그널로 한다. 이벤트 루프에서 오래 걸리는 작업이나 `sleep`을 하지 않는다. 사용자에게 보이는 문자열은 `tr()`.
- 시험성: `objectName`과 `accessibleName`을 설정한다. Qt 5.7~5.14의 UIA 자동화는 `QT_ACCESSIBILITY=1`이 필요하다.

## CMake·검사
- 타깃 기반으로 쓴다: `target_link_libraries`, `target_include_directories`, `target_compile_features`. 전역 `include_directories`/`link_directories`는 피하고 소스 트리 밖에서 빌드한다.
- Qt는 프로젝트가 쓰는 버전(Qt5 또는 Qt6)의 `find_package`를 따르고 섞지 않는다. `AUTOMOC`/`AUTOUIC`/`AUTORCC` 설정을 확인한다.
- 프로젝트에 이미 있는 도구만 쓴다: `cmake --build`, `ctest --output-on-failure`, `clang-format`, `clang-tidy`, `cppcheck`. 테스트는 GoogleTest와 CTest(`gtest_discover_tests`), 샌드박스는 GCC·Clang `-fsanitize=address,undefined`, MSVC `/fsanitize=address`. 새 의존성(`FetchContent` 포함)은 승인을 받는다. 확신이 80% 미만인 지적은 보고하지 않는다.
