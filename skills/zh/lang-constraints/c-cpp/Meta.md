
[#description]
C / C++ 文档约定

[#rules]
- API 文档风格: Doxygen（`/** */` / `///`）C++，`/* */` 注释 C；记录所有公开头文件
- 构建系统: 记录 `CMakeLists.txt` / `Makefile` 目标、选项、工具链要求
- 内存模型: 记录所有权（unique_ptr/shared_ptr/raw）、分配策略（arena/stack/heap）、RAII 模式
- ABI 考量: 注明 `extern "C"`、可见性（`__declspec(dllexport)` / `__attribute__((visibility("default")))`）
- 预处理: 记录 `#define` 宏、`#ifdef` 平台守卫、`#pragma` 指令
- 错误处理: 记录返回码、`errno`、`std::expected` / `std::optional` 或异常保证
- 测试: 注明测试框架（GoogleTest / Catch2 / Boost.Test / CTest）
- 命名约定: `snake_case` C 函数/变量，`PascalCase` C++ 类，`UPPER_SNAKE_CASE` 宏
