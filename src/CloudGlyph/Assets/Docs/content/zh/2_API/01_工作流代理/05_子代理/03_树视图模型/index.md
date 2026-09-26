# 工作流代理 — 子代理：树视图模型

一个作用域持有的名册是**扁平的、按作用域各一份**的 —— 它只装自己直接的孩子，而这正是让一个代理读不到另一个的原因。`SubAgentTreeNodeViewModel` 与 `SubAgentTreeViewModel` 把若干份这样的名册投影成一棵可绑定的树，用每个行所代表的子作用域把它们挂起来。两者都位于 `VeloxDev.AI.SubAgents`（`Agent/SubAgents/SubAgentTreeViewModel.cs`）。

## 类：`SubAgentTreeNodeViewModel`

`public sealed partial class SubAgentTreeNodeViewModel` —— 一个节点：一行，以及那一行派发的子代理的节点。由 MVVM 源生成器（`[VeloxProperty]`）驱动。

| 成员 | 签名 | 备注 |
|---|---|---|
| 构造器 | `SubAgentTreeNodeViewModel(SubAgentStatusViewModel row, SubAgentTreeNodeViewModel? parent)` | 一个被派发子代理的节点。行自己的属性**就是**节点的属性 —— 什么都不复制。`row` 为 null 时抛 `ArgumentNullException`。 |
| `Row` | `SubAgentStatusViewModel? { get; }` | 作用域根节点为 `null`。 |
| `Parent` | `SubAgentTreeNodeViewModel? { get; internal set; }` | 派发它的那个节点，树顶为 `null`。 |
| `Children` | `ObservableCollection<SubAgentTreeNodeViewModel> { get; }` | 它派发的子代理，按派发顺序。 |
| `Id` | `string` | 句柄，转发出来让模板不必穿过 `Row` 去取；作用域根的 id 是固定的 `__scope__`。 |
| `Depth` | `int` | 作用域为 0，它的直接孩子为 1。 |
| `IsScopeRoot` | `bool` | 该节点代表作用域本身，还是代表一个被派发的子代理。 |
| `Title` | `string` | `Row?.Name ?? ScopeTitle`。 |
| `HasChildren` | `bool` | 有没有可以展开的东西。 |
| `TokensUsed` | `long?` | 该节点**自身**那次运行的消耗；作用域根为 `ScopeTokens`。**不是**子树合计 —— 见 `SubtreeTokens`。 |
| `SubtreeTokens` / `SubtreeCallCount` | `long` / `int` | 子树合计，自下而上重算。 |
| `TokensText` | `string` | 该行显示的 token 数字：本节点自身的消耗，或什么也没测到时退回子树合计。 |
| `SubtreeTokensText` | `string` | 子树合计的缩写形式。 |
| `HasTokens` | `bool` | 有可显示的 token 数字，自身的或从子树继承来的。 |
| `ShowSubtreeTokens` | `bool` | `TokensUsed is not null && subtreeTokens > TokensUsed` —— 只有同时有自身实测值和花得更多的后代时才为真。 |
| `Duration` / `DurationText` / `HasDuration` | `TimeSpan?` / `string` / `bool` | 从行转发；作用域没有。 |
| `StateText` / `ShowStateText` | `string` / `bool` | `Completed` 时 `ShowStateText` 为假 —— 灰灯已经说了「完成了」，而那是最常见的状态。排队与运行、取消与失败，才是文字该出现的地方。 |
| `IsRunning` | `bool` | 作用域恒为假。 |
| `CallCount` | `int` | 本节点自身运行的调用数，自身没有时取子树合计。 |
| `HasDroppedRequests` / `DroppedRequestCount` | `bool` / `int` | 从行转发。 |
| `IsExpanded` / `ExpandGlyph` | `bool` / `string` | 默认展开，字形为 `▾` / `▸`；字形跟随状态，而不是被并排设置。 |
| `ScopeTitle` / `ScopeTokens` | `string` / `long?` | 仅作用域根：宿主给这次会话起的名字，以及宿主**自己**那个代理花了多少。`ScopeTokens` 可以在树建好之后再设，所以它的变更钩子重算合计而不只是发通知。 |
| `ToggleExpand()` | `void ToggleExpand()` | 翻转 `IsExpanded`。 |

`NotifyRow()` 宣告本节点的行动了，给那些转发它的成员用。模板应当绑这些成员，而不要穿过 `Row`：作用域根没有行，而这里每个成员都向它转发，所以一条以 `Row` 起头的路径恰好会在面板围着建的那个节点上指向空 —— 而且编译绑定抓不出这种错，因为该路径在类型上仍然合法。

`RecomputeAggregates()` 在子节点填好之后才调用，所以递归在构造上就是自下而上的：孩子的合计在父读它之前已经定稿。

