
[#description]
Go 文档约定

[#rules]
- API 文档风格: Go 注释（`//` 声明前）标准，记录所有导出符号
- 包结构: 记录 `go.mod` 模块路径和内部包布局
- 错误处理: 记录 `error` 返回值，展示 `errors.Is()` / `errors.As()` sentinel 模式
- 接口: 记录隐式接口满足，使用 `var _ Interface = (*Type)(nil)` 编译时检查
- 并发: 记录 goroutine 启动、channel 模式、`sync.WaitGroup` / `sync.Mutex` / `sync.RWMutex`
- 测试: 注明 `*_test.go` 约定、`go test` 标志、benchmark/example 函数
- 命名约定: `camelCase` 非导出，`PascalCase` 导出，`SCREAMING_SNAKE_CASE` 常量（少见）
