# 过渡动画 — 显式声明状态

> 本页取代旧的「定义快照」主题。捕获对象当前状态不再是 API 的一部分：引擎没有快照 / 捕获步骤，因此动画现在是**逐路径显式声明的状态**。

## 1. 声明模型

`Transition<T>`（`T` 是目标类型）同时是三样东西：静态入口（`Create`）、流式构建器（`Property`、`Effect`）与执行器（`Execute`）。一个实例描述一个**动画段** —— 一组显式声明的属性路径、每条路径应到达的值，外加一个效果（时长 / 缓动 / FPS / 循环）。

目标上没有任何东西被发现或记录。`Property(lambda, value)` 只存*目标*值；引擎在运行开始时读取属性的**当前**值（`InterpolatorCore.Prepare`），这正是同一个构建器可以存入静态字段并在任意多个目标上复用的原因。因为构建器只是数据，它可以构建一次、执行多次（见[执行与控制](../05_执行与控制/index.md)）—— 也可以锚定到调用方提供的时间轴上，让多个动画共享一套传输。

适配器的 `Transition<T>` 之下是 Core 构建器 `TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, TPriorityCore>` —— 一个段，加上指向下一段的 `next` 链接。它有三个声明点：`.Property(...)`（目标值）、`.Effect(...)`（时间），以及 `Repeat(count)` 链式扩展（本段循环还要再跑几次；见[序列与重复](../04_序列与重复/index.md)）。

## 2. 构建一个段

用 `Transition<T>.Create()` 创建段，用 `.Property(...)` 声明目标、用 `.Effect(...)` 声明时间。属性 lambda 可以是**嵌套路径** —— demo 直接动画 `((TranslateTransform)r.RenderTransform).X`：

```csharp
using System;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

public static class QuickStart
{
    public static readonly Transition<Rectangle> Animation0 =
        Transition<Rectangle>.Create()
            .Property(r => r.Opacity, 0)                                   // double target
            .Property(r => ((TranslateTransform)r.RenderTransform).X, 200d) // nested path
            .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))     // Brush target
            .Effect(new TransitionEffect
            {
                Duration = TimeSpan.FromSeconds(2),
                IsAutoReverse = true,
                LoopTime = 2,
            });
}
```

这就是 `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` 中 `Animation0` 的精确形状（那里的 200 是 `LoadTravel` 常量，成员是窗口 partial 类的 `static readonly`）。泛型 `Property<TValue>` 重载接受任意值类型 —— 除 Razor 外的每个适配器都声明了它，Razor 只提供带类型重载；各适配器还为平台值类型增加带类型重载（`Brush`、`Transform` 集合、`Color`、`Point`、`CornerRadius`、`Thickness`、`Size` 等，以及数值 `int` / `double` / `float`，除 Jalium 外还有 `decimal`），因此目标值以已类型化的形式存储。

**预期结果：** 流式链返回同一个 `Transition<Rectangle>`，其中声明了三个属性（`Opacity`、`RenderTransform.X`、`Fill`）与一个 2 秒自动反向效果。此时还没有任何动画。

## 3. 读回已声明的状态

声明的值位于状态字典中，以 `ITransitionProperty` 为键（其 `Path` 是点分隔的属性路径）：

```csharp
foreach (var kvp in QuickStart.Animation0.GetState().Values)
    Console.WriteLine($"{kvp.Key.Path} = {kvp.Value}");
```

**预期结果：** 循环打印 `Opacity = 0`、`RenderTransform.X = 200` 与 `Fill = <brush>`。`GetState()` 还暴露 `Interpolators` 与 `Options` 字典，用于你附加的逐属性采样器 / 选项。

## 4. 表达重置

重置不是捕获来的 —— 它像任何动画一样**声明**：逐路径列出初始值，并用零时长效果（`TransitionEffects.Empty`）播放，直接跳到这一趟的终点：

```csharp
// The box's defaults, expressed as explicit paths.
private static Transition<BoxModel> CreateReset(string color)
{
    return Transition<BoxModel>.Create()
        .Property(b => b.X, 0)
        .Property(b => b.Y, 0)
        .Property(b => b.Width, 60)   // SamplerBench.BodyWidth / BodyHeight in the Blazor demo
        .Property(b => b.Height, 60)
        .Property(b => b.Opacity, 1)
        .Property(b => b.Rotate, 0)
        .Property(b => b.Scale, 1)
        .Property(b => b.Color, color);
}

// ... later, restore those values instantly:
CreateReset("#00BFFF").Effect(TransitionEffects.Empty).Execute(Box0);
```

