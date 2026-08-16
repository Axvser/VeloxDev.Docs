# Transition — 快速入门

## Transition

### 快速入门

本指南让你用 **Transition**（VeloxDev 的跨平台、代码驱动插值引擎）驱动 UI 属性动画。核心理念是**「一切皆状态」**：将目标的属性值记录为*状态快照*（`StateSnapshot`），描述对象应到达的最终状态，然后执行 —— 引擎会把每个记录的属性从当前值插值到目标值，经过一条定时、带缓动、按帧的时间线。

> 示例源码：`Examples/Transition/{WPF, Avalonia, WinUI, WinForms, MAUI, Blazor}/Demo`。

#### 1. 前置条件

- **支持目标**（来自 `VeloxDev.Core.csproj`）：`netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` —— 可用于 .NET Framework 4.6.1+、.NET Core 3.0+ 与 .NET 5+。
- **SDK / 运行时：** 带 Roslyn 4.x（5.0+）的 .NET SDK；示例面向 `net9.0` / `net10.0` —— *被验证过*的配置。
- **包管理器：** NuGet（`dotnet` CLI 或 Visual Studio）。
- **所需服务：** 用于 UI 线程动画与平台插值器的 UI 框架适配器（WPF / Avalonia / WinUI / MAUI / WinForms / Razor）。**纯数学插值**（在普通 POCO 上）**无需任何适配器** —— `Eases`、`InterpolatorCore` / `IValueInterpolator` 可在纯控制台应用中运行。


#### 2. 安装 / 添加依赖

添加核心包与 GUI 框架的适配器包 —— 适配器附带过渡引擎、平台插值器与 UI 线程编组器：

```bash
dotnet add package VeloxDev.Core     # 纯数学 + 引擎核心
dotnet add package VeloxDev.WPF      # 或：Avalonia / WinUI / MAUI / WinForms / Razor
```

**预期结果：** 两条 `dotnet add` 命令都打印 `Successfully added package ...`，包被写入 `.csproj`；还原后 `using VeloxDev.TransitionSystem;` 可以解析。

#### 3. 基本设置 / 注册

使用 `Transition<T>.Create()` 创建 `StateSnapshot` 并记录目标属性值。属性 lambda 可以是**嵌套路径**（如 `r => ((TranslateTransform)r.RenderTransform).X`）：

