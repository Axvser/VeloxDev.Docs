# 工作流代理 — 入口点：`AgentEx`

把 `WorkflowAgentScope` 绑定到一棵工作流树的唯一入口。命名空间 `VeloxDev.AI.Workflow`；源 `Src/Core/VeloxDev.Core.Extension/AgentEx.cs`。

## AgentEx

`public static class AgentEx`

| 成员 | 签名 | 说明 |
|---|---|---|
| `AsAgentScope` | `WorkflowAgentScope AsAgentScope(this IWorkflowTreeViewModel tree)` | 创建绑定到该树的新 `WorkflowAgentScope`。唯一入口点——没有树就无法使用该作用域。 |

**示例** — `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 155 行：

```csharp
using VeloxDev.AI.Workflow;

var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)
    .WithAutoDiscovery(assemblyName: "Lib")
    .WithAllowNodeExecution(true)
    .WithMaxToolCalls(200);
```

配置完成后，宿主构造工具集与上下文提示词，交给某个 AI 聊天客户端：

```csharp
var contextPrompt = scope.ProvideProgressiveContextPrompt();   // 或 scope.ProvideAllContexts()
var tools = scope.ProvideTools();                              // 全部工具（所有类别）

// 'tools' 也可喂给 Microsoft.Extensions.AI 的 ChatOptions.Tools，或——
// 如 Demo 所示——经 Microsoft.Agents.AI 挂在聊天客户端上：
var agent = chatClient.AsAIAgent(instructions: contextPrompt);
```

> **`AsAIAgent` 并非由 VeloxDev 定义。** 它是 `Microsoft.Agents.AI` 对 `IChatClient` 的扩展方法（`chatClient.AsAIAgent(instructions: ..., tools: ...)`），证据见 `AgentHelper.ProvideAgent`（第 223 行）。VeloxDev 贡献作用域（`AsAgentScope`）、工具（`ProvideTools`）与上下文提示词（`ProvideProgressiveContextPrompt` / `ProvideAllContexts`）；Agent 会话本身由 `Microsoft.Agents.AI` 基于 `Microsoft.Extensions.AI` 托管。

完整链路——作用域构造、MCP 工具注册、上下文提示词与运行选项——见 `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` 的 `AgentHelper.ProvideAgent`。
