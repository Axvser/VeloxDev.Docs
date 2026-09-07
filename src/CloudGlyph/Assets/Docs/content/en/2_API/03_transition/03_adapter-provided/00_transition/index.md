# Transition — Adapter: `Transition`, `Transition<T>`, `StateSnapshot`, `TransitionEx`

Every adapter assembly (`VeloxDev.WPF`, `VeloxDev.Avalonia`, `VeloxDev.Jalium`, `VeloxDev.WinUI`, `VeloxDev.MAUI`, `VeloxDev.WinForms`, `VeloxDev.Razor`) defines these types in `PlatformAdapters/Transition.cs` inside the `VeloxDev.TransitionSystem` namespace.

### Class: `Transition` / `Transition<T>` / nested `StateSnapshot`

```csharp
public class Transition : TransitionCore { }

public class Transition<T> : TransitionCore<T, Transition<T>.StateSnapshot>
{
    public class StateSnapshot : StateSnapshotCore<T, State, TransitionEffect, Interpolator,
        UIThreadInspector, TransitionInterpreter[, TPriorityCore]>
    {
        public StateSnapshot Effect(Action<TransitionEffect> effectSetter);
        public StateSnapshot Effect(TransitionEffect effect);
        public StateSnapshot Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null);
        // (typed Property overloads per platform type follow — see the next section)
    }
}
```

**Notes:**
- `Transition<T>.StateSnapshot` derives from the 6-generic `StateSnapshotCore` (MAUI, WinForms, Razor) or the 7-generic one with a `TPriorityCore` (WPF, Avalonia, Jalium → `DispatcherPriority`; WinUI → `DispatcherQueuePriority`), using the adapter's `State`, `TransitionEffect`, `Interpolator`, `UIThreadInspector` and `TransitionInterpreter`.
- Building starts with `Transition<T>.Create()` (inherited from `TransitionCore<TTarget, TStateSnapshotCore>.Create`), which marks the snapshot as the root of a chain. Segment linking uses the `TransitionCoreEx` extensions (`Await`, `Then`, `AwaitThen`) documented in [01_abstractions](../../01_abstractions/index.md); running uses `Execute` (`TransitionCoreEx` extension or the static `Transition<T>.Execute`), and cancelling uses `Transition.Exit(target, IncludeMutual: true, IncludeNoMutual: true)`.

#### Effect overloads

| Signature | Description |
|---|---|
| `StateSnapshot Effect(Action<TransitionEffect> effectSetter)` | Builds a fresh `TransitionEffect`, invokes the setter to configure it, and stores it as this segment's timing descriptor. |
| `StateSnapshot Effect(TransitionEffect effect)` | Uses the supplied effect as this segment's timing descriptor. |

### Class: `TransitionEx` (per adapter)

```csharp
public static class TransitionEx
{
    public static Transition<T>.StateSnapshot Snapshot<T>(this T target, params Expression<Func<T, object?>>[] expressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotAll<T>(this T target, params Expression<Func<T, object?>>[] extraExpressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotExcept<T>(this T target, params Expression<Func<T, object?>>[] excludedExpressions) where T : class;
}
```

**Notes:**
- `Snapshot` records exactly the given expression paths; `SnapshotAll` / `SnapshotExcept` record the discovered animatable surface (`TransitionSnapshotHelper.CaptureAll` / `CaptureAllExcept`) using `Interpolator.TryGetInterpolator(type, out _)` as the "can animate" predicate, then add / exclude the extra expressions.
- Used to capture a *reset* state (record current values, later write them back synchronously). *Verified by:* WPF demo — `Rec1.SnapshotAll()`, `Rec1.Snapshot(x => x.RenderTransform, x => x.Fill)`.

### Class: `Transition<T>.StateSnapshot` — `Property` overloads

Every `Property` overload follows the same shape and records a target value (and, when given, an `interpolationOptions`) into the snapshot state:

```csharp
public StateSnapshot Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null);
```

**Notes:**
- The generic overload accepts any value type. Sampling for a recorded property only runs when `Interpolator.Prepare` can resolve an `ISampler` for its type (custom override → registry → struct `ISampleable`), otherwise that property is skipped for the animation.
- Typed convenience overloads mirror the same signature for the engine value types — `int`, `double`, `float`, `decimal`, `System.Drawing.{Point, PointF, Size, SizeF, Color, Rectangle, RectangleF}`, and (when not compiled for `netstandard2.0`) `System.Numerics.{Vector2, Vector3, Vector4, Quaternion}`. These exist on every adapter **except Jalium**, which only has `int`, `float` and `double` typed overloads plus the generic one.
- Transform overloads take a collection (`ICollection<Transform>` / `ICollection<Transform>`; Avalonia also has a single `ITransform?` form). A single transform is assigned directly to preserve its runtime type — wrapping it in a group would break nested property paths such as `((TranslateTransform)x.RenderTransform).X`. Multiple transforms are wrapped in a group (`TransformGroup`).
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
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 800)
    .Effect(new TransitionEffect()
    {
        Duration = TimeSpan.FromSeconds(2),
        IsAutoReverse = true,
        LoopTime = 2,
    });

animation.Execute(Rec0);                     // mutual: interrupts a running animation
animation.Execute(Rec0, CanMutualTask: false);  // concurrent
```

*Verified by:* `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` (`Animation0` / `Animation1` / `Animation2`, `LoadMainThread`, `LoadBackground`, `LoadMainThreadNonMutual`).
