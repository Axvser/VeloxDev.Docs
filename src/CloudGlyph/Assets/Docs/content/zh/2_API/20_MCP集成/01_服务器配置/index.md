# 服务器配置

服务器配置说明一个服务器如何启动或到达。它既是 `WithServers` 预注册的对象，也是 `LoadAsync` 装载的对象，还是状态行描述的对象。

## 类：McpServerConfiguration

`VeloxDev.AI.MCP.McpServerConfiguration` 是一个服务器的配置。其属性是生成的 MVVM 属性，可像任何 `[VeloxProperty]` 成员一样绑定与写入。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 服务器键，所有开关与按名装载使用它。 |
| `Description` | `string` | 面向操作者的描述。 |
| `RunMode` | `McpServerRunMode` | 如何到达服务器。 |
| `Package` | `string` | 包名或路径，由 `RunMode` 解释。 |
| `Version` | `string?` | `Npm` 与 `Pip` 的版本标签；`null` 表示 `latest`。 |
| `Arguments` | `string[]` | 传给服务器进程的额外参数。 |
| `Endpoint` | `string?` | `Http` 的远程 URL，如 `https://mcp.example.com/mcp`。连接使用 Streamable HTTP，SSE 回退。 |
| `Options` | `IReadOnlyDictionary<string, object?>?` | 按名称键控的逐服务器选项。未知键在装载时被拒绝。 |

### 识别的选项键

| 键 | 用途 |
|---|---|
| `headers` | HTTP 头，如 `Authorization`。 |
| `oauth` | `clientId`、`clientSecret`、`redirectUri`、`scopes`。 |
| `connectionTimeout` | 秒数，或 `TimeSpan` 字符串。 |
| `transportMode` | `Http` 模式：`AutoDetect`、`StreamableHttp`、`Sse`。 |
| `ownsSession` | `Http`：是否保持 MCP 会话（有状态）。 |
| `env` | stdio 子进程的环境变量。 |
| `workingDirectory` | stdio 子进程的工作目录。 |

`Options` 使用字典而非匿名对象，因为存档格式的世界是封闭的；映射无需反射即可读取。

## 枚举：McpServerRunMode

| 成员 | 启动方式 |
|---|---|
| `Npm` | 安装包，再用 Node 运行。 |
| `Npx` | `npx -y <package> <args>`；不安装。 |
| `Uvx` | `uvx <package> <args>`；隔离的 Python 环境。 |
| `Pip` | 创建 venv、`pip install`，再运行模块。 |
| `Dotnet` | `dotnet <dll> <args>`。 |
| `Exe` | 直接运行 `<mcpRoot>/exe/<Package>`。 |
| `Normal` | 原样运行 `Package`，`Arguments` 逐字传递。 |
| `Http` | 经 Streamable HTTP 连接 `Endpoint`，SSE 回退。 |

本地安装隔离在 `.evn/mcp/{runtime}/` 下。`Normal` 没有安装步骤也没有根前缀，由操作系统解析命令。

## 类：McpConfigurationFile

`VeloxDev.AI.MCP.McpConfigurationFile` 读取 Claude Code 等 MCP 客户端使用的常见 `.mcp.json` 形状。

| 成员 | 签名 | 说明 |
|---|---|---|
| `ServersProperty` | `const string ServersProperty = "mcpServers"` | 文档的服务器映射属性名。 |
| `Load` | `static IReadOnlyList<McpServerConfiguration> Load(string path)` | 读取并解析文件。文件缺失或文档不是服务器映射时抛异常。 |
| `Parse` | `static IReadOnlyList<McpServerConfiguration> Parse(string json)` | 解析 JSON 文本。 |
| `Parse` | `static IReadOnlyList<McpServerConfiguration> Parse(JsonElement root)` | 解析已打开的根元素。 |

支持的字段：`command`、`args`、`env`、`cwd`、`url`、`type`、`headers`、`description`、`disabled`。`command` 条目变成 `Normal` 并保留参数；`url` 条目变成 `Http`；`type: "sse"` 映射到 `Options`。`disabled: true` 条目被跳过。`${VAR}` 与 `${VAR:-default}` 从进程环境展开。

```csharp
var configs = McpConfigurationFile.Load(".mcp.json");
mcp.WithServers(configs.ToArray());
```

## 相关

- [McpScope](../00_MCP作用域/index.md) —— 消费这些配置。
- [服务器状态](../02_服务器状态/index.md) —— 配置装载后如何报告。
