# Transition — Sequence & Repeat

## 1. Timing, FPS and loop semantics

One `TransitionEffect` drives one segment. Its timing members (from `TransitionEffectCore`):

- `Duration` — wall-clock length of one pass. `Duration = TimeSpan.Zero` jumps straight to the end (how `TransitionEffects.Empty` resets an object instantly).
- `FPS` — the *maximum* sample rate (default `60`). The interpreter's yield interval is `1000 / FPS` ms, but elapsed time comes from a `Stopwatch`, so `FPS` is a cap, not a frame grid.
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

This is `Animation2` from the WPF demo. When executed, the interpreter walks the linked segments in order, honoring each one's lead-in delay (`spans` are dequeued before every segment), so the whole chain plays as one timeline.

**Expected result:** the first segment moves and scales the rectangle for 2 seconds (144 FPS cap, circular ease, three forth-and-back passes); a 5-second pause follows; then the second segment fades the fill in with `Eases.Sine.In`.

## 3. Presets and effect events

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

An effect raises lifecycle events (all `EventHandler<TransitionEventArgs>`, where `TransitionEventArgs` carries `Handled` — set it to `true` to stop the current pass):

- `Awaked` — once, when the scheduler begins (before value normalization).
- `Start` — once per interpreter run, when the sampling loop starts.
- `Update` — before each frame's value write; `LateUpdate` — right after it.
- `Completed` — after the last pass finishes normally.
- `Canceled` — when interrupted (new mutual animation, `Transition.Exit`, or `Handled = true`).
- `Finally` — always fires on *any* end path, after `Completed` or `Canceled`. (No-mutual scheduler bookkeeping is released by the run itself, not by this event.)

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
```

**Expected result:** running the animation prints `start`, then `completed` then `finally` on a clean run; interrupting it prints `start`, `canceled`, `finally`. The event handlers are backed by `WeakDelegate`, so holding an effect does not leak the target.

Next: [Execute & Control](../05_execute-and-control/index.md) shows how a transition (or chain) is actually started, cancelled and run in parallel.
