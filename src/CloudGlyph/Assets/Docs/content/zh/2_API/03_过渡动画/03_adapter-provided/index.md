# Transition — 命名空间：`VeloxDev.TransitionSystem`（适配器提供）

### 静态类：`TransitionEx`（按适配器）

```csharp
public static class TransitionEx
{
    public static Transition<T>.StateSnapshot Snapshot<T>(this T target, params Expression<Func<T, object?>>[] expressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotAll<T>(this T target, params Expression<Func<T, object?>>[] extraExpressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotExcept<T>(this T target, params Expression<Func<T, object?>>[] excludedExpressions) where T : class;
}
```

**说明：** `SnapshotAll`/`SnapshotExcept` 以 `Interpolator.TryGetInterpolator(type, out _)` 作为「可动画」判定（默认 `maxDepth = 4`）。
**验证依据：** WPF 示例 `Rec0.SnapshotAll()` / `Rec1.Snapshot(x => x.RenderTransform, x => x.Fill)`。

### 类：`Transition` / `Transition<T>`（按适配器）

非泛型 `Transition : TransitionCore` 与 `Transition<T> : TransitionCore<T, Transition<T>.StateSnapshot>` 是适配器子类。`Transition<T>.StateSnapshot` 派生自 6 或 7 泛型元数的 `StateSnapshotCore`，使用适配器的 `State`、`TransitionEffect`、`Interpolator`、`UIThreadInspector` 与 `TransitionInterpreter`。

### 类：`StateSnapshot` — `.Property(...)` 重载集（按适配器）

每个重载：`StateSnapshot Property(Expression<Func<T, X>>, X newValue, object? interpolationOptions = null)`。

| 适配器 | 优先级类型 | 额外重载 | 缺失 |
|---|---|---|---|
| WPF | `DispatcherPriority` | `IInterpolable?`、`Brush?`、`Transform?`（集合）、`Point`、`CornerRadius`、`Thickness`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect?`、`Point3D`、`Vector3D` | — |
| Avalonia | `DispatcherPriority` | `IInterpolable?`、`ITransform?`、`IBrush?`、`Thickness`、`Point`、`CornerRadius`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows` | — |
| WinUI | `DispatcherQueuePriority` | `IInterpolable?`、`Brush?`、`Transform?`、`Point`、`CornerRadius`、`Thickness`、`Projection?`、`Size`、`Rect`、`GridLength`、`Color` | — |
| MAUI | 无 | `IInterpolable?`、`Brush?`、`Transform?`、`Point`、`PointF`、`CornerRadius`、`Thickness`、`Color?`、`Size`、`SizeF`、`Rect`、`RectF`、`Shadow?` | `Transform?` 无 `interpolationOptions` |
| WinForms | 无 | `IInterpolable?`、`Padding` | — |
| Razor | 无 | `string?` | 无 `IInterpolable?`；有 `string?` |

所有适配器共有重载：`int`、`double`、`float`、`decimal`、`System.Drawing.*`、以及（非 netstandard2.0）`System.Numerics.*`。

### 平台特定类型

- **`UIThreadInspector`** — WPF：目标优先的 `DispatcherObject.Dispatcher` 再 `Application.Current.Dispatcher`，优先级 `DispatcherPriority`；Avalonia：`Dispatcher.UIThread`；WinUI：`DependencyObject.DispatcherQueue` 自动编组 + 可选 `CaptureUIThread()`；MAUI：`Application.Current.Dispatcher.Dispatch`；WinForms/Razor：`Control`/`SynchronizationContext` + 可选 `CaptureUIThread()`。
- **`Interpolator`** 静态构造函数注册平台类型（WPF：`Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect`、`Point3D`、`Vector3D`；Avalonia：`IBrush`、`ITransform`、`BoxShadows`、`GridLength`...；WinUI：`Projection`、`GridLength`...；MAUI：`Shadow`、`RectF`...；WinForms：`Padding`；Razor：`string` → `StringInterpolator`）。
- **`TransitionEffects`** — 静态预设：`Empty`（0 秒）、`Theme`（0.46 秒）、`Hover`（0.32 秒）。**注意：** WinUI 的 `TransitionEffects` 是**非静态**类。
