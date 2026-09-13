# Transition — Adapter: `UIThreadInspector`, `TransitionScheduler`, `TransitionInterpreter`

The platform marshaling and execution plumbing each adapter fills in. All are subclasses of the engine skeletons from [01_abstractions](../../01_abstractions/index.md) and live in the `VeloxDev.TransitionSystem` namespace.

### Class: `UIThreadInspector` (per adapter)

Each adapter's inspector implements `IsAppAlive`, `IsUIThread`, `ProtectedGetValue` and `ProtectedInvoke` with platform marshaling. Target objects that carry their own thread affinity (a `DispatcherObject` / `Control` / `DependencyObject`) are marshaled directly on their owning thread; otherwise a captured app-level dispatcher / synchronization context is used.

| Adapter | Priority type argument | Aliveness | UI detection / marshaling |
|---|---|---|---|
| WPF | `DispatcherPriority` | `IsAppAlive() => true` | Target `DispatcherObject.Dispatcher` first, else `Application.Current.Dispatcher`. `ProtectedInvoke` → `Dispatcher.InvokeAsync(action, priority)` when not on the UI thread; `ProtectedGetValue` → `Dispatcher.Invoke`. |
| Avalonia | `DispatcherPriority` | `true` | `Dispatcher.UIThread`. `ProtectedInvoke` → `Dispatcher.UIThread.InvokeAsync(action, priority)`; reads via `Dispatcher.UIThread.Invoke`. |
| Jalium | `DispatcherPriority` | `true` | Target `DispatcherObject.Dispatcher` first, else `Application.Current.Dispatcher`, else `Dispatcher.MainDispatcher`. `ProtectedInvoke` → `Dispatcher.BeginInvoke(priority, action)`. |
| WinUI | `DispatcherQueuePriority` | `_isAppAlive` flag | Target `DependencyObject.DispatcherQueue` first (accessible from any thread), else a lazily captured global `DispatcherQueue`; `CaptureUIThread()` pre-captures for non-`DependencyObject` targets. |
| MAUI | `NonPriority` | `Application.Current?.Windows?.Count > 0` | `Application.Current.Dispatcher.Dispatch(...)`; synchronous reads via a `TaskCompletionSource`. |
| WinForms | `NonPriority` | `_isAppAlive` flag (false after `Application.ApplicationExit`) | Target `Control` first (`Invoke` / `BeginInvoke` when handle created), else a `WindowsFormsSynchronizationContext` captured lazily; optional `CaptureUIThread()`. |
| Razor | `NonPriority` | `_isAppRunning` flag | Blazor circuit `SynchronizationContext` captured on first UI-thread access; `CaptureUIThread()` optional, `NotifyShutdown()` on app stop. |

**Notes:**
- WPF, Avalonia and Jalium return `IsAppAlive() => true` and rely on their dispatcher being live; WinForms/Razor/WinUI track an explicit alive flag; MAUI checks `Application.Current?.Windows?.Count > 0`.
- All inspectors are priority-typed: MAUI/WinForms/Razor derive from the parameterless `UIThreadInspectorCore`, which implements `IUIThreadInspector<NonPriority>` and discards the marker; the others derive from `UIThreadInspectorCore<TPriorityCore>` and take the adapter's dispatcher priority.
- `ProtectedInvoke` returns `bool` (was the action queued at all?); `ProtectedInvokeAsync` additionally completes once it ran, and the base's `DispatchAsync` is what makes awaiting safe — it only waits when the queue accepted the action.

### Class: `TransitionScheduler` (per adapter)

An empty subclass that parameterizes the scheduler base with the adapter's concrete inspector + interpreter:

| Adapter | Declared type / base class |
|---|---|
| WPF | `TransitionScheduler : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| Avalonia | `TransitionScheduler<TTarget> : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| Jalium | `TransitionScheduler : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| WinUI | `TransitionScheduler<TTarget> : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherQueuePriority>` |
| MAUI / WinForms / Razor | `TransitionScheduler : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, NonPriority>` |

All scheduling behavior — the `MutualSchedulers` / `NoMutualSchedulers` tables, `FindOrCreate`, gating, and `Exit` — is inherited (see [01_abstractions](../../01_abstractions/index.md)). This is the type the adapter's `Interpolator.CreateScheduler` hands out — the override returns `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, TPriorityCore>.FindOrCreate(target)`, so the parameterization above is exactly the one a theme switch runs on (see [01_effect-interpolator](../01_effect-interpolator/index.md)).

### Class: `TransitionInterpreter` (per adapter)

An empty subclass that parameterizes the sampling-loop interpreter with the adapter's concrete effect:

| Adapter | Base class |
|---|---|
| WPF / Avalonia / Jalium | `TransitionInterpreterCore<TransitionEffect, DispatcherPriority>` |
| WinUI | `TransitionInterpreterCore<TransitionEffect, DispatcherQueuePriority>` |
| MAUI / WinForms / Razor | `TransitionInterpreterCore<TransitionEffect>` (implements `ITransitionInterpreter<NonPriority>`) |

The priority-typed variants apply each eased frame with `frameSet.Apply(target, t, effect.Priority)`; the non-priority variants apply without a priority (see [01_abstractions](../../01_abstractions/index.md)).
