# Workflow Agent — Run a Conversation

With a built scope, a prompt and a tool set you can create a `ChatClientAgent` (`Microsoft.Agents.AI`), open a session and run messages. The tool set is **re-assembled per conversation call**, so servers loaded or unloaded mid-session take effect on the next call without rebuilding the agent.

## 1. Create the agent

`IChatClient.AsAIAgent(instructions: prompt)` wraps the chat client with the workflow system prompt. Tools are *not* fixed at construction time:

```csharp
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;

var agent = chatClient.AsAIAgent(instructions: prompt);   // ChatClientAgent
```

The `chatClient` is an `IChatClient` from `Microsoft.Extensions.AI` — the demo builds one from an OpenAI-compatible endpoint (`OpenAIClient(...).GetChatClient(model).AsIChatClient()`); you may equally use any other `IChatClient` implementation.

**Expected result:** `agent` is a non-null `ChatClientAgent` whose instructions contain the scope's prompt.

## 2. Open a session and define the per-call tool set

```csharp
var baseTools = scope.ProvideTools().ToArray();            // fixed workflow surface (+ any custom tools)
var session = await agent.CreateSessionAsync();            // AgentSession (conversation history)

var runOptions = new ChatClientAgentRunOptions
{
    ChatOptions = new ChatOptions
    {
        // base workflow tools + the MCP tools of the servers connected right now
        Tools = [.. baseTools, .. mcp.LoadedTools],
    },
};
```

`baseTools` is the fixed workflow surface (`scope.ProvideTools()` possibly plus custom tools). `mcp.LoadedTools` are the tools of currently connected MCP servers. Because the options are built fresh for every call, an agent that loads a server through `LoadMcpServers` mid-conversation sees its tools on the very next message.

**Expected result:** `session` is a fresh `AgentSession`; `runOptions.ChatOptions.Tools` contains the workflow tools plus every loaded MCP server's tools.

## 3. Run a message

```csharp
string message = "List all nodes and report how many are connected.";
var response = await agent.RunAsync(message, session, runOptions);
var text = response.Text;

// Streaming variant used by the demo when you want token-by-token UI:
await foreach (var part in agent.RunStreamingAsync(message, session, runOptions))
{
    Console.Write(part.Text);
}
```

**Expected result:** `RunAsync` returns a non-null response whose `Text` is the model's reply. Structural mutations the model performed through mutation tools (create/move/connect/patch nodes) are visible on `tree` afterwards and are undoable via `tree.UndoCommand` — single operations such as `MoveNode` replay GUI drag semantics and are intentionally not recorded in undo history, while command-backed edits (e.g. `AddSlotToCollection`) are.

## 4. Watch for the host-policy gates

Because the toolkit enforces policy in code, the conversation stays safe even if the model tries a blocked action:

- Running node business code (`ExecuteNode`, `GetNodeResult`, …) without `WithAllowNodeExecution(true)` returns an error JSON citing the host policy — the model should then ask the host to enable it.
- A mutation tool that exceeds `WithMaxWriteToolCalls` returns a limit error before executing.
- At safety level 3 the model must call `RequestConfirmation` before destructive changes; the host dialog's `Deny` surfaces as a `status:"denied"` result and the model must adapt.

**Expected result:** a blocked or over-budget tool call does not throw the whole conversation; it returns a `status:"error"` JSON that the model reads and reacts to.

## Run declaration

- ⚠️ Statically verified only. The call pattern (`AsAIAgent(instructions:)`, `CreateSessionAsync`, `RunAsync` / `RunStreamingAsync`, `ChatClientAgentRunOptions`) is taken verbatim from `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs` (AskAsync) and `AgentHelper.cs`; no live model conversation was run in this documentation pass.
