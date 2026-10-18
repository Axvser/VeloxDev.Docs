# 06 · 三种执行模型

agent 可以在三个层级运行 workflow。它们**不是**彼此的替代品 —— 各自回答不同的问题，且每个运行工具旁都有一个只编译的计划工具。

| 层级 | 计划工具 | 运行工具 | 驱动什么 |
|---|---|---|---|
| 节点 | — | `ExecuteNode` / `ExecuteNodes`、`BroadcastNode`、`ReverseBroadcastNode` | 单个节点的 `ReceiveCommand` / 广播命令（非编译） |
| 链（Root） | `CompileWorkflow` | `RunCompiledWorkflow` | 从起始节点可达的整条链 |
| 结果（Terminal） | `CompileNodeResult` | `GetNodeResult` | 单个节点的取值，由其祖先锥得出 |

## 1. 节点层 —— `ExecuteNode` 及其伙伴

```text
ExecuteNode(nodeIndex: 3, parameter: null)
→ {"status":"ok","message":"... completed ..."}
```

在单个节点上运行 `ReceiveCommand` 并**等待**节点真正完成；只有真实完成后才返回 `ok`。`ExecuteNodes` 对 JSON 索引数组（`nodeIndicesJson`）做同样的事，返回 `completed` 与失败项的 `errors` 数组。`BroadcastNode` 运行 `BroadcastCommand`，`ReverseBroadcastNode` 运行 `ReverseBroadcastCommand`（上游 `ReceiveCommand`）；两者都等待自己的命令，尽管下游/上游派发本身是即发即忘。

四者都要求 `WithAllowNodeExecution(true)`；否则返回 `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).` 来源：`WorkflowLifecycleFidelityTests.ExecuteNode_WaitsForCommandCompletion`、`GetNodeResult_WithoutAllowNodeExecution_IsRejectedByPolicy`。

**预期结果：** 在单节点树上，`ExecuteNode(0)` 返回 `status:"ok"`，消息包含 `completed`。

## 2. 链层 —— `RunCompiledWorkflow`

```text
RunCompiledWorkflow(startNodeIndex: 0, seed: "42")
```

编译从起始节点可达的子图（通常是 controller），并通过执行引擎驱动整条链 —— 与示例 **Run** 按钮相同的入口。节点以 `IRuntimeContext` 执行 `ReceiveAsync`（编译步语义：**不**自动广播 —— 下游派发由引擎负责）。`CompileWorkflow(startNodeIndex)` 只做编译并返回计划。

结果形状：

| 字段 | 含义 |
|---|---|
| `role` | `"Root"` |
| `runStatus` | `"Completed"` 或 `"Stopped"` |
| `outcome` | `Completed` / `Cancelled` / `Failed` —— 精确读法，因为 `runStatus` 在失败与取消之间共用 `"Stopped"` |
| `endedWithError` | 节点报错且流程结束时为 `true` |
| `attempts` | 本次运行做了多少次节点尝试 |
| `data` | 运行的最终数据 |
| `failures` | 失败记录（`phase` / `level` / `message` / `attempt` / `order`） |
| `logs` | 运行会话日志 |
| `logFile` | 宿主把日志行写入文件时为绝对路径，否则 `null` |

`RunCompiledWorkflow` 等待结束。若 agent 需要持有、放行或停止一次运行，使用下一页的运行句柄家族。

## 3. 结果层 —— `GetNodeResult`

```text
GetNodeResult(nodeIndex: 4, seed: null)
```

发现节点的**祖先锥**（从输入槽向后追踪的全部上游生产者），并从锥自己的入口前沿驱动它，因此**不需要 controller/起始节点**。锥内的路由器保持*真实*分支选择 —— 只编译通往该节点的分支，结果与一次走该分支的正常运行完全一致。`CompileNodeResult(nodeIndex)` 只做编译。

`GetNodeResult` 在结果形状上增加 `targetReached`（节点确实被驱动时为 `true`）。它的错误契约是下一页的主题。

## 4. 底下的引擎

两个运行工具共用 `RunCompiledRoleAsync`（`WorkflowAgentToolkit.cs`），它做：

```csharp
var graphs = await new CompilerViewModel().CompileAsync(node, role);   // role = Root | Terminal
await new RuntimeEngine().RunAsync(graphs[0], context, ct);
```

命名空间 `VeloxDev.Core.WorkflowSystem.CompilerEx`。`CompileRole.Root` 从起始节点编译下游子图；`CompileRole.Terminal` 反向编译单节点锥并把 `context.Target` 设为该节点。已不存在 `CompilerEngine` / `CompileToAsync`。

`RunCompiledRoleAsync` 通过 `NewSession(seed, target, run)` 构建会话：先应用宿主的 `WithSessionConfiguration`，再只填补仍未设置的部分（`CheckpointStore`、执行闸门、错误汇）。

## 5. 事后读取计划

| 工具 | 签名 | 返回 |
|---|---|---|
| `GetCompileStatus` | `GetCompileStatus()` | 每个编译感知节点的身份（`Order` / `ChainIndex` / `Offset`；`isStopped = Order == -1`），**无需重新编译** |
| `GetExecutionLog` | `GetExecutionLog()` | 树的聚合**直接**（非编译器）执行日志（约定命名的 `ExecutionLog` 属性） |

编译器运行会话日志用运行工具的 `logs` 字段（带序号与 `[Warning]` / `[Error]` 标记）；`GetExecutionLog` 只是直接执行日志。

**预期结果：** `CompileWorkflow(0)` 后，`GetCompileStatus()` 列出 `Order` 非负的已编译节点；起始节点不是 `isStopped`。

## 运行声明

- ⚠️ **本次修订未运行** —— 2026-10-18 对照当前源码静态核验。曾有一次 2026-10-01 的确定性测试记录（387 项）覆盖 `WorkflowLifecycleFidelityTests` 与 `CompiledRunControlTests`，但它早于权限模式重构，不能作为当前证据；该次运行也未对模型发起对话。
