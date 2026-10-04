# MVVM — 并发、取消与生命周期

`VeloxDev.MVVM.VeloxCommand`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）是每条生成命令背后的运行时。它是一个线程安全、与 UI 无关的异步命令：既能把执行串行化也能并行化，支持每次运行的合作式取消，并通过生命周期事件流报告每一次状态迁移。

## 1. 八个生命周期事件

每个事件类型都是 `CommandEventHandler` —— `void CommandEventHandler(CommandEventArgs e)`。`CommandEventArgs` 公开暴露 `Parameter`、`EventType` 与 `Exception`；它携带的每次执行 `CancellationTokenSource` 是 **`internal`**，不属于公开接口（完整成员列表见 API 参考）。

| 事件 | 含义 |
|---|---|
| `Created` | 一次执行请求已被受理 |
| `Enqueued` | 容量已满 —— 请求正在 FIFO 队列中等待 |
| `Dequeued` | 排队请求离开队列，即将运行 |
| `Started` | 被包装的方法真正开始执行 |
| `Completed` | 方法正常返回 |
| `Failed` | 方法抛异常 —— `e.Exception` 携带它（且仅此阶段携带） |
| `Canceled` | 运行被取消，或请求被拒绝 |
| `Exited` | 运行结束并离开活动集合 |

`CanExecuteChanged` 是标准的 `ICommand` 事件，单独触发。

**时序：**

- 立即执行：`Created → Started → Completed → Exited`
- 排队执行：`Created → Enqueued` …… 槽位空闲后 `Dequeued → Started → Completed → Exited`
- 被锁拒绝：仅 `Created → Canceled` —— 从不 `Started`，从不 `Exited`
- 运行中被取消：`Created → Started → Canceled → Exited`

一次执行最多上报**一条** `Canceled`。`Interrupt` / `Clear` 与命令体自身抛出的 `OperationCanceledException` 都想上报；先到的那条胜出，因此按执行计数 `Canceled` 的处理器只会数到一次。

**预期结果：** 订阅 `cmd.Started += e => ...` 与 `cmd.Completed += e => ...` 后，能在方法体运行前观察到 `Started`、返回后观察到 `Completed`；方法体抛出异常会触发带 `e.Exception` 的 `Failed` 而不是 `Completed`；其它所有阶段（包括 `Exited`）的 `e.Exception` 始终为 `null` —— 不要把 `Exited` 当成成功信号。

## 2. 串行与并行执行

执行由并发容量（`_maxConcurrency`，来自特性的 `semaphore`，默认 `1`）约束：

- `_active.Count < 容量` → 立即开始运行。
- 否则 → 请求入队（`Enqueued`），等活动中的运行退出后再启动（`Dequeued`）。

在默认容量下，每次触发都恰好执行一次，按 FIFO 顺序 —— 第一次还在运行时再次触发会被**排队，而不是丢弃或合并**。`ChangeSemaphore(n)` 可在运行时调整容量并立即启动能容纳的排队项。

**预期结果：** 对一个容量为 1、方法体耗时 100ms 的命令连续触发十次，会得到十次串行的方法体执行；容量为 3 时会有三次重叠。随后调高容量会启动积压的队列。容量小于 1 会被拒绝：构造函数与 `ChangeSemaphoreAsync` 抛 `ArgumentOutOfRangeException`，同步的 `ChangeSemaphore` 出于同样原因在派发前先自行校验。

## 3. 每次运行的取消

凡是形参里带 `CancellationToken` 的方法，其每次运行都拥有**自己的** `CancellationTokenSource`，并在该次执行结束时释放 —— 包括排队期间被 `Clear` 丢弃、从未真正运行的那次。token 从不跨队列共享；`OperationCanceledException` 呈现为 `Canceled`，绝不会是 `Failed`。

对于**不带** token 的方法形态（无参方法体、`void` 方法体、`Task M(object?)`），运行时依然追踪该次运行，但无法真正停止方法体：会触发 `Canceled` 并把该次运行移除，而方法体仍会继续跑到返回为止。

**预期结果：** `await Task.Delay(Timeout.Infinite, ct)` 的方法体在被中断时触发 `Canceled`；等价的仅带参数方法体同样触发 `Canceled`，但它自己的代码会继续执行到结束。

## 4. 加锁、中断、清空、继续

