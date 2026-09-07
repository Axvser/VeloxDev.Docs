# Transition — Execute & Control

## 1. Start a snapshot (one-shot)

Call the snapshot's `Execute` extension (namespace `VeloxDev.TransitionSystem`). Execution returns immediately and drives the frame loop in the background:

```csharp
using VeloxDev.TransitionSystem;

Animation0.Execute(rect);                  // mutual-exclusive (default): CanMutualTask: true
Animation0.Execute(rect, CanMutualTask: false); // run concurrently with other animations
Transition<Rectangle>.Execute(rect, Animation0); // static alternative
```

`Execute` on a *UI-bound* target can be called from the UI thread **or** from a background thread — the per-framework `UIThreadInspector` derives the owning UI thread from the target and marshals each frame write (see [UI Thread & Marshaling](../06_ui-thread-marshaling/index.md)). The demos exercise both entry points, e.g. the WPF demo starts the exact same animation with `Animation0.Execute(Rec0)` on the UI thread and inside `Task.Run(...)`.

**Expected result:** the recorded properties interpolate from their current values to the targets over the effect's duration/easing. The call returns before the animation finishes.

## 2. Mutual exclusion vs. parallel

A target has one **mutual** scheduler: while a `CanMutualTask: true` animation runs, starting another animation on the same target **cancels the running one** first (`scheduler.Exit()` is called before the new run). This is why the demos' "repeat" buttons restart an animation cleanly on each click.

To run several animations on one target at the same time, pass `CanMutualTask: false`. Each parallel run gets its own scheduler, and the engine tracks them so a later `Exit` can stop them:

```csharp
Animation0.Execute(rect, CanMutualTask: false);
Animation1.Execute(rect, CanMutualTask: false);   // both run concurrently
```

**Expected result:** with `CanMutualTask: false` neither animation cancels the other, and both advance toward their own targets.

## 3. Stop in place — `Transition.Exit`

`Transition.Exit(target)` cancels the target's running animations and leaves the property where it currently is (it does *not* jump to the snapshot's end value). The two flags select which schedulers to stop:

- `IncludeMutual: true` — the single mutual scheduler (the default).
- `IncludeNoMutual: true` — all parallel (`CanMutualTask: false`) schedulers.

```csharp
Transition.Exit(rect);                                   // mutual only
Transition.Exit(rect, IncludeMutual: true, IncludeNoMutual: true); // stop everything
```

**Expected result:** the animation freezes in place. A subsequent `Execute` on the same target starts afresh from the frozen values.

## 4. The per-target scheduler

Every `Execute` resolves a scheduler for the target via `TransitionSchedulerCore<...>.FindOrCreate(target, CanMutualTask)`. Mutual schedulers are cached per target in a `ConditionalWeakTable` (so they vanish with the target); no-mutual schedulers are created per run and released when the effect's `Finally` fires. The scheduler serializes access through a `SemaphoreSlim`, holds the animation's `CancellationTokenSource`, and hands the interpolator/interpreter the prepared `SamplerSet`. You normally never touch it, but you can address it directly with the static lookup helpers if needed:

```csharp
using VeloxDev.TransitionSystem.Abstractions;   // TransitionSchedulerCore

if (TransitionSchedulerCore.TryGetMutualScheduler(rect, out var mutual))
{
    mutual.Exit();   // cancel the running mutual animation
}
```

**Expected result:** querying the target after an animation starts returns its live scheduler; `Exit()` on it cancels the current run (equivalent to `Transition.Exit(rect)`).
