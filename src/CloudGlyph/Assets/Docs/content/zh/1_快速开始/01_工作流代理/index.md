# 工作流代理 — 快速入门

## 工作流代理

工作流代理（workflow-agent）特性是 VeloxDev 的 AI 控制层。它把一个运行中的工作流树变成 Agent 可控的表面：

- `tree.AsAgentScope()` 返回流式的 `WorkflowAgentScope` 构建器，收集提示词语言、输出语言、类型发现、交互安全、回调与自定义工具。
- `scope.ProvideProgressiveContextPrompt()` / `ProvideAllContexts()` 生成系统提示词（渐进式披露让提示词保持精简）。
- `scope.ProvideTools()` / `CreateToolkit()` 生成一个 `WorkflowAgentToolkit`，内含约 60 个函数调用型 `AITool`（Microsoft.Extensions.AI），让模型可以检查、变更、执行并布局图。
- `WorkflowStateTracker` 对树做 JSON 快照并报告 `added/removed/modified` 差异，让 Agent 用最少上下文观察变化。
- `McpScope` 加载 Model Context Protocol 服务器（本地 stdio + 远程 HTTP）并把其工具合并进会话。
- `VeloxDev.AI` 的反射工具（`AgentContextAttribute`、`AgentLanguages`、`AgentContextReader`、`AgentCommandDiscoverer`、`AgentMethodInvoker`、`AgentPropertyAccessor`、`AgentTypeResolver`、事件参数类型、`SlotSelectorsAttribute`）支撑这些工具。

### 快速入门

#### 1. 前置条件

- **支持目标**（来自 `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj` 与 `VeloxDev.Core.csproj`）：`netstandard2.0` —— 可用于 .NET Framework 4.6.1+、.NET Core 3.0+ 与 .NET 5+。
- **SDK / 运行时：** 带 Roslyn 4.x（5.0+）的 .NET SDK 以运行源码生成器；WinForms 示例面向 `net10.0-windows` —— *被验证过*的配置，并非要求。
- **包管理器：** NuGet / `dotnet` CLI。
- **必需服务：**
  - 一个运行中的工作流树（`IWorkflowTreeViewModel`），按工作流系统快速入门搭建。
  - 一个 AI 聊天客户端 —— 来自 `Microsoft.Extensions.AI` 的 `IChatClient`（演示通过 `AsIChatClient()` 构建）。
  - 若用 MCP：Node.js / `npx` 运行时（或 Python / dotnet / exe，视 `McpServerRunMode` 而定）以及一个 model-context-protocol 服务器包。


#### 2. 安装 / 添加依赖

```bash
dotnet add package VeloxDev.Core.Extension
```

`VeloxDev.Core`（工作流核心）在 Debug 构建下会传递引入；当只需要核心类型时显式引用：

```bash
dotnet add package VeloxDev.Core
```

**预期结果：**两个包出现在 `.csproj` 中；`dotnet restore` 退出码为 0。`VeloxDev.Core.Extension` 会传递引入 `Microsoft.Extensions.AI`、`Microsoft.Agents.AI`、`ModelContextProtocol`（MCP SDK）、`CliWrap` 与 `Newtonsoft.Json`。

#### 3. 基本设置 / 注册

从一棵树构建 Agent 作用域，并注册 Agent 可操作的组件：

```csharp
var scope = tree.AsAgentScope()                  // tree: IWorkflowTreeViewModel
    .WithPromptLanguage(AgentLanguages.English)  // 提示词/文档的默认语言
    .WithOutputLanguage(AgentLanguages.Chinese)  // LLM 回复必须使用的语言
    .WithAutoDiscovery(assemblyName: "Lib")      // 自动注册工作流组件/枚举/接口/数据
    .WithMaxToolCalls(200)
    .WithInteractionSafety(3)                    // 0 静默、1 谨慎、2 平衡、3 严格
    .WithSelectionHandler(ShowSelectionDialog)   // 启用 RequestSelection 工具
    .WithConfirmationHandler(ShowConfirmationDialog); // 启用 RequestConfirmation 工具
```

