# Transition — 显式声明状态

## 1. 逐条声明状态

适配器的构建器就是 **`Transition<T>` 本身**（`T` 是目标类型）。用 `Transition<T>.Create()` 创建它，再用 `.Property(...)` **逐条显式声明**每个路径的目标值、用 `.Effect(...)` 声明时序。在执行之前它不触碰目标（见 [执行与控制](../05_执行与控制/index.md)）。由于构建器只是一份描述，可以只构建一次、存成静态字段，并在任意多个目标上复用。

```csharp
using System;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

public static class QuickStart
{
    public static readonly Transition<Rectangle> Animation0 =
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

这与 `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` 中 `Animation0` 的形状一致（在那里它是窗口 partial 类的成员）。这里没有「拍摄」或「捕获」这一步：**每条要动画的路径都必须显式写出**，声明的值就是该路径的终点值。

适配器的 `Transition<T>` 为平台值类型提供了类型化 `Property` 重载（`Brush`、`Transform` 集合、`Color`、`Point`、`CornerRadius`、`Thickness`、`Size` … 以及数值 `int` / `double` / `float` / `decimal`），因此目标值会以已类型化形式存储。泛型 `Property<TValue>` 重载覆盖其余情形。

**预期结果：** 流式链返回同一个 `Transition<Rectangle>`，含三个已声明属性（`Opacity`、`RenderTransform.X`、`Fill`）与一个 2 秒自动往返的效果。此刻还不会动画。

## 2. 读回已声明状态

声明的值位于状态字典中，键为 `ITransitionProperty`（其 `Path` 是点分属性路径）：

```csharp
foreach (var kvp in QuickStart.Animation0.GetState().Values)
    Console.WriteLine($"{kvp.Key.Path} = {kvp.Value}");
```

**预期结果：** 循环打印 `Opacity = 0`、`RenderTransform.X = 800` 与 `Fill = <brush>`。`GetState()` 还暴露 `Interpolators` 与 `Options` 字典，分别对应经 `TransitionCoreEx.Interpolator` 附加的逐属性采样器与 `Property` 的可选 `interpolationOptions` 参数。

## 3. 路径约束与两个异常

- **父子冲突**：同一个 transition 内，新路径与已有路径构成父子关系（例如 `r.Fill` 与 `((LinearGradientBrush)r.Fill).StartPoint`）时，`StateCore.SetValue` 抛出 `TransitionPathConflictException`（`VeloxDev.TransitionSystem`）。一个对象只能由一条路径表达 —— 否则整体采样器与子叶采样器会每帧写同一个对象，结果取决于它们的运行顺序。该检查只覆盖单条 transition 的 value 路径；跨 transition 的冲突、以及经 `SetInterpolator` / `SetOptions` 注册的路径都不检查。
- **永不可动画的路径**：声明的路径叶子是引用类型、且既没有自定义采样器也没有已注册采样器时，`Transition<T>.Execute(...)` **同步**抛出 `TransitionPathUnsampleableException`（`VeloxDev.TransitionSystem`）—— 不再「静默什么都不做」。值类型豁免：结构体仍可逐成员装配。

这两个异常与 `TransitionProperty.UnreadablePath` 是**两件事**：后者指路径合法但对当前 target 的运行时类型无效，`Prepare` 每帧跳过它，不抛异常。

**预期结果：** 写错路径的 transition 在定义（冲突）或执行（永不可动画）时立刻失败，而不是悄悄不动。

**索引实参。** 路径除属性段外还可带索引段 / 数组段 —— `x.Items[i].Width`、`x.Map["player"].Color`、`x.Cells[1, 2]`。它们的实参属于路径的**身份**，而不属于路径的值：`x => x.Items[idx].Width` 无论 `idx` 当时是多少都解析为同一条路径，因此循环里从五个不同闭包局部量声明会得到五条条目。未冻结的实参默认每帧重新求值，所以路径会**跟随**移动的索引（闭包局部量，或目标自身的属性如 `x.SelectedIndex`）—— 但**终点值只在启动时读过一次**，因此中途移动的索引会写入一个按它起步时那个槽位算出的终点值。把实参包进 `PathIndex.Frozen(...)` 即可把它钉在启动时解析出的槽位上；凡终点值必须落在它被读取的那个位置时，都该这样做。常量实参不需要标记，无论怎么写它都是冻结的；并且 `Items[i]` 与 `Items[Frozen(i)]` 是两条不同的路径。（源码：`Src/Core/VeloxDev.Core/TransitionSystem/PathIndex.cs`；解析与身份由 `Src/Core/VeloxDev.Core.Test/TransitionSystem/TransitionPropertyIndexerTests.cs` 锁定。）

## 4. 重置

重置不是一个独立 API，而是**用同一个声明式构建器把各初始值逐条写回**，并把时长压到零（`TransitionEffects.Empty`）：

```csharp
// Examples/Transition/MAUI/Demo/MainPage.xaml.cs
private static Transition<Rectangle> CreateRec0Reset()
{
    return Transition<Rectangle>.Create()
        .Property(r => r.TranslationX, 0)
        .Property(r => r.Fill, CreateRec0Brush())
        .Effect(TransitionEffects.Empty);   // Duration = 0 → 瞬时写回
}

// 需要时执行：
CreateRec0Reset().Execute(Rec0);
```

要点：

- 重置必须覆盖动画**触碰过的每一条路径** —— 只写回一部分会让目标停在动画中途的值上。
- 终点值不要复用可能已被就地改写的实例：例如被动画修改过的画刷 / 变换，应重建一个新对象作为重置终点（示例里的 `CreateRec0Brush()` 就是为此在代码里重建的）。
- `TransitionEffects.Empty` 的 `Duration = TimeSpan.Zero`，解释器直接落到精确终点。

**预期结果：** 目标被瞬时写回这些路径的初始值，且不会留下任何进行中的动画。

## 5. 旋转选项

类似角度的数值路径可通过 `Property` 的可选 `interpolationOptions` 参数指定旋转方向（`VeloxDev.TransitionSystem` 中带 `[Flags]` 的 `RotationDirection`）：`Auto`（最短路径）、二维用 `ClockWise` / `CounterClockWise`，外加按轴的 `ClockWiseX/Y/Z` / `CounterClockWiseX/Y/Z` 三维选项。采样器（`DoubleSampler`）在帧时读取该选项。

```csharp
.Property(r => r.RenderTransform, [new RotateTransform(180)], RotationDirection.CounterClockWise)
```

**预期结果：** 该变换路径沿*逆时针*转 180 度，而不是默认任意的环绕方向。
