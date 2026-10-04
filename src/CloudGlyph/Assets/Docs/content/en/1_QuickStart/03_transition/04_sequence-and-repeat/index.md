# Transition — Sequence & Repeat

## 1. Timing, FPS and loop semantics

One `TransitionEffect` drives one segment. Its timing members (from `TransitionEffectCore`):

- `Duration` — wall-clock length of one pass. `Duration = TimeSpan.Zero` jumps straight to the end (how `TransitionEffects.Empty` resets an object instantly).
- `FPS` — the *maximum* sample rate (default `60`). The interpreter's yield interval is `1000 / FPS` ms, but elapsed time comes from the run's timeline, so `FPS` is a cap, not a frame grid.
- `IsAutoReverse` — after the forward pass, play the same pass backwards.
- `LoopTime` — number of *additional* cycles after the first. The engine plays cycles `0..LoopTime`, i.e. `LoopTime + 1` forward passes (each followed by a reverse pass when `IsAutoReverse` is set). The demos use `LoopTime: 2` + `IsAutoReverse: true` for three forth-and-back passes. `LoopTime = int.MaxValue` means **loop forever**.
- `Ease` — `IEaseCalculator`, default `Eases.Default`.

**Expected result:** a 2-second `LoopTime: 2` + `IsAutoReverse: true` effect runs three forward passes and three reverse passes and then fires `Completed`.

## 2. Chain segments into a timeline

Chain additional segments with three fluent calls (each segment has its own state + effect):

- `.Await(timeSpan)` — wait before playing **this** segment (used as the first call to delay the whole animation).
- `.Then()` — start the next segment immediately after this one.
- `.AwaitThen(timeSpan)` — wait `timeSpan`, then start the next segment.

```csharp
Transition<Rectangle>.Create()
    .Property(r => r.RenderTransform,
        [new TranslateTransform(200, 0), new ScaleTransform(1.3, 1.3)])
    .Effect(new TransitionEffect
    {
        Duration = TimeSpan.FromSeconds(2),
        IsAutoReverse = true,
        FPS = 144,
        Ease = Eases.Circ.InOut,
        LoopTime = 2,
    })
    .AwaitThen(TimeSpan.FromSeconds(5))   // wait 5 s, then the second segment
    .Property(r => r.Fill, new SolidColorBrush(Colors.Yellow))
    .Effect(new TransitionEffect
    {
        Duration = TimeSpan.FromSeconds(2),
        Ease = Eases.Sine.In,
    });
```

This is `Animation2` from the WPF demo. When executed, the interpreter walks the linked segments in order, honoring each one's lead-in delay, so the whole chain plays as one timeline. The lead-in wait is measured against the **wall clock** and re-evaluated after every wake, so the part of a delay that passes while the run is paused is not consumed.

**Expected result:** the first segment moves and scales the rectangle for 2 seconds (144 FPS cap, circular ease, three forth-and-back passes); a 5-second pause follows; then the second segment fades the fill in with `Eases.Sine.In`.

## 3. Repeat a chain — `Repeat(n)`

`LoopTime` repeats one segment's **passes**; `Repeat(count)` repeats a segment's **loop**, which wraps the chain from the first segment through this one. `0` — the default — runs it once, and `int.MaxValue` runs it forever.

```csharp
Transition<Rectangle>.Create()
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 200d)
    .Effect(new TransitionEffect { Duration = TimeSpan.FromSeconds(1) })
    .AwaitThen(TimeSpan.FromMilliseconds(250))
    .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
    .Effect(new TransitionEffect { Duration = TimeSpan.FromMilliseconds(500) })
    .Repeat(2);            // the whole two-segment chain, three times over
```

Loops **nest by where they end**: three segments each carrying `Repeat(1)` run `1, 1, 2, 1, 1, 2, 3, 1, 1, 2, 1, 1, 2, 3`. So only a count on the **last** segment repeats the whole chain.

Two consequences worth knowing:

- A repeated segment replays the frame set its **first** iteration prepared, rather than re-reading the target. Without that, a chain whose endpoint differs from its start would walk backwards, and a segment writing a property no earlier segment touched would drift a little per iteration.
- `Awake` does **not** re-raise on a replay. `Start`, `Update`, `LateUpdate`, `Completed` and the diagnostics fire exactly as they do for any other pass, so a replay is observable the same way a pass is.

**Expected result:** the two segments play, then repeat twice more, then the run completes — with no drift between iterations.

## 4. Presets and effect events

`TransitionEffects` ships three mutable presets of the adapter's `TransitionEffect`: `Empty` (zero duration — instant jump), `Theme` (0.46 s) and `Hover` (0.32 s). Override any property on a copy before executing — the demos reset an object by playing a declared state list under `Empty`:

```csharp
// The initial state, declared explicitly (see "Declare State Explicitly"):
private static readonly Transition<Rectangle> Reset =
    Transition<Rectangle>.Create()
        .Property(r => r.Opacity, 1d)
        .Property(r => r.Fill, new SolidColorBrush(Colors.Cyan));

// ... later, restore it instantly:
Reset.Effect(TransitionEffects.Empty).Execute(rect);
```

There is no capture step, so the reset list is part of the source and must be kept in step with the animation's own declared targets.

An effect raises lifecycle events (all `EventHandler<TransitionEventArgs>`; with its base `TimeLineEventArgs` that argument carries `Handled` — set it to `true` to stop the current pass — plus the frame's `DeltaTime` / `TotalTime`, while `Loop` / `Cycle` say where the run is):

- `Awaked` — once, when the scheduler begins (before value normalization).
- `Start` — once per interpreter run, when the sampling loop starts.
- `Update` — before each frame's value write; `LateUpdate` — right after it.
- `Completed` — after the last pass finishes normally.
- `Canceled` — when interrupted (new mutual animation, `Transition.Exit`, or `Handled = true`).
- `Finally` — always fires on *any* end path, after `Completed` or `Canceled`.

Two more events report **diagnostics** rather than lifecycle. Each `stage` is reported at most once per run, so a per-frame condition does not spam:

```csharp
var effect = new TransitionEffect
{
    Duration = TimeSpan.FromSeconds(1),
    Ease = Eases.Sine.InOut,
};
effect.Start += (_, _) => Console.WriteLine("start");
effect.Completed += (_, _) => Console.WriteLine("completed");
effect.Canceled += (_, _) => Console.WriteLine("canceled");
effect.Finally += (_, _) => Console.WriteLine("finally");
effect.Warn += (_, e) => Console.WriteLine($"degraded @{e.Stage}: {e.Value}");   // dropped frame, skipped path, unsampled property
effect.Error += (_, e) => Console.WriteLine($"failed @{e.Stage}: {e.Value}");   // a throwing callback / sampler / host
```

**Expected result:** a clean run prints `start`, then `completed` then `finally`; interrupting it prints `start`, `canceled`, `finally`; a run whose declared path does not match the target's runtime type prints one `degraded @Unreadable` line and carries on. The lifecycle handlers are backed by `WeakDelegate`, so holding an effect does not leak the target.

Next: [Execute & Control](../05_execute-and-control/index.md) shows how a transition (or chain) is actually started, cancelled and steered.
