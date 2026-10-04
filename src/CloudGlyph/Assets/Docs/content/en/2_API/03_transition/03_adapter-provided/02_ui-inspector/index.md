# Transition — Adapter: `UIThreadInspector`, `TransitionScheduler`, `TransitionInterpreter`

The platform host and execution plumbing each adapter fills in. All are subclasses of the engine skeletons from [abstractions](../../01_abstractions/01_engine/index.md) and live in the `VeloxDev.TransitionSystem` namespace.

### Class: `UIThreadInspector` (per adapter) — the adapter's host

Each adapter's inspector is its `ITransitionHost<TPriorityCore>`: it derives from `TransitionHostBase<TPriorityCore>`, supplies the three abstract members a host owes (`ThreadFor`, `IsCurrentThread`, `PostCore`) and reports its own liveness. Target objects that carry their own thread affinity (a `DispatcherObject` / `Control` / `DependencyObject`) are marshaled directly on their owning thread; otherwise a captured app-level dispatcher / synchronization context is used.

| Adapter | Priority type argument | Liveness | Thread resolution / marshaling |
|---|---|---|---|
| WPF | `DispatcherPriority` | `Lifetime.IsAlive` (always true) | Target `DispatcherObject.Dispatcher` first, else `Application.Current?.Dispatcher ?? Dispatcher.FromThread(Thread.CurrentThread)`. `PostCore` → `Dispatcher.InvokeAsync(action, priority)`; returns `false` when the thread is `None` or the dispatcher has begun shutting down. `InternalPriority` = `Send`. |
| Avalonia | `DispatcherPriority` | `Lifetime.IsAlive` | `Dispatcher.UIThread`. `PostCore` → `Dispatcher.InvokeAsync(action, priority)`. `InternalPriority` = `Send`. |
| Jalium | `DispatcherPriority` | `Lifetime.IsAlive` | Target `DispatcherObject.Dispatcher` first, else the app dispatcher. `PostCore` → `Dispatcher.BeginInvoke(...)`. |
| WinUI | `DispatcherQueuePriority` | `Lifetime.IsAlive`, driven by `SetAlive(accepted)` on every `TryEnqueue` | Target `DependencyObject.DispatcherQueue` first; otherwise a lazily captured global queue — `CaptureUIThread()` pre-captures it for non-`DependencyObject` targets started from a background thread. `PostCore` → `DispatcherQueue.TryEnqueue(priority, ...)`, and both directions are reported (a queue refusal means the app is exiting; an acceptance means it is alive), so one transient refusal does not mark it permanently dead. `InternalPriority` = `Normal`. |
| MAUI | `NonPriority` | overridden: `Application.Current?.Windows?.Count > 0` | Target `BindableObject.Dispatcher` first (its `Dispatcher` getter can throw before it is attached to a handler), else `Application.Current?.Dispatcher`. `PostCore` → `IDispatcher.Dispatch(action)` — the return value *is* the acceptance. |
| WinForms | `NonPriority` | overridden: an `_isAppAlive` flag cleared on `Application.ApplicationExit` | Target `Control` first (`BeginInvoke` once its handle exists — the control knows its own UI thread, so no capture is needed even for a background first start), else a `WindowsFormsSynchronizationContext` captured lazily. `CaptureUIThread()` is an optional fallback that throws when it cannot capture. `IsCurrentFor` is overridden to ask the control (`!InvokeRequired`). |
| Razor | `NonPriority` | an `_isAppRunning` flag; `NotifyShutdown()` clears it | Blazor circuit `SynchronizationContext`, captured lazily on first UI-thread access; `CaptureUIThread()` is optional and only needed when the first start is from a background thread. |

**Notes:**
- `ThreadFor` **never mints** a dispatcher for the calling thread and never throws: it catches and answers `ThreadRef.None`, which merely costs that target its pacer (the loop then waits on the default thread-pool timer). An exception there would be indistinguishable per frame from the animation failing.
- All inspectors are priority-typed hosts: MAUI, WinForms and Razor carry `NonPriority` (which costs nothing per frame), the others carry the adapter's dispatcher priority. There is no priority-free host base — `TransitionHostBase<NonPriority>` *is* the priority-free one.
- `Post` returns `bool` (*was the action queued at all?*); `PostAsync` additionally completes once it ran, and the base's `PostAsync` only waits when the queue accepted the action — a host that silently drops an action would otherwise never complete its `TaskCompletionSource`.
- *Verified by:* `AUTO TEST` `ObservationSurface_IsReachableAndTicking` on all seven platforms; `TransitionRunThreadAffinityTests`.

