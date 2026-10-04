# Complexity — Tickable

The feature's cost model is unusual in that almost nothing grows with the frame rate: the per-frame work is linear in the number of registered behaviours with a small constant, and the expensive-looking parts (re-sorting after a registration, rebuilding a snapshot) happen on a change rather than per frame.

Let $N$ be the number of behaviours registered on one channel, $F$ the target frames per second and $h$ the fixed step in milliseconds.

## Summary

| Operation | Time | Space | Bounded by |
|---|---|---|---|
| Per-frame `Update` + `LateUpdate` sweeps | $O(N)$ | $O(1)$ | $N$, not $F$ |
| Per-step `FixedUpdate` sweep | $O(N)$ per step | $O(1)$ | $N$ |
| `RegisterBehaviour` (caller side) | $O(1)$ amortised | $O(1)$ | `ConcurrentQueue<T>` enqueue |
| Registration drain (pump side) | $O(k \log N + k)$ | $O(1)$ per behaviour | $k$ = behaviours added this frame |
| `RebuildCachedWrappers` | $O(N^2)$ worst case | $O(N)$ | Insertion sort — chosen because $N$ is small |
| `GetCachedWrappers` cache hit | $O(1)$ | — | One `Stopwatch.GetTimestamp` |
| Status query | $O(1)$ expected | $O(1)$ | `ConcurrentDictionary` hash lookup |
| Pool `Get` / `Return` | $O(1)$ | $O(1)$ | Lock-free `ConcurrentStack<T>` |

## Where the numbers come from

- The dispatch arrays are read once per sweep and walked by index, so a sweep is exactly $N$ iterations of a body whose work is a delegate call plus a `Handled` check. The `Handled` flag can cut it short, which makes the *worst* case $O(N)$ and the common case smaller.
- Registration is amortised: the caller pays one enqueue, and the pump pays one dictionary insert plus an insertion sort. The sort is $O(N^2)$ in the worst case, but it runs only when `_wrappersNeedSort` was set by a drain, and the source notes that behaviour counts are small enough that avoiding LINQ's allocation is worth more than an $O(N \log N)$ sort.
- The `MAX_CONFIG_CACHE_DURATION_MS` refresh (1 s) means the cache is re-validated by timestamp almost every frame but only rebuilt on a change.

## Pages

| Sub-page | Covers |
|---|---|
| [Frame dispatch](00_frame-dispatch/index.md) | The per-frame and per-step sweeps, the `Handled` short-circuit, and the amortised cache validation |
| [Fixed-step pacing](01_fixed-step-pacing/index.md) | The compensating sampler's arithmetic, the debt bound, and why the sleep is chunked |
| [Registry and pooling](02_registry-and-pooling/index.md) | Channel registry lookup, the copy-on-write snapshot, and the three pools |

## The one formula worth carrying around

At target rate $F$ and step $h$ ms, a channel delivers about

$$
\text{deliveries per second} \approx F \cdot (2N) + \left(\frac{F \cdot h}{1000}\right)^{-1} \cdot N
$$

where the first term is the update and late sweeps and the second is the fixed steps. The demo reports the second factor directly as "steps per frame": the WPF demo measures $\Delta \text{fixed} / \Delta \text{frames}$ over a one-second window and displays it, and the point of the measurement is that it barely moves when the frame-rate buttons are pressed (`MainWindow.xaml.cs` lines 201-228).
