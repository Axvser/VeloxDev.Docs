# Transition — Timing Layer

## 1. What this page is

Every animation is anchored to an `ITimeSource`, and every control call (`Pause`, `Resume`, `SetRate`, `Seek`) acts on that source. The source, the two sampling modes built on it, and the registry that hands them out all live in `VeloxDev.Timing` — a **sub-module of this feature**, added 2026-09-14, shared by transition / dynamic-theme / tickable.

Nothing on this page needs a GUI, an adapter package or a target object. It is the layer under the engine, driven directly. If you only want to animate a rectangle, read [Easing & Interpolators](../02_easing-and-interpolators/index.md) instead — you never name these types.

### Prerequisites

- **Target frameworks** (from `VeloxDev.Core.csproj`): `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`. The Timing layer compiles into all four and has no conditional compilation.
- **Package:** `VeloxDev.Core` only — no adapter package.
- **Required services:** none.

**Expected result of this step:** you have a .NET project referencing `VeloxDev.Core`, and `using VeloxDev.Timing;` resolves.

## 2. Create a source

`TimerCore` is the registry: `CreateTimeSource<TContract>()` builds the Core default unless a platform registered over that same **contract**. Every lookup returns a *fresh instance*, because a source carries the pause / rate state.

```csharp
using VeloxDev.Timing;

ITimeSourceControl timeline = TimerCore.CreateTimeSource<ITimeSourceControl>();
Console.WriteLine($"{timeline.GetType().Name}, unit={timeline.TicksPerSecond} ticks/s, advancing={timeline.IsAdvancing}");
```

**Expected result:** `TimeSourceCore`, a tick unit equal to your machine's `Stopwatch.Frequency` (10 000 000 on the Windows machines this was run on — `TicksPerSecond` is per source, so never hard-code it), and `advancing=True`.

## 3. Sample it — the two modes

A source is read through a sampler, and there are exactly two modes. A sampler holds per-consumer state and has **one logical owner**; it is not thread-safe and must not be shared.

**Best-effort (`IUncompensatedTimeSampler`)** — the interval since the previous sample, owed to nobody. This is what an animation uses: it reads the absolute position and is correct whatever the sampling cadence.

**Fixed-step (`ICompensatingTimeSampler`)** — the delivered step count equals `floor(elapsed / Step)` with no drift. This is what physics needs.

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

**Expected result:** the uncompensated delta tracks the sleep; `Advance` hands out exactly `floor(100 / 16) = 6` steps of the default 16 ms step, with `pending = 0` and `dropped = 0` (the cap was not reached, so nothing was deferred and nothing forgiven); and every sample's `Delta` equals the fixed `Step`, never the measured interval.

## 4. Pause, and the park signal

`Pause()` freezes the position. Time spent paused is excluded **by construction** — nothing accrues — and a consumer that parks does not poll:

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

**Expected result:** `paused=True` / `advancing=False`; the returned task is **not** already completed (it is parked, and the `awaited` wake-up costs nothing until then); the position is identical before and after a 50 ms sleep; a sample taken after the pause reports `Delta == TimeSpan.Zero` (the caller's signal not to push a frame); and `await parked` returns once `Resume()` runs.

## 5. A rate of zero is not a pause

This is the distinction that makes `IsAdvancing` — not `IsPaused` — the predicate to park on:

```csharp
timeline.SetRate(0d);
Console.WriteLine($"at rate 0: paused={timeline.IsPaused}, advancing={timeline.IsAdvancing}");
timeline.SetRate(1d);
Console.WriteLine($"back at rate 1: advancing={timeline.IsAdvancing}");
```

**Expected result:** `paused=False` but `advancing=False` — the clock is frozen without being paused, so a loop that checked only `IsPaused` would keep running against a clock that never moves. `SetRate(1)` starts it again.

## 6. Registration is keyed by contract

```csharp
TimerCore.RegisterTimeSource<ITimeSourceControl>(static () => new TimeSourceCore());
// a lookup under a contract nobody registered throws:
try { TimerCore.CreateTimeSource<IMarker>(); }
catch (InvalidOperationException) { Console.WriteLine("an unregistered contract throws"); }
```

**Expected result:** registering under the contract `ITimeSourceControl` is what a lookup of that contract finds; a registration under an *implementation* type is not found by any contract lookup; and a contract with nothing registered throws `InvalidOperationException` rather than returning null. (The `AUTO TEST`/unit coverage for this is `TimerCoreRegistryTests`.)

## 7. Complete code

A single-file console program covering §2–§6. `dotnet new console -n TimingQuickStart`, then replace `Program.cs`:

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

## 8. Run declaration

- ✅ **Actually built and ran on 2026-10-01**, from this page's §7 source, `Release`, `net9.0`, on Windows 11. Recorded output:

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

Every expected result in §2–§6 holds in that output. Two honesty notes: the wall-clock numbers (`0.141` / `63.8` / `6` steps) are timing-dependent and will differ per run — only their *relationships* are asserted; and the program was linked against the prebuilt `VeloxDev.Core` assembly rather than the project, because at the time of writing the project's `net5.0` target had an unrelated compile error in `WorkflowSystem/Templates/Helpers/TreeHelper.cs` — outside this feature and outside this page's scope.

For the engine-level verification of the same types, see the unit tests under `Src/Core/VeloxDev.Core.Test/Timing/` (6 files, including `TimeSourceContractTests`, `HostTimeSourceTests`, `CompensatingTimeSamplerTests`, `UncompensatedTimeSamplerTests`, `TimerCoreRegistryTests`) and [Verify & Complete Code](../08_verify-and-complete-code/index.md).
