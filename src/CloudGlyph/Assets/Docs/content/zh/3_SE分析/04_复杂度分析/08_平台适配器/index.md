# 08 · 平台适配器 — 复杂度分析

平台适配器核心操作的时间与空间复杂度。界限以 WPF 适配器源码和 WPF 树视图模板为依据；未经演示覆盖的细节以源码推断并标注 `*推断所得*`。设 $N$ = 模型节点总数、$V$ = 可见（已实例化）视图数、$C$ = 与视口相交的空间网格单元数、$P$ = 池化视图数、$b$ = 批次大小。

## 视图池与虚拟化

`WorkflowSurfaceBehavior` 在每次滚动/平移时保持 `Helper.Viewport` 为最新；空间索引（`WorkflowSpatialManager` + `SpatialGridHashMap`）把该视口转换成画布面板绑定的 `VisibleItems` 集合。`ViewManager`（由 `ViewPool` 为每个 `Panel` 创建）只渲染该集合里的项。

| 操作 | 开销 | 说明 |
|---|---|---|
| 空间可见集计算（`WorkflowSpatialEx.Virtualize`） | $O(V + C)$ | 对节点/节点对网格地图做区域查询并带 1 跳连接扩展；结果按引用同一性就地 diff 进 `VisibleItems` 集合（删除过期、补加缺失），每项 $O(1)$ |
| 实例化一个可见项 | 摊还 $O(1)$ | 命中池（出队 + 重新绑定），否则每个具体类型执行一次 `template.LoadContent()` |
| 隐藏一项（从 `VisibleItems` 移除） | $O(1)$ | 折叠 + 清空 `DataContext` + 入对应类型的池 |
| 分批刷新 | 每 dispatcher `Background` 滴答 $O(b)$ | $b = 3$（WPF 源码已验证）；整个批次在 $\lceil V/b \rceil$ 个滴答内排空，单帧不会实例化超过一个小常数 |
| 全部重置 / 分离 | $O(V)$ | 逐个折叠并重新入池 |
| 模板查找 | 摊还 $O(1)$ | 按具体类型缓存于 `_templateMap`；未命中时依次走 `TemplateSelector` → 面板/可视祖先资源 → `Application.Current.Resources` |

复用而非销毁，使每次增删的稳态分配为摊还 $O(1)$，因此大图上的平移/缩放不会产生正比于 $N$ 的 GC 压力。

## 缩放：考虑缩放因子的锚点折叠

缩放不是单个渲染变换。画布写入更小的 `CanvasLayout.Scale`（一个*折叠*因子——滚轮向上除以 $1/1.1$）；每个 `NodeDefaultViewModel` 的 `Anchor`/`Size` getter 按该比例朝世界原点折叠，每个节点的 `WorkflowNodeScaleTracker` 在 `Scale` 变化时重新触发它们。

| 操作 | 开销 | 说明 |
|---|---|---|
| 一次缩放档位（一次滚轮） | $O(N)$ 模型通知 + $O(V)$ 重绑定 | 每个模型节点的缩放跟踪器都会触发（重新触发 `Anchor`/`Size`），但只有 $V$ 个已实例化视图会重新绑定并重新布局 |
| `CanvasLayout.Update` 自动扩展 | $O(1)$ | 重算 `ActualSize`/`ActualOffset`；无逐节点工作 |
| `EnsureNegativeCover`（深度缩放可达性） | $O(N)$ | 扫描一次全部节点锚点以增长 `NegativeOffset`，保证负世界内容仍可滚动；单调，仅正内容时为无操作 |
| 视口中心枢轴保持 | $O(1)$ | `WorldAtViewportCenter`/`PivotCenterScroll` 捕获视口中心下的世界点；画布从不平移，只有滚动移动 |
| 折叠后的槽锚点再同步 | $O(V_s)$ | `WorkflowSlotLayoutBehavior` 在每个可见槽中心变化后（`LayoutUpdated`/`SizeChanged`）重新读取，使连线端点在节点折叠的同帧跟随 |

因此缩放开销随模型规模变化（$O(N)$ 通知），但每帧可视工作仍有界于屏幕内容；深度缩放覆盖是一次脏式、每次手势 $O(N)$ 的遍历。

## 平移与越界增长

| 操作 | 开销 |
|---|---|
| 每次平移滴答（鼠标移动） | $O(1)$ — 计算候选偏移、夹取、两次 `ScrollTo*`、一次 `UpdateVisibleRegion` |
| 滚动时的可见区域更新 | $O(V + C)$ — 视口写入触发一次重新虚拟化 |
| 边缘越界增长 | 每次事件 $O(1)$；`ClampScrollOffset` 以离散步长（`DefaultPanExtendRatio = 0.15`）增长 `NegativeOffset`/`PositiveOffset`，随后仅在布局失效时让 `ScrollViewer` 对增大的画布重新度量 |

## 小地图投影

`WorkflowMinimapOverlay` 通过集合/属性变更把自身标记为脏（从不轮询），并缓存并集边界外加每个节点一个矩形。

| 操作 | 开销 |
|---|---|
| 全局边界刷新（脏时） | $O(N)$ — 对所有缓存的节点矩形求并（`WorkflowBounds.FromNodes`） |
| 整幅重绘 | $O(N)$ — 每个缓存的节点一个圆角矩形缩略图，每个在 $O(1)$ 适配/缩放投影后 $O(1)$；外加一个视口指示矩形 |
| 适配变换 | $O(1)$ — `MinimapFit` = 均匀 `min(drawW/cw, drawH/ch)` |
| 视口指示框拖拽 → 滚动 | $O(1)$ — `MinimapToWorld` + `MinimapToScroll`，随后夹取滚动 |

小地图刻意把*整张*图缩成缩略图（$O(N)$），而非仅可见区域——这正是它作为导航总览的意义所在。

## 总结

适配器让交互开销正比于屏幕上的内容：虚拟化把渲染视图限制为 $V$，视图池把每帧分配限制为小批量，平移每次输入事件为 $O(1)$。两个模型级开销分别是缩放（$O(N)$ 折叠通知 + 每次手势一次 $O(N)$ 覆盖检查）与小地图（$O(N)$ 重绘），二者都只由确实改变每个节点或整图总览的操作触发，且每个节点为常数因子。
