# 过渡动画系统 — 快速入门

本指南让你用**过渡动画系统**（VeloxDev 的跨平台、代码驱动插值引擎）驱动 UI 属性动画。核心理念是**「一切皆状态」**：将目标的属性值记录为*状态快照*，描述对象应到达的最终状态，然后执行 —— 引擎会把每个记录的属性从当前值插值到目标值，经过一条定时、带缓动、按帧的时间线。

> 示例源码：`Examples/Transition/{WPF, Avalonia, WinUI, WinForms, MAUI, Blazor}/Demo`

## 1. 安装 / 添加依赖

为你的 GUI 框架添加适配器包 —— 它包含过渡引擎与平台插值器：

```bash
# WPF
dotnet add package VeloxDev.WPF

# Avalonia
dotnet add package VeloxDev.Avalonia

# 亦支持 WinUI / MAUI / WinForms / Razor
```

## 2. 基本设置 / 注册

**第 1 步 — 使用 `Transition<T>.Create()` 创建状态快照**并记录目标属性值。属性 lambda 可以是**嵌套路径**（如 `r => ((TranslateTransform)r.RenderTransform).X`）：

```csharp
using VeloxDev.TransitionSystem;

// 流式构建器：记录目标值 + 效果，然后执行
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

**第 2 步 — 平台接线（仅部分平台需要）：**

- WPF / Avalonia：无需接线 —— 甚至可以从后台线程启动动画，适配器的 `UIThreadInspector` 会把更新调度回 UI 线程。
- WinUI：**必需** —— 调用一次 `UIThreadInspector.SetWindow(this);`，且不要在非 UI 线程上创建 `Transition<T>` 静态字段。
- WinForms / Razor：**必需** —— 在 UI 线程调用 `UIThreadInspector.CaptureUIThread();`（WinForms 在 `OnLoad`；Razor 在 `OnInitialized`）。

## 3. 核心用法（逐步）

**执行快照** —— 默认一个对象同时只允许一个动画（`CanMutualTask: true`，新动画会打断正在执行的）。传 `CanMutualTask: false` 可并行：

```csharp
Animation0.Execute(Rec0);                 // 默认：互斥
Animation0.Execute(Rec0, CanMutualTask: false);

// 也可在非 UI 线程启动
_ = Task.Run(() =>
{
    Animation0.Execute(Rec0);
    Animation1.Execute(Rec1);
    Animation2.Execute(Rec2);
});
```

**拼接多段动画** — 使用 `.Await`、`.Then`、`.AwaitThen`，每段可有独立效果与缓动：

```csharp
private static readonly Transition<Rectangle>.StateSnapshot Animation2 =
    Transition<Rectangle>.Create()
        .Property(r => r.RenderTransform,
        [
            new TranslateTransform(200, 0),
            new ScaleTransform(1.3, 1.3)
        ])
        .Effect(new TransitionEffect()
        {
            Duration = TimeSpan.FromSeconds(2),
            IsAutoReverse = true,
            FPS = 144,
            Ease = Eases.Circ.InOut,
            LoopTime = 2,
        })
        .AwaitThen(TimeSpan.FromSeconds(5)) // 等待 5 秒再开始下一段
        .Property(r => r.Fill, new SolidColorBrush(Colors.Yellow))
        .Effect(new TransitionEffect()
        {
            Duration = TimeSpan.FromSeconds(2),
            Ease = Eases.Sine.In
        });
```

**捕获实时快照**（记录对象*当前*值，用于重置/撤销）：

```csharp
var snapshot0 = Rec0.SnapshotAll();                                    // 所有可动画属性
var snapshot1 = Rec0.Snapshot(x => x.RenderTransform, x => x.Fill);    // 指定属性
var snapshot2 = Rec0.SnapshotExcept(x => x.Visibility);                // 排除某些属性

// 将对象立即恢复到捕获的状态
btnReset.Click += (s, e) => snapshot1.Effect(TransitionEffects.Empty).Execute(Rec0);
```

**停止动画**：

```csharp
// IncludeMutual   -> 停止 CanMutualTask: true 的动画
// IncludeNoMutual -> 停止 CanMutualTask: false 的动画
Transition.Exit(Rec0, IncludeMutual: true, IncludeNoMutual: false);
Transition.Exit(Rec1);
```

## 4. 验证

运行应用：

- `Rec0` 在 2 秒内动画透明度、位置与填充色，然后自动往返两次（`IsAutoReverse + LoopTime: 2`）。
- 多段 `Animation2` 先位移+缩放，等待 5 秒，再以不同缓动动画填充色。
- 重置按钮将 `Rec1` 立即恢复到捕获状态。
- 打断按钮调用 `Transition.Exit(...)`，矩形就地停止。
- 六个平台示例（WPF、Avalonia、WinUI、WinForms、MAUI、Blazor）运行相同的动画定义 —— Blazor 示例动画一个普通 `BoxModel` 视图模型，通过 `INotifyPropertyChanged` 触发重渲染。

## 5. 完整代码

一个最小化的 WPF 窗口动画一个矩形：

```csharp
public partial class MainWindow : Window
{
    private static readonly Transition<Rectangle>.StateSnapshot Animation0 =
        Transition<Rectangle>.Create()
            .Property(r => r.Opacity, 0)
            .Property(r => ((TranslateTransform)r.RenderTransform).X, 800)
            .Effect(new TransitionEffect()
            {
                Duration = TimeSpan.FromSeconds(2),
                IsAutoReverse = true,
                LoopTime = 2,
                Ease = Eases.Sine.InOut,
            });

    public MainWindow()
    {
        InitializeComponent();
        Loaded += (s, e) => Animation0.Execute(Rec0);
        btnExit.Click += (s, e) => Transition.Exit(Rec0);
    }
}
```

> **提示：** Razor 适配器额外提供 `string?` 的 `Property` 重载，可动画 CSS 颜色字符串（`"#ff7043"`、`rgb(...)`、命名颜色）。WinForms 动画 `IInterpolable`、`Padding` 及常用数值类型；MAUI 动画 MAUI 类型（`Brush`、`Shadow`、`PointF`、`RectF`...）。
