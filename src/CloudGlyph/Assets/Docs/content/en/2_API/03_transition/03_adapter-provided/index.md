# Transition — Namespace: `VeloxDev.TransitionSystem` (adapter-provided)

### Static Class: `TransitionEx` (per adapter)

```csharp
public static class TransitionEx
{
    public static Transition<T>.StateSnapshot Snapshot<T>(this T target, params Expression<Func<T, object?>>[] expressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotAll<T>(this T target, params Expression<Func<T, object?>>[] extraExpressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotExcept<T>(this T target, params Expression<Func<T, object?>>[] excludedExpressions) where T : class;
}
```

**Notes:** `SnapshotAll`/`SnapshotExcept` use `Interpolator.TryGetInterpolator(type, out _)` as the "can animate" predicate (default `maxDepth = 4`).
**Verified by:** WPF demo `Rec0.SnapshotAll()` / `Rec1.Snapshot(x => x.RenderTransform, x => x.Fill)`.

### Class: `Transition` / `Transition<T>` (per adapter)

The non-generic `Transition : TransitionCore` and `Transition<T> : TransitionCore<T, Transition<T>.StateSnapshot>` are adapter subclasses. `Transition<T>.StateSnapshot` derives from the 6- or 7-generic `StateSnapshotCore` using the adapter's `State`, `TransitionEffect`, `Interpolator`, `UIThreadInspector`, and `TransitionInterpreter`.

### Class: `StateSnapshot` — `.Property(...)` overload set (per adapter)

Each overload: `StateSnapshot Property(Expression<Func<T, X>>, X newValue, object? interpolationOptions = null)`.

| Adapter | Priority type | Extra overloads | Notable absence |
|---|---|---|---|
| WPF | `DispatcherPriority` | `Brush?`, `Transform?` (collection), `Point`, `CornerRadius`, `Thickness`, `Size`, `Rect`, `Vector`, `Color`, `DropShadowEffect?`, `Point3D`, `Vector3D` | — |
| Avalonia | `DispatcherPriority` | `ITransform?`, `IBrush?`, `Thickness`, `Point`, `CornerRadius`, `Size`, `PixelPoint`, `PixelSize`, `PixelRect`, `RelativePoint`, `RelativeRect`, `Color`, `BoxShadows` | — |
| WinUI | `DispatcherQueuePriority` | `Brush?`, `Transform?`, `Point`, `CornerRadius`, `Thickness`, `Projection?`, `Size`, `Rect`, `GridLength`, `Color` | — |
| MAUI | none | `Brush?`, `Transform?`, `Point`, `PointF`, `CornerRadius`, `Thickness`, `Color?`, `Size`, `SizeF`, `Rect`, `RectF`, `Shadow?` | no `interpolationOptions` on `Transform?` |
| WinForms | none | `Padding` | — |
| Razor | none | `string?` | — |

**Notes:** The old `IInterpolable?` overload is replaced by a generic `Property<TValue>(Expression<Func<T, TValue>>, TValue newValue, object? interpolationOptions = null)` that accepts any animatable type (including custom types that implement `ISampleable` or are backed by a registered `ISampleable`). Adapter samplers implement `ISampleable, ISampler`; WPF/Jalium reference-type targets (`SolidColorBrush`, `Transform`, `DropShadowEffect`) mutate the live `start` instance in place inside `Update` when possible (else compute-and-assign), rather than allocating new objects per frame.

Common overloads across all adapters: `int`, `double`, `float`, `decimal`, `System.Drawing.*`, and (non-netstandard2.0) `System.Numerics.*`.

### Platform-specific types

- **`UIThreadInspector`** — WPF: target-first `DispatcherObject.Dispatcher` then `Application.Current.Dispatcher`, priority `DispatcherPriority`; Avalonia: `Dispatcher.UIThread`; WinUI: `DependencyObject.DispatcherQueue` auto-marshalling + optional `CaptureUIThread()`; MAUI: `Application.Current.Dispatcher.Dispatch`; WinForms/Razor: `Control`/`SynchronizationContext` + optional `CaptureUIThread()`.
- **`Interpolator`** static ctor registers platform types (WPF: `Brush`, `Thickness`, `Point`, `CornerRadius`, `Transform`, `Size`, `Rect`, `Vector`, `Color`, `DropShadowEffect`, `Point3D`, `Vector3D`; Avalonia: `IBrush`, `ITransform`, `BoxShadows`, `GridLength`, ...; WinUI: `Projection`, `GridLength`, ...; MAUI: `Shadow`, `RectF`, ...; WinForms: `Padding`; Razor: `string` → `StringSampler`).
- **`TransitionEffects`** — static presets: `Empty` (0 s), `Theme` (0.46 s), `Hover` (0.32 s). **Note:** WinUI's `TransitionEffects` is a **non-static** class.
