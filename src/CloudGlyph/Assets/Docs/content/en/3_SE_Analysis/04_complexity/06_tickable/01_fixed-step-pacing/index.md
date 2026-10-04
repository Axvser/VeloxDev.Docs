# Fixed-Step Pacing and Compensation

The fixed pump's arithmetic is where the feature's only real algorithmic content sits: a compensating sampler that owes whole steps and repays them, with the total it reports taken from the step ordinal rather than a running sum.

Let $h$ be the step size in milliseconds, $r$ the clock's rate, and $\Delta t$ the wall-clock time between two `Advance` calls.

## The sampler's arithmetic

The virtual time advanced between two wakes is $r \cdot \Delta t$, so the number of whole steps owed is

$$
n = \left\lfloor \frac{r \cdot \Delta t + \varepsilon}{h} \right\rfloor
$$

where $\varepsilon$ carries the fractional remainder banked by the previous call. The sampler keeps that remainder, which is exactly what makes the push count track the virtual clock instead of the wake cadence: the total number of pushes over a wall-clock interval $T$ is

$$
\sum n \approx \left\lfloor \frac{r \cdot T}{h} \right\rfloor
$$

independent of how the interval was chopped into wake-ups. `TickableBusTests.FixedUpdatePushesTrackTheVirtualClockNotTheWakeCadence` asserts this with a 4× rate and a 600 ms window, accepting the measured count within a $\pm 30\% / +20\%$ band around $\frac{r \cdot T}{h} = 150$ — the band exists because a 600 ms window contains a non-integral number of steps and the sampler may hold a partial one.

The old implementation differs precisely here: it pushed **at most one step per wake-up**, so its count was $\min(\lfloor r \cdot \Delta t / h \rfloor, 1)$ per wake and its ceiling was one step per wake regardless of $r$. Measured over a second, the old form gave about $1000/h$ pushes no matter the rate; the new form gives about $r \cdot 1000 / h$.

## Per-step total

Each delivered step gets the total time of its own ordinal:

$$
t_i = \bigl(\text{firstStep} + i\bigr) \cdot h, \qquad i = 0 \ldots n-1, \qquad \text{firstStep} = \text{sample.Step} - n + 1
$$

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 583-599)
var count = _fixedSampler.Advance(out var sample);
if (count > 0)
{
    var stepTicks = _fixedSampler.Step.Ticks;
    var firstStep = sample.Step - count + 1;

    for (var i = 0; i < count; i++)
    {
        var fixedFrameArgs = CreateFrameEventArgs(
            sample.Delta,
            TimeSpan.FromTicks((firstStep + i) * stepTicks));
        ExecuteBehaviorsFixedUpdateSync(fixedFrameArgs, token);

        _frameEventArgsPool.Return(fixedFrameArgs);
    }
}
```

The alternative — reporting the last reading $n$ times — is what the code comment calls out as removed. The cost of the ordinal form is $O(1)$ per step (one multiply), and what it buys is that $t_i$ is exact and monotone even across a batch, which is what lets a consumer reconstruct the integration.

## The two bounds: burst and debt

The sampler keeps three integer quantities apart — `_acc` (sub-step remainder), `_earned` (steps time has paid for) and `_delivered` (steps handed out) — so that `PendingSteps = _earned - _delivered` is the debt at any instant (`CompensatingTimeSampler.cs` lines 32-44, 104). Two independent caps act on it:

| Cap | Constant | Default | What it bounds |
|---|---|---|---|
| `MaxStepsPerCall` | `DefaultMaxStepsPerCall` | 8 | How many steps one `Advance` may hand over. Bounds the catch-up burst. |
| `MaxPendingSteps` | `DefaultMaxPendingSteps` | 64 | How much debt may accumulate at all. About a second at a 16 ms step. |

The per-call cap bounds the work and leaves the rest **owed**; the pending cap bounds the debt and **forgives** the excess. In order:

$$
\text{pending} \to \min\left(\text{pending},\ P_{\max}\right) \quad\text{(excess forgiven, counted in } \texttt{DroppedSteps}\text{)}
$$

$$
n = \min\left(\text{pending},\ M_{\text{call}}\right)
$$

with $P_{\max} = 64$ and $M_{\text{call}} = 8$. A stall of $S$ ms at rate $r$ owes $\left\lfloor r \cdot S / h \right\rfloor$ steps; the part above $P_{\max}$ is discarded and never reappears:

$$
\text{steps forgiven} = \max\left(0, \left\lfloor \frac{r \cdot S}{h} \right\rfloor - P_{\max}\right), \qquad \text{steps still owed after the call} = \text{pending} - n
$$

The forgiveness is deliberate and the source says why: *"不宽恕的话，被挂起过的机器会欠下几百万步，而按 MaxStepsPerCall 限速偿还期间消费者要比直接宽恕落后得更久"* — a suspended machine would owe millions of steps, and repaying those at 8 per call leaves the consumer further behind than forgiving outright. `DroppedSteps` is a public counter precisely so the loss is observable rather than silent.

This is what the WPF demo's third stall button is for. Its label states the arithmetic directly: a 1500 ms stall at a 16 ms step owes about 94 steps, which exceeds the 64-step debt cap, so the excess is forgiven and permanently lost (`MainWindow.xaml`, lines 63-64). The same run on the 200 ms button owes about 12 — inside both caps, so nothing is dropped and the catch-up is simply a batch.

Two costs follow:

$$
T_{\text{catch-up}} = O(M_{\text{call}} \cdot N), \qquad T_{\text{steady}} = O(1) \text{ per step amortised}
$$

Bounded work per wake-up, at the price of a bounded amount of simulation time that may be discarded.

## Epoch: the third way debt disappears

There is one more path, and it is the one that makes a paused channel cost exactly nothing:

```csharp
// Src/Core/VeloxDev.Core/Timing/CompensatingTimeSampler.cs (lines 133-141)
if (epoch != _epoch)
{
    _epoch = epoch;
    _lastTicks = now;
    _acc = 0;
    _earned = _delivered;
    sample = default;
    return 0;
}
```

The bus bumps its `Epoch` on every rebase — pause, resume, rate change, seek. A sampler that sees a new epoch drops the debt by construction rather than repaying it, so **a pause owes zero steps, provably, with no special case for pausing**. That is the same mechanism that keeps a rate change from settling the accumulator against the old step, and it is why the WPF demo's "unspent time" readout is expected to fall back to zero after a rate or step change rather than climbing back.

The cost of the check is one `long` comparison per `Advance` — $O(1)$.

## Why the wait is chunked

Sleeping on the thread path is never a single `Thread.Sleep` of the whole interval:

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 862-870)
private static void Sleep(TimeSpan duration, CancellationToken token)
{
    var chunk = TimeSpan.FromMilliseconds(MAX_SLEEP_CHUNK_MS);
    for (var remaining = duration; remaining > TimeSpan.Zero; remaining -= chunk)
    {
        if (token.IsCancellationRequested) return;
        Thread.Sleep(remaining < chunk ? remaining : chunk);
    }
}
```

