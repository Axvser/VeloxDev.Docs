# Timing — Contracts

Namespace `VeloxDev.Timing` (`Src/Core/VeloxDev.Core/Interfaces/Timing/*.cs`). The source a consumer reads, the control face that steers it, and the two sampling modes built on top. The implementations are on [implementation](../01_implementation/index.md).

### Struct: `TimeSample`

```csharp
public readonly struct TimeSample
{
    public TimeSample(TimeSpan delta, TimeSpan total, long step, long epoch);

    public TimeSpan Delta { get; }
    public TimeSpan Total { get; }
    public long Step { get; }
    public long Epoch { get; }
}
```

| Member | Description |
|---|---|
| `Delta` | The time this sample covers. For an uncompensated sampler it is the measured interval since the previous sample; for a compensating one it is the fixed `Step`, because a fixed step is what the consumer must integrate with. `TimeSpan.Zero` means nothing advanced and the caller should not push a frame. |
| `Total` | Time accounted for since the last `ITimeSampler.Reset`. For a compensating sampler it is derived from the delivered step count, so it is exact and never absorbs a sub-step remainder. |
| `Step` | The number of steps delivered so far; zero for an uncompensated sampler. |
| `Epoch` | The source's `ITimeSource.Epoch` at the moment of sampling. A change means the source was rebased (paused, resumed, reseeked or re-rated) and any accumulated state is no longer comparable. |

**Notes:** `default(TimeSample)` is the "nothing to push" value — an all-zero sample. It deliberately carries **no absolute position**: a sampler's caller already holds the source and can read `ITimeSource.Ticks` when it needs the absolute value, and putting both an absolute and a relative quantity in one value invites reading the wrong one — for the compensating sampler the two are meant to disagree (the remainder under one step is excluded from `Total` by design).

### Interface: `ITimeSource`

```csharp
public interface ITimeSource
{
    long TicksPerSecond { get; }
    long Ticks { get; }
    TimeSpan Position { get; }
    double Rate { get; }
    bool IsPaused { get; }
    bool IsAdvancing { get; }
    long Epoch { get; }

    Task WaitWhileStalledAsync(CancellationToken cancellationToken = default);
}
```

| Member | Description |
|---|---|
| `TicksPerSecond` | The tick unit of `Ticks`. A consumer converts with this and **never** reads a framework clock's frequency directly: an injected source may not be `Stopwatch`-based (a browser's `Performance.now()`, a host's composition clock), and the conversion would then be silently wrong. |
| `Ticks` | The absolute position, in `TicksPerSecond` units. Differences between two readings are meaningful; the magnitude itself is not. |
| `Position` | The position relative to the source's origin, as a convenience view of `Ticks`. |
| `Rate` | How fast the source runs. Never negative; zero means it is not advancing. |
| `IsPaused` | True while the source has been paused with `ITimeSourceControl.Pause`. |
| `IsAdvancing` | True while the position is moving. This — and **not** `IsPaused` — is the predicate a consumer parks on. |
| `Epoch` | Increases by one every time the source is rebased — paused, resumed, reseeked or re-rated. A consumer holding accumulated state compares it to detect that its basis is no longer valid. |
| `WaitWhileStalledAsync(token)` | Completes when the source stops being stalled, or immediately when it is already advancing. The awaitable form of `IsAdvancing` — "stalled" means exactly `!IsAdvancing`. |

**Notes on `IsAdvancing` vs `IsPaused`:** the two differ because a rate of zero freezes the source without pausing it. A loop that checked only `IsPaused` would keep running with a frozen clock, and a loop that checked `IsAdvancing` but parked on the wrong signal would spin. `IsAdvancing` is stated as an **invariant, not a formula**: *true implies the position is moving*, whatever the reason it might not be — a source whose position is advanced by a host rather than computed from a clock at read time must report `false` whenever that host has stopped feeding it (a player loop suspended, a decoder buffer empty, a tab in the background), even though nobody called `Pause`. Getting it wrong is silent: a source that reports `true` while frozen never lets its consumers park, so every loop anchored to it goes on writing properties at its sampling rate for a frame that is not changing — no exception, no log, no frame, just work that never stops.

