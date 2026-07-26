# Go 文档约定

## 适用场景

检测到 `go.mod` 时加载此约束。

## 约束规则

### API 文档风格

Go 注释（声明前紧邻的 `//` 注释）：

```go
// Add 计算两个数的和。
// 返回 a + b，如果溢出则 panic。
func Add(a, b int) int {
    if a > 0 && b > math.MaxInt-a {
        panic("overflow")
    }
    return a + b
}
```

### 错误处理

```go
// LoadConfig 从指定路径加载配置文件。
// 如果文件不存在，返回 ErrConfigNotFound。
func LoadConfig(path string) (*Config, error) {
    if _, err := os.Stat(path); os.IsNotExist(err) {
        return nil, ErrConfigNotFound
    }
    // ...
}
```

### 接口

```go
type UserStore interface {
    GetUser(id int) (*User, error)
    CreateUser(u *User) error
}

// compile-time 检查
type inMemoryStore struct{}
var _ UserStore = (*inMemoryStore)(nil)
```

### 并发模式

```go
// ProcessUsers 并发处理用户列表。
// 使用 errgroup 管理 goroutine 生命周期。
func ProcessUsers(users []User) error {
    g, ctx := errgroup.WithContext(context.Background())
    for _, u := range users {
        u := u
        g.Go(func() error {
            return processUser(ctx, u)
        })
    }
    return g.Wait()
}
```

### 命名约定

| 范围 | 约定 |
|---|---|
| 导出符号 | `PascalCase` |
| 非导出符号 | `camelCase` |
| 常量 | `camelCase`（少见 `SCREAMING_SNAKE_CASE`） |