```csharp
using VeloxDev.TransitionSystem;

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

也可以用适配器扩展 `target.Snapshot(...)` / `target.SnapshotAll()` / `target.SnapshotExcept(...)` 捕获对象**当前**值，或用 `Transition<T>.Execute(target, snapshot, CanMutualTask)` 直接运行快照而无需预先声明的构建器。

**预期结果：** 流式链编译通过并构建一个 `StateSnapshot`，包含 3 个已记录属性（`Opacity`、`RenderTransform.X`、`Fill`）与一个 `TransitionEffect`（2 秒、往返两次）。此刻还不会动画 —— 快照只是纯描述符。

**平台接线（仅部分平台需要）：**

- **WPF / Avalonia / MAUI**：无需接线 —— 甚至可以从后台线程启动动画，适配器的 `UIThreadInspector` 会把更新调度回 UI 线程。
- **WinUI**：可选 —— 可在 UI 线程调用一次 `UIThreadInspector.CaptureUIThread()`。任何 `DependencyObject` 目标都会通过其自身的 `DispatcherQueue` 自动编组，因此仅当从后台线程首次启动非 UI 目标时才需要它。
- **WinForms / Razor**：可选 —— 可在 UI 线程调用 `UIThreadInspector.CaptureUIThread()`（WinForms 在 `OnLoad`；Razor 在 `OnInitialized`）。两个适配器也会在首次 UI 线程访问时惰性捕获，并通过 `Control` / `SynchronizationContext` 编组。

#### 4. 核心用法（逐步）

**第 1 步 — 记录目标值。** 对每个可动画属性使用 `.Property(x => x.Width, 200)`。每次调用都会把表达式解析为 `TransitionProperty` 并把目标值存入快照状态。

```csharp
Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 0)
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 800);
```

**预期结果：** 快照状态现在把两个属性映射到其目标值（`Opacity → 0`、`RenderTransform.X → 800`）。可通过 `snapshot.GetState().Values` 读回。

**第 2 步 — 用效果设置时序。** 要么直接修改效果对象，要么使用流式设置器：

```csharp
.Effect(e => e.Duration = TimeSpan.FromSeconds(2))          // 流式设置器
.Effect(TransitionEffects.Hover)                            // 预设：0.32 秒
.Effect(new TransitionEffect() { FPS = 144, Ease = Eases.Circ.InOut, IsAutoReverse = true, LoopTime = 2 });
```

**预期结果：** 效果描述符携带 `Duration`、`FPS`（默认 60）、`Ease`（默认 `Eases.Default`）、`IsAutoReverse` 与 `LoopTime`。`LoopTime = int.MaxValue` 表示「无限循环」。

**第 3 步 — 拼接分段。** `.Await(timeSpan)` 在本段前等待，`.Then()` 开始下一段，`.AwaitThen(timeSpan)` 两者兼顾。每段有独立的 `State` + `Effect`。

```csharp
.Then()
.Property(r => r.Fill, new SolidColorBrush(Colors.Yellow))
.Effect(new TransitionEffect() { Duration = TimeSpan.FromSeconds(2), Ease = Eases.Sine.In });
```

**预期结果：** 快照被链接成分段链表；解释器按顺序播放，尊重每段的延迟、缓动与循环设置。

**第 4 步 — 执行。** 对目标运行快照。默认是**互斥**（`CanMutualTask: true`）：一个对象同时只允许一个动画，新动画会取消正在运行的。传 `CanMutualTask: false` 可并行：

```csharp
Animation0.Execute(Rec0);                   // 默认：互斥
Animation0.Execute(Rec0, CanMutualTask: false);
Transition<Rectangle>.Execute(Rec0, snapshot);   // 静态替代写法
Transition.Exit(Rec0);                      // 停止：IncludeMutual / IncludeNoMutual
```

**预期结果：** 属性从当前值按效果时长与缓动动画到目标值。第二个互斥动画会取消第一个；`Transition.Exit(Rec0)` 让动画就地停止。

#### 5. 验证

运行应用（例如在 WPF 示例中 `dotnet run`）：

- 矩形在 2 秒内动画透明度、位置与填充色，然后自动往返两次（`IsAutoReverse + LoopTime: 2`）。
- 多段动画先位移+缩放，等待后以不同缓动动画填充色。
- 重置按钮通过 `snapshot.Effect(TransitionEffects.Empty).Execute(Rec0)` 立即把矩形恢复到捕获快照。
- 打断按钮调用 `Transition.Exit(...)`，矩形就地停止。
- 六个平台示例（WPF、Avalonia、WinUI、WinForms、MAUI、Blazor）运行相同的动画定义 —— Blazor 示例动画一个普通 `BoxModel` 视图模型，通过 `INotifyPropertyChanged` 触发重渲染。

#### 6. 完整代码

一个最小化、自包含的 WPF 程序（单个 `Program.cs`，无 XAML）动画一个矩形。用 `dotnet new` + `dotnet add package VeloxDev.WPF` 创建项目，然后把 `Program.cs` 替换为：

```csharp
using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

namespace TransitionDemo;

public static class Program
{
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
                Ease = Eases.Sine.InOut,
            });

    [STAThread]
    public static int Main()
    {
        var app = new Application();
        var window = new Window { Title = "Transition Quick Start", Width = 920, Height = 300 };
        var canvas = new Canvas { Background = Brushes.White };

        var rect = new Rectangle
        {
            Width = 120,
            Height = 60,
            Fill = Brushes.Cyan,
            RenderTransform = new TranslateTransform(),
        };
        canvas.Children.Add(rect);

        window.Content = canvas;
        window.Loaded += (s, e) => Animation0.Execute(rect);
        app.Run(window);
        return 0;
    }
}
```

对应的 `.csproj`（来自 `dotnet new`）：

```xml
<Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
        <OutputType>WinExe</OutputType>
        <TargetFramework>net9.0-windows</TargetFramework>
        <Nullable>enable</Nullable>
        <ImplicitUsings>enable</ImplicitUsings>
        <UseWPF>true</UseWPF>
    </PropertyGroup>
    <ItemGroup>
        <PackageReference Include="VeloxDev.WPF" />
    </ItemGroup>
</Project>
```

> **提示：** Razor 适配器额外提供 `string?` 的 `Property` 重载，可动画 CSS 颜色字符串（`"#ff7043"`、`rgb(...)`、命名颜色）。WinForms 动画 `IInterpolable`、`Padding` 及常用数值类型；MAUI 动画 MAUI 类型（`Brush`、`Shadow`、`PointF`、`RectF`...）。

#### 7. 运行声明

- ⚠️ **未实际运行** — 仅静态验证。上述代码依据已验证的 `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` 与 `Src/Adapters/VeloxDev.WPF/PlatformAdapters/Transition.cs` 中的适配器 API 编写；本次文档编写**未**实际编译或执行。
