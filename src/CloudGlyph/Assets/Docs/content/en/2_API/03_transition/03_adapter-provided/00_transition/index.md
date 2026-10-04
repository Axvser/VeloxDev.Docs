# Transition — Adapter: `Transition`, `Transition<T>`

Every adapter assembly (`VeloxDev.WPF`, `VeloxDev.Avalonia`, `VeloxDev.Jalium`, `VeloxDev.WinUI`, `VeloxDev.MAUI`, `VeloxDev.WinForms`, `VeloxDev.Razor`) defines these types in `PlatformAdapters/Transition.cs` inside the `VeloxDev.TransitionSystem` namespace.

### Class: `Transition` / `Transition<T>`

`Transition<T>` is the static entry point, the fluent builder and the executor at once — there is no nested `StateSnapshot` class:

```csharp
public class Transition : TransitionCore { }

public class Transition<T> : TransitionCore<
    T,
    State,
    TransitionEffect,
    Interpolator,
    UIThreadInspector,          // the adapter's ITransitionHost<TPriorityCore>
    TransitionInterpreter,
    TPriorityCore>              // DispatcherPriority / DispatcherQueuePriority / NonPriority
    where T : class
{
    public static Transition<T> Create();

    public Transition<T> Effect(Action<TransitionEffect> effectSetter);
    public Transition<T> Effect(TransitionEffect effect);
    public Transition<T> Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null);  // every adapter except Razor
    // (typed Property overloads per platform type follow — see the next section)
}
```

**Notes:**
- `Transition<T>` derives from the single-arity `TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, TPriorityCore>`, using the adapter's `State`, `TransitionEffect`, `Interpolator`, `UIThreadInspector` and `TransitionInterpreter`. The 5th type argument is the **host** — the adapter's `UIThreadInspector`, a `TransitionHostBase<TPriorityCore>` — and the 7th is the host's dispatcher priority: `DispatcherPriority` (WPF, Avalonia, Jalium), `DispatcherQueuePriority` (WinUI) or `NonPriority` (MAUI, WinForms, Razor).
- Building starts with `Transition<T>.Create()`, which marks the builder as the root of a chain. `Execute(...)` / the control methods / `GetState()` come from the `StateSnapshotCore<T>` base, and segment linking uses the Core `TransitionCoreEx` extensions (`Await`, `Then`, `AwaitThen`, `Repeat`, `Interpolator`) documented in [abstractions](../../01_abstractions/index.md). The non-generic `Transition` carries only the `TransitionCore` static entry points.

#### Effect overloads

| Signature | Description |
|---|---|
| `Transition<T> Effect(Action<TransitionEffect> effectSetter)` | Builds a fresh `TransitionEffect`, invokes the setter to configure it, and stores it as this segment's timing descriptor. |
| `Transition<T> Effect(TransitionEffect effect)` | Uses the supplied effect as this segment's timing descriptor. |

### Execution and control

`Execute` is not an extension — it is a member of the base chain, so every `Transition<T>` instance has it. The same is true of the control methods and the four queries:

