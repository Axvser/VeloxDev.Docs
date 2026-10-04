# 过渡动画 — 适配器：`Transition`、`Transition<T>`

每个适配器程序集（`VeloxDev.WPF`、`VeloxDev.Avalonia`、`VeloxDev.Jalium`、`VeloxDev.WinUI`、`VeloxDev.MAUI`、`VeloxDev.WinForms`、`VeloxDev.Razor`）在 `VeloxDev.TransitionSystem` 命名空间的 `PlatformAdapters/Transition.cs` 中定义这些类型。

### 类：`Transition` / `Transition<T>`

`Transition<T>` 集静态入口、流式构建器与执行器于一身 —— 没有嵌套的 `StateSnapshot` 类：

```csharp
public class Transition : TransitionCore { }

public class Transition<T> : TransitionCore<
    T,
    State,
    TransitionEffect,
    Interpolator,
    UIThreadInspector,          // 适配器的 ITransitionHost<TPriorityCore>
    TransitionInterpreter,
    TPriorityCore>              // DispatcherPriority / DispatcherQueuePriority / NonPriority
    where T : class
{
    public static Transition<T> Create();

    public Transition<T> Effect(Action<TransitionEffect> effectSetter);
    public Transition<T> Effect(TransitionEffect effect);
    public Transition<T> Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null);  // 除 Razor 外每个适配器都有
    // 各平台类型的带类型 Property 重载随后 —— 见下一节
}
```

**说明：**
- `Transition<T>` 派生自单一种元数的 `TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, TPriorityCore>`，使用适配器的 `State`、`TransitionEffect`、`Interpolator`、`UIThreadInspector` 与 `TransitionInterpreter`。第 5 个类型实参是**宿主** —— 适配器的 `UIThreadInspector`，一个 `TransitionHostBase<TPriorityCore>` —— 而第 7 个是宿主的调度器优先级：`DispatcherPriority`（WPF、Avalonia、Jalium）、`DispatcherQueuePriority`（WinUI）或 `NonPriority`（MAUI、WinForms、Razor）。
- 构建从 `Transition<T>.Create()` 开始，它把构建器标记为链的根。`Execute(...)` / 控制方法 / `GetState()` 来自 `StateSnapshotCore<T>` 基类，分段链接用 Core 的 `TransitionCoreEx` 扩展（`Await`、`Then`、`AwaitThen`、`Repeat`、`Interpolator`），记于 [abstractions](../../01_abstractions/index.md)。非泛型 `Transition` 只承载 `TransitionCore` 的静态入口。

#### Effect 重载

| 签名 | 说明 |
|---|---|
| `Transition<T> Effect(Action<TransitionEffect> effectSetter)` | 新建一个 `TransitionEffect`，调用 setter 配置它，存为本段的时间描述符。 |
| `Transition<T> Effect(TransitionEffect effect)` | 用给定 effect 作为本段的时间描述符。 |

### 执行与控制

`Execute` 不是扩展 —— 它是基链的成员，因此每个 `Transition<T>` 实例都有它。控制方法与四个查询同理：

