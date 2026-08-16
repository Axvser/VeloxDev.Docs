# Complexity Analysis — MonoBehaviour

## Per-frame dispatch

$$O(b), \quad b = \text{active behaviours}$$

`ExecuteBehaviorsUpdateSync` / `ExecuteBehaviorsLateUpdateSync` / `ExecuteBehaviorsFixedUpdateSync` iterate the cached wrapper array once, calling `InvokeUpdate` / `InvokeLateUpdate` / `InvokeFixedUpdate` per behaviour — `MonoBehaviourManager.cs` lines 610-656.

The wrapper array is rebuilt only when behaviours are added/removed or every `MAX_CONFIG_CACHE_DURATION_MS = 1000` ms, and the rebuild itself is an insertion sort over a small array (behaviour counts are typically tiny), so the per-frame sort cost is amortized away:

$$T_{\text{update}} = O(b) \text{ per frame}, \quad b \ll n_{\text{registered}}$$

When a behaviour sets `FrameEventArgs.Handled = true`, the loop breaks early, so the effective cost becomes $O(k)$ where $k$ is the number of behaviours executed before the short-circuit ($k \le b$).

## Fixed-update interval

$$O(b) \text{ every } \approx \text{interval ms}$$

`ExecuteBehaviorsFixedUpdateSync` runs on the fixed thread every `SetFixedUpdateInterval` ms (default `DEFAULT_FIXED_UPDATE_INTERVAL_MS = 16`). Its steady-state cost is independent of the frame rate — physics/timestep logic is decoupled from rendering FPS.

## Event-args reuse (object pool)

Each frame calls `CreateFrameEventArgs`, which draws from a per-channel `ObjectPool<FrameEventArgs>` (default `DEFAULT_OBJECT_POOL_SIZE = 50`) instead of allocating:

$$O(1) \text{ pool get/return per frame, zero steady-state allocation}$$

Unhandled `FixedUpdate` events are enqueued and drained back to the pool by the update thread (`DrainFixedUpdateEvents`, lines 756-760), so no `FrameEventArgs` escapes per frame.

## Frame pacing

`PrecisionSleep` spins below `SPIN_ONLY_THRESHOLD_MS = 2` ms and otherwise does `Thread.Sleep(1)` plus a tail spin — `MonoBehaviourManager.cs` lines 777-802. Per frame this is $O(1)$ wall-clock.

## Config / registration batching

Config changes, behaviour adds/removes and main-thread actions are exchanged through concurrent queues drained once per frame:

| Operation | Per frame |
|---|---|
| `SetTargetFPS` / `SetFixedUpdateInterval` / `SetTimeScale` | $O(1)$ queue enqueue; $O(q)$ drain per frame, $q$ = pending requests |
| `RegisterBehaviour` / `UnregisterBehaviour` | $O(1)$ queue enqueue; $O(r)$ drain, $r$ = pending registrations |
| `ExecuteOnMainThread` | $O(1)$ enqueue; up to 64 drained per frame |

## Memory

| Structure | Behaviour |
|---|---|
| Cached wrapper array | $O(b)$ `BehaviorWrapper[]`, rebuilt on change or every 1000 ms |
| `FrameEventArgs` pool | Fixed capacity 50 per channel; pooled instances are reused, not garbage |
| Concurrent queues | $O(q)$ config / $O(r)$ registration / $O(a)$ main-thread actions, drained each frame |
| Threads | 2 threads per channel (or 2 async tasks when `UseAsyncLoop`) |
| Wrapper objects | `BehaviorWrapper` and `ConfigChangeRequest` are themselves pooled |

## Per-operation summary

| Operation | Complexity |
|---|---|
| `Update` / `LateUpdate` dispatch (per frame) | $O(b)$ |
| `FixedUpdate` dispatch | $O(b)$ per fixed interval (~16 ms) |
| `Start` / `StopAsync` | $O(b + q)$ (build/clear structures) |
| Config setter (`SetTargetFPS`, `SetTimeScale`, ...) | $O(1)$ |
| `RegisterBehaviour` / `UnregisterBehaviour` | $O(1)$ enqueue; $O(b)$ cached-array rebuild (amortized) |
| `ExecuteOnMainThread` | $O(1)$ enqueue; ≤ 64/frame drain |
| `FrameEventArgs` creation | $O(1)$ pooled — no steady-state allocation |
