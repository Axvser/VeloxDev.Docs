# Design Patterns — Transition

```mermaid
classDiagram
    class TransitionCore~TTarget,TStateSnapshotCore~ {
        <<abstract static>>
        +Create() TStateSnapshotCore
        +Execute(target, value, CanMutualTask) void
        +Exit(target, IncludeMutual, IncludeNoMutual) void
    }
    class StateSnapshotCore~T,State,Effect,Interpolator,Inspector,Interpreter~ {
        <<abstract>>
        +Property(lambda, value, options) T
        +Effect(effect) T
        +Await(span) T
        +Then() T
        +AwaitThen(span) T
        +GetState() IFrameState
    }
    class StateCore {
        +Values dict
        +Interpolators dict
        +Options dict
        +SetValue(lambda, value) void
        +Clone() IFrameState
    }
    class TransitionProperty {
        +Path string
        +GetValue(target) object
        +SetValue(target, value) bool
        +TryCreate(expression, out) bool
    }
    class InterpolatorCore {
        <<abstract>>
        +NativeInterpolators dict
        +TryGetInterpolator(type, out) bool
        +RegisterInterpolator(type, sampleable) bool
        +Prepare(target, state, effect, inspector) SamplerSet
    }
    class ISampleable {
        <<interface>>
        +Normalize(start, end, options) ISampler
    }
    class ISampler {
        <<interface>>
        +Update(target, property, start, end, options, t) void
    }
    class SamplerSet {
        +Apply(target, t, priority) void
        +CanSetValue() bool
    }
    class TransitionEffectCore {
        +FPS int
        +Duration TimeSpan
        +IsAutoReverse bool
        +LoopTime int
        +Ease IEaseCalculator
        +events Awaked/Start/Update/LateUpdate/Canceled/Completed/Finally
    }
    class Eases {
        <<static>>
        +Default IEaseCalculator
        +Sine.In IEaseCalculator
        +Quad.In IEaseCalculator
    }
    class TransitionSchedulerCore {
        <<abstract>>
        +MutualSchedulers ConditionalWeakTable
        +NoMutualSchedulers ConditionalWeakTable
        +FindOrCreate(source, CanMutualTask) IScheduler
        +Execute(producer, state, effect, cts) Task
        +Exit() void
    }
    class TransitionInterpreterCore {
        <<abstract>>
        +Execute(target, samplerSet, effect, cts) Task
        +Exit() void
    }
    class UIThreadInspectorCore {
        <<abstract>>
        +IsAppAlive() bool
        +IsUIThread() bool
        +ProtectedInvoke(target, action, priority) void
        +ProtectedGetValue(target, property) object
    }

    TransitionCore~TTarget,TStateSnapshotCore~ --> StateSnapshotCore~T,State,Effect,Interpolator,Inspector,Interpreter~
    StateSnapshotCore~T,State,Effect,Interpolator,Inspector,Interpreter~ --> StateCore
    StateCore --> TransitionProperty
    TransitionSchedulerCore --> TransitionInterpreterCore
    TransitionInterpreterCore --> SamplerSet
    TransitionInterpreterCore --> TransitionEffectCore
    TransitionEffectCore --> Eases
    InterpolatorCore ..> ISampleable : registry
    ISampleable --> ISampler : Normalize
    SamplerSet --> ISampler : drives
    SamplerSet --> UIThreadInspectorCore
```

## Patterns Identified

### 1. Fluent Builder Pattern (`StateSnapshot`)

`Transition<T>.Create()` returns the `StateSnapshot` fluent builder. `.Property(lambda, value)`, `.Effect(...)`, `.Await(...)`, `.AwaitThen(...)`, `.Then()` each return the same snapshot for chaining; `.Execute(target, CanMutualTask)` consumes it. Segments are linked into a list (`next` pointer), so a single "builder" actually describes a **sequence** of segments.

```csharp
// Examples/Transition/WPF/Demo/MainWindow.xaml.cs
private static readonly Transition<Rectangle>.StateSnapshot Animation0 =
    Transition<Rectangle>.Create()
        .Property(r => r.Opacity, 0)
        .Property(r => ((TranslateTransform)r.RenderTransform).X, 800)
        .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
        .Effect(new TransitionEffect()
        {
            Duration = TimeSpan.FromSeconds(2),
            IsAutoReverse = true,
            LoopTime = 2,
        });
```

