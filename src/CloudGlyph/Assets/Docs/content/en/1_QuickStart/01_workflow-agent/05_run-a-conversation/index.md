# 05 · Run a Conversation

This is the page where a model is actually involved. Everything before it is offline configuration.

## 1. Build the agent

```csharp
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using VeloxDev.AI.Pipelines;

scope.WithTranscript(transcript);                                 // attach the conversation first

var instructions = scope.ProvideProgressiveContextPrompt();       // static skeleton

var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = instructions },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);                                  // observe both Run and RunStreaming

var session = await agent.CreateSessionAsync();
```

Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` (`ProvideAgent`).

Two rules are load-bearing here:

- **The context provider is the sole source of tools.** The Agent Framework unions the tools a provider contributes with whatever `ChatOptions.Tools` carries, and that union does **not** deduplicate by name. Supplying a tool through both channels sends it to the model twice. So leave `ChatOptions.Tools` empty — the provider is what renders the tool list.
- **Attach the transcript before the agent exists.** The scope composes its pipeline stage chain from the transcript at that moment; the agent is wrapped with the chain.

The convenience overload `AgentClientExtensions.AsAIAgent(this IChatClient chatClient, IReadOnlyList<AIContextProvider> providers, string? instructions = null)` does the same thing without spelling out `ChatClientAgentOptions`.

**Expected result:** `agent` is an `AIAgent` and `session` is created; when `chatClient` is a real model client this performs no network call yet.

## 2. The provider renders per turn

`WorkflowAgentContextProvider` (one of `scope.CreateContextProviders()`) is what makes attaching, switching off or loading something take effect on the **next** turn without rebuilding the agent. It keys its cached render on `scope.ContextKey` (the scope `Version` plus a budget-usage band):

- On an **unchanged** turn it takes no lock and allocates nothing — it returns the very same `AIContext` instance it returned last time.
- On a changed turn it rebuilds the instructions (`BuildDynamicInstructions`) and, if the scope `Version` moved, the tool list (`BuildDynamicTools`).

`CreateContextProviders()` assembles, in a **fixed** order (so the sequence of `With*` calls cannot change how the prompt reads):

1. the compaction provider, if `WithContextCompaction` was called;
2. this scope's own `WorkflowAgentContextProvider`;
3. the skill provider (if `WithSkills`);
4. the MCP provider (if `WithMcps`);
5. the sub-agent roster provider (if `WithSubAgents`);
6. the framework's todo provider (if `WithTodoTracking`) and mode provider (if `WithAgentModes`);
7. one provider per factory registered with `WithContextProvider`.

**Expected result:** calling the provider twice with no configuration change returns the same `AIContext` instance; a `SetToolEnabled(...)` between the two calls makes the second render a new one.

## 3. Optional framework scaffolding

```csharp
scope.WithTodoTracking()                     // the framework's todos_* tools + outstanding-work prompt
     .WithAgentModes(new AgentModeProviderOptions { /* Modes = [...], DefaultMode = "build" */ })
     .WithContextCompaction(maxContextWindowTokens: 128_000, maxOutputTokens: 8_192);
```

- `WithTodoTracking(options?)` puts the framework's todo list into play; the `todos_*` tools come from the framework's own provider and are deliberately **not** wrapped the way the workflow tools are (they neither read nor write the tree).
- `WithAgentModes(options)` adds the `mode_set` / `mode_get` tools. `options` is required — there is no useful default. The property `AgentMode` lets a host switch modes.
- `WithContextCompaction(maxContextWindowTokens, maxOutputTokens)` bounds the conversation: past a threshold the oldest tool results are summarised, and past the next the oldest turns are dropped. **The two numbers are facts about the host's model** — pass the real context window and output cap, not a guess (the demo omits this call for exactly that reason).

**Expected result:** after `WithTodoTracking` the model is offered the framework's `todos_*` tools; those calls do not spend the workflow budget and do not mark the tree dirty.

## 4. Send a turn

```csharp
AgentResponse response = await agent.RunAsync("Add a node of type Demo.ViewModels.NetworkRequest and wire it to the existing controller.", session);
Console.WriteLine(response.Text);
```

**Expected result:** the model answers and, if it decides to act, the transcript gains `ToolCall` entries in order; each tool call runs on the UI thread (if a `SynchronizationContext` was registered), is counted against the budgets, and (for mutations with auto-mark on) dirties the tree.

## 5. The transcript and the pipeline

```csharp
public AgentTranscript Transcript { get; } = new();
```

The pipeline is a chain of `IAgentPipelineStage`s the scope assembles for you:

```text
TextPipeline  →  SharedTools (ToolPipeline)  →  AccountingStage
```

- `TextPipeline` folds `AgentTextDelta` / `AgentReasoningDelta` / turn events into the `AgentTranscript` (`Entries`, `ToMarkdown`, `ToPlainTextLines`). Reasoning is kept beside the answer, wrapped in a fenced block (`AgentMarkdownOptions.ReasoningFence`, default `"thinking"`).
- `SharedTools` (a `ToolPipeline`) marshals onto the UI context and enforces the three call budgets before a call runs.
- `AccountingStage` counts a completed `Succeeded` call against the ledger, raises the callback, and marks the tree dirty when asked. A `Refused` or `Failed` call never ran its body, so it is not counted.

**Expected result:** `Transcript.Entries` after a turn contains the user message, the model's reasoning, its tool calls and the final answer, in order.

## Run declaration

- ⚠️ Not actually run — statically verified only. Running a conversation needs a real `IChatClient` and an API key (the demo reads `API_KEY_DEEPSEEK`), which was not available. The provider caching, pipeline composition and transcript behaviour are read from `WorkflowAgentContextProvider.cs`, `WorkflowAgentScope.cs` and `AgentHelper.cs`; nothing on this page was executed end-to-end.
