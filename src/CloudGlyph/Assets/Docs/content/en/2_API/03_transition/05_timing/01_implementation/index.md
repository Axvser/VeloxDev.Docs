# Timing — Implementation

Namespace `VeloxDev.Timing` (`Src/Core/VeloxDev.Core/Timing/*.cs`). The default source, the two default samplers, the tick arithmetic they share, and the registry a platform substitutes through. The contracts they implement are on [contracts](../00_contracts/index.md).

### Static Class: `TimeConversion`

Tick arithmetic in the unit a source publishes, so nothing outside a source reads a framework clock's frequency.

```csharp
public static class TimeConversion
{
    public static long DefaultTicksPerSecond { get; }          // Stopwatch.Frequency

    public static TimeSpan TicksToTimeSpan(long ticks, long ticksPerSecond);
    public static long TicksToSpanTicks(long ticks, long ticksPerSecond);
    public static long SpanToTicks(TimeSpan span, long ticksPerSecond);
    public static double TicksToMilliseconds(long ticks, long ticksPerSecond);
    public static double TicksToSeconds(long ticks, long ticksPerSecond);
    public static long MillisecondsToTicks(double milliseconds, long ticksPerSecond);
}
```

**Notes:** every member takes the unit rather than assuming one: an injected source may count in a browser's microseconds or a host's composition ticks, and a conversion that quietly used `Stopwatch.Frequency` would be wrong by orders of magnitude with no symptom. `DefaultTicksPerSecond` is the unit of the default source, and the only place `Stopwatch` is named in this namespace.

### Class: `TimeSourceCore : ITimeSourceControl`

The default time source: an absolute virtual timeline — where it is, how fast it is moving, and the gate that parks its consumers while it is paused. It is also **the base a host that owns time derives from**.

```csharp
public class TimeSourceCore : ITimeSourceControl
{
    public TimeSourceCore();                                       // machine clock
    protected TimeSourceCore(Func<long> nowStamp, long ticksPerSecond);

    public long TicksPerSecond { get; }
    public long Ticks { get; }
    public TimeSpan Position { get; }
    public bool IsPaused { get; }
    public bool IsAdvancing { get; }
    public long Epoch { get; }
    public double Rate { get; set; }                               // set → SetRate

    public void Pause();
    public void Resume();
    public void SetRate(double rate);
    public void Seek(TimeSpan position);
    public void Wake();
    public Task WaitWhileStalledAsync(CancellationToken cancellationToken = default);

    protected void SetHostFeeding(bool feeding);
}
```

**Notes:**
- Two seams, one per shape of host: a **pull** host answers "what time is it now" and supplies the stamp through the protected constructor, while a **push** host whose position arrives in a callback returns the last value it was given and reports its feed through `SetHostFeeding`. Everything either of them would otherwise have to re-derive — the anchor arithmetic, the epoch protocol, the overflow guard, the park signal — stays here. The stamp is a `Func<long>` rather than a virtual method **deliberately**: it is read once from the constructor, and a virtual would run the override before the subclass's own constructor had assigned anything it might read (the classic construction-order trap, here with a clock for a symptom). The protected constructor throws `ArgumentNullException` on a null stamp and `ArgumentOutOfRangeException` when `ticksPerSecond` is not positive.
- `SetHostFeeding(feeding)` reports that whoever feeds this source has stopped or resumed delivering. Its feed falling silent freezes the position without anyone calling `Pause`, and `IsAdvancing` has to say so or every loop anchored here goes on sampling a frame that is not changing. It is a method rather than an `IsAdvancing` a host overrides because the predicate and the park signal must move together, the host cannot see whether they did, and getting it wrong is invisible from the host's side. It is **not** a rebase: the position picks up exactly where it stopped, so an accumulator's basis stays valid and `Epoch` does not move (a host whose own clock keeps running while its feed is silent is describing a jump, and says so with `Seek`). Idempotent, callable from any thread.
- Time is raw integer ticks in the source's own unit — not milliseconds as a `double`. Precision is not the reason (a `double` holds exact integer ticks for decades); the reason is that the whole clock state can then be a set of `long` fields, which are individually atomic on 32-bit as well as 64-bit and cost nothing to swap. Playback rates are held as integers scaled by 10 000 so the clock's state is integral throughout.
- The timeline is **absolute, never restarted** — which is what lets several consumers be anchored to one instance and share a transport. A per-consumer pass is expressed as an *anchor* into this timeline, not by resetting it, so starting a pass on one consumer cannot move any other.
- Reading the position is **lock-free**: the coherent fields are published under a sequence counter, and because the only writers are control calls a reader effectively never retries. Writing takes the write gate, which no reader ever touches. The park signal (`_parkGate`) is non-null exactly while `IsAdvancing` is false — bound to the predicate a consumer parks on rather than to the pause, so the two can never disagree. It is also the wake mechanism; a control call that has to be seen while stalled replaces it and completes the old one, so a parked consumer wakes once per change and re-reads the state instead of polling.
- `internal static long Advance(position, elapsedTicks, speed)` is the position arithmetic, and its ordering is the whole point: the whole part of the elapsed time is taken out **before** anything is multiplied. The obvious `elapsed * speed / Scale` overflows at `long.MaxValue / speed` — about 2.9 years of real time on Windows, but 10.7 *days* on Linux, where a `Stopwatch` tick is a nanosecond. C# arithmetic is unchecked, so the failure is not an exception but a silent wrap to a negative position, which leaves a consumer that was never paused and never seeked jammed for good. (Committed as `f5485adf`; measured at 0.61 ns against 0.23 ns for the unsafe form — 0.38 ns per frame per animation.)
- *Verified by:* `TimeSourceContractTests` (`WaitWhileStalledIsAlreadyCompletedWhenAdvancing`, `WaitWhileStalledParksUntilResume`, `WakeLetsAParkedConsumerRedrawWithoutResuming`, `CancellationEndsAParkedWait`, `AZeroRateIsNotAPauseButIsStillStalled`, `ResumingAfterAZeroRateLiftsThePauseWithoutStartingTheClock`, `PausingAndResumingLeavesTheRemainingDurationUntouched`, `PositionAndTicksUseTheUnitTheSourcePublishes`), `HostTimeSourceTests` (`AStalledHostFreezesTheClockWithoutPausingIt`, `AStalledHostParksItsConsumers`, `FeedingAgainReleasesAParkedConsumer`, `AStallIsNotARebase`).

