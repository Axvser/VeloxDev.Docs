# 工作流代理 — 运行一轮对话

用构建好的作用域、提示词与工具集，你可以创建 `ChatClientAgent`（`Microsoft.Agents.AI`）、打开会话并运行消息。工具集**在每次对话调用时重新装配**，因此会话中途加载/卸载的服务器会在下一次调用生效，无需重建代理。

## 1. 创建代理

`IChatClient.AsAIAgent(instructions: prompt)` 用工作流系统提示词包装聊天客户端。工具**不是**在构造时固定的：

```csharp
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;

var agent = chatClient.AsAIAgent(instructions: prompt);   // ChatClientAgent
```

`chatClient` 是来自 `Microsoft.Extensions.AI` 的 `IChatClient` —— 演示用一个 OpenAI 兼容端点构建（`OpenAIClient(...).GetChatClient(model).AsIChatClient()`）；你同样可以使用任何其它 `IChatClient` 实现。

**预期结果：** `agent` 是非空的 `ChatClientAgent`，其 instructions 包含作用域的提示词。

## 2. 打开会话并定义逐调用工具集

```csharp
var baseTools = scope.ProvideTools().ToArray();            // 固定的工作流表面（+ 任意自定义工具）
var session = await agent.CreateSessionAsync();            // AgentSession（对话历史）

var runOptions = new ChatClientAgentRunOptions
{
    ChatOptions = new ChatOptions
    {
        // 基础工作流工具 + 当前已连接服务器的 MCP 工具
        Tools = [.. baseTools, .. mcp.LoadedTools],
    },
};
```

`baseTools` 是固定的工作流表面（`scope.ProvideTools()`，可能再加上自定义工具）。`mcp.LoadedTools` 是当前已连接 MCP 服务器的工具。因为每次调用都重新构建这些选项，代理在对话中途通过 `LoadMcpServers` 加载的服务器会在下一条消息里立刻可见。

**预期结果：** `session` 是全新的 `AgentSession`；`runOptions.ChatOptions.Tools` 包含工作流工具以及每个已加载 MCP 服务器的工具。

## 3. 运行一条消息

```csharp
string message = "List all nodes and report how many are connected.";
var response = await agent.RunAsync(message, session, runOptions);
var text = response.Text;

// 演示在希望逐 token 渲染 UI 时使用的流式变体：
await foreach (var part in agent.RunStreamingAsync(message, session, runOptions))
{
    Console.Write(part.Text);
}
```

**预期结果：** `RunAsync` 返回非空响应，其 `Text` 是模型的回复。模型通过变更工具执行的结构性变更（创建/移动/连接/修补节点）随后可在 `tree` 上看到，并可通过 `tree.UndoCommand` 撤销 —— `MoveNode` 这类单个操作复刻 GUI 拖拽语义、有意不记入撤销历史，而命令支撑的编辑（如 `AddSlotToCollection`）是可撤销的。

## 4. 留意宿主策略门禁

因为工具包在代码里强制执行策略，即使模型尝试被拦截的动作，对话也保持安全：

- 未设置 `WithAllowNodeExecution(true)` 就运行节点业务代码（`ExecuteNode`、`GetNodeResult` 等）会返回引用宿主策略的错误 JSON —— 模型应转而请求宿主启用它。
- 超过 `WithMaxWriteToolCalls` 的变更工具会在执行前返回限额错误。
- 在安全级别 3，模型必须在破坏性变更前调用 `RequestConfirmation`；宿主对话框的 `Deny` 表现为 `status:"denied"` 结果，模型必须据此调整。

**预期结果：** 被拦截或超预算的工具调用不会让整轮对话崩溃；它返回 `status:"error"` JSON，模型读到后作出反应。

## 运行声明

- ⚠️ 仅静态核验。调用模式（`AsAIAgent(instructions:)`、`CreateSessionAsync`、`RunAsync` / `RunStreamingAsync`、`ChatClientAgentRunOptions`）逐字取自 `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`（AskAsync）与 `AgentHelper.cs`；本次文档编写未运行真实模型对话。
