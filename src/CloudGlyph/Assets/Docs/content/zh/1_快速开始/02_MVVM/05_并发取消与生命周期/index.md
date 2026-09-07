# MVVM — 并发取消与生命周期

每个生成命令背后的运行时是 `VeloxDev.MVVM.VeloxCommand`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）。它是线程安全、与 UI 无关的异步命令：对执行做串行或并行控制、支持每次运行的协作式取消，并通过生命周期事件流报告每一次状态迁移。

## 1. 生命周期事件

`IVeloxCommand` 暴露 8 个事件，全部以 `CommandEventHandler` 为类型（委托 `void CommandEventHandler(CommandEventArgs e)`）。`CommandEventArgs` 携带 `Parameter`、`EventType`（`CommandEventType`）、`Exception`（失败时）与 `Cts`。

| 事件 | 含义 |
|---|---|
| `Created` | 收到一个执行请求 |
| `Enqueued` | 容量已满 —— 请求正在 FIFO 队列中等待 |
| `Dequeued` | 排队的请求离开队列、即将运行 |
| `Started` | 被包装的方法真正开始执行 |
| `Completed` | 方法正常返回 |
| `Failed` | 方法抛异常（非取消）—— `e.Exception` 持有它 |
| `Canceled` | 该次运行被取消（见下） |
| `Exited` | 该次运行结束并离开活动集 |

`CanExecuteChanged`（标准 `ICommand` 事件）在每次执行请求后与每次运行结束后被单独触发，让绑定的控件重新查询 `CanExecute`。

**容量充足、正常序列：** `Created → Started → Completed → Exited`。
**排队序列：** `Created → Enqueued` … 当空出位置后 `Dequeued → Started → Completed → Exited`。

**预期结果：** 订阅 `cmd.Started += e => ...` 与 `cmd.Completed += e => ...`，会观察到方法体运行前触发 `Started`、方法返回后触发 `Completed`；方法体内抛异常时触发 `Failed`（带 `e.Exception`）而不是 `Completed`。

## 2. 串行与并行执行（`semaphore`）

`ExecuteAsync` 检查并发预算（`_maxConcurrency`，来自特性的 `semaphore`，默认 `1`）：

- `_active.Count < semaphore` → 立即开始运行。
- 否则 → 请求入队（`Enqueued`），等某个活动运行退出后再启动（`Dequeued`）。

因此 `semaphore: 1` 下每次触发恰好执行一次、按 FIFO 顺序 —— 第一个还在运行时再次触发会**排队而不会丢失或合并**。`semaphore: 3` 时最多 3 个方法体并行；第 4 个入队。

**预期结果：** 对 `semaphore: 1`、方法体耗时 100 ms 的命令快速触发 10 次 `Execute`，方法体被串行执行 10 次；`semaphore: 3` 时同一时刻最多 3 个重叠。之后调用 `ChangeSemaphore(2)` 会实时调整预算。

## 3. 每次运行的取消

每个接收 `CancellationToken` 的方法运行都有**自己的** `CancellationTokenSource`（在 `ExecuteAsync` 内创建），因此令牌绝不会被排队的多次运行共享。包装器监视方法体：`OperationCanceledException` 表现为 `Canceled` 事件，绝不表现为 `Failed`。

对**不带**令牌的方法签名，运行时仍会跟踪该次运行，但无法协作式取消方法体 —— 会触发 `Canceled` 并丢弃该次运行，但方法体自身会继续直到返回。

**预期结果：** 一个 `await Task.Delay(Timeout.Infinite, ct)` 的方法体在其令牌被取消时触发 `Canceled`（而不是 `Failed`）。

## 4. Lock / interrupt / clear / continue

| API（同步 / 异步） | 效果 |
|---|---|
| `Lock()` / `LockAsync()` | 进入强制锁定状态：`CanExecute` 返回 `false`，新请求被立即取消；运行中的工作不受影响 |
| `UnLock()` / `UnLockAsync()` | 离开锁定状态并启动排队的任务 |
| `Interrupt()` / `InterruptAsync()` | 先锁定，再取消当前运行中的任务（`Canceled`） |
| `Clear()` / `ClearAsync()` | 先锁定，清空整个队列（每个排队项各触发一次 `Dequeued` + `Canceled`）并取消活动任务 |
| `Continue()` / `ContinueAsync()` | 未锁定时启动排队的任务 |
| `ChangeSemaphore(n)` / `ChangeSemaphoreAsync(n)` | 改变并发预算（`< 1` 时忽略）并启动排队的任务 |
| `Notify()` | 触发 `CanExecuteChanged`，让绑定的控件重新执行 `CanExecute` 谓词 |

WPF 演示同时展示了两种调用风格（`FreeCommand` 即发即忘 vs `FreeCommandAsync` 可等待）。

**预期结果：** `MinusCommand.Lock()` 之后，`MinusCommand.Execute(null)` 立即产生 `Canceled` 事件且方法体绝不运行；`MinusCommand.Clear()` 清空已满的队列；状态变化后调用 `Notify()` 会把禁用的按钮翻成可用（如同属性/命令页所示）。

## 5. 线程与调度说明

- **线程安全运行时：** 所有内部状态（`_pendingQueue`、`_active`、`_isForceLocked`、`_maxConcurrency`）都由私有 `SemaphoreSlim` 保护；内部 `await` 一律使用 `ConfigureAwait(false)`。你可以在任意线程调用 `ExecuteAsync` / `LockAsync` / …，并能在 UI 线程 `await` 它们而不会死锁。
- **不自动封送：** VeloxDev 不注入 dispatcher。命令体从哪里开始、事件在哪里触发，取决于调用方的上下文。绑定到 UI 的命令从 UI 线程启动，于是方法体自身的 `await` 延续经由它的 `SynchronizationContext` 回到该线程；从后台线程启动（或其等待的任务在线程池完成）的方法体则在完成线程上继续。如果这种延续要触碰 UI 绑定状态，请自行用宿主 dispatcher 封送（WPF 的 `Dispatcher.InvokeAsync`、Avalonia 的 `Dispatcher`）。

**预期结果：** 只做纯计算、不引用 UI 的命令可以完全跑在后台线程；命令从 UI 触发且更新被 UI 读取的可观察属性时，这些更新在 UI 线程上完成。

## 运行声明

- ⚠️ 仅静态核验 —— 编写本页时未编译或运行任何内容。事件顺序与 lock/interrupt/clear/continue 语义来自 `VeloxDev.Core/MVVM/VeloxCommand.cs`；演示调用风格来自 `Examples/MVVM/*/.../MainWindowViewModel.cs`。
