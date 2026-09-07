# 工作流代理 — 三种执行模型

代理可以在三个不同的层级驱动你的工作流，并且每一层都同时有**运行**工具（Execution 分类）与**仅编译计划**工具（Query 分类，只校验图、不运行节点代码）。这些运行工具都建立在现行引擎之上 —— `VeloxDev.Core.WorkflowSystem.CompilerEx` 中的 `CompilerViewModel.CompileAsync(component, CompileRole)` 加 `RuntimeEngine.RunAsync(graph, context)`。代码里已没有旧的 `CompilerEngine` / `CompileToAsync` API。

## 1. 执行入口对照表

| 层级 | 运行工具（Execution） | 仅编译计划工具（Query） | 角色 | 驱动什么 |
|---|---|---|---|---|
| 节点 | `ExecuteNode` / `ExecuteNodes` | — | — | 单节点（或多节点）的 `ReceiveCommand`，不编译 |
| 节点（广播） | `BroadcastNode` / `ReverseBroadcastNode` | — | — | 沿连接向下游 / 向上游推送，不编译 |
| 链级（Root） | `RunCompiledWorkflow(startNodeIndex, seed?)` | `CompileWorkflow(startNodeIndex)` | `CompileRole.Root` | 从控制器可达的前向链 |
| 结果级（Terminal） | `GetNodeResult(nodeIndex, seed?)` | `CompileNodeResult(nodeIndex)` | `CompileRole.Terminal` | 某个节点的值，从其祖先锥计算而来 |

`CompileRole.Root` 沿 `Targets` 向下游编译该节点可达的执行图；`CompileRole.Terminal` 沿 `Sources` 反向收集节点的祖先锥，只编译生成该节点所需的内容。

## 2. 节点级入口

节点级工具直接调用节点的命令 —— 从不编译，因此不涉及 `Order`/`CompileContext`：

- `ExecuteNode(nodeIndex, parameter?)` 会等待 `ReceiveCommand` 真正完成并报告完成（或取消/失败）—— 不只是派发。
- `ExecuteNodes(nodeIndicesJson, parameter?)` 对一组 JSON 索引做同样的事，返回汇总 `{status, completed, errors}`。
- `BroadcastNode(nodeIndex, parameter?)` 触发 `BroadcastCommand`（下游派发是即发即忘）；`ReverseBroadcastNode(nodeIndex, parameter?)` 触发 `ReverseBroadcastCommand`（上游 `ReceiveCommand`）。

可选的 `parameter` 会成为节点的 `ITaskContext.Data`。

**预期结果：** 对命令正常返回的节点调用 `ExecuteNode` 会报告完成；抛异常的节点返回失败消息，而不是挂起工具调用。

## 3. 链级（Root）—— 先编译后运行

`RunCompiledWorkflow(startNodeIndex, seed?)` 一步完成：编译某控制器下游的子图，再用执行引擎驱动它。其返回 JSON 形如：

```json
{ "status": "ok", "role": "Root", "runStatus": "Completed",
  "endedWithError": false, "attempts": 1,
  "data": "<最后一个节点的输出>", "logs": "[...]" }
```

可选的 `seed` 会成为运行时会话的 `Data`（第一个节点收到它）。想先查看计划，`CompileWorkflow(startNodeIndex)` 返回：

```json
{ "status": "ok", "role": "Root", "graphCount": 1,
  "entries": ["Ticker"], "nodeOrders": { "Ticker": 1, "Bias": 2, "Printer": 3 } }
```

## 4. 结果级（Terminal）—— 计算单个节点的值

`GetNodeResult(nodeIndex, seed?)` 反向编译节点的祖先锥，并从锥自身的入口前沿运行它。它的行为与到达该节点的正常前向运行完全一致，只是多带一个仅 Terminal 的字段：

```json
{ "status": "ok", "role": "Terminal", "runStatus": "Completed",
  "endedWithError": false, "attempts": 1,
  "data": "<结果节点自身的输出>", "targetReached": true,
  "logs": "[...]" }
```

`CompileNodeResult(nodeIndex)` 是仅计划的孪生，返回与 `CompileWorkflow` 相同的形状，只是 `"role": "Terminal"`。两个 Terminal 工具都绝不捏造结果 —— 确切的 `was NOT reached` 契约见下一页。

**预期结果：** 对一棵锥只有自身的单节点树，`GetNodeResult` 会把锥运行到完成，报告 `targetReached: true` 与 `endedWithError: false`（这一确切场景由生命周期测试 `GetNodeResult_SingleNodeTree_RunsToCompletionWithTerminalRole` 钉死）。

## 5. 其下的引擎

这些工具是同一引擎的薄包装 —— 工作流系统快速入门直接驱动它：

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var controller = tree.Nodes.First();                       // 来自你的树的 IWorkflowNodeViewModel
var seed = "start value";                                  // 可选的起始节点负载
var ct = CancellationToken.None;                           // 或真实的取消令牌

var compiler = new CompilerViewModel();
var graphs = await compiler.CompileAsync(controller, CompileRole.Root); // 或 CompileRole.Terminal
var context = new RuntimeContext { Data = seed };
await new RuntimeEngine().RunAsync(graphs[0], context, ct);
```

做 Terminal 运行时，工具包还会设置 `context.Target = node`，让引擎跟踪 `context.TargetReached`。因为引擎把一次运行视作一个带 `Data`/`Status`/`Attempt`/日志的会话，所有节点输出都会经由同一个共享 `RuntimeContext` 串联。

**预期结果：** 对同一控制器编译两次得到同一张图；运行后 `context.Data` 是最后一个节点的输出。

## 运行声明

- ⚠️ 仅静态核验。工具名、参数列表、角色与 JSON 形状取自 `WorkflowAgentToolkit.cs`（`CompileRoleAsync`、`RunCompiledRoleAsync`）与 CompilerEx 源码；本页内容未编译或执行。
