# Transition — Define a Snapshot

## 1. The snapshot concept

A `Transition<T>.StateSnapshot` is a **pure descriptor** of one animation segment: a set of recorded *property target values* plus one *effect* (duration / easing / FPS / loop) and, optionally, per-property samplers and options. It does not touch the target until you execute it (see [Execute & Control](../05_execute-and-control/index.md)). Because a snapshot is just data, it can be built once, stored in a static field, and reused on any number of targets.

## 2. Build a one-shot snapshot

Create the root snapshot with `Transition<T>.Create()` (`T` is the target's type), then declare targets with `.Property(...)` and timing with `.Effect(...)`. Property lambdas may be **nested paths** — the demo animates `((TranslateTransform)r.RenderTransform).X` directly:

```csharp
using System;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

public static class QuickStart
{
    public static readonly Transition<Rectangle>.StateSnapshot Animation0 =
        Transition<Rectangle>.Create()
            .Property(r => r.Opacity, 0)                                   // double target
            .Property(r => ((TranslateTransform)r.RenderTransform).X, 800) // nested path
            .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))     // Brush target
            .Effect(new TransitionEffect
            {
                Duration = TimeSpan.FromSeconds(2),
                IsAutoReverse = true,
                LoopTime = 2,
            });
}
```

This is the exact shape of `Animation0` in `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` (there it is a member of the window's partial class). The adapter's `StateSnapshot` exposes typed `Property` overloads for the platform's value types (`Brush`, `Transform` collections, `Color`, `Point`, `CornerRadius`, `Thickness`, `Size`, ... and the numerics `int` / `double` / `float` / `decimal`), so the target value is stored already typed. A generic `Property<TValue>` overload covers anything else.

**Expected result:** the fluent chain returns the same `StateSnapshot` with three recorded properties (`Opacity`, `RenderTransform.X`, `Fill`) and one 2-second auto-reverse effect. Nothing animates yet.

## 3. Read the recorded state back

The recorded values live in the snapshot's state dictionary, keyed by `ITransitionProperty` (its `Path` is the dotted property path):

```csharp
foreach (var kvp in QuickStart.Animation0.GetState().Values)
    Console.WriteLine($"{kvp.Key.Path} = {kvp.Value}");
```

**Expected result:** the loop prints `Opacity = 0`, `RenderTransform.X = 800` and `Fill = <brush>`. `snapshot.GetState()` also exposes `Interpolators` and `Options` dictionaries for the per-property samplers/options you attached.

## 4. Record the object's *current* state

Instead of writing target values by hand, capture the live values of an existing target with the adapter's `TransitionEx` extensions (`using VeloxDev.TransitionSystem`):

```csharp
var explicitSnapshot  = rect.Snapshot(r => r.Opacity, r => r.Fill); // only the listed paths
var allSnapshot       = rect.SnapshotAll();                          // auto-discover animatable props
var withoutWidth      = rect.SnapshotExcept(r => r.Width);           // all animatable except these
```

`SnapshotAll()` and `SnapshotExcept(...)` walk the object graph and record every property whose type has a registered sampler (`Interpolator.TryGetInterpolator(type, out _)`), recursing into composites. The demos take these snapshots **after** the element is loaded and initialized (in `Loaded` / `OnAppearing` / `OnInitialized`), so the captured state is the real initial state, and then restore it later with a zero-duration effect (see [Sequence & Repeat](../04_sequence-and-repeat/index.md)).

**Expected result:** the captured snapshot holds the target's *current* values for the discovered paths — ready to be `Effect`-overridden and executed to reset the object.

## 5. Rotation options

Angle-like numeric paths can steer rotation direction through `Property`'s optional `interpolationOptions` argument (`RotationDirection`, a `[Flags]` enum in `VeloxDev.TransitionSystem`): `Auto` (shortest path), `ClockWise` / `CounterClockWise` for 2-D, plus `ClockWiseX/Y/Z` / `CounterClockWiseX/Y/Z` for per-axis 3-D. The sampler (`DoubleSampler`) reads the option at frame time.

```csharp
.Property(r => r.RenderTransform, [new RotateTransform(180)], RotationDirection.CounterClockWise)
```

**Expected result:** the transform path rotates through the *counter-clockwise* 180 degrees rather than the arbitrary default wrap-around.