### Class: `UncompensatedTimeSampler : TimeSamplerCore, IUncompensatedTimeSampler`

```csharp
public sealed class UncompensatedTimeSampler : TimeSamplerCore, IUncompensatedTimeSampler
{
    public UncompensatedTimeSampler(ITimeSource source);
    public void Reset();
    public TimeSample Sample();
}
```

**Notes:** the default `IUncompensatedTimeSampler` — the measured interval since the previous sample, carried over from nothing. The whole state is two integers, and it stays correct because it holds **no accumulator**: a late sample reports a larger interval and a missed one reports a larger one still, but nothing is ever owed. Time spent paused is excluded for free — a paused source does not advance, so the next sample after a resume covers only the frames since the resume rather than the pause. That is why the frame loop's post-resume delta spike does not exist in this design; it was an artefact of measuring against a wall clock while a separate flag said "don't count". A repeated sample within the same tick returns `default` (nothing advanced), the caller's signal to skip the frame. *Verified by:* `UncompensatedTimeSamplerTests` (`TheFirstSamplePushesNothing`, `ReportsTheMeasuredIntervalAndAccumulatesTheTotal`, `NothingIsCarriedBetweenCalls`, `APausedSourceContributesNothing`, `ResumingDoesNotHandOverThePausedInterval`).

### Class: `CompensatingTimeSampler : TimeSamplerCore, ICompensatingTimeSampler`

```csharp
public sealed class CompensatingTimeSampler : TimeSamplerCore, ICompensatingTimeSampler
{
    public const int DefaultMaxStepsPerCall = 8;
    public const int DefaultMaxPendingSteps = 64;

    public CompensatingTimeSampler(ITimeSource source, TimeSpan step);

    public TimeSpan Step { get; set; }
    public int MaxStepsPerCall { get; set; }
    public int MaxPendingSteps { get; set; }
    public long PendingSteps { get; }
    public long DroppedSteps { get; }
    public TimeSpan TimeToNextStep { get; }
    public void Reset();
    public int Advance(out TimeSample sample);
}
```

**Notes:**
- The default `ICompensatingTimeSampler`: a fixed-step accumulator whose delivered step count equals `floor(elapsed / Step)` with no drift. Three quantities, kept apart on purpose, because collapsing any two of them is what makes a fixed-step loop drift: `_acc` (time not yet worth a whole step — carried, never rounded away), `_earned` (steps time has paid for — under a cap this runs ahead of what has been handed out) and `_delivered` (steps actually reported — the virtual clock is this times `Step`, so it stays a function of the integer count and never of a measured interval). All arithmetic is in the source's **integer ticks**: no float, so no accumulation error however long it runs, and the count comparison is exact rather than approximate.
- `DefaultMaxPendingSteps = 64` is about a second at a 16 ms step: a hitch, a slow frame or a briefly stalled thread stays far inside it; reaching it means the consumer cannot keep up at all. Changing `Step` drops the sub-step remainder (measured as a fraction of the old step, it is not a fraction of the new one) while leaving delivered steps untouched, so the count stays continuous. A step that rounds to less than one tick is floored to one tick, for a source whose unit is coarser than `TimeSpan`'s 100 ns.
- *Verified by:* `CompensatingTimeSamplerTests` (`DoesNotPushUntilAStepIsOwed`, `CarriesTheSubStepRemainderAcrossCalls`, `TheDeliveredCountEqualsFloorOfElapsedOverStep`, `TheCapDefersTheBurstInsteadOfDiscardingIt`, `PendingStepsTellATruncationFromBeingCaughtUp`, `PastThePendingBoundTheDebtIsForgivenAndCounted`, `ARebaseDiscardsTheDebtInsteadOfPayingIt`, `PausingDiscardsTheSubStepRemainderRatherThanBankingIt`, `ChangingTheStepDropsTheRemainderMeasuredInTheOldStep`, `ResetRePrimesTheClockAndClearsEveryCounter`, `AStepOfZeroOrLessIsRejected`, `BothCapsMustAllowAtLeastOne`).

