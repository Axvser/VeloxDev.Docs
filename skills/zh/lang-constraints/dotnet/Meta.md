
[#description]
.NET 文档约定（C# / VB / F#）

[#rules]
- API 文档风格: XML doc comments（`/// <summary>`、`<param>`、`<returns>`、`<exception>`），记录所有 `public` 类型和成员
- 可见性识别: `internal` 非公开 API；注意 `[EditorBrowsable(EditorBrowsableState.Never)]` 和 `[Obsolete]`
- 测试可及性: 检查 `InternalsVisibleTo`，通过此机制暴露的 API 非公开
- 异步模式: 明确标注 `Task` / `Task<T>` / `ValueTask<T>`，说明 CancellationToken 支持
- 可空性: 尊重可空引用类型（`string?` vs `string`），记录 API 的空值约定
- 依赖注入: 说明需要注册的服务及生命周期（Singleton / Scoped / Transient）
- 配置模式: 若使用 `IOptions<T>` / `IConfiguration` 记录绑定方式
- 命名约定: `PascalCase` 公开成员，`camelCase` 参数，`_camelCase` 私有字段
