# Effects and Easing

An effect carries timing, looping and lifecycle events. An easing curve maps normalized time to progress. Both live in `VeloxDev.TransitionSystem`.

## VeloxDev.TransitionSystem

### Interface: ITransitionEffectCore

**Signature:** `public interface ITransitionEffectCore`

| Member | Type | Default | Description |
|---|---|---|---|
| `FPS` | `int` | `60` | Target frame rate. |
| `Duration` | `TimeSpan` | `TimeSpan.Zero` | Length of one pass. |
| `IsAutoReverse` | `bool` | `false` | Plays the pass back in reverse after reaching the end. |
| `LoopTime` | `int` | `0` | Additional repeats. |
| `Ease` | `IEaseCalculator` | `Eases.Default` | The easing curve. |

**Events:** `Awaked`, `Start`, `Update`, `LateUpdate`, `Canceled`, `Completed`, `Finally` — each `EventHandler<TransitionEventArgs>`; `Warn` — `EventHandler<TransitionEventArgs<WarnStage, string>>`; `Error` — `EventHandler<TransitionEventArgs<ErrorStage, Exception>>`.

**Methods:** `InvokeAwake`, `InvokeStart`, `InvokeUpdate`, `InvokeLateUpdate`, `InvokeCompleted`, `InvokeCancled`, `InvokeFinally`, `InvokeWarn`, `InvokeError` (raise the matching event), and `ITransitionEffectCore Clone()`.

The `Invoke*` names are the interface's own; `InvokeCancled` keeps its historical spelling.

### Interface: ITransitionEffect<TPriorityCore>

**Signature:** `public interface ITransitionEffect<TPriorityCore> : ITransitionEffectCore`

| Member | Type | Description |
|---|---|---|
| `Priority` | `TPriorityCore { get; set; }` | The scheduling priority. |
| `Clone` | `new ITransitionEffect<TPriorityCore> Clone()` | A copy of the effect. |

### Class: TransitionEffectCore

The default effect, carrying a `NonPriority` priority.

**Signature:** `public class TransitionEffectCore : ITransitionEffectCore, ITransitionEffect<NonPriority>`

Public members: `FPS` (60), `Duration` (0), `IsAutoReverse` (`false`), `LoopTime` (0), `Ease` (`Eases.Default`), the ten events, the nine `Invoke*` methods, and `Clone()`. The `Priority` member is explicit and always `default`.

### Class: TransitionEffectCore<TPriorityCore>

The typed base an adapter derives from.

**Signature:** `public class TransitionEffectCore<TPriorityCore> : TransitionEffectCore, ITransitionEffect<TPriorityCore>`

| Member | Signature | Description |
|---|---|---|
| `Priority` | `virtual TPriorityCore Priority { get; set; }` | Platform scheduling priority. |
| `Clone` | `new ITransitionEffect<TPriorityCore> Clone()` | Copies the timing, loops and handlers. |

### Interface: IEaseCalculator

**Signature:** `public interface IEaseCalculator`

| Member | Signature | Description |
|---|---|---|
| `Ease` | `double Ease(double t)` | Maps normalized time `t` in `[0,1]` to progress. May leave `[0,1]` for `Back` and `Elastic`. |

### Class: Eases

The built-in curves. Every property returns a fresh calculator, so a curve can be assigned to multiple effects without sharing state.

**Signature:** `public static class Eases`

| Family | Members |
|---|---|
| `Eases.Default` | identity |
| `Sine` | `In`, `Out`, `InOut` |
| `Quad` | `In`, `Out`, `InOut` |
| `Cubic` | `In`, `Out`, `InOut` |
| `Quart` | `In`, `Out`, `InOut` |
| `Quint` | `In`, `Out`, `InOut` |
| `Expo` | `In`, `Out`, `InOut` |
| `Circ` | `In`, `Out`, `InOut` |
| `Back` | `In`, `Out`, `InOut` |
| `Elastic` | `In`, `Out`, `InOut` |
| `Bounce` | `In`, `Out`, `InOut` |

Each nested family is a `static class` whose `In`, `Out` and `InOut` properties return `IEaseCalculator`.

### Curve classes

Each member of `Eases` constructs one of these public classes. All implement `IEaseCalculator` and expose `double Ease(double t)`.

| Family | Classes |
|---|---|
| Default | `EaseDefault` |
| Sine | `EaseInSine`, `EaseOutSine`, `EaseInOutSine` |
| Quad | `EaseInQuad`, `EaseOutQuad`, `EaseInOutQuad` |
| Cubic | `EaseInCubic`, `EaseOutCubic`, `EaseInOutCubic` |
| Quart | `EaseInQuart`, `EaseOutQuart`, `EaseInOutQuart` |
| Quint | `EaseInQuint`, `EaseOutQuint`, `EaseInOutQuint` |
| Expo | `EaseInExpo`, `EaseOutExpo`, `EaseInOutExpo` |
| Circ | `EaseInCirc`, `EaseOutCirc`, `EaseInOutCirc` |
| Back | `EaseInBack`, `EaseOutBack`, `EaseInOutBack` |
| Elastic | `EaseInElastic`, `EaseOutElastic`, `EaseInOutElastic` |
| Bounce | `EaseInBounce`, `EaseOutBounce`, `EaseInOutBounce` |

The `Back` and `Elastic` curves deliberately overshoot. A sampler must accept progress above 1; a value type that clamps it loses the overshoot.

### Class: TransitionEventArgs

The payload for the events that carry no stage-specific value, extending `TimeLineEventArgs` (`Handled`, `DeltaTime`, `TotalTime`).

**Signature:** `public class TransitionEventArgs : TimeLineEventArgs`

| Member | Type | Description |
|---|---|---|
| `Loop` | `int { get; internal set; }` | Which repeat of the current segment is playing, 0-based. |
| `Cycle` | `long { get; internal set; }` | How many segments this target has played in total. |

### Class: TransitionEventArgs<TStage, TValue>

The payload for `Warn` and `Error`.

**Signature:** `public class TransitionEventArgs<TStage, TValue> : TransitionEventArgs` (namespace `VeloxDev.TransitionSystem`)

| Member | Type | Description |
|---|---|---|
| `Stage` | `TStage` | Which step reported. |
| `Value` | `TValue` | The message for `Warn`, the exception for `Error`. |

### Enums

**`ErrorStage`:** `Sampling`, `Run`, `Marshaling`, `Awake`, `Prepare`, `Start`, `Update`, `LateUpdate`, `Completed`, `Canceled`, `Finally`. The first five are the engine's own steps; the rest mean a subscriber of that event threw.

**`WarnStage`:** `Unreadable`, `Unsampled`, `Dropped`. Each is reported at most once per stage and instance.

## Example

```csharp
using System;
using VeloxDev.TransitionSystem;

var effect = new TransitionEffect
{
    Duration = TimeSpan.FromSeconds(0.46),
    FPS = 60,
    Ease = Eases.Back.Out,
    IsAutoReverse = true,
    LoopTime = 2
};

effect.Warn += (_, e) => Console.WriteLine($"warn {e.Stage}: {e.Value}");
effect.Error += (_, e) => Console.WriteLine($"error {e.Stage}: {e.Value.Value}");
```

`TransitionEffect` is the WPF adapter subclass of `TransitionEffectCore<DispatcherPriority>`; see [Platform adapter types](../04_platform-adapter-types/index.md).
