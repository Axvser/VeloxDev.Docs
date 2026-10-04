# 工作流系统 — 检查点

运行位置的对象形态：`ExecutionCheckpoint`、保存它的内存存储，以及让会话能力在并行组内依然有效的内部扇出门面。

源码：`Runtime/Model/ExecutionCheckpoints.cs`、`Runtime/Model/BranchRuntimeContext.cs`。

---

## `ExecutionCheckpoint`

**签名：** `public sealed class ExecutionCheckpoint`

运行的位置：它已经驱动了什么、那些节点产出了什么，以及足够带它继续下去的运行自身状态。当配置了 `IExecutionCheckpointStore` 时，由 `RuntimeEngine.RunAsync` 在每个节点成功后写入，并作为 `resumeFrom` 参数交还给它。

##### 属性

| 名称 | 类型 | 说明 |
|---|---|---|
| `Attempt` | `int` | 取得这份快照时运行所在的趟 —— `IRuntimeContext.Attempt`。 |
| `ActiveRedirectTarget` | `int?` | 那一趟正在使用的重定向目标，如果有。 |
| `Data` | `object?` | 快照时刻的链式载荷。`IGroupData` 会以按节点键归档的普通 `Dictionary<string, object?>` 存储。 |
| `Outputs` | `Dictionary<string, object?>` | 每个已完成节点产出了什么，按它的检查点键归档。 |
| `Shape` | `List<string>` | 图里的节点，按驱动顺序 —— 恢复时用来对照自身指纹。 |
| `Types` | `List<string>` | `Shape` 背后各节点的**类型**，顺序相同。本成员存在之前写下的检查点这里为空，于是重键会退化成只数节点。 |

##### 方法

#### `ExecutionCheckpoint.Rekey`

