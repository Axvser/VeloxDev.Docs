# 07 · 终结点结果语义

`GetNodeResult`（运行）与 `CompileNodeResult`（计划）使用 `CompileRole.Terminal`。终结点角色回答的是与链角色不同的问题：*「**这个**节点产出什么值？」* —— 且不需要控制器或起始节点。

## 1. 祖先锥

给定一个节点，编译器**从它的输入槽向上游回溯**，找出喂给它的每一个生产者 —— 该节点的*祖先锥* —— 并从锥自身的入口前沿驱动运行。图中位置较高的节点得到较大的锥；没有输入的节点得到仅含自身的锥。因此运行成本随锥而非整棵树伸缩。

```text
CompileNodeResult(nodeIndex: 4)   → {"status":"ok","role":"Terminal","graphCount":1}
GetNodeResult(nodeIndex: 4)       → {"status":"ok","role":"Terminal","runStatus":"Completed","targetReached":true,...}
```

来源：`WorkflowLifecycleFidelityTests.CompileNodeResult_SingleNodeTree_ProducesTerminalCompilePlan`、`GetNodeResult_SingleNodeTree_RunsToCompletionWithTerminalRole`。

**预期结果：** 在单节点树上两者都返回 `role:"Terminal"`；运行返回 `runStatus:"Completed"`、`targetReached:true`、`endedWithError:false`。

## 2. 路由器保持真实

不同于 Root 角色 —— 它静态剪枝，把不在活跃分支上的下游节点标为 `Order = -1` —— 终结点角色保留**真实的**分支选择。只编译通往目标节点的分支，因此结果与一次走该分支的正常运行*完全一致*。（一个后果：若同一个路由器的多个 route key 都抵达该节点，编译无法产出单次前向运行，于是返回错误。）

## 3. 错误契约

若锥上的路由器在运行时实际选择了**兄弟**分支，目标永不被驱动。此时工具返回：

```text
status: "error"
message: "Target node '<Type>' (id <id>) was NOT reached in this run: the router selected a
          branch that does not lead to it, so its condition was not satisfied. No result was produced."
```

且**无**数据。检查发生在运行之后：`if (role == CompileRole.Terminal && !context.TargetReached)` —— 用的是本次运行自己的 `TargetReached` 标志，因此绝不会从另一分支的载荷伪造一个值。

**绝不要把另一分支的最终载荷当成该节点的结果。** 恢复方法：先把路由器指向通往该节点的分支（用 `PatchNodeProperties` 或 `SetEnumSlotCollection` 设置 `CompileMode`/`Selection`）再重试 —— 或者改问一个确实位于被选中分支上的节点。

**预期结果：** 位于路由器未选中分支上的目标节点返回 `status:"error"`，点名该节点并含 `"was NOT reached"`，且没有 `data`；重设路由器后同样的调用返回 `targetReached:true`。

## 4. 用哪一层

| 你想要…… | 用 |
|---|---|
| 从控制器运行整条流 | `RunCompiledWorkflow`（Root） |
| 运行单个节点并读取其值，无需控制器 | `GetNodeResult`（Terminal） |
| 只看计划而不运行任何东西 | `CompileWorkflow` / `CompileNodeResult` |
| 持有 / 跟进 / 停止一次长链运行 | 运行句柄家族（下一页） |

`GetNodeResult` 受 `WithAllowNodeExecution` 闸控；只编译的计划工具不受。没有闸门时 `GetNodeResult` 返回 `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).`

## 运行声明

- ✅ 实际构建并运行 —— 确定性 agent 测试套件（2026-10-01，`已通过! 失败: 0，通过: 387`）经 `WorkflowLifecycleFidelityTests` 覆盖 Terminal 路径。兄弟分支错误契约及其恢复步骤读自 `WorkflowAgentToolkit.RunCompiledRoleAsync`，而套件并未在含分支的图上演练它（它驱动的 demo 图在锥上没有兄弟路由器）。
