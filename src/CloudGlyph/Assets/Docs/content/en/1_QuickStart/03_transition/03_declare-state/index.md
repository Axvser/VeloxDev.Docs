# Transition — Declare State Explicitly

> This page replaces the former "Define a Snapshot" topic. Capturing an object's current state is no longer part of the API: the engine has no snapshot/capture step, so an animation is now a **state declared explicitly, path by path**.

## 1. The declaration model

`Transition<T>` (`T` is the target's type) is three things at once: the static entry point (`Create`), the fluent builder (`Property`, `Effect`) and the executor (`Execute`). One instance describes one **animation segment** — a set of explicitly declared property paths, each with the value it should reach, plus one effect (duration / easing / FPS / loop).

Nothing is discovered or recorded from the target. `Property(lambda, value)` stores the *target* value; the engine reads the property's **current** value when the run starts (`InterpolatorCore.Prepare`), which is what makes one builder safe to store in a static field and reuse on any number of targets. Because a builder is just data, it can be built once and executed many times (see [Execute & Control](../05_execute-and-control/index.md)).

## 2. Build one segment

Create the segment with `Transition<T>.Create()`, declare targets with `.Property(...)` and timing with `.Effect(...)`. Property lambdas may be **nested paths** — the demo animates `((TranslateTransform)r.RenderTransform).X` directly:

```csharp
using System;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

public static class QuickStart
{
    public static readonly Transition<Rectangle> Animation0 =
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

This is the exact shape of `Animation0` in `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` (there it is a `static readonly` member of the window's partial class). The generic `Property<TValue>` overload accepts any value type; each adapter adds typed overloads for the platform's value types (`Brush`, `Transform` collections, `Color`, `Point`, `CornerRadius`, `Thickness`, `Size`, ... and the numerics `int` / `double` / `float` / `decimal`), so the target value is stored already typed.

**Expected result:** the fluent chain returns the same `Transition<Rectangle>` with three declared properties (`Opacity`, `RenderTransform.X`, `Fill`) and one 2-second auto-reverse effect. Nothing animates yet.

## 3. Read the declared state back

The declared values live in the state dictionary, keyed by `ITransitionProperty` (its `Path` is the dotted property path):

```csharp
foreach (var kvp in QuickStart.Animation0.GetState().Values)
    Console.WriteLine($"{kvp.Key.Path} = {kvp.Value}");
```

**Expected result:** the loop prints `Opacity = 0`, `RenderTransform.X = 800` and `Fill = <brush>`. `GetState()` also exposes the `Interpolators` and `Options` dictionaries for the per-property samplers/options you attached.

## 4. Express a reset

A reset is not captured — it is **declared**, exactly like any other animation: list the initial values path by path and play them with a zero-duration effect (`TransitionEffects.Empty`), which jumps straight to the end of the pass:

```csharp
// The box's defaults, expressed as explicit paths.
private static Transition<BoxModel> CreateReset(string color)
{
    return Transition<BoxModel>.Create()
        .Property(b => b.X, 0)
        .Property(b => b.Y, 0)
        .Property(b => b.Width, 120)
        .Property(b => b.Height, 80)
        .Property(b => b.Opacity, 1)
        .Property(b => b.Rotate, 0)
        .Property(b => b.Scale, 1)
        .Property(b => b.Color, color);
}

// ... later, restore those values instantly:
CreateReset("#00BFFF").Effect(TransitionEffects.Empty).Execute(Box0);
```

This is `CreateReset` / the reset branch in `Examples/Transition/Blazor/Demo/Demo/Components/Pages/Home.razor.cs`; the WPF demo uses the same `CreateResetRec*` shape (`Examples/Transition/WPF/Demo/MainWindow.xaml.cs`). Every demo's reset path list must be kept in step with the state the animation actually produces — nothing derives it for you.

**Expected result:** the reset run writes each declared value in one pass and completes immediately; the target is back at its declared initial state.

*Note on the WPF demo:* there the reset additionally writes the values straight through (`kvp.Key.SetValue(target, kvp.Value)` over `GetState().Values`) instead of going through `Execute`, because the async pipeline is unreliable for a `RenderTransform` / `Projection` reset on some platforms. That direct write is a demo workaround, not part of the API.

## 5. Path rules

Two path mistakes are rejected rather than silently animating nothing:

- **`TransitionPathConflictException`** (`VeloxDev.TransitionSystem`) — thrown while the transition is being **built**, from `StateCore.SetValue`, when a newly declared path sits above or below one already on the same transition (an object must be expressed by exactly one path). Re-declaring the identical path is a plain overwrite and is allowed. The check covers one transition's value paths only: conflicts **between** two transitions, and paths registered through `SetInterpolator` / `SetOptions`, are not checked.
- **`TransitionPathUnsampleableException`** (`VeloxDev.TransitionSystem`) — thrown **synchronously by `Execute`** when a declared path can never animate: its leaf is a reference type with no registered sampler and no custom interpolator. Value types are exempt (a struct can still be assembled member by member). This is unrelated to `TransitionProperty.UnreadablePath`, where a path is valid but does not match the current target's runtime type — that stays a per-frame skip.

```csharp
// Parent and child paths on one transition -> TransitionPathConflictException
Transition<Rectangle>.Create()
    .Property(r => r.RenderTransform, [new TranslateTransform(200, 0)])
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 800); // throws
```

**Expected result:** the conflict throws where the second `Property` is called; the unsampleable path throws from `Execute`, before any frame is scheduled.

## 6. Rotation options

Angle-like numeric paths can steer rotation direction through `Property`'s optional `interpolationOptions` argument (`RotationDirection`, a `[Flags]` enum in `VeloxDev.TransitionSystem`): `Auto` (shortest path), `ClockWise` / `CounterClockWise` for 2-D, plus `ClockWiseX/Y/Z` / `CounterClockWiseX/Y/Z` for per-axis 3-D. The sampler (`DoubleSampler`) reads the option at frame time.

```csharp
.Property(r => r.RenderTransform, [new RotateTransform(180)], RotationDirection.CounterClockWise)
```

**Expected result:** the transform path rotates through the *counter-clockwise* 180 degrees rather than the arbitrary default wrap-around.

Next: [Sequence & Repeat](../04_sequence-and-repeat/index.md) chains several segments into one timeline.
