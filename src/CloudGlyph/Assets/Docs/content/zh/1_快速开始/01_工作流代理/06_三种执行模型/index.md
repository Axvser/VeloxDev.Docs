# 06 · 三种执行模型

agent 可以在三个层级运行工作流。它们**并非**互相替代 —— 各答一个问题，且每个运行工具旁都有一个只编译的计划工具。

| 层级 | 计划工具 | 运行工具 | 驱动什么 |
|---|---|---|---|
| 节点 | — | `ExecuteNode` / `ExecuteNodes`、`BroadcastNode`、`ReverseBroadcastNode` | 单个节点的 `ReceiveCommand` / 广播命令（非编译） |
| 链（Root） | `CompileWorkflow` | `RunCompiledWorkflow` | 从起始节点可达的整条链 |
| 结果（Terminal） | `CompileNodeResult` | `GetNodeResult` | 单个节点的取值，来自其祖先锥 |

## 1. 节点层 —— `ExecuteNode` 及同类

```text
ExecuteNode(nodeIndex: 3, parameter: null)
→ {"status":"ok","message":"... completed ..."}
```

在单个节点上运行 `ReceiveCommand` 并**等待**该节点真正完成；只有真正完成后才返回 `ok`。`ExecuteNodes` 对一维索引 JSON 数组（`nodeIndicesJson`）做同样的事，返回 `completed` 以及失败项的 `errors` 数组。`BroadcastNode` 运行 `BroadcastCommand`，`ReverseBroadcastNode` 运行 `ReverseBroadcastCommand`（上游 `ReceiveCommand`）；两者都等待各自的命令，尽管下游/上游派发本身是发后即忘。

这四个都需要 `WithAllowNodeExecution(true)`；没有它时返回 `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).` 来源：`WorkflowLifecycleFidelityTests.ExecuteNode_WaitsForCommandCompletion`、`GetNodeResult_WithoutAllowNodeExecution_IsRejectedByPolicy`。

**预期结果：** 在单节点树上，`ExecuteNode(0)` 返回 `status:"ok"`，消息含 `completed`。

## 2. 链层 —— `RunCompiledWorkflow`

```text
RunCompiledWorkflow(startNodeIndex: 0, seed: "42")
```

编译从起始节点（通常是控制器）可达的子图，并通过执行引擎驱动整条链 —— 与 demo 的 **Run** 按钮所用入口相同。节点以 `IRuntimeContext` 执行其 `ReceiveAsync`（编译步语义：**不**自动广播 —— 引擎负责下游派发）。`CompileWorkflow(startNodeIndex)` 只做编译并返回计划。

结果形状：

| 字段 | 含义 |
|---|---|
| `role` | `"Root"` |
| `runStatus` | `"Completed"` 或 `"Stopped"` |
| `outcome` | `Completed` / `Cancelled` / `Failed` —— 精确读法，因为 `runStatus` 在失败与取消之间共用 `"Stopped"` |
| `endedWithError` | 某节点报告错误且流程终止时为 `true` |
| `attempts` | 本次运行做过的节点尝试数 |
| `data` | 本次运行的最终数据 |
| `failures` | 失败记录（`phase` / `level` / `message` / `attempt` / `order`） |
| `logs` | 运行会话日志 |
| `logFile` | 当宿主把日志行写入文件时是绝对路径，否则 `null` |

`RunCompiledWorkflow` 等待到结束。若需要 agent 持有、放开或停止一次运行，请用下一页的运行句柄家族。

## 3. 结果层 —— `GetNodeResult`

```text
GetNodeResult(nodeIndex: 4, seed: null)
```

发现该节点的**祖先锥**（从它的输入槽向上游回溯的全部生产者），并从锥自身的入口前沿驱动它，因此**不需要**控制器/起始节点。锥内的路由器保留*真实的*分支选择 —— 只编译通往该节点的分支，故结果与一次走该分支的正常运行完全一致。`CompileNodeResult(nodeIndex)` 只做编译。

`GetNodeResult` 在结果形状中增加 `targetReached`（节点确实被驱动时为 `true`）。它的错误契约是下一页的主题。

## 4. 底层引擎

两个运行工具共用 `RunCompiledRoleAsync`（`WorkflowAgentToolkit.cs`），它做：

```csharp
var graphs = await new CompilerViewModel().CompileAsync(node, role);   // role = Root | Terminal
await new RuntimeEngine().RunAsync(graphs[0], context, ct);
```

命名空间 `VeloxDev.Core.WorkflowSystem.CompilerEx`。`CompileRole.Root` 从起始节点编译下游子图；`CompileRole.Terminal` 反向编译单个节点的锥，并把 `context.Target` 设为该节点。不再有 `CompilerEngine` / `CompileToAsync`。

`RunCompiledRoleAsync` 经 `NewSession(seed, target, run)` 构建会话，它先应用宿主的 `WithSessionConfiguration`，然后只填补仍未设置的部分（`CheckpointStore`、执行门、错误汇）。

## 5. 事后读取计划

| 工具 | 签名 | 返回 |
|---|---|---|
| `GetCompileStatus` | `GetCompileStatus()` | 每个编译感知节点的编译身份（`Order` / `ChainIndex` / `Offset`；`isStopped = Order == -1`），**无需重新编译** |
| `GetExecutionLog` | `GetExecutionLog()` | 树的聚合**直接**（非编译器）执行日志（一个约定命名的 `ExecutionLog` 属性） |

编译器运行会话日志（带序号与 `[Warning]` / `[Error]` 标记）请用运行工具的 `logs` 字段；`GetExecutionLog` 只是直接执行日志。

**预期结果：** `CompileWorkflow(0)` 后，`GetCompileStatus()` 列出已编译节点且 `Order` 非负；起始节点不是 `isStopped`。

## 运行声明

- ✅ 实际构建并运行 —— 2026-10-01 执行了确定性 agent 测试套件（`已通过! 失败: 0，通过: 387`）。它覆盖 `WorkflowLifecycleFidelityTests`（`CompileNodeResult_SingleNodeTree_ProducesTerminalCompilePlan`、`GetNodeResult_SingleNodeTree_RunsToCompletionWithTerminalRole`、`GetNodeResult_WithoutAllowNodeExecution_IsRejectedByPolicy`）与 `CompiledRunControlTests`，这些都在带桩解释器的 demo 图上驱动编译器路径。该运行不包含对模型的对话。
