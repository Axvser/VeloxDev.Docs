# Transition — Event Arguments & Diagnostic Stages

Namespace `VeloxDev.TransitionSystem`. `TransitionEventArgs` is the payload of the seven lifecycle events an effect raises; `TransitionEventArgs<TStage, TValue>` adds a typed stage and value for the two **diagnostic** events, and `WarnStage` / `ErrorStage` name the step that reported them. All of them derive from `VeloxDev.TimeLine.TimeLineEventArgs`, which carries the shared `Handled` / `DeltaTime` / `TotalTime` trio (documented with the tickable feature's [TimeLineEventArgs](../../../06_tickable/02_TimeLineEventArgs/index.md) and re-summarized on the [timeline](../../04_timeline/index.md) page).

Sources: `Src/Core/VeloxDev.Core/TransitionSystem/Events/TransitionEventArgs.cs`, `TransitionEventArgs{TStage,TValue}.cs`, `Enums/WarnStage.cs`, `Enums/ErrorStage.cs`, `TransitionDiagnostics.cs`; base `Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`.

### Class: `TransitionEventArgs : TimeLineEventArgs`

```csharp
namespace VeloxDev.TransitionSystem;

public class TransitionEventArgs : TimeLineEventArgs
{
    public int Loop { get; internal set; }
    public long Cycle { get; internal set; }
}
```

| Member | Description |
|---|---|
| `Loop` | `int` — which pass of the **running segment** this is, `0` on its first pass. Compare it against `ITransitionEffectCore.LoopTime` to tell "which repeat" apart. |
| `Cycle` | `long` — how many segments this target has played in total, across every chain it has run; it advances once per pass. |
| `Handled`, `DeltaTime`, `TotalTime` | inherited unchanged from `TimeLineEventArgs`. |

**Notes:**
- Not `sealed` — the generic payload below subclasses it. The base itself is what the seven payload-free lifecycle events (`Awaked`, `Start`, `Update`, `LateUpdate`, `Canceled`, `Completed`, `Finally`) carry, and always **one shared instance per run**: the interpreter stamps `Loop` / `Cycle` / `DeltaTime` / `TotalTime` onto it before every callback, so a handler must not hold on to the reference.
- `Loop` counts passes of the current segment; a chain's earlier segments are not charged to it. `Cycle` is the run-wide counter. A `Seek` may move the run's counter, so treat `Cycle` as "position in the run", not a private tick.
- For a transition, `DeltaTime` is the frame's advance and `TotalTime` is the time accumulated **since the current segment began**; neither resets on a pass boundary — the pass is what `Loop` reports (`TransitionDiagnosticsTests.TotalTimeAccumulatesAcrossPassesWhileLoopCountsThem`).
- *Verified by:* `TimeLineEventArgsTests` (`TransitionEventArgs_Handled_DefaultFalse`, `TransitionEventArgs_Handled_SetTrue`), `TransitionDiagnosticsTests` (`EachPassIsNumberedInLoopAndCountedInCycle`, `TotalTimeAccumulatesAcrossPassesWhileLoopCountsThem`).

### Class: `TransitionEventArgs<TStage, TValue> : TransitionEventArgs`

```csharp
namespace VeloxDev.TransitionSystem;

public sealed class TransitionEventArgs<TStage, TValue> : TransitionEventArgs
    where TStage : struct, Enum
{
    public TStage Stage { get; init; }
    public TValue? Value { get; init; }
}
```

| Member | Description |
|---|---|
| `Stage` | `TStage` — the enum naming the step that reported this. `init`-only. |
| `Value` | `TValue?` — what that step produced; `null` when the step had nothing to hand over. `init`-only. |

**Notes:**
- `Warn` is an `EventHandler<TransitionEventArgs<WarnStage, string>>` and its `Value` is the human-readable message; `Error` is an `EventHandler<TransitionEventArgs<ErrorStage, Exception>>` and its `Value` is the escaped exception. The old string-triple (`Stage` / `Message` / `Exception`) is gone.
- `TransitionDiagnostics` constructs one per report and copies the run's `Loop` / `Cycle` onto it first, so a diagnostic handler sees the same position a lifecycle handler of that frame sees. Setting `Handled = true` on either diagnostic argument asks for the run to terminate.
- *Verified by:* `TransitionDiagnosticsTests` (`AThrowingUpdateEndsTheRunAndIsReported`, `AThrowingSamplerIsReportedAndStopsTheFrames`, `AnUnreadablePathIsWarnedAndTheRestStillAnimates`).

### Enum: `WarnStage`

Which step degraded **without** failing the run. Each value is reported at most once per stage and instance.

```csharp
public enum WarnStage
{
    Unreadable,   // a bound path could not be read off the target
    Unsampled,    // the value at a bound path has no sampler
    Dropped,      // the host refused a frame or a dispatch; the animation carried on
}
```

### Enum: `ErrorStage`

Which step failed the run. The `Value` of the `Error` argument is the escaped exception. The first five values are the engine's own steps; the last six say that a **subscriber of that event threw**.

```csharp
public enum ErrorStage
{
    Sampling,     // sampling a bound property threw
    Run,          // the segment's own run loop threw
    Marshaling,   // marshaling the eased value onto the target threw
    Awake,        // the scheduler's awake step threw
    Prepare,      // preparing the run threw

    Start,        // a subscriber of Start threw
    Update,       // a subscriber of Update threw
    LateUpdate,   // a subscriber of LateUpdate threw
    Completed,    // a subscriber of Completed threw
    Canceled,     // a subscriber of Canceled threw
    Finally,      // a subscriber of Finally threw
}
```

**Example:**
```csharp
var effect = new TransitionEffect { Duration = TimeSpan.FromSeconds(1) };

effect.Warn += (_, e) => Console.WriteLine($"degraded @{e.Stage}: {e.Value}");
effect.Error += (_, e) => Console.WriteLine($"failed @{e.Stage}: {e.Value}");
```

**Notes:**
- The stage enum is what lets a subscriber tell two failures of the same event apart without parsing a string (the removed `Message` / `Exception` triple).
- Because the enum names the step, a `WarnStage` and an `ErrorStage` are not interchangeable: "dropped" is always a `Warn`, "marshaling" is always an `Error`.
- *Verified by:* `TransitionDiagnosticsTests` (`AThrowingSamplerIsReportedAndStopsTheFrames` — `ErrorStage.Sampling`; `AnUnreadablePathIsWarnedAndTheRestStillAnimates` — `WarnStage.Unreadable`).
