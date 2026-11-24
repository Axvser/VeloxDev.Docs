# 使用

## 列出分类

`WorkflowToolCategory` 是 `VeloxDev.AI.Workflow.Functions` 中的标志枚举。工作流 toolkit 按分类注册工具，`CreateTools` 只返回选中的组。

```csharp
using VeloxDev.AI.Workflow.Functions;

var toolkit = scope.CreateToolkit();
foreach (var tool in toolkit.CreateTools(WorkflowToolCategory.Query))
    Console.WriteLine(tool.Name);
```

**预期结果：** 输出查询类工具名，开头是 `ListNodes`、`GetNodeDetail`、`GetWorkflowSummary`、`FindNodes`、`ValidateWorkflow`、`GetFullTopology`、`CompileWorkflow`、`SerializeWorkflow`、`ListCompiledRuns`。

| 分类 | 代表工具 |
|---|---|
| `Query` | `ListNodes`、`GetNodeDetail`、`GetFullTopology`、`GetTypeSchema`、`ValidateWorkflow`、`CompileWorkflow`、`GetExecutionLog` |
| `Mutation` | `CreateNode`、`DeleteNode`、`CreateSlotOnNode`、`ConnectSlots`、`PatchNodeProperties`、`SetEnumSlotCollection`、`Undo`、`Redo` |
| `Execution` | `ExecuteNode`、`ExecuteNodes`、`RunCompiledWorkflow`、`StartCompiledWorkflow`、`PauseCompiledRun`、`GetCompiledRunStatus` |
| `Command` | `ExecuteCommandOnNode`、`ExecuteCommandById` |
| `Graph` | `SearchForward`、`SearchReverse`、`IsConnected`、`FindPath` |
| `Layout` | `GetLayoutInfo`、`PreviewLayout`、`ArrangeLayout` |
| `Analytics` | `GetNodeStatistics` |
| `State` | `TakeSnapshot`、`GetChangesSinceSnapshot`、`MarkDirty` |
| `Interaction` | `RequestSelection`、`RequestConfirmation`（仅在配置了处理器时出现） |

`Composite` 是保留位，不注册任何工具：每个操作都是一个组件命令，Core 的撤销栈因此永远不会被绕过。

## 关闭单个工具

```csharp
using System.Linq;

scope.WithToolEnabled("DeleteNode", false);

var mutation = scope.CreateToolkit().CreateTools(WorkflowToolCategory.Mutation);
Console.WriteLine(mutation.Any(t => t.Name == "DeleteNode")); // False
```

**预期结果：** 输出 `False`。这个开关能到达所有来源的工具——内置的、自定义的、技能贡献的、MCP 贡献的——因为它在共享的调用包装器里检查，而不只在工作流 toolkit 自己的过滤器里。

## 接上聊天客户端

provider 是工具的唯一来源。智能体的静态指令来自 `ProvideProgressiveContextPrompt()`，每轮的工具面来自 `CreateContextProviders()`。

```csharp
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using OpenAI;
using System.ClientModel;

var apiKey = Environment.GetEnvironmentVariable("API_KEY_DEEPSEEK")
    ?? throw new InvalidOperationException("请先设置 API_KEY_DEEPSEEK。");

var chatClient = new OpenAIClient(
        new ApiKeyCredential(apiKey),
        new OpenAIClientOptions { Endpoint = new Uri("https://api.deepseek.com") })
    .GetChatClient("deepseek-v4-flash")
    .AsIChatClient();

var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);

var session = await agent.CreateSessionAsync();
var response = await agent.RunAsync("列出这张图里的节点索引。", session);
Console.WriteLine(response.Text);
```

**预期结果：** 工具回调打印 `ListNodes`，回答里列出树中的节点索引。

## 验证

1. 运行程序并索要节点列表。回调打印 `[tool] ListNodes (call #1)`，回答包含节点数。
2. 让它把节点移到 `(200, 120)`。默认的 `Auto` 模式会直接执行编辑，`tree.Nodes.Count` 加一。
3. 删除一个槽或调用 `ValidateWorkflow`；回调点名工具，回答反映结果。

拒绝与「工具不存在」是两回事：`Plan` 让工具保持可见，却在调用期拒绝并说明当前模式。这部分行为属于[智能体安全与预算](../../18_智能体安全与预算/index.md)。

## 完整代码

下面的程序列出查询工具、关闭一个修改工具，然后运行一段对话。控制台模板默认开启 `ImplicitUsings`，因此 `System`、`System.Linq` 与 `System.Threading.Tasks` 已在作用域内。

```csharp
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using OpenAI;
using System.ClientModel;
using VeloxDev.AI.Workflow;
using VeloxDev.AI.Workflow.Functions;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope()
    .WithAutoDiscovery()
    .WithMaxToolCalls(120)
    .WithToolCallCallback(args =>
    {
        Console.WriteLine($"[tool] {args.ToolName} (call #{args.CallCount})");
        return Task.CompletedTask;
    });

Console.WriteLine("Query tools:");
foreach (var tool in scope.CreateToolkit().CreateTools(WorkflowToolCategory.Query))
    Console.WriteLine($"  {tool.Name}");

scope.WithToolEnabled("DeleteNode", false);

var apiKey = Environment.GetEnvironmentVariable("API_KEY_DEEPSEEK")
    ?? throw new InvalidOperationException("请先设置 API_KEY_DEEPSEEK。");

var chatClient = new OpenAIClient(
        new ApiKeyCredential(apiKey),
        new OpenAIClientOptions { Endpoint = new Uri("https://api.deepseek.com") })
    .GetChatClient("deepseek-v4-flash")
    .AsIChatClient();

var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);

var session = await agent.CreateSessionAsync();
var response = await agent.RunAsync("列出这张图里的节点索引。", session);
Console.WriteLine(response.Text);
```

## 运行声明

- ⚠️ 未实际运行 —— 仅对照 `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs`、`Agent/Workflow/Functions/WorkflowAgentToolkit.cs`、`Agent/Workflow/Functions/WorkflowToolCategory.cs`，以及 `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` 中的 demo 接线做了静态核对。对话步骤需要可用的模型端点，因此没有记录输出。
