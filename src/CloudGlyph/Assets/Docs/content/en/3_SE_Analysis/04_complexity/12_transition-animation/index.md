# Transition animation

A transition is a chain of segments, each with one effect and one sampler set. Startup flattens the chain and prepares one sampler entry per animated property. After that the cost is per frame: one easing evaluation, one sampler call per property, and one host dispatch. With $t$ concurrent transitions and $k$ properties each, a frame costs $O(t k)$ — and each transition owns one timer, so wake-ups are also proportional to $t$.

Notation: $s$ segments in one chain, $k_s$ properties in segment $s$, $t$ active transitions, $h$ lifetime handlers, $L$ property-path length, $D$ base-type depth, $R$ registered samplers.

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| Flatten the chain | $O(s)$ | $O(s)$ | `Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs:417` |
| Prepare samplers | $O(\sum_s k_s (L + D))$ | $O(\sum_s k_s)$ | `Src/Core/VeloxDev.Core/TransitionSystem/Sampling/Interpolator.cs:139` |
| Resolve one sampler | $O(1)$ exact, $O(D)$ base walk, $O(R)$ interface fallback | — | `Src/Core/VeloxDev.Core/TransitionSystem/Sampling/Interpolator.cs:51` |
| One sampled frame | $O(k)$ per transition | $O(1)$ | `Src/Core/VeloxDev.Core/TransitionSystem/Runtime/TransitionInterpreter.cs:313` |
| All active transitions, one frame | $O(t k)$ + $O(t)$ dispatches | — | `Src/Core/VeloxDev.Core/TransitionSystem/Runtime/TransitionInterpreter.cs:355` |
| Repeat $n$ times | $n+1$ passes, fresh interpreter per pass | $O(k)$ per pass | `Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs:472` |
| Exit / pause / set rate | $O(r)$ over that target's runs | — | `Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs:30` |

## Startup is linear in the chain

Segments are collected by walking the linked chain, cloning each effect as it goes:

```csharp
currentNode = root;
do {
    segments.Add((currentNode.interpolator, currentNode.delay, currentNode.effect.Clone(), currentNode.state));
    repeats.Add(currentNode.RepeatTime);
    currentNode = currentNode.next;
} while (currentNode is not null);
```

Source: `Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs:417-425`

Preparation then reads each property once through the host and builds a sampler entry. Sampler resolution is a dictionary hit in the common case; a base-class walk adds $O(D)$, and an interface-typed property falls back to scanning the registry, $O(R)$.

## The per-frame loop

Each sampling loop advances on the shared timeline, emits a frame, and waits for the next sample interval:

```csharp
while (true)
{
    if (cts.IsCancellationRequested || Args.Handled) throw new OperationCanceledException();
    if (!timeline.IsAdvancing) { EmitFrame(...); await timeline.WaitWhileStalledAsync(cts.Token); continue; }
    var elapsedTicks = timeline.Ticks - run.PassAnchor;
    if (EmitFrame(...)) return;
    var sampleIntervalMs = 1000.0 / Math.Max(1, effect.FPS);
    await new FrameWait(this, TimeSpan.FromMilliseconds(sampleIntervalMs), cts.Token);
}
```

Source: `Src/Core/VeloxDev.Core/TransitionSystem/Runtime/TransitionInterpreter.cs:313-341`

`EmitFrame` evaluates the easing once and applies the sampler set on the host thread:

```csharp
foreach (var entry in _entries)
{
    if (!CanSetValue()) return;
    try { entry.Sampler.InsertFrame(target, entry.Property, ref entry.Working, entry.Start, entry.End, entry.Options, t); }
```

Source: `Src/Core/VeloxDev.Core/TransitionSystem/Sampling/SamplerSet.cs:128-143`

The easing call is $O(1)$; the sampler call is $O(1)$ plus a compiled setter. Nothing here allocates on the steady-state path, because time is passed through an `Interlocked` field and the application closure is cached per target. The aggregate bound is:

$$
T_{\text{frame}}(t,k) = O(t\,k) + O(t)\ \text{host dispatches}
$$

```plot
{
  "title": "Per-frame cost vs active transitions",
  "grid": true,
  "xAxis": { "domain": [0, 20] },
  "yAxis": { "domain": [0, 400] },
  "data": [
    { "fn": "5*x", "color": "#4a9eff", "title": "k = 5 properties" },
    { "fn": "20*x", "color": "#a78bfa", "title": "k = 20 properties" }
  ]
}
```

## Timers scale with transitions, not with properties

There is no central frame wheel. Each sampling loop owns one reusable timer or one host pacer; a paused loop parks on a stall wait and costs no wake-ups. One timer per active transition means $O(t)$ wakes per frame interval, with the interval set by the effect's `FPS` (60 by default). Timer coalescing at the OS level is the reason real CPU cost can be lower than that count suggests — an *inferred* platform effect.

## Easing is a family of constant-time functions

Every easing is a pure function of the normalized time, evaluated once per transition per frame. The family is easiest to compare as curves — In, Out and InOut differ only in where the acceleration is placed:

```plot
{
  "title": "EaseOut family",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [0, 1.2] },
  "data": [
    { "fn": "x", "color": "#888888", "title": "linear" },
    { "fn": "sin(x*PI/2)", "color": "#4a9eff", "title": "easeOutSine" },
    { "fn": "1 - (1-x)^3", "color": "#a78bfa", "title": "easeOutCubic" },
    { "fn": "1 + 2.70158*(x-1)^3 + 1.70158*(x-1)^2", "color": "#e5c07b", "title": "easeOutBack" }
  ]
}
```

## Repeats and memory

`Repeat(n)` runs the enclosed segment range $n+1$ times. The first iteration pays preparation; later iterations replay, skipping the target re-read, but each replay constructs a fresh interpreter and lazily a timer. A chain therefore retains $O(\sum k_s + s)$ live state — effects, state dictionaries, sampler entries — plus $O(1)$ interpreter and timer per currently executing segment.
