# Design Patterns — Transition

The Transition feature is a framework-agnostic animation engine. Its core lives in `Src/Core/VeloxDev.Core/TransitionSystem/**` (abstract/generic "core" types in the `VeloxDev.TransitionSystem.Abstractions` namespace, engine contracts in `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/**`, native samplers under `TransitionSystem/NativeSamplers/**`). It is UI-thread aware but has no reference to any concrete UI stack. Every UI framework is reached through a per-platform adapter package under `Src/Adapters/VeloxDev.*/PlatformAdapters` (WPF, Avalonia, WinUI, MAUI, WinForms, Razor, Jalium), and each platform is exercised by a demo under `Examples/Transition/**`.

The same core is instantiated twice: a **priority-aware** pipeline that carries a framework dispatcher priority (`DispatcherPriority`, `DispatcherQueuePriority`, …) and a **plain** pipeline without one. WPF/WinUI/Avalonia/Jalium use the priority arity; MAUI/WinForms/Razor use the plain arity.

## Core class diagram

```mermaid
classDiagram
    class TransitionCore~TTarget,TStateSnapshot~ {
        <<static factory>>
        +Create() TStateSnapshot
        +Execute(target, snapshot, CanMutualTask) void
    }
    class TransitionCore {
        <<abstract>>
        +Exit(target, IncludeMutual, IncludeNoMutual) void
    }
    class StateSnapshotCore~TTarget,...~ {
        <<fluent builder base>>
        +GetState() TState
        +CoreExecute(target, CanMutualTask) void
        +CoreAwaitThen(span) / CoreThen()
    }
    class IFrameState {
        <<interface>>
        +Values / Interpolators / Options ConcurrentDictionary
        +Clone() IFrameState
    }
    class StateCore {
        +Clone() IFrameState
    }
    class TransitionProperty {
        +Path string
        +Segments IReadOnlyList~PropertyInfo~
        +GetValue(target) object?
        +SetValue(target, value) bool
    }
    class InterpolatorCore {
        <<abstract>>
        +NativeInterpolators ConcurrentDictionary~Type, ISampler~
        +TryGetInterpolator(type) bool
        +RegisterInterpolator(type, sampler) bool
        +Prepare(target, state, effect, inspector) SamplerSet
    }
    class ISampler {
        <<interface>>
        +NormalizeStart(start, end, options) object?
        +NormalizeEnd(start, end, options) object?
        +InsertFrame(target, property, ref working, start, end, options, t) void
    }
    class ISampleable {
        <<interface>>
        +GetAnimatableMembers() IReadOnlyList~ITransitionProperty~
        +CreateFrameValue(memberValues) object?
    }
    class StructAssembler {
        <<internal static>>
        +Create(property, sampleable, start, end) ISampler?
    }
    class SamplerSet {
        +Apply(target, t, priority) void
        +CanSetValue() bool
    }
    class TransitionSchedulerCore {
        <<abstract>>
        +MutualSchedulers / NoMutualSchedulers ConditionalWeakTable
        +FindOrCreate(source, CanMutualTask) scheduler
        +Execute(producer, state, effect, cts) Task
        +Exit() void
    }
    class TransitionInterpreterCore {
        <<abstract>>
        +Args TransitionEventArgs
        +Execute(target, samplerSet, effect, cts) Task
        +Exit() / Dispose()
    }
    class ITransitionSchedulerCore {
        <<interface>>
    }
    class ITransitionInterpreterCore {
        <<interface>>
        +Args TransitionEventArgs
    }
    class TransitionEffectCore {
        +FPS / Duration / IsAutoReverse / LoopTime
        +Ease IEaseCalculator
        +events Awaked Start Update LateUpdate Canceled Completed Finally
    }
    class IEaseCalculator {
        <<interface>>
        +Ease(t) double
    }
    class Eases {
        <<static>>
        +Default IEaseCalculator
        +Sine / Quad / Cubic / Quart / Quint
        +Expo / Circ / Back / Elastic / Bounce
    }
    class UIThreadInspectorCore {
        <<abstract>>
        +IsAppAlive() bool
        +IsUIThread() bool
        +ProtectedInvoke(target, action, priority) void
        +ProtectedGetValue(target, property) object?
    }
    class IUIThreadInspectorCore {
        <<interface>>
    }

    TransitionCore~TTarget,TStateSnapshot~ --|> TransitionCore : Exit
    TransitionCore~TTarget,TStateSnapshot~ --> StateSnapshotCore~TTarget,...~ : Create / Execute
    StateSnapshotCore~TTarget,...~ --> IFrameState : records values
    StateCore ..|> IFrameState
    StateCore --> TransitionProperty : dictionary keys
    InterpolatorCore ..> ISampler : registry & per-property override
    InterpolatorCore ..> SamplerSet : Prepare builds
    InterpolatorCore ..> StructAssembler : value-type ISampleable
    StructAssembler ..> ISampleable : expands members
    StructAssembler ..> ISampler : produces StructAssemblerSampler
    SamplerSet --> ISampler : drives InsertFrame per frame
    SamplerSet --> IUIThreadInspectorCore : marshals writes
    TransitionSchedulerCore ..|> ITransitionSchedulerCore
    TransitionInterpreterCore ..|> ITransitionInterpreterCore
    TransitionSchedulerCore --> TransitionInterpreterCore : instantiates one per Execute
    TransitionInterpreterCore --> SamplerSet : samples eased time
    TransitionInterpreterCore --> TransitionEffectCore : lifecycle events + Ease
    TransitionEffectCore --> IEaseCalculator : strategy
    Eases ..> IEaseCalculator : produces (Sine/Quad/... )
```

