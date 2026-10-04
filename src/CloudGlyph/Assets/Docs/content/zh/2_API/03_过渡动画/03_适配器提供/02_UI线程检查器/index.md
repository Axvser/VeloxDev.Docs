# 过渡动画 — 适配器：`UIThreadInspector`、`TransitionScheduler`、`TransitionInterpreter`

各适配器填好的平台宿主与执行管线。它们都是 [abstractions](../../01_abstractions/01_引擎/index.md) 中引擎骨架的子类，位于 `VeloxDev.TransitionSystem` 命名空间。

### 类：`UIThreadInspector`（各适配器）—— 适配器宿主

各适配器的检查器就是它的 `ITransitionHost<TPriorityCore>`：派生自 `TransitionHostBase<TPriorityCore>`，提供宿主必须给出的三个抽象成员（`ThreadFor`、`IsCurrentThread`、`PostCore`）并报告自身存活。自带线程归属的目标对象（`DispatcherObject` / `Control` / `DependencyObject`）直接在它所属线程上编组；否则用捕获的应用级 dispatcher / 同步上下文。

| 适配器 | 优先级类型实参 | 存活 | 线程解析 / 编组 |
|---|---|---|---|
| WPF | `DispatcherPriority` | `Lifetime.IsAlive`（恒为 true） | 先目标 `DispatcherObject.Dispatcher`，否则 `Application.Current?.Dispatcher ?? Dispatcher.FromThread(Thread.CurrentThread)`。`PostCore` → `Dispatcher.InvokeAsync(action, priority)`；线程为 `None` 或 dispatcher 已开始关闭时返回 `false`。`InternalPriority` = `Send`。 |
| Avalonia | `DispatcherPriority` | `Lifetime.IsAlive` | `Dispatcher.UIThread`。`PostCore` → `Dispatcher.InvokeAsync(action, priority)`。`InternalPriority` = `Send`。 |
| Jalium | `DispatcherPriority` | `Lifetime.IsAlive` | 先目标 `DispatcherObject.Dispatcher`，否则应用 dispatcher。`PostCore` → `Dispatcher.BeginInvoke(...)`。 |
| WinUI | `DispatcherQueuePriority` | `Lifetime.IsAlive`，由每次 `TryEnqueue` 的 `SetAlive(accepted)` 驱动 | 先目标 `DependencyObject.DispatcherQueue`；否则惰性捕获的全局队列 —— `CaptureUIThread()` 为非 `DependencyObject` 目标、从后台线程首次启动时预先捕获。`PostCore` → `DispatcherQueue.TryEnqueue(priority, ...)`，两个方向都报（队列拒绝说明应用正在退出、接纳说明它还活着），因此一次瞬时拒绝不会永久判死。`InternalPriority` = `Normal`。 |
| MAUI | `NonPriority` | 重写：`Application.Current?.Windows?.Count > 0` | 先目标 `BindableObject.Dispatcher`（挂到 handler 之前其 `Dispatcher` 取值可能抛），否则 `Application.Current?.Dispatcher`。`PostCore` → `IDispatcher.Dispatch(action)` —— 返回值本身就是接纳与否。 |
| WinForms | `NonPriority` | 重写：`Application.ApplicationExit` 时清掉的 `_isAppAlive` 标志 | 先目标 `Control`（句柄建好后 `BeginInvoke` —— 控件知道自己的 UI 线程，因此即使后台首次启动也无需捕获），否则惰性捕获的 `WindowsFormsSynchronizationContext`。`CaptureUIThread()` 是可选的兜底，捕获不了时抛异常。`IsCurrentFor` 被重写为问控件（`!InvokeRequired`）。 |
| Razor | `NonPriority` | `_isAppRunning` 标志；`NotifyShutdown()` 清掉它 | Blazor 回路 `SynchronizationContext`，首次在 UI 线程访问时惰性捕获；`CaptureUIThread()` 可选，仅在首次从后台线程启动时需要。 |

**说明：**
- `ThreadFor` **绝不**为调用线程现造 dispatcher，也绝不抛异常：它捕获异常并回答 `ThreadRef.None`，那只是让该目标失去节奏器（循环随后等默认线程池定时器）。在那里抛异常，逐帧看与「动画失败」无法区分。
- 所有检查器都是带优先级的宿主：MAUI、WinForms、Razor 携带 `NonPriority`（每帧零成本），其余携带适配器的调度器优先级。不存在无优先级的宿主基类 —— `TransitionHostBase<NonPriority>` *就是*无优先级的那个。
- `Post` 返回 `bool`（*动作到底排进去了吗*）；`PostAsync` 在它真正运行后才完成，而基类的 `PostAsync` 只在队列接纳时才等 —— 否则静默丢弃动作的宿主会让它的 `TaskCompletionSource` 永不完成。
- *核验：* `AUTO TEST` 在全部七个平台上的 `ObservationSurface_IsReachableAndTicking`；`TransitionRunThreadAffinityTests`。

