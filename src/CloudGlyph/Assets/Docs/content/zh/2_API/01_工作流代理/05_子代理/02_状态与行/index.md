# 工作流代理 — 子代理：状态与名册行

一个枚举与两个类描述被派发的孩子处在哪、以及它被给了什么。它们刻意成对：`SubAgentStatusViewModel` 是活在名册线程上的可绑定行，`SubAgentSummary` 是别处读的那份不可变副本。三者都位于 `VeloxDev.AI.SubAgents`（`Agent/SubAgents/SubAgentStatus.cs`、`.../SubAgentStatusViewModel.cs`）。

## 枚举：`SubAgentState`

| 值 | 含义 |
|---|---|
| `Queued` | 已受理，但它的后台运行尚未开始。 |
| `Running` | 正在后台运行。 |
| `Completed` | 已结束并产生了结果。 |
| `Failed` | 以抛异常结束。 |
| `Cancelled` | 被请求停止 —— 被宿主、被它的父、或因为整棵树正在被销毁。 |

`Cancelled` 刻意自成一档，而不是 `Failed` 的一种口味：被宿主或父停掉的孩子并没有出错，而一个把它涂成红色的面板会教用户怀疑那个本来工作正常的控件。`SubAgentDispatchTests.CancellingAChild_ReadsAsCancelled_NotAsFailed` 与 `SubAgentTreeViewModelTests.AStoppedChild_IsNotCountedAsAFailedOne` 钉住这条。

## 类：`SubAgentSummary`

`public sealed class SubAgentSummary` —— 一个子代理状态的不可变副本，可以从任意线程安全读取。与 `McpServerSummary` 是同一套安排：行视图模型绑在 UI 线程上、无法在别处枚举，而一次 agent 调用与一次面板重建都需要从宿主不控制的线程读名册。

| 属性 | 类型 | 备注 |
|---|---|---|
| `Id` | `string` | spawn 返回的句柄，也是其他每个工具接受的参数。 |
| `Name` | `string` | 任务的展示标题 —— spawn 要求的那个，或一个编号占位。它是标题不是标识符：它的读者是看面板的人。 |
| `ParentId` | `string?` | 派发它的那个子代理的 id；宿主自己作用域的孩子为 `null`。父子关系**全部**就在这里：名册是扁平的，树是它的投影。 |
| `Depth` | `int` | 根作用域的孩子为 1，孙代理为 2。 |
| `Task` | `string` | spawn 被要求完成的任务。 |
| `State` | `SubAgentState` | 运行到了哪一步。 |
| `StateText` | `string` | 本地化状态文字，与 `SubAgentStatusViewModel.StateText` 一致。 |
| `Result` | `string?` | 完成后孩子给出的答复。 |
| `Error` | `string?` | 失败原因，或 `null`。 |
| `CallCount` | `int` | 孩子**以及它派发的一切**做了多少次工具调用。 |
| `MaxToolCalls` | `int?` | spawn 时授予的上限，或 `null` 表示无。 |
| `TokensUsed` | `long?` | 孩子**自身**各次运行的 token 合计，提供器未上报时为 `null`。父的总量是整棵树的求和，只有树算得出来 —— 见 `SubAgentTreeNodeViewModel.SubtreeTokens`。 |
| `InputTokens` / `OutputTokens` | `long?` | 提供器拆分上报时 `TokensUsed` 的两半。 |
| `StartedAt` / `FinishedAt` | `DateTimeOffset?` | 这次运行的跨度。 |
| `GrantedToolCount` / `GrantedSkillCount` / `GrantedMcpServerCount` | `int` | 每种能力实际给了孩子多少。零个技能同时也是「孩子根本没有技能源」时报的数。 |
| `DroppedRequests` | `IReadOnlyList<string>` | spawn 要了却没拿到的，逐行一条。它被带进摘要而不只留在 spawn 自己的回复里，因为「面板显示一个能力悄悄比它要的少的孩子」正是这份上报要防的那件事。 |

派生成员：`IsRunning`（状态为 `Queued` 或 `Running`）、`IsFinished`（与它刻意成对，免得消费者自己取反、并在新增状态时取反取错）、`HasError`、`HasResult`、`HasTokens`、`Duration`。

其中三个存在的意义是把「没测过」与「零」分开：

