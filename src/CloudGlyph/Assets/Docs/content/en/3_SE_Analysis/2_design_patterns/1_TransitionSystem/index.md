# Design Patterns — TransitionSystem

## 1. Strategy Pattern (Easing Functions)

Each `IEaseCalculator` implementation is a strategy for mapping time `[0, 1]` to value `[0, 1]`. The `Eases` factory statically provides 30 strategies organized by category.

## 2. Registry Pattern (Interpolator Core)

`InterpolatorCore` implements a global type-to-interpolator registry. Types register their interpolators once; the system looks them up dynamically at transition time. This allows third-party types to opt into the animation system without modifying core code.

## 3. Fluent Builder Pattern (State Snapshot Configuration)

`StateSnapshotCore<TTarget>.Property<T>()` returns a builder that chains:
```
.Property<T>(expr).To(value).Duration(ms).Ease(ease).Delay(ms)
```
Each call returns the builder for chaining, then `CoreExecute` consumes the configuration.

## 4. Template Method Pattern (TransitionCore)

`TransitionCore<TTarget, TStateSnapshotCore>` defines the skeleton of transition execution (create → configure → execute → exit). Subclasses (via type parameters) provide the specific state and target types.

## 5. Proxy Pattern (Platform Adapters)

Each platform adapter provides its own `Interpolator`, `Transition`, `State`, `TransitionScheduler`, and `UIThreadInspector` implementations. The core engine interacts through abstractions, with platform-specific behavior injected at startup via `ThemeManager.SetPlatformInterpolator()`.