**签名：** `public static ExecutionCheckpoint Rekey(ExecutionCheckpoint checkpoint, CompiledGraph target)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `checkpoint` | `ExecutionCheckpoint` | 写下的那份位置。 |
| `target` | `CompiledGraph` | 要把它适配到的那张图。 |

**返回：** `ExecutionCheckpoint` —— 一份以 `target` 的身份归档的新检查点。输入保持不动。

**异常：**

| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `checkpoint` 为 `null`。 |
| `InvalidOperationException` | 两张图不是同一结构 —— 节点数不同，或（在 `Types` 已写入时）某个位置的节点类型不同。 |

**说明：**

- **它为什么存在。** 检查点按 `IWorkflowIdentifiable.RuntimeId` 归档，而从序列化回来的图全是新 id —— 所以对它恢复会被 `RunAsync` 拒绝。拒绝是对的：那确实是不同的节点对象。`Rekey` 是宿主的显式选择，它说的是*我知道它们不同，映射在这里* —— 按位置映射，因为遍历顺序是同一结构永远共享的那一样东西。
- **它检查的是结构而不是身份**：同样的节点数、同样的驱动顺序下同样的节点类型。这能抓住另一张图；它抓不住一张形状相同、但部件被改名成恰好对得上的其它类型的图。两**代**图之间的迁移是宿主自己写的事。
- 检查点自身的形状不可能被重键改变：`Shape` 变成 `target` 的键，`Types` 变成 `target` 的类型名。按节点键归档的载荷字典会随之重键。

### 检查点里的节点身份

节点带 `IWorkflowIdentifiable.RuntimeId` 时引擎按它归档，否则按 `"{类型名}#{序号}"`。要记住的后果：经过序列化往返的图**所有 `RuntimeId` 都是新的**，所以它的指纹对不上、对它恢复会被拒绝 —— 这正是想要的，因为那些确实是不同的节点对象。`ExecutionCheckpoint.Rekey` 是显式说「不是这样」的方式。

### `Shape` 与被拒绝的恢复

`RunAsync` 在**碰会话之前**就把 `Shape` 与图自身的节点键比对。不符时抛 `InvalidOperationException` 并放着会话不管：`Status` 仍是 `"Idle"`，`IsRunning` 是 `false`。由 `ExecutionCheckpointTests.ACheckpointTakenOverAnotherGraph_IsRefused_AndTheSessionIsLeftAlone` 钉住，并在随库实现上复现：

```text
[7] refused on a serialized copy: The checkpoint does not belong to this graph status=Idle
```

**文件存储的异步注意事项：** 检查点是纯 JSON，而 JSON 只有一种整数类型。进去的 `int` 回来变成 `long`，`float` 变成 `double`，无论 `TypeNameHandling` 怎么设 —— 所以一个用 `int` 匹配载荷的节点在经由文件恢复之后匹配不上。保留对象图原样的存储（`InMemoryCheckpointStore`）没有这个缺口。

---

## `InMemoryCheckpointStore`

**签名：** `public sealed class InMemoryCheckpointStore : IExecutionCheckpointStore`

把位置留在内存里的检查点存储 —— 对一个进程内暂停再恢复的运行足够了，也是宿主想要检查点但不想写文件时得到的默认实现。

| 成员 | 签名 | 说明 |
|---|---|---|
| `HasCheckpoint` | `bool` | 是否保存过任何东西。 |
| `SaveAsync` | `Task SaveAsync(ExecutionCheckpoint checkpoint, CancellationToken ct)` | 替换已保存的内容。返回已完成的任务。 |
| `LoadAsync` | `Task<ExecutionCheckpoint?> LoadAsync(CancellationToken ct)` | 返回最近保存的检查点，或 `null`。 |
| `Clear()` | `void` | 丢弃已保存的内容 —— 给运行已结束、位置不再值得保留的宿主。 |

**异常：** 无。

**说明：** 并发保存用一把锁串行化，因为引擎可能同时有两条扇出分支在保存。传进来的检查点会**原样**保留，所以打算事后修改它的宿主应该先交一份拷贝。

**示例（测试 —— `CompilerEx/ExecutionCheckpointTests.cs`；并在随库实现上复现）：**

```csharp
var store = new InMemoryCheckpointStore();
var context = new RuntimeContext { CheckpointStore = store };
await new RuntimeEngine().RunAsync(graph, context, ct, null);
var saved = await store.LoadAsync(CancellationToken.None);
// saved.Shape 每个被驱动的节点一项；saved.Data 是最后一个节点的产物。
```

要一个活过进程的存储，用 `VeloxDev.Core.Extension` 里的 `FileCheckpointStore` —— 见 `MVVM 序列化`。

---

## `BranchRuntimeContext` *（internal）*

`internal sealed class BranchRuntimeContext(IRuntimeContext session) : IRuntimeContext`。不属于公开面；写在这里是因为它解释了两种否则不可见的行为。

扇出的分支并发运行，所以分支在 `await` 之间写下、又被节点读回的状态不能与它的兄弟共享。它也不能用 `AsyncLocal<T>` 做成流局部：节点在自己帧的深处调用 `Error`，而引擎在往上好几帧之后才读这个标志，而 `AsyncLocal` 的写入不会回到调用方 —— 第一次尝试这个改法就恰恰在那里失败，引擎既有的重定向/前缀测试把它抓住了。

于是每条分支拿到自己的对象：

| 分支私有 | 转发到会话 |
|---|---|
| `Data`、`ReportedLevel` / `RedirectRequested`、`PendingRedirectTarget`、`CurrentNode` | 身份（`Uid`）、进度（`Attempt`、`NodeIndex`、`Status`、`CurrentOrder`、`CurrentEntry`、`BranchKey`）、`Logs`、共享变量（`Set` / `TryGet`）、产物登记表（`RegisterOutput` / `ResetOutputs` / `CollectGroupedInputs`） |

作为调用方，有两点值得知道：

- **日志是转发而不是缓冲。** 运行的行必须按实际发生的顺序读，交错的分支也不例外，这样文件版 `ILogWriter` 与 `IRuntimeContext.Logs` 讲的才是同一个故事。这也正是宿主的单会话仍然有意义的原因（UI 仍然只绑一个会话）。
- **分支内的 `Warn` 标记的是分支，不是会话。** `CompilerLogWriterTests.ABranchsWarn_MarksTheBranch_NotTheSession` 断言 `session.RedirectRequested == false`，而分支的警告仍然出现在 `Logs` 里 —— 会话自己的 `CurrentNode` 属于最后被驱动的那条分支。

`IsCompilePhase` 不转发：它恒为 `false`。线性链注入的仍然是宿主自己的会话对象，这正是 `EntrySemanticsTests.OneRunSession_IsInjectedAsTheSameInstance_ToEveryNode` 钉住的事。
