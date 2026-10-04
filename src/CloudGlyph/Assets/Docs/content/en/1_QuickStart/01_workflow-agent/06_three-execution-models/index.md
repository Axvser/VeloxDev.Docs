# 06 · The Three Execution Models

The agent can run a workflow at three levels. They are **not** alternatives to each other — each answers a different question, and each has a compile-only plan tool beside its run tool.

| Level | Plan tool | Run tool | What it drives |
|---|---|---|---|
| Node | — | `ExecuteNode` / `ExecuteNodes`, `BroadcastNode`, `ReverseBroadcastNode` | one node's `ReceiveCommand` / broadcast commands (not compiled) |
| Chain (Root) | `CompileWorkflow` | `RunCompiledWorkflow` | the whole chain reachable from a start node |
| Result (Terminal) | `CompileNodeResult` | `GetNodeResult` | one node's value, from its ancestor cone |

## 1. Node level — `ExecuteNode` and friends

```text
ExecuteNode(nodeIndex: 3, parameter: null)
→ {"status":"ok","message":"... completed ..."}
```

Runs `ReceiveCommand` on one node and **waits** until the node actually completes; returns `ok` only after real completion. `ExecuteNodes` does the same for a JSON array of indices (`nodeIndicesJson`), returning `completed` plus an `errors` array for any that failed. `BroadcastNode` runs `BroadcastCommand` and `ReverseBroadcastNode` runs `ReverseBroadcastCommand` (upstream `ReceiveCommand`); both wait for their own command, though the downstream/upstream dispatch itself is fire-and-forget.

All four require `WithAllowNodeExecution(true)`; without it they return `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).` Source: `WorkflowLifecycleFidelityTests.ExecuteNode_WaitsForCommandCompletion`, `GetNodeResult_WithoutAllowNodeExecution_IsRejectedByPolicy`.

**Expected result:** on a single-node tree, `ExecuteNode(0)` returns `status:"ok"` with a message containing `completed`.

## 2. Chain level — `RunCompiledWorkflow`

```text
RunCompiledWorkflow(startNodeIndex: 0, seed: "42")
```

Compiles the sub-graph reachable from the start node (typically a controller) and drives the whole chain through the execution engine — the same entry the demo's **Run** button uses. Nodes execute their `ReceiveAsync` with an `IRuntimeContext` (compiled-step semantics: **no** auto-broadcast — the engine owns downstream dispatch). `CompileWorkflow(startNodeIndex)` performs the compile only and returns the plan.

The result shape:

| Field | Meaning |
|---|---|
| `role` | `"Root"` |
| `runStatus` | `"Completed"` or `"Stopped"` |
| `outcome` | `Completed` / `Cancelled` / `Failed` — the precise reading, since `runStatus` shares `"Stopped"` between a failure and a cancellation |
| `endedWithError` | `true` when a node reported an error and the flow ended |
| `attempts` | how many node attempts the run made |
| `data` | the run's final data |
| `failures` | the failures as records (`phase` / `level` / `message` / `attempt` / `order`) |
| `logs` | the run-session log |
| `logFile` | an absolute path when the host sent the lines to a file, else `null` |

`RunCompiledWorkflow` waits for the end. For a run the agent must hold, let go or stop, use the run-handle family on the next page.

## 3. Result level — `GetNodeResult`

```text
GetNodeResult(nodeIndex: 4, seed: null)
```

Discovers the node's **ancestor cone** (all upstream producers feeding it, traced backward from its input slots) and drives it from the cone's own entry frontier, so **no controller/start node is needed**. Routers inside the cone keep *real* branch selection — only the branch leading to this node is compiled, so the result exactly matches a normal run that took that branch. `CompileNodeResult(nodeIndex)` performs the compile only.

`GetNodeResult` adds `targetReached` to the result shape (`true` when the node was actually driven). Its error contract is the subject of the next page.

## 4. The engine underneath

Both run tools share `RunCompiledRoleAsync` (`WorkflowAgentToolkit.cs`), which does:

```csharp
var graphs = await new CompilerViewModel().CompileAsync(node, role);   // role = Root | Terminal
await new RuntimeEngine().RunAsync(graphs[0], context, ct);
```

Namespaces `VeloxDev.Core.WorkflowSystem.CompilerEx`. `CompileRole.Root` compiles the downstream sub-graph from a start node; `CompileRole.Terminal` reverse-compiles a single node's cone and sets `context.Target` to that node. There is no `CompilerEngine` / `CompileToAsync` anymore.

`RunCompiledRoleAsync` builds the session through `NewSession(seed, target, run)`, which applies the host's `WithSessionConfiguration`, then fills in only what is still unset (`CheckpointStore`, the execution gate, the error sink).

## 5. Read the plan afterwards

| Tool | Signature | Returns |
|---|---|---|
| `GetCompileStatus` | `GetCompileStatus()` | every compile-aware node's identity (`Order` / `ChainIndex` / `Offset`; `isStopped = Order == -1`) **without recompiling** |
| `GetExecutionLog` | `GetExecutionLog()` | the tree's aggregate **direct** (non-compiler) execution log (a convention-named `ExecutionLog` property) |

Use the run tool's `logs` field for the compiler run-session log (which carries sequence numbers and `[Warning]` / `[Error]` markers); `GetExecutionLog` is the direct-execution log only.

**Expected result:** after `CompileWorkflow(0)`, `GetCompileStatus()` lists the compiled nodes with non-negative `Order`; the start node is not `isStopped`.

## Run declaration

- ✅ Actually built and ran — the deterministic agent test suite was executed on 2026-10-01 (`已通过! 失败: 0，通过: 387`). It covers `WorkflowLifecycleFidelityTests` (`CompileNodeResult_SingleNodeTree_ProducesTerminalCompilePlan`, `GetNodeResult_SingleNodeTree_RunsToCompletionWithTerminalRole`, `GetNodeResult_WithoutAllowNodeExecution_IsRejectedByPolicy`) and `CompiledRunControlTests`, all of which drive the compiler path against the demo graph with a stubbed interpreter. Running a conversation against a model was not part of that run.
