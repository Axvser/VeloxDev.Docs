# Workflow Agent — `AgentEx`

**Signature:** `public static class AgentEx` — `public static WorkflowAgentScope AsAgentScope(this IWorkflowTreeViewModel tree)`.
**Returns:** a new `WorkflowAgentScope` bound to the tree.
**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, line 155.
**Notes:** `AsAIAgent` is *not* defined by VeloxDev — it is the `Microsoft.Extensions.AI` / `Microsoft.Agents.AI` extension on `IChatClient` (`chatClient.AsAIAgent(instructions:, tools:)`), evidenced in the repository root `README.md`.
**Source:** `Src/Core/VeloxDev.Core.Extension/AgentEx.cs`.
