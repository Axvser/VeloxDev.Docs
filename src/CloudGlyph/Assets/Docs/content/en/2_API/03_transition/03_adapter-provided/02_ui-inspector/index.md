# Transition — Adapter: `UIThreadInspector`, `TransitionScheduler`, `TransitionInterpreter`

The platform marshaling and execution plumbing each adapter fills in. All are subclasses of the engine skeletons from [01_abstractions](../../01_abstractions/index.md) and live in the `VeloxDev.TransitionSystem` namespace.

### Class: `UIThreadInspector` (per adapter)

Each adapter's inspector implements `IsAppAlive`, `IsUIThread`, `ProtectedGetValue` and `ProtectedInvoke` with platform marshaling. Target objects that carry their own thread affinity (a `DispatcherObject` / `Control` / `DependencyObject`) are marshaled directly on their owning thread; otherwise a captured app-level dispatcher / synchronization context is used.

| Adapter | Priority type | Aliveness | UI detection / marshaling |
|---|---|---|---|
| WPF | `DispatcherPriority` | `IsAppAlive() => true` | Target `DispatcherObject.Dispatcher` first, else `Application.Current.Dispatcher`. `ProtectedInvoke` → `Dispatcher.InvokeAsync(action, priority)` when not on the UI thread; `ProtectedGetValue` → `Dispatcher.Invoke`. |
| Avalonia | `DispatcherPriority` | `true` | `Dispatcher.UIThread`. `ProtectedInvoke` → `Dispatcher.UIThread.InvokeAsync(action, priority)`; reads via `Dispatcher.UIThread.Invoke`. |
| Jalium | `DispatcherPriority` | `true` | Target `DispatcherObject.Dispatcher` first, else `Application.Current.Dispatcher`, else `Dispatcher.MainDispatcher`. `ProtectedInvoke` → `Dispatcher.BeginInvoke(priority, action)`. |
| WinUI | `DispatcherQueuePriority` | `_isAppAlive` flag | Target `DependencyObject.DispatcherQueue` first (accessible from any thread), else a lazily captured global `DispatcherQueue`; `CaptureUIThread()` pre-captures for non-`DependencyObject` targets. |
| MAUI | — (none) | `Application.Current?.Windows?.Count > 0` | `Application.Current.Dispatcher.Dispatch(...)`; synchronous reads via a `TaskCompletionSource`. |
| WinForms | — | `_isAppAlive` flag (false after `Application.ApplicationExit`) | Target `Control` first (`Invoke` / `BeginInvoke` when handle created), else a `WindowsFormsSynchronizationContext` captured lazily; optional `CaptureUIThread()`. |
| Razor | — | `_isAppRunning` flag | Blazor circuit `SynchronizationContext` captured on first UI-thread access; `CaptureUIThread()` optional, `NotifyShutdown()` on app stop. |

**Notes:**
- WPF, Avalonia and Jalium return `IsAppAlive() => true` and rely on their dispatcher being live; WinForms/Razor/WinUI track an explicit alive flag; MAUI checks `Application.Current?.Windows?.Count > 0`.
- Priority-typed inspectors accept the adapter's dispatcher priority; non-priority inspectors (MAUI/WinForms/Razor) marshal at the framework default.
- The abstract `ProtectedInvoke(object target, Action action, object? priority = default)` (base) is overridden to dispatch to the typed overload.

### Class: `TransitionScheduler` (per adapter)

An empty subclass that parameterizes the scheduler base with the adapter's concrete inspector + interpreter:

| Adapter | Base class |
|---|---|
| WPF / Avalonia / Jalium | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| WinUI | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherQueuePriority>` |
| MAUI / WinForms / Razor | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter>` |

All scheduling behavior — the `MutualSchedulers` / `NoMutualSchedulers` tables, `FindOrCreate`, gating, and `Exit` — is inherited (see [01_abstractions](../../01_abstractions/index.md)).

### Class: `TransitionInterpreter` (per adapter)

An empty subclass that parameterizes the sampling-loop interpreter with the adapter's concrete effect:

| Adapter | Base class |
|---|---|
| WPF / Avalonia / Jalium | `TransitionInterpreterCore<TransitionEffect, DispatcherPriority>` |
| WinUI | `TransitionInterpreterCore<TransitionEffect, DispatcherQueuePriority>` |
| MAUI / WinForms / Razor | `TransitionInterpreterCore<TransitionEffect>` |

The priority-typed variants apply each eased frame with `frameSet.Apply(target, t, effect.Priority)`; the non-priority variants apply without a priority (see [01_abstractions](../../01_abstractions/index.md)).
