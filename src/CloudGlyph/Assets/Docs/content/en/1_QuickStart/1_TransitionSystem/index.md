# TransitionSystem — Quick Start

VeloxDev TransitionSystem is a cross-platform property animation engine. It provides interpolators, easing functions, state snapshots, and schedulers for creating smooth animated transitions between property values.

## Installation

The TransitionSystem is part of `VeloxDev.Core`:

```xml
<PackageReference Include="VeloxDev.Core" Version="6.0.82" />
```

## Basic Usage

### 1. Create a State Snapshot

A state snapshot captures the current values of one or more properties and defines their target values for animation.

```csharp
using VeloxDev.TransitionSystem.Abstractions;

// Create a state snapshot for a specific target type
var state = TransitionCore<MyControl, StateSnapshotCore<MyControl>>.Create();

// Configure property transitions
state.Property<double>(ctrl => ctrl.Opacity)
	.To(0.5)              // Target value
	.Duration(300)         // Duration in milliseconds
	.Ease(Eases.Sine.Out); // Easing function
```

### 2. Execute a Transition

```csharp
// Apply the transition to a target object
TransitionCore<MyControl, StateSnapshotCore<MyControl>>
	.Execute(myControl, state);

// Or use the extension method
state.Execute(myControl);
```

### 3. Platform Setup (Avalonia Example)

Each platform adapter provides a platform-specific interpolator. Register it once at startup:

```csharp
// In App.axaml.cs or Program.cs
using VeloxDev.DynamicTheme;

// Register the Avalonia interpolator
ThemeManager.SetPlatformInterpolator(new VeloxDev.Avalonia.Interpolator());
```

### 4. Multiple Property Animation

```csharp
var snapshot = TransitionCore<MyControl, StateSnapshotCore<MyControl>>.Create();

// Animate multiple properties simultaneously
snapshot.Property<double>(ctrl => ctrl.Opacity)
	.To(0.0)
	.Duration(500)
	.Ease(Eases.Quad.In);

snapshot.Property<double>(ctrl => ctrl.Width)
	.To(300)
	.Duration(1000)
	.Ease(Eases.Elastic.Out);

snapshot.Property<Brush>(ctrl => ctrl.Background)
	.To(new SolidColorBrush(Colors.Red))
	.Duration(300);

// Execute all at once
snapshot.Execute(myControl);
```

### 5. Using the Scheduler

For more control over timing and lifecycle, use `TransitionScheduler`:

```csharp
using VeloxDev.TransitionSystem.Abstractions;

var scheduler = new TransitionSchedulerCore();

// Schedule a transition
scheduler.Add(snapshot, myControl);
scheduler.Start();

// Later...
scheduler.Pause();
scheduler.Resume();
scheduler.Exit();  // Stop all transitions
```

## Easing Functions

VeloxDev provides a comprehensive set of easing functions via the `Eases` static class:

| Category | Functions |
|---|---|
| Sine | `Eases.Sine.In`, `.Out`, `.InOut` |
| Quad | `Eases.Quad.In`, `.Out`, `.InOut` |
| Cubic | `Eases.Cubic.In`, `.Out`, `.InOut` |
| Quart | `Eases.Quart.In`, `.Out`, `.InOut` |
| Quint | `Eases.Quint.In`, `.Out`, `.InOut` |
| Expo | `Eases.Expo.In`, `.Out`, `.InOut` |
| Circ | `Eases.Circ.In`, `.Out`, `.InOut` |
| Back | `Eases.Back.In`, `.Out`, `.InOut` |
| Elastic | `Eases.Elastic.In`, `.Out`, `.InOut` |
| Bounce | `Eases.Bounce.In`, `.Out`, `.InOut` |

## Native Interpolators

Built-in interpolators in `VeloxDev.TransitionSystem.NativeInterpolators`:

| Type | Interpolator |
|---|---|
| `double` | `DoubleInterpolator` |
| `float` | `FloatInterpolator` |
| `int` | `IntInterpolator` |
| `long` | `LongInterpolator` |
| `System.Drawing.Point` | `PointInterpolator` |
| `System.Drawing.PointF` | `PointFInterpolator` |
| `System.Drawing.Size` | `SizeInterpolator` |
| `System.Drawing.SizeF` | `SizeFInterpolator` |
| `System.Drawing.Rectangle` | `RectangleInterpolator` |
| `System.Drawing.RectangleF` | `RectangleFInterpolator` |
| `System.Numerics.Vector2` | `Vector2Interpolator` |
| `System.Numerics.Vector3` | `Vector3Interpolator` |
| `System.Numerics.Vector4` | `Vector4Interpolator` |
| `System.Numerics.Quaternion` | `QuaternionInterpolator` |
| `System.Drawing.Color` | `ColorInterpolator` |

## Custom Interpolators

Implement `IValueInterpolator` to add support for custom types:

```csharp
public class MyCustomInterpolator : IValueInterpolator
{
	public IList<object?> Interpolate(object? from, object? to, int steps)
	{
		// Generate intermediate values
	}
}

// Register globally
InterpolatorCore.RegisterInterpolator(typeof(MyType), new MyCustomInterpolator());
```

## Next Steps

- See the [API Reference](../../2_API/1_TransitionSystem/index.md) for detailed interface documentation
- See the [DynamicTheme](../2_DynamicTheme/index.md) Quick Start for theme animation integration
