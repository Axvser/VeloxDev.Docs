# Feature Map — TransitionSystem

## Responsibility

The TransitionSystem provides a cross-platform property animation engine. It handles value interpolation, easing curves, state snapshots, scheduling, and visual transition effects.

## Feature Breakdown

### 1. Easing Functions (`Eases`, `IEaseCalculator`)
- **Key files**: `TransitionSystem/Eases.cs`, `Interfaces/TransitionSystem/IEaseCalculator.cs`
- **Purpose**: 30 easing functions across 10 categories (Sine, Quad, Cubic, Quart, Quint, Expo, Circ, Back, Elastic, Bounce), each with In/Out/InOut variants. The `Eases` static class provides typed factory access.

### 2. Interpolator System (`InterpolatorCore`, `IValueInterpolator`)
- **Key files**: `TransitionSystem/Interpolator.cs`, `TransitionSystem/InterpolatorOutputCore.cs`
- **Purpose**: Pluggable interpolation engine. `InterpolatorCore` maintains a global registry of type-to-interpolator mappings. 15 native interpolators are pre-registered.

### 3. State Snapshots (`StateSnapshotCore<TTarget>`)
- **Key files**: `TransitionSystem/State.cs`, `TransitionSystem/StateSnapshot.cs`
- **Purpose**: Captures the property values to animate and their target values. Supports fluent configuration: `.Property<T>() → .To() → .Duration() → .Ease() → .Delay()`.

### 4. Property Path Resolution (`TransitionProperty`)
- **Key file**: `TransitionSystem/TransitionProperty.cs`
- **Purpose**: Resolves deep property access paths (e.g., `Background.Color`) using reflection. Supports read/write through a chain of `PropertyInfo` segments.

### 5. Transition Scheduler (`TransitionSchedulerCore`)
- **Key file**: `TransitionSystem/TransitionScheduler.cs`
- **Purpose**: Manages the execution timeline. Supports `Start`, `Pause`, `Resume`, `Exit`. Uses `IUIThreadInspector` to ensure thread-safe property updates.

### 6. Transition Effects (`TransitionEffect`, `TransitionEx`)
- **Key files**: `TransitionSystem/TransitionEffect.cs`, `TransitionSystem/TransitionEx.cs`
- **Purpose**: Higher-level orchestration for multi-property, multi-target transitions. Includes built-in effect types.

### 7. Native Interpolators Library
- **Key files**: `TransitionSystem/NativeInterpolators/*.cs` (15 files)
- **Purpose**: Concrete interpolators for primitive and common .NET types.

### 8. Platform Adapter Interpolators
- **Key files**: `Adapters/VeloxDev.Avalonia/PlatformAdapters/Interpolators/*.cs` (and WPF/WinUI equivalents)
- **Purpose**: Platform-specific interpolators for UI types like `Brush`, `Thickness`, `CornerRadius`, `Transform`, etc.

## Dependency Map

```
TransitionSystem (core)
├── Eases (self-contained, no dependencies)
├── InterpolatorCore (registry pattern)
│   └── NativeInterpolators (15 built-in)
├── StateSnapshotCore → TransitionProperty → Reflection
├── TransitionSchedulerCore → IUIThreadInspector
└── TransitionEffect → TransitionEx

Platform Adapters:
VeloxDev.Avalonia
└── PlatformAdapters/Interpolators/  ← Platform-specific types
```
