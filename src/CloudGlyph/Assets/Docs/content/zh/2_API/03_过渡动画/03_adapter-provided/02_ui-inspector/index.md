# Transition — 适配器：`UIThreadInspector`、`TransitionScheduler`、`TransitionInterpreter`

各适配器填入的平台编组与执行管道。它们都是 [01_abstractions](../../01_abstractions/index.md) 引擎骨架的子类，位于 `VeloxDev.TransitionSystem` 命名空间。

### 类：`UIThreadInspector`（各适配器）

各适配器的检查器用平台编组实现 `IsAppAlive`、`IsUIThread`、`ProtectedGetValue` 与 `ProtectedInvoke`。自带线程亲和性的目标对象（`DispatcherObject` / `Control` / `DependencyObject`）直接在其所属线程上编组；否则使用捕获的应用级 dispatcher / 同步上下文。

| 适配器 | 优先级类型 | 存活判定 | UI 检测 / 编组 |
|---|---|---|---|
| WPF | `DispatcherPriority` | `IsAppAlive() => true` | 优先目标 `DispatcherObject.Dispatcher`，否则 `Application.Current.Dispatcher`。`ProtectedInvoke` 不在 UI 线程时 → `Dispatcher.InvokeAsync(action, priority)`；`ProtectedGetValue` → `Dispatcher.Invoke`。 |
| Avalonia | `DispatcherPriority` | `true` | `Dispatcher.UIThread`。`ProtectedInvoke` → `Dispatcher.UIThread.InvokeAsync(action, priority)`；读经 `Dispatcher.UIThread.Invoke`。 |
| Jalium | `DispatcherPriority` | `true` | 优先目标 `DispatcherObject.Dispatcher`，否则 `Application.Current.Dispatcher`，再否则 `Dispatcher.MainDispatcher`。`ProtectedInvoke` → `Dispatcher.BeginInvoke(priority, action)`。 |
| WinUI | `DispatcherQueuePriority` | `_isAppAlive` 标志 | 优先目标 `DependencyObject.DispatcherQueue`（任意线程可访问），否则惰性捕获的全局 `DispatcherQueue`；非 `DependencyObject` 目标可 `CaptureUIThread()` 预捕获。 |
| MAUI | `NonPriority`（无优先级） | `Application.Current?.Windows?.Count > 0` | `Application.Current.Dispatcher.Dispatch(...)`；同步读经 `TaskCompletionSource`。 |
| WinForms | `NonPriority` | `_isAppAlive` 标志（`Application.ApplicationExit` 后为 false） | 优先目标 `Control`（handle 已创建时 `Invoke` / `BeginInvoke`），否则惰性捕获的 `WindowsFormsSynchronizationContext`；可选 `CaptureUIThread()`。 |
| Razor | `NonPriority` | `_isAppRunning` 标志 | Blazor 电路 `SynchronizationContext` 在首次 UI 线程访问时捕获；可选 `CaptureUIThread()`，应用停止时 `NotifyShutdown()`。 |

**说明：**
- WPF、Avalonia、Jalium 返回 `IsAppAlive() => true`，依赖其 dispatcher 存活；WinForms/Razor/WinUI 跟踪显式存活标志；MAUI 检查 `Application.Current?.Windows?.Count > 0`。
- 优先级类型化检查器接受适配器的 dispatcher 优先级（`TPriorityCore`）；非优先级检查器（MAUI/WinForms/Razor）用 `NonPriority` 填类型参数，命中 `UIThreadInspectorCore` 的无优先级重载（`ProtectedInvoke(target, action, NonPriority)` 直接转发到 `ProtectedInvoke(target, action)`），按框架默认编组。
- 所有 `ProtectedInvoke` 返回 `bool`——该 action 是否真的入队；`ProtectedInvokeAsync` 只在 action 真的执行完后才完成，供调度器 await 效果的 Awake。

### 类：`TransitionScheduler`（各适配器）

用适配器具体检查器 + 解释器参数化调度器基类的空子类：

| 适配器 | 基类 |
|---|---|
| WPF / Avalonia / Jalium | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| WinUI | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherQueuePriority>` |
| MAUI / WinForms / Razor | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, NonPriority>` |

全部调度行为——`MutualSchedulers` / `NoMutualSchedulers` 表、`FindOrCreate`、门控、`Exit`——均继承（见 [01_abstractions](../../01_abstractions/index.md)）。这也是适配器 `Interpolator.CreateScheduler` 交回的类型——该重写返回 `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, TPriorityCore>.FindOrCreate(target)`，所以上表的参数化正是主题切换所跑的那一套（见 [01_effect-interpolator](../01_effect-interpolator/index.md)）。

### 类：`TransitionInterpreter`（各适配器）

用适配器具体效果参数化采样循环解释器的空子类：

| 适配器 | 基类 |
|---|---|
| WPF / Avalonia / Jalium | `TransitionInterpreterCore<TransitionEffect, DispatcherPriority>` |
| WinUI | `TransitionInterpreterCore<TransitionEffect, DispatcherQueuePriority>` |
| MAUI / WinForms / Razor | `TransitionInterpreterCore<TransitionEffect>` |

优先级类型化变体以 `frameSet.Apply(target, t, effect.Priority)` 应用每个缓动帧；非优先级变体不带优先级应用（见 [01_abstractions](../../01_abstractions/index.md)）。
