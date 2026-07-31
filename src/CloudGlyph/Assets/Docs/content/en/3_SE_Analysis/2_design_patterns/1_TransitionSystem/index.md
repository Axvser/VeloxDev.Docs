# Design Patterns — Transition System

```mermaid
classDiagram
    class TransitionCore~T,TSnapshot~ {
        <<static>>
        +Create() TSnapshot
        +Execute(target, value, CanMutualTask) void
    }
    class StateSnapshotCore {
        <<abstract>>
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
    }
    class InterpolatorCore {
        <<abstract>>
        +NativeInterpolators dict
        +TryGetInterpolator(type, out) bool
        +RegisterInterpolator(type, i) bool
    }
    class IValueInterpolator {
        <<interface>>
        +Interpolate(start, end, steps, options) List
    }
    class TransitionEffectCore {
        +FPS int
        +Duration TimeSpan
        +IsAutoReverse bool
        +LoopTime int
        +Ease IEaseCalculator
    }
    class Eases {
        <<static>>
        +Default IEaseCalculator
    }
    class TransitionSchedulerCore {
        <<abstract>>
        +MutualSchedulers table
        +FindOrCreate(source, CanMutualTask) IScheduler
        +Exit() void
    }
    class TransitionInterpreterCore {
        <<abstract>>
        +Execute(target, frames, effect, isUIAccess, cts) Task
        +Exit() void
    }
    class InterpolatorOutputBase {
        +Frames dict
        +Update(target, index, isUIAccess, priority) void
    }
    class UIThreadInspectorCore {
        <<abstract>>
        +IsUIThread() bool
        +ProtectedInvoke(isUIThread, action) void
    }

    TransitionCore~T,TSnapshot~ --> StateSnapshotCore
    StateSnapshotCore --> StateCore
    StateCore --> TransitionProperty
    TransitionSchedulerCore --> TransitionInterpreterCore
    TransitionInterpreterCore --> InterpolatorOutputBase
    TransitionInterpreterCore --> TransitionEffectCore
    TransitionEffectCore --> Eases
    InterpolatorOutputBase --> IValueInterpolator
    InterpolatorOutputBase --> UIThreadInspectorCore
    InterpolatorCore <|-- InterpolatorOutputBase
```

## Patterns Identified

### 1. Fluent Builder Pattern (`StateSnapshot`)

`Transition<T>.Create()` returns the `StateSnapshot` fluent builder. `.Property(lambda, value)`, `.Effect(...)`, `.Await(...)`, `.AwaitThen(...)`, `.Then()` each return the same snapshot for chaining; `.Execute(target, CanMutualTask)` consumes it.

```csharp
// Examples/Transition/WPF/Demo/MainWindow.xaml.cs (lines 80-90)
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

A global `ConcurrentDictionary<Type, IValueInterpolator>` (`NativeInterpolators`) plus `RegisterInterpolator`/`TryGetInterpolator`/`UnregisterInterpolator`. Resolution order: per-property custom interpolator → registry → `IInterpolable` on the current/new value.

### 3. Strategy Pattern (Easing + Interpolators)

`IEaseCalculator.Ease(double t)` strategies come from `Eases.*` (`Sine`, `Quad`, `Bounce`, ...). `IValueInterpolator.Interpolate(...)` strategies map a value type to a frame list (e.g. `ColorInterpolator`, `QuaternionInterpolator`). Easing is applied by re-indexing the pre-computed frame array (`GetEaseIndex` maps eased `t` → frame index), not re-evaluating values per frame.

### 4. Template Method Pattern (core engine)

The core classes (`StateSnapshotCore` 6/7-generic arities, `InterpolatorCore<T>`, `TransitionSchedulerCore<T>`, `TransitionInterpreterCore<T>`, `InterpolatorOutputCore<T>`, `UIThreadInspectorCore<T>`) define the algorithm skeleton; each **adapter** provides concrete subclasses for its platform (`TransitionEffect` priority, `Interpolator` registrations, `UIThreadInspector` marshalling).

### 5. Proxy / Adapter Pattern (platform adapters)

`UIThreadInspector` wraps each platform's dispatcher (`Application.Current.Dispatcher`, `Dispatcher.UIThread`, `DispatcherQueue.TryEnqueue`, `SynchronizationContext.Post`) so the engine can start animations on any thread and marshal frame writes back to the UI thread.

### 6. Singleton + `ConditionalWeakTable` caching (schedulers)

`TransitionSchedulerCore.MutualSchedulers` is a `ConditionalWeakTable<object, ITransitionSchedulerCore>` — one shared mutual scheduler per target, garbage-collected with the target (no leaks). `FindOrCreate(source, CanMutualTask)` returns it, or a one-off non-mutual scheduler for parallel animations.

### 7. Composite (state segments)

`.AwaitThen(...)` links snapshots into a **linked list of segments**, each with its own `State` + `Effect`; the interpreter plays them in order, honoring each segment's delay, easing and loop settings.

### 8. Observer Pattern (effect lifecycle events)

`TransitionEffectCore` exposes `Awaked/Start/Update/LateUpdate/Canceled/Completed/Finally` events backed by `WeakDelegate` (leak-free); `TransitionInterpreterCore` invokes them around each frame and at completion/cancellation.

> Source references: `Src/Core/VeloxDev.Core/TransitionSystem/*.cs`, `Src/Adapters/VeloxDev.{WPF,...}/PlatformAdapters/*.cs`, `Examples/Transition/WPF/Demo/MainWindow.xaml.cs`.
