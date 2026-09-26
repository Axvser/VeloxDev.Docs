# Workflow Agent — Sub-Agents: Toolkit & Context Provider

Two public types carry the subsystem to the model: `SubAgentAgentToolkit` is the Agent-facing view of the subsystem (five tools), and `SubAgentAgentContextProvider` is how those tools — plus the prose that explains them — reach an agent invocation. Both live in `VeloxDev.AI.SubAgents` and are implemented in `Agent/SubAgents/`.

## Class: `SubAgentAgentToolkit`

`public sealed class SubAgentAgentToolkit(SubAgentScope scope, WorkflowAgentScope host)` — a primary-constructor class; both arguments are null-checked in the field initialisers, so a null throws `ArgumentNullException` at construction.

| Member | Signature | Notes |
|---|---|---|
| `ToolNames` | `static readonly string[]` | `["SpawnSubAgent", "WaitSubAgents", "GetSubAgentResult", "ListSubAgents", "CancelSubAgent"]`. Exposed so a host composing several tool sources can classify them without repeating the literals; all five are **read-only with respect to the workflow graph**, so the workflow toolkit keeps them out of its mutation budget and out of its dirty marking. |
| `CreateAllTools` | `IList<AITool> CreateAllTools()` | Every tool this toolkit can offer, **ignoring the host's switches**. This is what a host UI enumerates to show the switchable surface. |
| `CreateTools` | `IList<AITool> CreateTools()` | The same set, unwrapped, omitting the tools the host switched off (`host.IsToolEnabled`). |
| `CreateTools` | `IList<AITool> CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | Wrapped in `TrackedAIFunction` so every call is marshalled onto the host's thread, gated against the same budget as every other call, and reported afterwards. Throws `ArgumentNullException` when `tools` is null. **This is what the context provider contributes.** |

### The five tools

All five are asynchronous in shape even where the work is immediate. That is the contract rather than an implementation detail: `SpawnSubAgent` returns a handle and runs the child in the background, so a caller never waits on a child inside a tool call, and a host reading the schema sees dispatch-and-poll rather than call-and-block.

| Tool | Required | Optional | Returns |
|---|---|---|---|
| `SpawnSubAgent` | `task` | `name`, `allowedTools`, `allowedSkills`, `allowedMcpServers`, `maxToolCalls`, `maxReadToolCalls`, `maxWriteToolCalls`, `allowNodeExecution`, `allowedGenericCommands`, `autoMarkDirty`, `notes` | `{status, id, name, depth, maxToolCalls, grantedToolCount, grantedSkillCount, grantedMcpServerCount, dropped[], message}` |
| `WaitSubAgents` | — | `ids`, `timeoutMs` (default 60000) | `{status, timedOut, agents[], message}` |
| `GetSubAgentResult` | `id` | — | `{status, id, name, depth, state, stateText, callCount, maxToolCalls, grantedToolCount, grantedSkillCount, grantedMcpServerCount, dropped[]?, result?, error?}` |
| `ListSubAgents` | — | — | `{status, count, running, agents[]}` (each: `id, name, depth, state, stateText, callCount, task`) |
| `CancelSubAgent` | `id` | — | The same shape as `GetSubAgentResult` |

Failure is a JSON object, never an exception: `{"status":"refused","message":"…"}` for a refused spawn or an unknown handle. `SpawnSubAgent` also refuses a blank `task` **before** anything is created — `SubAgentNarrowingTests.ASpawnWithNoTask_IsRefusedBeforeAnythingIsCreated` asserts no row is left behind.

Per-tool payload details:

- `SpawnSubAgent`'s `dropped` is the list of what the spawn asked for and did not get, one line each, and `message` switches to "Dispatched, but not with everything you asked for — read \"dropped\"" when it is non-empty.
- `WaitSubAgents` truncates each report at 4000 characters and puts the marker **inside the text** as well as in a `truncated` flag, so a model reading the value alone can tell a complete report from a cut one. `GetSubAgentResult` returns the report untruncated. *inferred* — the payload shape is asserted (`SubAgentDispatchTests.ASecondWait_CollectsWhatTheFirstTimedOutOn` reads `result` back verbatim), but the 4000-character limit itself is read from the source and is not covered by a test.
- `ListSubAgents` truncates the task preview at 120 characters; the roster's own prompt line truncates at 100. *inferred* — source-read; no test exercises a task long enough to be cut.

`SubAgentToolSchemaTests` pins the schema the model actually reads: `task` is the **only** required argument of `SpawnSubAgent`; all twelve capability arguments are described; `WaitSubAgents` and `ListSubAgents` require nothing; `GetSubAgentResult` and `CancelSubAgent` require exactly `id`.

## Class: `SubAgentAgentContextProvider`

`public sealed class SubAgentAgentContextProvider : AIContextProvider` — contributes the standing text, the roster, and the five wrapped tools to one agent invocation.

| Member | Signature | Notes |
|---|---|---|
| `SubAgentAgentContextProvider` | `SubAgentAgentContextProvider(SubAgentScope scope, ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | Throws `ArgumentNullException` when `scope` is null. Omit `tools` for standalone use: a thread-only policy is derived from `scope.Parent?.UIContext`. |
| `StateKeys` | `override IReadOnlyList<string> { get; }` | Exactly one key per subsystem instance: `"{nameof(SubAgentAgentContextProvider)}:{scope.InstanceId}"`. |

`ProvideAIContextAsync` renders on the scope's `Version`, so a child finishing reaches the model on the next turn without rebuilding the agent: the render is cached, and only the *rendering* is cached — the instructions are transient per invocation and the tools are version-cached instances, both handed back on every call.

There is **no language dimension**. The subsystem's own text is written once in both languages (headings such as `## 子代理 / Sub-agents`) rather than following the workflow prompt language, because a sub-agent's briefing is read by the model and not by the user.

## The prompt in two halves

`BuildInstructions` concatenates two renders, each answering a different question:

- `BuildPromptContext()` — **standing text**, read by host and child alike. It is built from the tools the host actually offers (`CreateTools()`), so a switched-off tool is not advertised, and it is **empty** when the host offers none of the five. Its load-bearing sentences are pinned as strings by `SubAgentDispatchTests`:
  - the mandate is a rule about *kinds of work* (`must be dispatched to a sub-agent`), never a permission; the escape clause is deliberately narrow (`only when the entire answer is one value read off a single call`) and the old, wider wording is asserted **absent**;
  - the title is asked for where the model reads it every turn (`Title each one with \`name\``), not only in the parameter description;
  - what a spawn hands down is stated where the model reads it (`omit them to hand down the lot`);
  - "it cannot ask **you** anything" — it may still put a question to the user directly, because a child inherits the host's interaction configuration.
- `BuildRosterBlock()` — the **live block**: a `ChildBriefing` for a child (depth, budget, notes, dropped requests, granted skills/servers when narrowed, and whether it may dispatch), then the roster of the model's own children. The roster appears only once there are children (`SubAgentDispatchTests.TheRoster_OnlyAppearsOnceThereAreChildren`).

`ChildBriefing` exists because a child's *instructions* are the host's: `ForClient` writes a fixed preamble, and a host that supplied its own would lose every fact about the spawn. Contributing it per turn, beside the roster, survives either choice — `SubAgentHierarchyTests.AChildIsToldWhatItIs_AndWhatItDidNotGet`.

The roster is also the gate on the child's approval to delegate: `AppendBriefing` says "you cannot dispatch — do the work yourself" at the depth limit, and otherwise states affirmatively that the child **may** dispatch, gated on `MayDispatch` (`host.IsToolEnabled("SpawnSubAgent")`, the same switch `CreateTools()` filters by, so the two cannot disagree). `AChildThatCannotDispatch_IsNotToldItCan` and `AChildDispatchedWithoutAWhitelist_IsToldItMayDispatchToo` pin each half.

> Source: `SubAgentAgentToolkit.cs` lines 31-76 (toolkit), 238-374 (prompt building); `SubAgentAgentContextProvider.cs` lines 24-113. Tests: `SubAgentToolSchemaTests`, `SubAgentDispatchTests` (prompt pins), `SubAgentHierarchyTests` (briefing pins) under `Src/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/`.