### 2. Registry Pattern (`InterpolatorCore`)

A global `ConcurrentDictionary<Type, ISampleable>` (`NativeInterpolators`) plus `RegisterInterpolator`/`TryGetInterpolator`/`UnregisterInterpolator`. Resolution order in `Prepare`: per-property custom sampler (`state.Interpolators`) → registry → the value IS `ISampleable`. `RegisterInterpolator` uses atomic `AddOrUpdate` (last-writer-wins, no lost updates).

### 3. Strategy Pattern (easing + samplers)

`IEaseCalculator.Ease(double t)` strategies come from `Eases.*` (`Sine`, `Quad`, `Bounce`, ...). `ISampler.Update(target, property, start, end, options, t)` strategies write the property at a normalized time (e.g. `DoubleSampler`, `ColorSampler`, `QuaternionSampler`). Easing is applied by the interpreter **before** sampling: it eases and clamps the normalized time to `easedT ∈ [0,1]` and then asks the sampler to update the property — there is no pre-computed frame array to re-index.

### 4. Template Method Pattern (core engine)

The core classes (`StateSnapshotCore` 6/7-generic arities, the non-generic `InterpolatorCore`, `TransitionSchedulerCore<TUIThreadInspector, TTransitionInterpreter[, TPriorityCore]>`, `TransitionInterpreterCore<TEffectCore[, TPriorityCore]>`, `UIThreadInspectorCore<TPriorityCore>`) define the algorithm skeleton; each **adapter** provides concrete subclasses for its platform (`TransitionEffect` priority, `Interpolator` sampler registrations, `UIThreadInspector` marshalling).

### 5. Proxy / Adapter Pattern (platform adapters)

`UIThreadInspector` wraps each platform's dispatcher (`Application.Current.Dispatcher`, `Dispatcher.UIThread`, `DispatcherQueue.TryEnqueue`, `SynchronizationContext.Post`, `Control.Invoke/BeginInvoke`) so the engine can start animations on any thread and marshal frame writes back to the UI thread.

### 6. Scheduler + `ConditionalWeakTable` caching

`TransitionSchedulerCore.MutualSchedulers` is a `ConditionalWeakTable<object, ITransitionSchedulerCore>` — one shared **mutual** scheduler per target, garbage-collected with the target (no leaks). `FindOrCreate(source, CanMutualTask)` returns it, or a one-off **non-mutual** scheduler (registered in `NoMutualSchedulers`) for parallel animations. A `SemaphoreSlim` gate serializes executions on a mutual scheduler.

### 7. Composite (state segments)

`.AwaitThen(...)` links snapshots into a **linked list of segments**, each with its own `State` + `Effect`; the interpreter plays them in order, honoring each segment's delay, easing, and loop settings.

### 8. Observer Pattern (effect lifecycle events)

`TransitionEffectCore` exposes `Awaked/Start/Update/LateUpdate/Canceled/Completed/Finally` events backed by `WeakDelegate` (leak-free); `TransitionInterpreterCore` invokes them around each sample and at completion/cancellation.

## Pattern Summary

| Pattern | Where it appears | Role |
|---|---|---|
| Fluent Builder | `StateSnapshotCore` chain | Describe a target state + timing without mutable config objects |
| Registry | `InterpolatorCore.NativeInterpolators` | Map a type to an `ISampleable` at runtime |
| Strategy | `IEaseCalculator`/`Eases`, `ISampler` | Swap easing curves and value interpolation without changing the engine |
| Template Method | `InterpolatorCore`, `TransitionSchedulerCore`, `TransitionInterpreterCore`, `UIThreadInspectorCore` | Fix the algorithm skeleton; let adapters fill in platform specifics |
| Adapter / Proxy | `UIThreadInspector` per platform | Hide dispatcher differences behind one interface |
| Scheduler + CWT cache | `TransitionSchedulerCore` mutual/non-mutual tables | One serialized animation per target; no leaks |
| Composite | `StateSnapshotCore.next` chain | Compose multi-segment timelines |
| Observer | `TransitionEffectCore` events | Observe lifecycle without polling |

> Source references: `Src/Core/VeloxDev.Core/TransitionSystem/*.cs`, `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/*.cs`, `Src/Adapters/VeloxDev.{WPF,...}/PlatformAdapters/*.cs`, `Examples/Transition/WPF/Demo/MainWindow.xaml.cs`.
