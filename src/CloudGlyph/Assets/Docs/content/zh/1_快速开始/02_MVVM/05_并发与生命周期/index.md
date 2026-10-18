# MVVM — 并发、取消与生命周期

`VeloxDev.MVVM.VeloxCommand`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）是每条生成命令背后的运行时。它派生自 `CommandPipeline<object?, object?>`，线程安全且与 UI 无关：可串行或并行执行、支持每次执行的协作式取消，并通过生命周期事件流报告每一次状态转换。

## 1. 八个生命周期事件

每个事件的类型都是 `CommandEventHandler`（`void CommandEventHandler(CommandEventArgs e)`）。`CommandEventArgs` 公开 `Parameter`、`EventType` 与 `Exception`；每次执行的 `CancellationTokenSource` 是 internal。

| 事件 | 含义 |
| --- | --- |
| `Created` | 执行请求被受理 |
| `Enqueued` | 并发已满，请求在 FIFO 队列中等待 |
| `Dequeued` | 排队请求离开队列，即将运行 |
| `Started` | 被包装的方法开始 |
| `Completed` | 方法正常返回 |
| `Failed` | 方法抛出异常；`e.Exception` 携带它（只有该阶段携带） |
| `Canceled` | 运行被取消，或请求被拒绝 |
| `Exited` | 运行离开活动集合 |

`CanExecuteChanged` 是标准 `ICommand` 事件，单独触发。

**序列：**

- 立即运行：`Created → Started → Completed → Exited`
- 排队：`Created → Enqueued`，槽位释放后 `Dequeued → Started → Completed → Exited`
- 因锁被拒绝：只有 `Created → Canceled`，永不 `Started`、永不 `Exited`
- 运行中取消：`Created → Started → Canceled → Exited`

一次执行最多上报**一条** `Canceled`：`Interrupt` / `Clear` 会及时上报，方法体随后抛出的 `OperationCanceledException` 会被抑制。

**预期结果：** 方法体运行前触发 `Started`，返回后触发 `Completed`；方法体抛异常时触发 `Failed`（而非 `Completed`）；其它阶段（包括 `Exited`）的 `e.Exception` 保持 `null`。

## 2. 串行与并行执行

并发容量来自特性的 `semaphore`（默认 `1`）。

- `_active.Count < capacity` → 立即开始。
- 否则 → 请求入队（`Enqueued`），槽位释放后启动（`Dequeued`）。

第一条运行期间再次触发会**排队，而不是丢弃或合并**。`ChangeSemaphore(n)` 调整容量并立即排空能容纳的项。

**预期结果：** 容量为 1 时连续触发十次会串行运行十次；容量为 3 时三次重叠。容量小于 1 会从构造函数与两个 `ChangeSemaphore` 重载抛出 `ArgumentOutOfRangeException`。

## 3. 每次执行的取消

方法体接收 `CancellationToken` 时，每次执行都有独立的源，并在该次执行结束时释放 —— 包括被 `Clear` 丢弃、从未运行的排队项。`OperationCanceledException` 表现为 `Canceled`，绝不会是 `Failed`。

没有 token 的形态仍会被追踪，但无法停止方法体：触发 `Canceled` 并移除该次运行，而方法体继续跑完。

**预期结果：** 方法体等待 `Task.Delay(Timeout.Infinite, ct)` 时，中断会报告 `Canceled`；等价的仅形参方法体也报告 `Canceled`，但其自身的代码仍继续运行。

## 4. 锁定、中断、清空、继续

| API（同步 / 异步） | 效果 |
| --- | --- |
| `Lock()` / `LockAsync()` | 进入强制锁定：`CanExecute` 为 `false`，新请求被拒绝（`Created → Canceled`）；运行中的工作不受影响 |
| `Unlock()` / `UnlockAsync()` | 解除锁定，并启动队列当前能容纳的工作 |
| `Interrupt()` / `InterruptAsync()` | 取消正在运行的执行；原本已锁定的命令保持锁定 |
| `Clear()` / `ClearAsync()` | 丢弃整个队列（每个排队项先 `Dequeued` 再 `Canceled`），并取消活动执行 |
| `Continue()` / `ContinueAsync()` | 启动待处理工作 —— 锁定时为空操作 |
| `ChangeSemaphore(n)` / `ChangeSemaphoreAsync(n)` | 修改容量（`< 1` 抛异常）并启动待处理工作 |
| `Notify()` | 触发 `CanExecuteChanged`，让绑定控件重新查询谓词 |

同步成员是对 `Async` 版本的 fire-and-forget 便捷封装。拼写是 **`Unlock`**，不是 `UnLock`。

**预期结果：** `Lock()` 之后 `Execute(null)` 产生 `Created → Canceled` 且方法体不运行；`Clear()` 清空已饱和的队列；状态变化后 `Notify()` 让之前禁用的绑定按钮启用。

## 5. 线程、编组与故障订阅者

- **线程安全。** 内部状态由私有 `SemaphoreSlim(1,1)` 保护，内部 await 使用 `ConfigureAwait(false)`。持锁期间不运行任何用户代码。
- **`EventContext`** —— 默认在管线所在线程上内联触发事件。将其设为 UI 的 `SynchronizationContext` 后，事件会按生命周期顺序投递到该上下文。投递是异步的：事件可能在触发调用返回之后才到达处理器。
- **`HandlerException`** —— 订阅者抛异常不会干扰命令；异常通过静态 `VeloxCommand.HandlerException` 上报，否则被丢弃。`CanExecuteChanged` 订阅者同理。
- **`Dispose()`** —— 释放内部锁。只应在拆除、且没有执行在途时调用。释放是最终操作。

**预期结果：** 未设置 `EventContext` 时处理器在管线线程运行；设置后按顺序在上下文线程运行。抛异常的处理器仍然得到 `Completed`；若订阅了 `HandlerException`，异常会出现在那里。

## 运行声明

- ⚠️ 本次文档修订未实际运行 —— 仅对照 `MVVM/CommandPipeline{TParam,TResult}.cs` 以及 `Src/Core/VeloxDev.Core.Test/MVVM/` 中的测试（`VeloxCommandLifecycleTests`、`VeloxCommandCancellationTests`、`VeloxCommandControlTests`、`VeloxCommandEventContextTests`、`VeloxCommandDiagnosticsTests`）做了静态核对。
