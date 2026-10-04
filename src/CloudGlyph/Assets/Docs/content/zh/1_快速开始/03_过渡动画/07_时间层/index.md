# 过渡动画 — 时间层

## 1. 这一页是什么

每个动画都锚定在一个 `ITimeSource` 上，而每个控制调用（`Pause`、`Resume`、`SetRate`、`Seek`）都作用于那个源。源、建在它上面的两种采样模式，以及发放它们的注册表，全都在 `VeloxDev.Timing` 里 —— 一个**本特性的子模块**，加入于 2026-09-14，由 transition / dynamic-theme / tickable 共享。

本页不需要 GUI、不需要适配器包、也不需要目标对象。它是引擎之下、被直接驱动的那一层。如果你只想动画一个矩形，请看[缓动与插值器](../02_缓动与插值器/index.md) —— 你永远不会命名这些类型。

### 前置条件

- **目标框架**（来自 `VeloxDev.Core.csproj`）：`netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`。时间层编进全部四个且没有条件编译。
- **包：** 只需 `VeloxDev.Core` —— 不需要适配器包。
- **必需服务：** 无。

**这一步的预期结果：** 你有一个引用 `VeloxDev.Core` 的 .NET 项目，且 `using VeloxDev.Timing;` 可解析。

## 2. 创建一个源

`TimerCore` 是注册表：`CreateTimeSource<TContract>()` 构造 Core 默认实现，除非某平台在同一**契约**下注册过。每次查找都返回一个*全新实例*，因为源携带暂停 / 速率状态。

```csharp
using VeloxDev.Timing;

ITimeSourceControl timeline = TimerCore.CreateTimeSource<ITimeSourceControl>();
Console.WriteLine($"{timeline.GetType().Name}, unit={timeline.TicksPerSecond} ticks/s, advancing={timeline.IsAdvancing}");
```

**预期结果：** `TimeSourceCore`，tick 单位等于你机器的 `Stopwatch.Frequency`（本页运行所在的 Windows 机器上是 10 000 000 —— `TicksPerSecond` 按源而定，永不硬编码），且 `advancing=True`。

## 3. 采样 —— 两种模式

源经采样器读取，而模式恰好两种。采样器持有逐消费者状态且有**一个逻辑所有者**；它不是线程安全的，不得共享。

**尽力而为（`IUncompensatedTimeSampler`）** —— 自上次采样以来的间隔，不欠任何人。这是动画用的模式：它读绝对位置，无论采样节奏如何都正确。

**定步长（`ICompensatingTimeSampler`）** —— 交付步数等于 `floor(elapsed / Step)` 且无漂移。这是物理需要的。

```csharp
var uncompensated = TimerCore.CreateTimeSampler<IUncompensatedTimeSampler>(timeline);
var first = uncompensated.Sample();
Console.WriteLine($"first sample: {first.Delta.TotalMilliseconds:F3} ms");

Thread.Sleep(50);
var second = uncompensated.Sample();
Console.WriteLine($"delta after ~50 ms: {second.Delta.TotalMilliseconds:F1} ms, total {second.Total.TotalMilliseconds:F1} ms");

var fixedStep = TimerCore.CreateTimeSampler<ICompensatingTimeSampler>(timeline);
Console.WriteLine($"default step: {fixedStep.Step.TotalMilliseconds:F0} ms, max/call {fixedStep.MaxStepsPerCall}, max pending {fixedStep.MaxPendingSteps}");

Thread.Sleep(100);
var pushed = 0;
int count;
while ((count = fixedStep.Advance(out var sample)) > 0) pushed += count;
Console.WriteLine($"steps delivered after ~100 ms: {pushed} (pending {fixedStep.PendingSteps}, dropped {fixedStep.DroppedSteps})");
```

**预期结果：** 非补偿的 delta 跟随睡眠；`Advance` 恰好发放 `floor(100 / 16) = 6` 步（默认 16 ms 步长），且 `pending = 0`、`dropped = 0`（未触及上限，因此没有迟延、也没有宽恕）；每个样本的 `Delta` 都等于固定 `Step`，绝不是实测间隔。

