# 服务器状态

MCP 状态遵循与技能相同的双视图模式：每个服务器一个可绑定行，以及一个可在渲染提示的线程上安全读取的不可变快照。

## 枚举：McpServerStatus

| 成员 | 含义 |
|---|---|
| `NotStarted` | 已配置但未装载。 |
| `Installing` | 正在安装运行时（本地 npm/pip）。 |
| `Connecting` | 正在启动进程或与远程握手。 |
| `Connected` | 存活；工具可用。 |
| `Error` | 装载失败。 |

## 类：McpServerStatusViewModel

一个服务器作为可绑定行，由 `[VeloxProperty]` 字段生成。

### 生成属性

| 名称 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 服务器名。 |
| `Description` | `string` | 面向操作者的描述。 |
| `RunMode` | `McpServerRunMode` | 启动方式。 |
| `State` | `McpServerStatus` | 原始生命周期状态。 |
| `ToolCount` | `int` | 服务器暴露的工具数。 |
| `Error` | `string?` | `State == Error` 时的失败文本。 |
| `Endpoint` | `string?` | 非本地启动时的远程端点。 |
| `IsEnabled` | `bool` | 服务器工具是否到达智能体。默认 `true`。 |

### 计算成员

| 名称 | 类型 | 说明 |
|---|---|---|
| `IsConnected` | `bool` | `State == Connected`。 |
| `IsActive` | `bool` | `IsConnected && IsEnabled`——工具提供的唯一状态。 |
| `IsInstalling` | `bool` | `State == Installing`。 |
| `IsConnecting` | `bool` | `State == Connecting`。 |
| `IsError` | `bool` | `State == Error`。 |
| `StateText` | `string` | 状态的展示文本。 |

禁用服务器使它保持 `Connected` 且工具已装载，只是不再提供它们。这与卸载不同，卸载会拆掉连接。

## 类：McpServerSummary

一个服务器状态的不可变副本，可从任意线程读取。它携带一行所需的全部信息，因此从快照构建的作用域无需跟踪服务器即可重建行。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 服务器名。 |
| `Description` | `string` | 面向操作者的描述。 |
| `RunMode` | `McpServerRunMode` | 启动模式。 |
| `State` | `McpServerStatus` | 原始生命周期状态。 |
| `StateText` | `string` | 展示文本。 |
| `ToolCount` | `int` | 当前暴露的工具数。 |
| `Error` | `string?` | 装载失败文本。 |
| `Endpoint` | `string?` | 远程端点。 |
| `IsEnabled` | `bool` | 工具是否到达智能体。 |
| `IsActive` | `bool` | 已连接且已打开。 |

## 类：McpStatusViewModel

`McpScope.Status` 持有的全局可绑定状态视图模型。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Servers` | `ObservableCollection<McpServerStatusViewModel>` | 可绑定行，由被跟踪集合生成。 |
| `Snapshot` | `IReadOnlyList<McpServerSummary>` | 不可变副本，在被跟踪服务器变化时于绑定线程重新发布。 |
| `ConnectedCount` | `int` | 已连接服务器数。 |
| `ErrorCount` | `int` | 失败服务器数。 |
| `WorkingCount` | `int` | 正在安装或连接的服务器数。 |
| `IsAllReady` | `bool` | 没有服务器正在安装、连接或失败。 |
| `HasError` | `bool` | 是否至少一个服务器失败。 |
| `Track` | `void Track(McpServerStatusViewModel server)` | 注册一行并订阅其变化。在 UI 线程调用。 |
| `SetLoading` | `void SetLoading(bool loading)` | 设置批量装载标志并刷新聚合。 |
| `Reset` | `void Reset()` | 清空所有服务器状态；重载前调用。 |

提示在智能体调用线程渲染，因此任何非绑定线程都应读 `Snapshot` 而非 `Servers`。

## 示例

```csharp
Console.WriteLine(mcp.Status.IsAllReady);
foreach (var server in mcp.Status.Snapshot)
    Console.WriteLine($"{server.Name} {server.StateText} {server.ToolCount}");
```

## 相关

- [McpScope](../00_MCP作用域/index.md) —— `Status` 的持有者。
- [MCP 工具](../03_MCP工具/index.md) —— 向模型报告这些状态的工具。
