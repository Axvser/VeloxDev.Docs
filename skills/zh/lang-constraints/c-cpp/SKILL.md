# C / C++ 文档约定

## 适用场景

检测到 `CMakeLists.txt` / `Makefile` 及 `.c` / `.cpp` / `.h` 源码时加载此约束。

## 约束规则

### API 文档风格

使用 Doxygen（C++ `///`，C `/* */`）：

```cpp
/// @brief 计算两个数的和
///
/// @param a 第一个加数
/// @param b 第二个加数
/// @return a + b 的结果
/// @throw std::overflow_error 当结果溢出时
int add(int a, int b) {
    if ((b > 0) && (a > INT_MAX - b)) {
        throw std::overflow_error("integer overflow");
    }
    return a + b;
}
```

### 内存模型

记录所有权和 RAII 模式：

```cpp
/// @brief 管理数据库连接的生命周期
class DatabaseConnection {
public:
    DatabaseConnection(const std::string& conn_str);
    ~DatabaseConnection();  // RAII：析构时自动关闭连接

    // 禁止拷贝
    DatabaseConnection(const DatabaseConnection&) = delete;
    DatabaseConnection& operator=(const DatabaseConnection&) = delete;

private:
    std::unique_ptr<ConnectionImpl> impl_;  // 唯一所有权
};
```

### 错误处理

```cpp
/// @brief 读取配置文件
/// @return 解析后的配置，如果失败返回 std::nullopt
std::optional<Config> loadConfig(const std::string& path) {
    std::ifstream file(path);
    if (!file) {
        return std::nullopt;
    }
    // ...
}
```

### 命名约定

| 范围 | 约定 |
|---|---|
| C 函数/变量 | `snake_case` |
| C++ 类 | `PascalCase` |
| 宏常量 | `UPPER_SNAKE_CASE` |
| 命名空间 | `snake_case` |
