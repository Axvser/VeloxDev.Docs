# 安装准备

## 前置条件

- **支持的目标框架：** `netstandard2.0` 与 `net8.0`，见 `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`。
- **SDK：** .NET SDK 8.0 或更新。仓库的测试工程以 `net10.0` 为目标，因此 .NET 10 是实测配置。
- **包：** `VeloxDev.Core.Extension` 12.3.0（会带上 `VeloxDev.Core` 12.3.0）。
- **Agent Framework：** `Microsoft.Agents.AI` 1.22.0，`Microsoft.Extensions.AI` 10.10.0 或更新。
- **模型端点（仅对话步骤需要）：** 仓库 demo 使用 `Microsoft.Agents.AI.OpenAI` 1.22.0 连接 DeepSeek（`https://api.deepseek.com`），密钥放在环境变量 `API_KEY_DEEPSEEK` 中。任何 `IChatClient` 都能走同一套接线。

## 安装

```powershell
dotnet new console -n WorkflowAgentQuickStart
cd WorkflowAgentQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
dotnet add package Microsoft.Agents.AI.OpenAI --version 1.22.0
```

**预期结果：** `dotnet list package` 中能看到 `VeloxDev.Core.Extension`、`Microsoft.Agents.AI` 与 `Microsoft.Agents.AI.OpenAI`。

## 创建 scope

`AsAgentScope()` 是 `Src/Core/VeloxDev.Core.Extension/AgentEx.cs` 中的扩展方法 `AgentEx.AsAgentScope(this ITreeComponent)`。

```csharp
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope();

Console.WriteLine(ReferenceEquals(scope.Tree, tree)); // True
```

**预期结果：** 输出 `True`。scope 包住这棵树，但不会替换它。

## 配置工具面

```csharp
scope
    .WithAutoDiscovery()                 // 发现生成器编译好的组件上下文
    .WithAllowNodeExecution(false)       // 宿主明确允许之前，执行工具保持拒绝
    .WithMaxToolCalls(120)
    .WithMaxToolResultChars(48 * 1024)
    .WithToolCallCallback(args =>
    {
        Console.WriteLine($"[tool] {args.ToolName} (call #{args.CallCount})");
        return Task.CompletedTask;
    });
```

`WithToolCallCallback` 收到 `AgentToolCallEventArgs`（`ToolName`、`Result`、`CallCount`）。它只在调用**成功**后触发；被拒绝与失败的调用改走 `AgentToolCallCompleted` 事件。

**预期结果：** 链式调用返回同一个 `scope`；`scope.MaxToolCalls` 为 `120`。

## 分清两种控制

有两个容易混淆的独立控制：

| 控制 | 类型 | 决定 |
|---|---|---|
| `WorkflowToolCategory` | 工具面过滤器 | 哪些工具组会送到模型面前 |
| `AgentPermissionMode` | 调用期策略 | 已经送出的工具里，哪些真的能运行 |

只注册 `WorkflowToolCategory.Query` 时，模型根本看不到修改工具；把会话留在 `Plan` 时，模型看得到它们，但调用期会被拒绝。下一页会分别演示这两种情况。

**预期结果：** 对同一个工具，你能分别回答「它是否可见」与「它是否被允许」——两个答案不必一致。