### Static Class: `TimerCore`

The registry that hands out time sources and samplers, so a platform can substitute its own and everything else keeps asking for the same contract.

```csharp
public static class TimerCore
{
    public const int DefaultFixedStepMilliseconds = 16;

    public static bool RegisterTimeSource<TContract>(Func<TContract> factory) where TContract : class, ITimeSourceControl;
    public static bool RegisterTimeSampler<TSampler>(Func<ITimeSource, TSampler> factory) where TSampler : class, ITimeSampler;
    public static bool UnregisterTimeSource<TContract>() where TContract : class, ITimeSourceControl;
    public static bool UnregisterTimeSampler<TSampler>() where TSampler : class, ITimeSampler;

    public static TContract CreateTimeSource<TContract>() where TContract : class, ITimeSourceControl;
    public static TSampler CreateTimeSampler<TSampler>(ITimeSource source) where TSampler : class, ITimeSampler;
}
```

| Member | Description |
|---|---|
| `RegisterTimeSource<TContract>(factory)` / `RegisterTimeSampler<TSampler>(factory)` | Installs a factory under the **contract** being replaced — the key is the contract type, not the implementation type. Last-writer-wins and atomic (`AddOrUpdate`), the same rule `InterpolatorCore.RegisterInterpolator` follows. The type argument is the contract: `RegisterTimeSource<ITimeSourceControl>(...)`. Registering under an implementation type would file it where nothing looks. Throws `ArgumentNullException` on a null factory. |
| `UnregisterTimeSource<TContract>()` / `UnregisterTimeSampler<TSampler>()` | Removes a registration, leaving the contract unresolvable again. |
| `CreateTimeSource<TContract>()` | Creates a source for the contract, looked up by **exact** contract with no fallback to a wider or narrower registration. A fallback would have to pick between several assignable keys, and dictionary order is not specified, so the same lookup would return different implementations across runs. **Throws `InvalidOperationException`** when nothing is registered under the contract. |
| `CreateTimeSampler<TSampler>(source)` | Creates a sampler over the source; throws `ArgumentNullException` on a null source and `InvalidOperationException` when the contract is unregistered. |

**Notes:**
- Core installs its defaults in the static constructor, so a lookup always resolves whether or not any platform opted in: `ITimeSourceControl` → `TimeSourceCore`; `IUncompensatedTimeSampler` → `UncompensatedTimeSampler`; `ICompensatingTimeSampler` → `CompensatingTimeSampler` with `Step = 16 ms` (`DefaultFixedStepMilliseconds`).
- **Every lookup builds a new instance**, and a host with one clock keeps that shape: return a fresh wrapper over the one feed per call rather than a shared singleton, so each consumer keeps its own pause and rate. A singleton registered here would make pausing one channel pause every channel — the opposite of what the per-channel sources in `TickManager` (the `tickable` feature) are for. The keys are private and never handed out: a caller replacing the dictionary wholesale would drop the defaults and leave every lookup unresolvable.
- The substitution that exists is for a **host that owns time** — a player loop, a media position, an audio callback — which supplies its clock through `TimeSourceCore`'s protected constructor and reports whether it is still feeding through `SetHostFeeding`, rather than reimplementing the timeline. It is deliberately **not** for a framework's render loop: a clock that only moves on frames makes the frame rate the timing authority, and the sampling path is built on the opposite — the timeline decides how far an animation has gone, and the wake-up is only a reminder. Holding a loop on a UI thread is a real but different problem, solved by `FramePacerCore` in the subsystem that owns the loop.
- *Verified by:* `TimerCoreRegistryTests` (`CoreProvidesADefaultSource`, `CoreProvidesBothDefaultSamplers`, `TheDefaultFixedStepIsTheOneTheRegistryAdvertises`, `EveryLookupHandsBackAFreshInstance`, `ARegistrationUnderAContractIsWhatThatContractResolvesTo`, `RegisteringUnderAnImplementationTypeIsNotWhatAContractLookupFinds`, `AnUnregisteredContractThrows`, `UnregisteringLeavesTheContractUnresolvableAgain`, `ANullFactoryIsRejected`, `ANullSourceIsRejectedByASamplerLookup`).

### Class: `TimeSamplerCore` (abstract support type)

```csharp
public abstract class TimeSamplerCore
{
    protected TimeSamplerCore(ITimeSource source);
    protected ITimeSource Source { get; }
    protected long TicksPerSecond { get; }
    protected TimeSpan ToTimeSpan(long ticks);
    protected long ToTicks(TimeSpan span);
}
```

**Notes:** the read handle and the tick arithmetic the two default samplers share. Throws `ArgumentNullException` on a null source. It deliberately holds **no sampling state and declares no reset**: a base constructor runs before the derived field initializers, so a reset invoked from here would read fields the derived type has not initialised yet. Each sampler primes itself from its own constructor instead.