### 类：`TransitionScheduler`（各适配器）

空子类，用适配器的具体宿主 + 解释器参数化调度器基类：

| 适配器 | 声明类型 / 基类 |
|---|---|
| WPF | `TransitionScheduler : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| Avalonia | `TransitionScheduler<TTarget> : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| Jalium | `TransitionScheduler : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| WinUI | `TransitionScheduler<TTarget> : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherQueuePriority>` |
| MAUI / WinForms / Razor | `TransitionScheduler : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, NonPriority>` |

所有调度行为 —— `MutualSchedulers` / `NoMutualSchedulers` 表、`FindOrCreate`、门控、`ExecuteCapturing` / `Replay`，以及 `Exit` —— 都是继承来的（见 [abstractions](../../01_abstractions/01_引擎/index.md)）。这个类型正是适配器 `Interpolator.CreateScheduler` 交出的东西 —— 重写返回 `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, TPriorityCore>.FindOrCreate(target)`，因此上表的参数化就是一次主题切换实际运行的那套（见 [effect-interpolator](../01_效果插值器/index.md)）。Avalonia 与 WinUI 上该类型被声明为泛型，`TTarget` 形参未被使用。

### 类：`TransitionInterpreter`（各适配器）

子类，用适配器的具体 effect 参数化采样循环解释器，**并（Razor 除外）重写 `CreateFramePacer`**，让循环等平台自己的定时器而不是默认线程池那个：

| 适配器 | 基类 | `CreateFramePacer` 重写 |
|---|---|---|
| WPF | `TransitionInterpreterCore<TransitionEffect, DispatcherPriority>` | 目标的 `Dispatcher` → 一个 `DispatcherTimer(DispatcherPriority.Normal, dispatcher)` 节奏器（`Dispose` 时停表并置空） |
| Avalonia | `TransitionInterpreterCore<TransitionEffect, DispatcherPriority>` | 线程非 `None` → Avalonia 唯一 UI dispatcher 上的 `DispatcherTimer` 节奏器（`Dispose` 时退订） |
| Jalium | `TransitionInterpreterCore<TransitionEffect, DispatcherPriority>` | 目标的 `Dispatcher` → 一个 `DispatcherTimer` 节奏器 |
| WinUI | `TransitionInterpreterCore<TransitionEffect, DispatcherQueuePriority>` | 目标的 `DispatcherQueue` → 一个非重复的 `DispatcherQueueTimer` 节奏器（`Dispose` 时退订） |
| MAUI | `TransitionInterpreterCore<TransitionEffect>`（实现 `ITransitionInterpreter<NonPriority>`） | 目标的 `IDispatcher` → 一个重复的 `IDispatcherTimer` 节奏器（`Dispose` 时停表并退订） |
| WinForms | `TransitionInterpreterCore<TransitionEffect>`（实现 `ITransitionInterpreter<NonPriority>`） | 当前线程上的目标 `Control` → 一个 `PostedFramePacer`，从线程池定时器用 `Control.BeginInvoke` 把每一帧投递过去（`Dispose` 时释放） |
| Razor | `TransitionInterpreterCore<TransitionEffect>`（实现 `ITransitionInterpreter<NonPriority>`） | 无 —— 用默认线程池定时器 |

**说明：**
- 在 UI 线程自己的定时器上等待，是把续体留在这个线程上的手段，于是 effect 的 `Update` / `LateUpdate` 回调在那里跑，每帧的属性写入也无需排队一次派发即可到达目标。把续体投回来会每帧一次派发 —— 而那正是采样路径竭力避免的一件事（见 `FramePacerCore`）。
- 每个重写在无答案时返回 `null` —— 没有可命名线程（`ThreadRef.None`），或对 WinForms 而言目标不在当前线程上 —— 这是受支持的答案：循环随后等默认定时器。
- 带优先级的变体以 `frameSet.Apply(target, t, effect.Priority)` 施加每个缓动帧；无优先级的变体不带优先级（见 [abstractions](../../01_abstractions/01_引擎/index.md)）。
- *核验：* `AUTO TEST` 在全部七个平台上的 `TimelineControl_SteersTheRunningAnimation`；`FramePacerTests`。
