# Transition — Execute & Control

## 1. Start a transition (one-shot)

Call the transition's `Execute(target, CanMutualTask)` instance method (inherited from `StateSnapshotCore<T>`, namespace `VeloxDev.TransitionSystem.Abstractions`). Execution returns immediately and drives the frame loop in the background:

```csharp
using VeloxDev.TransitionSystem;

Animation0.Execute(rect);                       // mutual-exclusive (default): CanMutualTask: true
Animation0.Execute(rect, CanMutualTask: false); // run concurrently with other animations
```

A static batch entry also exists — `Transition<T>.Execute(T target, IEnumerable<Transition<T>> values, bool CanMutualTask = false)` — and runs each transition in the batch; it is source-verified in `Transition.cs` but not exercised by the demos.

`Execute` on a *UI-bound* target can be called from the UI thread **or** from a background thread — the adapter's host derives the owning UI thread from the target and marshals each frame write (see [UI Thread & Marshaling](../06_ui-thread-marshaling/index.md)). The demos exercise both entry points, e.g. the WPF demo starts the exact same animation with `Animation0.Execute(Rec0)` on the UI thread and inside `Task.Run(...)`.

**Expected result:** the recorded properties interpolate from their current values to the targets over the effect's duration/easing. The call returns before the animation finishes.

## 2. Mutual exclusion vs. parallel

A target has one **mutual** scheduler: while a `CanMutualTask: true` animation runs, starting another animation on the same target **cancels the running one** first. This is why the demos' "repeat" buttons restart an animation cleanly on each click.

To run several animations on one target at the same time, pass `CanMutualTask: false`. Each parallel run gets its own scheduler, and the engine tracks them so a later `Exit` can stop them:

```csharp
Animation0.Execute(rect, CanMutualTask: false);
Animation1.Execute(rect, CanMutualTask: false);   // both run concurrently
```

The load-bearing observable is `TransitionScheduler.TryGetNoMutualScheduler(target, out var schedulers)` — the returned array's **length** counts the concurrent runs still registered. The mutual table, by contrast, is cached per target for its lifetime and is never cleared, so `TryGetMutualScheduler` returning true only means "this target has run a mutual animation".

**Expected result:** with `CanMutualTask: false` neither animation cancels the other, and both advance toward their own targets.

## 3. Share one timeline between animations

`Execute` also has an overload that takes the timeline to anchor the run to:

```csharp
using VeloxDev.Timing;

ITimeSourceControl timeline = new TimeSourceCore();
Animation0.Execute(rect0, timeline);
Animation1.Execute(rect1, timeline);   // same transport
```

Animations sharing a timeline share a transport: pausing, changing the rate or seeking **one** moves all of them together, while each keeps its own pass and its own place in it. That is what a choreographed group needs — several animations staying in lockstep without any of them knowing about the others. Without the overload, every run gets its own private source from `TimerCore.CreateTimeSource<ITimeSourceControl>()`.

**Expected result:** `Transition.Pause(rect0, IncludeMutual: true, IncludeNoMutual: true)` freezes *both* rectangles, because both runs read the same source. `Transition.Exit(rect0, ...)` still stops only `rect0` — exit cancels runs, not the clock.

## 4. Stop in place — `Transition.Exit`

`Transition.Exit(target)` cancels the target's running animations and leaves the property where it currently is (it does *not* jump to the transition's end value). The two flags select which schedulers to stop:

- `IncludeMutual: true` — the single mutual scheduler (the default).
- `IncludeNoMutual: true` — all parallel (`CanMutualTask: false`) schedulers.

```csharp
Transition.Exit(rect);                                   // mutual only
Transition.Exit(rect, IncludeMutual: true, IncludeNoMutual: true); // stop everything
```

Cancellation is a **signal**: the run stops at its next await, so it may still be releasing its scheduler when `Exit` returns. That is fine for a following mutual `Execute`, which queues on the scheduler's own gate behind the cancelled run.

**Expected result:** the animation freezes in place (verified by the `AUTO TEST` case `LoadModes_MatchTheLibrarySemantics`, "停止全部把目标冻在原地"). A subsequent `Execute` on the same target starts afresh from the frozen values.

## 5. Steer a running animation

`Exit` stops a run; the rest of the transport **moves** one while keeping it alive. All of it is static on `Transition`, addressed by target, and takes the same two flags as `Exit` to select which schedulers to reach.

| Call | Effect |
|---|---|
| `Transition.Pause(target)` | freezes the run where it is |
| `Transition.Resume(target)` | continues, at the rate it was last set to |
| `Transition.SetRate(target, 0.5)` | halves the speed without moving the position; a `0` rate freezes the clock without pausing it (`IsPaused` stays false, and `Resume` does not make it advance) |
| `Transition.Seek(target, TimeSpan)` | jumps to a position inside the current pass, keeping the rate |
| `Transition.Seek(target, cycle, TimeSpan)` | jumps into the pass numbered `cycle` |
| `Transition.Position(target)` | how far into the current pass — a `TimeSpan` |
| `Transition.Cycle(target)` | which pass is playing — an `int` |
| `Transition.IsPaused(target)` | whether **every** animation on the target is paused |
| `Transition.Rate(target)` | the rate it is set to |

```csharp
Transition.Pause(rect);
Transition.SetRate(rect, 0.5);          // remembered while paused, applied on Resume
Transition.Seek(rect, TimeSpan.FromMilliseconds(300));
Transition.Resume(rect);
```