| Member | Signature | Description |
|---|---|---|
| `Execute` | `void Execute(T target, bool CanMutualTask = true)` | Runs this builder chain on `target`. `true` (the default) uses the target's *mutual* scheduler, cancelling a running mutual animation; `false` runs concurrently on a fresh non-mutual scheduler. |
| `Execute` (shared timeline) | `void Execute(T target, ITimeSourceControl timeline, bool CanMutualTask = true)` | Runs the chain anchored to a timeline the caller supplies. Animations sharing a timeline share a transport: pausing, changing the rate or seeking one moves all of them together, while each keeps its own pass and its own place in it. |
| `Execute` (static batch) | `static void Execute(T target, IEnumerable<Transition<T>> values, bool CanMutualTask = false)` | Runs each builder in the batch on `target`; non-mutual by default. |
| `Exit` / `Pause` / `Resume` | `void Exit/Pause/Resume(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Stops / freezes / unfreezes the target's running animations. |
| `SetRate` | `void SetRate(T target, double rate, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Changes the playback rate without moving the position; `0` freezes without pausing; a negative rate is rejected. |
| `Seek` | `void Seek(T target, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false)` and `void Seek(T target, int cycle, TimeSpan position, …)` | Moves within the running pass, or into a numbered pass. |
| `IsPaused` / `Position` / `Cycle` / `Rate` | `… (T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | The four queries; each answers for nothing running rather than throwing. |
| `Exit` (static, on the non-generic `Transition`) | `static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | Same, reachable without a `Transition<T>` instance — as are `Pause`, `Resume`, `SetRate`, `Seek`, `IsPaused`, `Position`, `Cycle`, `Rate`. |
| `GetState` | `TStateCore GetState()` | The declared values / samplers / options of this segment. |

Every `Exit` / `Pause` / `Resume` / `SetRate` / `Seek` / query has a matching static on `TransitionCore`, addressed by target: `Transition.Exit(rect)`, `Transition.Pause(rect)`, `Transition.Seek(rect, cycle, TimeSpan.Zero)`, `Transition.IsPaused(rect)`. There are **no** snapshot/capture extensions on any adapter, and no `Snapshot*` family of methods: animated state is declared explicitly, path by path. To reset an object, declare its initial values as a transition and play them under `TransitionEffects.Empty` (see [QuickStart — Declare State Explicitly](../../../../1_QuickStart/03_transition/03_declare-state/index.md)).

### Class: `Transition<T>.Property` — overloads

Every `Property` overload follows the same shape and declares a target value (and, when given, an `interpolationOptions`) in the builder's state:

```csharp
public Transition<T> Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null);
```

**Notes:**
- The generic overload accepts any value type. Razor is the one adapter that does **not** declare it — it offers only typed overloads. Sampling for a declared property only runs when `InterpolatorCore.Prepare` can resolve an `ISampler` for its type (custom override → registry → struct `ISampleable`), otherwise that property is skipped (and reported through the effect's `Warn`). A reference-type leaf for which nothing resolves is rejected up front by `Execute` (`TransitionPathUnsampleableException`), and declaring both a path and one of its sub-leaves throws `TransitionPathConflictException` while building.
- Typed convenience overloads mirror the same signature for the engine value types — `int`, `double`, `float`, `decimal`, `System.Drawing.{Point, PointF, Size, SizeF, Color, Rectangle, RectangleF}`, and (when not compiled for `netstandard2.0`) `System.Numerics.{Vector2, Vector3, Vector4, Quaternion}`. Jalium is the exception here: it has only `int`, `float` and `double` typed overloads (it does declare the generic overload).
- Transform overloads take a collection (`ICollection<Transform>`; Avalonia also has a single `ITransform?` form). A single transform is assigned directly to preserve its runtime type — wrapping it in a group would break nested property paths such as `((TranslateTransform)x.RenderTransform).X`. Multiple transforms are wrapped in a group (`TransformGroup`).
- Platform-specific typed overloads (each also carrying `object? interpolationOptions = null` unless noted):

| Adapter | Platform value-type overloads (beyond the engine types above) |
|---|---|
| WPF | `Brush?`, `Transform?` (collection), `Point`, `CornerRadius`, `Thickness`, `Size`, `Rect`, `Vector`, `Color`, `DropShadowEffect?`, `Point3D`, `Vector3D` |
| Avalonia | `IBrush?`, `ITransform?` (single or `ICollection<Transform>`), `Point`, `CornerRadius`, `Thickness`, `Size`, `PixelPoint`, `PixelSize`, `PixelRect`, `RelativePoint`, `RelativeRect`, `Color`, `BoxShadows` |
| WinUI | `Brush?`, `Transform?` (collection), `Point`, `CornerRadius`, `Thickness`, `Projection?`, `Size`, `Rect`, `GridLength`, `Color` |
| MAUI | `Brush?`, `Transform?` (collection — **no** `interpolationOptions` parameter), `Point`, `PointF`, `CornerRadius`, `Thickness`, `Color?`, `Size`, `SizeF`, `Rect`, `RectF`, `Shadow?` |
| WinForms | `Padding` |
| Razor | `string?` |
| Jalium | `Brush?`, `Transform?` (collection), `Point`, `CornerRadius`, `Thickness`, `Size`, `Rect`, `Color`, `Transform3D?` (`Jalium.UI.Media.Media3D.Transform3D`) |

### Minimal usage (from the WPF demo)

```csharp
using VeloxDev.TransitionSystem;

var animation = Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 0)
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 200d)
    .Effect(new TransitionEffect()
    {
        Duration = TimeSpan.FromSeconds(2),
        IsAutoReverse = true,
        LoopTime = 2,
    });

animation.Execute(Rec0);                        // mutual: interrupts a running animation
animation.Execute(Rec0, CanMutualTask: false);  // concurrent

// A chain that repeats a whole two-segment loop three times over (Repeat on the last segment):
Transition<Rectangle>.Create()
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 200d)
    .Effect(new TransitionEffect { Duration = TimeSpan.FromSeconds(1) })
    .AwaitThen(TimeSpan.FromMilliseconds(250))
    .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
    .Effect(new TransitionEffect { Duration = TimeSpan.FromMilliseconds(500) })
    .Repeat(2);
```

*Verified by:* `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` (`Animation0` / `Animation1` / `Animation2`, `LoadMainThread`, `LoadBackground`, `LoadMainThreadNonMutual`, `PauseAll`, `SeekNextPass`), `AUTO TEST` (`LoadModes_MatchTheLibrarySemantics`, `TimelineControl_SteersTheRunningAnimation`), `ChainRepeatTests`.
