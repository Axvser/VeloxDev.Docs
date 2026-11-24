# 过渡动画

构建一个 WPF 窗口，让 `Rectangle` 以流畅的声明式动画平移并淡出，随后自动反向。同一组声明既可从 UI 线程执行，也可从后台线程执行；适配层会把每一帧切回调度器。

## 1. 前置条件

- **WPF 适配器支持的目标框架**（`Src/Adapters/VeloxDev.WPF/VeloxDev.WPF.csproj`）：`netframework4.6.1;net5.0-windows;netcoreapp3.0;net8.0-windows`。本示例使用 `net8.0-windows`。
- **`VeloxDev.WPF`** 会一并引入 `VeloxDev.Core`。Demo 以 .NET 9 构建；`net8.0-windows` 是该适配器线声明的下限。
- Windows 上 .NET SDK 8.0 或更高，并安装 Windows Desktop 工作负载。无需任何服务。

## 2. 安装/引入依赖

```text
dotnet new console -n TransitionQuickStart
cd TransitionQuickStart
dotnet add package VeloxDev.WPF --version 12.3.0
```

修改工程以启用 WPF：

```xml
<PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWPF>true</UseWPF>
</PropertyGroup>
```

**预期结果：** 包还原成功，工程以 WPF 可执行文件构建，`VeloxDev.TransitionSystem` 可以解析。

## 3. 基础配置/注册

一条过渡由若干属性声明加一个效果组成。`Transition<T>` 是平台类型；`Create()` 从空链开始。

```csharp
using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

var box = new Rectangle
{
    Width = 80,
    Height = 60,
    Fill = Brushes.Cyan,
    RenderTransform = new TranslateTransform()
};

var slide = Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 0.25d)
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 220d)
    .Effect(new TransitionEffect
    {
        Duration = TimeSpan.FromSeconds(1.5),
        FPS = 60,
        Ease = Eases.Cubic.InOut,
        IsAutoReverse = true,
        LoopTime = 1
    });
```

**预期结果：** 构造这条链不会启动动画，只记录终值与效果。起始值在 `Execute` 运行时从目标上读取。

## 4. 核心用法（逐步构建）

### 4.1 属性路径与强类型重载

`Property` 接收 lambda 而非字符串。嵌套成员就是嵌套路径：`((TranslateTransform)r.RenderTransform).X` 就地写子对象的属性。`double`、`int`、`float`、`decimal`、`Brush`、`Transform`、`Color`、`Point`、`Size`、`Rect`、`CornerRadius`、`Thickness`、`Vector`、`Point3D` 及 `System.Drawing` 对应类型都有强类型重载，WPF 适配层为它们提供采样器。

对 `Transform` 成员，重载接收集合：单个元素直接赋值——保留运行时类型，从而让 `((TranslateTransform)r.RenderTransform).X` 这类嵌套路径继续成立；多个元素才包装成 `TransformGroup`。

**预期结果：** `Property(r => r.Opacity, 0.25d)` 落到 `double` 重载；只含一个元素的变换集合仍是 `TranslateTransform`。

### 4.2 效果与缓动

`TransitionEffect` 携带 `Duration`、`FPS`（默认 60）、`Ease`、`IsAutoReverse` 与 `LoopTime`。`Eases` 提供十个族——`Sine`、`Quad`、`Cubic`、`Quart`、`Quint`、`Expo`、`Circ`、`Back`、`Elastic`、`Bounce`——每族有 `In`、`Out`、`InOut`，另有 `Eases.Default`。

`Back` 与 `Elastic` 会故意越过目标再回来，因此采样器使用的进度可以离开 `[0, 1]`：

```plot
{
  "title": "过冲缓动",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.2, 1.8] },
  "data": [
    { "fn": "x", "color": "#888888" },
    { "fn": "1 + 2.70158*(x-1)^3 + 1.70158*(x-1)^2", "color": "#4a9eff" },
    { "fn": "exp(-10*x*0.6931471805599453)*sin((10*x-0.75)*2.0943951023931953)+1", "color": "#f472b6" }
  ]
}
```

**预期结果：** `Back.Out` 峰值约为 1.10，`Elastic.Out` 约为 1.37，最终都收敛到 1。

### 4.3 执行、互斥与并发

`Execute(target)` 运行一个快照，默认 `CanMutualTask: true`：同一目标上的新动画会取消上一条。传 `false` 可让它们并发。

