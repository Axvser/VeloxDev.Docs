# 07 · Terminal Result Semantics

`GetNodeResult` (run) and `CompileNodeResult` (plan) use `CompileRole.Terminal`. The terminal role answers a different question from the chain role: *"what value does **this** node produce?"* — with no controller or start node required.

## 1. The ancestor cone

Given a node, the compiler traces **backward from its input slots** to find every upstream producer feeding it — the node's *ancestor cone* — and drives the run from the cone's own entry frontier. A node high in the graph gets a large cone; a node with no inputs gets a cone of just itself. The run cost therefore scales with the cone, not the whole tree.

```text
CompileNodeResult(nodeIndex: 4)   → {"status":"ok","role":"Terminal","graphCount":1}
GetNodeResult(nodeIndex: 4)       → {"status":"ok","role":"Terminal","runStatus":"Completed","targetReached":true,...}
```

Source: `WorkflowLifecycleFidelityTests.CompileNodeResult_SingleNodeTree_ProducesTerminalCompilePlan`, `GetNodeResult_SingleNodeTree_RunsToCompletionWithTerminalRole`.

**Expected result:** on a single-node tree, both return `role:"Terminal"`; the run returns `runStatus:"Completed"`, `targetReached:true`, `endedWithError:false`.

## 2. Routers stay real

Unlike the Root role — which prunes statically, giving a downstream node on no live branch `Order = -1` — the Terminal role keeps **real** branch selection. Only the branch leading to the target node is compiled, so the result *exactly matches* a normal run that took that branch. (A consequence: if more than one route key of the same router reaches the node, compilation cannot produce a single forward run and returns an error.)

## 3. The error contract

If a router on the cone actually selects a **sibling** branch at runtime, the target is never driven. The tool then returns:

```text
status: "error"
message: "Target node '<Type>' (id <id>) was NOT reached in this run: the router selected a
          branch that does not lead to it, so its condition was not satisfied. No result was produced."
```

with **no data**. The check is `if (role == CompileRole.Terminal && !context.TargetReached)` after the run — the run's own `TargetReached` flag, so no value is ever fabricated from another branch's payload.

**Never treat another branch's final payload as this node's result.** To recover: point the router at the branch leading to the node first (`PatchNodeProperties` or `SetEnumSlotCollection` to set `CompileMode`/`Selection`), then retry — or ask for a node that sits on the actually-selected branch.

**Expected result:** a target node on a branch the router did not select yields `status:"error"` naming the node and `"was NOT reached"`, and no `data`; retargeting the router makes the same call return `targetReached:true`.

## 4. Which level to use

| You want to… | Use |
|---|---|
| run the whole flow from its controller | `RunCompiledWorkflow` (Root) |
| run one node and read its value, without a controller | `GetNodeResult` (Terminal) |
| inspect the plan without running anything | `CompileWorkflow` / `CompileNodeResult` |
| hold / follow / stop a long chain run | the run-handle family (next page) |

`GetNodeResult` is gated by `WithAllowNodeExecution`; the compile-only plan tools are not. Without the gate, `GetNodeResult` returns `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).`

## Run declaration

- ✅ Actually built and ran — the deterministic agent test suite (2026-10-01, `已通过! 失败: 0，通过: 387`) covers the Terminal path through `WorkflowLifecycleFidelityTests`. The sibling-branch error contract and its recovery steps are read from `WorkflowAgentToolkit.RunCompiledRoleAsync`, which the suite does not exercise on a branching graph (the demo graphs it drives have no sibling router on a cone).
