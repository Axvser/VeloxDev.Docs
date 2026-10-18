# 过渡动画 — 时间层

## 1. 本页是什么

每个动画都锚定到一个 `ITimeSource`，每个控制调用（`Pause`、`Resume`、`SetRate`、`Seek`）都作用于该源。源、建在它之上的两种采样模式，以及分发它们的注册表，都位于 `VeloxDev.Timing` —— 本特性的一个**子模块**（2026-09-14 加入），由过渡动画 / 动态主题 / Tickable 共享。

本页不需要 GUI、适配器包或目标对象。它是引擎之下的一层，直接驱动。如果你只想动画一个矩形，读[缓动与插值器](../02_缓动与插值器/index.md)即可 —— 你永远不会命名这些类型。

### 前置条件

- **目标框架**（来自 `VeloxDev.Core.csproj`）：`netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` / `net8.0`。时间层编译进全部目标，没有条件编译。
- **包：** 仅 `VeloxDev.Core` —— 无需适配器包。
- **必需服务：** 无。

**本步预期结果：** 你有一个引用 `VeloxDev.Core` 的 .NET 项目，且 `using VeloxDev.Timing;` 可解析。

## 2. 创建时间源

`TimerCore` 是注册表：`CreateTimeSource<TContract>()` 构建 Core 默认实现，除非某平台注册到同一**契约**上。每次查找都返回*新实例*，因为源携带暂停 / 速率状态。

```csharp
using VeloxDev.Timing;

ITimeSourceControl timeline = TimerCore.CreateTimeSource<ITimeSourceControl>();
Console.WriteLine($"{timeline.GetType().Name}, unit={timeline.TicksPerSecond} ticks/s, advancing={timeline.IsAdvancing}");
```

**预期结果：** `TimeSourceCore`，tick 单位等于本机 `Stopwatch.Frequency`（在本次运行所用的 Windows 机器上是 10 000 000 —— `TicksPerSecond` 是每源的，永远不要硬编码），且 `advancing=True`。

## 3. 采样 —— 两种模式

源经采样器读取，且恰好有两种模式。采样器持有逐消费者状态，且有**一个逻辑所有者**；它不是线程安全的，不得共享。

**尽力而为（`IUncompensatedTimeSampler`）** —— 距上一次采样的间隔，不欠任何人。动画使用它：它读取绝对位置，无论采样节奏如何都正确。

**固定步长（`ICompensatingTimeSampler`）** —— 交付的步数等于 `floor(elapsed / Step)`，无漂移。物理需要它。

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

**预期结果：** 未补偿 delta 跟随睡眠；`Advance` 恰好交出 `floor(100 / 16) = 6` 个默认 16 ms 步，`pending = 0`、`dropped = 0`（未触及上限，因此既没有延期也没有豁免）；且每个采样的 `Delta` 都等于固定 `Step`，绝不是实测间隔。

## 4. 暂停与停泊信号

`Pause()` 冻结位置。暂停期间的时间**按构造**被排除 —— 不累积 —— 且停泊的消费者不轮询：

```csharp
timeline.Pause();
var parked = timeline.WaitWhileStalledAsync();
Console.WriteLine($"paused={timeline.IsPaused}, advancing={timeline.IsAdvancing}, parked already done={parked.IsCompleted}");

var frozen = timeline.Position;
Thread.Sleep(50);
Console.WriteLine($"position frozen across a 50 ms sleep: {timeline.Position == frozen}");

_ = uncompensated.Sample();                               // whatever accrued before the pause
Console.WriteLine($"a paused source no longer advances: {uncompensated.Sample().Delta == TimeSpan.Zero}");

timeline.Resume();
await parked;
Console.WriteLine($"after Resume: advancing={timeline.IsAdvancing}, parked wait released");
```

**预期结果：** `paused=True` / `advancing=False`；返回的任务**尚未**完成（它停泊着，`await` 的唤醒在此之前不花代价）；50 ms 睡眠前后位置相同；暂停后取样的 `Delta == TimeSpan.Zero`（调用方不推帧的信号）；`await parked` 在 `Resume()` 后返回。

## 5. 速率为零不是暂停

这是让 `IsAdvancing` —— 而不是 `IsPaused` —— 成为停泊谓词的区分：

```csharp
timeline.SetRate(0d);
Console.WriteLine($"at rate 0: paused={timeline.IsPaused}, advancing={timeline.IsAdvancing}");
timeline.SetRate(1d);
Console.WriteLine($"back at rate 1: advancing={timeline.IsAdvancing}");
```