- `HasTokens` 即 `TokensUsed is not null`。对一个完全不上报用量的提供器来说，`false` 才是常态 —— 面板该什么都不显示，而不是显示一个它没测过的 0。`SubAgentMetricsTests.AProviderThatReportsNothing_IsNotAZero` 钉住这条。
- `HasError` / `HasResult` 是**测试而不是与 `null` 比较**，因为成功孩子的 `Error` 与 `Result` 带着该行的默认值空字符串 —— 那是任何消费者都不该需要知道的区别。
- `Duration` 是 `(FinishedAt ?? DateTimeOffset.Now) - StartedAt`，下限为 0。孩子还在跑时它是对着时钟算的，所以重复读同一份摘要会读到更大的跨度 —— 而 `Snapshot` 不会仅仅因为时间流逝就重发。读它，不要缓存它。

## 类：`SubAgentStatusViewModel`

`public sealed partial class SubAgentStatusViewModel` —— 一个被派发的子代理作为可绑定的行，由 MVVM 源生成器（`[VeloxProperty]`）驱动。它写在名册被编组到的那个线程上，由活在同一个线程上的树面板读取。

| 构造器 | 签名 | 备注 |
|---|---|---|
| | `internal SubAgentStatusViewModel(string id, string name, string? parentId, int depth, string task)` | **internal** —— 行由名册创建，宿主从不自己建。 |

| 属性 | 类型 | 备注 |
|---|---|---|
| `Id` / `ParentId` / `Depth` | `string` / `string?` / `int` | 只读，构造时定下。 |
| `Transcript` | `AgentTranscript? { get; internal set; }` | 孩子自己的对话，等它的作用域有了之后。持有而不是复制：第二份 transcript 就是第二个事实源。 |
| `Name` | `string` | 任务标题。 |
| `Task` | `string` | 任务正文。 |
| `State` | `SubAgentState` | 写它会连带通知 `StateText`、`IsRunning`、`IsFinished`。 |
| `Result` / `Error` / `Notes` | `string` | 默认 `""`，绝不为 null。 |
| `CallCount` | `int` | 在名册渲染前与等待返回前，从孩子的账本刷新。 |
| `MaxToolCalls` | `int?` | 被授予的上限。 |
| `StartedAt` / `FinishedAt` | `DateTimeOffset?` | 两者都会通知 `Duration` / `DurationText`，因为一个被就地重跑的行会让新的开始与旧的结束并存。 |
| `TokensUsed` / `InputTokens` / `OutputTokens` | `long?` | token 数字，**只在成功结束**的分支写入。 |
| `GrantedTools` / `GrantedSkills` / `GrantedMcpServers` / `DroppedRequests` | `ObservableCollection<string>` | spawn 时填好并**永不改写** —— 改写一个在跑的孩子被授予了什么，就是对其历史的撒谎。 |

派生成员：`StateText`（`排队中` / `运行中` / `已完成` / `失败` / `已取消` / `未知`）、`IsRunning`、`IsFinished`、`HasError`、`HasResult`、`HasDroppedRequests`、`GrantedSummary`（为空时 `无工具`，否则把被授予的工具名用 `、` 连接）、`Duration`、`DurationText`（`N秒` / `N分N秒` / `N小时N分`）、`HasTokens`、`TokensText`（低于 1000 给准确值，之后是 `N.Nk`，再之后是 `N.NNM`）。

| 方法 | 签名 | 备注 |
|---|---|---|
| `NotifyElapsed` | `void NotifyElapsed()` | 告诉已绑定的面板 `Duration` / `DurationText` 动了。由驱动时钟的一方调用 —— 现成的调用者是 `SubAgentTreeViewModel.TickElapsed`。**库自己不持有计时器**：会跳的面板与会活的进程寿命不同，在这里起一个计时器对两者都不干净。 |

## 这些字段是在哪里写的

名册在三处写一行，其中两处的顺序是承载语义的：

- spawn 时：`StartedAt` **先于** `State`，绝不反过来。`State` 是可绑定属性，赋值即发布该行 —— 在那个通知上读取的消费者否则会看到一个正在运行却没有开始时间的孩子。
- 结束时：载荷（`Result` / `Error` / token 数字）**先于** `State`，理由相同。比它宣告的东西先到的信号，是对它所属于那一行的谎言。
- 被取消或抛异常时，token 数字留 `null` 而不是写 0：那两条路径本该测量的 response 已经不存在，而 `HasTokens` 正是用来让「没测过」与「花了 0」在界面上不是一件事。

> 源码：`SubAgentStatus.cs`（枚举 + 摘要）、`SubAgentStatusViewModel.cs`（行），以及 `SubAgentScope.cs` 第 781-839 行（`RunAsync` / `Finish`）。测试：`Src/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/` 下的 `SubAgentMetricsTests`、`SubAgentDispatchTests`、`SubAgentCapabilityGrantTests`。
