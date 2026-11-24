# 脚本模块

文件：`wwwroot/veloxdev.workflow.js`，随 `VeloxDev.Razor` 发布，并以 `_content/VeloxDev.Razor/veloxdev.workflow.js` 提供。

组件按需导入该模块。每个导出都转发到 `window.veloxdevWorkflow` 上的同名函数，所以宿主无需导入也能直接调用。滚轮初始化器安装非被动 `wheel` 监听器，缩放路径在缩放后的下一帧派发 `veloxdev-wf-layout-changed`；手写缩放路径必须派发同一事件，否则插槽锚点会停在缩放前的位置。

## 表面与视口

| 导出 | 参数 | 结果 |
| --- | --- | --- |
| `initSurface` | `scrollerEl, canvasHostEl, dotnetRef, initialW, initialH, contentX, contentY, initialOffsetX, initialOffsetY, initialScrollX, initialScrollY` | 带 `dispose()` 的句柄；开始滚动上报与 DOM 边缘扩展。 |
| `getCanvasTranslate` | `canvasEl` | 画布的 `{ x, y }` 平移。 |
| `toCanvasLocal` | `scrollerId, clientX, clientY` | `[x, y]` 画布局部点。 |
| `getViewportSize` | `scrollerEl` | 滚动视口的 `{ width, height }`。 |
| `scrollToRatio` | `scrollerId, ratioX, ratioY` | 滚到滚动范围的某个比例。 |
| `scrollToPosition` | `scrollerId, x, y` | 滚到绝对偏移。 |
| `scrollByDelta` | `scrollerId, dx, dy` | 增加像素位移。 |
| `scrollSurfaceBy` | `scrollerId, dx, dy` | 表面滚动口使用的滚轮式滚动。 |
| `setSurfaceLayout` | `scrollerId, contentX, contentY` | 为网格/轴层发布内容平移。 |
| `ensureCanvasSize` | `scrollerId, width, height` | 把画布宿主至少扩到请求尺寸。 |
| `applySurfaceNavigation` | `scrollerId, layoutX, layoutY, contentW, contentH, scrollX, scrollY` | 在一个同步步骤里应用平移、范围与滚动。 |
| `applyZoomSurface` | `scrollerId, layoutX, layoutY, contentW, contentH, scrollX, scrollY, nodeGeometry` | 在一个浏览器帧里应用整次缩放事务。 |

## 网格与小地图

| 导出 | 参数 | 结果 |
| --- | --- | --- |
| `measureMinimapArea` | `scrollerId` | `{ availableRight, availableTop, availableBottom, overlayWidth }`。 |
| `setMinimapMapping` | `scrollerId, scale, ox, oy, minX, minY, maxX, maxY` | 保存内容适配映射。 |
| `setMinimapViewport` | `scrollerId, worldX, worldY, vw, vh` | 移动视口块。 |
| `refreshMinimapViewport` | `scrollerId` | 重渲染后重新应用最后的世界矩形。 |
| `initMinimap` | `minimapEl, scrollerId, dotnetRef` | 带 `dispose()` 的句柄；启用拖拽导航。 |

## 逐视图手势

| 导出 | 参数 | 结果 |
| --- | --- | --- |
| `initNodeDrag` | `nodeEl, dotnetRef` | 句柄；调用 `OnNodeDrag` / `OnNodeDragEnd` 与 `RequestPressVerdict`。 |
| `setNodePosition` | `nodeEl, x, y` | 不触发 .NET 渲染地重定位节点包装元素。 |
| `initSlotConnection` | `slotEl, dotnetRef` | 句柄；执行橡皮筋手势并上报 start/move/end。 |
| `initSlotLayout` | `hostEl, dotnetRef` | 句柄；测量 `data-slot-id` 元素并投递 `[id, x, y]` 批次。 |
| `initWheelZoom` | `scrollerEl, dotnetRef` | 句柄；把 Ctrl+滚轮连发合并成一次 `OnWheelZoom` 调用。 |
| `initWheelScroll` | `scrollerEl, dotnetRef` | 句柄；同步 `preventDefault` 普通滚轮并路由它。 |

## 互操作契约

- .NET 侧是 `WorkflowSurfaceBehavior`、`WorkflowNodeDragBehavior`、`WorkflowSlotConnectionBehavior`、`WorkflowSlotLayoutBehavior` 与 `WorkflowMinimapOverlay`。
- 坐标批次与几何数组都用 `.` 小数转成字符串；逗号小数的文化不得解析它们。
- 释放句柄会取消该句柄安装的所有监听器与观察器。