**预期结果：** `paused=False` 但 `advancing=False` —— 时钟被冻结却没有暂停，因此只检查 `IsPaused` 的循环会对着一个永不移动的时钟继续跑。`SetRate(1)` 让它重新开始。

## 6. 注册以契约为键

```csharp
TimerCore.RegisterTimeSource<ITimeSourceControl>(static () => new TimeSourceCore());
// a lookup under a contract nobody registered throws:
try { TimerCore.CreateTimeSource<IMarker>(); }
catch (InvalidOperationException) { Console.WriteLine("an unregistered contract throws"); }
```

**预期结果：** 注册在契约 `ITimeSourceControl` 下，正是该契约的查找能找到的；注册在*实现*类型下不会被任何契约查找找到；没有任何注册的契约抛 `InvalidOperationException` 而不是返回 null。（单元覆盖为 `TimerCoreRegistryTests`。）

## 7. 完整代码

一个覆盖 §2–§6 的单文件控制台程序。`dotnet new console -n TimingQuickStart`，然后替换 `Program.cs`：

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
        // 1. A source, and the two sampling modes built on it.
        ITimeSourceControl timeline = TimerCore.CreateTimeSource<ITimeSourceControl>();
        Console.WriteLine($"1 source = {timeline.GetType().Name}, unit = {timeline.TicksPerSecond} ticks/s, advancing = {timeline.IsAdvancing}");

        var uncompensated = TimerCore.CreateTimeSampler<IUncompensatedTimeSampler>(timeline);
        var first = uncompensated.Sample();
        Console.WriteLine($"  first sample covers the interval since construction: {first.Delta.TotalMilliseconds:F3} ms");

        Thread.Sleep(50);
        var second = uncompensated.Sample();
        Console.WriteLine($"  measured delta after ~50 ms: {second.Delta.TotalMilliseconds:F1} ms, total {second.Total.TotalMilliseconds:F1} ms");

        // 2. Fixed-step sampling repays what it owes: the delivered count is floor(elapsed / step).
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

        // 3. A pause is excluded by construction, and a paused consumer parks instead of polling.
        timeline.Pause();
        var parked = timeline.WaitWhileStalledAsync();
        Console.WriteLine($"3 after Pause: paused = {timeline.IsPaused}, advancing = {timeline.IsAdvancing}, parked wait already done = {parked.IsCompleted}");

        var frozen = timeline.Position;
        Thread.Sleep(50);
        Console.WriteLine($"  position frozen across a 50 ms sleep: {timeline.Position == frozen}");
        _ = uncompensated.Sample();   // whatever accrued before the pause
        Console.WriteLine($"  a paused source no longer advances: {uncompensated.Sample().Delta == TimeSpan.Zero}");

        timeline.Resume();
        await parked;
        Console.WriteLine($"  after Resume: advancing = {timeline.IsAdvancing}, parked wait released");

        // 4. A rate of zero freezes the clock without pausing it.
        timeline.SetRate(0d);
        Console.WriteLine($"4 at rate 0: paused = {timeline.IsPaused}, advancing = {timeline.IsAdvancing}");
        timeline.SetRate(1d);
        Console.WriteLine($"  back at rate 1: advancing = {timeline.IsAdvancing}");

        // 5. Every lookup builds a fresh instance, and registration is keyed by contract.
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

- ✅ **2026-10-01 实际构建并运行过**（记录转自英文页），本页 §7 源码，`Release`、`net9.0`、Windows 11。记录输出：

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

§2–§6 的每个预期结果都在该输出中成立。两条诚实说明：墙钟数字（`0.141` / `63.8` / `6` 步）依赖时序，每次运行会不同 —— 只断言它们的*关系*；该程序当时链接的是预构建的 `VeloxDev.Core` 程序集而不是项目，因为写作时项目的 `net5.0` 目标在 `WorkflowSystem/Templates/Helpers/TreeHelper.cs` 有一个与本节无关的编译错误。

本次文档更新（2026-10-18）**没有**重新运行这个独立控制台程序；同层契约由 `Src/Core/VeloxDev.Core.Test/Timing/*`（6 个文件、属于本次实际运行的 287 个用例）覆盖。

引擎级验证见 `Src/Core/VeloxDev.Core.Test/Timing/`（6 个文件，包括 `TimeSourceContractTests`、`HostTimeSourceTests`、`CompensatingTimeSamplerTests`、`UncompensatedTimeSamplerTests`、`TimerCoreRegistryTests`）与[验证与完整代码](../08_验证与完整代码/index.md)。