| 成员 | 签名 | 说明 |
|---|---|---|
| `Execute` | `void Execute(T target, bool CanMutualTask = true)` | 在 `target` 上跑本构建器链。`true`（默认）用目标的*互斥*调度器，会取消正在运行的互斥动画；`false` 在全新的非互斥调度器上并发运行。 |
| `Execute`（共享时间轴） | `void Execute(T target, ITimeSourceControl timeline, bool CanMutualTask = true)` | 把链锚定在调用方提供的时间轴上。共享时间轴的动画共享一套传输：暂停、变速或定位其中一个会一起移动全部，而每一个保留自己的趟与位置。 |
| `Execute`（静态批） | `static void Execute(T target, IEnumerable<Transition<T>> values, bool CanMutualTask = false)` | 在 `target` 上跑批中每个构建器；默认非互斥。 |
| `Exit` / `Pause` / `Resume` | `void Exit/Pause/Resume(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 停止 / 冻结 / 解冻目标的运行中动画。 |
| `SetRate` | `void SetRate(T target, double rate, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 改变播放速率而不移动位置；`0` 冻结但不暂停；负速率被拒绝。 |
| `Seek` | `void Seek(T target, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false)` 与 `void Seek(T target, int cycle, TimeSpan position, …)` | 在当前趟内移动，或移入编号趟。 |
| `IsPaused` / `Position` / `Cycle` / `Rate` | `… (T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 四个查询；每个对无运行给出答案而非抛异常。 |
| `Exit`（非泛型 `Transition` 上的静态） | `static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | 同上，不必有 `Transition<T>` 实例 —— `Pause`、`Resume`、`SetRate`、`Seek`、`IsPaused`、`Position`、`Cycle`、`Rate` 亦然。 |
| `GetState` | `TStateCore GetState()` | 本段已声明的值 / 采样器 / 选项。 |

`Exit` / `Pause` / `Resume` / `SetRate` / `Seek` / 查询各有一个 `TransitionCore` 上的静态版本，按目标寻址：`Transition.Exit(rect)`、`Transition.Pause(rect)`、`Transition.Seek(rect, cycle, TimeSpan.Zero)`、`Transition.IsPaused(rect)`。任何适配器都**没有**快照 / 捕获扩展，也没有 `Snapshot*` 一族方法：动画状态逐路径显式声明。要重置一个对象，把它的初始值声明成一次过渡并配 `TransitionEffects.Empty` 播放（见 [快速开始 —— 显式声明状态](../../../../1_快速开始/03_过渡动画/03_声明状态/index.md)）。

### 类：`Transition<T>.Property` —— 重载

所有 `Property` 重载形状一致，在构建器的 state 中声明一个目标值（以及在给出时的一个 `interpolationOptions`）：

```csharp
public Transition<T> Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null);
```

**说明：**
- 泛型重载接受任意值类型。Razor 是唯一**没有**声明它的适配器 —— 它只提供带类型重载。某个已声明属性只有在 `InterpolatorCore.Prepare` 能为其类型解析出 `ISampler`（自定义覆盖 → 注册表 → 结构体 `ISampleable`）时才会被采样，否则该属性被跳过（并经 effect 的 `Warn` 报出）。什么都没解析到的引用类型末端会被 `Execute` 事先拒绝（`TransitionPathUnsampleableException`），而同时声明一条路径与它的某个子叶会在构建时抛 `TransitionPathConflictException`。
- 带类型的便捷重载对引擎值类型形状相同 —— `int`、`double`、`float`、`decimal`、`System.Drawing.{Point, PointF, Size, SizeF, Color, Rectangle, RectangleF}`，以及（非 `netstandard2.0` 编译时）`System.Numerics.{Vector2, Vector3, Vector4, Quaternion}`。这里 Jalium 是例外：它只有 `int`、`float`、`double` 三个带类型重载（它确实声明了泛型重载）。
- 变换重载接收集合（`ICollection<Transform>`；Avalonia 另有单个 `ITransform?` 形式）。单个变换直接赋值以保留运行时类型 —— 包成组会破坏 `((TranslateTransform)x.RenderTransform).X` 这类嵌套路径。多个变换会被包进一个组（`TransformGroup`）。
- 平台专属带类型重载（除注明外均另带 `object? interpolationOptions = null`）：

| 适配器 | 平台值类型重载（在上表引擎类型之外） |
|---|---|
| WPF | `Brush?`、`Transform?`（集合）、`Point`、`CornerRadius`、`Thickness`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect?`、`Point3D`、`Vector3D` |
| Avalonia | `IBrush?`、`ITransform?`（单个或 `ICollection<Transform>`）、`Point`、`CornerRadius`、`Thickness`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows` |
| WinUI | `Brush?`、`Transform?`（集合）、`Point`、`CornerRadius`、`Thickness`、`Projection?`、`Size`、`Rect`、`GridLength`、`Color` |
| MAUI | `Brush?`、`Transform?`（集合 —— **没有** `interpolationOptions` 形参）、`Point`、`PointF`、`CornerRadius`、`Thickness`、`Color?`、`Size`、`SizeF`、`Rect`、`RectF`、`Shadow?` |
| WinForms | `Padding` |
| Razor | `string?` |
| Jalium | `Brush?`、`Transform?`（集合）、`Point`、`CornerRadius`、`Thickness`、`Size`、`Rect`、`Color`、`Transform3D?`（`Jalium.UI.Media.Media3D.Transform3D`） |

### 最小用法（取自 WPF 演示）

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

animation.Execute(Rec0);                        // 互斥：打断正在运行的动画
animation.Execute(Rec0, CanMutualTask: false);  // 并发

// 一条整链重复三轮的两段循环（Repeat 写在末段上）：
Transition<Rectangle>.Create()
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 200d)
    .Effect(new TransitionEffect { Duration = TimeSpan.FromSeconds(1) })
    .AwaitThen(TimeSpan.FromMilliseconds(250))
    .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
    .Effect(new TransitionEffect { Duration = TimeSpan.FromMilliseconds(500) })
    .Repeat(2);
```

*核验：* `Examples/Transition/WPF/Demo/MainWindow.xaml.cs`（`Animation0` / `Animation1` / `Animation2`、`LoadMainThread`、`LoadBackground`、`LoadMainThreadNonMutual`、`PauseAll`、`SeekNextPass`），`AUTO TEST`（`LoadModes_MatchTheLibrarySemantics`、`TimelineControl_SteersTheRunningAnimation`），`ChainRepeatTests`。
