# Razor Adapter

Razor moves the per-frame work into JavaScript. Every drag frame scans all link elements in the DOM, re-measures the endpoints of the links that touch the dragged node, and rewrites a 128-point polyline string. The .NET side adds Blazor diffing and one interop round trip per render, so the adapter trades CPU locality for a much smaller managed surface.

## Cost model

| Symbol | Meaning |
|---|---|
| $m$ | link elements in the DOM |
| $t$ | links touching the dragged node |
| $p$ | polyline samples (128) |
| $v$ | visible items |
| $r$ | rendered grid ticks |
| $n$ | nodes |

## Drag-time link sync

`syncLinksForNode` queries every link element, then filters to those touching the dragged node's slots (`Src/Adapters/VeloxDev.Razor/wwwroot/veloxdev.workflow.js:468-497`).

```javascript
const touched = [];
const linkEls = host.querySelectorAll('[data-veloxdev-link-id]');
for (let i = 0; i < linkEls.length; i++) {
    const svg = linkEls[i];
    const senderId = svg.getAttribute('data-veloxdev-sender-slot');
    const receiverId = svg.getAttribute('data-veloxdev-receiver-slot');
    if (!slotIds.has(senderId) && !slotIds.has(receiverId)) continue;
    const ends = linkEndsFromSlotElements(host, senderId, receiverId);
    if (!ends) continue;
    ...
    const d = polylinePathFromEnds(ends);          // 128 points
    for (let k = 0; k < paths.length; k++) {
        if (paths[k].getAttribute('d') !== d) paths[k].setAttribute('d', d);
```

The filter reduces the rewrite to $t$ links, but the scan is still over all $m$. Each touched link pays two `getBoundingClientRect` reads and one 128-point string build (`:427-443`), so a drag frame costs

$$
T_{\text{drag}} = O(m + t \cdot p)
$$

```plot
{
  "title": "Links examined per drag frame",
  "grid": true,
  "xAxis": { "domain": [1, 100] },
  "yAxis": { "domain": [0, 1000] },
  "data": [
    { "fn": "x", "color": "#f472b6", "title": "querySelectorAll scan" },
    { "fn": "x/10", "color": "#4a9eff", "title": "links actually rewritten" }
  ]
}
```

## Slot measurement

`initSlotLayout.measure` scans every slot element, calls `getBoundingClientRect` per slot — a forced synchronous layout — dedupes by a string key, and invokes .NET once with a batch (`veloxdev.workflow.js:1390-1408`).

```javascript
hostEl.querySelectorAll('[data-veloxdev-slot-id]').forEach(function (el) {
    const id = el.getAttribute('data-veloxdev-slot-id'); if (!id) return;
    const r = glyphRect(el);                              // getBoundingClientRect
    if (!r || (r.width <= 0 && r.height <= 0)) return;
    const cx = ((r.left + r.width/2) - canvasRect.left - contentX).toFixed(2);
    const cy = ((r.top + r.height/2) - canvasRect.top - contentY).toFixed(2);
    seen[id] = [id, cx, cy];
});
for (const id in seen) batch.push(seen[id]);
if (!batch.length) return;
const key = batch.map(b => b[0] + ':' + b[1] + ',' + b[2]).join(';');
if (key === lastKey) return;
lastKey = key;
dotnetRef.invokeMethodAsync('OnSlotLayoutBatch', batch);
```

One pass is $O(v)$ layout-forcing reads. During a drag it re-runs on every animation frame until the rounded coordinates converge, so a settle costs several passes; the `lastKey` comparison is what stops the loop.

## Zoom

`applyZoomLinkCurves` iterates every link element and rebuilds each measurable curve inside one atomic `applyZoomSurface` (`veloxdev.workflow.js:511-531`, `:549-628`). Wheel notches are compounded on the .NET side and issued as one interop call with a `string[][]` node batch, so the round-trip count is $O(1)$ per gesture while the JS pass is $O(m)$.

## Grid and minimap

Grid ticks are generated for the rendered window plus a one-viewport margin, $O(r)$, and the band is moved by a CSS transform each frame rather than re-rendered (`Src/Adapters/VeloxDev.Razor/WorkflowSystem/AttachedBehaviors/WorkflowGridDecorator.razor.cs:180-221`).

The minimap emits one `<rect>` per node per rebuild, $O(n)$ DOM nodes, throttled to 16 ms (`WorkflowMinimapOverlay.razor:10-22`; `:428-473`). Scroll only moves the viewport block through one JS call, so it does not rebuild markup.

## Pool and interop

`ViewPool` batches Add/Remove bursts into a single `StateHasChanged` and snapshots the source once, so one render diffs $O(v)$ items (`WorkflowSystem/AttachedBehaviors/ViewPool.razor.cs:52-90`). Each render on Blazor Server is a network round trip; the code minimises calls through atomic zoom, batched slot reports and a JS-owned minimap viewport.

## Caching summary

- `lastKey` dedupe stops redundant slot batches.
- The rAF convergence loop stops when coordinates settle.
- Grid ticks cover a margin, not one per scroll frame.
- Minimap rebuilds are throttled to 16 ms.
- Link paths are compared before writing `d`.

## Related

- [Platform Adapter Contract](../24_platform-adapter-contract/index.md) — the shared structures this adapter consumes.
- [MAUI Adapter](../28_maui-adapter/index.md) — the other single-layer link strategy, kept in-process.