本类型与下面那个类型上有两处「读源码所得」的细节属于*推断所得*、而非测试钉住的：两处构造器的 `ArgumentNullException` 守卫（没有测试用 null 参数构造它们），以及 `ShowStateText` 背后的确切判据 —— `SubAgentTreeViewModelTests` 断言的是计数、字形与节点身份，不是这个旗标。

## 类：`SubAgentTreeViewModel`

`public sealed partial class SubAgentTreeViewModel : IDisposable` —— 以可绑定树的形式呈现的子代理关系图，建在一个子系统之上。

| 成员 | 签名 | 备注 |
|---|---|---|
| 构造器 | `SubAgentTreeViewModel(SubAgentScope scope)` | 在 `scope` 上建树并渲染一次。`scope` 为 null 时抛 `ArgumentNullException`。重建被排到创建本对象的那个线程上。 |
| `ScopeRoot` | `SubAgentTreeNodeViewModel { get; }` | 代表作用域自身的节点：`Tree` 里唯一的那一个顶，也是 `Roots` 里每个节点的父。没有 `Row`。 |
| `Tree` | `ObservableCollection<SubAgentTreeNodeViewModel> { get; }` | 恰好一个元素 —— `ScopeRoot` —— 供只渲染第一层的层级控件使用。 |
| `Roots` | `ObservableCollection<SubAgentTreeNodeViewModel> { get; }` | 该作用域派发的子代理，各一个节点 —— 与 `ScopeRoot.Children` 是同一个集合，不是拷贝。 |
| `TotalCount` | `int` | 树里每一层的子代理总数。作用域自己不计入。 |
| `RunningCount` / `CompletedCount` / `FailedCount` / `CancelledCount` | `int` | 按结局分别计数，于是「被停掉」永远不会被折进「失败」。 |
| `IsEmpty` / `IsIdle` / `HasFailed` | `bool` | 什么都没派 / 没有仍在跑的 / 至少一个失败。 |
| `SubtreeTokens` / `SubtreeTokensText` | `long` / `string` | 树里每一层子代理花掉的 token —— 委托给 `ScopeRoot.SubtreeTokens`。 |
| `TickElapsed()` | `void TickElapsed()` | 刷新每个在跑节点及其行的时长，供显示时钟的面板使用。**库不持有计时器** —— 宿主用它已有的东西（调度器计时器、帧节拍）按它觉得好读的节奏驱动。 |
| `Rebuild()` | `void Rebuild()` | 按作用域当前的样子重建，与所有其他重建串行，所以调用方不必是创建本对象的那条线程。已销毁后是空操作。 |
| `Dispose()` | `void Dispose()` | 退订它订阅过的每个作用域。**不取消任何东西**，且幂等。 |

### 重建语义

它是活的而不是快照式的：树里每个作用域在名册或任一行动了时触发 `SubAgentScope.Changed`，重建被**排**到创建本对象的线程上。重建会被**合并**，所以「孩子启动 + 孩子完成 + 孙代理出现」在同一瞬间只花一趟。`Fill` 对一层做**就地重整** —— 先移除离开的，再插入与移动 —— 而不是清空重建，因为名册在**每一行的每一次属性写入**上都重发一次，清空会把面板的容器每孩子拆装好几遍，并连带丢掉展开状态与选中项。`SubAgentMetricsTests.ARebuild_ReconcilesTheLevelInPlace` 断言重置次数为 0、新增恰好一次、且原来那些节点还是原来那些实例。

重建还被一道内部闸门串行化。本类的全局假设是它们发生在一条线程上，而队列只负责**投递**到那条线程 —— 但当没有可投递的 `SynchronizationContext` 时（无头宿主，以及每一个测试），重建**就在触发变化的那个作用域的线程上内联执行**，于是同一瞬间完成的两个孩子就是两条线程同时进 `Fill`。这不是罕见的交错：这就是一次扇出按构造会发生的事。

`Dispose` 也走那道闸门，因为它是唯一第三处同时改根集合、扁平列表与订阅集合的地方。它把 `Roots` **和计数**一起清掉：计数派生自最后一次重建，而 `Rebuild` 在销毁之后早返回，所以留下来的一个总数永远无法被刷新回一致 —— 它会描述这个面板已经不再持有的孩子，且是永久性的。`AfterDispose_NothingRebuilds` 断言计数与节点一致。

订阅是在**遍历时**顺带登记的，而不是事先：还不存在的孩子无法预先订阅 —— 而 `Dispose` 要退订的正是「访问过的每一个」，否则每多一层孙代理就漏一个 handler。`Dispose_DetachesFromEveryScopeItVisited` 断言的是**投递次数**而不是排空后的结果。

> 源码：`SubAgentTreeViewModel.cs`。测试：`Src/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/` 下的 `SubAgentTreeViewModelTests`、`SubAgentMetricsTests`。Demo 绑定（Avalonia）：`Examples/Workflow/Avalonia/Demo/Views/Workflow/WorkflowView.axaml` 第 264-299 行与 `WorkflowView.axaml.cs` 第 87-105 行。
