
[#description]
Rust 文档约定

[#rules]
- API 文档风格: Rustdoc（`///`、`//!`）标准，提供 `# Examples` 示例块
- 模块层次: 记录 `mod.rs` / `lib.rs` 结构，显示 `pub use` 重导出树
- Trait: 说明 required vs provided 方法、blanket 实现、泛型约束
- 错误处理: 记录 `Result<T, E>` 的错误变体；若使用 `thiserror` / `anyhow` 说明模式
- Feature flags: 记录 `Cargo.toml` 功能标志及其影响
- 异步: 若使用 `tokio` / `async-std` 说明运行时选择及 spawn 模式
- 命名约定: `snake_case` 函数/方法，`PascalCase` 类型/trait，`SCREAMING_SNAKE_CASE` 常量
