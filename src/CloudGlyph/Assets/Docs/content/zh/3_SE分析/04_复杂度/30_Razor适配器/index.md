# Razor适配器

Razor 把每帧工作移进 JavaScript。每个拖拽帧都会扫描 DOM 中的所有连线元素，重新测量与被拖节点相连的连线端点，并重写 128 点折线字符串。.NET 侧还要做 Blazor 差分，每次渲染一次互操作往返，所以本适配器用 CPU 局部性换取更小的托管面。

## 代价模型

| 符号 | 含义 |
|---|---|
| $m$ | DOM 中的连线元素数 |
| $t$ | 与被拖节点相连的连线数 |
| $p$ | 折线采样数（128） |
| $v$ | 可见条目数 |
| $r$ | 渲染的网格刻度数 |
| $n$ | 节点数 |

## 拖拽期的连线同步

`syncLinksForNode` 查询所有连线元素，再筛选出触及被拖节点插槽的那些（`Src/Adapters/VeloxDev.Razor/wwwroot/veloxdev.workflow.js:468-497`）。

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

筛选把重写量降到 $t$ 条，但扫描仍然是全部 $m$ 条。每条被触及的连线付两次 `getBoundingClientRect` 读取和一次 128 点字符串构造（`:427-443`），所以一个拖拽帧的代价是

$$
T_{\text{drag}} = O(m + t \cdot p)
$$

```plot
{
  "title": "每个拖拽帧检查的连线数",
  "grid": true,
  "xAxis": { "domain": [1, 100] },
  "yAxis": { "domain": [0, 1000] },
  "data": [
    { "fn": "x", "color": "#f472b6", "title": "querySelectorAll 扫描" },
    { "fn": "x/10", "color": "#4a9eff", "title": "实际重写的连线" }
  ]
}
```

## 插槽测量

`initSlotLayout.measure` 扫描所有插槽元素，逐个调用 `getBoundingClientRect` —— 一次强制同步布局 —— 用字符串键去重，然后只调用一次 .NET 批处理（`veloxdev.workflow.js:1390-1408`）。

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

一趟是 $O(v)$ 次强制布局读取。拖拽期间它在每个动画帧重跑，直到取整后的坐标收敛，所以一次稳定要花几趟；`lastKey` 比较是循环的终止条件。

## 缩放

`applyZoomLinkCurves` 在一个原子的 `applyZoomSurface` 内遍历所有连线元素并重建每条可测量的曲线（`veloxdev.workflow.js:511-531`、`:549-628`）。滚轮刻度在 .NET 侧累加，并以一次带 `string[][]` 节点批处理的互操作调用发出，所以每个手势的往返次数是 $O(1)$，而 JS 侧那一趟是 $O(m)$。

## 网格与小地图

网格刻度只为渲染窗口加一个视口边距生成，$O(r)$；标尺带每帧靠 CSS 变换移动而不重渲染（`Src/Adapters/VeloxDev.Razor/WorkflowSystem/AttachedBehaviors/WorkflowGridDecorator.razor.cs:180-221`）。

小地图每次重建为每个节点发一个 `<rect>`，$O(n)$ 个 DOM 节点，并节流到 16 ms（`WorkflowMinimapOverlay.razor:10-22`；`:428-473`）。滚动只通过一次 JS 调用移动视口块，不重建标记。

## 池与互操作

`ViewPool` 把 Add/Remove 突发合并成一次 `StateHasChanged`，并只快照一次源集合，所以一次渲染差分 $O(v)$ 个条目（`WorkflowSystem/AttachedBehaviors/ViewPool.razor.cs:52-90`）。Blazor Server 上每次渲染是一次网络往返；代码通过原子缩放、批量插槽上报与 JS 自管小地图视口来减少调用。

## 缓存小结

- `lastKey` 去重阻止冗余的插槽批处理。
- rAF 收敛循环在坐标稳定后停止。
- 网格刻度覆盖一个边距，而不是每个滚动帧一次。
- 小地图重建节流到 16 ms。
- 写入 `d` 之前先比较路径。

## 相关

- [平台适配器契约](../24_平台适配器契约/index.md) —— 本适配器消费的共享结构。
- [MAUI适配器](../28_MAUI适配器/index.md) —— 另一种单层连线策略，留在进程内。
