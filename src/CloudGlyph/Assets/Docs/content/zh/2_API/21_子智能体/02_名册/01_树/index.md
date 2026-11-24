# 树

`SubAgentTreeViewModel` 把多个作用域的扁平名册投影成一棵可绑定树。它实时更新且不是快照，也不是第二事实源：每个值都转发到行。

## 类：SubAgentTreeViewModel

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| 构造函数 | `SubAgentTreeViewModel(SubAgentScope scope)` | 在作用域上建树并渲染一次。 |
| `ScopeRoot` | `SubAgentTreeNodeViewModel` | 代表作用域自身的节点；树唯一的顶。 |
| `Roots` | `ObservableCollection<SubAgentTreeNodeViewModel>` | 作用域派出的子代理，每个一个节点。 |
| `TotalCount` | `int` | 每层的每个子代理；作用域自身不计。 |
| `RunningCount` | `int` | 仍在工作。 |
| `CompletedCount` | `int` | 以结果完成。 |
| `FailedCount` | `int` | 失败。 |
| `CancelledCount` | `int` | 被取消。 |
| `IsEmpty` | `bool` | 尚未派出任何子代理。 |
| `IsIdle` | `bool` | 没有仍在运行。 |
| `HasFailed` | `bool` | 至少一个子代理失败。 |
| `SubtreeTokens` | `long` | 每层每个子代理花费的 token。 |
| `SubtreeTokensText` | `string` | 同一总数的展示文本。 |
| `TickElapsed()` | `void TickElapsed()` | 刷新每个运行中节点的已用时间。宿主用自己的计时器驱动。 |
| `Rebuild()` | `void Rebuild()` | 在调用线程上按当前状态重建，与其他重建串行化。 |
| `Dispose()` | `void Dispose()` | 从它观察的每个作用域分离。**子代理继续运行。** |

重建会被合并，因此多个子代理同时变化只付一次代价。节点身份在重建中保留：现有节点被重挂而非替换，因此展开的节点保持展开。

关闭面板不是对面板所示工作做出的决定；应通过作用域或 `CancelSubAgent` 取消。

## 类：SubAgentTreeNodeViewModel

一个节点：一个名册行，以及该行派生的子代理节点。顶部节点代表作用域，没有 `Row`。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| 构造函数 | `SubAgentTreeNodeViewModel(SubAgentStatusViewModel row, SubAgentTreeNodeViewModel? parent)` | 为一个已派发子代理建节点。 |
| `Row` | `SubAgentStatusViewModel?` | 此节点显示的行；作用域根为 `null`。 |
| `Parent` | `SubAgentTreeNodeViewModel?` | 派生此节点的节点，顶为 `null`。 |
| `Children` | `ObservableCollection<SubAgentTreeNodeViewModel>` | 此节点派生的子代理，按派发顺序。 |
| `Id` | `string` | 转发的句柄。 |
| `Depth` | `int` | 作用域为 0，直接子级为 1。 |
| `IsScopeRoot` | `bool` | 此节点是否是作用域自身。 |
| `Title` | `string` | spawn 给任务的名称，顶部为作用域自身名称。 |
| `HasChildren` | `bool` | 是否有可展开内容。 |
| `TokensUsed` | `long?` | 此节点自身花费，非其子树。 |
| `SubtreeTokensText` | `string` | 子树总数，缩写。 |
| `HasTokens` | `bool` | 是否有 token 数字，自身或继承。 |
| `TokensText` | `string` | 行显示的数字：自身花费，未测量时为子树总数。 |
| `ShowSubtreeTokens` | `bool` | 仅当节点既有测量花费又有花费更多的后代时为真。 |
| `Duration` | `TimeSpan?` | 此节点自身运行时间，或 `null`。 |
| `DurationText` | `string` | 已用时间文本；无则为空。 |
| `HasDuration` | `bool` | 是否有已用时间可显示。 |
| `StateText` | `string` | 行的状态文本；作用域为空。 |
| `ShowStateText` | `bool` | 状态是否值得打印在指示灯旁。 |
| `IsRunning` | `bool` | 此节点自身运行是否进行；作用域恒为 false。 |
| `CallCount` | `int` | 此节点自身运行的调用数，或没有自身时其子树。 |
| `HasDroppedRequests` | `bool` | 此节点的 spawn 是否请求了未获得的内容。 |
| `DroppedRequestCount` | `int` | 被拒绝的请求数。 |
| `ToggleExpand()` | `void ToggleExpand()` | 显示或隐藏此节点的子级。 |

## 示例

```csharp
using VeloxDev.AI.SubAgents;

using var roster = new SubAgentTreeViewModel(subAgents);
Console.WriteLine($"idle: {roster.IsIdle}, total: {roster.TotalCount}");
```

## 相关

- [摘要与行](../00_摘要与行/index.md) —— 此树转发的行。
- [SubAgentScope](../../00_子智能体作用域/index.md) —— 它观察的名册。
