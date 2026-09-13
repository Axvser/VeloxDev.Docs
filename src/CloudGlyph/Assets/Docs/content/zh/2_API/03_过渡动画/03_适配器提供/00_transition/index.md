# Transition — 适配器：`Transition`、`Transition<T>`

每个适配器程序集（`VeloxDev.WPF`、`VeloxDev.Avalonia`、`VeloxDev.Jalium`、`VeloxDev.WinUI`、`VeloxDev.MAUI`、`VeloxDev.WinForms`、`VeloxDev.Razor`）在 `PlatformAdapters/Transition.cs`（位于 `VeloxDev.TransitionSystem` 命名空间）中定义这些类型。

### 类：`Transition` / `Transition<T>`

```csharp
public class Transition : TransitionCore { }

public class Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator,
    UIThreadInspector, TransitionInterpreter, TPriorityCore>
    where T : class
{
    public static Transition<T> Create();

    public Transition<T> Effect(Action<TransitionEffect> effectSetter);
    public Transition<T> Effect(TransitionEffect effect);

    public Transition<T> Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null);
    // （平台类型的类型化 Property 重载见下节）
}
```

**说明：**
- **`Transition<T>` 本身就是构建器**，它没有嵌套的 `StateSnapshot` 类型。`Create()`（转发到 `TransitionCore.Create<Transition<T>>()`）新建一个实例并把它标记为链的根；每个 `Property` / `Effect` 调用返回同一个实例，因此可以流式串联。
- 泛型父类是**单一元数**：`TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, TPriorityCore>`。优先级类型 `TPriorityCore` 为 `DispatcherPriority`（WPF、Avalonia、Jalium）、`DispatcherQueuePriority`（WinUI）或 `NonPriority`（MAUI、WinForms、Razor —— 无 dispatcher 优先级），见 [abstractions](../../01_abstractions/index.md)。
- 分段链接用 `TransitionCoreEx` 扩展（`Await`、`Then`、`AwaitThen`、`Interpolator`）；运行用**实例方法** `Execute(target, CanMutualTask)`（继承自 `StateSnapshotCore<T>`，单次默认 `CanMutualTask: true`），或静态 `TransitionCore<...>.Execute(target, values, CanMutualTask: false)` 批量入口；取消用静态 `Transition.Exit(target, IncludeMutual: true, IncludeNoMutual: false)`。
- 运行动画可能同步抛 `TransitionPathConflictException`（父子路径冲突）或 `TransitionPathUnsampleableException`（路径永不可动画），见 [abstractions](../../01_abstractions/index.md)。

#### Effect 重载

| 签名 | 说明 |
|---|---|
| `Transition<T> Effect(Action<TransitionEffect> effectSetter)` | 构造新 `TransitionEffect`、调用 setter 配置它、把它存为本段时序描述符。 |
| `Transition<T> Effect(TransitionEffect effect)` | 使用给定效果作为本段时序描述符。 |

### 类：`Transition<T>` — `Property` 重载

每个 `Property` 重载遵循同一形态，把目标值（以及给出时的 `interpolationOptions`）记录进本段状态：

```csharp
public Transition<T> Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null);
```

**说明：**
- 泛型重载接受任何值类型。某属性的采样只有当 `InterpolatorCore.Prepare` 能为它的类型解析出 `ISampler`（自定义覆盖 → 注册表 → 值类型 `ISampleable`）时才会运行。解析不到时：叶子是**值类型**则该属性被跳过；叶子是**引用类型**则 `Execute` 同步抛 `TransitionPathUnsampleableException`（不再静默跳过）。
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

Transition<Rectangle> animation = Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 0)
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 800)
    .Effect(new TransitionEffect()
    {
        Duration = TimeSpan.FromSeconds(2),
        IsAutoReverse = true,
        LoopTime = 2,
    });

animation.Execute(Rec0);                        // 互斥：打断正在运行的动画
animation.Execute(Rec0, CanMutualTask: false);  // 并发
```

*验证依据：* `Examples/Transition/WPF/Demo/MainWindow.xaml.cs`（`Animation0` / `Animation1` / `Animation2`、`CreateResetRec0`、`LoadMainThread`、`LoadBackground`、`LoadMainThreadNonMutual`）。
