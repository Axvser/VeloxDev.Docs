# APIs

## 职责

为每个功能模块编写完整的 API 参考文档。比 Quick Start 更深入，展示所有使用模式（声明式 + 命令式），包含安全覆盖。

## 编写要求

### API 发现优先级

提取 API 文档时，遵循以下严格优先层级：

> **优先级 1 — Demo/示例项目**
> 扫描 `Examples/` 目录中该 API 的真实使用代码，**完整读取所有源文件**。Demo 项目揭示了预期的公共 API 表面和最惯用的调用模式。
>
> **优先级 2 — 单元测试**
> **完整读取所有测试文件**，提取 API 签名、典型输入/输出和边界情况。测试提供了真实的参数值、断言期望和异常路径。
>
> **优先级 3（兜底）— 源码接口自行发现**
> 仅在 Demo 和测试都不存在时：直接从源文件中读取公共 API 签名。这些必须明确标注为*推断所得*。

### 语义层面

- 此 API 解决什么问题？（高级意图，非方法名本身）
- 何时使用 vs 替代方案
- 前置条件和后置条件

### 完整代码层面

```csharp
/// <summary>
/// 异步获取用户信息
/// </summary>
/// <param name="userId">用户唯一标识</param>
/// <param name="cancellationToken">取消令牌</param>
/// <returns>用户对象，未找到时返回 null</returns>
/// <exception cref="ArgumentException">userId 无效时抛出</exception>
/// <exception cref="HttpRequestException">网络错误时抛出</exception>
public async Task<User?> GetUserAsync(
    int userId,
    CancellationToken cancellationToken = default)
```

### 异常表

| 异常 | 条件 |
|---|---|
| `ArgumentException` | `userId <= 0` |
| `HttpRequestException` | 网络请求失败 |
| `TimeoutException` | 超过 30 秒未响应 |

### 多种使用风格

展示声明式和命令式两种用法：

```csharp
// 声明式（Quick Start 风格）
[HttpGet("users/{id}")]
public async Task<IActionResult> GetUser(int id)

// 命令式（完整控制）
var endpoint = app.MapGet("/users/{id}", async (int id) => { ... });
endpoint.WithName("GetUser");
endpoint.WithOpenApi();
```

### 安全覆盖

- 认证/授权要求
- 输入验证逻辑
- 数据敏感性说明
- 安全默认值

## 输出位置

`content/{lang}/{category}/1_API参考/{Feature}/index.md`

每个功能模块对应一个子目录：

```
# 示例：1_核心 的 API 参考
content/zh/1_核心/1_API参考/
├── index.md                    ← 概览
├── 0_工作流/                   ← 工作流系统 API
│   └── index.md
├── 1_MVVM/                     ← MVVM API
│   └── index.md
├── 2_过渡动画/                  ← 过渡动画 API
│   └── index.md
└── ...
```
3. **Extract API signatures** — Method name, parameter types, return type, exception declarations
4. **Record typical input/output** — Extract real invocation examples from test cases
5. **Capture edge cases** — `null`, empty collections, boundary values, error paths
6. **Generate documentation** — API signature → parameter table → return value → example code → notes/caveats

## Document Template

```markdown
## ClassName.MethodName

**Signature:** `ReturnType MethodName(ParamType1 param1, ParamType2 param2)`

| Parameter | Type | Description |
|---|---|---|
| `param1` | `ParamType1` | Description of param1 |
| `param2` | `ParamType2` | Description of param2 |

**Returns:** `ReturnType` — Description of return value

**Example:**

```csharp
// From test: TestClass.Should_X_When_Y
var result = instance.MethodName(value1, value2);
Assert.Equal(expected, result);
```

**Notes:**
- May throw YException when X occurs
- Null values cause Z behavior
```

## 写入后操作

编写 API 文档后：

- [ ] **重新生成导航索引** — 运行树生成脚本（如 `python gen_tree.py`）重建 tree.json
- [ ] **构建项目** — 运行 `dotnet build` 验证新内容正确嵌入
