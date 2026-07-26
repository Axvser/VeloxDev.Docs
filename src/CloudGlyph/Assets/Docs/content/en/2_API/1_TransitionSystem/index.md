# TransitionSystem — API Reference

## Namespace: `VeloxDev.TransitionSystem`

### Core Abstractions (`VeloxDev.TransitionSystem.Abstractions`)

#### `TransitionCore<TTarget, TStateSnapshotCore>`
Base class for type-safe transition operations.

| Method | Description |
|---|---|
| `Create()` | Creates a new state snapshot for the target type |
| `Execute(TTarget, StateSnapshotCore)` | Executes a state snapshot on a target |
| `Execute(StateSnapshotCore)` | Executes a state snapshot (target was already set) |
| `Execute(TTarget, IEnumerable<StateSnapshotCore>)` | Executes multiple snapshots on a target |
| `Exit(TTarget)` | Exits all active transitions on a target |

#### `TransitionCore`
Non-generic base providing static `Exit()` for lifecycle management.

#### `StateSnapshotCore<TTarget>`
Captures and applies property value changes on a target object.

| Method | Description |
|---|---|
| `Property<T>(Expression<Func<TTarget, T>>)` | Select a property to animate, returns a property builder |
| `AsRoot()` | Marks this snapshot as a root (standalone execution) |
| `CoreExecute(TTarget, bool)` | Executes the snapshot on the target |

#### `TransitionProperty`
Represents a chain of property accessors for deep property navigation.

| Property | Type | Description |
|---|---|---|
| `Path` | `string` | Dot-separated property path (e.g. "Background.Color") |
| `PropertyType` | `Type` | Type of the leaf property |
| `CanRead` | `bool` | Whether all segments support reading |
| `CanWrite` | `bool` | Whether the leaf property supports writing |

| Method | Description |
|---|---|
| `GetValue(object)` | Reads the current value through the property chain |
| `SetValue(object, object?)` | Writes a value through the property chain |

#### `TransitionSchedulerCore`
Manages the timing and lifecycle of multiple transitions.

| Method | Description |
|---|---|
| `Add(StateSnapshotCore, object)` | Schedules a snapshot for execution |
| `Remove(StateSnapshotCore)` | Removes a pending snapshot |
| `Start()` | Starts (or resumes) processing |
| `Pause()` | Pauses all active transitions |
| `Exit()` | Stops and cleans up all transitions |

### Enums

| Enum | Values |
|---|---|
| `RotationDirection` | `Shortest`, `Longest`, `CW`, `CCW` |
| `State` | Transition state flags |

### Interfaces (`VeloxDev.TransitionSystem`)

| Interface | Purpose |
|---|---|
| `IEaseCalculator` | Defines an easing curve (`Ease(double t) → double`) |
| `IValueInterpolator` | Generates intermediate values between start and end |
| `ITransitionScheduler` | Scheduler lifecycle contract |
| `ITransitionProperty` | Property access abstraction |
| `ITransitionInterpreter` | Interprets transition configurations |
| `ITransitionEffect` | Visual transition effect |
| `IFrameInterpolator` | Frame-level interpolation |
| `IFrameSequence` | Sequence of interpolation frames |
| `IFrameState` | State at a specific frame |
| `IInterpolable` | Makes a type interpolable |
| `IUIThreadInspector` | UI thread awareness |

### Eases Factory (`VeloxDev.TransitionSystem.Eases`)

| Category | In | Out | InOut |
|---|---|---|---|
| `Sine` | `Eases.Sine.In` | `.Out` | `.InOut` |
| `Quad` | `Eases.Quad.In` | `.Out` | `.InOut` |
| `Cubic` | `Eases.Cubic.In` | `.Out` | `.InOut` |
| `Quart` | `Eases.Quart.In` | `.Out` | `.InOut` |
| `Quint` | `Eases.Quint.In` | `.Out` | `.InOut` |
| `Expo` | `Eases.Expo.In` | `.Out` | `.InOut` |
| `Circ` | `Eases.Circ.In` | `.Out` | `.InOut` |
| `Back` | `Eases.Back.In` | `.Out` | `.InOut` |
| `Elastic` | `Eases.Elastic.In` | `.Out` | `.InOut` |
| `Bounce` | `Eases.Bounce.In` | `.Out` | `.InOut` |

### Interpolator Registry (`InterpolatorCore`)

| Method | Description |
|---|---|
| `RegisterInterpolator(Type, IValueInterpolator)` | Registers an interpolator for a type |
| `TryGetInterpolator(Type, out IValueInterpolator?)` | Retrieves a registered interpolator |
| `UnregisterInterpolator(Type, out IValueInterpolator?)` | Removes a registration |
| `NativeInterpolators` | Dictionary of built-in interpolators |

### TransitionEffect (`TransitionEffect`, `TransitionEx`)

Provides higher-level transition orchestration:

| Method | Description |
|---|---|
| `TransitionEffect.Create<T>()` | Creates a transition effect |
| `TransitionEx.Animate<T>(T target, Action<T> to, ...)` | Fluent animation API |
