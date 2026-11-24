# 安装准备

## 前置条件

- **支持的目标框架：** `netstandard2.0` 与 `net8.0`，见 `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`。
- **SDK：** .NET SDK 8.0 或更新；仓库测试运行在 .NET 10。
- **包：** `VeloxDev.Core.Extension` 12.3.0。
- **策略本身不需要模型。** 评估一次调用是纯内存决策；只有实时智能体才需要聊天客户端。

## 安装

```powershell
dotnet new console -n AgentSafetyQuickStart
cd AgentSafetyQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
```

**预期结果：** `dotnet list package` 中能看到 `VeloxDev.Core.Extension`。

## 建立第一条策略

`AgentPermissionPolicy` 不可变；每次 `With*` 都返回新策略，因此读取方在一次调用全程持有的是一份一致的规则集。

```csharp
using VeloxDev.AI.Safety;

var policy = AgentPermissionPolicy.For(AgentPermissionMode.AutoEdit)
    .WithRule(new AgentPermissionRule(PermissionDecision.Ask, "DeleteNode"))
    .WithRule(new AgentPermissionRule(PermissionDecision.Deny, "category:Curate"));

Console.WriteLine(policy.Mode);       // AutoEdit
Console.WriteLine(policy.Rules.Count); // 2
```

**预期结果：** 输出 `AutoEdit` 和 `2`。原策略不变；每次调用都产生了新策略。

## 评估一次调用

```csharp
var call = new ToolInvocation(
    Name: "DeleteNode",
    Category: AgentActionCategory.Edit,
    Source: null,
    Arguments: new Dictionary<string, object?>());

Console.WriteLine(policy.Evaluate(call)); // Ask
```

`ToolInvocation` 携带工具名、分类、来源（MCP 工具为 `mcp:<server>`，其余为 `null`）以及模型提供的参数。之所以带参数，是因为有些策略关心的是**这次调用会做什么**，而不只是工具名——从本地包添加 MCP 服务器会安装软件，而 HTTP 端点不会。

**预期结果：** 输出 `Ask`。规则命中了工具名，覆盖了模式对 `Edit` 的 `Allow`。

## 把策略接到 scope

```csharp
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope()
    .WithPermissionMode(AgentPermissionMode.AutoEdit)
    .WithPermissionRule(PermissionDecision.Ask, "DeleteNode", "DeleteSlot", "DisconnectSlots")
    .WithMaxToolCalls(200)
    .WithMaxReadToolCalls(150)
    .WithMaxWriteToolCalls(50);
```

`WithPermissionRule` 接收一个决策和一到多个模式。`WithPermissionMode` 只用于构造期；`SetPermissionMode` 是运行期开关。

**预期结果：** 调用 `scope.SetPermissionMode(AgentPermissionMode.Plan)` 返回 `true`，下一次工具调用按 `Plan` 判定。
