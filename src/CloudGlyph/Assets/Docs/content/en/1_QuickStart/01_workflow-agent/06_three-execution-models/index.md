# Workflow Agent — Three Execution Models

The agent can drive your workflow at three distinct levels, and for each level there is a **run** tool (Execution category) plus a **compile-only plan** tool (Query category) that validates the graph without running node code. The run tools all rest on the current engine — `CompilerViewModel.CompileAsync(component, CompileRole)` plus `RuntimeEngine.RunAsync(graph, context)` in `VeloxDev.Core.WorkflowSystem.CompilerEx`. The old `CompilerEngine` / `CompileToAsync` API no longer exists in code.

## 1. The execution-entry table

| Level | Run tool (Execution) | Compile-only plan tool (Query) | Role | What it drives |
|---|---|---|---|---|
| Node | `ExecuteNode` / `ExecuteNodes` | — | — | One node's `ReceiveCommand` (or many), un-compiled |
| Node (broadcast) | `BroadcastNode` / `ReverseBroadcastNode` | — | — | Push downstream / upstream along links, un-compiled |
| Chain (Root) | `RunCompiledWorkflow(startNodeIndex, seed?)` | `CompileWorkflow(startNodeIndex)` | `CompileRole.Root` | The forward chain reachable from a controller |
| Result (Terminal) | `GetNodeResult(nodeIndex, seed?)` | `CompileNodeResult(nodeIndex)` | `CompileRole.Terminal` | One node's value, computed from its ancestor cone |

`CompileRole.Root` compiles the execution graph reachable from the node downstream along `Targets`; `CompileRole.Terminal` walks backward along `Sources` to collect the node's ancestor cone and compiles only what is needed to produce that node.

## 2. Node-level entry points

Node-level tools call the node's commands directly — they never compile, so no `Order`/`CompileContext` is involved:

- `ExecuteNode(nodeIndex, parameter?)` waits for `ReceiveCommand` to actually finish and reports completion (or cancellation/failure) — it does not merely dispatch.
- `ExecuteNodes(nodeIndicesJson, parameter?)` does the same for a JSON array of indices and returns a summary `{status, completed, errors}`.
- `BroadcastNode(nodeIndex, parameter?)` triggers `BroadcastCommand` (downstream dispatch is fire-and-forget); `ReverseBroadcastNode(nodeIndex, parameter?)` triggers `ReverseBroadcastCommand` (upstream `ReceiveCommand`).

The optional `parameter` becomes the node's `ITaskContext.Data`.

**Expected result:** `ExecuteNode` on a node whose command returns normally reports completion; a throwing node reports the failure message instead of hanging the tool call.

## 3. Chain level (Root) — compile then run

`RunCompiledWorkflow(startNodeIndex, seed?)` compiles the sub-graph downstream of a controller and drives it with the execution engine in one step. Its result JSON looks like:

```json
{ "status": "ok", "role": "Root", "runStatus": "Completed",
  "endedWithError": false, "attempts": 1,
  "data": "<the last node's output>", "logs": "[...]" }
```

The optional `seed` becomes the runtime session's `Data` (the first node receives it). To inspect the plan before running, `CompileWorkflow(startNodeIndex)` returns:

```json
{ "status": "ok", "role": "Root", "graphCount": 1,
  "entries": ["Ticker"], "nodeOrders": { "Ticker": 1, "Bias": 2, "Printer": 3 } }
```

## 4. Result level (Terminal) — compute one node's value

`GetNodeResult(nodeIndex, seed?)` reverse-compiles the node's ancestor cone and runs it from the cone's own entry frontier. It behaves exactly like a forward run that reaches the node, and adds a Terminal-only field:

```json
{ "status": "ok", "role": "Terminal", "runStatus": "Completed",
  "endedWithError": false, "attempts": 1,
  "data": "<the result node's output>", "targetReached": true,
  "logs": "[...]" }
```

`CompileNodeResult(nodeIndex)` is the plan-only twin and returns the same shape as `CompileWorkflow` but with `"role": "Terminal"`. Both Terminal tools never fabricate a result — see the next page for the exact `was NOT reached` contract.

**Expected result:** for a single node whose cone is only itself, `GetNodeResult` runs the cone to completion, reports `targetReached: true` and `endedWithError: false` (this exact case is pinned by the lifecycle test `GetNodeResult_SingleNodeTree_RunsToCompletionWithTerminalRole`).

## 5. The engine underneath

The tools are thin wrappers over the same engine the Workflow System Quick Start drives directly:

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var controller = tree.Nodes.First();                       // IWorkflowNodeViewModel from your tree
var seed = "start value";                                  // optional first-node payload
var ct = CancellationToken.None;                            // or a real cancellation token

var compiler = new CompilerViewModel();
var graphs = await compiler.CompileAsync(controller, CompileRole.Root); // or CompileRole.Terminal
var context = new RuntimeContext { Data = seed };
await new RuntimeEngine().RunAsync(graphs[0], context, ct);
```

For a Terminal run the toolkit additionally sets `context.Target = node`, which makes the engine track `context.TargetReached`. Because the engine treats a run as a session with `Data`/`Status`/`Attempt`/logs, all node outputs chain through one shared `RuntimeContext`.

**Expected result:** compiling the same controller twice produces the same graph; running it leaves `context.Data` as the final node's output.

## Run declaration

- ⚠️ Statically verified only. Tool names, parameter lists, roles and JSON shapes are taken from `WorkflowAgentToolkit.cs` (`CompileRoleAsync`, `RunCompiledRoleAsync`) and the CompilerEx sources; nothing here was compiled or executed.
