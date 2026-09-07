# Transition — Contracts: Effect, Scheduler, Interpreter, UI Thread

Namespace `VeloxDev.TransitionSystem`. These interfaces describe the timing descriptor, the per-target execution coordinator, the sampling-loop runner, and UI-thread marshaling. Each has a priority-typed variant used by adapters that marshal at a dispatcher priority (WPF, Avalonia, Jalium, WinUI) and a non-typed variant used by the others.

### Interface: `ITransitionEffectCore`

| Member | Type / Signature | Description |
|---|---|---|
| `FPS` | `int FPS { get; set; }` | **Maximum sample-rate cap**, default `60`. The yield interval is `1000 / FPS` ms. Timing is Stopwatch-driven continuous sampling — `FPS` bounds how often the loop samples; it is *not* a frame grid. |
| `Duration` | `TimeSpan Duration { get; set; }` | Nominal pass length; default `0` (a zero-duration pass samples once and jumps to the end). |
| `IsAutoReverse` | `bool IsAutoReverse { get; set; }` | When `true`, each pass is followed by a reverse pass. |
| `LoopTime` | `int LoopTime { get; set; }` | Number of repeat passes after the first; `int.MaxValue` = infinite looping. |
| `Ease` | `IEaseCalculator Ease { get; set; }` | Easing curve applied to the raw normalized time. |
| Events | `EventHandler<TransitionEventArgs>` | `Awaked`, `Start`, `Update`, `LateUpdate`, `Canceled`, `Completed`, `Finally`. |
| Invokers | `void Invoke*(object sender, TransitionEventArgs e)` | `InvokeAwake`, `InvokeStart`, `InvokeUpdate`, `InvokeLateUpdate`, `InvokeCompleted`, `InvokeCancled`, `InvokeFinally` (the misspelling `InvokeCancled` is the real member name). |
| `Clone` | `ITransitionEffectCore Clone()` | Deep copy that also clones the (weak) event backing stores. |

**Notes:**
- Event ordering in a normal run: scheduler fires `Awaked` on the UI thread before preparing, then the loop fires `Start` once, then `Update` / `LateUpdate` per sample, and `Completed` after the last pass. A cancelled run fires `Canceled`, and **every** end path (completed or cancelled) fires `Finally`.
- *Verified by:* `TransitionEffectCoreTests` (`Defaults_AreCorrect`, `Events_AreInvoked`, `Clone_CopiesProperties`, `EventRemove_StopsFiring`), `SamplingLoopTests` (event-order assertions).

### Interface: `ITransitionEffect<TPriorityCore>`

Extends `ITransitionEffectCore` with a typed priority and a covariant clone:

```csharp
public interface ITransitionEffect<TPriorityCore> : ITransitionEffectCore
{
    TPriorityCore Priority { get; set; }
    new ITransitionEffect<TPriorityCore> Clone();
}
```

**Notes:** Adapter effects set a concrete priority default (e.g. WPF/Avalonia `DispatcherPriority.Render`, WinUI `DispatcherQueuePriority.High`); the loop passes `Priority` through to the sampler set's `Apply`.

### Interface: `ITransitionSchedulerCore`

```csharp
public interface ITransitionSchedulerCore
{
    Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    void Exit();
}
```

**Notes:**
- `Execute` runs one prepared animation on the scheduler's target: it prepares the `SamplerSet`, fires `Awaked`, then delegates to the interpreter. A `SemaphoreSlim` gate serializes executions on a *mutual* scheduler (a second animation cancels the first); `externCts` lets the caller supply its own cancellation source.
- `Exit()` cancels the currently running animation of that scheduler.
- Typed variants narrow the effect parameter:
  - `ITransitionScheduler<TPriorityCore> : ITransitionSchedulerCore` — `Execute(InterpolatorCore, IFrameState, ITransitionEffect<TPriorityCore>, CancellationTokenSource? externCts = default)`.
  - `ITransitionScheduler : ITransitionSchedulerCore` — marker (no new members).
- The concrete scheduler base `Abstractions.TransitionSchedulerCore` supplies the per-target registry tables and `FindOrCreate` (see [01_abstractions](../../01_abstractions/index.md)).
- *Verified by:* `SamplingLoopTests`; WPF demo `RepeatMutual` (a new mutual animation cancels the previous one).

### Interface: `ITransitionInterpreterCore`

```csharp
public interface ITransitionInterpreterCore : IDisposable
{
    TransitionEventArgs Args { get; set; }
    Task Execute(object target, SamplerSet samplerSet, ITransitionEffectCore effect, CancellationTokenSource cts);
    void Exit();
}
```

**Notes:**
- `Args` is the event-arguments instance the interpreter drives; setting `Args.Handled = true` short-circuits the timeline (the loop throws `OperationCanceledException` → `Canceled` + `Finally`).
- `Execute` runs the Stopwatch-driven sampling loop against the prepared `SamplerSet`. `Exit()` (alias of `Dispose`) cancels the active `CancellationTokenSource`.
- Typed variants:
  - `ITransitionInterpreter<TPriorityCore> : ITransitionInterpreterCore` — `Execute(object target, SamplerSet samplerSet, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource cts)`.
  - `ITransitionInterpreter : ITransitionInterpreterCore` — marker.
- The concrete loop behavior lives in `Abstractions.TransitionInterpreterCore` (see [01_abstractions](../../01_abstractions/index.md)).
- *Verified by:* `SamplingLoopTests` (`DurationZero_JumpsToEnd_AndCompletes`, `HandledBeforeStart_CancelsAndFiresFinally`).

### Interfaces: `IUIThreadInspectorCore`, `IUIThreadInspector`, `IUIThreadInspector<TPriorityCore>`

```csharp
public interface IUIThreadInspectorCore
{
    bool IsAppAlive();
    bool IsUIThread();
    void ProtectedInvoke(object target, Action action, object? priority = default);
    object? ProtectedGetValue(object target, ITransitionProperty property);
}
```

| Member | Description |
|---|---|
| `IsAppAlive` | Whether the host application is still alive (stale-frame guard: `SamplerSet.Apply` returns early when false). |
| `IsUIThread` | Whether the caller already runs on the UI thread. |
| `ProtectedInvoke` | Marshals `action` to the UI thread (uses the target's owning dispatcher / control when available). `priority` is opaque unless the concrete inspector understands the type. |
| `ProtectedGetValue` | Reads the property through the chain, marshaling to the UI thread when needed. |

**Notes:**
- Two typed specializations add a no-priority convenience overload and a priority-taking overload:
  - `IUIThreadInspector : IUIThreadInspectorCore` — `void ProtectedInvoke(object target, Action action);`
  - `IUIThreadInspector<TPriorityCore> : IUIThreadInspectorCore` — `void ProtectedInvoke(object target, Action action, TPriorityCore priority);`
- The `abstract` keyword on `ProtectedInvoke` (see the interface source) is an implementation detail of the concrete core classes.
- Per-platform behavior is documented in [03_adapter-provided/02_ui-inspector](../../03_adapter-provided/02_ui-inspector/index.md).
