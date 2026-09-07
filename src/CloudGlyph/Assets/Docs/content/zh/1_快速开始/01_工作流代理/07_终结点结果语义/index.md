# 工作流代理 — 终结点结果语义

`GetNodeResult` / `CompileNodeResult` 是代理用来问「这单个节点的值是多少？」的方式。它们与一次前向 Root 运行有一处关键区别：答案**绝不捏造**。编译保留真实的路由语义、只编译确实能到达该节点的分支，运行则会在该分支未被选中时如实报告。

## 1. 祖先锥编译保留真实路由

要计算节点 `X`，编译器沿 `Sources` **反向**收集 `X` 的祖先锥，再从锥自身的入口前沿前向编译。途中的路由器保持它们真实的 `BranchSegment` 语义：

- 只有目标**位于锥内**的路由器分支会被编译；兄弟分支在计划中是*缺失*的（不是作为 `Order = -1` 占位存在）。
- 运行时路由器仍然正常解析分支（静态地由编译锁定的 key 决定，或动态地经 `ResolveRouteKey(context)`），引擎只驱动被选中的子图。

所以编译产物不是扁平化的猜测 —— 它是锥自身的前向分解。

**预期结果：** 对一个位于某路由器某一分支之后的节点调用 `CompileNodeResult`，会返回一张只含锥内分支的 Terminal 计划图。

## 2. 当选中兄弟分支时：`was NOT reached`

因为只编译锥内分支，运行时真正决定走**兄弟**分支的路由器无法到达目标。运行会在目标之前结束，工具如实报告：

```json
{ "status": "error", "role": "Terminal",
  "message": "Target node 'BiasNode' (id 2) was NOT reached in this run: the router selected a branch that does not lead to it, so its condition was not satisfied. No result was produced." }
```

`targetReached` 字段**只由 Terminal 运行**发出：目标节点确实被驱动时为 `true`，其分支未被选中时为 `false` —— 工具从不编造值。（Root 链运行没有目标，所以不报告 `targetReached`。）这与引擎层契约一致：一次运行的 `RuntimeContext` 携带可选 `Target`，引擎只有在匹配节点被驱动时才设置 `TargetReached`。

**预期结果：** 请求一个位于路由器不会选中的分支之后的节点结果，会返回带 `was NOT reached ... No result was produced.` 消息且无 `data` 的 `status:"error"`。

## 3. 恢复：切换分支后重试

未达成的结果不是死路。路由器的选择只是一个普通运行时值（对动态路由器，就是 `ResolveRouteKey` 从负载里返回的东西）：

1. 检查路由器（例如一个由 `SlotEnumerator` 驱动的枚举选择器）及其当前选择。
2. 把选择改为指向通往目标节点的那个分支（代理用枚举/槽位变更工具，例如 `SetEnumSlotChannel`）。
3. 再次调用 `GetNodeResult` —— 修正分支后锥可编译、目标被驱动，返回 `targetReached: true` 与结果。

一个可以拿来实验的真实路由器是 `EnumSelectorNodeViewModel`（`Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`），它的 `ResolveRouteKey` 从数据负载中挑分支。

**预期结果：** 把路由器切到能到达目标的分支后，重试 `GetNodeResult` 返回 `status:"ok"` 且 `targetReached: true`。

## 4. 有歧义的锥：超过一个分支到达目标

如果**同一路由器的多个路由 key**都到达目标节点，就不存在单一诚实的答案，编译器拒绝而非猜测：

```text
CompileAsync(CompileRole.Terminal): the router 'EnumSelectorNodeViewModel' has more than one
branch reaching the terminal node. A single forward run can only take one branch, so this
target cannot be computed; no result is fabricated.
```

这从工具包以 `Compile failed: ...` 错误的形式呈现。请改问某一条具体分支上的节点。

**预期结果：** 对这种节点调用 `CompileNodeResult` 会返回错误，说明一次前向运行只能走一条分支；它绝不捏造组合结果。

## 运行声明

- ⚠️ 仅静态核验。错误字符串与 `targetReached` 契约引自 `WorkflowAgentToolkit.cs` 与编译器的 `RestrictRouteToCone`；本次文档编写未执行任何 Terminal 运行。