| API（同步 / 异步） | 效果 |
|---|---|
| `Lock()` / `LockAsync()` | 进入强制锁定状态：`CanExecute` 返回 `false`，新请求被拒绝（`Created → Canceled`）；运行中的工作不受影响 |
| `Unlock()` / `UnlockAsync()` | 退出锁定状态，并启动队列现在能容纳的项 |
| `Interrupt()` / `InterruptAsync()` | 取消当前正在运行的执行；本就处于锁定状态的命令保持锁定 |
| `Clear()` / `ClearAsync()` | 丢弃整个队列（每个排队项先 `Dequeued` 再 `Canceled`），并取消活动中的执行 |
| `Continue()` / `ContinueAsync()` | 启动排队中的工作 —— 锁定期间为空操作 |
| `ChangeSemaphore(n)` / `ChangeSemaphoreAsync(n)` | 修改容量（`< 1` 抛异常）并启动排队中的工作 |
| `Notify()` | 触发 `CanExecuteChanged`，让绑定控件重新查询 `CanExecute` 谓词 |

同步成员是异步孪生方法的即发即忘（fire-and-forget）便捷版。注意拼写：成员是 **`Unlock`**，不是 `UnLock`。

WPF 演示对 `MinusCommand` 同时展示了两种调用风格 —— `FreeCommand`（即发即忘）与 `FreeCommandAsync`（可等待）。

**预期结果：** `MinusCommand.Lock()` 之后，`MinusCommand.Execute(null)` 产生 `Created → Canceled` 且方法体从不运行；`MinusCommand.Clear()` 清空已饱和的队列并让命令保持未锁定；状态变化后调用 `Notify()` 会把被禁用的绑定按钮翻转为启用。

## 5. 线程、编组与抛异常的订阅者

- **线程安全：** 所有内部状态（`_pendingQueue`、`_active`、`_isForceLocked`、`_maxConcurrency`）由私有 `SemaphoreSlim(1,1)` 保护，内部 await 一律 `ConfigureAwait(false)`。持锁期间不运行任何用户代码，因此阻塞在命令上的处理器不会把命令锁死。
- **`EventContext`** —— 默认事件在管线所在线程上就地触发，因此触碰 UI 的处理器必须自己编组。把 `EventContext` 设为 UI 框架的 `SynchronizationContext` 后，命令会改为把事件投递到那里，并保持生命周期顺序。投递是异步的：某个事件可能在那次触发调用返回之后才到达处理器。
- **`HandlerException`** —— 抛异常的订阅者绝不会干扰命令，异常被吞掉。`VeloxCommand.HandlerException` 是报告这些失败的静态事件（`CanExecuteChanged` 的订阅者同样适用）。没有订阅者时，行为与这个事件不存在时完全一致；钩子自身抛异常也会被丢弃而不会向外传播。
- **`Dispose()`** —— 释放命令内部的锁。仅应在拆除阶段、且没有任何在途调用时使用；仅仅被丢弃的命令无需释放。释放是终态。

**预期结果：** `EventContext` 未设置时，触碰 UI 的处理器在管线线程上运行；设置后处理器在目标上下文的线程上按生命周期顺序运行；抛异常的处理器产出的是 `Completed`（而非 `Failed`），若订阅了 `HandlerException` 则该异常会在那里被上报。

## 运行声明

- ✅ 2026-10-01 已部分执行。生命周期与加锁行为在一个临时控制台项目中验证过（该项目以 Debug 项目引用 `VeloxDev.Core`，用 `dotnet run -c Debug` 运行，录制输出）：

  ```text
  Increment -> Completed (Succeeded=True)
  Decrement -> Completed
  status: IsBusy=False, Active=0, Pending=0
  while locked -> Refused
  ```

  第三、四行是第 2、4 节的可观察结果：两条命令结束后计数器空闲，而在持有 `LockAsync()` 期间发出的调用被拒绝。

- 事件顺序、单条 `Canceled` 规则、每次执行 token 源的释放，以及 `EventContext` 的投递路径本次**未**实际执行。它们转录自 `VeloxCommand.cs`，并由 `Src/Core/VeloxDev.Core.Test/MVVM/` 下的一组测试钉住（`VeloxCommandLifecycleTests`、`VeloxCommandCancellationTests`、`VeloxCommandDisposalTests`、`VeloxCommandEventContextTests`、`VeloxCommandDiagnosticsTests`、`VeloxCommandControlTests`、`VeloxCommandConcurrencyTests`、`VeloxCommandLockInvariantTests`）。