这是 `Examples/Transition/Blazor/Demo/Demo/Components/Pages/Home.razor.cs` 中的 `CreateReset` / 重置分支；WPF demo 使用同样的 `CreateResetRec*` 形状（`Examples/Transition/WPF/Demo/MainWindow.xaml.cs`）。每个 demo 的重置路径列表都必须与动画实际产生的状态保持同步 —— 没有东西替你推导它。

**预期结果：** 重置运行在一趟内写入每条声明值并立即完成；目标回到其声明的初始状态。

*关于 WPF demo 的说明：* 那里重置还直接把值写穿（对 `GetState().Values` 逐个 `kvp.Key.SetValue(target, kvp.Value)`）而不是走 `Execute`，因为异步管线在某些平台上重置 `RenderTransform` / `Projection` 不可靠。那个直接写入是 demo 的变通，不是 API 的一部分。

## 5. 路径规则

两类路径错误会被拒绝，而不是静默地什么都不动画：

- **`TransitionPathConflictException`**（`VeloxDev.TransitionSystem`）—— 在过渡**构建**期间由 `StateCore.SetValue` 抛出，当新声明的路径位于同一次过渡上已有路径之上或之下时（一个对象必须由且只由一条路径表达）。重复声明同一条路径只是普通覆盖，允许。该检查只覆盖一次过渡的值路径：两次过渡**之间**的冲突，以及经 `SetInterpolator` / `SetOptions` 注册的路径，都不检查。
- **`TransitionPathUnsampleableException`**（`VeloxDev.TransitionSystem`）—— 由 **`Execute` 同步抛出**，当一条声明路径永远无法动画时：其末端为引用类型，既无注册采样器也无自定义插值器。值类型豁免此检查（实现 `ISampleable` 的结构体会逐成员装配；未实现的会被 `Warn` 后跳过）。这与 `TransitionProperty.UnreadablePath` 无关 —— 后者路径有效但不匹配当前目标的运行时类型，仍属逐帧跳过。

```csharp
// Parent and child paths on one transition -> TransitionPathConflictException
Transition<Rectangle>.Create()
    .Property(r => r.RenderTransform, [new TranslateTransform(200, 0)])
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 200d); // throws
```

**预期结果：** 冲突在调用第二个 `Property` 处抛出；不可采样路径从 `Execute` 抛出，发生在调度任何帧之前。

**索引实参。** 路径除属性分段外还可以携带索引或数组分段 —— `x.Items[i].Width`、`x.Map["player"].Color`、`x.Cells[1, 2]`。它们的实参是路径**身份**的一部分，不是值的一部分：`x => x.Items[idx].Width` 不管 `idx` 是什么都解析成一条路径，这就是为什么一个循环用五个捕获的局部变量声明五条路径会得到五个条目。默认情况下非冻结实参每帧重新求值，因此路径会**跟随**移动的索引（捕获的局部变量，或目标自身的属性如 `x.SelectedIndex`）—— 但**终值只在运行开始时读取一次**，因此中途移动的路径会把一个针对它起步槽位算出的终值写下去。把实参包进 `PathIndex.Frozen(...)` 可把它钉在开始时解析到的槽位；当终值必须落在它被读取的位置时，这正是你要的。常量实参不需要标记，怎么写都被冻结，且 `Items[i]` 与 `Items[Frozen(i)]` 是两条不同的路径。（源：`Src/Core/VeloxDev.Core/TransitionSystem/Binding/PathIndex.cs`；解析与身份由 `Src/Core/VeloxDev.Core.Test/TransitionSystem/TransitionPropertyIndexerTests.cs` 钉住。）

## 6. 旋转选项

类角度的数值路径可以通过 `Property` 的可选 `interpolationOptions` 实参引导旋转方向（`RotationDirection`，`VeloxDev.TransitionSystem` 中的 `[Flags]` 枚举）：`Auto`（最短路径）、二维的 `ClockWise` / `CounterClockWise`，以及逐轴三维的 `ClockWiseX/Y/Z` / `CounterClockWiseX/Y/Z`。采样器（`DoubleSampler`）在帧时读取该选项。

```csharp
.Property(r => r.RenderTransform, [new RotateTransform(180)], RotationDirection.CounterClockWise)
```

**预期结果：** 变换路径按*逆时针* 180 度旋转，而不是默认的任意环绕方向。

下一步：[序列与重复](../04_序列与重复/index.md) 把多个段串成一条时间轴。