```csharp
slide.Execute(box);                        // 与上一次运行互斥
slide.Execute(box, CanMutualTask: false);  // 并发
_ = System.Threading.Tasks.Task.Run(() => slide.Execute(box));
```

从非 UI 线程启动是受支持的；适配层逐帧按目标的调度器切回 UI 线程。起始值就是运行开始时目标持有的值，因此若必须从已知状态开始，先把起点写回目标。

**预期结果：** 第二次点击替换第一段动画；非互斥调用允许两段同时写同一目标。

### 4.4 串联片段

`Await` 在下一段前暂停，`Then` 立即开始下一段，`AwaitThen` 暂停后再开始，`Repeat(n)` 从第一段起重跑整条链。只有最后一段上的计数才重复整条链。

```csharp
var chain = Transition<Rectangle>.Create()
    .Await(TimeSpan.FromSeconds(0.5))
    .Property(r => r.Width, 160d)
    .Effect(new TransitionEffect { Duration = TimeSpan.FromSeconds(1) })
    .Then()
    .Property(r => r.Opacity, 0.5d)
    .Effect(new TransitionEffect { Duration = TimeSpan.FromSeconds(1) })
    .Repeat(1);
```

**预期结果：** 宽度段先等半秒，再在一秒内增长；随后透明度在一秒内淡出；这一对再重复一次。

### 4.5 时间轴控制

控制面按**目标**寻址，而不是按快照：`Transition.Pause`、`Resume`、`SetRate`、`Seek`、`Exit`、`Position`、`Rate`、`Cycle` 与 `IsPaused` 都接收被动画的对象，以及两个分别选择互斥、非互斥或两者的标志。

```csharp
Transition.Pause(box, IncludeMutual: true, IncludeNoMutual: true);
Transition.SetRate(box, 0.5d, IncludeMutual: true, IncludeNoMutual: true);
Transition.Seek(box, TimeSpan.FromMilliseconds(750), IncludeMutual: true, IncludeNoMutual: true);
Transition.Exit(box, IncludeMutual: true, IncludeNoMutual: true);   // 原地停止
```

**预期结果：** 暂停冻结所有被选中的运行；速率设为 0.5 让速度减半，但不会报告 `IsPaused`；`Exit` 原地停止，不跳到终值。

## 5. 验证

运行完整程序。青色矩形应在淡出到 25% 的同时向右移动 220 像素，然后反向回到起点。`IsAutoReverse = true` 且 `LoopTime = 1` 时这一对会跑两遍。关闭窗口即结束进程。

## 6. 完整代码

```csharp
using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        var app = new Application();

        app.Startup += (_, _) =>
        {
            var box = new Rectangle
            {
                Width = 80,
                Height = 60,
                Fill = Brushes.Cyan,
                RenderTransform = new TranslateTransform(),
                HorizontalAlignment = HorizontalAlignment.Left,
                VerticalAlignment = VerticalAlignment.Top,
                Margin = new Thickness(40)
            };

            var window = new Window
            {
                Title = "Transition quick start",
                Width = 420,
                Height = 240,
                Content = box
            };

            var slide = Transition<Rectangle>.Create()
                .Property(r => r.Opacity, 0.25d)
                .Property(r => ((TranslateTransform)r.RenderTransform).X, 220d)
                .Effect(new TransitionEffect
                {
                    Duration = TimeSpan.FromSeconds(1.5),
                    FPS = 60,
                    Ease = Eases.Cubic.InOut,
                    IsAutoReverse = true,
                    LoopTime = 1
                });

            window.Loaded += (_, _) => slide.Execute(box);
            window.Show();
        };

        app.Run();
    }
}
```

声明部分改写自 `Examples/Transition/WPF/Demo/MainWindow.xaml.cs`（`Animation0`、`Animation2`）；时间轴调用与同文件的 `PauseAll`、`SetRate`、`SeekNextPass`、`ExitAll` 一致。

## 7. 运行声明

- ⚠️ 未实际运行——仅于 2026-11-25 静态核验。已对照 `Src/Adapters/VeloxDev.WPF/TransitionSystem/Transition.cs`、`TransitionEffect.cs`、`TransitionEffects.cs`、`Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs`、`TransitionEx.cs`、`Eases.cs` 以及 WPF demo 核验。本环境未启动窗口。
