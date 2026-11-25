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
# stack-cpp-qt-cmake: C++, Qt, and CMake checklist

> Source: condensed from ECC (MIT) `rules/cpp`, `cpp-reviewer`, `cpp-coding-standards` (checklist), and `windows-desktop-e2e` (Qt testability) (third_party/ECC@ccd8da1) plus the self-written "Qt" section (hypothesis until measured). Project rules (CLAUDE.md, existing code conventions) win over this file.
>
> Scope: apply to the code you write or change now. Report violations outside the change instead of fixing them (the project's surgical-change rule wins).

## C++ checks
- Use RAII and never raw `new`/`delete` or `malloc`/`free` (`make_unique`, `make_shared`). Initialize variables at declaration, default to `const`/`constexpr`, and make member functions `const` where possible.
- Do not use C arrays or `strcpy`/`sprintf` (`std::array`, `std::vector`, `std::string`). Avoid `reinterpret_cast` and C-style casts. Use `nullptr`, `enum class`, and mark single-argument constructors `explicit`.
- Prefer the Rule of Zero, and if you define any special member function define all five. Pass large objects as `const&`, small types by value, and sink parameters with `std::move`. Never put `using namespace` in headers.
- Concurrency: lock with `lock_guard`/`scoped_lock`, and lock several mutexes with one `scoped_lock` to avoid deadlock. Always `join` a `std::thread`. Synchronize shared mutable state.
- Throw exceptions by value and catch by reference. Use `std::optional` for values that may not exist. Do not pass unvalidated input to `system()`/`popen()` and do not put user input in format strings.

## Qt (self-written)
- QObjects are owned through the parent-child relationship. Do not `delete` an object that has a parent or put it in a smart pointer (double free).
- Use the function-pointer `connect` syntax (`connect(a, &A::sig, b, &B::slot)`) so the compiler checks it. When a lambda captures `this`, check that the lifetime matches.
- Touch widgets only on the GUI thread. Move a worker QObject with `moveToThread` and communicate between threads with signals. Do no long work or `sleep` in the event loop. User-visible strings go through `tr()`.
- Testability: set `objectName` and `accessibleName`. UIA automation on Qt 5.7 to 5.14 needs `QT_ACCESSIBILITY=1`.

## CMake and checks
- Use target-based CMake: `target_link_libraries`, `target_include_directories`, `target_compile_features`. Avoid global `include_directories`/`link_directories` and build out of the source tree.
- For Qt, follow the `find_package` of the version the project uses (Qt5 or Qt6) and do not mix them. Check the `AUTOMOC`/`AUTOUIC`/`AUTORCC` settings.
- Use only the tools the project already has: `cmake --build`, `ctest --output-on-failure`, `clang-format`, `clang-tidy`, `cppcheck`. Tests use GoogleTest with CTest (`gtest_discover_tests`); sanitizers are `-fsanitize=address,undefined` on GCC and Clang and `/fsanitize=address` on MSVC. Ask before adding new dependencies (including `FetchContent`). Do not report findings you are less than 80% sure of.
