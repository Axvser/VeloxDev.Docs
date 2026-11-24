# 安装准备

## 前置条件

- **支持的目标框架：** `netstandard2.0` 与 `net8.0`，见 `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`。
- **SDK：** .NET SDK 8.0 或更新；测试运行在 .NET 10。
- **包：** `VeloxDev.Core.Extension` 12.3.0。
- **模型：** 派发子代理会运行一段对话，因此真正派发需要可用的 `IChatClient`。只配置子系统并读取名册不需要。

## 安装

```powershell
dotnet new console -n SubAgentsQuickStart
cd SubAgentsQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
dotnet add package Microsoft.Agents.AI.OpenAI --version 1.22.0
```

**预期结果：** `dotnet list package` 中能看到 `VeloxDev.Core.Extension` 与 `Microsoft.Agents.AI.OpenAI`。

## 创建子系统

```csharp
using Microsoft.Extensions.AI;
using VeloxDev.AI.SubAgents;

var subAgents = SubAgentScope.ForClient(chatClient)
    .WithSubAgentDepth(3)      // 根最多向下派发 3 层
    .WithSpawnBudget(40);      // 父级没有设置调用上限时使用
```

`ForClient` 让每个子代理都用宿主的客户端。`ForClientFactory` 按 spawn 携带的 `model` 名逐个挑选客户端：

```csharp
var byModel = SubAgentScope.ForClientFactory(
    model => model switch
    {
        null => chatClient,
        "fast" => fastChatClient,
        _ => throw new NotSupportedException($"Unknown model '{model}'."),
    });
```

工厂抛异常就是拒绝这次 spawn；拒绝会作为子代理的失败回到派发它的智能体。

**预期结果：** `subAgents.MaxDepth` 为 `3`，`subAgents.SpawnBudget` 为 `40`，`subAgents.Snapshot` 为空。

## 在创建 provider 之前挂载

```csharp
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope()
    .WithSynchronizationContext(SynchronizationContext.Current)
    .WithSubAgents(subAgents);

var providers = scope.CreateContextProviders();
```

顺序很重要：`WithSubAgents` 注册子系统的 context provider。如果在 `CreateContextProviders()` 之后才挂，模型一个派发工具都拿不到，子系统无论怎么配置都不可达。

**预期结果：** `scope.SubAgents` 与 `subAgents` 是同一实例，`providers` 中包含子代理 provider。

## 子代理继承什么

什么都不指定的 spawn 会得到父级当前提供的一切：同样的工具、技能与 MCP 服务器，包括继续派发的能力。点名更小集合的 spawn 得到交集——永远不会超过父级，超出部分会被丢弃并在 spawn 结果里回报。

**预期结果：** `AutoEdit` 父级的子代理继承 `AutoEdit`；它不可能以为自己握有父级被拒绝的能力。