`WithAutoDiscovery` 接受 `Assembly` 或简单程序集名（如 `"Lib"`、`"VeloxDev.Core"`）；它会扫描具体工作流组件、`[SlotSelectors]` 引用的枚举、接口类型成员、`[AgentCommandParameter]` 参数类型以及带 `[AgentContext]` 的数据类型。

**预期结果：**`scope` 无异常构建；`scope.ProvideProgressiveContextPrompt()` 返回非空提示词字符串；`scope.ProvideTools()` 返回非空且多于 0 个工具的 `IList<AITool>`。

#### 4. 核心用法（分步）

1. **自动发现。** 对每个包含工作流组件的程序集调用 `WithAutoDiscovery(assembly)` / `WithAutoDiscovery(assemblyName: "...")`。**预期结果：**`ProvideProgressiveContextPrompt()` 会在 "Registered Component Types" 分区中列出你的类型及其 `[AgentContext]` 摘要。

2. **交互安全。** 调用 `WithInteractionSafety(0..3)` —— `0` 静默（不注册任何交互工具，完全自主）、`1` 谨慎（有歧义或批量/破坏性操作时询问）、`2` 平衡（存在多个可行路径或操作涉及 ≥ 2 个节点/连接时询问）、`3` 严格（确认门禁 + 强制走工具交互）。可选地通过 `WithInteractionSafetyPrompt(level, body)` 覆盖 1–3 档的提示词正文。**预期结果：**在第 0 档时 `RequestSelection`/`RequestConfirmation` 不出现于 `ProvideTools()`；在第 1–3 档时**仅当**注册了对应处理器才出现。

3. **选择与确认处理器。** `WithSelectionHandler(Func<AgentSelectionEventArgs, Task>)` 与 `WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task>)` 接通宿主 UI 对话框。选择处理器内设置 `args.SelectedOption`（单选）或 `args.SelectedOptions`/`args.FreeTextResponse`（多选）；确认处理器内设置 `args.Result = AgentConfirmationResult.AllowOnce | AllowAlways | Deny`。**预期结果：**注册了处理器且安全级别 > 0 时，`ProvideTools()` 中恰好包含一个 `RequestSelection` 和一个 `RequestConfirmation`。

4. **创建 Agent。** 把提示词和工具列表交给聊天客户端：

   ```csharp
   var agent = chatClient.AsAIAgent(
       instructions: scope.ProvideProgressiveContextPrompt(),
       tools: scope.ProvideTools());
   ```

   **预期结果：**`agent` 是工具集为工作流工具包的 `IAIAgent`。

5. **运行一轮对话。** 创建会话并运行一条消息。工具通过 `ChatOptions` 逐次传入，使会话中途加载的 MCP 工具自动并入（仓库内演示正是如此）：

   ```csharp
   var session = await agent.CreateSessionAsync();
   var runOptions = new ChatClientAgentRunOptions
   {
       ChatOptions = new ChatOptions { Tools = [.. scope.ProvideTools(), .. mcp.LoadedTools] },
   };
   var response = await agent.RunAsync(message, session, runOptions);
   var text = response.Text;
   ```

   **预期结果：**`RunAsync` 返回 `AgentResponse`；`text` 是模型回复。模型执行的结构性变更（创建/移动/连接/修补节点）随后可在 `tree` 上看到，并可通过 `tree.UndoCommand` 撤销。

6. **加载 MCP 工具。** `new McpScope().WithMcpRoot(".evn/mcp").LoadAsync(configs)` 安装包（npm/pip）并通过 stdio 连接，返回服务器的工具为 `AITool[]`。合并进会话：

   ```csharp
   var mcp = new McpScope().WithMcpRoot(".evn/mcp");
   var mcpTools = await mcp.LoadAsync(
   [
       new McpServerConfiguration
       {
           Name = "Filesystem",
           RunMode = McpServerRunMode.Npx,
           Package = "@modelcontextprotocol/server-filesystem",
           Arguments = [AppContext.BaseDirectory],
       },
   ]);
   var allTools = scope.ProvideTools().Concat(mcpTools).ToArray();
   ```

   **预期结果：**对可达的服务器，`mcpTools` 至少有一个工具；合并后 `allTools` 同时包含工作流工具与服务器工具。注意配置属性名是 `Package`（不是 `NpmPackage`）。

