# Rust 文档约定

## 适用场景

检测到 `Cargo.toml` 时加载此约束。

## 约束规则

### API 文档风格

使用 Rustdoc：

```rust
/// 计算两个数的和。
///
/// # Examples
///
/// ```
/// let result = crate::math::add(2, 3);
/// assert_eq!(result, 5);
/// ```
///
/// # Panics
///
/// 当 `a + b` 溢出时 panic。
pub fn add(a: i32, b: i32) -> i32 {
    a.checked_add(b).expect("overflow")
}
```

### 模块层次

展示 `pub use` 重导出树：

```rust
// lib.rs
pub mod math;
pub use math::add;  // 用户可以直接 use crate::add
```

### Trait 文档

```rust
/// 可序列化为 JSON 的接口
pub trait ToJson {
    /// 将对象序列化为 JSON 字符串。
    fn to_json(&self) -> String;
}

/// 为所有 `T: Display` 实现 ToJson
impl<T: Display> ToJson for T {
    fn to_json(&self) -> String {
        format!("{{\"value\": \"{}\"}}", self)
    }
}
```

### 错误处理

```rust
/// 从文件中读取配置
///
/// # Errors
///
/// 返回 `IoError` 如果文件无法读取，
/// 返回 `ParseError` 如果内容格式无效。
pub fn load_config(path: &str) -> Result<Config, ConfigError> {
    // ...
}
```

### 命名约定

| 范围 | 约定 |
|---|---|
| 函数/方法 | `snake_case` |
| 类型/trait | `PascalCase` |
| 常量 | `SCREAMING_SNAKE_CASE` |
| 宏 | `snake_case!` |