Six properties of the contract, each of which a caller meets the moment they use it:

- **A pause is excluded from the animation, not skipped.** The clock stops accruing, so a pause of any length leaves the remaining duration unchanged — and a paused animation costs **no timer wake-ups**, because its sampling loop parks on a signal.
- **`SetRate` does not move the position.** The timeline rebases before the rate changes, which is why a change during playback is seamless. A rate set while paused is remembered and takes effect on `Resume`.
- **Time only moves forwards.** There is no reverse playback: a negative rate is **rejected** with an `ArgumentOutOfRangeException`, not clamped. To go back to a point, `Seek` there.
- **Seeking past the end of a pass finishes it**, landing exactly on the endpoint rather than being clamped; a negative position is pinned to that pass's start.
- **A pass has a number, not only a time.** Seeking by `cycle` exists because an absolute timeline cannot otherwise name a pass — a zero-duration pass consumes no time at all. Jumping past the last pass the effect allows finishes the animation, exactly as running off the end would.
- **Seeking while paused draws the new position without resuming.**

The three readers answer for *nothing running* rather than throwing: `Cycle` gives `0`, `Position` gives `TimeSpan.Zero`, `Rate` gives `0`, and `IsPaused` gives `false`.

```csharp
// the demo's "next pass" button
Transition.Seek(rect, Transition.Cycle(rect, IncludeMutual: true, IncludeNoMutual: true) + 1,
    TimeSpan.Zero, IncludeMutual: true, IncludeNoMutual: true);
```

**Expected result:** the readout (`paused` / `rate` / `pos` / `cycle`) tracks what you asked for, and `Exit` still stops the run from any of these states.

*Verified by:* `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` — its control panel drives `Pause` / `Resume` / `SetRate` / `Seek` over a live `IsPaused` / `Rate` / `Position` / `Cycle` readout. The `AUTO TEST` case `TimelineControl_SteersTheRunningAnimation` asserts the same behaviour on all seven platforms: pause freezes the position and keeps it frozen, resume advances it, a quarter speed covers visibly less of the same wall clock, and a jump to another pass moves `cycle`.

## 6. The per-target scheduler

Every `Execute` resolves a scheduler for the target via `TransitionSchedulerCore<THost, TTransitionInterpreterCore, TPriorityCore>.FindOrCreate(target, CanMutualTask)`. Mutual schedulers are cached per target in a `ConditionalWeakTable` (so they vanish with the target); no-mutual schedulers are created per run and registered/unregistered over the **whole** animation — including the `Await` gaps between segments — so an `Exit` during a gap still finds and cancels them. The scheduler serializes access through a `SemaphoreSlim`, tracks every live run of the animation, and hands the interpreter the prepared `SamplerSet<TPriorityCore>`. You normally never touch it, but you can address it directly with the static lookup helpers if needed:

```csharp
using VeloxDev.TransitionSystem.Abstractions;   // TransitionSchedulerCore

if (TransitionSchedulerCore.TryGetMutualScheduler(rect, out var mutual))
{
    mutual.Exit();   // cancel the running mutual animation
}
```

The scheduler also carries the two members a chain's loops are built on: `ExecuteCapturing`, which runs one segment and hands back the frame set it prepared, and `Replay(frameSet, effect)`, which runs that segment again against the **same** endpoints (the target is not re-read and `Awake` is not re-raised). `Repeat` is the only reader of that pair.

**Expected result:** querying the target after an animation starts returns its live scheduler; `Exit()` on it cancels the current run (equivalent to `Transition.Exit(rect)`).

## 7. The adapter's half: `InterpolatorCore.CreateScheduler`

A scheduler's *type arguments* — the host, the interpreter, the dispatcher priority — are fixed per platform. `Transition<T>` is a closed `TransitionCore<...>` whose last three type arguments are exactly those, so `Transition<T>.Execute` names them without asking anyone. A caller that knows its target only as an `object` cannot, so the adapter exposes the same resolution as a virtual on its interpolator:

```csharp
namespace VeloxDev.TransitionSystem.Abstractions;

public abstract class InterpolatorCore
{
    public virtual TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect) => null;
}
```

The theme system ([Dynamic Theme](../../04_dynamic-theme/index.md)) is the caller that needs it — it drives one switch across targets of many runtime types, so it asks the interpolator which scheduler to animate a given target with. `Transition<T>.Execute` does not go through it, because `T` already names the type arguments. Three points the contract carries:

- **Every adapter overrides it** (`PlatformAdapters/Interpolator.cs`), each answering with its own host / `TransitionInterpreter` / priority triple — `DispatcherPriority` for WPF, Avalonia and Jalium; `DispatcherQueuePriority` for WinUI; `NonPriority` for MAUI, WinForms and Razor.
- **`null` is an honest answer**, both for "this platform has not opted in" and for "this effect does not belong to this platform" (the override casts the effect, so the answer mirrors the cast the scheduler itself performs before running). The caller then switches without animating, rather than starting a run that draws nothing.
- **An implementation must go through `TransitionSchedulerCore<...>.FindOrCreate`, never `new`** — only that path files the scheduler under the target, which is what lets a later `Transition.Pause` / `Seek` / `Exit` find the animation.

As a QuickStart reader you normally write nothing here: the adapter package already implements it. You meet it when you write an adapter of your own, or when a theme switch does not animate.
