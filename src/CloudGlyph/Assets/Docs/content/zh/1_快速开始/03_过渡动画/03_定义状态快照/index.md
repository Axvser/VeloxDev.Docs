# Transition — 定义状态快照

## 1. 快照概念

一个 `Transition<T>.StateSnapshot` 是一段动画的**纯描述符**：一组记录的*属性目标值*加上一个*效果*（时长 / 缓动 / FPS / 循环），可选地带有逐属性采样器与选项。在执行之前它不触碰目标（见 [执行与控制](../05_执行与控制/index.md)）。由于快照只是数据，可以只构建一次、存成静态字段，并在任意多个目标上复用。

## 2. 构建一次性快照

用 `Transition<T>.Create()` 创建根快照（`T` 是目标类型），再用 `.Property(...)` 声明目标、`.Effect(...)` 声明时序。属性 lambda 可以是**嵌套路径** —— 示例直接动画 `((TranslateTransform)r.RenderTransform).X`：

```csharp
using System;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

public static class QuickStart
{
    public static readonly Transition<Rectangle>.StateSnapshot Animation0 =
        Transition<Rectangle>.Create()
            .Property(r => r.Opacity, 0)                                   // double 目标
            .Property(r => ((TranslateTransform)r.RenderTransform).X, 800) // 嵌套路径
            .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))     // Brush 目标
            .Effect(new TransitionEffect
            {
                Duration = TimeSpan.FromSeconds(2),
                IsAutoReverse = true,
                LoopTime = 2,
            });
}
```

这与 `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` 中 `Animation0` 的形状完全一致（在那里它是窗口 partial 类的成员）。适配器的 `StateSnapshot` 为平台值类型提供了类型化 `Property` 重载（`Brush`、`Transform` 集合、`Color`、`Point`、`CornerRadius`、`Thickness`、`Size` … 以及数值 `int` / `double` / `float` / `decimal`），因此目标值会以已类型化形式存储。泛型 `Property<TValue>` 重载覆盖其余情形。

**预期结果：** 流式链返回同一个 `StateSnapshot`，含三个已记录属性（`Opacity`、`RenderTransform.X`、`Fill`）与一个 2 秒自动往返的效果。此刻还不会动画。

## 3. 读回已记录状态

记录的值位于快照状态字典中，键为 `ITransitionProperty`（其 `Path` 是点分属性路径）：

```csharp
foreach (var kvp in QuickStart.Animation0.GetState().Values)
    Console.WriteLine($"{kvp.Key.Path} = {kvp.Value}");
```

**预期结果：** 循环打印 `Opacity = 0`、`RenderTransform.X = 800` 与 `Fill = <brush>`。`snapshot.GetState()` 还暴露 `Interpolators` 与 `Options` 字典，分别对应你附加的逐属性采样器与选项。

## 4. 记录对象*当前*状态

与其手写目标值，不如用适配器 `TransitionEx` 扩展（`using VeloxDev.TransitionSystem`）捕获现有目标的实况值：

```csharp
var explicitSnapshot  = rect.Snapshot(r => r.Opacity, r => r.Fill); // 仅列出的路径
var allSnapshot       = rect.SnapshotAll();                          // 自动发现可动画属性
var withoutWidth      = rect.SnapshotExcept(r => r.Width);           // 除这些外的全部可动画属性
```

`SnapshotAll()` 与 `SnapshotExcept(...)` 会遍历对象图，记录每个类型拥有已注册采样器（`Interpolator.TryGetInterpolator(type, out _)`）的属性，并递归进入复合类型。示例在元素加载并初始化**之后**（`Loaded` / `OnAppearing` / `OnInitialized`）才拍快照，使捕获的是真实的初始状态；之后用一个零时长效果恢复它（见 [分段与循环](../04_分段与循环/index.md)）。

**预期结果：** 捕获的快照持有目标这些路径的*当前*值 —— 之后可 `Effect` 覆盖并执行来重置对象。

## 5. 旋转选项

类似角度的数值路径可通过 `Property` 的可选 `interpolationOptions` 参数指定旋转方向（`VeloxDev.TransitionSystem` 中带 `[Flags]` 的 `RotationDirection`）：`Auto`（最短路径）、二维用 `ClockWise` / `CounterClockWise`，外加按轴的 `ClockWiseX/Y/Z` / `CounterClockWiseX/Y/Z` 三维选项。采样器（`DoubleSampler`）在帧时读取该选项。

```csharp
.Property(r => r.RenderTransform, [new RotateTransform(180)], RotationDirection.CounterClockWise)
```

**预期结果：** 该变换路径沿*逆时针*转 180 度，而不是默认任意的环绕方向。
