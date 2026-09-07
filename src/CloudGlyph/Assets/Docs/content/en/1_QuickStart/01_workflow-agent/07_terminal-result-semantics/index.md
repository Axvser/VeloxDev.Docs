# Workflow Agent — Terminal Result Semantics

`GetNodeResult` / `CompileNodeResult` are the agent's way to ask *"what is the value of this one node?"* They differ from a forward root run in one crucial respect: the answer is **never fabricated**. The compile keeps real routing semantics and only compiles the branch that can actually reach the node, and the run reports honestly when that branch was not taken.

## 1. Ancestor-cone compilation keeps real routing

To compute node `X`, the compiler walks **backward along `Sources`** and collects `X`'s ancestor cone, then forward-compiles the cone from its own entry frontier. Routers on the way keep their real `BranchSegment` semantics:

- Only the router branches whose targets lie **inside the cone** are compiled; sibling branches are *absent* from the plan (not present as `Order = -1` stubs).
- At runtime the router still resolves its branch normally (statically from the compile-locked key, or dynamically via `ResolveRouteKey(context)`), and the engine drives only the chosen subgraph.

So the compiled artifact is not a flattened guess — it is the cone's own forward decomposition.

**Expected result:** `CompileNodeResult` on a target that sits behind one branch of a router returns a Terminal plan whose graph contains only the in-cone branch.

## 2. When a sibling branch is selected: `was NOT reached`

Because only the in-cone branch is compiled, a router that actually decides on a **sibling** branch at runtime cannot reach the target. The run then ends before the target and the tool reports the truth:

```json
{ "status": "error", "role": "Terminal",
  "message": "Target node 'BiasNode' (id 2) was NOT reached in this run: the router selected a branch that does not lead to it, so its condition was not satisfied. No result was produced." }
```

The `targetReached` field is emitted **only by Terminal runs**: `true` when the target node was actually driven, `false` when its branch was not taken — the tool never invents a value. (A Root chain run has no target, so it does not report `targetReached`.) This mirrors the engine-level contract: a run's `RuntimeContext` carries an optional `Target`, and the engine sets `TargetReached` only once the matching node is driven.

**Expected result:** requesting a result for a node behind a branch that the router will not select returns `status:"error"` with the `was NOT reached ... No result was produced.` message and no `data`.

## 3. Recovery: switch the branch, then retry

The not-reached outcome is not a dead end. The router's selection is a normal runtime value (for a dynamic router, whatever `ResolveRouteKey` returns from the payload):

1. Inspect the router (for example a `SlotEnumerator`-driven enum selector) and its current selection.
2. Change the selection so it points at the branch that leads to the target node (the agent uses the enum/slot mutation tools, e.g. `SetEnumSlotChannel`).
3. Call `GetNodeResult` again — with the corrected branch the cone compiles and the target is driven, returning `targetReached: true` and the value.

A real router to experiment with is `EnumSelectorNodeViewModel` (`Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`), whose `ResolveRouteKey` picks the branch from the data payload.

**Expected result:** after switching the router to the branch that reaches the target, a retried `GetNodeResult` returns `status:"ok"` with `targetReached: true`.

## 4. Ambiguous cone: more than one branch reaches the target

If **more than one route key of the same router** reaches the target node, there is no single honest answer, and the compile refuses rather than guessing:

```text
CompileAsync(CompileRole.Terminal): the router 'EnumSelectorNodeViewModel' has more than one
branch reaching the terminal node. A single forward run can only take one branch, so this
target cannot be computed; no result is fabricated.
```

This surfaces from the toolkit as a `Compile failed: ...` error. Ask for a node on one specific branch instead.

**Expected result:** `CompileNodeResult` on such a node returns an error explaining that a single forward run can only take one branch; it never fabricates a combined result.

## Run declaration

- ⚠️ Statically verified only. The error strings and `targetReached` contract are quoted from `WorkflowAgentToolkit.cs` and the compiler's `RestrictRouteToCone`; no terminal run was executed in this documentation pass.