Native samplers implement `ISampler` and live under `TransitionSystem/NativeSamplers/*`: `DoubleSampler`, `FloatSampler`, `IntSampler`, `LongSampler`, `PointSampler`, `PointFSampler`, `SizeSampler`, `SizeFSampler`, `ColorSampler`, `RectangleSampler`, `RectangleFSampler`, and (outside `netstandard2.0`) `Vector2Sampler`, `Vector3Sampler`, `Vector4Sampler`, `QuaternionSampler`.

## Adapter side class diagram (WPF as example)

Every adapter fills the generic parameters of the core with framework-bound subclasses. WPF demonstrates the priority arity; the same shape is repeated in every adapter package.

```mermaid
classDiagram
    class Transition {
        <<empty core subclass>>
    }
    class Transition~T~ {
        <<static factory>>
        +StateSnapshot nested
    }
    class StateSnapshot {
        +Property(lambda, value, options) StateSnapshot
        +Effect(effect) / Effect(Action~TransitionEffect~) StateSnapshot
    }
    class State {
        <<StateCore subclass>>
    }
    class Interpolator {
        <<InterpolatorCore subclass>>
    }
    class TransitionEffect {
        <<TransitionEffectCore~DispatcherPriority~>>
        +Priority DispatcherPriority = Render
    }
    class UIThreadInspector {
        <<UIThreadInspectorCore~DispatcherPriority~>>
        +ProtectedInvoke(target, action, DispatcherPriority)
    }
    class TransitionScheduler {
        <<TransitionSchedulerCore~UIThreadInspector,TransitionInterpreter,DispatcherPriority~>>
    }
    class TransitionInterpreter {
        <<TransitionInterpreterCore~TransitionEffect,DispatcherPriority~>>
    }

    Transition~T~ --|> TransitionCore~T,StateSnapshot~
    StateSnapshot --|> StateSnapshotCore~T,State,TransitionEffect,Interpolator,UIThreadInspector,TransitionInterpreter,DispatcherPriority~
    State --|> StateCore
    Interpolator --|> InterpolatorCore
    TransitionEffect --|> TransitionEffectCore~DispatcherPriority~
    UIThreadInspector --|> UIThreadInspectorCore~DispatcherPriority~
    TransitionScheduler --|> TransitionSchedulerCore
    TransitionInterpreter --|> TransitionInterpreterCore
    Transition --|> TransitionCore
```