#### 5. 验证

- 运行 WinForms 演示（`Examples/Workflow/WinForms/Demo`）：它打开一个成品图，其聊天面板（`Form1`）让用户用自然语言发指令。演示的 `AgentHelper` 用 `WithAutoDiscovery("VeloxDev.Core")` + `WithAutoDiscovery("Lib")`、`WithAllowNodeExecution(true)`、`WithSynchronizationContext(SynchronizationContext.Current)`、交互安全 3 构建作用域，并通过 `McpAgentToolkit` 注册 MCP 服务器管理工具。
- `Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/WorkflowAgentToolkitTests.cs` 中的自动化测试断言工具调用行为：`MarkDirty` 会把树标记为脏、`WithAutoMarkDirty(true)` 下查询工具从不置脏、`CreateTools(WorkflowToolCategory.Query)` 排除变更/执行工具、已移除的捆绑工具（`AutoLayout`、`BatchExecute`、`CloneNodes`、`CreateAndConfigureNode`）绝不出现、`SetEnumSlotCollection` 不产生幻影撤销条目。
- 反射工具由 `Src/Core/VeloxDev.Core.Test/AI/*` 覆盖（`AgentContextReaderTests`、`AgentLanguagesTests`、`AgentCommandDiscovererTests`、`AgentMethodInvokerTests`、`AgentPropertyAccessorTests`、`AgentTypeResolverTests`、`AgentToolCallEventArgsTests`）。
- MCP 加载由 `Src/Core/VeloxDev.Core.Extension.Test/Agent/MCP/McpAgentToolkitTests.cs` 与 `McpRemoteTests.cs` 覆盖。

#### 6. 完整代码

一个端到端示例：构建作用域、加载 MCP 工具、合并并运行一轮对话。`tree` 是按工作流系统快速入门创建的 `IWorkflowTreeViewModel`（如演示的 `TreeViewModel`）；`chatClient` 是来自 `Microsoft.Extensions.AI` 的 `IChatClient`（如经 `AsIChatClient()` 的 OpenAI 兼容客户端）。`ShowSelectionDialog` / `ShowConfirmationDialog` 是宿主 UI 对话框，设置如下所示的事件参数结果。

```csharp
using Microsoft.Extensions.AI;
using VeloxDev.AI;
using VeloxDev.AI.MCP;
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
        var baseTools = scope.ProvideTools();

        var mcp = new McpScope().WithMcpRoot(".evn/mcp");
        var mcpTools = await mcp.LoadAsync(
        [
            new McpServerConfiguration
            {
                Name = "Filesystem",
                RunMode = McpServerRunMode.Npx,
                Package = "@modelcontextprotocol/server-filesystem",
                Arguments = [AppContext.BaseDirectory],
            },
        ]);

        var allTools = baseTools.Concat(mcpTools).ToArray();
        var agent = chatClient.AsAIAgent(instructions: prompt, tools: allTools);
        var session = await agent.CreateSessionAsync();
        var runOptions = new ChatClientAgentRunOptions
        {
            ChatOptions = new ChatOptions { Tools = allTools },
        };

        var response = await agent.RunAsync(
            "List all nodes and report how many are connected.", session, runOptions);
        Console.WriteLine(response.Text);
    }
}
```

#### 7. 运行声明

- ⚠️ 未实际运行 —— 仅静态验证。上面的示例由仓库内 README、`AgentHelper` 演示与 `WorkflowAgentToolkit` 源码拼装而成；本次文档编写中未编译或执行。处理器正文请当作占位的 UI 逻辑。
