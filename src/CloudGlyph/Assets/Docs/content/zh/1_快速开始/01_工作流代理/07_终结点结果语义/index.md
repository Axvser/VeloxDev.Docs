# 07 · 终结点结果语义

`GetNodeResult`（运行）与 `CompileNodeResult`（计划）使用 `CompileRole.Terminal`。Terminal 角色回答与链角色不同的问题：*“**这个**节点产出什么值？”* —— 不需要 controller 或起始节点。

## 1. 祖先锥

给定一个节点，编译器**从其输入槽向后**追踪所有上游生产者 —— 节点的*祖先锥* —— 并从锥自己的入口前沿驱动运行。图中位置越高的节点锥越大；没有输入的节点锥只有它自己。因此运行成本随锥而变，而不是整棵树。

```text
CompileNodeResult(nodeIndex: 4)   → {"status":"ok","role":"Terminal","graphCount":1}
GetNodeResult(nodeIndex: 4)       → {"status":"ok","role":"Terminal","runStatus":"Completed","targetReached":true,...}
```

来源：`WorkflowLifecycleFidelityTests.CompileNodeResult_SingleNodeTree_ProducesTerminalCompilePlan`、`GetNodeResult_SingleNodeTree_RunsToCompletionWithTerminalRole`。

**预期结果：** 在单节点树上，两者都返回 `role:"Terminal"`；运行返回 `runStatus:"Completed"`、`targetReached:true`、`endedWithError:false`。

## 2. 路由器保持真实

与 Root 角色不同 —— Root 会做静态剪枝，使不在活分支上的下游节点得到 `Order = -1` —— Terminal 角色保持**真实**分支选择。只编译通往目标节点的分支，因此结果与一次走该分支的正常运行完全一致。（一个后果：若同一路由器的多个路由键都能到达该节点，编译无法产出单次前向运行并返回错误。）

## 3. 错误契约

若锥上的路由器在运行时确实选择了**兄弟**分支，目标永远不会被驱动。工具随后返回：

```text
status: "error"
message: "Target node '<Type>' (id <id>) was NOT reached in this run: the router selected a
          branch that does not lead to it, so its condition was not satisfied. No result was produced."
```

且**没有 data**。检查是运行后的 `if (role == CompileRole.Terminal && !context.TargetReached)` —— 使用运行自己的 `TargetReached` 标志，因此绝不会从其他分支的载荷伪造值。

**绝不要把其他分支的最终载荷当作本节点的结果。** 恢复方式：先把路由器指向通往该节点的分支（用 `PatchNodeProperties` 或 `SetEnumSlotCollection` 设置 `CompileMode`/`Selection`），然后重试 —— 或者请求一个位于实际选中分支上的节点。

**预期结果：** 路由器未选中分支上的目标节点返回 `status:"error"`，点名该节点并包含 `"was NOT reached"`，且没有 `data`；重新指向路由器后同一调用返回 `targetReached:true`。

## 4. 该用哪一层

| 你想…… | 使用 |
|---|---|
| 从 controller 运行整个流程 | `RunCompiledWorkflow`（Root） |
| 运行单个节点并读取其值，无需 controller | `GetNodeResult`（Terminal） |
| 只检查计划而不运行 | `CompileWorkflow` / `CompileNodeResult` |
| 持有 / 跟进 / 停止长链运行 | 运行句柄家族（下一页） |

`GetNodeResult` 受 `WithAllowNodeExecution` 闸控；只编译的计划工具不受。没有闸门时，`GetNodeResult` 返回 `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).`

## 运行声明

- ⚠️ **本次修订未运行** —— 2026-10-18 对照当前源码静态核验。Terminal 路径与兄弟分支错误契约读自 `WorkflowAgentToolkit.RunCompiledRoleAsync`；此前的测试记录早于权限模式重构，且从未在分支图上演练该契约。