Sources: `Src/Core/VeloxDev.Core/TransitionSystem/Transition.cs`, `StateSnapshot.cs`, `State.cs`, `SamplerSet.cs`, `Interpolator.cs`, `TransitionScheduler.cs`, `TransitionInterpreter.cs`, `TransitionEffect.cs`, `StructAssembler.cs`, `TransitionProperty.cs`, `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/*.cs`, `Src/Adapters/VeloxDev.WPF/PlatformAdapters/*.cs` (plus the sibling `VeloxDev.{Avalonia,WinUI,MAUI,WinForms,Razor,Jalium}/PlatformAdapters` folders).

## Patterns Identified

### 1. Fluent Builder + chain-of-segments (`Transition<T>.StateSnapshot`)

`Transition<T>.Create()` returns the adapter's `StateSnapshot`, whose typed `.Property(expr, value, options)` overloads and `.Effect(...)` methods each return the same snapshot. `.Await(span)`, `.Then()` and `.AwaitThen(span)` (extension methods on `StateSnapshotCore`) create the **next** segment and link it through the `next` pointer, so one builder expression actually describes an ordered **list of segments** — each carrying its own `State`, `Effect`, `Interpolator` and pre-delay. `Execute(target, CanMutualTask)` consumes the whole chain.

```csharp
// Examples/Transition/WPF/Demo/MainWindow.xaml.cs (Animation0, lines 141-151)
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

### 2. Registry (`InterpolatorCore.NativeInterpolators`)

`NativeInterpolators` is a static `ConcurrentDictionary<Type, ISampler>` — samplers, not "sampleables", are registered **by property type**. `InterpolatorCore`'s static constructor seeds cross-platform types (numeric, `System.Drawing` geometry, `System.Numerics`), and each adapter's `Interpolator` static constructor adds framework types (e.g. WPF `Brush`, `Thickness`, `Transform`, `Color`, `Point3D`, `DropShadowEffect`). `RegisterInterpolator` uses atomic `AddOrUpdate` (last-writer-wins, no lost updates).

`Prepare` resolves each recorded property in this order: per-property override in `state.Interpolators` → registry lookup by `PropertyType` → for **value-type** properties only, `currentValue is ISampleable` → `StructAssembler.Create`. Properties that resolve to nothing are skipped, so one bad path never distorts the others.

### 3. `ISampleable` member expansion / struct assembly

`ISampleable` is *not* a sampler. A type implements it to declare which of its members are animatable (`GetAnimatableMembers`) and, for structs, how to rebuild the value from interpolated members (`CreateFrameValue`). Reference-type `ISampleable` values are expanded into member paths **at capture time** by the snapshot helpers. A value-type `ISampleable` property is animated as a whole by `StructAssembler` (an internal adapter object that interpolates each member with its own `ISampler` and reconstructs the struct through its constructor — zero reflection at runtime).

### 4. Strategy (easing + sampling)

`IEaseCalculator.Ease(double t)` is the easing strategy selected by `effect.Ease`; `Eases` is the strategy set (Sine/Quad/Cubic/… each In/Out/InOut, plus `Default` = identity). `ISampler` is the value-interpolation strategy: the core calls `NormalizeStart`/`NormalizeEnd` once at prepare time to fix the exact endpoint values, then `InsertFrame(target, property, ref working, start, end, options, t)` to compute a middle frame. `t` is already eased and clamped by the interpreter; each sampler treats `t <= 0`/`t >= 1` as exact endpoint writes (it never relies on `Ease(1)` being exactly `1`). Reference-type samplers reuse a per-animation `working` scratch (never mutate the shared `start`/`end`, which would pollute the snapshot).

### 5. Template Method / generic policy pipeline

The core classes fix the algorithm skeleton and leave the framework-specific choices to subclasses supplied through generic parameters:

| Core skeleton | What the adapter fills |
|---|---|
| `StateSnapshotCore<…>` | `State`, `TransitionEffect`, `Interpolator`, `UIThreadInspector`, `TransitionInterpreter` (+ optional `TPriority`) |
| `TransitionSchedulerCore<TInspector,TInterpreter[,TPriority]>` | concrete inspector/interpreter (via `new()`) used per `Execute` |
| `TransitionInterpreterCore<TEffect[,TPriority]>` | the sampling loop's `apply` callback (frame writes with/without a dispatcher priority) |
| `UIThreadInspectorCore[<TPriority>]` | dispatcher marshaling, `IsAppAlive`/`IsUIThread` |
| `TransitionEffectCore[<TPriority>]` | default `Priority` value, default `FPS` |

### 6. Adapter (per-platform packages)

`Transition<T>` / `State` / `Interpolator` / `TransitionEffect` / `TransitionScheduler` / `TransitionInterpreter` / `UIThreadInspector` in each adapter adapt the engine to one UI stack: platform `Property` overloads (typed to framework value types such as WPF `Brush`, `Transform`, `CornerRadius`, `Point3D`), framework sampler registrations, dispatcher-priority-typed effects, and thread marshaling.

### 7. Scheduler + `ConditionalWeakTable` cache (`TransitionSchedulerCore`)

`MutualSchedulers` is a `ConditionalWeakTable<object, ITransitionSchedulerCore>` — one shared **mutual** scheduler per target, collected with the target (no leak). `FindOrCreate(target, CanMutualTask)` returns it, or a fresh **non-mutual** scheduler that is tracked in `NoMutualSchedulers` (a `List` per target) while it runs and removed when its effect's `Finally` fires. A `SemaphoreSlim` gate serializes `Execute` calls on a scheduler; each scheduler also holds a `WeakReference` to its target so finished animations do not keep the target alive.

### 8. Composite (multi-segment timeline)

Each segment is a small object holding `State + Effect + Interpolator + delay`; segments are linked by `next`. `CoreExecute` walks the chain once to queue every segment, then plays them in order (honoring each segment's `Await` delay), giving a composite timeline (see Data Flow).

### 9. Observer (effect lifecycle events)

`TransitionEffectCore` exposes `Awaked/Start/Update/LateUpdate/Canceled/Completed/Finally` events backed by `WeakDelegate` (leak-free). Handlers can set `TransitionEventArgs.Handled = true` to kill the timeline; the interpreter raises `Update`/`LateUpdate` around each sample and `Completed`/`Canceled`/`Finally` around the run's end.

## Pattern Summary

| Pattern | Where it appears | Role |
|---|---|---|
| Fluent Builder + chain | `StateSnapshot`/`StateSnapshotCore.next` | Describe a target state + segment timing without mutable config objects |
| Registry | `InterpolatorCore.NativeInterpolators` | Map a property type to an `ISampler` at runtime |
| `ISampleable` expansion | Snapshot helpers + `StructAssembler` | Animate object members / structs the registry has no sampler for |
| Strategy | `IEaseCalculator`/`Eases`, `ISampler` | Swap easing curves and per-type interpolation without changing the engine |
| Template Method / policy | `StateSnapshotCore`, `InterpolatorCore`, scheduler/interpreter/inspector/effect cores | Fix the skeleton; adapters supply platform specifics via generics |
| Adapter | per-platform `PlatformAdapters/*` | Bridge the engine to one UI framework's types and dispatcher |
| Scheduler + CWT cache | `TransitionSchedulerCore` mutual/non-mutual tables | One serialized animation per target; no leaks |
| Composite | `StateSnapshotCore.next` chain | Compose multi-segment timelines |
| Observer | `TransitionEffectCore` events + `WeakDelegate` | Observe lifecycle without polling |

Sources: `Src/Core/VeloxDev.Core/TransitionSystem/*.cs`, `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/*.cs`, `Src/Core/VeloxDev.Core/TransitionSystem/NativeSamplers/*.cs`, `Src/Adapters/VeloxDev.{WPF,Avalonia,WinUI,MAUI,WinForms,Razor,Jalium}/PlatformAdapters/*.cs`, `Examples/Transition/WPF/Demo/MainWindow.xaml.cs`.

Related analysis: [Data flow — Transition](../../03_data-flow/03_transition/index.md) · [Complexity — Transition](../../04_complexity/03_transition/index.md)
