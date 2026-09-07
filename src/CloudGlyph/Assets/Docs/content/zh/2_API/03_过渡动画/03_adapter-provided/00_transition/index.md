# Transition — 适配器：`Transition`、`Transition<T>`、`StateSnapshot`、`TransitionEx`

每个适配器程序集（`VeloxDev.WPF`、`VeloxDev.Avalonia`、`VeloxDev.Jalium`、`VeloxDev.WinUI`、`VeloxDev.MAUI`、`VeloxDev.WinForms`、`VeloxDev.Razor`）在 `PlatformAdapters/Transition.cs`（位于 `VeloxDev.TransitionSystem` 命名空间）中定义这些类型。

### 类：`Transition` / `Transition<T>` / 嵌套 `StateSnapshot`

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
        // （平台类型的类型化 Property 重载见下节）
    }
}
```

**说明：**
- `Transition<T>.StateSnapshot` 派生自 6 泛型元数 `StateSnapshotCore`（MAUI、WinForms、Razor）或带 `TPriorityCore` 的 7 泛型元数版本（WPF、Avalonia、Jalium → `DispatcherPriority`；WinUI → `DispatcherQueuePriority`），使用适配器的 `State`、`TransitionEffect`、`Interpolator`、`UIThreadInspector` 与 `TransitionInterpreter`。
- 构建以 `Transition<T>.Create()`（继承自 `TransitionCore<TTarget, TStateSnapshotCore>.Create`）开始，它把快照标记为链的根。分段链接用 [01_abstractions](../../01_abstractions/index.md) 记录的 `TransitionCoreEx` 扩展（`Await`、`Then`、`AwaitThen`）；运行用 `Execute`（`TransitionCoreEx` 扩展或静态 `Transition<T>.Execute`）；取消用 `Transition.Exit(target, IncludeMutual: true, IncludeNoMutual: true)`。

#### Effect 重载

| 签名 | 说明 |
|---|---|
| `StateSnapshot Effect(Action<TransitionEffect> effectSetter)` | 构造新 `TransitionEffect`、调用 setter 配置它、把它存为本段时序描述符。 |
| `StateSnapshot Effect(TransitionEffect effect)` | 使用给定效果作为本段时序描述符。 |

### 类：`TransitionEx`（各适配器）

```csharp
public static class TransitionEx
{
    public static Transition<T>.StateSnapshot Snapshot<T>(this T target, params Expression<Func<T, object?>>[] expressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotAll<T>(this T target, params Expression<Func<T, object?>>[] extraExpressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotExcept<T>(this T target, params Expression<Func<T, object?>>[] excludedExpressions) where T : class;
}
```

**说明：**
- `Snapshot` 只记录给定的表达式路径；`SnapshotAll` / `SnapshotExcept` 记录发现出的可动画表面（`TransitionSnapshotHelper.CaptureAll` / `CaptureAllExcept`），以 `Interpolator.TryGetInterpolator(type, out _)` 作为「可动画」判定，再添加 / 排除额外表达式。
- 用于捕获*重置*状态（记录当前值，之后同步写回）。*验证依据：* WPF 示例——`Rec1.SnapshotAll()`、`Rec1.Snapshot(x => x.RenderTransform, x => x.Fill)`。

### 类：`Transition<T>.StateSnapshot` — `Property` 重载

每个 `Property` 重载遵循同一形态，把目标值（以及给出时的 `interpolationOptions`）记录进快照状态：

```csharp
public StateSnapshot Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null);
```

**说明：**
- 泛型重载接受任何值类型。某属性的采样只有当 `Interpolator.Prepare` 能为它的类型解析出 `ISampler`（自定义覆盖 → 注册表 → 结构体 `ISampleable`）时才会运行，否则该属性在动画中被跳过。
- 类型化便捷重载对引擎值类型镜像同一签名——`int`、`double`、`float`、`decimal`、`System.Drawing.{Point, PointF, Size, SizeF, Color, Rectangle, RectangleF}`，以及（非 `netstandard2.0` 编译时）`System.Numerics.{Vector2, Vector3, Vector4, Quaternion}`。除 **Jalium** 外每个适配器都有这些；Jalium 只有 `int`、`float`、`double` 类型化重载外加泛型重载。
- 变换重载接受集合（`ICollection<Transform>`；Avalonia 另有单一 `ITransform?` 形式）。单一变换直接赋值以保留其运行时类型——包进组会破坏嵌套属性路径（如 `((TranslateTransform)x.RenderTransform).X`）；多个变换才被包进组（`TransformGroup`）。
- 平台特定类型化重载（除注明外均带 `object? interpolationOptions = null`）：

| 适配器 | 平台值类型重载（引擎类型之外） |
|---|---|
| WPF | `Brush?`、`Transform?`（集合）、`Point`、`CornerRadius`、`Thickness`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect?`、`Point3D`、`Vector3D` |
| Avalonia | `IBrush?`、`ITransform?`（单一或 `ICollection<Transform>`）、`Point`、`CornerRadius`、`Thickness`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows` |
| WinUI | `Brush?`、`Transform?`（集合）、`Point`、`CornerRadius`、`Thickness`、`Projection?`、`Size`、`Rect`、`GridLength`、`Color` |
| MAUI | `Brush?`、`Transform?`（集合——**无** `interpolationOptions` 参数）、`Point`、`PointF`、`CornerRadius`、`Thickness`、`Color?`、`Size`、`SizeF`、`Rect`、`RectF`、`Shadow?` |
| WinForms | `Padding` |
| Razor | `string?` |
| Jalium | `Brush?`、`Transform?`（集合）、`Point`、`CornerRadius`、`Thickness`、`Size`、`Rect`、`Color`、`Transform3D?`（`Jalium.UI.Media.Media3D.Transform3D`） |

### 最小用法（取自 WPF 示例）

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

animation.Execute(Rec0);                     // 互斥：打断正在运行的动画
animation.Execute(Rec0, CanMutualTask: false);  // 并发
```

*验证依据：* `Examples/Transition/WPF/Demo/MainWindow.xaml.cs`（`Animation0` / `Animation1` / `Animation2`、`LoadMainThread`、`LoadBackground`、`LoadMainThreadNonMutual`）。
