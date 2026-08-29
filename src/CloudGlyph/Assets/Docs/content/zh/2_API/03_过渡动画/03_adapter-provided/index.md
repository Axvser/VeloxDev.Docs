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
| WPF | `DispatcherPriority` | `Brush?`、`Transform?`（集合）、`Point`、`CornerRadius`、`Thickness`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect?`、`Point3D`、`Vector3D` | — |
| Avalonia | `DispatcherPriority` | `ITransform?`、`IBrush?`、`Thickness`、`Point`、`CornerRadius`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows` | — |
| WinUI | `DispatcherQueuePriority` | `Brush?`、`Transform?`、`Point`、`CornerRadius`、`Thickness`、`Projection?`、`Size`、`Rect`、`GridLength`、`Color` | — |
| MAUI | 无 | `Brush?`、`Transform?`、`Point`、`PointF`、`CornerRadius`、`Thickness`、`Color?`、`Size`、`SizeF`、`Rect`、`RectF`、`Shadow?` | `Transform?` 无 `interpolationOptions` |
| WinForms | 无 | `Padding` | — |
| Razor | 无 | `string?` | — |

**说明：** 旧的 `IInterpolable?` 重载已被泛型 `Property<TValue>(Expression<Func<T, TValue>>, TValue newValue, object? interpolationOptions = null)` 取代——它接受任何可动画类型（包括实现 `ISampleable` 的自定义类型）。适配器采样器实现 `ISampleable, ISampler`（`Normalize => this` + `Update`）；WPF/Jalium 引用类型目标（`SolidColorBrush`、`Transform`、`DropShadowEffect`）在 `Update` 内**原地修改** `start` 现有实例（不 new），否则走计算路径。

所有适配器共有重载：`int`、`double`、`float`、`decimal`、`System.Drawing.*`、以及（非 netstandard2.0）`System.Numerics.*`。

### 平台特定类型

- **`UIThreadInspector`** — WPF：目标优先的 `DispatcherObject.Dispatcher` 再 `Application.Current.Dispatcher`，优先级 `DispatcherPriority`；Avalonia：`Dispatcher.UIThread`；WinUI：`DependencyObject.DispatcherQueue` 自动编组 + 可选 `CaptureUIThread()`；MAUI：`Application.Current.Dispatcher.Dispatch`；WinForms/Razor：`Control`/`SynchronizationContext` + 可选 `CaptureUIThread()`。
- **`Interpolator`** 静态构造函数注册平台采样器（WPF：`Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect`、`Point3D`、`Vector3D`；Avalonia：`IBrush`、`ITransform`、`BoxShadows`、`GridLength`...；WinUI：`Projection`、`GridLength`...；MAUI：`Shadow`、`RectF`...；WinForms：`Padding`；Razor：`string` → `StringSampler`）。
- **`TransitionEffects`** — 静态预设：`Empty`（0 秒）、`Theme`（0.46 秒）、`Hover`（0.32 秒）。**注意：** WinUI 的 `TransitionEffects` 是**非静态**类。
