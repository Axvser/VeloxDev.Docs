# .NET 文档约定（C# / VB / F#）

## 适用场景

检测到 `.slnx` / `.sln` / `.csproj` / `.vbproj` / `.fsproj` 时加载此约束。

## 约束规则

### API 文档风格

使用 XML doc comments：

```xml
/// <summary>
/// 计算两个数的和
/// </summary>
/// <param name="a">第一个加数</param>
/// <param name="b">第二个加数</param>
/// <returns>a 与 b 的和</returns>
/// <exception cref="ArgumentOutOfRangeException">参数超出有效范围时抛出</exception>
public int Add(int a, int b) => a + b;
```

### 可见性识别

- `public` = 公开 API，必须记录
- `internal` = 非公开，除非有 `InternalsVisibleTo` 才记录
- `private protected` = 实现细节，不记录
- 注意 `[EditorBrowsable(EditorBrowsableState.Never)]` 和 `[Obsolete]` 标记

### 异步模式

```csharp
/// <summary>
/// 异步获取用户信息
/// </summary>
/// <param name="userId">用户标识</param>
/// <param name="cancellationToken">取消令牌</param>
public Task<User> GetUserAsync(int userId, CancellationToken cancellationToken = default)
```

### 依赖注入

说明服务的 DI 生命周期：

```csharp
// Singleton: 整个应用共享一个实例
builder.Services.AddSingleton<IUserStore, InMemoryUserStore>();
// Scoped: 每个请求范围一个实例
builder.Services.AddScoped<IUserService, UserService>();
// Transient: 每次注入一个新实例
builder.Services.AddTransient<IEmailSender, EmailSender>();
```

### 可空性

尊重可空引用类型：

```csharp
// string? 表示可能为 null
public string? GetOptionalValue(string key) { ... }
// string 表示不为 null
public string GetRequiredValue(string key) { ... }
```

### 命名约定

| 范围 | 约定 |
|---|---|
| 公开成员 | `PascalCase` |
| 参数 | `camelCase` |
| 私有字段 | `_camelCase` |
| 接口 | `I` + `PascalCase` |
