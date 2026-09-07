# Complexity Analysis — MonoBehaviour

All per-frame bounds below hold for a channel with $b$ active behaviours, driven by its update and fixed drivers. `MonoBehaviourManager.cs` line references match the current source.

## Per-frame dispatch

$$
O(b), \quad b = \text{active behaviours}
$$

`ExecuteBehaviorsUpdateSync` / `ExecuteBehaviorsLateUpdateSync` / `ExecuteBehaviorsFixedUpdateSync` iterate the cached wrapper array once, calling `InvokeUpdate` / `InvokeLateUpdate` / `InvokeFixedUpdate` per behaviour — `MonoBehaviourManager.cs` lines 611-657.

The wrapper array is rebuilt by `GetCachedWrappers` (lines 663-673) only when a registration/removal flagged a sort, or every `MAX_CONFIG_CACHE_DURATION_MS = 1000` ms. The rebuild copies the active wrappers and insertion-sorts them by `ExecutionOrder` (`RebuildCachedWrappers`, lines 805-834). Behaviour counts are typically tiny, so the per-frame sort cost is amortized away:

$$
T_{\text{update}} = O(b) \text{ per frame}, \quad b \ll n_{\text{registered}}
$$

When a behaviour sets `FrameEventArgs.Handled = true`, the loop breaks early, so the effective cost becomes $O(k)$ where $k$ is the number of behaviours executed before the short-circuit ($k \le b$).

## Fixed-update interval

$$
O(b) \text{ every } \approx \text{interval ms}
$$

The fixed driver runs `ExecuteBehaviorsFixedUpdateSync` concurrently with the update driver, paced by `SetFixedUpdateInterval` (default `DEFAULT_FIXED_UPDATE_INTERVAL_MS = 16`). Its steady-state cost is independent of the frame rate — physics/timestep logic is decoupled from rendering FPS.

## Event-args reuse (object pool)

Each frame the update driver calls `CreateFrameEventArgs` (lines 745-755), which draws from a per-channel `ObjectPool<FrameEventArgs>` (default `DEFAULT_OBJECT_POOL_SIZE = 50`) instead of allocating:

$$
O(1) \text{ pool get/return per frame, zero steady-state allocation}
$$

The pool is a lock-free `ConcurrentStack` with a bounded capacity, shared by both drivers (fixed events come from the same pool). Unhandled `FixedUpdate` events are enqueued and drained back to the pool by the update driver at the top of the next frame (`DrainFixedUpdateEvents`, lines 757-761); handled ones are returned immediately. `ConfigChangeRequest` and `BehaviorWrapper` objects come from their own pools of the same capacity, so registration/config churn also avoids steady-state allocation.

## Frame pacing

`FrameRateControlSync` sleeps until the target frame duration (`_cachedTargetFrameDurationTicks`, updated when `TargetFPS` is applied). `PrecisionSleep` spins below `SPIN_ONLY_THRESHOLD_MS = 2` ms and otherwise does `Thread.Sleep(1)` plus a tail spin — lines 763-803. Per frame this is $O(1)$ wall-clock. In async-loop mode the same pacing is a `Task.Delay` with a minimum of 1 ms plus `Task.Yield` when a frame overshoots (`UpdateLoopAsync`, lines 548-605).

## Config / registration batching

Config changes, behaviour adds/removes and marshalled main-thread actions are exchanged through concurrent queues drained once per frame by `ProcessMainThreadOperations` (lines 675-688):

| Operation | Per frame |
|---|---|
| `SetTargetFPS` / `SetFixedUpdateInterval` / `SetTimeScale` | $O(1)$ pooled enqueue; $O(q)$ drain per frame, $q$ = pending requests |
| `RegisterBehaviour` / `UnregisterBehaviour` | $O(1)$ enqueue; $O(r)$ drain, $r$ = pending registrations |
| `ExecuteOnMainThread` | $O(1)$ enqueue; up to 64 drained per frame |
| `Pause` / `Resume` / `Stop` | $O(1)$ volatile write + event raise (not queued) |

## Memory

| Structure | Behaviour |
|---|---|
| Cached wrapper array | $O(b)$ `BehaviorWrapper[]`, rebuilt on change or every 1000 ms |
| Object pools | 3 pools (`FrameEventArgs`, `ConfigChangeRequest`, `BehaviorWrapper`), fixed capacity 50 per channel; instances reused, not garbage |
| Concurrent queues | $O(q)$ config / $O(r)$ registration / $O(a)$ main-thread actions, drained each frame; `_fixedUpdateEvents` drains next update frame |
| Drivers | 2 per channel — threads (thread mode) or async tasks (async-loop mode) |

## Per-operation summary

| Operation | Complexity |
|---|---|
| `Update` / `LateUpdate` dispatch (per frame) | $O(b)$ |
| `FixedUpdate` dispatch | $O(b)$ per fixed interval (~16 ms) |
| `Start` / `StopAsync` | $O(b + q)$ (build / clear structures) |
| Config setter (`SetTargetFPS`, `SetTimeScale`, ...) | $O(1)$ pooled enqueue |
| `RegisterBehaviour` / `UnregisterBehaviour` | $O(1)$ enqueue; $O(b)$ cached-array rebuild (amortized) |
| `ExecuteOnMainThread` | $O(1)$ enqueue; ≤ 64/frame drain |
| `FrameEventArgs` creation | $O(1)$ pooled — no steady-state allocation |
