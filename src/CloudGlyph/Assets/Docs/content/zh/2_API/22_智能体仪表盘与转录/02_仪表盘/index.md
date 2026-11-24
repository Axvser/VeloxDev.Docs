# 仪表盘

`VeloxDev.AI.Dashboard.AgentDashboardViewModel` 是一个 `WorkflowAgentScope` 上的宿主面板：智能体当前能做什么、各部分有多忙，以及每个成员一个开关。每行都是投影，绝不是第二事实源。

## 类：AgentDashboardViewModel

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Create` | `static AgentDashboardViewModel Create(WorkflowAgentScope scope)` | 在作用域上建面板。作用域无需预先配置；之后的 `With*` 调用经 `Changed` 到达面板。 |
| `SystemTools` | `ObservableCollection<ToolMemberViewModel>` | 工作流内置工具加开发者注册工具。 |
| `SkillTools` | `ObservableCollection<ToolMemberViewModel>` | 四个技能管理工具。 |
| `McpServers` | `ObservableCollection<McpServerMemberViewModel>` | 每个已配置服务器一行，可展开到其工具。 |
| `Skills` | `ObservableCollection<SkillMemberViewModel>` | 每个已发现技能。 |
| `SubAgents` | `ObservableCollection<SubAgentStatusViewModel>` | 本会话派出的子代理（子系统挂载时）。 |
| `SystemToolSummary` | `string` | 已打开工具数 / 已提供工具数。 |
| `SkillSummary` | `string` | 已打开技能数 / 已发现技能数。 |
| `McpSummary` | `string` | 已连接服务器数 / 已配置服务器数。 |
| `SubAgentSummary` | `string` | 仍在运行的子代理数 / 已派发子代理数。 |
| `McpStatusText` | `string` | 存活/失败拆分，按各服务器的互斥状态计数。 |
| `CanReloadMcp` | `bool` | 没有服务器正在连接，因此重载不会与在途连接冲突。 |
| `ReloadAllServersAsync()` | `Task ReloadAllServersAsync()` | 重连宿主注册的每个服务器。 |
| `CallSummary` | `string` | 已连接、已关闭与回退到秒表的计数。 |
| `Rebuild()` | `void Rebuild()` | 从作用域重读每个成员。公开以便宿主直接改作用域后强制刷新。 |
| `Dispose()` | `void Dispose()` | 从作用域分离。视图消失时调用。 |

面板捕获构造时的 `SynchronizationContext` 并把每个作用域驱动的更新编组到它。没有上下文时完全同步，这使它无需调度器即可测试。`Changed` 在每次配置性 `With*` 调用时触发——仅 `WithAutoDiscovery` 就为每个发现类型触发一次——因此重建被合并为一次投递。

## 类：AgentMemberViewModel

一个可开关行的抽象基类：工具、MCP 服务器、MCP 服务器的工具或技能。

### 生成属性

| 名称 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 显示名。 |
| `Description` | `string` | 描述。 |
| `IsEnabled` | `bool` | 成员是否被提供。设置它调用 `ApplyToScope`。 |
| `StateText` | `string` | 状态文本。 |
| `Note` | `string` | 成员已打开但仍被阻塞的原因。 |
| `CallCount` | `int` | 本会话调用数。 |
| `LastCalledText` | `string` | 上次调用时间文本。 |

### 计算与受保护成员

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `IsOff` | `bool` | `!IsEnabled`。 |
| `IsReachable` | `bool` | `IsEnabled && Note.Length == 0`——「已打开但被宿主策略阻塞」是真实状态。 |
| `HasBeenCalled` | `bool` | `CallCount > 0`。 |
| `ActivityText` | `string` | 调用数的显示文本。 |
| `ApplyToScope` | `protected abstract void ApplyToScope(bool enabled)` | 把宿主开关推入所属作用域。由每种行类型实现。 |

行不得直接写作用域的可绑定标志（如 `SkillStatusViewModel.IsEnabled`）：那会绕过作用域的 `Version` 推进，而缓存提示会继续提供宿主以为已关闭的文本。行的 `ApplyToScope` 改经作用域路由。

## 行类型

| 类型 | 额外成员 |
|---|---|
| `ToolMemberViewModel` | 无；开关存放在共享工具策略上。 |
| `SkillMemberViewModel` | `HasResources`。 |
| `McpServerMemberViewModel` | `HasError`、`IsFailedState`、`ToggleExpand()`、`CanUnload`、`CanReload`、`UnloadAsync()`、`ReloadAsync()`。 |
| `McpToolMemberViewModel` | 无；关闭它时服务器仍提供其他工具。 |

`McpServerMemberViewModel` 刻意同时提供开关与卸载：开关把服务器工具从工具集去掉但连接保持（即时可逆），而 `UnloadAsync` 拆掉进程或传输，下次要重新付出代价。`ReloadAsync` 用注册的配置再次连接。

## 示例

```csharp
using VeloxDev.AI.Dashboard;

using var dashboard = AgentDashboardViewModel.Create(scope);
Console.WriteLine(dashboard.SystemToolSummary);
Console.WriteLine(dashboard.SkillSummary);
Console.WriteLine(dashboard.McpSummary);
Console.WriteLine(dashboard.SubAgentSummary);
```

## 相关

- [转录](../00_转录/index.md) —— 面板旁的对话。
- [MCP 状态](../../20_MCP集成/02_服务器状态/index.md) —— demo 实际绑定的视图模型。
- [子智能体名册](../../21_子智能体/02_名册/00_摘要与行/index.md) —— `SubAgents` 持有的行。