The number of `Thread.Sleep` calls for a wait of $w$ ms is $\lceil w / 50 \rceil$, so the stop latency is bounded by $50$ ms:

$$
\text{stop latency} \le \min(w, 50\ \text{ms})
$$

At the lowest permitted target FPS ($1$), a frame budget is $1000$ ms; without chunking a stop would wait out the whole second. The chunks cost at most $50$-ms-quantised scheduling overhead per frame, which the sampler absorbs because the fixed pump is compensated and the update pump's `DeltaTime` is measured rather than assumed.

## Pacing the update pump

The update pump is paced against the **wall clock**, not the virtual one:

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 836-847)
private void FrameRateControlSync(long frameStartTime, CancellationToken token)
{
    // 目标帧率约束的是采样节奏，不是虚拟时钟，所以这里量的是墙钟——rate 减半不应该让帧率也减半。
    var elapsed = GetTimestamp() - frameStartTime;
    var target = _cachedTargetFrameDurationTicks;
    if (elapsed < target)
    {
        var sleepTime = (long)(target - elapsed);
        if (sleepTime > 0)
            Sleep(TimeConversion.TicksToTimeSpan(sleepTime, TimeConversion.DefaultTicksPerSecond), token);
    }
}
```

So the frame interval in wall-clock terms is

$$
\max\left(\frac{1}{F},\ \text{time spent in the sweep}\right)
$$

and the achievable frame rate is capped by the sweep cost:

$$
F_{\text{achieved}} \le \frac{1}{T_{\text{sweep}}}
$$

which is the practical reason the dispatch constant matters. If one behaviour takes 30 ms, no target above ~33 fps is reachable, and `CurrentFPS` — measured from the wall clock — is the number that reports it. `TargetFPS` will keep claiming 60.

> Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 446-507, 557-620, 836-870; `Examples/Tickable/WPF/Demo/MainWindow.xaml` lines 63-64; `Src/Core/VeloxDev.Core.Test/TimeLine/TickableBusTests.cs` lines 255-319.
