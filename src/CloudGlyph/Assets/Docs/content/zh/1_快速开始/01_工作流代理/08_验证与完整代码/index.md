# 工作流代理 — 验证与完整代码

本页先展示该特性如何被验证（演示与自动化测试），再给出整个快速入门一直在构建的那个可运行单文件程序。

## 1. 用演示验证

`Examples/Workflow/*/Demo` 下的每个完整（非 Trimmed）桌面演示（Avalonia、Blazor、Jalium、MAUI、WPF、WinForms、WinUI）都带一个代理聊天面板。它们共享同一个构建器 —— `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` —— 构建作用域的方式与本快速入门完全一致：

- `WithPromptLanguage(English)` + `WithOutputLanguage(Chinese)`、两遍 `WithAutoDiscovery`（`VeloxDev.Core`、`Lib`）、`WithAutoMarkDirty(false)`、`WithMaxToolCalls(200)`、`WithAllowNodeExecution(true)`、`WithSynchronizationContext(SynchronizationContext.Current)`、`WithToolCallCallback`（抛出一个虚拟化刷新事件）、选择/确认处理器，以及由宿主属性驱动的交互安全（默认 3）。
- 通过 `scope.WithTools(...)` 在一个共享 `McpScope` 上注册 MCP 管理工具（`ListMcpServers`、`DescribeMcpServer`、`LoadMcpServers`、`UnloadMcpServer`）；服务器由宿主预注册（远程 `McpServerRunMode.Http` + 本地 `Npx`），并经 `helper.Mcp.LoadAsync` 加载。
- 每个演示视图注册真实对话框 —— WinForms（`Form1.cs` + `Dialogs/AgentConfirmationDialog.cs`、`Dialogs/AgentSelectionDialog.cs`）是其一；`TreeViewModel` 上的聊天命令 `AskAsync` 运行 `agent.RunAsync(message, session, helper.BuildRunOptions())`（或其流式变体）。

要运行其一：把 `API_KEY_DEEPSEEK` 环境变量设为一个 OpenAI 兼容 key，然后启动某个演示工程（例如 `Examples/Workflow/WinForms/Demo`）。

## 2. 用自动化测试验证

- `VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/WorkflowLifecycleFidelityTests.cs` 经 `ProvideTools()` 驱动公开工具并断言生命周期保真：`AddSlotToCollection` 注册槽位且可用同一实例撤销/重做；`ExecuteNode` 报告真实完成；对单节点树 `CompileNodeResult` 产生 Terminal 角色计划（`graphCount == 1`）；`GetNodeResult` 在未 `WithAllowNodeExecution(true)` 时被宿主策略拒绝、允许时运行到完成且 `targetReached == true`；`MoveNode` 复刻 GUI 拖拽语义且不可撤销；`WithSynchronizationContext` 把每个工具调用编组到 UI 上下文。
- `WorkflowSerializationTests.cs` 钉死整树 JSON 往返（`SlotEnumerator` 驱动的枚举节点保住选择器类型与 `CurrentValue`；缩放过的树存储原始/世界坐标，加载后只折叠一次）。
- `DeepZoomSpatialRefreshProbeTests.cs` 是纯数据 GUI 探针，断言仅缩放变更必须同步重建空间提供器索引，使节点在 `Virtualize` 之后仍可见。
- `VeloxDev.Core.Extension.Test/Agent/MCP/McpAgentToolkitTests.cs` 与 `McpRemoteTests.cs` 覆盖四个管理工具与 `McpScope`：Http 传输选项（headers、经 `WithOAuthAuthorizationRedirect` 的 OAuth、超时、`transportMode`）、stdio（`Npx`）的 env/工作目录选项、状态跟踪，以及不抛出地报告错误。
- `VeloxDev.Core.Test/AI/*` 覆盖反射桥（`AgentContextReader`、`AgentLanguages`、`AgentCommandDiscoverer`、`AgentMethodInvoker`、`AgentPropertyAccessor`、`AgentTypeResolver`、`AgentToolCallEventArgs`）。
- 引擎保真（线性链、动态路由器分支选择、扇出负载还原、`IGroupData` 汇合、Terminal 分支、错误处理）由 `VeloxDev.Core.Test/WorkflowSystem/CompilerEx/RuntimeEngineRunTests.cs` 钉死。

## 3. 完整代码

一个自包含的程序：给定一棵运行中的工作流树与一个 `IChatClient`，构建加固过的作用域、生成渐进式提示词、创建代理并运行一轮对话。`ShowSelectionDialog` / `ShowConfirmationDialog` 是设置所示事件参数结果的宿主 UI 对话框。`tree` 是按工作流系统快速入门创建的 `IWorkflowTreeViewModel`；`chatClient` 是任意 `IChatClient`（像演示那样经 `AsIChatClient()` 得到一个 OpenAI 兼容客户端）。

```csharp
using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using VeloxDev.AI;
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

public static class WorkflowAgentQuickStart
{
    public static async Task RunAsync(IWorkflowTreeViewModel tree, IChatClient chatClient)
    {
        var scope = tree.AsAgentScope()
            .WithPromptLanguage(AgentLanguages.English)
            .WithOutputLanguage(AgentLanguages.Chinese)
            .WithAutoDiscovery(assemblyName: "VeloxDev.Core")
            .WithAutoDiscovery(assemblyName: "Lib")
            .WithAutoMarkDirty(false)
            .WithMaxToolCalls(200)
            .WithAllowNodeExecution(true)
            .WithSynchronizationContext(SynchronizationContext.Current)
            .WithInteractionSafety(3)
            .WithSelectionHandler(async args =>
            {
                args.SelectedOption = args.Options.FirstOrDefault();
                await Task.CompletedTask;
            })
            .WithConfirmationHandler(async args =>
            {
                args.Result = AgentConfirmationResult.AllowOnce;
                await Task.CompletedTask;
            });

        var prompt = scope.ProvideProgressiveContextPrompt();
        var baseTools = scope.ProvideTools().ToArray();

        var agent = chatClient.AsAIAgent(instructions: prompt);
        var session = await agent.CreateSessionAsync();
        var runOptions = new ChatClientAgentRunOptions
        {
            ChatOptions = new ChatOptions { Tools = baseTools },
        };

        var response = await agent.RunAsync(
            "List all nodes and report how many are connected.",
            session,
            runOptions);
        if (response is not null)
        {
            Console.WriteLine(response.Text);
        }
    }
}
```

没有 `...` —— 每个标识符都定义于本块、前序页面，或可追溯到真实文件（`tree` 与 `chatClient` 如上所述）。要加入 MCP 服务器工具，请构建 `McpScope`、`LoadAsync(servers)`，再把 `[.. baseTools, .. mcp.LoadedTools]` 合并进 `ChatOptions.Tools`，正如「自定义工具与 MCP」页面所示。

## 4. 运行声明

- ⚠️ 未实际运行 —— 仅静态核验。完整代码程序复刻真实 `AgentHelper.ProvideAgent` 流程（`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`）与 `TreeViewModel.AskAsync` 中 `ChatClientAgent`/`AgentSession` 的调用模式；本次文档编写中未编译或执行。处理器正文是占位的宿主 UI 逻辑；前置条件中的 key/endpoint 未被实际使用。