## 4. 暂停与停摆信号

`Pause()` 冻结位置。暂停期间的时间**按构造**被排除 —— 什么都不累积 —— 而停摆的消费者不轮询：

```csharp
timeline.Pause();
var parked = timeline.WaitWhileStalledAsync();
Console.WriteLine($"paused={timeline.IsPaused}, advancing={timeline.IsAdvancing}, parked already done={parked.IsCompleted}");

var frozen = timeline.Position;
Thread.Sleep(50);
Console.WriteLine($"position frozen across a 50 ms sleep: {timeline.Position == frozen}");

_ = uncompensated.Sample();                               // 暂停前累积的那点
Console.WriteLine($"a paused source no longer advances: {uncompensated.Sample().Delta == TimeSpan.Zero}");

timeline.Resume();
await parked;
Console.WriteLine($"after Resume: advancing={timeline.IsAdvancing}, parked wait released");
```

**预期结果：** `paused=True` / `advancing=False`；返回的任务**没有**已完成（它在停摆，在 `awaited` 唤醒之前零成本）；位置在 50 毫秒睡眠前后完全相同；暂停后取的样本报 `Delta == TimeSpan.Zero`（调用方不推帧的信号）；`await parked` 在 `Resume()` 运行后返回。

## 5. 速率为零不是暂停

这正是使 `IsAdvancing`（而非 `IsPaused`）成为停摆谓词的区别：

```csharp
timeline.SetRate(0d);
Console.WriteLine($"at rate 0: paused={timeline.IsPaused}, advancing={timeline.IsAdvancing}");
timeline.SetRate(1d);
Console.WriteLine($"back at rate 1: advancing={timeline.IsAdvancing}");
```

**预期结果：** `paused=False` 但 `advancing=False` —— 时钟被冻结却没有被暂停，因此只检查 `IsPaused` 的循环会对着一个永不移动的时钟继续跑。`SetRate(1)` 让它重新启动。

## 6. 注册以契约为键

```csharp
TimerCore.RegisterTimeSource<ITimeSourceControl>(static () => new TimeSourceCore());
// 在一个没人注册的契约下查找会抛异常：
try { TimerCore.CreateTimeSource<IMarker>(); }
catch (InvalidOperationException) { Console.WriteLine("an unregistered contract throws"); }
```

**预期结果：** 在契约 `ITimeSourceControl` 下注册，该契约的查找就找到它；注册在*实现*类型下的东西，任何契约查找都找不到；而一个什么都没注册的契约抛 `InvalidOperationException` 而不是返回 null。（单元测试覆盖为 `TimerCoreRegistryTests`。）

## 7. 完整代码

一个单文件控制台程序，覆盖 §2–§6。`dotnet new console -n TimingQuickStart`，然后替换 `Program.cs`：

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using VeloxDev.Timing;

namespace TimingQuickStart;