### Class: `TransitionScheduler` (per adapter)

An empty subclass that parameterizes the scheduler base with the adapter's concrete host + interpreter:

| Adapter | Declared type / base class |
|---|---|
| WPF | `TransitionScheduler : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| Avalonia | `TransitionScheduler<TTarget> : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| Jalium | `TransitionScheduler : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| WinUI | `TransitionScheduler<TTarget> : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherQueuePriority>` |
| MAUI / WinForms / Razor | `TransitionScheduler : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, NonPriority>` |

All scheduling behavior — the `MutualSchedulers` / `NoMutualSchedulers` tables, `FindOrCreate`, gating, `ExecuteCapturing` / `Replay`, and `Exit` — is inherited (see [abstractions](../../01_abstractions/01_engine/index.md)). This is the type the adapter's `Interpolator.CreateScheduler` hands out — the override returns `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, TPriorityCore>.FindOrCreate(target)`, so the parameterization above is exactly the one a theme switch runs on (see [effect-interpolator](../01_effect-interpolator/index.md)). On Avalonia and WinUI the type is declared generic with an unused `TTarget` parameter.

### Class: `TransitionInterpreter` (per adapter)

A subclass that parameterizes the sampling-loop interpreter with the adapter's concrete effect **and — except for Razor — overrides `CreateFramePacer`** so the loop waits on the platform's own timer instead of the default thread-pool one:

| Adapter | Base class | `CreateFramePacer` override |
|---|---|---|
| WPF | `TransitionInterpreterCore<TransitionEffect, DispatcherPriority>` | the target's `Dispatcher` → a `DispatcherTimer(DispatcherPriority.Normal, dispatcher)` pacer (stopped and nulled on `Dispose`) |
| Avalonia | `TransitionInterpreterCore<TransitionEffect, DispatcherPriority>` | non-`None` thread → a `DispatcherTimer` pacer on Avalonia's single UI dispatcher (unsubscribed on `Dispose`) |
| Jalium | `TransitionInterpreterCore<TransitionEffect, DispatcherPriority>` | the target's `Dispatcher` → a `DispatcherTimer` pacer |
| WinUI | `TransitionInterpreterCore<TransitionEffect, DispatcherQueuePriority>` | the target's `DispatcherQueue` → a non-repeating `DispatcherQueueTimer` pacer (unsubscribed on `Dispose`) |
| MAUI | `TransitionInterpreterCore<TransitionEffect>` (implements `ITransitionInterpreter<NonPriority>`) | the target's `IDispatcher` → a repeating `IDispatcherTimer` pacer (stopped and unsubscribed on `Dispose`) |
| WinForms | `TransitionInterpreterCore<TransitionEffect>` (implements `ITransitionInterpreter<NonPriority>`) | the target `Control` on the current thread → a `PostedFramePacer` that posts each frame with `Control.BeginInvoke` from a thread-pool timer (`Dispose` releases it) |
| Razor | `TransitionInterpreterCore<TransitionEffect>` (implements `ITransitionInterpreter<NonPriority>`) | none — the default thread-pool timer is used |

**Notes:**
- Waiting on the UI thread's own timer is what keeps the continuation on that thread, so the effect's `Update` / `LateUpdate` callbacks run there and each frame's property write reaches the target without queueing a dispatch. Posting the continuation back would cost a dispatch per frame — the one thing the sampling path is built to avoid (see `FramePacerCore`).
- Each override returns `null` when it has no answer — no nameable thread (`ThreadRef.None`), or, for WinForms, a target that is not on the current thread — which is a supported answer: the loop then waits on the default timer.
- The priority-typed variants apply each eased frame with `frameSet.Apply(target, t, effect.Priority)`; the non-priority variants apply without a priority (see [abstractions](../../01_abstractions/01_engine/index.md)).
- *Verified by:* `AUTO TEST` `TimelineControl_SteersTheRunningAnimation` on all seven platforms; `FramePacerTests`.
