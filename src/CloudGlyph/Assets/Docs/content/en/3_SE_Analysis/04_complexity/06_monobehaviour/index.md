# Complexity Analysis — MonoBehaviour

All per-frame bounds below hold for a channel with $b$ active behaviours, driven by its update and fixed drivers. `MonoBehaviourManager.cs` line references match the current source.

## Per-frame dispatch

$$
O(b), \quad b = \text{active behaviours}
$$

`ExecuteBehaviorsUpdateSync` / `ExecuteBehaviorsLateUpdateSync` / `ExecuteBehaviorsFixedUpdateSync` iterate the cached wrapper array once, calling `InvokeUpdate` / `InvokeLateUpdate` / `InvokeFixedUpdate` per behaviour — `MonoBehaviourManager.cs` lines 690-738.

The wrapper array is rebuilt by `GetCachedWrappers` (lines 742-752) only when a registration/removal flagged a sort, or every `MAX_CONFIG_CACHE_DURATION_MS = 1000` ms. The rebuild copies the active wrappers and insertion-sorts them by `ExecutionOrder` (`RebuildCachedWrappers`, lines 873-903). Behaviour counts are typically tiny, so the per-frame sort cost is amortized away:

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

Each frame the update driver calls `CreateFrameEventArgs` (lines 825-835), which draws from a per-channel `ObjectPool<FrameEventArgs>` (default `DEFAULT_OBJECT_POOL_SIZE = 50`) instead of allocating:

$$
O(1) \text{ pool get/return per frame, zero steady-state allocation}
$$

The pool is a lock-free `ConcurrentStack` with a bounded capacity, shared by both pumps: the fixed pump returns each `FrameEventArgs` to the same pool as soon as that push is done, so nothing crosses threads to recycle it. `ConfigChangeRequest` and `BehaviorWrapper` objects come from their own pools of the same capacity, so registration/config churn also avoids steady-state allocation.

## Frame pacing

`FrameRateControlSync` sleeps until the target frame duration (`_cachedTargetFrameDurationTicks`, updated when `TargetFPS` is applied), and the fixed pump sleeps until the next step is owed. Both go through `Sleep` (lines 863-871), which is an ordinary `Thread.Sleep` in chunks of at most `MAX_SLEEP_CHUNK_MS = 50`, with the token checked between chunks — so there is no busy-wait anywhere on the frame path. Precision was given up deliberately: the samplers own correctness, so a late wake is a late frame and never a lost one or a wrong interval. Per frame this is $O(1)$ wall-clock. In async-loop mode the same pacing is a `Task.Delay` with a minimum of 1 ms plus `Task.Yield` when a frame overshoots (`UpdateLoopAsync`, lines 623-688).

## Config / registration batching

Config changes, behaviour adds/removes and marshalled main-thread actions are exchanged through concurrent queues drained once per frame by `ProcessMainThreadOperations` (lines 754-767):

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
| Concurrent queues | $O(q)$ config / $O(r)$ registration / $O(a)$ main-thread actions, drained each frame; fixed args return to the pool inline rather than through a queue |
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
