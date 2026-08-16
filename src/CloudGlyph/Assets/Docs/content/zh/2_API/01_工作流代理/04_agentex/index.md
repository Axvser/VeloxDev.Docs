# Workflow Agent — `AgentEx`

**签名：** `public static class AgentEx` —— `public static WorkflowAgentScope AsAgentScope(this IWorkflowTreeViewModel tree)`。
**返回：** 绑定到树的新 `WorkflowAgentScope`。
**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 155 行。
**说明：** `AsAIAgent` **不由** VeloxDev 定义 —— 它是 `Microsoft.Extensions.AI` / `Microsoft.Agents.AI` 在 `IChatClient` 上的扩展（`chatClient.AsAIAgent(instructions:, tools:)`），由仓库根 `README.md` 佐证。
**源码：** `Src/Core/VeloxDev.Core.Extension/AgentEx.cs`。