**Notes on `WaitWhileStalledAsync`:** it pairs exactly with `IsAdvancing` so that `while (!IsAdvancing) await WaitWhileStalledAsync()` cannot return while the predicate is still false (which would spin a core hot), and so a stalled consumer costs no wake-ups rather than polling. It also returns on a **nudge** — a seek applied while stalled — so the new position can be drawn; callers re-read the state after every wake instead of treating completion as "resumed". Implementations must not take a write gate here, must complete continuations asynchronously rather than inline from the control call, must return an already-completed task when advancing, and must observe the `cancellationToken` (a consumer's stop has to reach it even though nothing is going to resume the source on its behalf).

### Interface: `ITimeSourceControl : ITimeSource`

```csharp
public interface ITimeSourceControl : ITimeSource
{
    void Pause();
    void Resume();
    void SetRate(double rate);
    void Seek(TimeSpan position);
    void Wake();
}
```

| Member | Description |
|---|---|
| `Pause()` | Freezes the source. Time spent paused is excluded **by construction** — nothing accrues. Idempotent. |
| `Resume()` | Lets the source run again, at the rate it was last set to. |
| `SetRate(rate)` | Changes how fast the source runs, without moving its position. Zero freezes it without pausing it; a resume then does nothing, and only a non-zero rate starts it again. **Throws `ArgumentOutOfRangeException`** when `rate` is negative — time only ever moves forwards, and a negative rate is a caller mistake rather than something to clamp (clamping to a pause would leave an animation silently not running; clamping forward would ignore what was asked for). |
| `Seek(position)` | Moves the source to `position`, keeping the rate. A consumer holding an accumulator must treat this as a discontinuity. While paused there is no frame left to pick the new position up, so this also nudges parked consumers to redraw. |
| `Wake()` | Wakes a parked consumer **once** without resuming. A no-op when the source is running. Needed for two things that are not a resume: redrawing a position changed while paused, and letting a cancellation reach a consumer whose parked wait knows nothing about its token. An implementation must **replace** the parked signal rather than complete it in place — completing it and leaving it installed would let the next wait return immediately, spinning out frames. |

**Notes:** separate from `ITimeSource` so that the read-only face is what a sampler and a passive consumer receive — an `ITimeSampler` takes the read-only contract and *cannot pause the world*. Control calls are safe from any thread and are serialised internally.

### Interface: `ITimeSampler`

```csharp
public interface ITimeSampler
{
    void Reset();
}
```

**Notes:** the shared state contract of the two sampling modes; not used directly — pick `IUncompensatedTimeSampler` or `ICompensatingTimeSampler`. A sampler holds **per-consumer state** and has exactly **one logical owner** — one loop, one sampler. It takes no lock: the state is a few integers touched once per frame, and a lock there would cost more than the arithmetic it guards. An implementation must not be shared between threads, and `Reset` is not an exception. `Reset` re-anchors to the source's present and clears every accumulated quantity, so the next sample behaves like the first one after construction; it is called when a loop (re)starts, never while its sampling call is in flight, and it does not touch the source.

### Interface: `IUncompensatedTimeSampler : ITimeSampler`

```csharp
public interface IUncompensatedTimeSampler : ITimeSampler
{
    TimeSample Sample();
}
```

**Notes:** best-effort sampling — how much time has passed since the previous sample, with no guarantee about how many samples should have happened. **Late is merely late.** The right mode whenever the consumer positions itself against the source rather than accumulating: an animation reads the absolute position and is correct whatever the sampling cadence. Nothing is carried between calls, so a missed sample loses nothing. `Sample()` returns a sample whose `Delta` is `TimeSpan.Zero` when the source has not advanced since the last call, which is the caller's signal not to push a frame.

### Interface: `ICompensatingTimeSampler : ITimeSampler`

```csharp
public interface ICompensatingTimeSampler : ITimeSampler
{
    TimeSpan Step { get; set; }
    int MaxStepsPerCall { get; set; }
    int MaxPendingSteps { get; set; }
    long PendingSteps { get; }
    long DroppedSteps { get; }
    TimeSpan TimeToNextStep { get; }
    int Advance(out TimeSample sample);
}
```

| Member | Description |
|---|---|
| `Step` | The fixed interval each step covers. Also what `TimeSample.Delta` reports, because a fixed step is what the consumer integrates with — the measured interval is deliberately not exposed. **Throws `ArgumentOutOfRangeException`** when zero or negative. |
| `MaxStepsPerCall` | The most steps a single `Advance` may deliver. The excess stays **owed**, so this bounds the catch-up burst without affecting the total. Throws when less than one. |
| `MaxPendingSteps` | How many steps may be owed at once before the debt is forgiven. Reaching it means the consumer cannot keep up with the source's rate at all, so repaying in full would leave it permanently behind; the excess is dropped and added to `DroppedSteps`. Throws when less than one. |
| `PendingSteps` | Steps owed but not yet delivered. Reading it after an `Advance` is the only way to tell a cap truncation (non-zero) from the consumer simply having reached the source's present (zero). |
| `DroppedSteps` | Steps forgiven by `MaxPendingSteps`. Non-zero means the delivered step count and the source's elapsed time have diverged, by exactly this many steps. |
| `TimeToNextStep` | How long until the next step is owed — `TimeSpan.Zero` while steps already are. What a loop waits out between pushes: sleeping exactly to the boundary is the point, since the alternative is waking on a fraction of the step and re-asking, which is both late and a wake-up per poll. |
| `Advance(out sample)` | Reports how many steps the caller should push now — at most `MaxStepsPerCall`, zero when less than one step is owed. The caller pushes that many times, each with the same fixed `Delta`. |

**Notes:** fixed-step sampling that **repays what it owes**: over any interval the number of steps delivered equals `floor(elapsed / Step)`, with no drift and no step silently lost. For consumers whose step count must be exact — physics, fixed-rate integration. It differs from the uncompensated mode in what it does with the two leftovers: a sub-step remainder is carried to the next call, never rounded away, and whole steps that `MaxStepsPerCall` would not let through this call stay owed rather than being discarded, so the count still comes out right and only the burst is spread. The one bound is `MaxPendingSteps`: without it the contract is unsatisfiable, because a machine suspended for hours owes millions of steps and repaying them at a capped rate takes hours, during which the consumer is further behind than if the debt had been forgiven. A **rebase** of the source (an `Epoch` change) discards the debt instead of repaying it: a backward seek must never produce negative pushes, and a forward one must not inject a burst that never happened.
