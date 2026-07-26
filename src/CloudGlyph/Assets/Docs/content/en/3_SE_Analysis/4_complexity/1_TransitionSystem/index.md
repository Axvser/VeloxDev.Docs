# Complexity Analysis — TransitionSystem

## Code Size

| Component | Files | Lines |
|---|---|---|
| Easing functions | 1 | ~240 |
| Core abstractions | 10 | ~800 |
| Native interpolators | 15 | ~450 |
| State/Transition | 6 | ~600 |
| Scheduler | 2 | ~300 |
| **Subtotal (core)** | **~34** | **~2,400** |
| Tests | 5 | ~450 |
| Platform adapters (per platform) | ~15 | ~600 |

## Interpolator Performance

| Operation | Complexity |
|---|---|
| RegisterInterpolator | O(1) |
| TryGetInterpolator | O(1) |
| Interpolate (linear) | O(steps) |
| Interpolate (color) | O(steps × channels) |
| Ease calculation | O(1) per call |