public static class Program
{
    public static async Task Main()
    {
        // 1. 一个源，以及建在它上面的两种采样模式。
        ITimeSourceControl timeline = TimerCore.CreateTimeSource<ITimeSourceControl>();
        Console.WriteLine($"1 source = {timeline.GetType().Name}, unit = {timeline.TicksPerSecond} ticks/s, advancing = {timeline.IsAdvancing}");

        var uncompensated = TimerCore.CreateTimeSampler<IUncompensatedTimeSampler>(timeline);
        var first = uncompensated.Sample();
        Console.WriteLine($"  first sample covers the interval since construction: {first.Delta.TotalMilliseconds:F3} ms");

        Thread.Sleep(50);
        var second = uncompensated.Sample();
        Console.WriteLine($"  measured delta after ~50 ms: {second.Delta.TotalMilliseconds:F1} ms, total {second.Total.TotalMilliseconds:F1} ms");

        // 2. 定步长采样复还所欠：交付数等于 floor(elapsed / step)。
        var fixedStep = TimerCore.CreateTimeSampler<ICompensatingTimeSampler>(timeline);
        Console.WriteLine($"2 default step = {fixedStep.Step.TotalMilliseconds:F0} ms, max/call = {fixedStep.MaxStepsPerCall}, max pending = {fixedStep.MaxPendingSteps}");

        Thread.Sleep(100);
        var pushed = 0;
        int count;
        while ((count = fixedStep.Advance(out var sample)) > 0)
        {
            pushed += count;
            if (sample.Delta != fixedStep.Step) throw new InvalidOperationException("a fixed step must report a fixed delta");
        }

        Console.WriteLine($"  steps delivered after ~100 ms: {pushed}, pending = {fixedStep.PendingSteps}, dropped = {fixedStep.DroppedSteps}");

        // 3. 暂停按构造被排除，且停摆的消费者在等待而不是轮询。
        timeline.Pause();
        var parked = timeline.WaitWhileStalledAsync();
        Console.WriteLine($"3 after Pause: paused = {timeline.IsPaused}, advancing = {timeline.IsAdvancing}, parked wait already done = {parked.IsCompleted}");

        var frozen = timeline.Position;
        Thread.Sleep(50);
        Console.WriteLine($"  position frozen across a 50 ms sleep: {timeline.Position == frozen}");
        _ = uncompensated.Sample();   // 暂停前累积的那点
        Console.WriteLine($"  a paused source no longer advances: {uncompensated.Sample().Delta == TimeSpan.Zero}");

        timeline.Resume();
        await parked;
        Console.WriteLine($"  after Resume: advancing = {timeline.IsAdvancing}, parked wait released");

        // 4. 速率为零会冻结时钟而不暂停它。
        timeline.SetRate(0d);
        Console.WriteLine($"4 at rate 0: paused = {timeline.IsPaused}, advancing = {timeline.IsAdvancing}");
        timeline.SetRate(1d);
        Console.WriteLine($"  back at rate 1: advancing = {timeline.IsAdvancing}");

        // 5. 每次查找都新建实例，注册以契约为键。
        var a = TimerCore.CreateTimeSource<ITimeSourceControl>();
        var b = TimerCore.CreateTimeSource<ITimeSourceControl>();
        Console.WriteLine($"5 fresh instance per lookup: {!ReferenceEquals(a, b)}");
        try
        {
            TimerCore.CreateTimeSource<IMarker>();
        }
        catch (InvalidOperationException)
        {
            Console.WriteLine("  an unregistered contract throws InvalidOperationException");
        }
    }

    private interface IMarker : ITimeSourceControl { }
}
```

## 8. 运行声明

- ✅ **已于 2026-10-01 实际构建并运行**，源码取自本页 §7，`Release`，`net9.0`，Windows 11。记录输出：

```text
1 source = TimeSourceCore, unit = 10000000 ticks/s, advancing = True
  first sample covers the interval since construction: 0.141 ms
  measured delta after ~50 ms: 63.8 ms, total 64.0 ms
2 default step = 16 ms, max/call = 8, max pending = 64
  steps delivered after ~100 ms: 6, pending = 0, dropped = 0
3 after Pause: paused = True, advancing = False, parked wait already done = False
  position frozen across a 50 ms sleep: True
  a paused source no longer advances: True
  after Resume: advancing = True, parked wait released
4 at rate 0: paused = False, advancing = False
  back at rate 1: advancing = True
5 fresh instance per lookup: True
  an unregistered contract throws InvalidOperationException
```

§2–§6 的每一条预期结果都在这份输出中成立。两点诚实说明：墙钟数值（`0.141` / `63.8` / `6` 步）依赖计时，每次运行都会不同 —— 被断言的只是它们之间的*关系*；程序是链接到预构建的 `VeloxDev.Core` 程序集而不是项目，因为撰写时该项目 `net5.0` 目标在 `WorkflowSystem/Templates/Helpers/TreeHelper.cs` 里有一个无关的编译错误 —— 不在本特性范围内，也不在本页范围内。

这些类型的引擎级核验见 `Src/Core/VeloxDev.Core.Test/Timing/`（6 个文件，含 `TimeSourceContractTests`、`HostTimeSourceTests`、`CompensatingTimeSamplerTests`、`UncompensatedTimeSamplerTests`、`TimerCoreRegistryTests`）与[验证与完整代码](../08_验证与完整代码/index.md)。
